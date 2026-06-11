"""
SageMaker container entrypoint for the Random Forest Regressor.
This file is bundled with the model artifact (random_forest_regressor.pkl)
and executed inside the SKLearn inference container.
"""

import os
import json
import numpy as np
import joblib


def model_fn(model_dir):
    return joblib.load(os.path.join(model_dir, "random_forest_regressor.pkl"))


def input_fn(request_body, content_type="application/json"):
    if content_type == "application/json":
        data = json.loads(request_body)
        instances = data.get("instances", data)
        return np.array(instances, dtype=float)
    raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data, model):
    return model.predict(input_data)


def output_fn(prediction, accept="application/json"):
    return json.dumps({"predictions": prediction.tolist()}), "application/json"
