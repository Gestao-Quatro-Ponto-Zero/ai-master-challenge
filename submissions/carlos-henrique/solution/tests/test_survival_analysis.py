"""Tests for Kaplan-Meier, Nelson-Aalen, RMST and support tables."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from survival_analysis import analyze_population, kaplan_meier_curve, nelson_aalen_curve, restricted_mean_survival_time  # noqa: E402


def test_km_starts_at_one_is_bounded_and_monotone() -> None:
    curve = kaplan_meier_curve([1, 2, 3, 4], [1, 0, 1, 0])
    assert curve.iloc[0]["survival_probability"] == 1.0
    assert curve["survival_probability"].between(0, 1).all()
    assert curve["survival_probability"].is_monotonic_decreasing
    assert curve["at_risk"].is_monotonic_decreasing


def test_nelson_aalen_is_non_decreasing() -> None:
    curve = nelson_aalen_curve([1, 2, 3, 4], [1, 0, 1, 0])
    assert curve["cumulative_hazard"].is_monotonic_increasing
    assert curve.iloc[0]["cumulative_hazard"] == 0.0


def test_median_not_reached_and_rmst_non_negative() -> None:
    frame = pd.DataFrame({"duration_days": [100, 110, 120, 130], "event_observed": [0, 0, 0, 0]})
    analysis = analyze_population(frame)
    assert analysis["median_survival_days"] == "NOT_REACHED"
    assert restricted_mean_survival_time(frame["duration_days"], frame["event_observed"], 90) >= 0


def test_horizon_support_and_counts_are_explicit() -> None:
    frame = pd.DataFrame({"duration_days": [30, 60, 90], "event_observed": [1, 0, 1]})
    analysis = analyze_population(frame)
    row = next(item for item in analysis["kaplan_meier"]["horizons"] if item["horizon_days"] == 60)
    assert row["at_risk"] == 2
    assert row["events_observed"] == 1
    assert row["censored"] == 1
    assert row["support_status"] == "LOW_AT_RISK"
