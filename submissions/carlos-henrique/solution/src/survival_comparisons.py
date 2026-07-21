"""Governed descriptive comparisons for survival curves."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy.stats import chi2

from survival_analysis import analyze_population


MIN_GROUP_SIZE = 20
MIN_GROUP_EVENTS = 5


def logrank_two_sample(
    durations_a: Iterable[float],
    events_a: Iterable[int],
    durations_b: Iterable[float],
    events_b: Iterable[int],
) -> dict[str, float]:
    """Classical two-sample log-rank statistic."""

    da = np.asarray(list(durations_a), dtype=float)
    ea = np.asarray(list(events_a), dtype=int)
    db = np.asarray(list(durations_b), dtype=float)
    eb = np.asarray(list(events_b), dtype=int)
    event_times = np.unique(np.concatenate([da[ea == 1], db[eb == 1]]))
    observed_a = expected_a = variance = 0.0
    for time in event_times:
        risk_a = int(np.sum(da >= time))
        risk_b = int(np.sum(db >= time))
        deaths_a = int(np.sum((da == time) & (ea == 1)))
        deaths_b = int(np.sum((db == time) & (eb == 1)))
        risk = risk_a + risk_b
        deaths = deaths_a + deaths_b
        if risk <= 0:
            continue
        observed_a += deaths_a
        expected_a += deaths * risk_a / risk
        if risk > 1:
            variance += risk_a * risk_b * deaths * (risk - deaths) / (risk**2 * (risk - 1))
    statistic = 0.0 if variance <= 0 else (observed_a - expected_a) ** 2 / variance
    return {
        "statistic": float(statistic),
        "p_value": float(chi2.sf(statistic, 1)),
        "observed_events_group_a": float(observed_a),
        "expected_events_group_a": float(expected_a),
    }


def benjamini_hochberg(p_values: Iterable[float]) -> list[float]:
    """Return monotone Benjamini-Hochberg adjusted p-values."""

    values = np.asarray(list(p_values), dtype=float)
    if len(values) == 0:
        return []
    order = np.argsort(values)
    ranked = values[order]
    adjusted = np.empty(len(values), dtype=float)
    running = 1.0
    for index in range(len(values) - 1, -1, -1):
        candidate = ranked[index] * len(values) / (index + 1)
        running = min(running, candidate)
        adjusted[order[index]] = min(1.0, running)
    return adjusted.tolist()


def _horizon_value(analysis: dict[str, Any], horizon: int) -> float | None:
    for row in analysis["kaplan_meier"]["horizons"]:
        if row["horizon_days"] == horizon:
            return row["survival_probability"]
    return None


def compare_groups(
    frame: pd.DataFrame,
    group_column: str,
    *,
    population: str,
    duration_column: str = "duration_days",
    event_column: str = "event_observed",
    min_group_size: int = MIN_GROUP_SIZE,
    min_group_events: int = MIN_GROUP_EVENTS,
) -> dict[str, Any]:
    """Run eligible pairwise log-rank comparisons and aggregate effect sizes."""

    groups: dict[str, dict[str, Any]] = {}
    skipped: list[dict[str, Any]] = []
    for name, group in frame.dropna(subset=[group_column]).groupby(group_column, sort=True):
        name = str(name)
        event_count = int(group[event_column].sum())
        status = "ELIGIBLE"
        reasons: list[str] = []
        if len(group) < min_group_size:
            status = "SMALL_SAMPLE"
            reasons.append(f"n<{min_group_size}")
        if event_count < min_group_events:
            status = "INSUFFICIENT_EVENTS"
            reasons.append(f"events<{min_group_events}")
        if status == "ELIGIBLE":
            analysis = analyze_population(group, duration_column=duration_column, event_column=event_column)
            groups[name] = {
                "frame": group,
                "sample_size": int(len(group)),
                "event_count": event_count,
                "censored_count": int(len(group) - event_count),
                "analysis": analysis,
            }
        else:
            skipped.append(
                {
                    "group": name,
                    "sample_size": int(len(group)),
                    "event_count": event_count,
                    "status": status,
                    "reasons": reasons,
                }
            )

    comparisons: list[dict[str, Any]] = []
    for left, right in combinations(sorted(groups), 2):
        left_data = groups[left]
        right_data = groups[right]
        left_frame = left_data["frame"]
        right_frame = right_data["frame"]
        test = logrank_two_sample(
            left_frame[duration_column], left_frame[event_column], right_frame[duration_column], right_frame[event_column]
        )
        survival_differences: dict[str, float | None] = {}
        for horizon in (90, 180, 365):
            left_value = _horizon_value(left_data["analysis"], horizon)
            right_value = _horizon_value(right_data["analysis"], horizon)
            survival_differences[f"{horizon}d"] = (
                None if left_value is None or right_value is None else float(left_value - right_value)
            )
        left_rmst = next(row["rmst_days"] for row in left_data["analysis"]["rmst"] if row["horizon_days"] == 365)
        right_rmst = next(row["rmst_days"] for row in right_data["analysis"]["rmst"] if row["horizon_days"] == 365)
        comparisons.append(
            {
                "group_dimension": group_column,
                "population": population,
                "group_a": left,
                "group_b": right,
                "sample_size_a": left_data["sample_size"],
                "sample_size_b": right_data["sample_size"],
                "events_a": left_data["event_count"],
                "events_b": right_data["event_count"],
                "statistic": test["statistic"],
                "p_value": test["p_value"],
                "survival_probability_difference_a_minus_b": survival_differences,
                "rmst_365_difference_days_a_minus_b": None if left_rmst is None or right_rmst is None else float(left_rmst - right_rmst),
                "interpretation": "DESCRIPTIVE_ASSOCIATION_ONLY",
                "limitation": "Pairwise log-rank does not establish causality or individual future risk.",
            }
        )
    adjusted = benjamini_hochberg(item["p_value"] for item in comparisons)
    for item, value in zip(comparisons, adjusted):
        item["p_value_bh"] = value
        item["multiplicity_status"] = "BH_SIGNIFICANT_0_05" if value < 0.05 else "NOT_BH_SIGNIFICANT_0_05"

    public_groups = {
        name: {key: value for key, value in payload.items() if key not in {"frame", "analysis"}}
        for name, payload in groups.items()
    }
    return {
        "group_dimension": group_column,
        "population": population,
        "minimum_group_size": min_group_size,
        "minimum_group_events": min_group_events,
        "eligible_groups": public_groups,
        "skipped_groups": skipped,
        "comparisons": comparisons,
    }


def annotate_stability(
    main_results: list[dict[str, Any]], strict_results: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Compare direction and magnitude between main and strict populations."""

    strict_lookup: dict[tuple[str, str, str], dict[str, Any]] = {}
    for block in strict_results:
        for comparison in block["comparisons"]:
            key = (comparison["group_dimension"], comparison["group_a"], comparison["group_b"])
            strict_lookup[key] = comparison
    output: list[dict[str, Any]] = []
    for block in main_results:
        copied = {**block, "comparisons": []}
        for comparison in block["comparisons"]:
            item = dict(comparison)
            key = (item["group_dimension"], item["group_a"], item["group_b"])
            strict = strict_lookup.get(key)
            main_effect = item["survival_probability_difference_a_minus_b"].get("180d")
            strict_effect = None if strict is None else strict["survival_probability_difference_a_minus_b"].get("180d")
            if main_effect is None or strict_effect is None:
                status = "NOT_COMPARABLE"
            elif main_effect == 0 and strict_effect == 0:
                status = "ROBUST"
            elif np.sign(main_effect) != np.sign(strict_effect):
                status = "UNSTABLE"
            elif abs(main_effect - strict_effect) <= 0.05:
                status = "ROBUST"
            else:
                status = "SENSITIVE"
            item["strict_population_stability"] = status
            item["strict_effect_180d"] = strict_effect
            copied["comparisons"].append(item)
        output.append(copied)
    return output


def classify_metric_sensitivity(reference: float | None, alternative: float | None) -> str:
    if reference is None or alternative is None:
        return "UNSTABLE"
    scale = max(abs(reference), 1e-9)
    relative = abs(alternative - reference) / scale
    if relative <= 0.10:
        return "ROBUST"
    if relative <= 0.30:
        return "SENSITIVE"
    return "UNSTABLE"
