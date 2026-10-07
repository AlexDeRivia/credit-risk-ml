from io import BytesIO
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from openpyxl import Workbook

from .views import HEADERS


def sample_case(**overrides):
    case = {
        "dni": "12345678", "nombre": "Caso Uno", "dependientes": "2",
        "ingreso": "4500000", "prestamo": "30000000", "plazo": "12",
        "credito": "750", "residencial": "5000000", "comerciales": "2000000",
        "lujo": "1000000", "banco": "15000000", "educativo": "tecnico",
        "autonomo": "no",
    }
    case.update(overrides)
    return case


@override_settings(SECURE_SSL_REDIRECT=False)
class DemoFlowTests(SimpleTestCase):
    def test_home_and_model_inference(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        response = self.client.post(reverse("consulta_individual"), sample_case())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PROBABILIDAD DE APROBACIÓN")
        self.assertIn("pending_case", self.client.session)

    def test_save_uses_server_prediction_and_session_history(self):
        self.client.post(reverse("consulta_individual"), sample_case())
        expected = self.client.session["pending_case"]["estado"]
        result = self.client.post(reverse("guardar_consulta_individual"), data="{}", content_type="application/json")
        self.assertTrue(result.json()["success"])
        self.assertEqual(self.client.session["history"][0]["estado"], expected)
        self.assertEqual(self.client.post(reverse("guardar_consulta_individual")).status_code, 400)
        self.assertContains(self.client.get(reverse("reportes")), "Caso Uno")

    def test_invalid_form_does_not_predict(self):
        with patch("loans.views.predecir") as predict:
            result = self.client.post(reverse("consulta_individual"), sample_case(credito="1001"))
        self.assertContains(result, "fuera de rango")
        predict.assert_not_called()

    def test_csrf_blocks_save_without_token(self):
        from django.test import Client
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(reverse("guardar_consulta_individual"), "{}", content_type="application/json").status_code, 403)

    def test_batch_template_and_export(self):
        book = Workbook()
        sheet = book.active
        sheet.append(HEADERS)
        case = sample_case()
        sheet.append([case["dni"], case["nombre"], *[case[key] for key in HEADERS[2:]]])
        output = BytesIO()
        book.save(output)
        output.name = "demo.xlsx"
        output.seek(0)
        response = self.client.post(reverse("consulta_lotes"), {"archivo": output})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(len(response.json()["resultados"]), 1)
        self.assertEqual(self.client.get(reverse("descargar_resultados")).status_code, 200)

    def test_bad_batch_is_rejected_without_results(self):
        book = Workbook()
        book.active.append(("wrong", "columns"))
        output = BytesIO()
        book.save(output)
        output.name = "bad.xlsx"
        output.seek(0)
        response = self.client.post(reverse("consulta_lotes"), {"archivo": output})
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("batch", self.client.session)
