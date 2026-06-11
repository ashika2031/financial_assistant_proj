"""Central configuration for the Financial Assistant app."""

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR    = os.path.join(PROJECT_ROOT, "models")
DATA_DIR      = os.path.join(PROJECT_ROOT, "data")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/real_estate_db")

# AWS
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
SAGEMAKER_ROLE_ARN = os.getenv("SAGEMAKER_ROLE_ARN", "")
REGRESSION_ENDPOINT = os.getenv("REGRESSION_ENDPOINT_NAME", "housing-rf-regressor")
CLASSIFICATION_ENDPOINT = os.getenv("CLASSIFICATION_ENDPOINT_NAME", "bank-marketing-classifier")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

# GCP / Vertex AI
GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
VERTEX_AGENT_ID = os.getenv("VERTEX_AGENT_ID", "")

# SEC EDGAR
EDGAR_USER_AGENT = os.getenv("EDGAR_USER_AGENT", "Demo demo@example.com")
COMPANY_TICKER = os.getenv("REAL_ESTATE_COMPANY_TICKER", "PLD")
COMPANY_CIK = os.getenv("REAL_ESTATE_COMPANY_CIK", "0001045609")
COMPANY_NAME = "Prologis, Inc."

# Model artifact paths
REGRESSION_MODEL_PATH = os.path.join(MODELS_DIR, "random_forest_regressor.pkl")
CLASSIFICATION_MODEL_PATH = os.path.join(MODELS_DIR, "logistic_regression_classifier.pkl")
