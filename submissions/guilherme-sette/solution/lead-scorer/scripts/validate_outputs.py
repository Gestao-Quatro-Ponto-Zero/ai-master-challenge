#!/usr/bin/env python3
"""Validate generated files for the Lead Scorer challenge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FRONTEND_DATA = PROJECT_ROOT / "frontend" / "data" / "dashboard_data.json"


EXPECTED_RAW_ROWS = {
    "accounts.csv": 85,
    "products.csv": 7,
    "sales_teams.csv": 35,
    "sales_pipeline.csv": 8800,
    "data_dictionary.csv": 21,
}

EXPECTED_PROCESSED_ROWS = {
    "dim_accounts.csv": 85,
    "dim_products.csv": 7,
    "dim_sales_teams.csv": 35,
    "fact_sales_pipeline.csv": 8800,
    "opportunities_enriched.csv": 8800,
    "training_closed_opportunities.csv": 6711,
    "open_pipeline_for_scoring.csv": 2089,
    "scored_open_opportunities.csv": 2089,
    "seller_portal_summary.csv": 27,
    "manager_portal_summary.csv": 6,
    "score_benchmark.csv": 12,
}

ALLOWED_SIGNALS = {
    "manter",
    "consultar_especialista",
    "remanejar",
    "manager_review",
    "corrigir_dados",
    "last_chance",
    "nurture",
}

REQUIRED_SCORED_COLUMNS = {
    "opportunity_id",
    "deal_stage",
    "current_sales_agent",
    "current_manager",
    "product",
    "estimated_deal_value",
    "account_known",
    "priority_score",
    "priority_band",
    "confidence_score",
    "confidence_band",
    "routing_signal",
    "recommended_action",
    "approval_required",
    "approval_type",
    "approval_label",
    "recommended_sales_agent",
    "match_score",
    "current_match_score",
    "fit_delta",
    "value_score",
    "fit_score",
    "timing_score",
    "stage_score",
    "account_score",
    "portfolio_score",
    "reason_codes",
}


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_csv(path: Path) -> pd.DataFrame:
    require(path.exists(), f"Missing file: {path}")
    return pd.read_csv(path)


def validate_row_counts() -> dict[str, int]:
    observed: dict[str, int] = {}

    for file_name, expected in EXPECTED_RAW_ROWS.items():
        rows = len(read_csv(RAW_DIR / file_name))
        observed[f"raw/{file_name}"] = rows
        require(rows == expected, f"{file_name}: expected {expected} rows, got {rows}")

    for file_name, expected in EXPECTED_PROCESSED_ROWS.items():
        rows = len(read_csv(PROCESSED_DIR / file_name))
        observed[f"processed/{file_name}"] = rows
        require(rows == expected, f"{file_name}: expected {expected} rows, got {rows}")

    return observed


def validate_leakage() -> None:
    training = read_csv(PROCESSED_DIR / "training_closed_opportunities.csv")
    scoring = read_csv(PROCESSED_DIR / "open_pipeline_for_scoring.csv")

    training_forbidden = {"deal_stage", "engage_date", "close_date", "close_value"}
    scoring_forbidden = {"close_date", "close_value", "target_won"}

    require(
        training_forbidden.isdisjoint(training.columns),
        f"Training table contains leakage columns: {training_forbidden.intersection(training.columns)}",
    )
    require(
        scoring_forbidden.isdisjoint(scoring.columns),
        f"Scoring table contains outcome columns: {scoring_forbidden.intersection(scoring.columns)}",
    )
    require("target_won" in training.columns, "Training table must include target_won")


def validate_scored_pipeline() -> dict[str, Any]:
    scored = read_csv(PROCESSED_DIR / "scored_open_opportunities.csv")
    missing = REQUIRED_SCORED_COLUMNS.difference(scored.columns)
    require(not missing, f"scored_open_opportunities missing columns: {sorted(missing)}")

    require(scored["opportunity_id"].is_unique, "Scored opportunity_id must be unique")
    require(scored["priority_score"].between(0, 100).all(), "priority_score must be 0-100")
    require(scored["confidence_score"].between(0, 100).all(), "confidence_score must be 0-100")
    require(set(scored["routing_signal"]).issubset(ALLOWED_SIGNALS), "Unknown routing_signal found")
    require(scored["reason_codes"].fillna("").str.len().gt(0).all(), "All deals need reason_codes")

    approvals = scored[scored["approval_required"].map(bool_value)]
    expected_approvals = scored["routing_signal"].isin({"remanejar", "manager_review"}).sum()
    require(len(approvals) == int(expected_approvals), "approval_required does not match routing policy")
    require(len(approvals) == 132, f"Expected 132 approval deals, got {len(approvals)}")

    transfers = scored[scored["routing_signal"] == "remanejar"]
    require(len(transfers) == 22, f"Expected 22 transfer recommendations, got {len(transfers)}")
    require(
        (transfers["current_sales_agent"] != transfers["recommended_sales_agent"]).all(),
        "Transfer recommendations must point to a different seller",
    )

    account_unknown = ~scored["account_known"].map(bool_value)
    require(int(account_unknown.sum()) == 1425, f"Expected 1425 open deals missing account, got {int(account_unknown.sum())}")

    return {
        "scored_rows": int(len(scored)),
        "approval_deals": int(len(approvals)),
        "transfer_deals": int(len(transfers)),
        "missing_account_open_deals": int(account_unknown.sum()),
        "routing_signal_counts": scored["routing_signal"].value_counts().to_dict(),
    }


def validate_dashboard_payload() -> dict[str, Any]:
    require(FRONTEND_DATA.exists(), f"Missing dashboard payload: {FRONTEND_DATA}")
    payload = json.loads(FRONTEND_DATA.read_text())

    for key in ["generated_at", "score_weights", "cutoffs", "deals", "sellers", "managers"]:
        require(key in payload, f"dashboard_data.json missing key: {key}")

    scored = read_csv(PROCESSED_DIR / "scored_open_opportunities.csv")
    sellers = read_csv(PROCESSED_DIR / "seller_portal_summary.csv")
    managers = read_csv(PROCESSED_DIR / "manager_portal_summary.csv")

    require(len(payload["deals"]) == len(scored), "Dashboard deal count differs from scored CSV")
    require(len(payload["sellers"]) == len(sellers), "Dashboard seller count differs from seller summary")
    require(len(payload["managers"]) == len(managers), "Dashboard manager count differs from manager summary")

    dashboard_approvals = sum(1 for deal in payload["deals"] if bool_value(deal.get("approval_required")))
    csv_approvals = int(scored["approval_required"].map(bool_value).sum())
    require(dashboard_approvals == csv_approvals, "Dashboard approval count differs from scored CSV")

    return {
        "dashboard_deals": len(payload["deals"]),
        "dashboard_sellers": len(payload["sellers"]),
        "dashboard_managers": len(payload["managers"]),
        "dashboard_approval_deals": dashboard_approvals,
    }


def validate_benchmark() -> dict[str, Any]:
    benchmark = read_csv(PROCESSED_DIR / "score_benchmark.csv")
    required = {
        "strategy",
        "top_cut",
        "top_n",
        "top_win_rate",
        "lift_vs_overall_win_rate",
        "won_revenue_capture",
        "avg_score_top",
    }
    missing = required.difference(benchmark.columns)
    require(not missing, f"score_benchmark missing columns: {sorted(missing)}")
    require((PROJECT_ROOT / "reports" / "score_benchmark.md").exists(), "Missing score benchmark report")
    require(benchmark["top_win_rate"].between(0, 1).all(), "Benchmark win rates must be 0-1")
    require(benchmark["won_revenue_capture"].between(0, 1).all(), "Benchmark revenue capture must be 0-1")
    return {
        "benchmark_rows": len(benchmark),
        "strategies": sorted(benchmark["strategy"].unique().tolist()),
    }


def main() -> None:
    summary = {
        "row_counts": validate_row_counts(),
        "leakage": "passed",
        "scored_pipeline": validate_scored_pipeline(),
        "dashboard": validate_dashboard_payload(),
        "benchmark": validate_benchmark(),
    }
    validate_leakage()
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
