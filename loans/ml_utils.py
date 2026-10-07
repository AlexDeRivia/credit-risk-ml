"""Inference for the bundled experimental model (trusted local artifact only)."""

import pickle
from functools import lru_cache
from pathlib import Path

import pandas as pd
from django.conf import settings


@lru_cache(maxsize=1)
def cargar_modelo():
    model_dir = Path(settings.BASE_DIR) / "ml_models"
    with (model_dir / "modelo_rf.pkl").open("rb") as model_file:
        model = pickle.load(model_file)
    with (model_dir / "columnas_modelo.pkl").open("rb") as columns_file:
        columns = pickle.load(columns_file)
    return model, columns


def predecir(datos_entrada):
    model, columns = cargar_modelo()
    if len(datos_entrada) != len(columns):
        raise ValueError("El número de variables no coincide con el modelo.")
    frame = pd.DataFrame([datos_entrada], columns=columns)
    prediction = int(model.predict(frame)[0])
    positive_index = list(model.classes_).index(1)
    approval_probability = float(model.predict_proba(frame)[0][positive_index])
    return prediction, approval_probability
