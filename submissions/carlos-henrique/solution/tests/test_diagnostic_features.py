"""Tests for Phase 3 feature grains, cutoffs, windows and privacy."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from diagnostic_features import build_account_features, build_subscription_features  # noqa: E402


def _event(event_id: str, account: str, when: str, kind: str, *, status: str = "VALID", subscription: str | None = None, numeric: float | None = None, category: str | None = None) -> dict:
    return {
        "event_id": event_id, "account_id": account, "subscription_id": subscription,
        "event_time": pd.Timestamp(when), "event_type": kind, "event_value_numeric": numeric,
        "event_value_category": category, "source_record_id": event_id,
        "event_order_on_same_day": 1, "quality_status": status,
        "quality_flags": "" if status == "VALID" else "TEST_WARNING", "is_quarantined": False,
    }


def _frames():
    events = pd.DataFrame([
        _event("E1", "A1", "2024-01-01", "ACCOUNT_CREATED"),
        _event("E2", "A1", "2024-01-02", "SUBSCRIPTION_STARTED", subscription="S1", numeric=100, category="PRO"),
        _event("E3", "A1", "2024-01-05", "FEATURE_USED", subscription="S1", numeric=3, category="SEARCH"),
        _event("E4", "A1", "2024-01-10", "CHURN_RECORDED"),
        _event("E5", "A1", "2024-01-11", "FEATURE_USED", subscription="S1", numeric=9, category="FUTURE"),
        _event("E6", "A2", "2024-01-01", "ACCOUNT_CREATED"),
        _event("E7", "A2", "2024-01-20", "FEATURE_USED", numeric=1, category="SEARCH"),
    ])
    episodes = pd.DataFrame([
        {"episode_id": "P1", "account_id": "A1", "subscription_id": "S1", "episode_start": pd.Timestamp("2024-01-02"), "episode_end": pd.NaT, "episode_status": "OPEN", "plan": "PRO", "mrr": 100.0, "quality_status": "VALID", "quality_flags": "", "has_overlap": False},
    ])
    quarantine = pd.DataFrame([_event("Q1", "A1", "2024-01-06", "FEATURE_USED")]).assign(is_quarantined=True, quality_status="QUARANTINED")
    return events, episodes, quarantine


def test_account_grain_cutoff_windows_and_no_future() -> None:
    events, episodes, quarantine = _frames()
    result = build_account_features(events, episodes, quarantine).set_index("account_id")
    assert result.index.is_unique
    assert result.loc["A1", "feature_cutoff_time"] == pd.Timestamp("2024-01-10")
    assert result.loc["A1", "feature_event_count_lifetime"] == 1
    assert result.loc["A1", "feature_event_count_7d"] == 1
    assert result.loc["A1", "feature_event_count_30d"] == 1
    assert result.loc["A1", "feature_event_count_60d"] == 1
    assert result.loc["A1", "feature_event_count_90d"] == 1
    assert "FUTURE" not in result.to_json(date_format="iso")


def test_episode_grain_and_censoring() -> None:
    events, episodes, _ = _frames()
    result = build_subscription_features(events, episodes)
    assert len(result) == 1 and result["episode_id"].is_unique
    assert bool(result.iloc[0]["is_censored_episode"])
    assert result.iloc[0]["episode_end"] is pd.NaT or pd.isna(result.iloc[0]["episode_end"])


def test_forbidden_columns_are_absent() -> None:
    events, episodes, quarantine = _frames()
    result = build_account_features(events, episodes, quarantine)
    assert {"churn_flag", "account_name", "feedback_text", "reason_code"}.isdisjoint(result.columns)


def test_real_feature_outputs_have_required_grains_and_no_future_usage() -> None:
    processed = ROOT / "data" / "processed"
    accounts = pd.read_parquet(processed / "account_diagnostic_features.parquet")
    subscriptions = pd.read_parquet(processed / "subscription_diagnostic_features.parquet")
    events = pd.read_parquet(processed / "event_log.parquet")
    assert len(accounts) == accounts["account_id"].nunique() == 500
    assert len(subscriptions) == subscriptions["episode_id"].nunique() == 5000
    required_windows = {
        f"{prefix}_{days}d"
        for prefix in ("feature_event_count", "distinct_features", "active_days", "support_ticket_count")
        for days in (30, 90)
    } | {
        "feature_event_count_7d", "feature_event_count_60d",
        "support_ticket_count_7d", "support_ticket_count_60d",
    }
    assert required_windows.issubset(accounts.columns)
    usage = events.loc[
        events["event_type"].eq("FEATURE_USED"), ["account_id", "event_time"]
    ].merge(
        accounts[["account_id", "feature_cutoff_time"]],
        on="account_id", how="inner", validate="many_to_one",
    )
    expected = usage.loc[
        usage["event_time"].le(usage["feature_cutoff_time"])
    ].groupby("account_id").size()
    observed = accounts.set_index("account_id")["feature_event_count_lifetime"]
    assert observed.equals(expected.reindex(observed.index, fill_value=0).astype(observed.dtype))
    churned = accounts["first_churn_time"].notna()
    assert accounts.loc[churned, "feature_cutoff_time"].equals(accounts.loc[churned, "first_churn_time"])
