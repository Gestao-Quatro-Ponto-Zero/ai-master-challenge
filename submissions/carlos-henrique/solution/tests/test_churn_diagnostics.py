"""Tests for recurrence, reactivation and mutually exclusive outcomes."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from churn_diagnostics import classify_account_outcomes, usable_events  # noqa: E402


def _events() -> pd.DataFrame:
    rows = []
    definitions = {
        "A0": [("ACCOUNT_CREATED", "2024-01-01")],
        "A1": [("CHURN_RECORDED", "2024-01-02")],
        "A2": [("CHURN_RECORDED", "2024-01-02"), ("CHURN_RECORDED", "2024-01-04")],
        "A3": [("CHURN_RECORDED", "2024-01-02"), ("REACTIVATION_RECORDED", "2024-01-03")],
        "A4": [("CHURN_RECORDED", "2024-01-02"), ("REACTIVATION_RECORDED", "2024-01-03"), ("CHURN_RECORDED", "2024-01-04")],
    }
    for account, events in definitions.items():
        for index, (kind, when) in enumerate(events):
            rows.append({"event_id": f"{account}-{index}", "account_id": account, "event_time": pd.Timestamp(when), "event_type": kind, "event_order_on_same_day": 1, "quality_status": "VALID", "is_quarantined": False})
    return pd.DataFrame(rows)


def test_primary_outcome_priority_and_recurrence() -> None:
    outcomes = classify_account_outcomes(_events()).set_index("account_id")
    assert outcomes.loc["A0", "primary_outcome"] == "NO_CHURN_OBSERVED"
    assert outcomes.loc["A1", "primary_outcome"] == "SINGLE_CHURN"
    assert outcomes.loc["A2", "primary_outcome"] == "RECURRING_CHURN"
    assert outcomes.loc["A3", "primary_outcome"] == "REACTIVATED"
    assert outcomes.loc["A4", "primary_outcome"] == "REACTIVATED_THEN_CHURNED_AGAIN"
    assert outcomes.loc["A4", "churn_count"] == 2


def test_quarantine_never_enters_population() -> None:
    events = _events()
    bad = events.iloc[[0]].assign(event_id="Q", quality_status="QUARANTINED", is_quarantined=True)
    assert "Q" not in set(usable_events(pd.concat([events, bad]))["event_id"])


def test_real_diagnostics_cover_required_stratifications() -> None:
    import json

    churn = json.loads((ROOT / "artifacts" / "churn_diagnostics.json").read_text(encoding="utf-8"))
    reactivation = json.loads((ROOT / "artifacts" / "reactivation_diagnostics.json").read_text(encoding="utf-8"))
    dimensions = {item["dimension"] for item in churn["stratified_observed_outcomes"]}
    assert {
        "signup_quarter", "first_plan", "mrr_band", "subscription_count_band",
        "usage_intensity_90d", "support_frequency_90d", "satisfaction_band",
        "subscription_overlap",
    } <= dimensions
    assert churn["auxiliary_group_comparisons"]
    before_after = reactivation["usage_support_before_after"]
    assert before_after["paired_accounts"] == reactivation["reactivated_accounts"]
    assert before_after["usage_before_churn_30d"]["n"] == before_after["paired_accounts"]
    assert reactivation["reactivation_by_previous_plan"]
    assert reactivation["reactivation_by_mrr_band"]
    assert reactivation["churn_to_reactivation_interval"]["n"] == reactivation["reactivation_events"]
