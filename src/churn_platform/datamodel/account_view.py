"""SPEC-3: Account View — tabela unificada 1 linha por account."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "account_id",
    "churn_flag",
    "industry",
    "mrr_amount",
}


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    for col in df.columns:
        if col.endswith("_acc"):
            base = col[:-4]
            if base in ("churn_flag", "plan_tier", "seats", "is_trial") and base + "_sub" in df.columns:
                rename_map[col] = base + "_account"
        if col.endswith("_sub"):
            base = col[:-4]
            if base in ("churn_flag", "plan_tier", "seats", "is_trial"):
                rename_map[col] = base + "_subscription"
    return df.rename(columns=rename_map)


def _ensure_churn_flag(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if "churn_flag" in col and col != "churn_flag":
            if col.endswith("_account") or col.endswith("_acc"):
                df["churn_flag"] = df[col].fillna(False).astype(bool)
                break
    if "churn_flag" not in df.columns:
        logger.warning("churn_flag não encontrado, usando False default")
        df["churn_flag"] = False
    return df


def validate_account_view(df: pd.DataFrame) -> list[str]:
    issues = []
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        issues.append(f"Colunas obrigatórias ausentes: {missing}")

    if df["account_id"].duplicated().any():
        n_dup = df["account_id"].duplicated().sum()
        issues.append(f"{n_dup} account_ids duplicados")

    return issues


def build(sources: dict[str, pd.DataFrame], merged: pd.DataFrame) -> pd.DataFrame:
    logger.info("=== Construindo Account View ===")

    df = merged.copy()
    df = _standardize_columns(df)
    df = _ensure_churn_flag(df)

    issues = validate_account_view(df)
    for issue in issues:
        logger.warning("Account View: %s", issue)

    logger.info("Account View: %s contas, %s colunas", len(df), len(df.columns))
    return df
