"""Small, tested non-parametric estimators for governed survival analysis."""

from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np
import pandas as pd


DEFAULT_HORIZONS = (30, 60, 90, 180, 365, 540)
RMST_HORIZONS = (90, 180, 365)
MIN_AT_RISK = 20
Z_95 = 1.959963984540054


def _validated_arrays(durations: Iterable[float], events: Iterable[int]) -> tuple[np.ndarray, np.ndarray]:
    duration = np.asarray(list(durations), dtype=float)
    observed = np.asarray(list(events), dtype=int)
    if len(duration) == 0 or len(duration) != len(observed):
        raise ValueError("Durations and events must have the same non-zero length.")
    if not np.isfinite(duration).all() or (duration < 0).any():
        raise ValueError("Durations must be finite and non-negative.")
    if not np.isin(observed, [0, 1]).all():
        raise ValueError("Events must be binary.")
    return duration, observed


def _event_table(duration: np.ndarray, observed: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized counts by unique duration and numbers at risk."""

    times, inverse, totals = np.unique(duration, return_inverse=True, return_counts=True)
    event_counts = np.zeros(len(times), dtype=int)
    np.add.at(event_counts, inverse, observed)
    censored_counts = totals - event_counts
    at_risk = len(duration) - np.concatenate(([0], np.cumsum(totals[:-1])))
    return times, at_risk, event_counts, censored_counts


def kaplan_meier_curve(durations: Iterable[float], events: Iterable[int]) -> pd.DataFrame:
    """Estimate a Kaplan-Meier step curve with Greenwood intervals."""

    duration, observed = _validated_arrays(durations, events)
    survival = 1.0
    greenwood = 0.0
    rows: list[dict[str, Any]] = [
        {
            "time_days": 0.0,
            "at_risk": int(len(duration)),
            "events": 0,
            "censored": 0,
            "survival_probability": 1.0,
            "confidence_interval_lower": 1.0,
            "confidence_interval_upper": 1.0,
        }
    ]
    table = _event_table(duration, observed)
    for time, at_risk, event_count, censored_count in zip(*table):
        if event_count:
            survival *= 1.0 - event_count / at_risk
            if at_risk > event_count:
                greenwood += event_count / (at_risk * (at_risk - event_count))
        if survival <= 0:
            lower = upper = 0.0
        else:
            standard_error = survival * math.sqrt(greenwood)
            lower = max(0.0, survival - Z_95 * standard_error)
            upper = min(1.0, survival + Z_95 * standard_error)
        rows.append(
            {
                "time_days": float(time),
                "at_risk": at_risk,
                "events": event_count,
                "censored": censored_count,
                "survival_probability": float(survival),
                "confidence_interval_lower": float(lower),
                "confidence_interval_upper": float(upper),
            }
        )
    result = pd.DataFrame(rows)
    if not result["survival_probability"].between(0, 1).all() or not result["survival_probability"].is_monotonic_decreasing:
        raise AssertionError("Kaplan-Meier invariants failed.")
    if not result["at_risk"].is_monotonic_decreasing:
        raise AssertionError("At-risk counts must be non-increasing.")
    return result


def nelson_aalen_curve(durations: Iterable[float], events: Iterable[int]) -> pd.DataFrame:
    """Estimate Nelson-Aalen cumulative hazard with a normal interval."""

    duration, observed = _validated_arrays(durations, events)
    cumulative = 0.0
    variance = 0.0
    rows: list[dict[str, Any]] = [
        {
            "time_days": 0.0,
            "at_risk": int(len(duration)),
            "events": 0,
            "censored": 0,
            "cumulative_hazard": 0.0,
            "confidence_interval_lower": 0.0,
            "confidence_interval_upper": 0.0,
        }
    ]
    table = _event_table(duration, observed)
    for time, at_risk, event_count, censored_count in zip(*table):
        cumulative += event_count / at_risk
        variance += event_count / (at_risk**2)
        standard_error = math.sqrt(variance)
        rows.append(
            {
                "time_days": float(time),
                "at_risk": at_risk,
                "events": event_count,
                "censored": censored_count,
                "cumulative_hazard": float(cumulative),
                "confidence_interval_lower": float(max(0.0, cumulative - Z_95 * standard_error)),
                "confidence_interval_upper": float(cumulative + Z_95 * standard_error),
            }
        )
    result = pd.DataFrame(rows)
    if not result["cumulative_hazard"].is_monotonic_increasing:
        raise AssertionError("Cumulative hazard must be non-decreasing.")
    return result


def _value_at(curve: pd.DataFrame, horizon: float, column: str) -> float:
    available = curve.loc[curve["time_days"].le(horizon)]
    return float(available.iloc[-1][column])


def horizon_table(
    durations: Iterable[float],
    events: Iterable[int],
    curve: pd.DataFrame,
    *,
    estimator: str,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
    min_at_risk: int = MIN_AT_RISK,
) -> list[dict[str, Any]]:
    duration, observed = _validated_arrays(durations, events)
    max_duration = float(duration.max())
    value_column = "survival_probability" if estimator == "kaplan_meier" else "cumulative_hazard"
    rows: list[dict[str, Any]] = []
    for horizon in horizons:
        beyond = float(horizon) > max_duration
        at_risk = int(np.sum(duration >= horizon))
        row = {
            "horizon_days": int(horizon),
            value_column: None if beyond else _value_at(curve, horizon, value_column),
            "confidence_interval_lower": None if beyond else _value_at(curve, horizon, "confidence_interval_lower"),
            "confidence_interval_upper": None if beyond else _value_at(curve, horizon, "confidence_interval_upper"),
            "at_risk": at_risk,
            "events_observed": int(np.sum((duration <= horizon) & (observed == 1))),
            "censored": int(np.sum((duration <= horizon) & (observed == 0))),
            "support_status": "BEYOND_SUPPORT" if beyond else ("LOW_AT_RISK" if at_risk < min_at_risk else "SUPPORTED"),
        }
        rows.append(row)
    return rows


def survival_quantile(curve: pd.DataFrame, probability: float) -> float | str:
    reached = curve.loc[curve["survival_probability"].le(probability)]
    return "NOT_REACHED" if reached.empty else float(reached.iloc[0]["time_days"])


def restricted_mean_survival_time(
    durations: Iterable[float], events: Iterable[int], horizon: float
) -> float | None:
    duration, observed = _validated_arrays(durations, events)
    if horizon < 0:
        raise ValueError("RMST horizon must be non-negative.")
    if horizon > duration.max():
        return None
    curve = kaplan_meier_curve(duration, observed)
    times = curve["time_days"].to_numpy(dtype=float)
    survival = curve["survival_probability"].to_numpy(dtype=float)
    area = 0.0
    for index, start in enumerate(times):
        if start >= horizon:
            break
        end = min(horizon, times[index + 1] if index + 1 < len(times) else horizon)
        area += (end - start) * survival[index]
    return float(max(area, 0.0))


def _rmst_from_curve(curve: pd.DataFrame, horizon: float, maximum_duration: float) -> float | None:
    if horizon > maximum_duration:
        return None
    times = curve["time_days"].to_numpy(dtype=float)
    survival = curve["survival_probability"].to_numpy(dtype=float)
    area = 0.0
    for index, start in enumerate(times):
        if start >= horizon:
            break
        end = min(horizon, times[index + 1] if index + 1 < len(times) else horizon)
        area += (end - start) * survival[index]
    return float(max(area, 0.0))


def analyze_population(
    frame: pd.DataFrame,
    *,
    duration_column: str = "duration_days",
    event_column: str = "event_observed",
    horizons: Iterable[int] = DEFAULT_HORIZONS,
    min_at_risk: int = MIN_AT_RISK,
) -> dict[str, Any]:
    """Return aggregate KM, Nelson-Aalen, quantiles and RMST evidence."""

    durations = pd.to_numeric(frame[duration_column], errors="raise").to_numpy(dtype=float)
    events = pd.to_numeric(frame[event_column], errors="raise").to_numpy(dtype=int)
    km = kaplan_meier_curve(durations, events)
    na = nelson_aalen_curve(durations, events)
    return {
        "sample_size": int(len(frame)),
        "event_count": int(events.sum()),
        "censored_count": int(len(events) - events.sum()),
        "censoring_rate": float(1 - events.mean()),
        "maximum_observed_duration_days": float(durations.max()),
        "median_survival_days": survival_quantile(km, 0.5),
        "survival_quartiles_days": {
            "survival_75_percent": survival_quantile(km, 0.75),
            "survival_50_percent": survival_quantile(km, 0.50),
            "survival_25_percent": survival_quantile(km, 0.25),
        },
        "kaplan_meier": {
            "curve": km.to_dict("records"),
            "horizons": horizon_table(
                durations, events, km, estimator="kaplan_meier", horizons=horizons, min_at_risk=min_at_risk
            ),
        },
        "nelson_aalen": {
            "curve": na.to_dict("records"),
            "horizons": horizon_table(
                durations, events, na, estimator="nelson_aalen", horizons=horizons, min_at_risk=min_at_risk
            ),
        },
        "rmst": [
            {
                "horizon_days": horizon,
                "rmst_days": _rmst_from_curve(km, horizon, float(durations.max())),
                "support_status": "SUPPORTED" if horizon <= durations.max() else "BEYOND_SUPPORT",
            }
            for horizon in RMST_HORIZONS
        ],
    }
