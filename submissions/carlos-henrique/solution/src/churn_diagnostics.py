"""Governed descriptive churn and reactivation diagnostics.

The functions in this module never infer retention or causality.  Outcomes are
derived only from usable temporal events and every reported proportion carries
its denominator.
"""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd


OUTCOME_PRIORITY = (
    "REACTIVATED_THEN_CHURNED_AGAIN",
    "REACTIVATED",
    "RECURRING_CHURN",
    "SINGLE_CHURN",
    "NO_CHURN_OBSERVED",
)


def usable_events(events: pd.DataFrame, strict: bool = False) -> pd.DataFrame:
    """Return the authorized population, explicitly excluding quarantine."""

    allowed = {"VALID"} if strict else {"VALID", "VALID_WITH_WARNING"}
    mask = events["quality_status"].isin(allowed) & ~events["is_quarantined"].astype(bool)
    return events.loc[mask].copy()


def classify_account_outcomes(events: pd.DataFrame) -> pd.DataFrame:
    """Create mutually exclusive outcomes from usable churn/reactivation events."""

    rows: list[dict[str, Any]] = []
    for account_id, group in events.groupby("account_id", sort=True):
        account = group.sort_values(
            ["event_time", "event_order_on_same_day", "event_id"]
        )
        account_id = str(account_id)
        churn = account.loc[account["event_type"].eq("CHURN_RECORDED"), "event_time"]
        react = account.loc[account["event_type"].eq("REACTIVATION_RECORDED"), "event_time"]
        churn_times = list(pd.to_datetime(churn).sort_values())
        react_times = list(pd.to_datetime(react).sort_values())
        has_valid_reactivation = any(r > c for r in react_times for c in churn_times)
        churn_after_reactivation = any(c > r for c in churn_times for r in react_times)
        if churn_after_reactivation:
            primary = OUTCOME_PRIORITY[0]
        elif has_valid_reactivation:
            primary = OUTCOME_PRIORITY[1]
        elif len(churn_times) >= 2:
            primary = OUTCOME_PRIORITY[2]
        elif len(churn_times) == 1:
            primary = OUTCOME_PRIORITY[3]
        else:
            primary = OUTCOME_PRIORITY[4]
        last_churn = max(churn_times) if churn_times else pd.NaT
        reactivation_after_last = bool(
            churn_times and any(r > last_churn for r in react_times)
        )
        rows.append(
            {
                "account_id": account_id,
                "primary_outcome": primary,
                "churn_count": len(churn_times),
                "reactivation_count": len(react_times),
                "first_churn_time": min(churn_times) if churn_times else pd.NaT,
                "last_churn_time": last_churn,
                "first_reactivation_time": min(react_times) if react_times else pd.NaT,
                "last_reactivation_time": max(react_times) if react_times else pd.NaT,
                "is_churned_not_reactivated": bool(churn_times and not reactivation_after_last),
                "is_reactivated": has_valid_reactivation,
                "is_recurring_churn": len(churn_times) >= 2,
                "is_reactivated_then_churned_again": churn_after_reactivation,
            }
        )
    return pd.DataFrame(rows).sort_values("account_id").reset_index(drop=True)


def _describe(values: pd.Series) -> dict[str, Any]:
    numeric = pd.to_numeric(values, errors="coerce")
    present = numeric.dropna()
    return {
        "n": int(len(values)),
        "non_missing": int(present.size),
        "missing_ratio": float(numeric.isna().mean()) if len(numeric) else None,
        "mean": float(present.mean()) if len(present) else None,
        "median": float(present.median()) if len(present) else None,
        "q1": float(present.quantile(0.25)) if len(present) else None,
        "q3": float(present.quantile(0.75)) if len(present) else None,
    }


def compare_groups(
    accounts: pd.DataFrame,
    group_column: str,
    left: str,
    right: str,
    metrics: Iterable[str],
) -> list[dict[str, Any]]:
    """Compare groups with effect magnitudes and missingness, not p-values."""

    output: list[dict[str, Any]] = []
    for metric in metrics:
        left_stats = _describe(accounts.loc[accounts[group_column].eq(left), metric])
        right_stats = _describe(accounts.loc[accounts[group_column].eq(right), metric])
        left_median = left_stats["median"]
        right_median = right_stats["median"]
        absolute = None if left_median is None or right_median is None else right_median - left_median
        ratio = None
        if left_median not in (None, 0) and right_median is not None:
            ratio = right_median / left_median
        output.append(
            {
                "metric": metric,
                "comparison": f"{left} vs {right}",
                "left": left_stats,
                "right": right_stats,
                "median_difference_right_minus_left": absolute,
                "median_ratio_right_over_left": ratio,
            }
        )
    return output


