"""SPEC-2 REQ-2-004: Clean e transformação de datas."""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

DATE_COLUMNS = {
    "ravenstack_accounts.csv": ["signup_date"],
    "ravenstack_subscriptions.csv": ["start_date", "end_date"],
    "ravenstack_feature_usage.csv": ["usage_date"],
    "ravenstack_support_tickets.csv": ["submitted_at", "closed_at"],
    "ravenstack_churn_events.csv": ["churn_date"],
}


def _infer_source_name(path: str) -> str:
    return path.split("/")[-1]


def clean_dates(sources: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    for name, df in sources.items():
        source_name = _infer_source_name(str(name))
        date_cols = DATE_COLUMNS.get(source_name, [])
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                n_null = df[col].isna().sum()
                if n_null > 0:
                    logger.warning("  %s.%s: %s nulls após parse", name, col, n_null)
    return sources


def clean_booleans(sources: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    for name, df in sources.items():
        for col in df.columns:
            if df[col].dtype == "object" and df[col].nunique() <= 2:
                unique_vals = df[col].dropna().unique()
                if set(unique_vals).issubset({True, False, "True", "False", "true", "false", 0, 1}):
                    df[col] = df[col].astype(bool)
    return sources


def run(sources: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    logger.info("=== Limpeza de dados ===")
    sources = clean_dates(sources)
    sources = clean_booleans(sources)
    return sources
