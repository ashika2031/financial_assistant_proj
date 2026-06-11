"""
Chatbot router and orchestrator for the Financial Assistant.

Responsibilities:
  1. Classify the user's natural language question (route())
  2. Fetch data from the appropriate source: Postgres, SEC EDGAR,
     press releases, or SageMaker ML endpoints (handle_question())
  3. Generate a natural-language answer via Vertex AI ADK / Gemini,
     falling back to AWS Bedrock (Claude), then a rule-based summarizer
     (get_answer())
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum

import pandas as pd

from app.config import GCP_PROJECT, GCP_LOCATION, BEDROCK_MODEL_ID, AWS_REGION, COMPANY_NAME


# ─────────────────────────────────────────────────────────────────────────────
# 1. Query routing
# ─────────────────────────────────────────────────────────────────────────────

class RouteType(str, Enum):
    FINANCIALS_DB = "financials_db"
    PROPERTIES_DB = "properties_db"
    PRESS_RELEASES = "press_releases"
    SEC_EDGAR      = "sec_edgar"
    REGRESSION     = "regression"
    CLASSIFICATION = "classification"
    GENERAL        = "general"
    OUT_OF_SCOPE_COMPANY = "out_of_scope_company"
    OUT_OF_SCOPE_YEAR    = "out_of_scope_year"


# Companies other than the one this assistant is configured for. If any of
# these are mentioned, the question is out of scope and must not be answered
# with Prologis data.
_OTHER_COMPANIES: dict[str, str] = {
    "google": "Google", "alphabet": "Alphabet (Google)",
    "apple": "Apple",
    "amazon": "Amazon",
    "microsoft": "Microsoft",
    "tesla": "Tesla",
    "meta": "Meta", "facebook": "Meta (Facebook)",
    "netflix": "Netflix",
    "nvidia": "Nvidia",
    "walmart": "Walmart",
    "jpmorgan": "JPMorgan", "jp morgan": "JPMorgan",
    "berkshire": "Berkshire Hathaway",
    "realty income": "Realty Income",
    "simon property": "Simon Property Group",
    "equinix": "Equinix",
    "digital realty": "Digital Realty",
}


def _detect_other_company(q_lower: str) -> str | None:
    """Return the display name of a non-Prologis company mentioned in the question, if any."""
    for keyword, display_name in _OTHER_COMPANIES.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", q_lower):
            return display_name
    return None


_available_fiscal_years_cache: set[int] | None = None


def _get_available_fiscal_years() -> set[int]:
    """Return the set of fiscal years present in the financials table (cached)."""
    global _available_fiscal_years_cache
    if _available_fiscal_years_cache is None:
        try:
            from app.postgres_queries import execute_query
            df = execute_query("SELECT DISTINCT fiscal_year FROM financials")
            _available_fiscal_years_cache = set(df["fiscal_year"].tolist())
        except Exception:
            _available_fiscal_years_cache = {2023}
    return _available_fiscal_years_cache


@dataclass
class Route:
    route_type: RouteType
    extracted_params: dict


_PATTERNS: list[tuple[list[str], RouteType]] = [
    (["acquisition", "acqui", "merger", "expand", "partnership", "announce", "press release",
      "news", "recently", "sustainability", "bond", "offering", "amazon", "agreement"],
     RouteType.PRESS_RELEASES),
    (["revenue", "net income", "earnings", "profit", "expense", "quarterly", "q1", "q2",
      "q3", "q4", "annual", "fiscal", "financial result"],
     RouteType.FINANCIALS_DB),
    (["property", "properties", "building", "warehouse", "industrial", "office", "square",
      "sqft", "sq ft", "metro", "region", "chicago", "dallas", "los angeles", "new york",
      "atlanta", "seattle", "denver", "memphis", "phoenix", "houston"],
     RouteType.PROPERTIES_DB),
    (["10-k", "10k", "10-q", "10q", "sec", "edgar", "filing", "annual report",
      "regulatory", "gaap"],
     RouteType.SEC_EDGAR),
    (["housing price", "house value", "california housing", "predict price",
      "home value", "median house", "regression"],
     RouteType.REGRESSION),
    (["subscribe", "subscription", "bank marketing", "customer", "will buy",
      "classify", "classification", "predict whether"],
     RouteType.CLASSIFICATION),
]


def route(question: str) -> Route:
    """Classify a natural-language question and extract routing parameters."""
    q_lower = question.lower()

    other_company = _detect_other_company(q_lower)
    if other_company:
        return Route(route_type=RouteType.OUT_OF_SCOPE_COMPANY, extracted_params={"company": other_company})

    scores: dict[RouteType, int] = {rt: 0 for rt in RouteType}

    for keywords, route_type in _PATTERNS:
        for kw in keywords:
            if kw in q_lower:
                scores[route_type] += 1

    best = max(scores, key=lambda rt: scores[rt])
    if scores[best] == 0:
        best = RouteType.GENERAL

    params: dict = {}

    metro_match = re.search(
        r"\b(chicago|dallas|los angeles|new york|atlanta|seattle|denver|memphis|"
        r"phoenix|houston|louisville|miami|columbus|inland empire|boston|kansas city|"
        r"baltimore|minneapolis|washington)\b",
        q_lower,
    )
    if metro_match:
        params["metro_area"] = metro_match.group(1).title()

    for ptype in ["industrial", "office", "retail", "multifamily"]:
        if ptype in q_lower:
            params["property_type"] = ptype.capitalize()
            break

    year_match = re.search(r"\b(20\d{2})\b", question)
    if year_match:
        params["fiscal_year"] = int(year_match.group(1))

    q_match = re.search(r"\bq([1-4])\b", q_lower)
    if q_match:
        params["quarter"] = int(q_match.group(1))

    if best == RouteType.PRESS_RELEASES:
        for kw in ["acquisition", "earnings", "sustainability", "partnership", "finance"]:
            if kw in q_lower:
                params["keyword"] = kw
                break

    if best == RouteType.FINANCIALS_DB and "fiscal_year" in params:
        if params["fiscal_year"] not in _get_available_fiscal_years():
            return Route(route_type=RouteType.OUT_OF_SCOPE_YEAR, extracted_params={"year": params["fiscal_year"]})

    return Route(route_type=best, extracted_params=params)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Generative AI answer (Vertex AI ADK -> Bedrock -> rule-based)
# ─────────────────────────────────────────────────────────────────────────────

def _build_prompt(question: str, context_data: dict) -> str:
    ctx = json.dumps(context_data, indent=2, default=str)
    return f"""You are a financial analyst assistant for {COMPANY_NAME}, a leading industrial REIT.
