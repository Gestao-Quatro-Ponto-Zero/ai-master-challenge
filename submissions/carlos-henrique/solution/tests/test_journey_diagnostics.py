"""Tests for reduced deterministic descriptive journeys."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from journey_diagnostics import build_journey_summary, collapse_consecutive  # noqa: E402


def test_consecutive_events_are_collapsed_and_limited() -> None:
    assert collapse_consecutive(["A", "A", "B", "B", "A"], limit=3) == ("A", "B", "A")


def test_journey_support_has_explicit_denominator() -> None:
    kinds = ["ACCOUNT_CREATED", "FEATURE_USED", "FEATURE_USED", "CHURN_RECORDED"]
    events = pd.DataFrame([
        {"event_id": str(i), "account_id": "A1", "event_time": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i), "event_type": kind, "event_order_on_same_day": 1, "quality_status": "VALID", "is_quarantined": False}
        for i, kind in enumerate(kinds)
    ])
    result = build_journey_summary(events)
    top = result["top_complete_journeys"][0]
    assert top["sequence"] == ["ACCOUNT_CREATED", "FEATURE_USED", "CHURN_RECORDED"]
    assert top["account_support"] == 1
    assert top["denominator_accounts"] == 1


def test_real_journey_artifact_has_aggregate_support_only() -> None:
    import json

    payload = json.loads((ROOT / "artifacts" / "journey_summary.json").read_text(encoding="utf-8"))
    for key in (
        "top_complete_journeys", "top_pre_first_churn_prefixes",
        "top_churn_to_reactivation_sequences", "top_post_reactivation_sequences",
    ):
        for item in payload[key]:
            assert item["account_support"] <= item["denominator_accounts"]
            assert 0 <= item["relative_support"] <= 1
            assert len(item["sequence"]) <= 12
            assert "account_id" not in item
