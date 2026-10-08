"""Public portfolio demo. Requests never persist applicant data on the server."""

from io import BytesIO
import os
import re
from urllib.parse import urlparse
from zipfile import ZipFile

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from openpyxl import Workbook, load_workbook

from .ml_utils import predecir
from .demo_data import example_results


FIELDS = (
    "dependientes", "ingreso", "prestamo", "plazo", "credito", "residencial",
    "comerciales", "lujo", "banco",
)
LIMITS = {
    "dependientes": (0, 20), "ingreso": (0, 1_000_000_000),
    "prestamo": (1_000, 1_000_000_000), "plazo": (1, 20),
    "credito": (0, 1000), "residencial": (0, 1_000_000_000),
    "comerciales": (0, 1_000_000_000), "lujo": (0, 1_000_000_000),
    "banco": (0, 1_000_000_000),
}
HEADERS = ("id", "alias", *FIELDS, "educativo", "autonomo")
SCENARIO_FIELDS = {"prestamo", "plazo", "credito"}


def _parse_case(source):
    case_id = str(source.get("dni", source.get("id", ""))).strip()
    alias = str(source.get("nombre", source.get("alias", ""))).strip()
    if not re.fullmatch(r"[0-9]{8}", case_id):
        raise ValueError("El ID ficticio debe tener ocho dígitos.")
    if not re.fullmatch(r"[\wÀ-ÿ ]{3,40}", alias, re.UNICODE):
        raise ValueError("El alias debe tener entre 3 y 40 caracteres (letras, números o espacios).")
    parsed = {"dni": case_id, "nombre": alias}
    for field in FIELDS:
        raw = str(source.get(field, "")).strip()
        if not re.fullmatch(r"[0-9]{1,10}", raw):
            raise ValueError(f"{field}: ingresa un número entero válido.")
        value = int(raw)
        minimum, maximum = LIMITS[field]
        if not minimum <= value <= maximum:
            raise ValueError(f"{field}: valor fuera de rango ({minimum}–{maximum}).")
        parsed[field] = value
    for field, choices in (("educativo", ("tecnico", "secundaria")), ("autonomo", ("si", "no"))):
        value = str(source.get(field, "")).strip().lower()
        if value not in choices:
            raise ValueError(f"{field}: selecciona una opción válida.")
        parsed[field] = value
    return parsed


def _prediction(case):
    features = [case[field] for field in FIELDS]
    features += [int(case["educativo"] == "tecnico"), int(case["autonomo"] == "si")]
    result, probability = predecir(features)
    return "Aprobado" if result == 1 else "Denegado", round(probability * 100, 2)


def _summary(case, state, probability):
    return {
        "dni": case["dni"], "name": case["nombre"], "estado": state,
        "probabilidad": f"{probability:.2f}%", "loan_amount": case["prestamo"],
        "cibil_score": case["credito"], "source": "Tu sesión",
    }


def _all_results(request):
    return example_results() + request.session.get("history", []) + request.session.get("batch", [])


def _portfolio_metrics(rows):
    total = len(rows)
    approved = sum(row["estado"] == "Aprobado" for row in rows)
    return {
        "total": total,
        "approved": approved,
        "denied": total - approved,
        "rate": int(approved * 100 / total + 0.5) if total else 0,
        "average_score": round(sum(row["cibil_score"] for row in rows) / total) if total else 0,
        "amount": sum(row["loan_amount"] for row in rows),
        "amount_short": (f"{sum(row['loan_amount'] for row in rows) / 1_000_000:.1f}".replace(".", ",") + " M"),
    }


def home_view(request):
    rows = _all_results(request)
    return render(request, "home.html", {"metrics": _portfolio_metrics(rows), "recent": rows[-5:][::-1]})


def consulta_individual_view(request):
    context = {"form_data": {}}
    if request.method == "POST":
        request.session.pop("pending_case", None)
        context["form_data"] = request.POST
        try:
            case = _parse_case(request.POST)
            state, probability = _prediction(case)
            request.session["pending_case"] = _summary(case, state, probability)
            context.update(estado=state, probabilidad=probability, form_data=case)
        except (ValueError, TypeError) as exc:
            context["error"] = str(exc)
        except Exception:
            context["error"] = "No se pudo evaluar el caso. Inténtalo de nuevo."
    return render(request, "consulta_individual.html", context)


