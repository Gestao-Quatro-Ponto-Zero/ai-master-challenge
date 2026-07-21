"""Tests for fixed-window landmark accounting and leakage controls."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from survival_dataset import build_landmark_dataset  # noqa: E402


def _inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    survival = pd.DataFrame(
        {
            "account_id": ["A1", "A2", "A3"], "is_eligible": [True, True, True],
            "exposure_start": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-12-20"]),
            "exposure_end": pd.to_datetime(["2024-01-20", "2024-03-15", "2024-12-31"]),
            "first_churn_time": pd.to_datetime(["2024-01-20", "2024-03-15", None]),
            "event_observed": pd.Series([1, 1, 0], dtype="Int64"),
            "observation_end": pd.to_datetime(["2024-12-31"] * 3),
        }
    )
    definitions = [
        ("A1", "S1", "SUBSCRIPTION_STARTED", "2024-01-01", "VALID", 100, "Basic"),
        ("A2", "S2", "SUBSCRIPTION_STARTED", "2024-01-01", "VALID", 100, "Basic"),
        ("A2", "S2", "FEATURE_USED", "2024-01-10", "VALID", 3, "feature_1"),
        ("A2", "S2", "FEATURE_USED", "2024-02-15", "VALID", 99, "future_feature"),
        ("A3", "S3", "SUBSCRIPTION_STARTED", "2024-12-20", "VALID", 100, "Basic"),
    ]
    events = pd.DataFrame(
        [
            {"event_id": f"E{i}", "account_id": a, "subscription_id": s, "event_type": t,
             "event_time": pd.Timestamp(when), "quality_status": quality, "is_quarantined": False,
             "event_order_on_same_day": 1, "event_value_numeric": value,
             "event_value_category": category, "source_record_id": f"R{i}"}
            for i, (a, s, t, when, quality, value, category) in enumerate(definitions)
        ]
    )
    episodes = pd.DataFrame(
        {"account_id": ["A1", "A2", "A3"], "subscription_id": ["S1", "S2", "S3"],
         "episode_start": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-12-20"]),
         "episode_end": [pd.NaT] * 3, "plan": ["Basic"] * 3, "mrr": [100.0] * 3}
    )
    support = pd.DataFrame({"ticket_id": [], "resolution_time_hours": []})
    return survival, events, episodes, support


def test_landmark_excludes_early_churn_and_insufficient_observation() -> None:
    build = build_landmark_dataset(*_inputs(), landmark_days=30)
    assert list(build.dataset["account_id"]) == ["A2"]
    assert build.accounting["churn_before_or_on_landmark"] == 1
    assert build.accounting["not_observable_to_landmark"] == 1
    assert build.accounting["included"] == 1


def test_landmark_features_do_not_use_future_events() -> None:
    build = build_landmark_dataset(*_inputs(), landmark_days=30)
    row = build.dataset.iloc[0]
    assert row["usage_count_landmark"] == 3
    assert row["distinct_features_landmark"] == 1
    assert row["duration_after_landmark"] >= 0


def test_landmark_population_accounting_reconciles() -> None:
    build = build_landmark_dataset(*_inputs(), landmark_days=30)
    accounted = sum(value for key, value in build.accounting.items() if key != "source_accounts")
    assert accounted == build.accounting["source_accounts"]
