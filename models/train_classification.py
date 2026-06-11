"""
Train a Logistic Regression classifier on the Bank Marketing dataset (UCI).
Saves the model artifact (logistic_regression_classifier.pkl) and metrics.

Usage:
    python models/train_classification.py
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
)
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

MODELS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(MODELS_DIR), "data")
MODEL_PATH = os.path.join(MODELS_DIR, "logistic_regression_classifier.pkl")
METRICS_PATH = os.path.join(MODELS_DIR, "classification_metrics.json")
FEATURE_SCHEMA_PATH = os.path.join(MODELS_DIR, "feature_schema.json")

DATA_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00222/bank-additional-full.csv"
LOCAL_CSV = os.path.join(DATA_DIR, "bank_marketing.csv")


def load_data() -> pd.DataFrame:
    """Load the Bank Marketing dataset (UCI download -> local CSV -> synthetic)."""
    try:
        print("Downloading Bank Marketing dataset from UCI...")
        df = pd.read_csv(DATA_URL, sep=";")
        print(f"  Loaded {len(df)} rows, {df.shape[1]} columns from UCI")
        return df
    except Exception as e:
        print(f"  Download failed ({e})")
        if os.path.exists(LOCAL_CSV):
            print(f"  Loading local sample dataset: {LOCAL_CSV}")
            return pd.read_csv(LOCAL_CSV)
        print("  Generating synthetic fallback data...")
        return _generate_synthetic_data()


def _generate_synthetic_data() -> pd.DataFrame:
    np.random.seed(42)
    n = 5000
    duration = np.random.randint(0, 4000, n)
    poutcome_raw = np.random.choice(["nonexistent", "failure", "success"], n, p=[0.7, 0.2, 0.1])
    log_odds = -2.5 + 0.002 * duration + 1.5 * (poutcome_raw == "success").astype(int)
    prob_yes = 1 / (1 + np.exp(-log_odds))
    y = np.where(np.random.random(n) < prob_yes, "yes", "no")
    return pd.DataFrame({
        "age": np.random.randint(18, 80, n),
        "job": np.random.choice(["admin.", "technician", "services", "management", "blue-collar", "self-employed"], n),
        "marital": np.random.choice(["married", "single", "divorced"], n),
        "education": np.random.choice(["basic.4y", "basic.6y", "high.school", "university.degree"], n),
        "default": np.random.choice(["no", "yes", "unknown"], n),
        "housing": np.random.choice(["yes", "no", "unknown"], n),
        "loan": np.random.choice(["yes", "no", "unknown"], n),
        "contact": np.random.choice(["cellular", "telephone"], n),
        "month": np.random.choice(["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"], n),
        "day_of_week": np.random.choice(["mon","tue","wed","thu","fri"], n),
        "duration": duration,
        "campaign": np.random.randint(1, 30, n),
        "pdays": np.random.choice([999] + list(range(1, 30)), n),
        "previous": np.random.randint(0, 7, n),
        "poutcome": poutcome_raw,
        "emp.var.rate": np.random.uniform(-3.4, 1.4, n),
        "cons.price.idx": np.random.uniform(92.0, 94.8, n),
        "cons.conf.idx": np.random.uniform(-50.8, -26.9, n),
        "euribor3m": np.random.uniform(0.6, 5.0, n),
        "nr.employed": np.random.uniform(4963.6, 5228.1, n),
        "y": y,
    })


def preprocess(df: pd.DataFrame):
    y = (df["y"] == "yes").astype(int)
    X = df.drop(columns=["y"])

    categorical_cols = X.select_dtypes(include="object").columns.tolist()
    numeric_cols = X.select_dtypes(exclude="object").columns.tolist()
    schema = {"categorical": categorical_cols, "numeric": numeric_cols}

    preprocessor = ColumnTransformer(transformers=[
        ("num", StandardScaler(), numeric_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols),
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    return X_train, X_test, y_train, y_test, preprocessor, schema


def build_pipeline(preprocessor) -> Pipeline:
    return Pipeline([
        ("preprocessor", preprocessor),
        ("clf", LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs",
                                    class_weight="balanced", random_state=42, n_jobs=-1)),
    ])


def evaluate(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    return {
        "accuracy":  float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall":    float(recall_score(y_test, y_pred, zero_division=0)),
        "f1_score":  float(f1_score(y_test, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
    }


def train():
    df = load_data()
    X_train, X_test, y_train, y_test, preprocessor, schema = preprocess(df)
    print(f"  Train: {X_train.shape}, Test: {X_test.shape}")
    print(f"  Class balance (train): {y_train.value_counts().to_dict()}")

    print("Training Logistic Regression classifier...")
    pipeline = build_pipeline(preprocessor)
    pipeline.fit(X_train, y_train)

    metrics = evaluate(pipeline, X_test, y_test)
    print("\nEvaluation Metrics:")
    print(f"  Accuracy  : {metrics['accuracy']:.4f}")
    print(f"  Precision : {metrics['precision']:.4f}")
    print(f"  Recall    : {metrics['recall']:.4f}")
    print(f"  F1 Score  : {metrics['f1_score']:.4f}")
    print(f"  Confusion Matrix:\n    {metrics['confusion_matrix']}")

    joblib.dump(pipeline, MODEL_PATH)
    print(f"\nModel saved to: {MODEL_PATH}")

    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    with open(FEATURE_SCHEMA_PATH, "w") as f:
        json.dump(schema, f, indent=2)

    return pipeline, metrics


if __name__ == "__main__":
    train()