@require_POST
def simular_escenario(request):
    """Compare two actual inferences without changing the saved case."""
    try:
        base = _parse_case(request.POST)
        field = request.POST.get("variable", "")
        if field not in SCENARIO_FIELDS:
            raise ValueError("Selecciona una variable disponible para comparar.")
        candidate = {**base, field: request.POST.get("valor", "")}
        candidate = _parse_case(candidate)
        base_state, base_probability = _prediction(base)
        simulated_state, simulated_probability = _prediction(candidate)
    except (ValueError, TypeError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({
        "actual": {"estado": base_state, "probabilidad": base_probability},
        "escenario": {"estado": simulated_state, "probabilidad": simulated_probability},
        "diferencia": round(simulated_probability - base_probability, 2),
    })


@require_POST
def guardar_consulta_individual(request):
    pending = request.session.pop("pending_case", None)
    if not pending:
        return JsonResponse({"success": False, "message": "Evalúa un caso antes de guardarlo."}, status=400)
    history = request.session.get("history", [])[-9:]
    history.append(pending)
    request.session["history"] = history
    return JsonResponse({"success": True, "message": "Caso ficticio añadido al historial de esta sesión."})


@require_POST
def comprobar_cliente(request):
    case_id = request.POST.get("dni", "").strip()
    if not re.fullmatch(r"[0-9]{8}", case_id):
        return JsonResponse({"success": False, "message": "El ID debe tener ocho dígitos."}, status=400)
    found = any(row["dni"] == case_id for row in request.session.get("history", []))
    message = "El ID ya figura en esta sesión." if found else "ID disponible en esta sesión."
    return JsonResponse({"success": True, "message": message})


def consulta_lotes_view(request):
    if request.method == "GET":
        return render(request, "consulta_lotes.html", {"resultados": request.session.get("batch", [])})
    file = request.FILES.get("archivo")
    if not file or not file.name.lower().endswith(".xlsx") or file.size > 1_000_000:
        return JsonResponse({"success": False, "errors": ["Sube un archivo .xlsx de hasta 1 MB."]}, status=400)
    try:
        with ZipFile(file) as archive:
            parts = archive.infolist()
            if len(parts) > 100 or sum(part.file_size for part in parts) > 5_000_000:
                raise ValueError("El archivo Excel excede el límite de contenido.")
        file.seek(0)
        book = load_workbook(file, read_only=True, data_only=True, keep_links=False)
        sheet = book.active
        rows = sheet.iter_rows(values_only=True)
        headers = next(rows, None)
        if not headers or tuple(str(h).strip().lower() for h in headers) != HEADERS:
            raise ValueError("Las columnas no coinciden con la plantilla documentada.")
        cases = []
        for row in rows:
            if all(value is None for value in row):
                continue
            if len(cases) == 10:
                raise ValueError("El lote admite como máximo diez casos.")
            cases.append(_parse_case(dict(zip(HEADERS, row))))
        book.close()
        if not cases:
            raise ValueError("El archivo no contiene casos.")
        results = [_summary(case, *_prediction(case)) for case in cases]
    except (ValueError, TypeError, KeyError) as exc:
        return JsonResponse({"success": False, "errors": [str(exc)]}, status=400)
    except Exception:
        return JsonResponse({"success": False, "errors": ["No se pudo leer el archivo Excel."]}, status=400)
    request.session["batch"] = results
    return JsonResponse({"success": True, "resultados": results})


def _excel_response(rows, filename):
    book = Workbook()
    sheet = book.active
    sheet.append(["ID ficticio", "Alias", "Estado", "Probabilidad de aprobación", "Préstamo", "Puntaje"])
    for row in rows:
        sheet.append([row["dni"], row["name"], row["estado"], row["probabilidad"], row["loan_amount"], row["cibil_score"]])
    stream = BytesIO()
    book.save(stream)
    response = HttpResponse(stream.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def descargar_resultados(request):
    return _excel_response(request.session.get("batch", []), "resultados_demo.xlsx")


def generar_reporte_lote(request):
    return descargar_resultados(request)


def generar_reporte(request):
    pending = request.session.get("pending_case")
    if not pending:
        return redirect("consulta_individual")
    return _excel_response([pending], "resultado_demo.xlsx")


@require_POST
def limpiar_sesion(request):
    request.session.flush()
    return redirect("home")


def limpiar_filtros(request):
    return redirect("reportes")


def reportes_view(request):
    rows = _all_results(request)
    case_id = request.GET.get("dni", "").strip()
    state = request.GET.get("estado", "Todos")
    if case_id:
        rows = [row for row in rows if row["dni"] == case_id]
    if state in ("Aprobado", "Denegado"):
        rows = [row for row in rows if row["estado"] == state]
    return render(request, "reportes.html", {
        "resultados": rows, "dni": case_id, "estado": state,
        "metrics": _portfolio_metrics(rows),
    })


def reporte_global_view(request):
    rows = _all_results(request)
    metrics = _portfolio_metrics(rows)
    bands = (
        ("0–599", 0, 599), ("600–699", 600, 699),
        ("700–799", 700, 799), ("800–1000", 800, 1000),
    )
    score_bands = []
    for label, low, high in bands:
        count = sum(low <= row["cibil_score"] <= high for row in rows)
        score_bands.append({"label": label, "count": count, "width": round(count * 100 / metrics["total"]) if metrics["total"] else 0})
    amounts = []
    for state in ("Aprobado", "Denegado"):
        subset = [row["loan_amount"] for row in rows if row["estado"] == state]
        amounts.append({"label": state, "average": round(sum(subset) / len(subset)) if subset else 0})
    maximum = max((item["average"] for item in amounts), default=0)
    for item in amounts:
        item["width"] = round(item["average"] * 100 / maximum) if maximum else 0
    embed_url = os.getenv("POWER_BI_EMBED_URL", "").strip()
    parsed = urlparse(embed_url)
    if parsed.scheme != "https" or parsed.hostname != "app.powerbi.com" or parsed.path != "/view" or parsed.username or parsed.password or parsed.port:
        embed_url = ""
    return render(request, "reporte_global.html", {
        "metrics": metrics, "score_bands": score_bands, "amounts": amounts,
        "embed_url": embed_url,
    })