You have access to the following retrieved data context:

{ctx}

User question: {question}

Provide a clear, concise, and insightful answer based on the data provided.
Use specific numbers and metrics where available. Limit the response to 3-5 sentences."""


def _call_vertex(question: str, context_data: dict) -> str:
    """Call Vertex AI ADK / Gemini for a natural language answer."""
    import vertexai
    from vertexai.generative_models import GenerativeModel

    vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    model = GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(_build_prompt(question, context_data))
    return response.text


def _call_bedrock(question: str, context_data: dict) -> str:
    """Fallback: AWS Bedrock (Claude) for summarization/generation."""
    import boto3

    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 512,
            "messages": [{"role": "user", "content": _build_prompt(question, context_data)}],
        }
    )
    response = client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def _rule_based_summary(question: str, context_data: dict) -> str:
    """Offline fallback that summarizes context_data without an LLM."""
    rt = context_data.get("route", "general")
    data = context_data.get("data", {})

    if isinstance(data, list) and data and "error" in data[0]:
        return (
            f"I couldn't retrieve data for {COMPANY_NAME} right now "
            f"(connection issue: {data[0]['error']}). "
            "Please check the data connection and try again."
        )

    if rt == "press_releases":
        releases = data if isinstance(data, list) else []
        if not releases:
            return "No press releases matched your query."
        lines = [f"- **{r.get('title','')}** ({r.get('publish_date','')}): {r.get('summary','')}" for r in releases[:3]]
        return "Here are the most relevant press releases:\n\n" + "\n".join(lines)

    if rt == "sec_edgar":
        if isinstance(data, list) and data:
            first = data[0]
            metric = first.get("metric", "")
            value = first.get("value", 0)
            form = first.get("form", "")
            if metric:
                return f"The latest reported {metric} ({form}) for {COMPANY_NAME} was ${value:,.0f}."
        return f"No SEC EDGAR financial metrics were found for {COMPANY_NAME}."

    if rt == "financials_db":
        fiscal_year = context_data.get("params", {}).get("fiscal_year", 2023)
        if isinstance(data, list) and data:
            total_revenue = sum(float(r.get("total_revenue", 0) or 0) for r in data)
            total_net_income = sum(float(r.get("total_net_income", 0) or 0) for r in data)
            total_expenses = sum(float(r.get("total_expenses", 0) or 0) for r in data)
            total_props = sum(int(r.get("property_count", 0) or 0) for r in data)
            margin = (total_net_income / total_revenue * 100) if total_revenue else 0
            return (
                f"{COMPANY_NAME} reported total revenue of ${total_revenue:,.0f} in {fiscal_year} "
                f"across {total_props} properties. Net income was ${total_net_income:,.0f} "
                f"and operating expenses were ${total_expenses:,.0f}, "
                f"for a net margin of {margin:.1f}%."
            )
        return f"No financial records were found for {COMPANY_NAME} in {fiscal_year}. Make sure the database is set up (see sql/create_tables.sql and sql/insert_sample_data.sql)."

    if rt == "properties_db":
        if isinstance(data, list) and data:
            count = len(data)
            total_sqft = sum(int(p.get("sq_footage", 0) or 0) for p in data)
            metros = sorted({p.get("metro_area", "") for p in data if p.get("metro_area")})
            types = sorted({p.get("property_type", "") for p in data if p.get("property_type")})
            metro_str = ", ".join(metros[:5]) + ("…" if len(metros) > 5 else "")
            type_str = ", ".join(types)
            return (
                f"Found {count} {type_str or 'properties'} totaling {total_sqft:,} sq ft "
                f"in {metro_str or 'the portfolio'}. Details are shown in the table below."
            )
        return "No properties matched your criteria. Try a different metro area or property type."

    if rt == "regression":
        if isinstance(data, list) and data:
            val = data[0].get("predicted_value_usd")
            if val:
                return f"The predicted median housing value is ${val:,.0f}."
        return "Housing value prediction generated. See results below."

    if rt == "classification":
        if isinstance(data, list) and data:
            label = data[0].get("label")
            prob = data[0].get("probability_yes", 0) * 100
            if label:
                return f"Prediction: **{label}** with a {prob:.1f}% probability of subscribing."
        return "Subscription prediction generated. See results below."

    return (
        f"I found relevant information for your question about {COMPANY_NAME}. "
        "Please review the data displayed below."
    )


def get_answer(question: str, context_data: dict) -> tuple[str, str]:
    """
    Returns (answer_text, source_label) where source_label is one of:
    'Vertex AI (Gemini)', 'AWS Bedrock (Claude)', 'Rule-based'
    """
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
# 3. Orchestrator entry point used by the Streamlit UI
# ─────────────────────────────────────────────────────────────────────────────

def _df_to_records(df: pd.DataFrame) -> list[dict]:
    return df.to_dict(orient="records") if not df.empty else []


def _data_source_label(route_type: RouteType, extra: dict) -> str:
    """Human-readable label for where the answer's data came from."""
    if route_type == RouteType.FINANCIALS_DB:
        return "Postgres Financials"
    if route_type == RouteType.PROPERTIES_DB:
        return "Postgres Properties"
    if route_type == RouteType.PRESS_RELEASES:
        return "Press Releases"
    if route_type == RouteType.SEC_EDGAR:
        return "SEC Filings"
    if route_type == RouteType.REGRESSION:
        ml = extra.get("ml_result", {})
        return "SageMaker Regression" if ml.get("source") == "sagemaker" else "Local Regression Model"
    if route_type == RouteType.CLASSIFICATION:
        ml = extra.get("ml_result", {})
        return "SageMaker Classification" if ml.get("source") == "sagemaker" else "Local Classification Model"
    return "Press Releases & Postgres Financials"


