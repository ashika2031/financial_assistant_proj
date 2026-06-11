"""
Thin client wrapping Amazon SageMaker runtime invocations for both
the regression (housing price) and classification (subscription) endpoints.
"""

from __future__ import annotations

import json

from app.config import AWS_REGION, REGRESSION_ENDPOINT, CLASSIFICATION_ENDPOINT

LABEL_MAP = {0: "No Subscription", 1: "Will Subscribe"}


def _runtime_client():
    import boto3
    return boto3.client("sagemaker-runtime", region_name=AWS_REGION)


def invoke_regression_endpoint(features: dict) -> dict:
    """Send feature vector to the SageMaker housing-price regression endpoint."""
    runtime = _runtime_client()
    payload = json.dumps({"instances": [list(features.values())]})
    response = runtime.invoke_endpoint(
        EndpointName=REGRESSION_ENDPOINT,
        ContentType="application/json",
        Body=payload,
    )
    result = json.loads(response["Body"].read())
    pred = result["predictions"][0]
    if isinstance(pred, list):
        pred = pred[0]
    return {
        "predicted_value_100k": float(round(pred, 4)),
        "predicted_value_usd": float(round(pred * 100_000, 2)),
        "source": "sagemaker",
    }


def invoke_classification_endpoint(features: dict) -> dict:
    """Send customer feature dict to the SageMaker bank-marketing classification endpoint."""
    runtime = _runtime_client()
    payload = json.dumps({"instances": [features]})
    response = runtime.invoke_endpoint(
        EndpointName=CLASSIFICATION_ENDPOINT,
        ContentType="application/json",
        Body=payload,
    )
    result = json.loads(response["Body"].read())
    pred = result["predictions"][0]
    return {
        "prediction": pred.get("predicted_label", 0),
        "label": LABEL_MAP.get(pred.get("predicted_label", 0), "Unknown"),
        "probability_no":  float(pred.get("probability_no", 0.5)),
        "probability_yes": float(pred.get("probability_yes", 0.5)),
        "source": "sagemaker",
    }


def check_endpoint_status(endpoint_name: str) -> str:
    """Return the current status of a SageMaker endpoint (InService, Creating, Failed, etc.)."""
    client = boto3.client("sagemaker", region_name=AWS_REGION)
    response = client.describe_endpoint(EndpointName=endpoint_name)
    return response["EndpointStatus"]
