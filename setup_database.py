"""
One-shot setup script for the Financial Assistant PostgreSQL database.

Creates the `properties`, `financials`, and `press_releases` tables
(sql/create_tables.sql) and loads the sample dataset
(sql/insert_sample_data.sql) if the `properties` table is empty.

Usage:
    python setup_database.py
"""

import sys

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.config import DATABASE_URL
from app.postgres_queries import init_db, execute_query, engine


def _apply_migrations() -> None:
    """Safe schema migrations — run before init_db so queries never hit missing columns."""
    with engine.connect() as conn:
        # Add fiscal_quarter if the financials table exists but the column is absent.
        conn.execute(text(
            "ALTER TABLE financials ADD COLUMN IF NOT EXISTS fiscal_quarter TEXT;"
        ))
        conn.commit()
        print("  Migration applied: financials.fiscal_quarter TEXT (IF NOT EXISTS).")


def main() -> None:
    print(f"Connecting to: {DATABASE_URL}")
    try:
        init_db()
        _apply_migrations()
    except OperationalError as e:
        print("\nERROR: Could not connect to PostgreSQL.")
        print("  - Is PostgreSQL running? (e.g. `docker ps` should show a postgres container)")
        print("  - Does DATABASE_URL in .env match your running instance?")
        print(f"\nDetails: {e}")
        sys.exit(1)

    props = execute_query("SELECT COUNT(*) AS n FROM properties").iloc[0]["n"]
    fins = execute_query("SELECT COUNT(*) AS n FROM financials").iloc[0]["n"]
    prs = execute_query("SELECT COUNT(*) AS n FROM press_releases").iloc[0]["n"]

    print("Database ready.")
    print(f"  properties:      {props} rows")
    print(f"  financials:      {fins} rows")
    print(f"  press_releases:  {prs} rows")


if __name__ == "__main__":
    main()
