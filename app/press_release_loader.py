"""Press release loader — reads from data/press_releases.json."""

from __future__ import annotations

import json
import os
import pandas as pd

from app.config import DATA_DIR

_JSON_PATH = os.path.join(DATA_DIR, "press_releases.json")


def load_press_releases_json() -> list[dict]:
    with open(_JSON_PATH) as f:
        return json.load(f)


def search_press_releases_json(keyword: str | None = None, category: str | None = None) -> pd.DataFrame:
    releases = load_press_releases_json()
    df = pd.DataFrame(releases)
    if keyword:
        kw = keyword.lower()
        mask = (
            df["title"].str.lower().str.contains(kw, na=False)
            | df["summary"].str.lower().str.contains(kw, na=False)
            | df["content"].str.lower().str.contains(kw, na=False)
        )
        df = df[mask]
    if category:
        df = df[df["category"].str.lower() == category.lower()]
    return df.reset_index(drop=True)


def get_press_release_categories() -> list[str]:
    releases = load_press_releases_json()
    return sorted({r["category"] for r in releases})


def extract_insights(df: pd.DataFrame | None = None) -> dict:
    """
    Extract simple structured insights from press releases:
    acquisitions, expansions, and quarterly business updates.
    """
    if df is None:
        df = pd.DataFrame(load_press_releases_json())

    insights = {
        "acquisitions": df[df["category"] == "Acquisition"][["title", "publish_date", "summary"]].to_dict("records"),
        "earnings_updates": df[df["category"] == "Earnings"][["title", "publish_date", "summary"]].to_dict("records"),
        "partnerships": df[df["category"] == "Partnership"][["title", "publish_date", "summary"]].to_dict("records"),
        "sustainability": df[df["category"] == "Sustainability"][["title", "publish_date", "summary"]].to_dict("records"),
    }
    return insights
