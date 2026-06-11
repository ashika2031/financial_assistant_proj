"""
Train a Random Forest Regressor on the California Housing dataset.
Saves the model artifact (random_forest_regressor.pkl) and metrics.

Usage:
    python models/train_regression.py
"""

import os
import json
import numpy as np
import joblib
from sklearn.datasets import fetch_california_housing
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODELS_DIR, "random_forest_regressor.pkl")
METRICS_PATH = os.path.join(MODELS_DIR, "regression_metrics.json")
FEATURE_NAMES_PATH = os.path.join(MODELS_DIR, "feature_names.json")


def load_and_prepare_data():
    housing = fetch_california_housing(as_frame=True)
    X, y = housing.data, housing.target
    feature_names = list(X.columns)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test, feature_names


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestRegressor(
            n_estimators=100, max_depth=20,
            min_samples_split=5, min_samples_leaf=2,
            random_state=42, n_jobs=-1,
        )),
    ])


def evaluate(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    return {
        "RMSE": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "MAE":  float(mean_absolute_error(y_test, y_pred)),
        "R2":   float(r2_score(y_test, y_pred)),
    }


def train():
    print("Loading California Housing dataset...")
    X_train, X_test, y_train, y_test, feature_names = load_and_prepare_data()
    print(f"  Train: {X_train.shape}, Test: {X_test.shape}")

    print("Training Random Forest Regressor...")
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    metrics = evaluate(pipeline, X_test, y_test)
    print("\nEvaluation Metrics:")
    print(f"  RMSE : {metrics['RMSE']:.4f}")
    print(f"  MAE  : {metrics['MAE']:.4f}")
    print(f"  R2   : {metrics['R2']:.4f}")

    joblib.dump(pipeline, MODEL_PATH)
    print(f"\nModel saved to: {MODEL_PATH}")

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    with open(FEATURE_NAMES_PATH, "w") as f:
        json.dump(feature_names, f)

    return pipeline, metrics, feature_names


if __name__ == "__main__":
    train()
