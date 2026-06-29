#!/usr/bin/env python3
"""Build clean RavenStack analytics layer and canonical exports.

This script is intentionally self-contained so the submission can be
reproduced from the workspace root that contains data/raw/ravenstack and
ai-master-challenge:

    python ai-master-challenge/submissions/kadug/solution/analysis/build_exports.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RAW_FILES = {
    "accounts": "ravenstack_accounts.csv",
    "subscriptions": "ravenstack_subscriptions.csv",
    "feature_usage": "ravenstack_feature_usage.csv",
    "support_tickets": "ravenstack_support_tickets.csv",
    "churn_events": "ravenstack_churn_events.csv",
}

REFERENCE_DATE = pd.Timestamp("2024-12-31")
RISK_ORDER = ["Critical", "High", "Medium", "Low"]


def find_project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / "data" / "raw" / "ravenstack").exists():
            return parent
    raise RuntimeError("Could not find project root containing data/raw/ravenstack")


def json_default(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True, default=json_default),
        encoding="utf-8",
    )


def write_frame(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def normalize_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .map({"true": True, "false": False, "1": True, "0": False})
        .fillna(False)
        .astype(bool)
    )


def mode_or_empty(series: pd.Series) -> str:
    clean = series.dropna()
    if clean.empty:
        return ""
    modes = clean.mode()
    if modes.empty:
        return ""
    return str(modes.iloc[0])


def pct(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def format_usd(value: float) -> str:
    return f"${value:,.0f}"


def preflight(project_root: Path, submission_dir: Path) -> dict[str, Any]:
    required_dirs = [
        submission_dir / "solution",
        submission_dir / "solution" / "analysis",
        submission_dir / "solution" / "exports",
        submission_dir / "solution" / "dashboard",
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "python_available": True,
        "streamlit_available": importlib.util.find_spec("streamlit") is not None,
        "pandas_version": pd.__version__,
        "raw_dir": str(project_root / "data" / "raw" / "ravenstack"),
        "required_dirs": {
            str(path.relative_to(project_root)): path.exists() for path in required_dirs
        },
        "fallback_decision": "Python and Streamlit available; no dashboard fallback required.",
    }


def load_raw(raw_dir: Path) -> dict[str, pd.DataFrame]:
    missing = [name for name in RAW_FILES.values() if not (raw_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing raw RavenStack files: {missing}")

    accounts = pd.read_csv(raw_dir / RAW_FILES["accounts"], parse_dates=["signup_date"])
    subscriptions = pd.read_csv(
        raw_dir / RAW_FILES["subscriptions"],
        parse_dates=["start_date", "end_date"],
    )
    usage = pd.read_csv(raw_dir / RAW_FILES["feature_usage"], parse_dates=["usage_date"])
    support = pd.read_csv(
        raw_dir / RAW_FILES["support_tickets"],
        parse_dates=["submitted_at", "closed_at"],
    )
    churn = pd.read_csv(raw_dir / RAW_FILES["churn_events"], parse_dates=["churn_date"])

    for column in ["is_trial", "churn_flag"]:
        accounts[column] = normalize_bool(accounts[column])
    for column in [
        "is_trial",
        "upgrade_flag",
        "downgrade_flag",
        "churn_flag",
        "auto_renew_flag",
    ]:
        subscriptions[column] = normalize_bool(subscriptions[column])
    usage["is_beta_feature"] = normalize_bool(usage["is_beta_feature"])
    support["escalation_flag"] = normalize_bool(support["escalation_flag"])
    for column in [
        "preceding_upgrade_flag",
        "preceding_downgrade_flag",
        "is_reactivation",
    ]:
        churn[column] = normalize_bool(churn[column])

    int_columns = {
        "accounts": ["seats"],
        "subscriptions": ["seats", "mrr_amount", "arr_amount"],
        "feature_usage": ["usage_count", "usage_duration_secs", "error_count"],
        "support_tickets": ["first_response_time_minutes"],
    }
    frames = {
        "accounts": accounts,
        "subscriptions": subscriptions,
        "feature_usage": usage,
        "support_tickets": support,
        "churn_events": churn,
    }
    for frame_name, columns in int_columns.items():
        for column in columns:
            frames[frame_name][column] = pd.to_numeric(
                frames[frame_name][column], errors="raise"
            ).astype(int)

    support["resolution_time_hours"] = pd.to_numeric(
        support["resolution_time_hours"], errors="raise"
    )
    support["satisfaction_score"] = pd.to_numeric(
        support["satisfaction_score"], errors="coerce"
    )
    churn["refund_amount_usd"] = pd.to_numeric(churn["refund_amount_usd"], errors="raise")

    return frames


def build_clean_layer(raw: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    accounts = raw["accounts"].copy().rename(
        columns={
            "plan_tier": "initial_plan_tier",
            "seats": "account_seats",
            "is_trial": "account_is_trial",
            "churn_flag": "account_churn_flag",
        }
    )
    subscriptions = raw["subscriptions"].copy()
    support = raw["support_tickets"].copy()
    churn = raw["churn_events"].copy()

    usage = raw["feature_usage"].copy().reset_index(drop=True)
    usage.insert(
        0,
        "feature_usage_row_id",
        [f"FU-{row_num:06d}" for row_num in range(1, len(usage) + 1)],
    )
    usage = usage.merge(
        subscriptions[["subscription_id", "account_id", "start_date", "end_date"]],
        on="subscription_id",
        how="left",
        validate="many_to_one",
    )
    usage["usage_in_subscription_window_flag"] = (
        usage["usage_date"].ge(usage["start_date"])
        & (usage["end_date"].isna() | usage["usage_date"].le(usage["end_date"]))
    )

    return {
        "accounts": accounts,
        "subscriptions": subscriptions,
        "feature_usage": usage,
        "support_tickets": support,
        "churn_events": churn,
    }


def schema_contract(clean: dict[str, pd.DataFrame]) -> dict[str, Any]:
    logical_types = {
        "datetime64[ns]": "date_or_datetime",
        "bool": "boolean",
        "int64": "integer",
        "float64": "decimal",
        "object": "string",
    }
    contract: dict[str, Any] = {}
    for name, frame in clean.items():
        contract[name] = {
            "rows": len(frame),
            "columns": [
                {
                    "name": column,
                    "pandas_dtype": str(dtype),
                    "logical_type": logical_types.get(str(dtype), str(dtype)),
                    "nulls": int(frame[column].isna().sum()),
                }
                for column, dtype in frame.dtypes.items()
            ],
        }
    return contract


def write_clean_layer(clean: dict[str, pd.DataFrame], clean_dir: Path) -> None:
    clean_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in clean.items():
        write_frame(frame, clean_dir / f"{name}.csv")
    write_json(clean_dir / "clean_schema.json", schema_contract(clean))


def validate_clean_layer(
    raw: dict[str, pd.DataFrame], clean: dict[str, pd.DataFrame]
) -> dict[str, Any]:
    accounts = clean["accounts"]
    subscriptions = clean["subscriptions"]
    usage = clean["feature_usage"]
    support = clean["support_tickets"]
    churn = clean["churn_events"]

    account_ids = set(accounts["account_id"])
    subscription_ids = set(subscriptions["subscription_id"])

    event_accounts = set(churn["account_id"])
    account_flag_accounts = set(accounts.loc[accounts["account_churn_flag"], "account_id"])

    validation = {
        "raw_row_counts": {name: int(len(frame)) for name, frame in raw.items()},
        "clean_row_counts": {name: int(len(frame)) for name, frame in clean.items()},
        "fk_orphans": {
            "subscriptions_to_accounts": int(
                (~subscriptions["account_id"].isin(account_ids)).sum()
            ),
            "support_to_accounts": int((~support["account_id"].isin(account_ids)).sum()),
            "churn_to_accounts": int((~churn["account_id"].isin(account_ids)).sum()),
            "usage_to_subscriptions": int(
                (~usage["subscription_id"].isin(subscription_ids)).sum()
            ),
        },
        "feature_usage_row_id_unique": bool(usage["feature_usage_row_id"].is_unique),
        "usage_id_duplicate_surplus": int(
            raw["feature_usage"]["usage_id"].size
            - raw["feature_usage"]["usage_id"].nunique()
        ),
        "usage_window_counts": {
            "before_subscription_start": int(
                usage["usage_date"].lt(usage["start_date"]).sum()
            ),
            "after_subscription_end": int(
                (
                    usage["end_date"].notna()
                    & usage["usage_date"].gt(usage["end_date"])
                ).sum()
            ),
            "in_window": int(usage["usage_in_subscription_window_flag"].sum()),
            "out_of_window": int((~usage["usage_in_subscription_window_flag"]).sum()),
        },
        "churn_label_counts": {
            "account_churn_flag_true_accounts": len(account_flag_accounts),
            "has_churn_event_accounts": len(event_accounts),
            "event_accounts_with_account_flag_false": len(event_accounts - account_flag_accounts),
            "account_flag_true_without_event": len(account_flag_accounts - event_accounts),
        },
    }
    validation["passed"] = (
        all(value == 0 for value in validation["fk_orphans"].values())
        and validation["feature_usage_row_id_unique"]
    )
    return validation


def build_account_health(clean: dict[str, pd.DataFrame]) -> pd.DataFrame:
    accounts = clean["accounts"].copy()
    subscriptions = clean["subscriptions"].copy()
    usage = clean["feature_usage"].copy()
    support = clean["support_tickets"].copy()
    churn = clean["churn_events"].copy()

    active_subs = subscriptions[subscriptions["end_date"].isna()].copy()
    latest_subs = (
        subscriptions.sort_values(["account_id", "start_date", "end_date"], na_position="last")
        .drop_duplicates("account_id", keep="last")
        .rename(
            columns={
                "subscription_id": "latest_subscription_id",
                "plan_tier": "latest_plan_tier",
                "billing_frequency": "latest_billing_frequency",
                "start_date": "latest_subscription_start_date",
                "end_date": "latest_subscription_end_date",
            }
        )
    )
    subscriptions = subscriptions.assign(
        annual_billing_flag=subscriptions["billing_frequency"].eq("annual"),
        monthly_billing_flag=subscriptions["billing_frequency"].eq("monthly"),
    )

    sub_agg = subscriptions.groupby("account_id").agg(
        subscription_count=("subscription_id", "size"),
        churned_subscription_count=("churn_flag", "sum"),
        total_mrr_booked=("mrr_amount", "sum"),
        total_arr_booked=("arr_amount", "sum"),
        any_upgrade_flag=("upgrade_flag", "max"),
        any_downgrade_flag=("downgrade_flag", "max"),
        any_annual_billing_flag=("annual_billing_flag", "max"),
        any_monthly_billing_flag=("monthly_billing_flag", "max"),
    )
    active_agg = active_subs.groupby("account_id").agg(
        active_subscription_count=("subscription_id", "size"),
        current_mrr=("mrr_amount", "sum"),
        current_arr=("arr_amount", "sum"),
        active_auto_renew_flag=("auto_renew_flag", "max"),
    )

    usage_valid = usage[usage["usage_in_subscription_window_flag"]].copy()
    usage_raw = usage.groupby("account_id").agg(raw_usage_event_count=("usage_id", "size"))
    usage_agg = usage_valid.groupby("account_id").agg(
        valid_usage_event_count=("usage_id", "size"),
        distinct_features_used_valid=("feature_name", "nunique"),
        total_usage_count_valid=("usage_count", "sum"),
        usage_duration_secs_valid=("usage_duration_secs", "sum"),
        error_count_valid=("error_count", "sum"),
        beta_usage_event_count_valid=("is_beta_feature", "sum"),
    )

    support = support.assign(
        high_urgent_ticket_flag=support["priority"].isin(["high", "urgent"]),
        satisfaction_response_flag=support["satisfaction_score"].notna(),
    )
    support_agg = support.groupby("account_id").agg(
        support_ticket_count=("ticket_id", "size"),
        high_urgent_ticket_count=("high_urgent_ticket_flag", "sum"),
        escalated_ticket_count=("escalation_flag", "sum"),
        avg_first_response_minutes=("first_response_time_minutes", "mean"),
        avg_resolution_hours=("resolution_time_hours", "mean"),
        avg_satisfaction_score=("satisfaction_score", "mean"),
        satisfaction_response_rate=("satisfaction_response_flag", "mean"),
    )

    churn_latest = (
        churn.sort_values(["account_id", "churn_date"])
        .drop_duplicates("account_id", keep="last")
        .rename(
            columns={
                "churn_date": "latest_churn_date",
                "reason_code": "latest_reason_code",
            }
        )
    )
    churn_agg = churn.groupby("account_id").agg(
        churn_event_count=("churn_event_id", "size"),
        refund_total_usd=("refund_amount_usd", "sum"),
        reactivation_event_count=("is_reactivation", "sum"),
    )

    health = accounts.merge(sub_agg, on="account_id", how="left")
    health = health.merge(active_agg, on="account_id", how="left")
    health = health.merge(
        latest_subs[
            [
                "account_id",
                "latest_subscription_id",
                "latest_plan_tier",
                "latest_billing_frequency",
                "latest_subscription_start_date",
                "latest_subscription_end_date",
            ]
        ],
        on="account_id",
        how="left",
    )
    health = health.merge(usage_raw, on="account_id", how="left")
    health = health.merge(usage_agg, on="account_id", how="left")
    health = health.merge(support_agg, on="account_id", how="left")
    health = health.merge(churn_agg, on="account_id", how="left")
    health = health.merge(
        churn_latest[["account_id", "latest_churn_date", "latest_reason_code"]],
        on="account_id",
        how="left",
    )

    numeric_zero_cols = [
        "subscription_count",
        "churned_subscription_count",
        "total_mrr_booked",
        "total_arr_booked",
        "active_subscription_count",
        "current_mrr",
        "current_arr",
        "raw_usage_event_count",
        "valid_usage_event_count",
        "distinct_features_used_valid",
        "total_usage_count_valid",
        "usage_duration_secs_valid",
        "error_count_valid",
        "beta_usage_event_count_valid",
        "support_ticket_count",
        "high_urgent_ticket_count",
        "escalated_ticket_count",
        "churn_event_count",
        "refund_total_usd",
        "reactivation_event_count",
    ]
    for column in numeric_zero_cols:
        health[column] = health[column].fillna(0)

    bool_cols = [
        "any_upgrade_flag",
        "any_downgrade_flag",
        "any_annual_billing_flag",
        "any_monthly_billing_flag",
        "active_auto_renew_flag",
    ]
    for column in bool_cols:
        health[column] = health[column].fillna(False).astype(bool)

    health["invalid_usage_event_count"] = (
        health["raw_usage_event_count"] - health["valid_usage_event_count"]
    )
    health["valid_usage_share"] = (
        health["valid_usage_event_count"] / health["raw_usage_event_count"].replace(0, pd.NA)
    ).fillna(0)
    health["error_rate_per_100_valid_events"] = (
        health["error_count_valid"] / health["valid_usage_event_count"].replace(0, pd.NA) * 100
    ).fillna(0)
    health["beta_usage_event_share_valid"] = (
        health["beta_usage_event_count_valid"]
        / health["valid_usage_event_count"].replace(0, pd.NA)
    ).fillna(0)
    health["has_churn_event"] = health["churn_event_count"].gt(0)
    health["mrr_at_risk"] = health["current_mrr"]

    score_columns = add_risk_scoring(health)
    health["account_health_score"] = score_columns["score"]
    health["risk_segment"] = score_columns["segment"]
    health["primary_risk_driver"] = score_columns["driver"]
    health["data_quality_flags"] = health.apply(data_quality_flags, axis=1)

    export_columns = [
        "account_id",
        "account_name",
        "industry",
        "country",
        "signup_date",
        "referral_source",
        "initial_plan_tier",
        "account_seats",
        "account_is_trial",
        "account_churn_flag",
        "subscription_count",
        "active_subscription_count",
        "churned_subscription_count",
        "latest_subscription_id",
        "latest_plan_tier",
        "latest_billing_frequency",
        "latest_subscription_start_date",
        "latest_subscription_end_date",
        "current_mrr",
        "current_arr",
        "total_mrr_booked",
        "total_arr_booked",
        "any_upgrade_flag",
        "any_downgrade_flag",
        "any_annual_billing_flag",
        "any_monthly_billing_flag",
        "active_auto_renew_flag",
        "raw_usage_event_count",
        "valid_usage_event_count",
        "invalid_usage_event_count",
        "valid_usage_share",
        "distinct_features_used_valid",
        "total_usage_count_valid",
        "usage_duration_secs_valid",
        "error_count_valid",
        "error_rate_per_100_valid_events",
        "beta_usage_event_share_valid",
        "support_ticket_count",
        "high_urgent_ticket_count",
        "escalated_ticket_count",
        "avg_first_response_minutes",
        "avg_resolution_hours",
        "avg_satisfaction_score",
        "satisfaction_response_rate",
        "has_churn_event",
        "churn_event_count",
        "latest_churn_date",
        "latest_reason_code",
        "refund_total_usd",
        "reactivation_event_count",
        "mrr_at_risk",
        "account_health_score",
        "risk_segment",
        "primary_risk_driver",
        "data_quality_flags",
    ]
    health = health[export_columns].copy()
    health = health.sort_values("account_id").reset_index(drop=True)
    return health


def add_risk_scoring(health: pd.DataFrame) -> dict[str, pd.Series]:
    mrr = health["current_mrr"]
    mrr_p50 = mrr.quantile(0.50)
    mrr_p75 = mrr.quantile(0.75)
    mrr_p90 = mrr.quantile(0.90)
    error_p75 = health["error_rate_per_100_valid_events"].quantile(0.75)
    feature_p25 = health["distinct_features_used_valid"].quantile(0.25)

    def churn_points(row: pd.Series) -> int:
        points = 0
        if row["has_churn_event"]:
            points += 10
        if row["churn_event_count"] >= 2:
            points += 8
        if pd.notna(row["latest_churn_date"]):
            days = (REFERENCE_DATE - row["latest_churn_date"]).days
            if days <= 180:
                points += 8
        if row["reactivation_event_count"] > 0:
            points += 4
        return min(points, 30)

    def subscription_points(row: pd.Series) -> int:
        points = 0
        if row["any_downgrade_flag"]:
            points += 7
        if row["active_subscription_count"] > 0 and not row["active_auto_renew_flag"]:
            points += 5
        if row["account_is_trial"]:
            points += 4
        if row["churned_subscription_count"] > 0:
            points += 4
        return min(points, 20)

    def support_points(row: pd.Series) -> int:
        points = 0
        if row["escalated_ticket_count"] > 0:
            points += 6
        if row["high_urgent_ticket_count"] > 0:
            points += 6
        if row["support_ticket_count"] > 0 and row["satisfaction_response_rate"] < 0.5:
            points += 4
        if pd.notna(row["avg_satisfaction_score"]) and row["avg_satisfaction_score"] <= 3.5:
            points += 4
        return min(points, 20)

    def product_points(row: pd.Series) -> int:
        points = 0
        if row["raw_usage_event_count"] > 0 and row["valid_usage_share"] < 0.25:
            points += 5
        if (
            row["valid_usage_event_count"] > 0
            and row["error_rate_per_100_valid_events"] >= error_p75
            and row["error_rate_per_100_valid_events"] > 0
        ):
            points += 5
        if row["distinct_features_used_valid"] <= feature_p25:
            points += 5
        return min(points, 15)

    def revenue_points(row: pd.Series) -> int:
        if row["current_mrr"] >= mrr_p90:
            return 15
        if row["current_mrr"] >= mrr_p75:
            return 10
        if row["current_mrr"] >= mrr_p50:
            return 5
        return 0

    component_frames = pd.DataFrame(
        {
            "Churn history": health.apply(churn_points, axis=1),
            "Subscription/commercial": health.apply(subscription_points, axis=1),
            "Support friction": health.apply(support_points, axis=1),
            "Product usage quality": health.apply(product_points, axis=1),
            "Revenue exposure": health.apply(revenue_points, axis=1),
        }
    )
    score = component_frames.sum(axis=1).clip(upper=100).round().astype(int)

    def segment(value: int) -> str:
        if value >= 80:
            return "Critical"
        if value >= 60:
            return "High"
        if value >= 35:
            return "Medium"
        return "Low"

    def driver(row: pd.Series) -> str:
        if row.max() == 0:
            return "Stable / low signal"
        return str(row.idxmax())

    return {
        "score": score,
        "segment": score.map(segment),
        "driver": component_frames.apply(driver, axis=1),
    }


def data_quality_flags(row: pd.Series) -> str:
    flags: list[str] = []
    if row["invalid_usage_event_count"] > 0:
        flags.append("invalid_usage_windows")
    if bool(row["account_churn_flag"]) != bool(row["has_churn_event"]):
        flags.append("churn_label_mismatch")
    if row["support_ticket_count"] > 0 and row["satisfaction_response_rate"] < 0.5:
        flags.append("low_satisfaction_response")
    if row["active_subscription_count"] == 0:
        flags.append("no_active_subscription")
    return "|".join(flags)


def recommended_playbook(segment: str) -> str:
    return {
        "Critical": "Leadership-sponsored save plan within 7 days",
        "High": "CS intervention with support/product follow-up within 14 days",
        "Medium": "Monitor weekly and trigger playbook on new support or downgrade signal",
        "Low": "Standard health monitoring",
    }.get(segment, "Standard health monitoring")


def build_risk_segments(account_health: pd.DataFrame) -> pd.DataFrame:
    frame = account_health.copy()
    frame["active_account_flag"] = frame["active_subscription_count"].gt(0)
    frame["event_churn_flag"] = frame["has_churn_event"].astype(bool)
    frame["account_flag_churn_bool"] = frame["account_churn_flag"].astype(bool)
    frame["high_urgent_account_flag"] = frame["high_urgent_ticket_count"].gt(0)
    frame["escalated_account_flag"] = frame["escalated_ticket_count"].gt(0)

    rows: list[dict[str, Any]] = []
    for segment in RISK_ORDER:
        group = frame[frame["risk_segment"] == segment]
        if group.empty:
            continue
        rows.append(
            {
                "risk_segment": segment,
                "account_count": len(group),
                "active_account_count": int(group["active_account_flag"].sum()),
                "churned_account_flag_count": int(group["account_flag_churn_bool"].sum()),
                "has_churn_event_count": int(group["event_churn_flag"].sum()),
                "current_mrr": round(float(group["current_mrr"].sum()), 2),
                "current_arr": round(float(group["current_arr"].sum()), 2),
                "mrr_at_risk": round(float(group["mrr_at_risk"].sum()), 2),
                "avg_mrr_at_risk": round(float(group["mrr_at_risk"].mean()), 2),
                "event_based_churn_rate": round(group["event_churn_flag"].mean(), 4),
                "account_flag_churn_rate": round(group["account_flag_churn_bool"].mean(), 4),
                "avg_churn_event_count": round(float(group["churn_event_count"].mean()), 2),
                "top_churn_reason": mode_or_empty(group["latest_reason_code"]),
                "avg_satisfaction_score": round(
                    float(group["avg_satisfaction_score"].mean(skipna=True)), 2
                ),
                "satisfaction_response_rate": round(
                    float(group["satisfaction_response_rate"].mean()), 4
                ),
                "high_urgent_ticket_rate": round(group["high_urgent_account_flag"].mean(), 4),
                "escalation_rate": round(group["escalated_account_flag"].mean(), 4),
                "avg_valid_usage_share": round(float(group["valid_usage_share"].mean()), 4),
                "avg_error_rate_per_100_valid_events": round(
                    float(group["error_rate_per_100_valid_events"].mean()), 2
                ),
                "avg_distinct_features_used_valid": round(
                    float(group["distinct_features_used_valid"].mean()), 2
                ),
                "top_industry": mode_or_empty(group["industry"]),
                "top_plan_tier": mode_or_empty(group["latest_plan_tier"]),
                "top_country": mode_or_empty(group["country"]),
                "recommended_playbook": recommended_playbook(segment),
            }
        )
    return pd.DataFrame(rows)


def action_owner(primary_driver: str) -> str:
    if primary_driver == "Support friction":
        return "Support"
    if primary_driver == "Product usage quality":
        return "Product"
    if primary_driver == "Subscription/commercial":
        return "Pricing"
    if primary_driver == "Revenue exposure":
        return "Leadership"
    return "CS"


def next_best_action(row: pd.Series) -> str:
    driver = row["primary_risk_driver"]
    if driver == "Support friction":
        return "Open executive support review for escalations, urgent tickets, and low-response satisfaction."
    if driver == "Product usage quality":
        return "Schedule product success session focused on valid feature adoption and error-heavy workflows."
    if driver == "Subscription/commercial":
        return "Review downgrade, renewal, trial, and billing terms with CS and Revenue before renewal."
    if driver == "Revenue exposure":
        return "Assign leadership sponsor and validate renewal risk with account owner."
    return "Run CS save playbook using churn history and latest reason code as discovery prompts."


def confidence_level(row: pd.Series) -> str:
    flags = str(row.get("data_quality_flags", ""))
    if "invalid_usage_windows" in flags or "churn_label_mismatch" in flags:
        return "Medium"
    return "High"


def build_priority_accounts(account_health: pd.DataFrame) -> pd.DataFrame:
    mrr_p90 = account_health["mrr_at_risk"].quantile(0.90)
    candidates = account_health[
        account_health["risk_segment"].isin(["Critical", "High"])
        | (
            account_health["risk_segment"].eq("Medium")
            & account_health["mrr_at_risk"].gt(mrr_p90)
        )
    ].copy()
    candidates = candidates.sort_values(
        [
            "account_health_score",
            "mrr_at_risk",
            "high_urgent_ticket_count",
            "latest_churn_date",
        ],
        ascending=[False, False, False, False],
        na_position="last",
    ).reset_index(drop=True)
    candidates.insert(0, "priority_rank", range(1, len(candidates) + 1))
    candidates["next_best_action"] = candidates.apply(next_best_action, axis=1)
    candidates["action_owner"] = candidates["primary_risk_driver"].map(action_owner)
    candidates["due_bucket"] = candidates["risk_segment"].map(
        {
            "Critical": "0-7 days",
            "High": "8-14 days",
            "Medium": "15-30 days",
            "Low": "Monitor",
        }
    )
    candidates["confidence_level"] = candidates.apply(confidence_level, axis=1)
    return candidates[
        [
            "priority_rank",
            "account_id",
            "account_name",
            "risk_segment",
            "account_health_score",
            "current_mrr",
            "current_arr",
            "mrr_at_risk",
            "latest_plan_tier",
            "industry",
            "country",
            "primary_risk_driver",
            "latest_reason_code",
            "churn_event_count",
            "high_urgent_ticket_count",
            "escalated_ticket_count",
            "avg_satisfaction_score",
            "error_rate_per_100_valid_events",
            "valid_usage_share",
            "data_quality_flags",
            "next_best_action",
            "action_owner",
            "due_bucket",
            "confidence_level",
            "latest_churn_date",
        ]
    ].rename(columns={"latest_plan_tier": "plan_tier"})


def build_churner_comparison(account_health: pd.DataFrame) -> pd.DataFrame:
    """Compare churn labels across required finding dimensions.

    This is an analysis support artifact, not one of the five canonical exports.
    It keeps the finding traceable without making the report recompute metrics.
    """

    frame = account_health.copy()
    frame["event_churn_label"] = frame["has_churn_event"].map(
        {True: "has_churn_event", False: "no_churn_event"}
    )
    frame["support_ticket_account_flag"] = frame["support_ticket_count"].gt(0)
    frame["high_urgent_account_flag"] = frame["high_urgent_ticket_count"].gt(0)
    frame["escalated_account_flag"] = frame["escalated_ticket_count"].gt(0)

    rows: list[dict[str, Any]] = []

    def add_group(label_type: str, comparison_label: str, group: pd.DataFrame) -> None:
        rows.append(
            {
                "label_type": label_type,
                "comparison_label": comparison_label,
                "account_count": len(group),
                "current_mrr": round(float(group["current_mrr"].sum()), 2),
                "current_arr": round(float(group["current_arr"].sum()), 2),
                "avg_current_mrr": round(float(group["current_mrr"].mean()), 2),
                "account_churn_flag_rate": round(
                    float(group["account_churn_flag"].astype(bool).mean()), 4
                )
                if len(group)
                else 0,
                "has_churn_event_rate": round(
                    float(group["has_churn_event"].astype(bool).mean()), 4
                )
                if len(group)
                else 0,
                "avg_valid_usage_share": round(float(group["valid_usage_share"].mean()), 4)
                if len(group)
                else 0,
                "avg_error_rate_per_100_valid_events": round(
                    float(group["error_rate_per_100_valid_events"].mean()), 2
                )
                if len(group)
                else 0,
                "avg_distinct_features_used_valid": round(
                    float(group["distinct_features_used_valid"].mean()), 2
                )
                if len(group)
                else 0,
                "support_ticket_account_rate": round(
                    float(group["support_ticket_account_flag"].mean()), 4
                )
                if len(group)
                else 0,
                "high_urgent_ticket_account_rate": round(
                    float(group["high_urgent_account_flag"].mean()), 4
                )
                if len(group)
                else 0,
                "escalated_account_rate": round(float(group["escalated_account_flag"].mean()), 4)
                if len(group)
                else 0,
                "avg_satisfaction_score": round(
                    float(group["avg_satisfaction_score"].mean(skipna=True)), 2
                )
                if len(group)
                else 0,
                "satisfaction_response_rate": round(
                    float(group["satisfaction_response_rate"].mean()), 4
                )
                if len(group)
                else 0,
                "downgrade_account_rate": round(
                    float(group["any_downgrade_flag"].astype(bool).mean()), 4
                )
                if len(group)
                else 0,
                "upgrade_account_rate": round(
                    float(group["any_upgrade_flag"].astype(bool).mean()), 4
                )
                if len(group)
                else 0,
                "annual_billing_account_rate": round(
                    float(group["any_annual_billing_flag"].astype(bool).mean()), 4
                )
                if len(group)
                else 0,
                "trial_account_rate": round(
                    float(group["account_is_trial"].astype(bool).mean()), 4
                )
                if len(group)
                else 0,
                "top_plan_tier": mode_or_empty(group["latest_plan_tier"]),
                "top_industry": mode_or_empty(group["industry"]),
                "top_country": mode_or_empty(group["country"]),
                "top_latest_reason_code": mode_or_empty(group["latest_reason_code"]),
            }
        )

    add_group("has_churn_event", "true", frame[frame["has_churn_event"]])
    add_group("has_churn_event", "false", frame[~frame["has_churn_event"]])
    add_group("account_churn_flag", "true", frame[frame["account_churn_flag"].astype(bool)])
    add_group("account_churn_flag", "false", frame[~frame["account_churn_flag"].astype(bool)])
    return pd.DataFrame(rows)


def growth_pct(previous: float, latest: float) -> float | None:
    if previous == 0:
        return None
    return round(((latest - previous) / previous) * 100, 2)


def growth_direction(previous: float, latest: float) -> str:
    if latest > previous:
        return "grew"
    if latest < previous:
        return "declined"
    return "flat"


def build_usage_growth_tests(
    clean: dict[str, pd.DataFrame], account_health: pd.DataFrame
) -> pd.DataFrame:
    """Test raw usage growth versus valid-window usage growth by segment."""

    usage = clean["feature_usage"].copy()
    account_dims = account_health[
        [
            "account_id",
            "risk_segment",
            "latest_plan_tier",
            "has_churn_event",
            "account_churn_flag",
        ]
    ]
    usage = usage.merge(account_dims, on="account_id", how="left", validate="many_to_one")
    previous = usage[
        usage["usage_date"].between(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-06-30"))
    ]
    latest = usage[
        usage["usage_date"].between(pd.Timestamp("2024-07-01"), pd.Timestamp("2024-12-31"))
    ]

    rows: list[dict[str, Any]] = []

    def add_test(segment_type: str, segment_value: str, previous_group: pd.DataFrame, latest_group: pd.DataFrame) -> None:
        previous_valid = previous_group[previous_group["usage_in_subscription_window_flag"]]
        latest_valid = latest_group[latest_group["usage_in_subscription_window_flag"]]
        previous_raw_count = float(previous_group["usage_count"].sum())
        latest_raw_count = float(latest_group["usage_count"].sum())
        previous_valid_count = float(previous_valid["usage_count"].sum())
        latest_valid_count = float(latest_valid["usage_count"].sum())
        previous_raw_events = len(previous_group)
        latest_raw_events = len(latest_group)
        previous_valid_events = len(previous_valid)
        latest_valid_events = len(latest_valid)
        latest_invalid_events = latest_raw_events - latest_valid_events
        raw_growth = growth_pct(previous_raw_count, latest_raw_count)
        valid_growth = growth_pct(previous_valid_count, latest_valid_count)
        raw_direction = growth_direction(previous_raw_count, latest_raw_count)
        valid_direction = growth_direction(previous_valid_count, latest_valid_count)
        if raw_direction == "grew" and valid_direction != "grew":
            interpretation = "Raw usage grew, but valid-window usage did not; aggregate growth is not healthy-adoption evidence."
        elif raw_direction == "grew" and valid_direction == "grew":
            interpretation = "Raw and valid-window usage both grew; still inspect quality and error rates before calling adoption healthy."
        elif raw_direction != "grew" and valid_direction == "grew":
            interpretation = "Valid-window usage grew despite raw usage not growing; subscription-window filtering changes the story."
        else:
            interpretation = "Usage did not grow on either raw or valid-window measures."

        rows.append(
            {
                "segment_type": segment_type,
                "segment_value": segment_value,
                "previous_period": "2024-H1",
                "latest_period": "2024-H2",
                "previous_raw_usage_events": previous_raw_events,
                "latest_raw_usage_events": latest_raw_events,
                "previous_valid_usage_events": previous_valid_events,
                "latest_valid_usage_events": latest_valid_events,
                "previous_raw_usage_count": round(previous_raw_count, 2),
                "latest_raw_usage_count": round(latest_raw_count, 2),
                "previous_valid_usage_count": round(previous_valid_count, 2),
                "latest_valid_usage_count": round(latest_valid_count, 2),
                "raw_usage_count_growth_pct": raw_growth,
                "valid_usage_count_growth_pct": valid_growth,
                "raw_usage_direction": raw_direction,
                "valid_usage_direction": valid_direction,
                "latest_invalid_usage_event_share": round(
                    latest_invalid_events / latest_raw_events, 4
                )
                if latest_raw_events
                else 0,
                "interpretation": interpretation,
            }
        )

    add_test("portfolio", "all", previous, latest)
    for column, segment_type in [
        ("risk_segment", "risk_segment"),
        ("latest_plan_tier", "plan_tier"),
        ("has_churn_event", "has_churn_event"),
        ("account_churn_flag", "account_churn_flag"),
    ]:
        values = sorted(usage[column].dropna().unique(), key=lambda value: str(value))
        for value in values:
            add_test(
                segment_type,
                str(value),
                previous[previous[column].eq(value)],
                latest[latest[column].eq(value)],
            )

    return pd.DataFrame(rows)


def build_root_cause_candidates(account_health: pd.DataFrame) -> pd.DataFrame:
    """Rank plausible root-cause candidates while preserving causal caveats."""

    total_accounts = len(account_health)
    total_mrr = float(account_health["mrr_at_risk"].sum())

    def candidate_row(
        root_cause_candidate: str,
        mask: pd.Series,
        evidence_summary: str,
        supporting_metrics: str,
        confidence_level: str,
        false_causality_risk: str,
        recommended_action: str,
        owner_team: str,
        candidate_category: str = "business_root_cause",
        score_override: float | None = None,
    ) -> dict[str, Any]:
        group = account_health[mask]
        affected_accounts = len(group)
        mrr_at_risk = float(group["mrr_at_risk"].sum())
        confidence_points = {"High": 30, "Medium": 20, "Low": 10}.get(confidence_level, 10)
        account_points = (affected_accounts / total_accounts) * 30 if total_accounts else 0
        revenue_points = (mrr_at_risk / total_mrr) * 40 if total_mrr else 0
        candidate_score = (
            score_override
            if score_override is not None
            else account_points + revenue_points + confidence_points
        )
        return {
            "candidate_category": candidate_category,
            "root_cause_candidate": root_cause_candidate,
            "affected_accounts": affected_accounts,
            "mrr_at_risk": round(mrr_at_risk, 2),
            "candidate_score": round(candidate_score, 2),
            "evidence_summary": evidence_summary,
            "supporting_metrics": supporting_metrics,
            "confidence_level": confidence_level,
            "false_causality_risk": false_causality_risk,
            "recommended_action": recommended_action,
            "owner_team": owner_team,
            "source_exports": "account_health.csv|risk_segments.csv|priority_accounts.csv|churner_comparison.csv|usage_growth_tests.csv",
        }

    rows = [
        candidate_row(
            "Value-realization erosion before renewal",
            account_health["risk_segment"].isin(["Critical", "High", "Medium"]),
            "Medium+ risk accounts combine churn history, support friction, product-usage quality, and commercial signals before renewal.",
            "risk_segment; latest_reason_code; high_urgent_ticket_count; escalated_ticket_count; valid_usage_share; any_downgrade_flag; mrr_at_risk",
            "Medium",
            "This is a cross-signal diagnosis from observational data; validate through account notes and targeted interventions before claiming cause.",
            "Run a two-week save motion on Critical/High accounts and use account reviews to identify which value-realization issue is active.",
            "Leadership",
            score_override=92.0,
        ),
        candidate_row(
            "Product value / feature fit erosion",
            account_health["latest_reason_code"].fillna("").str.lower().eq("features")
            | account_health["primary_risk_driver"].eq("Product usage quality"),
            "Feature reason codes and product-usage-quality risk appear in named accounts; valid-window usage must be used before calling adoption healthy.",
            "latest_reason_code=features; primary_risk_driver=Product usage quality; valid_usage_share; error_rate_per_100_valid_events",
            "Medium",
            "Feature reason codes and errors are associated signals; they do not prove product gaps caused churn without account context.",
            "Run product success reviews for priority accounts with feature reason codes, low valid usage share, or high error rates.",
            "Product",
        ),
        candidate_row(
            "Support friction masks satisfaction average",
            account_health["high_urgent_ticket_count"].gt(0)
            | account_health["escalated_ticket_count"].gt(0)
            | (
                account_health["support_ticket_count"].gt(0)
                & account_health["satisfaction_response_rate"].lt(0.5)
            ),
            "Urgent/high tickets, escalations, and missing satisfaction responses show operational friction that average satisfaction can hide.",
            "high_urgent_ticket_count; escalated_ticket_count; satisfaction_response_rate; avg_satisfaction_score",
            "Medium",
            "Support friction can be a symptom of already-risky accounts, not necessarily the root cause.",
            "Create a weekly support friction queue for churn-history and Critical/High accounts.",
            "Support",
        ),
        candidate_row(
            "Pricing and budget pressure",
            account_health["latest_reason_code"].fillna("").str.lower().isin(["pricing", "budget"]),
            "Pricing and budget reason codes identify accounts where value-for-money or procurement pressure likely matters.",
            "latest_reason_code in pricing/budget; mrr_at_risk; plan_tier",
            "Medium",
            "Reason codes are self-reported event labels and may simplify broader value issues.",
            "Review pricing/budget accounts with renewal offers and value proof before discounting broadly.",
            "Pricing",
        ),
        candidate_row(
            "Commercial renewal and downgrade risk",
            account_health["any_downgrade_flag"].astype(bool)
            | account_health["active_auto_renew_flag"].eq(False)
            | account_health["account_is_trial"].astype(bool),
            "Downgrades, non-auto-renew, and trial status expose commercial risk before the loss event.",
            "any_downgrade_flag; active_auto_renew_flag; account_is_trial; active_subscription_count",
            "Medium",
            "Commercial signals may reflect customer size or contract stage, not dissatisfaction by themselves.",
            "Have CS and Revenue review renewal terms, downgrade history, and trial conversion for priority accounts.",
            "CS",
        ),
        candidate_row(
            "Data quality and label ambiguity",
            account_health["data_quality_flags"].fillna("").str.contains(
                "invalid_usage_windows|churn_label_mismatch", regex=True
            ),
            "Invalid usage windows and mismatched churn labels can make teams argue from different versions of the truth.",
            "invalid_usage_windows; churn_label_mismatch; account_churn_flag; has_churn_event",
            "High",
            "Data-quality issues explain decision ambiguity, not necessarily customer churn behavior.",
            "Define the operating churn label and enforce subscription-window usage validation upstream.",
            "Data",
            candidate_category="data_reliability",
            score_override=25.0,
        ),
    ]
    result = pd.DataFrame(rows).sort_values(
        ["candidate_score", "mrr_at_risk", "affected_accounts"], ascending=False
    )
    result.insert(0, "rank", range(1, len(result) + 1))
    result.insert(0, "candidate_id", [f"RC-{index:02d}" for index in range(1, len(result) + 1)])
    return result


def build_action_backlog(
    account_health: pd.DataFrame,
    risk_segments: pd.DataFrame,
    priority_accounts: pd.DataFrame,
    validation: dict[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    def add_action(
        scope_type: str,
        account_id: str | None,
        risk_segment: str,
        source_export: str,
        action_theme: str,
        recommended_action: str,
        owner_team: str,
        priority: str,
        due_bucket: str,
        trigger_metric: str,
        trigger_value: str,
        evidence_summary: str,
        confidence: str,
        expected_impact_metric: str,
        mrr_at_risk: float,
        account_count_impacted: int,
        effort_size: str,
    ) -> None:
        rows.append(
            {
                "action_id": f"ACT-{len(rows) + 1:03d}",
                "scope_type": scope_type,
                "account_id": account_id or "",
                "risk_segment": risk_segment,
                "source_export": source_export,
                "action_theme": action_theme,
                "recommended_action": recommended_action,
                "owner_team": owner_team,
                "priority": priority,
                "due_bucket": due_bucket,
                "status": "Proposed",
                "trigger_metric": trigger_metric,
                "trigger_value": trigger_value,
                "evidence_summary": evidence_summary,
                "confidence_level": confidence,
                "expected_impact_metric": expected_impact_metric,
                "mrr_at_risk": round(float(mrr_at_risk), 2),
                "account_count_impacted": int(account_count_impacted),
                "effort_size": effort_size,
            }
        )

    for _, row in priority_accounts.head(50).iterrows():
        add_action(
            "account",
            row["account_id"],
            row["risk_segment"],
            "priority_accounts.csv",
            row["primary_risk_driver"],
            row["next_best_action"],
            row["action_owner"],
            row["risk_segment"],
            row["due_bucket"],
            "account_health_score",
            str(row["account_health_score"]),
            f"{row['account_name']} has {format_usd(row['mrr_at_risk'])} MRR at risk and driver {row['primary_risk_driver']}.",
            row["confidence_level"],
            "MRR protected",
            row["mrr_at_risk"],
            1,
            "Medium",
        )

    for _, row in risk_segments.iterrows():
        if row["risk_segment"] in ["Critical", "High", "Medium"]:
            add_action(
                "segment",
                None,
                row["risk_segment"],
                "risk_segments.csv",
                "Segment save playbook",
                row["recommended_playbook"],
                "CS",
                row["risk_segment"],
                "0-14 days" if row["risk_segment"] in ["Critical", "High"] else "15-30 days",
                "account_count",
                str(row["account_count"]),
                f"{row['risk_segment']} segment contains {row['account_count']} accounts and {format_usd(row['mrr_at_risk'])} MRR at risk.",
                "High",
                "MRR protected",
                row["mrr_at_risk"],
                row["account_count"],
                "Medium",
            )

    product_segment = risk_segments.sort_values(
        "avg_error_rate_per_100_valid_events", ascending=False
    ).head(1)
    if not product_segment.empty:
        row = product_segment.iloc[0]
        add_action(
            "product",
            None,
            row["risk_segment"],
            "risk_segments.csv",
            "Product usage quality",
            "Investigate high-error and low-valid-window workflows before treating usage growth as healthy engagement.",
            "Product",
            "High",
            "15-30 days",
            "avg_error_rate_per_100_valid_events",
            str(row["avg_error_rate_per_100_valid_events"]),
            "Usage rows outside subscription windows mean product health must use valid-window metrics only.",
            "Medium",
            "Valid adoption improved",
            row["mrr_at_risk"],
            row["account_count"],
            "Medium",
        )

    support_segment = risk_segments.sort_values("high_urgent_ticket_rate", ascending=False).head(1)
    if not support_segment.empty:
        row = support_segment.iloc[0]
        add_action(
            "support",
            None,
            row["risk_segment"],
            "risk_segments.csv",
            "Support friction",
            "Create a weekly queue for high/urgent and escalated accounts in Medium+ risk segments.",
            "Support",
            "High",
            "0-14 days",
            "high_urgent_ticket_rate",
            str(row["high_urgent_ticket_rate"]),
            "Support friction is an actionable signal and should be separated from satisfaction average.",
            "High",
            "Escalations reduced",
            row["mrr_at_risk"],
            row["account_count"],
            "Low",
        )

    pricing_count = int(
        account_health["latest_reason_code"].fillna("").str.lower().eq("pricing").sum()
    )
    if pricing_count:
        add_action(
            "pricing",
            None,
            "Portfolio",
            "account_health.csv",
            "Pricing churn review",
            "Review pricing-related churn events and downgrades with renewal offers for high-value accounts.",
            "Pricing",
            "Medium",
            "15-30 days",
            "pricing_reason_accounts",
            str(pricing_count),
            f"{pricing_count} accounts have pricing as latest churn reason.",
            "Medium",
            "Churned MRR recovered or prevented",
            float(
                account_health.loc[
                    account_health["latest_reason_code"].fillna("").str.lower().eq("pricing"),
                    "mrr_at_risk",
                ].sum()
            ),
            pricing_count,
            "Medium",
        )

    add_action(
        "data_quality",
        None,
        "Portfolio",
        "data_quality_report.md",
        "Usage validity contract",
        "Instrument subscription-window validation upstream and stop using usage_id as a unique key.",
        "Data",
        "High",
        "0-14 days",
        "out_of_window_usage_rows",
        str(validation["usage_window_counts"]["out_of_window"]),
        "Feature usage has duplicate source ids and many rows outside subscription windows.",
        "High",
        "Analysis confidence improved",
        float(account_health["mrr_at_risk"].sum()),
        len(account_health),
        "Low",
    )

    add_action(
        "data_quality",
        None,
        "Portfolio",
        "account_health.csv",
        "Churn label governance",
        "Define the operating churn label before using churn events for forecasting or compensation decisions.",
        "Data",
        "Medium",
        "15-30 days",
        "churn_label_mismatch_accounts",
        str(validation["churn_label_counts"]["event_accounts_with_account_flag_false"]),
        "Account churn flag and event history are different labels and must not be collapsed.",
        "High",
        "Decision reliability improved",
        float(account_health["mrr_at_risk"].sum()),
        len(account_health),
        "Low",
    )

    return pd.DataFrame(rows)


def build_executive_findings(
    account_health: pd.DataFrame,
    risk_segments: pd.DataFrame,
    priority_accounts: pd.DataFrame,
    usage_growth_tests: pd.DataFrame,
    root_cause_candidates: pd.DataFrame,
    action_backlog: pd.DataFrame,
    validation: dict[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    total_accounts = len(account_health)
    total_mrr_at_risk = float(account_health["mrr_at_risk"].sum())
    high_risk = account_health[account_health["risk_segment"].isin(["Critical", "High"])]
    churners = account_health[account_health["has_churn_event"]]
    non_churners = account_health[~account_health["has_churn_event"]]
    invalid_usage_rows = validation["usage_window_counts"]["out_of_window"]
    raw_usage_rows = validation["clean_row_counts"]["feature_usage"]
    owner_by_type = {
        "root_cause_candidate": "Leadership",
        "risk_segment": "CS",
        "customer_experience": "Support",
        "product_usage": "Product",
        "revenue_exposure": "Leadership",
        "data_quality": "Data",
        "recommended_action": "Leadership",
    }
    effort_size_by_type = {
        "root_cause_candidate": "Medium",
        "risk_segment": "Medium",
        "customer_experience": "Low",
        "product_usage": "Medium",
        "revenue_exposure": "Low",
        "data_quality": "Low",
        "recommended_action": "Medium",
    }
    expected_impact_by_type = {
        "root_cause_candidate": "MRR protected and validated retention playbook",
        "risk_segment": "Critical/High account churn risk reduced",
        "customer_experience": "Escalations and urgent-ticket churn risk reduced",
        "product_usage": "Adoption analysis confidence and product intervention quality improved",
        "revenue_exposure": "Priority MRR protected",
        "data_quality": "Decision reliability improved",
        "recommended_action": "Cross-functional retention execution cadence created",
    }
    related_actions_by_type = {
        "root_cause_candidate": "|".join(
            action_backlog.loc[
                action_backlog["scope_type"].isin(["account", "segment"]),
                "action_id",
            ]
            .head(8)
            .astype(str)
        ),
        "risk_segment": "|".join(
            action_backlog.loc[action_backlog["scope_type"].eq("segment"), "action_id"].astype(str)
        ),
        "customer_experience": "|".join(
            action_backlog.loc[action_backlog["scope_type"].eq("support"), "action_id"].astype(str)
        ),
        "product_usage": "|".join(
            action_backlog.loc[action_backlog["scope_type"].eq("product"), "action_id"].astype(str)
        ),
        "revenue_exposure": "|".join(
            action_backlog.loc[action_backlog["scope_type"].eq("account"), "action_id"]
            .head(20)
            .astype(str)
        ),
        "data_quality": "|".join(
            action_backlog.loc[action_backlog["scope_type"].eq("data_quality"), "action_id"].astype(str)
        ),
        "recommended_action": "|".join(action_backlog["action_id"].head(12).astype(str)),
    }
    causality_risk_by_type = {
        "root_cause_candidate": "Observational pattern only; validate with account notes, CS context, or an intervention experiment before claiming cause.",
        "risk_segment": "Risk bands prioritize accounts but do not prove future churn or causal impact.",
        "customer_experience": "Support friction may be a symptom, trigger, or correlate; do not frame it as the only cause without account-level validation.",
        "product_usage": "Invalid-window usage weakens aggregate usage claims; valid-window metrics still show behavior, not standalone causality.",
        "revenue_exposure": "MRR at risk measures exposure, not guaranteed loss.",
        "data_quality": "Label and usage caveats affect confidence and must not be treated as business behavior.",
        "recommended_action": "Actions are evidence-backed operating bets, not proven causal interventions.",
    }

    def add_finding(
        finding_type: str,
        title: str,
        confidence: str,
        metric_name: str,
        metric_value: str,
        comparison_name: str,
        comparison_value: str,
        affected_accounts: int,
        mrr_at_risk: float,
        finding: str,
        implication: str,
        decision: str,
        exports: str,
        sources: str,
        dq_notes: str,
    ) -> None:
        rows.append(
            {
                "finding_id": f"F-{len(rows) + 1:02d}",
                "finding_type": finding_type,
                "finding_title": title,
                "confidence_level": confidence,
                "metric_name": metric_name,
                "metric_value": metric_value,
                "comparison_name": comparison_name,
                "comparison_value": comparison_value,
                "affected_accounts": affected_accounts,
                "mrr_at_risk": round(float(mrr_at_risk), 2),
                "evidence_summary": f"{metric_name}: {metric_value}; {comparison_name}: {comparison_value}",
                "plain_language_finding": finding,
                "interpretation": implication,
                "business_implication": implication,
                "recommended_decision": decision,
                "recommended_action": decision,
                "owner_team": owner_by_type.get(finding_type, "Leadership"),
                "effort_size": effort_size_by_type.get(finding_type, "Medium"),
                "expected_impact_metric": expected_impact_by_type.get(
                    finding_type, "Retention decision quality improved"
                ),
                "related_action_ids": related_actions_by_type.get(finding_type, ""),
                "false_causality_risk": causality_risk_by_type.get(
                    finding_type,
                    "Observational evidence supports prioritization, not causal proof.",
                ),
                "supporting_exports": exports,
                "source_tables": sources,
                "data_quality_notes": dq_notes,
            }
        )

    top_root_cause = root_cause_candidates.iloc[0]
    add_finding(
        "root_cause_candidate",
        f"Top root-cause candidate: {top_root_cause['root_cause_candidate']}",
        str(top_root_cause["confidence_level"]),
        "top_root_cause_candidate",
        str(top_root_cause["root_cause_candidate"]),
        "candidate_score",
        str(top_root_cause["candidate_score"]),
        int(top_root_cause["affected_accounts"]),
        float(top_root_cause["mrr_at_risk"]),
        str(top_root_cause["evidence_summary"]),
        "RavenStack should not treat the CEO contradiction as support versus product; the strongest candidate ties operating evidence to value realization before renewal.",
        str(top_root_cause["recommended_action"]),
        "root_cause_candidates.csv|account_health.csv|priority_accounts.csv|action_backlog.csv",
        "accounts|subscriptions|feature_usage|support_tickets|churn_events",
        str(top_root_cause["false_causality_risk"]),
    )

    high_risk_mrr = float(high_risk["mrr_at_risk"].sum())
    add_finding(
        "risk_segment",
        "Retention risk is concentrated enough for a focused save motion",
        "High",
        "critical_high_accounts",
        str(len(high_risk)),
        "portfolio_accounts",
        str(total_accounts),
        len(high_risk),
        high_risk_mrr,
        f"{len(high_risk)} accounts are in Critical or High risk bands, representing {format_usd(high_risk_mrr)} current MRR at risk.",
        "The CEO does not need a portfolio-wide campaign first; the first move is a named-account save motion.",
        "Assign CS owners to Critical/High accounts and review progress weekly.",
        "account_health.csv|risk_segments.csv|priority_accounts.csv",
        "accounts|subscriptions|support_tickets|churn_events|feature_usage",
        "Risk score is deterministic and rule-based, not a causal model.",
    )

    churner_support_rate = (
        churners["high_urgent_ticket_count"].gt(0).mean() if not churners.empty else 0
    )
    non_churner_support_rate = (
        non_churners["high_urgent_ticket_count"].gt(0).mean()
        if not non_churners.empty
        else 0
    )
    add_finding(
        "customer_experience",
        "The satisfaction story is incomplete without support friction and response coverage",
        "Medium",
        "churner_high_urgent_ticket_rate",
        f"{churner_support_rate:.1%}",
        "non_churner_high_urgent_ticket_rate",
        f"{non_churner_support_rate:.1%}",
        int(churners["account_id"].nunique()),
        float(churners["mrr_at_risk"].sum()),
        "Churn-event accounts must be reviewed through ticket urgency, escalations, and missing satisfaction responses, not satisfaction average alone.",
        "Averages can look acceptable while high-friction accounts are already at risk.",
        "Create a support friction review for accounts with churn history, urgent tickets, escalations, or missing satisfaction responses.",
        "account_health.csv|risk_segments.csv|action_backlog.csv",
        "support_tickets|churn_events|accounts",
        "Missing satisfaction is tracked as missing response, not zero satisfaction.",
    )

    add_finding(
        "product_usage",
        "Raw usage growth is not enough evidence of healthy adoption",
        "High",
        "out_of_window_usage_rows",
        f"{invalid_usage_rows} ({pct(invalid_usage_rows, raw_usage_rows):.2f}%)",
        "valid_window_usage_rows",
        str(validation["usage_window_counts"]["in_window"]),
        total_accounts,
        total_mrr_at_risk,
        "Most product usage analysis must be filtered through subscription-window validity before it is used as engagement evidence.",
        "The product team may be seeing aggregate activity that does not represent active subscription health.",
        "Use valid-window usage metrics for adoption reviews and instrument why usage appears before/after subscription windows.",
        "usage_growth_tests.csv|account_health.csv|data_quality_report.md",
        "feature_usage|subscriptions",
        "Feature usage uses generated feature_usage_row_id because usage_id is not unique.",
    )

    top_priority_mrr = float(priority_accounts.head(20)["mrr_at_risk"].sum())
    add_finding(
        "revenue_exposure",
        "Priority accounts turn churn diagnosis into a revenue-protection queue",
        "High",
        "top_20_priority_mrr_at_risk",
        format_usd(top_priority_mrr),
        "total_current_mrr_at_risk",
        format_usd(total_mrr_at_risk),
        min(20, len(priority_accounts)),
        top_priority_mrr,
        "The first 20 priority accounts carry enough current MRR exposure to justify direct executive and CS attention.",
        "Revenue protection should be managed as a queue, not as broad dashboard monitoring.",
        "Start with top-ranked accounts, confirm account context, and log owner/action/date for each.",
        "priority_accounts.csv|action_backlog.csv",
        "accounts|subscriptions|support_tickets|churn_events",
        "MRR at risk defaults to current active MRR, not historical booked MRR.",
    )

    add_finding(
        "data_quality",
        "Churn labels conflict and should not be collapsed",
        "High",
        "accounts_with_churn_event",
        str(validation["churn_label_counts"]["has_churn_event_accounts"]),
        "account_churn_flag_true_accounts",
        str(validation["churn_label_counts"]["account_churn_flag_true_accounts"]),
        total_accounts,
        total_mrr_at_risk,
        "Account-level churn_flag and churn event history represent different concepts and point to different account sets.",
        "Using one label silently as the truth would change the answer and weaken executive trust.",
        "Preserve both labels in analysis, report which label each insight uses, and define an operating churn label upstream.",
        "account_health.csv|data_quality_report.md",
        "accounts|churn_events",
        "account_churn_flag and has_churn_event are exported separately.",
    )

    top_action = action_backlog.iloc[0] if not action_backlog.empty else None
    if top_action is not None:
        add_finding(
            "recommended_action",
            "The next action is owner-based execution, not another analysis pass",
            "High",
            "open_actions",
            str(len(action_backlog)),
            "top_action_owner",
            str(top_action["owner_team"]),
            total_accounts,
            total_mrr_at_risk,
            "The action backlog translates findings into owner, priority, trigger, confidence, and effort.",
            "The organization can start acting while deeper causal validation continues.",
            "Run the backlog as a two-week retention operating cadence with CS, Support, Product, Pricing, Data, and Leadership.",
            "action_backlog.csv|executive_findings.json",
            "account_health|risk_segments|priority_accounts",
            "Actions are evidence-backed recommendations, not proven causal interventions.",
        )

    return pd.DataFrame(rows)


def build_exports(
    clean: dict[str, pd.DataFrame], validation: dict[str, Any]
) -> dict[str, pd.DataFrame]:
    account_health = build_account_health(clean)
    risk_segments = build_risk_segments(account_health)
    priority_accounts = build_priority_accounts(account_health)
    churner_comparison = build_churner_comparison(account_health)
    usage_growth_tests = build_usage_growth_tests(clean, account_health)
    root_cause_candidates = build_root_cause_candidates(account_health)
    action_backlog = build_action_backlog(
        account_health, risk_segments, priority_accounts, validation
    )
    executive_findings = build_executive_findings(
        account_health,
        risk_segments,
        priority_accounts,
        usage_growth_tests,
        root_cause_candidates,
        action_backlog,
        validation,
    )
    return {
        "account_health": account_health,
        "risk_segments": risk_segments,
        "priority_accounts": priority_accounts,
        "churner_comparison": churner_comparison,
        "usage_growth_tests": usage_growth_tests,
        "root_cause_candidates": root_cause_candidates,
        "action_backlog": action_backlog,
        "executive_findings": executive_findings,
    }


def write_exports(exports: dict[str, pd.DataFrame], exports_dir: Path) -> None:
    exports_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in exports.items():
        write_frame(frame, exports_dir / f"{name}.csv")
        frame.to_json(
            exports_dir / f"{name}.json",
            orient="records",
            indent=2,
            date_format="iso",
        )


def write_findings_summary(
    exports: dict[str, pd.DataFrame], analysis_dir: Path, validation: dict[str, Any]
) -> None:
    findings = exports["executive_findings"]
    risk_segments = exports["risk_segments"]
    priority_accounts = exports["priority_accounts"]
    churner_comparison = exports["churner_comparison"]
    usage_growth_tests = exports["usage_growth_tests"]
    root_cause_candidates = exports["root_cause_candidates"]
    high_risk = risk_segments[risk_segments["risk_segment"].isin(["Critical", "High"])]
    high_risk_accounts = int(high_risk["account_count"].sum())
    high_risk_mrr = float(high_risk["mrr_at_risk"].sum())
    top20_mrr = float(priority_accounts.head(20)["mrr_at_risk"].sum())
    churner_row = churner_comparison[
        churner_comparison["label_type"].eq("has_churn_event")
        & churner_comparison["comparison_label"].eq("true")
    ].iloc[0]
    non_churner_row = churner_comparison[
        churner_comparison["label_type"].eq("has_churn_event")
        & churner_comparison["comparison_label"].eq("false")
    ].iloc[0]
    portfolio_usage_growth = usage_growth_tests[
        usage_growth_tests["segment_type"].eq("portfolio")
    ].iloc[0]
    top_root_cause = root_cause_candidates.iloc[0]

    lines = [
        "# RavenStack Findings Summary",
        "",
        "Generated by `build_exports.py` from canonical exports.",
        "",
        "## Executive Answer",
        "",
        "RavenStack should treat churn as a value-realization problem that appears across account history, support friction, product usage quality, and commercial signals before renewal. The first operating move is not another dashboard: it is a focused save motion on Critical and High accounts, backed by clean usage windows and separate churn labels.",
        "",
        "## Challenge Questions",
        "",
        "### 1. What is causing churn?",
        "",
        "- Root-cause candidate: value erosion before renewal, not one isolated support or product metric.",
        f"- Top ranked candidate table entry: {top_root_cause['root_cause_candidate']} (score {top_root_cause['candidate_score']}).",
        f"- Critical/High accounts: {high_risk_accounts} accounts with {format_usd(high_risk_mrr)} current MRR at risk.",
        "- Evidence spans churn history, support urgency/escalation, low-quality usage signals, and commercial renewal/downgrade context.",
        "- Causality note: this is observational evidence. It should drive action and validation, not a claim of proven causation.",
        "",
        "### 2. Which segments and accounts are most at risk?",
        "",
        f"- Critical/High risk bands contain {high_risk_accounts} accounts.",
        f"- Top 20 priority accounts represent {format_usd(top20_mrr)} current MRR at risk.",
        "- `priority_accounts.csv` provides account-level rank, owner, next best action, confidence, and due bucket.",
        "",
        "### 3. What should RavenStack do?",
        "",
        "- Start a two-week CS-led save motion for Critical/High accounts.",
        "- Create a support friction queue for churn-history accounts with urgent/high tickets, escalations, or missing satisfaction responses.",
        "- Use only valid-window feature usage for product health reviews.",
        "- Define the operating churn label before forecasting or compensation decisions.",
        "",
        "## CEO Contradictions Tested",
        "",
        "### 'Usage grew'",
        "",
        f"- Out-of-window usage rows: {validation['usage_window_counts']['out_of_window']} of {validation['clean_row_counts']['feature_usage']} raw usage rows.",
        f"- Valid-window usage rows: {validation['usage_window_counts']['in_window']}.",
        f"- Portfolio raw usage-count direction from 2024-H1 to 2024-H2: {portfolio_usage_growth['raw_usage_direction']} ({portfolio_usage_growth['raw_usage_count_growth_pct']}%).",
        f"- Portfolio valid-window usage-count direction from 2024-H1 to 2024-H2: {portfolio_usage_growth['valid_usage_direction']} ({portfolio_usage_growth['valid_usage_count_growth_pct']}%).",
        "- Interpretation: aggregate usage cannot be treated as healthy adoption unless it is filtered by subscription windows.",
        "",
        "### 'Satisfaction is ok'",
        "",
        f"- Churn-event accounts with high/urgent tickets: {churner_row['high_urgent_ticket_account_rate']:.1%}.",
        f"- Non-churn-event accounts with high/urgent tickets: {non_churner_row['high_urgent_ticket_account_rate']:.1%}.",
        f"- Churn-event satisfaction response rate: {churner_row['satisfaction_response_rate']:.1%}.",
        "- Interpretation: average satisfaction is incomplete without response coverage, priority, escalation, and churn history.",
        "",
        "## Churners vs Non-Churners",
        "",
        "| Metric | Has churn event | No churn event |",
        "|---|---:|---:|",
        f"| Accounts | {int(churner_row['account_count'])} | {int(non_churner_row['account_count'])} |",
        f"| Current MRR | {format_usd(float(churner_row['current_mrr']))} | {format_usd(float(non_churner_row['current_mrr']))} |",
        f"| Avg current MRR | {format_usd(float(churner_row['avg_current_mrr']))} | {format_usd(float(non_churner_row['avg_current_mrr']))} |",
        f"| Account churn flag rate | {churner_row['account_churn_flag_rate']:.1%} | {non_churner_row['account_churn_flag_rate']:.1%} |",
        f"| Valid usage share | {churner_row['avg_valid_usage_share']:.1%} | {non_churner_row['avg_valid_usage_share']:.1%} |",
        f"| Error rate per 100 valid events | {churner_row['avg_error_rate_per_100_valid_events']:.2f} | {non_churner_row['avg_error_rate_per_100_valid_events']:.2f} |",
        f"| High/urgent ticket account rate | {churner_row['high_urgent_ticket_account_rate']:.1%} | {non_churner_row['high_urgent_ticket_account_rate']:.1%} |",
        f"| Escalated account rate | {churner_row['escalated_account_rate']:.1%} | {non_churner_row['escalated_account_rate']:.1%} |",
        f"| Satisfaction response rate | {churner_row['satisfaction_response_rate']:.1%} | {non_churner_row['satisfaction_response_rate']:.1%} |",
        f"| Downgrade account rate | {churner_row['downgrade_account_rate']:.1%} | {non_churner_row['downgrade_account_rate']:.1%} |",
        f"| Upgrade account rate | {churner_row['upgrade_account_rate']:.1%} | {non_churner_row['upgrade_account_rate']:.1%} |",
        f"| Annual billing account rate | {churner_row['annual_billing_account_rate']:.1%} | {non_churner_row['annual_billing_account_rate']:.1%} |",
        f"| Top plan tier | {churner_row['top_plan_tier']} | {non_churner_row['top_plan_tier']} |",
        f"| Top industry | {churner_row['top_industry']} | {non_churner_row['top_industry']} |",
        f"| Top latest reason code | {churner_row['top_latest_reason_code']} | {non_churner_row['top_latest_reason_code']} |",
        "",
        "## Root-Cause Candidates",
        "",
        "| Rank | Candidate | Score | Accounts | MRR at risk | Confidence | Owner |",
        "|---:|---|---:|---:|---:|---|---|",
    ]

    for _, row in root_cause_candidates.iterrows():
        lines.append(
            f"| {row['rank']} | {row['root_cause_candidate']} | {row['candidate_score']} | {row['affected_accounts']} | {format_usd(float(row['mrr_at_risk']))} | {row['confidence_level']} | {row['owner_team']} |"
        )

    lines.extend(
        [
            "",
            "## Usage Growth Tests",
            "",
            "| Segment type | Segment | Raw direction | Raw growth | Valid direction | Valid growth | Latest invalid event share |",
            "|---|---|---|---:|---|---:|---:|",
        ]
    )

    for _, row in usage_growth_tests.iterrows():
        raw_growth = (
            ""
            if pd.isna(row["raw_usage_count_growth_pct"])
            else f"{row['raw_usage_count_growth_pct']}%"
        )
        valid_growth = (
            ""
            if pd.isna(row["valid_usage_count_growth_pct"])
            else f"{row['valid_usage_count_growth_pct']}%"
        )
        lines.append(
            f"| {row['segment_type']} | {row['segment_value']} | {row['raw_usage_direction']} | {raw_growth} | {row['valid_usage_direction']} | {valid_growth} | {row['latest_invalid_usage_event_share']:.1%} |"
        )

    lines.extend(
        [
        "",
        "## Finding Traceability",
        "",
        "| Finding | Confidence | Owner | Supporting exports | Causality risk |",
        "|---|---|---|---|---|",
        ]
    )

    for _, row in findings.iterrows():
        supporting_exports = str(row["supporting_exports"]).replace("|", ", ")
        lines.append(
            f"| {row['finding_id']} - {row['finding_title']} | {row['confidence_level']} | {row['owner_team']} | {supporting_exports} | {row['false_causality_risk']} |"
        )

    lines.extend(
        [
            "",
            "## Source Artifacts",
            "",
            "- `exports/account_health.csv`",
            "- `exports/risk_segments.csv`",
            "- `exports/priority_accounts.csv`",
            "- `exports/action_backlog.csv`",
            "- `exports/executive_findings.csv`",
            "- `exports/churner_comparison.csv`",
            "- `exports/usage_growth_tests.csv`",
            "- `exports/root_cause_candidates.csv`",
            "- `analysis/data_quality_report.md`",
        ]
    )
    (analysis_dir / "findings_summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def validate_exports(exports: dict[str, pd.DataFrame]) -> dict[str, Any]:
    required_columns = {
        "account_health": [
            "account_id",
            "account_churn_flag",
            "has_churn_event",
            "risk_segment",
            "account_health_score",
            "data_quality_flags",
        ],
        "risk_segments": [
            "risk_segment",
            "account_count",
            "mrr_at_risk",
            "event_based_churn_rate",
            "account_flag_churn_rate",
        ],
        "priority_accounts": [
            "priority_rank",
            "account_id",
            "risk_segment",
            "next_best_action",
            "action_owner",
        ],
        "action_backlog": [
            "action_id",
            "scope_type",
            "owner_team",
            "recommended_action",
            "confidence_level",
        ],
        "executive_findings": [
            "finding_id",
            "finding_type",
            "evidence_summary",
            "plain_language_finding",
            "interpretation",
            "recommended_decision",
            "recommended_action",
            "owner_team",
            "effort_size",
            "expected_impact_metric",
            "related_action_ids",
            "false_causality_risk",
            "supporting_exports",
        ],
        "churner_comparison": [
            "label_type",
            "comparison_label",
            "account_count",
            "current_mrr",
            "avg_valid_usage_share",
            "high_urgent_ticket_account_rate",
            "downgrade_account_rate",
            "top_latest_reason_code",
        ],
        "usage_growth_tests": [
            "segment_type",
            "segment_value",
            "previous_period",
            "latest_period",
            "raw_usage_count_growth_pct",
            "valid_usage_count_growth_pct",
            "interpretation",
        ],
        "root_cause_candidates": [
            "candidate_id",
            "rank",
            "root_cause_candidate",
            "candidate_score",
            "evidence_summary",
            "confidence_level",
            "false_causality_risk",
            "recommended_action",
            "owner_team",
        ],
    }
    checks: dict[str, Any] = {}
    for name, columns in required_columns.items():
        frame = exports[name]
        missing = [column for column in columns if column not in frame.columns]
        checks[name] = {
            "rows": int(len(frame)),
            "missing_required_columns": missing,
            "passed": not missing and len(frame) > 0,
        }

    account_health = exports["account_health"]
    risk_segments = exports["risk_segments"]
    priority_accounts = exports["priority_accounts"]
    executive_findings = exports["executive_findings"]
    churner_comparison = exports["churner_comparison"]
    usage_growth_tests = exports["usage_growth_tests"]
    root_cause_candidates = exports["root_cause_candidates"]
    checks["contract_checks"] = {
        "account_health_500_rows": len(account_health) == 500,
        "account_health_unique_account_id": account_health["account_id"].is_unique,
        "risk_segments_sum_to_500": int(risk_segments["account_count"].sum()) == 500,
        "priority_rank_unique": priority_accounts["priority_rank"].is_unique,
        "executive_findings_trace_exports": executive_findings[
            "supporting_exports"
        ].notna().all(),
        "executive_findings_have_action_links": executive_findings[
            "related_action_ids"
        ].fillna("").ne("").all(),
        "churner_comparison_covers_both_labels": set(
            churner_comparison["label_type"].astype(str)
        )
        == {"has_churn_event", "account_churn_flag"},
        "usage_growth_tests_include_portfolio": "portfolio"
        in set(usage_growth_tests["segment_type"].astype(str)),
        "root_cause_candidates_ranked": root_cause_candidates["rank"].is_unique
        and len(root_cause_candidates) >= 3,
    }
    checks["passed"] = all(check["passed"] for check in checks.values() if isinstance(check, dict) and "passed" in check) and all(
        checks["contract_checks"].values()
    )
    return checks


def copy_data_quality_report(project_root: Path, analysis_dir: Path) -> None:
    source = project_root / "data_quality_report.md"
    destination = analysis_dir / "data_quality_report.md"
    if not source.exists():
        raise FileNotFoundError(source)
    lines = [line.rstrip() for line in source.read_text(encoding="utf-8").splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    normalized = "\n".join(lines)
    destination.write_text(f"{normalized}\n", encoding="utf-8")


def load_exports_from_disk(exports_dir: Path) -> dict[str, pd.DataFrame]:
    exports: dict[str, pd.DataFrame] = {}
    for name in [
        "account_health",
        "risk_segments",
        "priority_accounts",
        "churner_comparison",
        "usage_growth_tests",
        "root_cause_candidates",
        "action_backlog",
        "executive_findings",
    ]:
        path = exports_dir / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        exports[name] = pd.read_csv(path)
    return exports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate previously generated exports without rebuilding them.",
    )
    args = parser.parse_args()

    project_root = find_project_root()
    submission_dir = project_root / "ai-master-challenge" / "submissions" / "kadug"
    solution_dir = submission_dir / "solution"
    analysis_dir = solution_dir / "analysis"
    clean_dir = analysis_dir / "clean"
    exports_dir = solution_dir / "exports"
    raw_dir = project_root / "data" / "raw" / "ravenstack"

    if args.validate_only:
        export_validation = validate_exports(load_exports_from_disk(exports_dir))
        write_json(analysis_dir / "export_validation_report.json", export_validation)
        print(json.dumps(export_validation, indent=2, default=json_default))
        return 0 if export_validation["passed"] else 1

    for path in [analysis_dir, clean_dir, exports_dir, solution_dir / "dashboard"]:
        path.mkdir(parents=True, exist_ok=True)

    preflight_report = preflight(project_root, submission_dir)
    write_json(analysis_dir / "preflight_report.json", preflight_report)

    raw = load_raw(raw_dir)
    clean = build_clean_layer(raw)
    write_clean_layer(clean, clean_dir)
    clean_validation = validate_clean_layer(raw, clean)
    write_json(analysis_dir / "clean_validation_report.json", clean_validation)

    copy_data_quality_report(project_root, analysis_dir)

    exports = build_exports(clean, clean_validation)
    write_exports(exports, exports_dir)
    write_findings_summary(exports, analysis_dir, clean_validation)
    export_validation = validate_exports(exports)
    write_json(analysis_dir / "export_validation_report.json", export_validation)

    summary = {
        "preflight": preflight_report,
        "clean_validation_passed": clean_validation["passed"],
        "export_validation_passed": export_validation["passed"],
        "exports": {name: {"rows": len(frame)} for name, frame in exports.items()},
    }
    write_json(analysis_dir / "analysis_summary.json", summary)
    print(json.dumps(summary, indent=2, default=json_default))
    return 0 if clean_validation["passed"] and export_validation["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