def handle_question(question: str, use_sagemaker: bool = False) -> dict:
    """
    Route a question to the right data source / ML model and return an
    answer plus supporting data for display.

    Returns:
        {
            "answer": str,
            "source": str,
            "route": str,
            "data": list[dict],
            "dataframe": pd.DataFrame | None,
            "extra": dict,
            "data_source_label": str,
        }
    """
    r = route(question)
    params = r.extracted_params

    if r.route_type == RouteType.OUT_OF_SCOPE_COMPANY:
        company = params.get("company", "that company")
        answer = (
            f"This assistant is currently configured for Prologis only. "
            f"I do not have connected financial records for {company}. "
            "Please ask about Prologis financials, properties, SEC filings, press releases, or ML predictions."
        )
        return {
            "answer": answer, "source": "Scope Guard", "route": r.route_type.value,
            "data": [], "dataframe": None, "extra": {}, "data_source_label": "Out of scope",
        }

    if r.route_type == RouteType.OUT_OF_SCOPE_YEAR:
        answer = (
            "No connected records are available for that year. "
            "The current dataset contains only the loaded fiscal years and sample records."
        )
        return {
            "answer": answer, "source": "Scope Guard", "route": r.route_type.value,
            "data": [], "dataframe": None, "extra": {}, "data_source_label": "Out of scope",
        }

    data_records: list[dict] = []
    df: pd.DataFrame | None = None
    extra: dict = {}

    try:
        if r.route_type == RouteType.PROPERTIES_DB:
            from app.postgres_queries import get_properties
            df = get_properties(metro_area=params.get("metro_area"), property_type=params.get("property_type"))
            data_records = _df_to_records(df)

        elif r.route_type == RouteType.FINANCIALS_DB:
            from app.postgres_queries import get_portfolio_summary
            df = get_portfolio_summary(params.get("fiscal_year", 2023))
            data_records = _df_to_records(df)

        elif r.route_type == RouteType.PRESS_RELEASES:
            from app.press_release_loader import search_press_releases_json
            df = search_press_releases_json(keyword=params.get("keyword"), category=params.get("category"))
            data_records = _df_to_records(df)

        elif r.route_type == RouteType.SEC_EDGAR:
            from app.sec_edgar import get_latest_financials
            df = get_latest_financials()
            data_records = _df_to_records(df)

        elif r.route_type == RouteType.REGRESSION:
            from inference.regression_inference import predict, DEFAULT_SAMPLE
            result = predict(DEFAULT_SAMPLE, use_sagemaker=use_sagemaker)
            data_records = [result]
            df = pd.DataFrame([result])
            extra["ml_result"] = result

        elif r.route_type == RouteType.CLASSIFICATION:
            from inference.classification_inference import predict, DEFAULT_SAMPLE
            result = predict(DEFAULT_SAMPLE, use_sagemaker=use_sagemaker)
            data_records = [result]
            df = pd.DataFrame([result])
            extra["ml_result"] = result

        else:
            from app.press_release_loader import search_press_releases_json
            from app.postgres_queries import get_portfolio_summary
            pr_df = search_press_releases_json()
            fin_df = get_portfolio_summary(2023)
            data_records = _df_to_records(pr_df.head(3)) + _df_to_records(fin_df.head(5))
            df = pr_df

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
