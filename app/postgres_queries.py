"""PostgreSQL query helpers for the real estate financial assistant.

Falls back to CSV sample data when no database is reachable, so the app
runs fully on Streamlit Cloud without a configured DATABASE_URL.
"""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

from app.config import DATABASE_URL, PROJECT_ROOT

# ── DB engine (lazy — only created when actually needed) ──────────────────────
_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        from sqlalchemy import create_engine
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine


def _db_available() -> bool:
    """Return True if PostgreSQL is reachable."""
    try:
        from sqlalchemy import text
        with _get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def execute_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    from sqlalchemy import text
    with _get_engine().connect() as conn:
        result = conn.execute(text(sql), params or {})
        return pd.DataFrame(result.fetchall(), columns=result.keys())


def init_db():
    """Create schema and seed data if tables don't exist."""
    from sqlalchemy import text
    schema_path = os.path.join(PROJECT_ROOT, "sql", "create_tables.sql")
    seed_path = os.path.join(PROJECT_ROOT, "sql", "insert_sample_data.sql")
    with _get_engine().connect() as conn:
        with open(schema_path) as f:
            conn.execute(text(f.read()))
        conn.commit()
        count = conn.execute(text("SELECT COUNT(*) FROM properties")).scalar()
        if count == 0:
            with open(seed_path) as f:
                conn.execute(text(f.read()))
            conn.commit()


# ── CSV fallback helpers ───────────────────────────────────────────────────────

def _load_csv_properties() -> pd.DataFrame:
    path = os.path.join(PROJECT_ROOT, "data", "properties_sample.csv")
    return pd.read_csv(path)


def _load_csv_financials() -> pd.DataFrame:
    path = os.path.join(PROJECT_ROOT, "data", "financials_sample.csv")
    df = pd.read_csv(path)
    df["fiscal_quarter"] = df["fiscal_quarter"].where(df["fiscal_quarter"].notna(), None)
    return df


# ---------------------------------------------------------------------------
# Query helpers used by the chatbot and UI
# ---------------------------------------------------------------------------

def get_properties(metro_area: str | None = None, property_type: str | None = None) -> pd.DataFrame:
    if _db_available():
        where_clauses = []
        params: dict[str, Any] = {}
        if metro_area:
            where_clauses.append("LOWER(metro_area) LIKE :metro")
            params["metro"] = f"%{metro_area.lower()}%"
        if property_type:
            where_clauses.append("LOWER(property_type) = :ptype")
            params["ptype"] = property_type.lower()
        where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        return execute_query(f"SELECT * FROM properties {where} ORDER BY metro_area", params)

    # CSV fallback
    df = _load_csv_properties()
    if metro_area:
        df = df[df["metro_area"].str.lower().str.contains(metro_area.lower())]
    if property_type:
        df = df[df["property_type"].str.lower() == property_type.lower()]
    return df.sort_values("metro_area").reset_index(drop=True)


def get_financials_by_property(property_id: int | None = None, fiscal_year: int | None = None) -> pd.DataFrame:
    if _db_available():
        where_clauses = []
        params: dict[str, Any] = {}
        if property_id:
            where_clauses.append("f.property_id = :pid")
            params["pid"] = property_id
        if fiscal_year:
            where_clauses.append("f.fiscal_year = :yr")
            params["yr"] = fiscal_year
        where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        sql = f"""
            SELECT p.address, p.metro_area, p.property_type, p.sq_footage,
                   f.fiscal_year, f.fiscal_quarter, f.revenue, f.net_income, f.expenses
            FROM financials f
            JOIN properties p ON p.property_id = f.property_id
            {where}
            ORDER BY p.metro_area, f.fiscal_year, f.fiscal_quarter NULLS FIRST
        """
        return execute_query(sql, params)

    # CSV fallback
    props = _load_csv_properties()
    fins = _load_csv_financials()
    if property_id:
        fins = fins[fins["property_id"] == property_id]
    if fiscal_year:
        fins = fins[fins["fiscal_year"] == fiscal_year]
    merged = fins.merge(props, on="property_id", how="left")
    cols = ["address", "metro_area", "property_type", "sq_footage",
            "fiscal_year", "fiscal_quarter", "revenue", "net_income", "expenses"]
    return merged[cols].sort_values(["metro_area", "fiscal_year"]).reset_index(drop=True)


def get_portfolio_summary(fiscal_year: int = 2023) -> pd.DataFrame:
    if _db_available():
        sql = """
            SELECT
                p.metro_area,
                p.property_type,
                COUNT(DISTINCT p.property_id)          AS property_count,
                SUM(p.sq_footage)                       AS total_sqft,
                SUM(f.revenue)                          AS total_revenue,
                SUM(f.net_income)                       AS total_net_income,
                SUM(f.expenses)                         AS total_expenses
            FROM properties p
            JOIN financials f ON f.property_id = p.property_id
            WHERE f.fiscal_year = :yr AND f.fiscal_quarter IS NULL
            GROUP BY p.metro_area, p.property_type
            ORDER BY total_revenue DESC
        """
        return execute_query(sql, {"yr": fiscal_year})

    # CSV fallback
    props = _load_csv_properties()
    fins = _load_csv_financials()
    annual = fins[(fins["fiscal_year"] == fiscal_year) & (fins["fiscal_quarter"].isna())]
    merged = annual.merge(props, on="property_id", how="left")
    summary = (
        merged.groupby(["metro_area", "property_type"])
        .agg(
            property_count=("property_id", "nunique"),
            total_sqft=("sq_footage", "sum"),
            total_revenue=("revenue", "sum"),
            total_net_income=("net_income", "sum"),
            total_expenses=("expenses", "sum"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )
    return summary


def search_press_releases(keyword: str | None = None, category: str | None = None) -> pd.DataFrame:
    if not _db_available():
        return pd.DataFrame()
    where_clauses = []
    params: dict[str, Any] = {}
    if keyword:
        where_clauses.append(
            "(LOWER(title) LIKE :kw OR LOWER(summary) LIKE :kw OR LOWER(content) LIKE :kw)"
        )
        params["kw"] = f"%{keyword.lower()}%"
    if category:
        where_clauses.append("LOWER(category) = :cat")
        params["cat"] = category.lower()
    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    return execute_query(
        f"SELECT * FROM press_releases {where} ORDER BY publish_date DESC", params
    )


def get_quarterly_trend(property_id: int) -> pd.DataFrame:
    if _db_available():
        return execute_query(
            """
            SELECT fiscal_year, fiscal_quarter, revenue, net_income, expenses
            FROM financials
            WHERE property_id = :pid AND fiscal_quarter IS NOT NULL
            ORDER BY fiscal_year, fiscal_quarter
            """,
            {"pid": property_id},
        )
    fins = _load_csv_financials()
    return fins[(fins["property_id"] == property_id) & (fins["fiscal_quarter"].notna())]