def _interval_summary(values: list[float]) -> dict[str, Any]:
    series = pd.Series(values, dtype="float64")
    return {
        "n": int(series.size),
        "median_days": float(series.median()) if len(series) else None,
        "mean_days": float(series.mean()) if len(series) else None,
        "q1_days": float(series.quantile(0.25)) if len(series) else None,
        "q3_days": float(series.quantile(0.75)) if len(series) else None,
    }


def temporal_intervals(events: pd.DataFrame) -> dict[str, Any]:
    """Summarize observed intervals without fitting time-to-event models."""

    first_churn: list[float] = []
    inter_churn: list[float] = []
    churn_to_reactivation: list[float] = []
    reactivation_to_churn: list[float] = []
    for _, group in events.groupby("account_id", sort=True):
        ordered = group.sort_values(["event_time", "event_order_on_same_day", "event_id"])
        created = ordered.loc[ordered["event_type"].eq("ACCOUNT_CREATED"), "event_time"]
        churn = list(ordered.loc[ordered["event_type"].eq("CHURN_RECORDED"), "event_time"])
        react = list(ordered.loc[ordered["event_type"].eq("REACTIVATION_RECORDED"), "event_time"])
        if churn and len(created):
            first_churn.append(float((churn[0].normalize() - created.min().normalize()).days))
        inter_churn.extend(float((b.normalize() - a.normalize()).days) for a, b in zip(churn, churn[1:]))
        for react_time in react:
            previous = [c for c in churn if c < react_time]
            if previous:
                previous_churn = max(previous)
                churn_to_reactivation.append(float((react_time.normalize() - previous_churn.normalize()).days))
        for react_time in react:
            next_churn = next((c for c in churn if c > react_time), None)
            if next_churn is not None:
                reactivation_to_churn.append(float((next_churn.normalize() - react_time.normalize()).days))
    return {
        "signup_to_first_churn": _interval_summary(first_churn),
        "between_churns": _interval_summary(inter_churn),
        "churn_to_reactivation": _interval_summary(churn_to_reactivation),
        "reactivation_to_new_churn": _interval_summary(reactivation_to_churn),
    }


