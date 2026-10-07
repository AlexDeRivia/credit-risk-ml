"""Fixed synthetic examples scored with the bundled model."""

DEMO_CASES = (
    ("90000001", "Caso Andino", 64000000, 772, "Aprobado", "92.28%"),
    ("90000002", "Caso Costa", 21500000, 609, "Aprobado", "91.89%"),
    ("90000003", "Caso Norte", 39000000, 506, "Denegado", "5.76%"),
    ("90000004", "Caso Sur", 44500000, 916, "Aprobado", "80.06%"),
    ("90000005", "Caso Central", 24000000, 504, "Denegado", "12.28%"),
    ("90000006", "Caso Valle", 48500000, 813, "Aprobado", "76.91%"),
    ("90000007", "Caso Sierra", 45000000, 518, "Denegado", "12.18%"),
    ("90000008", "Caso Pacífico", 71500000, 565, "Aprobado", "89.27%"),
    ("90000009", "Caso Oriente", 5000000, 441, "Denegado", "24.89%"),
    ("90000010", "Caso Río", 71500000, 713, "Aprobado", "87.03%"),
    ("90000011", "Caso Altura", 33500000, 818, "Aprobado", "86.63%"),
    ("90000012", "Caso Horizonte", 79000000, 375, "Denegado", "11.41%"),
    ("90000013", "Caso Lago", 67500000, 679, "Aprobado", "91.55%"),
    ("90000014", "Caso Prado", 72500000, 838, "Aprobado", "85.62%"),
    ("90000015", "Caso Brisa", 9000000, 501, "Denegado", "7.56%"),
    ("90000016", "Caso Sol", 79500000, 847, "Aprobado", "90.40%"),
)


def example_results():
    return [
        {
            "dni": case_id,
            "name": alias,
            "loan_amount": amount,
            "cibil_score": score,
            "estado": status,
            "probabilidad": probability,
            "source": "Ejemplo",
        }
        for case_id, alias, amount, score, status, probability in DEMO_CASES
    ]
