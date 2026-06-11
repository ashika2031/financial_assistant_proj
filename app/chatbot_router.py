"""
Chatbot router and orchestrator for the Financial Assistant.

Responsibilities:
  1. Classify the user's question into one of the intent buckets (route())
  2. Fetch data from the appropriate source only for that intent
  3. Generate a natural-language answer via Vertex AI ADK / Gemini,
     falling back to AWS Bedrock (Claude), then a rich rule-based summarizer
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum

import pandas as pd

from app.config import GCP_PROJECT, GCP_LOCATION, BEDROCK_MODEL_ID, AWS_REGION, COMPANY_NAME


# ─────────────────────────────────────────────────────────────────────────────
# 1. Intent types
# ─────────────────────────────────────────────────────────────────────────────

class RouteType(str, Enum):
    GREETING             = "greeting"
    META                 = "meta"           # app-info questions (data, models, cloud)
    FINANCIALS_DB        = "financials_db"
    PROPERTIES_DB        = "properties_db"
    PRESS_RELEASES       = "press_releases"
    SEC_EDGAR            = "sec_edgar"
    ML_PREDICTION        = "ml_prediction"
    GENERAL              = "general"
    OUT_OF_SCOPE_COMPANY = "out_of_scope_company"
    OUT_OF_SCOPE_YEAR    = "out_of_scope_year"


# ─── Greeting detection ───────────────────────────────────────────────────────

_GREETING_RE = re.compile(
    r"^\s*(hi+|hello+|hey+|howdy|yo+|sup|greetings|"
    r"good\s+(morning|afternoon|evening|day)|"
    r"how are you|how\s+r\s+u|what'?s\s+up)\b",
    re.IGNORECASE,
)

_EXACT_GREETINGS = {"hi", "hello", "hey", "yo", "sup", "howdy", "hiya", "heya"}


# ─── Out-of-scope companies ───────────────────────────────────────────────────

_OTHER_COMPANIES: dict[str, str] = {
    "google": "Google",       "alphabet": "Alphabet (Google)",
    "apple": "Apple",
    "amazon": "Amazon",
    "microsoft": "Microsoft",
    "tesla": "Tesla",
    "meta": "Meta",           "facebook": "Meta (Facebook)",
    "netflix": "Netflix",
    "nvidia": "Nvidia",
    "walmart": "Walmart",
    "jpmorgan": "JPMorgan",   "jp morgan": "JPMorgan",
    "berkshire": "Berkshire Hathaway",
    "realty income": "Realty Income",
    "simon property": "Simon Property Group",
    "equinix": "Equinix",
    "digital realty": "Digital Realty",
}


def _detect_other_company(q_lower: str) -> str | None:
    for keyword, display_name in _OTHER_COMPANIES.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", q_lower):
            return display_name
    return None


# ─── Available fiscal years (cached) ─────────────────────────────────────────

_available_fiscal_years_cache: set[int] | None = None


def _get_available_fiscal_years() -> set[int]:
    global _available_fiscal_years_cache
    if _available_fiscal_years_cache is None:
        years: set[int] = set()
        try:
            from app.postgres_queries import _load_csv_financials
            df = _load_csv_financials()
            years = set(df["fiscal_year"].dropna().astype(int).tolist())
        except Exception:
            pass
        if not years:
            try:
                from app.postgres_queries import execute_query
                df = execute_query("SELECT DISTINCT fiscal_year FROM financials")
                years = set(df["fiscal_year"].tolist())
            except Exception:
                pass
        _available_fiscal_years_cache = years or {2023, 2024}
    return _available_fiscal_years_cache


# ─── Keyword → route pattern table ───────────────────────────────────────────

_PATTERNS: list[tuple[list[str], RouteType]] = [
    (
        ["acquisition", "acqui", "merger", "expand", "expansion", "partnership",
         "press release", "recent press", "announcement", "announce", "announced",
         "sustainability", "green bond", "bond offering", "agreement", "new deal",
         "joint venture", "recently acquired", "latest news", "news release",
         "summarize latest", "company news", "recent news"],
        RouteType.PRESS_RELEASES,
    ),
    (
        ["revenue", "net income", "earnings", "profit", "expense", "expenses",
         "quarterly result", "q1", "q2", "q3", "q4", "annual result",
         "fiscal year", "financial result", "income", "ebitda", "margin",
         "last quarter", "last year", "operating income",
         "portfolio summary", "financial summary", "net margin",
         "which metro", "metro revenue", "highest revenue"],
        RouteType.FINANCIALS_DB,
    ),
    (
        ["property", "properties", "building", "warehouse", "industrial", "office",
         "retail", "multifamily", "square", "sqft", "sq ft", "metro area",
         "region", "portfolio location", "property performance",
         "chicago", "dallas", "los angeles", "new york", "atlanta",
         "seattle", "denver", "memphis", "phoenix", "houston"],
        RouteType.PROPERTIES_DB,
    ),
    (
        ["10-k", "10k", "10-q", "10q", "sec", "edgar", "filing", "annual report",
         "quarterly report", "regulatory", "gaap", "form 10", "latest filing",
         "latest sec", "show latest"],
        RouteType.SEC_EDGAR,
    ),
    (
        ["housing price", "house value", "california housing", "predict price",
         "home value", "median house", "regression model",
         "subscribe", "subscription", "bank marketing", "will subscribe",
         "predict whether", "predict subscription", "subscription probability",
         "classify", "classification", "predict", "prediction", "ml prediction",
         "machine learning model", "run model", "predict housing"],
        RouteType.ML_PREDICTION,
    ),
]

# ── Meta / app-info question detection ───────────────────────────────────────
# Each entry: (list_of_trigger_phrases, meta_type_tag)
_META_TRIGGERS: list[tuple[list[str], str]] = [
    (["what data", "data available", "data do you have", "what information",
      "data is available", "what datasets", "data sources"],
     "data_available"),
    (["is this real", "real prologis", "real data", "actual data",
      "is it real", "demo data", "sample data"],
     "is_real_data"),
    (["local fallback", "fallback mode", "offline mode", "without cloud",
      "without credentials", "no credentials"],
     "local_fallback"),
    (["what models", "models are used", "which models", "ml models used",
      "what ml", "models used"],
     "models_info"),
    (["are models running", "running locally", "running on sagemaker",
      "locally or on sagemaker", "local or cloud"],
     "models_running"),
    (["is sagemaker configured", "sagemaker configured", "sagemaker enabled",
      "sagemaker status", "is sagemaker"],
     "sagemaker_status"),
    (["what cloud services", "cloud services used", "which cloud",
      "cloud services are", "what cloud"],
     "cloud_services"),
    (["what is vertex", "vertex ai used", "vertex ai for", "what does vertex"],
     "vertex_info"),
    (["what is aws bedrock", "aws bedrock used", "bedrock used for",
      "what does bedrock", "what is bedrock"],
     "bedrock_info"),
]

# Help-intent triggers  (→ GENERAL with a help message)
_HELP_PATTERNS = [
    "what can you", "what do you do", "help me", "capabilities",
    "how do i", "what should i ask", "what topics", "show me what",
    "how can you help", "what can i ask", "what can i do",
]


@dataclass
class Route:
    route_type: RouteType
    extracted_params: dict


# ─────────────────────────────────────────────────────────────────────────────
# 2. Router
# ─────────────────────────────────────────────────────────────────────────────

def route(question: str) -> Route:
    q_lower = question.lower().strip()

    # ── Greeting ──
    if q_lower in _EXACT_GREETINGS or _GREETING_RE.match(q_lower):
        return Route(route_type=RouteType.GREETING, extracted_params={})

    # ── Help / capability questions ──
    if any(kw in q_lower for kw in _HELP_PATTERNS):
        return Route(route_type=RouteType.GENERAL, extracted_params={"help": True})

    # ── Meta / app-info questions ──
    for triggers, meta_type in _META_TRIGGERS:
        if any(t in q_lower for t in triggers):
            return Route(route_type=RouteType.META, extracted_params={"meta_type": meta_type})

    # ── Out-of-scope company ──
    other_company = _detect_other_company(q_lower)
    if other_company:
        return Route(
            route_type=RouteType.OUT_OF_SCOPE_COMPANY,
            extracted_params={"company": other_company},
        )

    # ── Score keyword patterns ──
    scores: dict[RouteType, int] = {rt: 0 for rt in RouteType}
    for keywords, route_type in _PATTERNS:
        for kw in keywords:
            if kw in q_lower:
                scores[route_type] += 1

    best = max(scores, key=lambda rt: scores[rt])
    if scores[best] == 0:
        best = RouteType.GENERAL

    # Tie-break: "propert" in query → prefer PROPERTIES_DB over FINANCIALS_DB
    if (
        best == RouteType.FINANCIALS_DB
        and scores[RouteType.PROPERTIES_DB] == scores[RouteType.FINANCIALS_DB]
        and "propert" in q_lower
    ):
        best = RouteType.PROPERTIES_DB

    params: dict = {}

    # ── Extract metro area ──
    metro_match = re.search(
        r"\b(chicago|dallas|los angeles|new york|atlanta|seattle|denver|memphis|"
        r"phoenix|houston|louisville|miami|columbus|inland empire|boston|"
        r"kansas city|baltimore|minneapolis|washington)\b",
        q_lower,
    )
    if metro_match:
        params["metro_area"] = metro_match.group(1).title()

    # ── Extract property type ──
    for ptype in ["industrial", "office", "retail", "multifamily"]:
        if ptype in q_lower:
            params["property_type"] = ptype.capitalize()
            break

    # ── Extract fiscal year ──
    year_match = re.search(r"\b(20\d{2})\b", question)
    if year_match:
        params["fiscal_year"] = int(year_match.group(1))

    # ── Extract quarter ──
    q_match = re.search(r"\bq([1-4])\b", q_lower)
    if q_match:
        params["quarter"] = int(q_match.group(1))

    # ── Press release keyword ──
    if best == RouteType.PRESS_RELEASES:
        for kw in ["acquisition", "earning", "sustainability", "partnership", "expansion", "finance"]:
            if kw in q_lower:
                # strip trailing 's' so "acquisitions" → "acquisition"
                params["keyword"] = kw
                break

    # ── Year validation for financials ──
    if best == RouteType.FINANCIALS_DB and "fiscal_year" in params:
        available = _get_available_fiscal_years()
        if params["fiscal_year"] not in available:
            return Route(
                route_type=RouteType.OUT_OF_SCOPE_YEAR,
                extracted_params={
                    "year": params["fiscal_year"],
                    "available_years": sorted(available),
                },
            )

    return Route(route_type=best, extracted_params=params)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Generative AI answer  (Vertex → Bedrock → rule-based)
# ─────────────────────────────────────────────────────────────────────────────

def _build_prompt(question: str, context_data: dict) -> str:
    ctx = json.dumps(context_data, indent=2, default=str)
    return (
        f"You are a financial analyst assistant for {COMPANY_NAME}, a leading industrial REIT.\n"
        f"You have access to the following retrieved data context:\n\n{ctx}\n\n"
        f"User question: {question}\n\n"
        "Provide a clear, concise, and insightful answer based on the data provided. "
        "Use specific numbers and metrics where available. "
        "Limit the response to 3-5 sentences. Be professional and direct."
    )


def _call_vertex(question: str, context_data: dict) -> str:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    model = GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(_build_prompt(question, context_data))
    return response.text


def _call_bedrock(question: str, context_data: dict) -> str:
    import boto3
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "messages": [{"role": "user", "content": _build_prompt(question, context_data)}],
    })
    response = client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def _fmt_currency(v: float) -> str:
    if v >= 1e9:
        return f"${v / 1e9:.2f}B"
    if v >= 1e6:
        return f"${v / 1e6:.1f}M"
    return f"${v:,.0f}"


def _rule_based_summary(question: str, context_data: dict) -> str:
    """Rich, natural-language offline summarizer."""
    rt = context_data.get("route", "general")
    data = context_data.get("data", [])
    params = context_data.get("params", {})

    # ── Greeting ──
    if rt == RouteType.GREETING or rt == "greeting":
        return (
            f"Hi! I'm Prologis AI, your financial intelligence assistant. "
            f"You can ask me about Prologis revenue, net income, property performance, "
            f"SEC filings, press releases, acquisitions, or ML predictions."
        )

    # ── General / help ──
    if rt == RouteType.GENERAL or rt == "general":
        return (
            "I can help with Prologis financials, property performance, SEC filings, "
            "press releases, acquisitions, and ML predictions.\n\n"
            "Try asking:\n"
            "- *\"What was net income in 2024?\"*\n"
            "- *\"Show industrial properties in Chicago\"*\n"
            "- *\"Any recent acquisitions?\"*\n"
            "- *\"Show latest 10-K report\"*\n"
            "- *\"Predict subscription probability\"*"
        )

    # ── ML redirect ──
    if rt == RouteType.ML_PREDICTION or rt == "ml_prediction":
        return (
            "I can help with that! Please open the **ML Predictions** page using the sidebar "
            "to enter model features and run the prediction.\n\n"
            "The page supports:\n"
            "- 🏠 **Housing Value Regression** — Predict California block group median values\n"
            "- 📊 **Subscription Classification** — Predict bank marketing subscription probability"
        )

    # ── Data error ──
    if isinstance(data, list) and data and "error" in data[0]:
        return (
            f"I couldn't retrieve data right now (connection issue: {data[0]['error']}). "
            "Please check the data connection and try again."
        )

    # ── Press releases ──
    if rt == "press_releases":
        releases = data if isinstance(data, list) else []
        if not releases:
            kw = params.get("keyword", "")
            topic = f" matching '{kw}'" if kw else ""
            return (
                f"No press releases found{topic}. "
                "Try asking about acquisitions, earnings, partnerships, or sustainability."
            )
        count = len(releases)
        first = releases[0]
        title = first.get("title", "")
        date = str(first.get("publish_date", ""))[:10]
        summary_snippet = str(first.get("summary", ""))[:140].rstrip()
        if len(str(first.get("summary", ""))) > 140:
            summary_snippet += "…"

        lead = f"I found {count} relevant press release{'s' if count > 1 else ''}."
        if title:
            lead += f" The most recent is **\"{title}\"** ({date})"
            if summary_snippet:
                lead += f", which reports: {summary_snippet}"
        lead += "."
        if count > 1:
            lead += f" {count - 1} additional release{'s are' if count > 2 else ' is'} shown in the table below."
        return lead

    # ── SEC filings ──
    if rt == "sec_edgar":
        if isinstance(data, list) and data:
            def _get_metric(rows: list[dict], name: str) -> tuple[float | None, str]:
                for row in rows:
                    if row.get("metric") == name:
                        return float(row.get("value", 0) or 0), str(row.get("end_date", ""))[:10]
                return None, ""

            ten_k = [d for d in data if d.get("form") == "10-K"]
            ten_q = [d for d in data if d.get("form") == "10-Q"]

            if ten_k:
                rev, period = _get_metric(ten_k, "Revenue")
                ni, _ = _get_metric(ten_k, "Net Income")
                oe, _ = _get_metric(ten_k, "Operating Expenses")
                parts = []
                if rev:
                    parts.append(f"Revenue of {_fmt_currency(rev)}")
                if ni:
                    parts.append(f"Net Income of {_fmt_currency(ni)}")
                if oe:
                    parts.append(f"Operating Expenses of {_fmt_currency(oe)}")
                metrics_str = ", ".join(parts) if parts else "key financial metrics"
                return (
                    f"The latest 10-K filing (period ending {period or '2023-12-31'}) "
                    f"for {COMPANY_NAME} reports {metrics_str}. "
                    "Full metrics are shown in the table below."
                )

            if ten_q:
                rev, period = _get_metric(ten_q, "Revenue")
                ni, _ = _get_metric(ten_q, "Net Income")
                parts = []
                if rev:
                    parts.append(f"Revenue of {_fmt_currency(rev)}")
                if ni:
                    parts.append(f"Net Income of {_fmt_currency(ni)}")
                metrics_str = ", ".join(parts) if parts else "key financial metrics"
                return (
                    f"The latest 10-Q filing (period ending {period}) "
                    f"for {COMPANY_NAME} reports {metrics_str}. "
                    "Full metrics are shown in the table below."
                )
        return f"No SEC EDGAR financial metrics were found for {COMPANY_NAME}."

    # ── Financials DB ──
    if rt == "financials_db":
        fiscal_year = params.get("fiscal_year", 2023)
        if isinstance(data, list) and data:
            total_revenue = sum(float(r.get("total_revenue", 0) or 0) for r in data)
            total_net_income = sum(float(r.get("total_net_income", 0) or 0) for r in data)
            total_expenses = sum(float(r.get("total_expenses", 0) or 0) for r in data)
            total_props = sum(int(r.get("property_count", 0) or 0) for r in data)
            margin = (total_net_income / total_revenue * 100) if total_revenue else 0
            return (
                f"In FY{fiscal_year}, the {COMPANY_NAME} sample portfolio generated "
                f"{_fmt_currency(total_revenue)} in revenue, "
                f"{_fmt_currency(total_net_income)} in net income, "
                f"and {_fmt_currency(total_expenses)} in operating expenses "
                f"across {total_props} properties, "
                f"with a net margin of {margin:.1f}%. "
                "A full breakdown by metro area is shown in the table below."
            )
        return (
            f"No financial records found for FY{fiscal_year}. "
            "The sample dataset may not include that year."
        )

    # ── Properties DB ──
    if rt == "properties_db":
        if isinstance(data, list) and data:
            count = len(data)
            metro = params.get("metro_area", "")
            ptype = params.get("property_type", "")

            if ptype and metro:
                label = f"{ptype.lower()} properties in {metro}"
            elif ptype:
                label = f"{ptype.lower()} properties"
            elif metro:
                label = f"properties in {metro}"
            else:
                label = "properties"

            # Best performer by revenue
            best_prop = None
            best_rev = -1.0
            for p in data:
                rev = float(p.get("revenue", 0) or p.get("total_revenue", 0) or 0)
                if rev > best_rev:
                    best_rev = rev
                    best_prop = p

            summary = f"I found {count} {label}."
            if best_prop and best_rev > 0:
                addr = best_prop.get("address") or best_prop.get("metro_area", "")
                ni = float(best_prop.get("net_income", 0) or best_prop.get("total_net_income", 0) or 0)
                summary += (
                    f" The strongest performer is **{addr}** "
                    f"with revenue of {_fmt_currency(best_rev)}"
                )
                if ni > 0:
                    summary += f" and net income of {_fmt_currency(ni)}"
                summary += "."
            else:
                total_sqft = sum(int(p.get("sq_footage", 0) or 0) for p in data)
                if total_sqft:
                    summary += f" Total portfolio footprint: {total_sqft:,} sq ft."
            summary += " Full details are shown in the table below."
            return summary
        return (
            "No properties matched your criteria. "
            "Try a different metro area or property type."
        )

    # ── Fallback ──
    return (
        "I'm not connected to that data. "
        "This assistant is focused on Prologis financials, property performance, "
        "SEC filings, press releases, acquisitions, and ML predictions.\n\n"
        "Try asking: *\"What was net income in 2023?\"* "
        "or *\"Show industrial properties in Chicago.\"*"
    )


def get_answer(question: str, context_data: dict) -> tuple[str, str]:
    """Return (answer_text, source_label). Falls back: Vertex → Bedrock → rule-based."""
    if GCP_PROJECT:
        try:
            return _call_vertex(question, context_data), "Vertex AI ADK (Gemini 1.5 Pro)"
        except Exception:
            pass

    try:
        return _call_bedrock(question, context_data), "AWS Bedrock (Claude 3 Sonnet)"
    except Exception:
        pass

    return _rule_based_summary(question, context_data), "Rule-based summarizer"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Data source label
# ─────────────────────────────────────────────────────────────────────────────

_SOURCE_LABELS: dict[RouteType, str] = {
    RouteType.GREETING:             "Prologis AI Assistant",
    RouteType.META:                 "Prologis AI Assistant",
    RouteType.GENERAL:              "Prologis AI Assistant",
    RouteType.ML_PREDICTION:        "ML Predictions Page",
    RouteType.FINANCIALS_DB:        "Source: Postgres Financials",
    RouteType.PROPERTIES_DB:        "Source: Property Database",
    RouteType.PRESS_RELEASES:       "Source: Press Releases",
    RouteType.SEC_EDGAR:            "Source: SEC Filing Metrics",
    RouteType.OUT_OF_SCOPE_COMPANY: "Out of scope",
    RouteType.OUT_OF_SCOPE_YEAR:    "Out of scope",
}


def _data_source_label(route_type: RouteType, extra: dict) -> str:
    return _SOURCE_LABELS.get(route_type, "Source: Prologis AI")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Orchestrator entry point used by the Streamlit UI
# ─────────────────────────────────────────────────────────────────────────────

def _df_to_records(df: pd.DataFrame) -> list[dict]:
    return df.to_dict(orient="records") if not df.empty else []


def handle_question(question: str, use_sagemaker: bool = False) -> dict:
    """
    Route a question to the right data source and return an answer plus
    supporting data for display.

    Returns:
        {
            "answer":           str,
            "source":           str,   # AI engine used
            "route":            str,   # RouteType value
            "data":             list[dict],
            "dataframe":        pd.DataFrame | None,
            "extra":            dict,
            "data_source_label": str,
        }
    """
    r = route(question)
    params = r.extracted_params

    def _no_data_response(answer: str, source: str = "Rule-based") -> dict:
        return {
            "answer": answer,
            "source": source,
            "route": r.route_type.value,
            "data": [],
            "dataframe": None,
            "extra": {},
            "data_source_label": _data_source_label(r.route_type, {}),
        }

    # ── Immediate responses that require no DB query ──────────────────────────

    if r.route_type == RouteType.GREETING:
        return _no_data_response(
            f"Hi! I'm Prologis AI, your financial intelligence assistant. "
            f"You can ask me about Prologis revenue, net income, property performance, "
            f"SEC filings, press releases, acquisitions, or ML predictions."
        )

    if r.route_type == RouteType.GENERAL:
        return _no_data_response(
            "I can help with Prologis financials, property performance, SEC filings, "
            "press releases, acquisitions, and ML predictions.\n\n"
            "Try asking:\n"
            "- *\"What was net income in 2024?\"*\n"
            "- *\"Show industrial properties in Chicago\"*\n"
            "- *\"Any recent acquisitions?\"*\n"
            "- *\"Show latest 10-K report\"*\n"
            "- *\"Predict subscription probability\"*"
        )

    if r.route_type == RouteType.META:
        sub = params.get("meta_type", "")
        _meta_answers: dict[str, str] = {
            "data_available": (
                "The app includes sample property-level records, sample financial metrics, "
                "selected SEC filing-style metrics, stored press release records, "
                "and local/cloud-ready ML prediction endpoints."
            ),
            "is_real_data": (
                "This is a Prologis-focused academic demo. It uses sample property-level data, "
                "selected SEC-style metrics, and mock press release records for demonstration purposes. "
                "It is not connected to live Prologis financial systems."
            ),
            "local_fallback": (
                "Local fallback mode means the app runs without live cloud credentials. "
                "It uses PostgreSQL, sample CSV data, and local scikit-learn models. "
                "SageMaker, Vertex AI, and Bedrock can be enabled later through environment variables."
            ),
            "models_info": (
                "The ML section uses a **Random Forest Regressor** for housing value prediction "
                "(California Housing dataset) and a **Logistic Regression classifier** for "
                "subscription prediction (Bank Marketing dataset)."
            ),
            "models_running": (
                "The deployed demo currently uses **local ML fallback**. "
                "Models run via scikit-learn on the Streamlit Cloud instance. "
                "SageMaker endpoints can be activated by adding AWS credentials and endpoint names "
                "through environment variables."
            ),
            "sagemaker_status": (
                "The deployed demo currently uses local ML fallback. "
                "SageMaker can be enabled by adding AWS credentials and endpoint names "
                "(`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `REGRESSION_ENDPOINT_NAME`, "
                "`CLASSIFICATION_ENDPOINT_NAME`) as environment variables."
            ),
            "cloud_services": (
                "The app is designed to connect to three cloud services:\n"
                "- ☁️ **Amazon SageMaker** — ML inference endpoints\n"
                "- 🤖 **Google Vertex AI (Gemini)** — LLM summarization\n"
                "- 🔵 **AWS Bedrock (Claude)** — LLM fallback\n\n"
                "All three fall back to local mode when credentials are not configured."
            ),
            "vertex_info": (
                "Vertex AI (Gemini 1.5 Pro) is used for generating natural language answers "
                "when a user asks a question. It summarizes retrieved financial data, property results, "
                "and press release content into a plain-English response."
            ),
            "bedrock_info": (
                "AWS Bedrock (Claude 3 Sonnet) is the secondary LLM fallback for generating "
                "natural language answers. It is used when Vertex AI credentials are not configured. "
                "If both are unavailable, the app falls back to a rule-based summarizer."
            ),
        }
        answer = _meta_answers.get(
            sub,
            "I can help with Prologis financials, property performance, SEC filings, "
            "press releases, acquisitions, and ML predictions.",
        )
        return _no_data_response(answer)

    if r.route_type == RouteType.ML_PREDICTION:
        return _no_data_response(
            "I can help with that! Please open the **ML Predictions** page using the sidebar "
            "to enter model features and run the prediction.\n\n"
            "The page supports:\n"
            "- 🏠 **Housing Value Regression** — Predict California block group median values\n"
            "- 📊 **Subscription Classification** — Predict bank marketing subscription probability"
        )

    if r.route_type == RouteType.OUT_OF_SCOPE_COMPANY:
        company = params.get("company", "that company")
        return _no_data_response(
            f"This assistant is currently configured for a Prologis-focused demo. "
            f"I do not have connected financial records for **{company}**. "
            "Please ask about Prologis financials, properties, SEC filings, "
            "press releases, or ML predictions.",
            source="Scope Guard",
        )

    if r.route_type == RouteType.OUT_OF_SCOPE_YEAR:
        year = params.get("year", "that year")
        available = params.get("available_years", sorted(_get_available_fiscal_years()))
        years_str = ", ".join(str(y) for y in available)
        return _no_data_response(
            f"No connected records are available for **{year}**. "
            f"Available fiscal years in this demo dataset are: **{years_str}**.",
            source="Scope Guard",
        )

    # ── Data-backed responses ─────────────────────────────────────────────────

    data_records: list[dict] = []
    df: pd.DataFrame | None = None
    extra: dict = {}

    try:
        if r.route_type == RouteType.PROPERTIES_DB:
            from app.postgres_queries import get_properties
            df = get_properties(
                metro_area=params.get("metro_area"),
                property_type=params.get("property_type"),
            )
            data_records = _df_to_records(df)

        elif r.route_type == RouteType.FINANCIALS_DB:
            from app.postgres_queries import get_portfolio_summary
            df = get_portfolio_summary(params.get("fiscal_year", 2023))
            data_records = _df_to_records(df)

        elif r.route_type == RouteType.PRESS_RELEASES:
            from app.press_release_loader import search_press_releases_json
            df = search_press_releases_json(
                keyword=params.get("keyword"),
                category=params.get("category"),
            )
            data_records = _df_to_records(df)

        elif r.route_type == RouteType.SEC_EDGAR:
            from app.sec_edgar import get_latest_financials
            df = get_latest_financials()
            data_records = _df_to_records(df)

    except Exception as fetch_err:
        data_records = [{"error": str(fetch_err)}]

    context = {
        "route": r.route_type.value,
        "params": params,
        "company": COMPANY_NAME,
        "data": data_records[:10],
    }
    answer, source = get_answer(question, context)

    return {
        "answer": answer,
        "source": source,
        "route": r.route_type.value,
        "data": data_records,
        "dataframe": df,
        "extra": extra,
        "data_source_label": _data_source_label(r.route_type, extra),
    }
