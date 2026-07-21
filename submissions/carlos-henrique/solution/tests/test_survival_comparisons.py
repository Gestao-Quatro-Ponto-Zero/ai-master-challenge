"""Tests for log-rank, multiplicity, small groups and sensitivity policy."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from survival_comparisons import benjamini_hochberg, classify_metric_sensitivity, compare_groups, logrank_two_sample  # noqa: E402


def test_logrank_returns_valid_statistic_and_probability() -> None:
    result = logrank_two_sample([1, 2, 3, 4], [1, 1, 1, 1], [4, 5, 6, 7], [1, 1, 1, 1])
    assert result["statistic"] >= 0
    assert 0 <= result["p_value"] <= 1


def test_bh_correction_is_bounded_and_monotone_by_rank() -> None:
    adjusted = benjamini_hochberg([0.01, 0.04, 0.20])
    assert all(0 <= value <= 1 for value in adjusted)
    assert adjusted[0] <= adjusted[1] <= adjusted[2]


def test_small_groups_are_skipped() -> None:
    frame = pd.DataFrame({"duration_days": [1, 2, 3, 4], "event_observed": [1, 1, 0, 0], "group": ["A", "A", "B", "B"]})
    result = compare_groups(frame, "group", population="TEST", min_group_size=3, min_group_events=1)
    assert result["comparisons"] == []
    assert len(result["skipped_groups"]) == 2


def test_sensitivity_status_thresholds() -> None:
    assert classify_metric_sensitivity(1.0, 1.05) == "ROBUST"
    assert classify_metric_sensitivity(1.0, 1.20) == "SENSITIVE"
    assert classify_metric_sensitivity(1.0, 1.50) == "UNSTABLE"
    assert classify_metric_sensitivity(None, 1.0) == "UNSTABLE"
