"""PostgreSQL query helpers for the real estate financial assistant."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text

from app.config import DATABASE_URL, PROJECT_ROOT

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def execute_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        return pd.DataFrame(result.fetchall(), columns=result.keys())


def init_db():
    """Create schema and seed data if tables don't exist."""
    schema_path = os.path.join(PROJECT_ROOT, "sql", "create_tables.sql")
    seed_path = os.path.join(PROJECT_ROOT, "sql", "insert_sample_data.sql")
    with engine.connect() as conn:
        with open(schema_path) as f:
            conn.execute(text(f.read()))
        conn.commit()
        count = conn.execute(text("SELECT COUNT(*) FROM properties")).scalar()
        if count == 0:
            with open(seed_path) as f:
                conn.execute(text(f.read()))
            conn.commit()


# ---------------------------------------------------------------------------
# Query helpers used by the chatbot and UI
# ---------------------------------------------------------------------------

def get_properties(metro_area: str | None = None, property_type: str | None = None) -> pd.DataFrame:
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


def get_financials_by_property(property_id: int | None = None, fiscal_year: int | None = None) -> pd.DataFrame:
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


def get_portfolio_summary(fiscal_year: int = 2023) -> pd.DataFrame:
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


def search_press_releases(keyword: str | None = None, category: str | None = None) -> pd.DataFrame:
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
    return execute_query(
        """
        SELECT fiscal_year, fiscal_quarter, revenue, net_income, expenses
        FROM financials
        WHERE property_id = :pid AND fiscal_quarter IS NOT NULL
        ORDER BY fiscal_year, fiscal_quarter
        """,
        {"pid": property_id},
    )
