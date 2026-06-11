"""
SageMaker container entrypoint for the Logistic Regression classifier.
This file is bundled with the model artifact (logistic_regression_classifier.pkl)
and executed inside the SKLearn inference container.
"""

import os
import json
import pandas as pd
import joblib


def model_fn(model_dir):
    return joblib.load(os.path.join(model_dir, "logistic_regression_classifier.pkl"))


def input_fn(request_body, content_type="application/json"):
    if content_type == "application/json":
        data = json.loads(request_body)
        instances = data.get("instances", data)
        return pd.DataFrame(instances)
    raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data, model):
    pred_classes = model.predict(input_data).tolist()
    proba = model.predict_proba(input_data).tolist()
    return [
        {
            "predicted_label": int(pred_classes[i]),
            "probability_no":  round(proba[i][0], 4),
            "probability_yes": round(proba[i][1], 4),
        }
        for i in range(len(pred_classes))
    ]


def output_fn(prediction, accept="application/json"):
    return json.dumps({"predictions": prediction}), "application/json"
