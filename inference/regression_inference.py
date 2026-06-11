"""
Local and SageMaker inference for the Random Forest Regressor
(California Housing -> median house value prediction).

Local usage:
    from inference.regression_inference import predict_local, DEFAULT_SAMPLE
    result = predict_local(DEFAULT_SAMPLE)

SageMaker usage:
    from inference.regression_inference import predict
    result = predict(DEFAULT_SAMPLE, use_sagemaker=True)
"""

from __future__ import annotations

import json
import os

import joblib
import numpy as np

from app.config import REGRESSION_MODEL_PATH, MODELS_DIR

FEATURE_NAMES_PATH = os.path.join(MODELS_DIR, "feature_names.json")

DEFAULT_SAMPLE = {
    "MedInc": 8.3252, "HouseAge": 41.0, "AveRooms": 6.984,
    "AveBedrms": 1.023, "Population": 322.0, "AveOccup": 2.556,
    "Latitude": 37.88, "Longitude": -122.23,
}

_model = None
_feature_names = None


def _load_model():
    global _model, _feature_names
    if _model is None:
        _model = joblib.load(REGRESSION_MODEL_PATH)
    if _feature_names is None and os.path.exists(FEATURE_NAMES_PATH):
        with open(FEATURE_NAMES_PATH) as f:
            _feature_names = json.load(f)
    return _model, _feature_names


def predict_local(features: dict) -> dict:
    """Run inference using the locally saved model artifact."""
    model, feature_names = _load_model()
    if feature_names:
        row = np.array([[features.get(k, 0.0) for k in feature_names]], dtype=float)
    else:
        row = np.array([list(features.values())], dtype=float)
    pred = model.predict(row)[0]
    return {
        "predicted_value_100k": float(round(pred, 4)),
        "predicted_value_usd": float(round(pred * 100_000, 2)),
        "source": "local",
    }


def predict_sagemaker(features: dict) -> dict:
    """Invoke the SageMaker hosted regression endpoint."""
    from app.sagemaker_client import invoke_regression_endpoint
    return invoke_regression_endpoint(features)


def predict(features: dict, use_sagemaker: bool = False) -> dict:
    """Route prediction to SageMaker or local model, with automatic fallback."""
    if use_sagemaker:
        try:
            return predict_sagemaker(features)
        except Exception as e:
            return {**predict_local(features), "fallback_reason": str(e)}
    return predict_local(features)
