"""Tests for MRR, small groups, health and aggregate attention segments."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from business_diagnostics import build_attention_segments, cohort_diagnostics, revenue_diagnostics  # noqa: E402


def _accounts() -> pd.DataFrame:
    return pd.DataFrame({
        "account_id": ["A1", "A2"], "primary_outcome": ["SINGLE_CHURN", "NO_CHURN_OBSERVED"],
        "churn_count": [1, 0], "is_reactivated": [False, False], "is_recurring_churn": [False, False],
        "last_churn_time": [pd.Timestamp("2024-01-10"), pd.NaT], "observation_end": [pd.Timestamp("2024-01-31")] * 2,
        "total_mrr_current": [100.0, 200.0], "subscription_count": [1, 1],
        "feature_event_count_30d": [0, 4], "active_days_90d": [0, 2], "support_ticket_count_90d": [0, 1],
        "quality_coverage_ratio": [0.4, 1.0], "initial_usage_event_count_30d": [0, 4],
        "observation_start": [pd.Timestamp("2024-01-01")] * 2,
    })


def _episodes() -> pd.DataFrame:
    return pd.DataFrame({
        "episode_id": ["E1", "E2"], "account_id": ["A1", "A2"],
        "subscription_id": ["S1", "S2"],
        "episode_start": [pd.Timestamp("2024-01-01")] * 2, "plan": ["PRO", "BASIC"],
        "mrr": [100.0, 200.0], "is_censored_episode": [True, False],
    })


def test_revenue_is_associated_and_reconciled() -> None:
    result = revenue_diagnostics(_accounts(), _episodes())
    assert result["episode_mrr_total"] == 300.0
    assert result["mrr_associated_with_open_episodes"] == 100.0


def test_small_cohorts_are_flagged() -> None:
    result = cohort_diagnostics(_accounts(), _episodes())
    assert result["small_sample_groups"] > 0
    assert all(row["sample_status"] == "SMALL_SAMPLE" for row in result["cohorts"])


def test_segments_are_aggregate_and_bounded() -> None:
    segments = build_attention_segments(_accounts())
    assert len(segments) <= 5
    assert "account_id" not in segments.columns
    assert segments["account_count"].ge(0).all()


def test_real_revenue_and_segments_are_reconciled() -> None:
    import json

    processed = ROOT / "data" / "processed"
    episodes = pd.read_parquet(processed / "subscription_diagnostic_features.parquet")
    segments = pd.read_parquet(processed / "retention_attention_segments.parquet")
    revenue = json.loads((ROOT / "artifacts" / "revenue_diagnostics.json").read_text(encoding="utf-8"))
    assert revenue["episode_mrr_total"] == float(episodes["mrr"].fillna(0).sum())
    assert revenue["denominator_episodes"] == len(episodes) == 5000
    assert len(segments) <= 5 and "account_id" not in segments.columns
