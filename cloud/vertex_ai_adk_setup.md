# Vertex AI ADK Chatbot Setup

The chatbot's primary reasoning layer is built on **Vertex AI** using the
`vertexai.generative_models` SDK (the Google Agent Development Kit / ADK
pattern), with a query router that decides which data source(s) feed the
prompt context.

## 1. Prerequisites

- A GCP project with the **Vertex AI API** enabled
- A service account with the `roles/aiplatform.user` role
- A downloaded service-account JSON key

## 2. Enable the API and authenticate

```bash
gcloud services enable aiplatform.googleapis.com --project=<your-gcp-project-id>
gcloud auth application-default login
```

Or, for a service account key:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

## 3. Configure environment variables

In `.env`:

```
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VERTEX_AGENT_ID=your-vertex-agent-id   # optional, for a managed ADK agent
```

## 4. How routing works

`app/chatbot_router.py` implements the routing + orchestration logic:

1. `route(question)` — pattern-matches the question against keywords/regex
   to classify it into one of:
   - `FINANCIALS_DB` — Postgres `Financials` table (revenue, net income, expenses)
   - `PROPERTIES_DB` — Postgres `Properties` table (portfolio, metro, sq ft)
   - `PRESS_RELEASES` — `data/press_releases.json` (acquisitions, partnerships, sustainability)
   - `SEC_EDGAR` — live 10-K/10-Q metrics from the SEC EDGAR XBRL API
   - `REGRESSION` / `CLASSIFICATION` — ML model inference
   - `GENERAL` — fallback, answered directly by the LLM

2. `handle_question(question, use_sagemaker=False)` pulls the relevant
   context data (a DataFrame or dict) based on the route, then calls
   `get_answer(question, context_data)`.

3. `get_answer()` tries, in order:
   - **Vertex AI** (`_call_vertex`) — `gemini-1.5-pro`, given the question
     and the retrieved context as a grounding prompt
   - **AWS Bedrock** (`_call_bedrock`) — fallback if Vertex AI is
     unavailable (see `cloud/bedrock_or_azure_integration.md`)
   - **Rule-based summarizer** (`_rule_based_summary`) — final offline
     fallback that formats the raw context data into a readable answer

## 5. Initializing Vertex AI in code

```python
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
model = GenerativeModel("gemini-1.5-pro")
response = model.generate_content(prompt)
```

This is implemented in `_call_vertex()` inside `app/chatbot_router.py`.

## 6. (Optional) Building a managed ADK Agent

For a fully managed conversational agent (Dialogflow CX / Vertex AI Agent
Builder), create an agent in the GCP console, configure a webhook that
calls the same `handle_question()` orchestration function as a Cloud
Function, and set `VERTEX_AGENT_ID` to the resulting agent ID. The Streamlit
chat page will continue to work standalone via the direct
`GenerativeModel` integration even if a managed agent is not configured.

## 7. Testing locally

```bash
python -c "from app.chatbot_router import handle_question; print(handle_question('What was Prologis revenue in 2023?'))"
```

If `GOOGLE_CLOUD_PROJECT` is not set or Vertex AI authentication fails, the
router automatically falls back to AWS Bedrock and then to the rule-based
summarizer, so the chatbot remains functional offline.
