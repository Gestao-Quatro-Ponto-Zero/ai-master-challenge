"""Tests for governed exposure, endpoint, censoring and account grain."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from survival_dataset import build_account_survival_dataset  # noqa: E402


def _fixtures() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    accounts = pd.DataFrame(
        {"account_id": ["A1", "A2", "A3"], "primary_outcome": ["x"] * 3, "quality_coverage_ratio": [1.0, 0.8, 0.6]}
    )
    definitions = {
        "A1": [("ACCOUNT_CREATED", "2024-01-01", "VALID", None), ("CHURN_RECORDED", "2024-01-03", "VALID", None), ("SUBSCRIPTION_STARTED", "2024-01-05", "VALID", "S1"), ("CHURN_RECORDED", "2024-01-10", "VALID", None), ("CHURN_RECORDED", "2024-01-20", "VALID", None)],
        "A2": [("ACCOUNT_CREATED", "2024-01-02", "VALID", None), ("SUBSCRIPTION_STARTED", "2024-01-05", "VALID_WITH_WARNING", "S2")],
        "A3": [("ACCOUNT_CREATED", "2024-01-03", "VALID_WITH_WARNING", None), ("SUBSCRIPTION_STARTED", "2024-01-07", "VALID", "S3"), ("CHURN_RECORDED", "2024-01-07", "VALID", None)],
    }
    rows = []
    for account_id, items in definitions.items():
        for index, (event_type, time, quality, subscription_id) in enumerate(items):
            rows.append(
                {
                    "event_id": f"{account_id}-{index}", "account_id": account_id,
                    "subscription_id": subscription_id, "event_time": pd.Timestamp(time),
                    "event_type": event_type, "event_order_on_same_day": index + 1,
                    "quality_status": quality, "is_quarantined": False,
                    "event_value_numeric": 100.0 if event_type == "SUBSCRIPTION_STARTED" else None,
                    "event_value_category": "Basic" if event_type == "SUBSCRIPTION_STARTED" else None,
                    "source_record_id": f"R{index}",
                }
            )
    events = pd.DataFrame(rows)
    episodes = pd.DataFrame(
        {
            "account_id": ["A1", "A2", "A3"], "subscription_id": ["S1", "S2", "S3"],
            "episode_start": pd.to_datetime(["2024-01-05", "2024-01-05", "2024-01-07"]),
            "episode_end": [pd.NaT, pd.NaT, pd.NaT], "plan": ["Basic", "Pro", "Basic"],
            "mrr": [100.0, 200.0, 100.0],
        }
    )
    return accounts, events, episodes


def test_account_grain_duration_binary_censoring_and_same_day() -> None:
    accounts, events, episodes = _fixtures()
    result = build_account_survival_dataset(accounts, events, episodes, observation_end="2024-01-31")
    assert len(result) == result["account_id"].nunique() == 3
    eligible = result.loc[result["is_eligible"]]
    assert eligible["duration_days"].ge(0).all()
    assert eligible["event_observed"].isin([0, 1]).all()
    assert result.set_index("account_id").loc["A2", "censoring_status"] == "RIGHT_CENSORED"
    assert bool(result.set_index("account_id").loc["A3", "same_day_event"])


def test_first_post_exposure_churn_is_endpoint_and_recurrence_does_not_replace_it() -> None:
    accounts, events, episodes = _fixtures()
    result = build_account_survival_dataset(accounts, events, episodes, observation_end="2024-01-31").set_index("account_id")
    assert result.loc["A1", "first_churn_time"] == pd.Timestamp("2024-01-10")
    assert result.loc["A1", "duration_days"] == 5.0
    assert result.loc["A1", "pre_exposure_churn_count"] == 1


def test_strict_and_signup_origins_have_explicit_exclusions() -> None:
    accounts, events, episodes = _fixtures()
    strict = build_account_survival_dataset(accounts, events, episodes, strict=True, observation_end="2024-01-31")
    assert strict.set_index("account_id").loc["A2", "exclusion_reason"] == "NO_VALID_SUBSCRIPTION_START"
    signup = build_account_survival_dataset(accounts, events, episodes, origin="signup", observation_end="2024-01-31")
    assert signup["is_eligible"].all()
    assert signup["time_origin"].eq("ACCOUNT_SIGNUP_TIME").all()


def test_dataset_has_no_pii_or_snapshot_churn_flag() -> None:
    accounts, events, episodes = _fixtures()
    result = build_account_survival_dataset(accounts, events, episodes, observation_end="2024-01-31")
    assert {"account_name", "feedback_text", "churn_flag"}.isdisjoint(result.columns)
    assert set(result["primary_outcome"]) <= {"FIRST_CHURN_OBSERVED", "RIGHT_CENSORED", "EXCLUDED"}