def _quantile_band(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce").fillna(0)
    if numeric.nunique() < 4:
        return pd.Series("ALL", index=values.index, dtype="string")
    return pd.qcut(
        numeric.rank(method="first"), 4,
        labels=["Q1_LOW", "Q2", "Q3", "Q4_HIGH"],
    ).astype("string")


def _stratified_outcomes(accounts: pd.DataFrame) -> list[dict[str, Any]]:
    work = accounts.copy()
    definitions: dict[str, pd.Series] = {
        "signup_quarter": work["observation_start"].dt.to_period("Q").astype(str),
        "first_plan": work["first_plan"].fillna("MISSING").astype(str),
        "mrr_band": _quantile_band(work["total_mrr_current"]),
        "subscription_count_band": pd.cut(
            work["subscription_count"], [-1, 1, 5, 10, np.inf],
            labels=["ONE", "TWO_TO_FIVE", "SIX_TO_TEN", "ELEVEN_PLUS"],
        ).astype("string"),
        "usage_intensity_90d": pd.cut(
            work["feature_event_count_90d"], [-1, 0, 2, np.inf],
            labels=["NONE", "LOW_1_2", "HIGH_3_PLUS"],
        ).astype("string"),
        "support_frequency_90d": pd.cut(
            work["support_ticket_count_90d"], [-1, 0, 1, np.inf],
            labels=["NONE", "ONE", "TWO_PLUS"],
        ).astype("string"),
        "satisfaction_band": pd.cut(
            work["satisfaction_mean"], [-np.inf, 3, 4, np.inf],
            labels=["LOW_UP_TO_3", "MID_3_TO_4", "HIGH_ABOVE_4"],
        ).astype("string").fillna("MISSING"),
        "subscription_overlap": work["has_subscription_overlap"].map({True: "OVERLAP", False: "NO_OVERLAP"}),
    }
    rows: list[dict[str, Any]] = []
    for dimension, values in definitions.items():
        grouped = work.assign(_value=values).groupby("_value", observed=True, sort=True)
        for value, group in grouped:
            n = len(group)
            rows.append({
                "dimension": dimension,
                "value": str(value),
                "denominator_accounts": int(n),
                "churn_observed_accounts": int(group["churn_count"].gt(0).sum()),
                "observed_churn_proportion": float(group["churn_count"].gt(0).mean()),
                "recurring_churn_accounts": int(group["churn_count"].ge(2).sum()),
                "reactivated_accounts": int(group["is_reactivated"].sum()),
                "sample_status": "OK" if n >= 20 else "SMALL_SAMPLE",
            })
    return rows


def build_churn_diagnostics(accounts: pd.DataFrame, events: pd.DataFrame) -> dict[str, Any]:
    denominator = int(accounts["account_id"].nunique())
    outcome_counts = accounts["primary_outcome"].value_counts().reindex(OUTCOME_PRIORITY, fill_value=0)
    churned = int(accounts["churn_count"].gt(0).sum())
    recurring = int(accounts["churn_count"].ge(2).sum())
    comparisons: list[dict[str, Any]] = []
    metrics = [
        "feature_event_count_90d", "active_days_90d", "support_ticket_count_90d",
        "satisfaction_mean", "total_mrr_current", "subscription_count",
    ]
    for left, right in (
        ("NO_CHURN_OBSERVED", "SINGLE_CHURN"),
        ("NO_CHURN_OBSERVED", "RECURRING_CHURN"),
        ("REACTIVATED", "REACTIVATED_THEN_CHURNED_AGAIN"),
    ):
        comparisons.extend(compare_groups(accounts, "primary_outcome", left, right, metrics))

    recurrence_groups = accounts.assign(
        auxiliary_comparison=np.where(
            accounts["churn_count"].ge(2), "RECURRING_CHURN",
            np.where(accounts["churn_count"].eq(0), "NO_CHURN_OBSERVED", "OTHER"),
        )
    )
    reactivation_groups = accounts.assign(
        auxiliary_comparison=np.where(
            accounts["is_reactivated"], "REACTIVATED",
            np.where(accounts["churn_count"].gt(0), "CHURNED_NOT_REACTIVATED", "OTHER"),
        )
    )
    auxiliary_comparisons = compare_groups(
        recurrence_groups, "auxiliary_comparison", "NO_CHURN_OBSERVED", "RECURRING_CHURN", metrics
    ) + compare_groups(
        reactivation_groups, "auxiliary_comparison", "CHURNED_NOT_REACTIVATED", "REACTIVATED", metrics
    )
    auxiliary = {
        "CHURNED_NOT_REACTIVATED": int(accounts["is_churned_not_reactivated"].sum()),
        "REACTIVATED": int(accounts["is_reactivated"].sum()),
        "RECURRING_CHURN": recurring,
        "REACTIVATED_THEN_CHURNED_AGAIN": int(accounts["is_reactivated_then_churned_again"].sum()),
    }
    return {
        "methodology": "Account-grain descriptive outcomes from usable events; proportions are observed shares, not temporal churn rates.",
        "population": "VALID + VALID_WITH_WARNING; quarantine excluded",
        "denominator_accounts": denominator,
        "primary_outcomes": [
            {"outcome": key, "accounts": int(value), "observed_proportion": float(value / denominator)}
            for key, value in outcome_counts.items()
        ],
        "auxiliary_states": auxiliary,
        "churn_observed_accounts": churned,
        "observed_churn_proportion": float(churned / denominator),
        "recurring_churn_accounts": recurring,
        "observed_recurring_churn_proportion": float(recurring / denominator),
        "churn_count_distribution": {
            str(int(k)): int(v) for k, v in accounts["churn_count"].value_counts().sort_index().items()
        },
        "intervals": temporal_intervals(events),
        "group_comparisons": comparisons,
        "auxiliary_group_comparisons": auxiliary_comparisons,
        "stratified_observed_outcomes": _stratified_outcomes(accounts),
        "limitations": [
            "Administrative censoring at observation_end; no churn observed does not mean permanent retention.",
            "Daily timestamps and technical same-day ordering do not establish intraday precedence or causality.",
            "Warning events materially expand churn coverage and require sensitivity analysis.",
        ],
    }


def build_reactivation_diagnostics(accounts: pd.DataFrame, events: pd.DataFrame) -> dict[str, Any]:
    churn_events = events.loc[events["event_type"].eq("CHURN_RECORDED")]
    reactivated_accounts = accounts.loc[accounts["is_reactivated"]]
    followed = 0
    for _, row in churn_events.iterrows():
        future = events.loc[
            events["account_id"].eq(row["account_id"])
            & events["event_type"].eq("REACTIVATION_RECORDED")
            & events["event_time"].gt(row["event_time"])
        ]
        followed += int(not future.empty)
    denominator = int(len(churn_events))
    intervals = temporal_intervals(events)

    before_after_rows: list[dict[str, Any]] = []
    for account_id in reactivated_accounts["account_id"]:
        account_events = events.loc[events["account_id"].eq(account_id)].sort_values(
            ["event_time", "event_order_on_same_day", "event_id"]
        )
        churn_times = list(account_events.loc[account_events["event_type"].eq("CHURN_RECORDED"), "event_time"])
        react_times = list(account_events.loc[account_events["event_type"].eq("REACTIVATION_RECORDED"), "event_time"])
        pair = next(
            ((max(c for c in churn_times if c < react), react) for react in react_times if any(c < react for c in churn_times)),
            None,
        )
        if pair is None:
            continue
        churn_time, react_time = pair
        before = account_events.loc[account_events["event_time"].between(churn_time - pd.Timedelta(days=29), churn_time, inclusive="both")]
        after = account_events.loc[account_events["event_time"].between(react_time, react_time + pd.Timedelta(days=29), inclusive="both")]
        before_after_rows.append({
            "usage_before_churn_30d": int(before["event_type"].eq("FEATURE_USED").sum()),
            "usage_after_reactivation_30d": int(after["event_type"].eq("FEATURE_USED").sum()),
            "support_before_churn_30d": int(before["event_type"].eq("SUPPORT_TICKET_OPENED").sum()),
            "support_after_reactivation_30d": int(after["event_type"].eq("SUPPORT_TICKET_OPENED").sum()),
        })
    before_after = pd.DataFrame(before_after_rows)

    def before_after_summary(column: str) -> dict[str, Any]:
        values = before_after[column] if column in before_after else pd.Series(dtype="float64")
        return {
            "n": int(len(values)),
            "mean": float(values.mean()) if len(values) else None,
            "median": float(values.median()) if len(values) else None,
        }

    churned_accounts = accounts.loc[accounts["churn_count"].gt(0)].copy()
    churned_accounts["mrr_band"] = _quantile_band(churned_accounts["total_mrr_current"])
    by_plan = [{
        "previous_plan": str(plan),
        "denominator_churned_accounts": int(len(group)),
        "reactivated_accounts": int(group["is_reactivated"].sum()),
        "observed_reactivation_proportion": float(group["is_reactivated"].mean()),
        "sample_status": "OK" if len(group) >= 20 else "SMALL_SAMPLE",
    } for plan, group in churned_accounts.groupby("latest_plan", dropna=False, sort=True)]
    by_mrr = [{
        "mrr_band": str(band),
        "denominator_churned_accounts": int(len(group)),
        "reactivated_accounts": int(group["is_reactivated"].sum()),
        "observed_reactivation_proportion": float(group["is_reactivated"].mean()),
        "sample_status": "OK" if len(group) >= 20 else "SMALL_SAMPLE",
    } for band, group in churned_accounts.groupby("mrr_band", observed=True, sort=True)]

    return {
        "methodology": "Explicit usable reactivation events only; post-reactivation measures are descriptive and are not predictive features.",
        "population": "VALID + VALID_WITH_WARNING; quarantine excluded",
        "denominator_accounts": int(accounts["account_id"].nunique()),
        "reactivated_accounts": int(len(reactivated_accounts)),
        "reactivation_events": int(events["event_type"].eq("REACTIVATION_RECORDED").sum()),
        "reactivations_per_account_distribution": {
            str(int(k)): int(v) for k, v in accounts["reactivation_count"].value_counts().sort_index().items()
        },
        "denominator_churn_events": denominator,
        "churn_events_followed_by_reactivation": followed,
        "observed_share_churn_followed_by_reactivation": float(followed / denominator) if denominator else None,
        "churn_to_reactivation_interval": intervals["churn_to_reactivation"],
        "reactivation_to_new_churn_interval": intervals["reactivation_to_new_churn"],
        "recurrence_after_reactivation_accounts": int(accounts["is_reactivated_then_churned_again"].sum()),
        "reactivation_by_previous_plan": by_plan,
        "reactivation_by_mrr_band": by_mrr,
        "usage_support_before_after": {
            "usage_before_churn_30d": before_after_summary("usage_before_churn_30d"),
            "usage_after_reactivation_30d": before_after_summary("usage_after_reactivation_30d"),
            "support_before_churn_30d": before_after_summary("support_before_churn_30d"),
            "support_after_reactivation_30d": before_after_summary("support_after_reactivation_30d"),
            "paired_accounts": int(len(before_after)),
            "interpretation": "Post-reactivation values are descriptive and never used as prediction features.",
        },
        "limitations": [
            "Reactivation is explicit and is not inferred from a later subscription.",
            "Observed intervals are censored and do not estimate a survival function.",
        ],
    }


def safe_ratio(numerator: float, denominator: float) -> float | None:
    return None if denominator == 0 or np.isnan(denominator) else float(numerator / denominator)
