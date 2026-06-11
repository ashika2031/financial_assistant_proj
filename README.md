# Prologis AI Financial Intelligence Platform

A Streamlit-based financial assistant for Prologis-style real estate portfolio analysis. Combines a conversational chatbot, property explorer, SEC filing metrics, press release intelligence, and ML predictions in a single dark-themed web app.

---

## Features

| Page | Description |
|---|---|
| **Chat Assistant** | Natural-language Q&A over financials, properties, SEC filings, and press releases |
| **Property Explorer** | Filter and visualize the property portfolio by metro area and property type |
| **Press Releases** | Search and browse Prologis news — earnings, acquisitions, partnerships |
| **SEC Filings** | Live financial metrics pulled from SEC EDGAR via XBRL API |
| **ML Predictions** | Housing value regression (Random Forest) and subscription classification (Logistic Regression) |
| **Portfolio Dashboard** | Consolidated KPIs, revenue by metro, P&L waterfall, and property-type breakdown |

---

## Tech Stack

- **Frontend**: Streamlit (single-file app, dark navy theme)
- **Database**: PostgreSQL via SQLAlchemy + psycopg2
- **ML**: scikit-learn (local fallback), Amazon SageMaker (cloud endpoints)
- **AI / Chat**: Vertex AI Agent Builder, AWS Bedrock (Claude fallback)
- **Data**: SEC EDGAR XBRL API, sample Prologis-style property records, stored press releases

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/ashika2031/financial_assistant_proj.git
cd financial_assistant_proj
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set DATABASE_URL and any cloud credentials
```

### 3. Start PostgreSQL

```bash
docker run --name financial-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=real_estate_db \
  -p 5432:5432 -d postgres:16
```

### 4. Set up the database

```bash
python setup_database.py
```

This creates the schema, applies migrations, and seeds sample data automatically.

### 5. Train ML models (optional — pre-trained models included)

```bash
python models/train_regression.py
python models/train_classification.py
```

### 6. Run the app

```bash
streamlit run app/streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## Project Structure

```
financial_assistant_proj/
├── app/
│   ├── streamlit_app.py          # Main Streamlit app (all pages)
│   ├── chatbot_router.py         # Question routing logic
│   ├── postgres_queries.py       # SQL query helpers
│   ├── press_release_loader.py   # JSON press release loader
│   ├── sagemaker_client.py       # AWS SageMaker client
│   ├── sec_edgar.py              # SEC EDGAR XBRL API client
│   └── config.py                 # Environment config
├── inference/
│   ├── regression_inference.py   # Housing price prediction
│   └── classification_inference.py  # Subscription classification
├── models/
│   ├── logistic_regression_classifier.pkl
│   ├── random_forest_regressor.pkl
│   ├── train_regression.py
│   └── train_classification.py
├── sql/
│   ├── create_tables.sql         # Schema DDL
│   └── insert_sample_data.sql    # Seed data
├── data/
│   └── press_releases.json       # Stored press release records
├── cloud/                        # AWS / GCP deployment guides
├── setup_database.py             # One-shot DB setup + migrations
└── requirements.txt
```

---

## ML Models

| Model | Dataset | Task | Key Metric |
|---|---|---|---|
| Random Forest Regressor | California Housing (20,640 samples) | Predict median house value | R² ≈ 0.81 |
| Logistic Regression | Bank Marketing | Predict term deposit subscription | Accuracy ≈ 0.91 |

Both models run locally by default. Toggle **"Use SageMaker"** on the ML Predictions page to route inference to cloud endpoints.

---

## Demo Note

This app uses sample Prologis-style property data, selected SEC-style financial metrics, stored press release records, and local/cloud-ready ML endpoints for **academic demonstration purposes**.

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | AWS credentials for SageMaker / Bedrock |
| `REGRESSION_ENDPOINT_NAME` | SageMaker regression endpoint name |
| `CLASSIFICATION_ENDPOINT_NAME` | SageMaker classification endpoint name |
| `GOOGLE_CLOUD_PROJECT` | GCP project for Vertex AI |
| `VERTEX_AGENT_ID` | Vertex AI Agent Builder agent ID |
