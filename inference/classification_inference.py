"""
Local and SageMaker inference for the Logistic Regression classifier
(Bank Marketing -> term-deposit subscription prediction).

Local usage:
    from inference.classification_inference import predict_local, DEFAULT_SAMPLE
    result = predict_local(DEFAULT_SAMPLE)

SageMaker usage:
    from inference.classification_inference import predict
    result = predict(DEFAULT_SAMPLE, use_sagemaker=True)
"""

from __future__ import annotations

import joblib
import pandas as pd

from app.config import CLASSIFICATION_MODEL_PATH

LABEL_MAP = {0: "No Subscription", 1: "Will Subscribe"}

DEFAULT_SAMPLE = {
    "age": 35, "job": "admin.", "marital": "married", "education": "university.degree",
    "default": "no", "housing": "yes", "loan": "no", "contact": "cellular",
    "month": "may", "day_of_week": "mon", "duration": 260, "campaign": 2,
    "pdays": 999, "previous": 0, "poutcome": "nonexistent",
    "emp.var.rate": -1.8, "cons.price.idx": 92.893, "cons.conf.idx": -46.2,
    "euribor3m": 1.313, "nr.employed": 5099.1,
}

_model = None


def _load_model():
    global _model
    if _model is None:
        _model = joblib.load(CLASSIFICATION_MODEL_PATH)
    return _model


def predict_local(features: dict) -> dict:
    """Run inference using the locally saved model artifact."""
    model = _load_model()
    row = pd.DataFrame([features])
    pred_class = int(model.predict(row)[0])
    proba = model.predict_proba(row)[0]
    return {
        "prediction": pred_class,
        "label": LABEL_MAP[pred_class],
        "probability_no":  float(round(proba[0], 4)),
        "probability_yes": float(round(proba[1], 4)),
        "source": "local",
    }


def predict_sagemaker(features: dict) -> dict:
    """Invoke the SageMaker hosted classification endpoint."""
    from app.sagemaker_client import invoke_classification_endpoint
    return invoke_classification_endpoint(features)


def predict(features: dict, use_sagemaker: bool = False) -> dict:
    """Route prediction to SageMaker or local model, with automatic fallback."""
    if use_sagemaker:
        try:
            return predict_sagemaker(features)
        except Exception as e:
            return {**predict_local(features), "fallback_reason": str(e)}
    return predict_local(features)
