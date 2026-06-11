#!/usr/bin/env python3
"""
DealPriority — reproducible scoring pipeline

This script rebuilds the final ranked opportunity file from the original
Challenge 003 CSVs.

Expected inputs:
  data/raw/sales_pipeline.csv
  data/raw/accounts.csv
  data/raw/products.csv
  data/raw/sales_teams.csv

Default output:
  data/output/ranked_open_deals_final.csv

Run:
  python scripts/generate_scores.py
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def normalize_product_name(value: Any, product_dimension: pd.Series | None = None) -> Any:
    """
    Normalizes product names before joining sales_pipeline -> products.

    Known source inconsistency:
      sales_pipeline.product = GTXPro
      products.product       = GTX Pro
    """
    if pd.isna(value):
        return value

    original = str(value).strip()

    if product_dimension is not None:
        compact_original = "".join(ch for ch in original.lower() if ch.isalnum())
        compact_to_canonical = {
            "".join(ch for ch in str(product).strip().lower() if ch.isalnum()): str(product).strip()
            for product in product_dimension.dropna().unique()
        }
        if compact_original in compact_to_canonical:
            return compact_to_canonical[compact_original]

    if original.lower().replace(" ", "") == "gtxpro":
        return "GTX Pro"

    return original


def safe_rate_map(closed_df: pd.DataFrame, group_col: str, default_value: float) -> pd.Series:
    return closed_df.groupby(group_col)["won_flag"].mean()


def positive_reasons(row: pd.Series, thresholds: dict[str, float]) -> list[str]:
    reasons: list[str] = []

    if row.get("stage_weight", 0) >= 0.25:
        reasons.append("estágio avançado no funil")
    if row.get("seller_win_rate", 0) >= thresholds["seller_high"]:
        reasons.append("bom histórico do vendedor")
    if row.get("product_win_rate", 0) >= thresholds["product_high"]:
        reasons.append("produto com bom desempenho histórico")
    if row.get("regional_win_rate", 0) >= thresholds["regional_high"]:
        reasons.append("região com boa conversão histórica")
    if row.get("manager_win_rate", 0) >= thresholds["manager_high"]:
        reasons.append("histórico do manager acima do ideal")

    if not reasons:
        reasons.append("deal ainda ativo no pipeline")
    if len(reasons) == 1:
        reasons.append("oportunidade elegível para acompanhamento comercial")

    return reasons[:2]


def risk_reasons(row: pd.Series, thresholds: dict[str, float]) -> list[str]:
    risks: list[str] = []

    if bool(row.get("aging_risk_flag", False)):
        risks.append("deal envelhecendo acima do ideal")
    if row.get("seller_win_rate", 1) <= thresholds["seller_low"]:
        risks.append("histórico do vendedor abaixo do ideal")
    if row.get("product_win_rate", 1) <= thresholds["product_low"]:
        risks.append("produto com baixa conversão histórica")
    if row.get("regional_win_rate", 1) <= thresholds["regional_low"]:
        risks.append("região com baixa conversão histórica")
    if row.get("manager_win_rate", 1) <= thresholds["manager_low"]:
        risks.append("histórico do manager abaixo do ideal")
    if pd.isna(row.get("account")):
        risks.append("conta ausente na origem dos dados")

    if not risks:
        risks.append("sem risco crítico identificado")
    if len(risks) == 1:
        risks.append("monitorar evolução do próximo passo")

    return risks[:2]


def recommended_action(row: pd.Series) -> str:
    label = row.get("priority_label")

    if label == "Foco Agora":
        if bool(row.get("aging_risk_flag", False)):
            return "recuperar urgência e definir próximo passo hoje"
        return "avançar para o próximo passo hoje"

    if label == "Nutrir":
        return "revisar próximos passos nesta semana e manter cadência"

    return "decidir se vale recuperar ou encerrar esta semana"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--out", default="data/output/ranked_open_deals_final.csv")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sales_pipeline = pd.read_csv(raw_dir / "sales_pipeline.csv")
    accounts = pd.read_csv(raw_dir / "accounts.csv")
    products = pd.read_csv(raw_dir / "products.csv")
    sales_teams = pd.read_csv(raw_dir / "sales_teams.csv")

    sales_pipeline["engage_date"] = pd.to_datetime(sales_pipeline["engage_date"], errors="coerce")
    sales_pipeline["close_date"] = pd.to_datetime(sales_pipeline["close_date"], errors="coerce")

    sales_pipeline["product_normalized"] = sales_pipeline["product"].apply(
        lambda value: normalize_product_name(value, products["product"])
    )

    merged = (
        sales_pipeline
        .merge(accounts, on="account", how="left")
        .merge(sales_teams, on="sales_agent", how="left")
        .merge(products, left_on="product_normalized", right_on="product", how="left", suffixes=("", "_product_dim"))
    )

    merged["product"] = merged["product_normalized"]

    if merged["opportunity_id"].duplicated().any():
        duplicated = merged.loc[merged["opportunity_id"].duplicated(), "opportunity_id"].head(10).tolist()
        raise ValueError(f"Join created duplicated opportunity_id values. Examples: {duplicated}")

    if len(merged) != len(sales_pipeline):
        raise ValueError(f"Row count changed after joins: input={len(sales_pipeline)}, merged={len(merged)}")

    merged["deal_status_group"] = np.select(
        [merged["deal_stage"].eq("Won"), merged["deal_stage"].eq("Lost")],
        ["won", "lost"],
        default="open",
    )

    closed = merged[merged["deal_status_group"].isin(["won", "lost"])].copy()
    closed["won_flag"] = closed["deal_status_group"].eq("won").astype(int)
    global_win_rate = float(closed["won_flag"].mean())

    merged["seller_win_rate"] = merged["sales_agent"].map(safe_rate_map(closed, "sales_agent", global_win_rate)).fillna(global_win_rate)
    merged["product_win_rate"] = merged["product"].map(safe_rate_map(closed, "product", global_win_rate)).fillna(global_win_rate)
    merged["regional_win_rate"] = merged["regional_office"].map(safe_rate_map(closed, "regional_office", global_win_rate)).fillna(global_win_rate)
    merged["manager_win_rate"] = merged["manager"].map(safe_rate_map(closed, "manager", global_win_rate)).fillna(global_win_rate)

    stage_weight_map = {
        "Prospecting": 0.10,
        "Engaging": 0.25,
        "Won": 1.00,
        "Lost": 0.00,
    }
    merged["stage_weight"] = merged["deal_stage"].map(stage_weight_map).fillna(0.10)

    reference_date = merged["engage_date"].max()
    merged["deal_age_days"] = (reference_date - merged["engage_date"]).dt.days
    closed["days_to_close"] = (closed["close_date"] - closed["engage_date"]).dt.days
    aging_threshold = float(closed["days_to_close"].dropna().quantile(0.75))

    merged["aging_risk_flag"] = (
        merged["deal_status_group"].eq("open")
        & merged["deal_age_days"].notna()
        & (merged["deal_age_days"] > aging_threshold)
    )

    merged["priority_score"] = 100 * (
        0.45 * merged["stage_weight"]
        + 0.20 * merged["seller_win_rate"]
        + 0.15 * merged["product_win_rate"]
        + 0.10 * merged["regional_win_rate"]
        + 0.10 * merged["manager_win_rate"]
    )

    merged.loc[merged["aging_risk_flag"], "priority_score"] -= 10
    merged["priority_score"] = merged["priority_score"].clip(lower=0, upper=100)

    open_deals = merged[merged["deal_status_group"].eq("open")].copy()

    p50 = float(open_deals["priority_score"].quantile(0.50))
    p85 = float(open_deals["priority_score"].quantile(0.85))

    open_deals["priority_label"] = np.select(
        [open_deals["priority_score"] >= p85, open_deals["priority_score"] >= p50],
        ["Foco Agora", "Nutrir"],
        default="Baixa Prioridade",
    )

    thresholds = {
        "seller_high": float(closed.groupby("sales_agent")["won_flag"].mean().quantile(0.75)),
        "seller_low": float(closed.groupby("sales_agent")["won_flag"].mean().quantile(0.25)),
        "product_high": float(closed.groupby("product")["won_flag"].mean().quantile(0.75)),
        "product_low": float(closed.groupby("product")["won_flag"].mean().quantile(0.25)),
        "regional_high": float(closed.groupby("regional_office")["won_flag"].mean().quantile(0.75)),
        "regional_low": float(closed.groupby("regional_office")["won_flag"].mean().quantile(0.25)),
        "manager_high": float(closed.groupby("manager")["won_flag"].mean().quantile(0.75)),
        "manager_low": float(closed.groupby("manager")["won_flag"].mean().quantile(0.25)),
    }

    positive = open_deals.apply(lambda row: positive_reasons(row, thresholds), axis=1)
    risks = open_deals.apply(lambda row: risk_reasons(row, thresholds), axis=1)

    open_deals["top_positive_reason_1"] = [items[0] for items in positive]
    open_deals["top_positive_reason_2"] = [items[1] for items in positive]
    open_deals["top_risk_reason_1"] = [items[0] for items in risks]
    open_deals["top_risk_reason_2"] = [items[1] for items in risks]
    open_deals["recommended_action"] = open_deals.apply(recommended_action, axis=1)

    final_columns = [
        "opportunity_id", "account", "sales_agent", "manager", "regional_office",
        "product", "deal_stage", "engage_date", "close_value", "priority_score",
        "priority_label", "top_positive_reason_1", "top_positive_reason_2",
        "top_risk_reason_1", "top_risk_reason_2", "recommended_action",
    ]

    ranked = open_deals[final_columns].sort_values("priority_score", ascending=False)
    ranked.to_csv(out_path, index=False)

    print("DealPriority scoring pipeline completed.")
    print(f"Input rows: {len(sales_pipeline)}")
    print(f"Open deals exported: {len(ranked)}")
    print(f"p50: {p50:.4f}")
    print(f"p85: {p85:.4f}")
    print("Priority distribution:")
    print(ranked["priority_label"].value_counts().to_string())
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
