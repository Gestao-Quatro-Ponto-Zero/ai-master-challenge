"""Retrospective, cutoff-safe features for deterministic watchlist rules."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from graph_schema import stable_key


REFERENCE_DATE = pd.Timestamp("2024-12-31T19:00:00")
MAIN_STATUSES = {"VALID", "VALID_WITH_WARNING"}
STRICT_STATUSES = {"VALID"}


@dataclass(frozen=True)
class FeatureBuild:
    frame: pd.DataFrame
    accounting: dict[str, Any]


def _days_since(reference: pd.Timestamp, timestamp: pd.Timestamp | None) -> float:
    if timestamp is None or pd.isna(timestamp):
        return np.nan
    return max((reference - pd.Timestamp(timestamp)).total_seconds() / 86400.0, 0.0)


def _window(frame: pd.DataFrame, reference: pd.Timestamp, days: int) -> pd.DataFrame:
    start = reference - pd.Timedelta(days=days)
    return frame.loc[frame["event_time"].gt(start) & frame["event_time"].le(reference)]


def _support_resolution(support: pd.DataFrame, reference: pd.Timestamp, days: int = 90) -> tuple[float, bool, float]:
    scoped = _window(support, reference, days)
    durations: list[float] = []
    satisfaction: list[float] = []
    for _, ticket in scoped.groupby("source_record_id", sort=False):
        opened = ticket.loc[ticket["event_type"].eq("SUPPORT_TICKET_OPENED"), "event_time"]
        closed = ticket.loc[ticket["event_type"].eq("SUPPORT_TICKET_CLOSED")]
        if len(opened) and len(closed):
            duration = (closed["event_time"].min() - opened.min()).total_seconds() / 3600.0
            if duration >= 0:
                durations.append(float(duration))
        satisfaction.extend(closed["event_value_numeric"].dropna().astype(float).tolist())
    return (
        float(np.mean(durations)) if durations else np.nan,
        bool(satisfaction),
        float(np.mean(satisfaction)) if satisfaction else np.nan,
    )


def _mrr_band(values: pd.Series) -> tuple[pd.Series, dict[str, float]]:
    positive = values.loc[values.gt(0)]
    q25, q50, q75 = (float(positive.quantile(q)) if len(positive) else 0.0 for q in (.25, .50, .75))
    def band(value: float) -> str:
        if value <= q25: return "LOW"
        if value <= q50: return "MEDIUM"
        if value <= q75: return "HIGH"
        return "VERY_HIGH"
    return values.map(band), {"q25": q25, "q50": q50, "q75": q75, "basis_accounts": int(len(positive))}


def _as_of_outcome(churn_times: list[pd.Timestamp], reactivation_times: list[pd.Timestamp]) -> str:
    if not churn_times:
        return "NO_CHURN_OBSERVED"
    if reactivation_times and any(churn > reactivation_times[-1] for churn in churn_times):
        return "REACTIVATED_THEN_CHURNED_AGAIN"
    if reactivation_times:
        return "REACTIVATED"
    if len(churn_times) >= 2:
        return "RECURRING_CHURN"
    return "SINGLE_CHURN"


def build_retrospective_features(
    events: pd.DataFrame, diagnostic: pd.DataFrame, survival: pd.DataFrame,
    taxonomy: pd.DataFrame, journeys: pd.DataFrame,
    reference_date: pd.Timestamp = REFERENCE_DATE,
) -> FeatureBuild:
    """Build one cutoff-safe row per source account; raw IDs remain internal only."""
    reference = pd.Timestamp(reference_date)
    event_work = events.copy()
    event_work["account_id"] = event_work["account_id"].astype(str)
    event_work["event_time"] = pd.to_datetime(event_work["event_time"])
    future_count = int(event_work["event_time"].gt(reference).sum())
    observed = event_work.loc[event_work["event_time"].le(reference)].copy()
    behavioral = observed.loc[observed["quality_status"].isin(MAIN_STATUSES) & ~observed["is_quarantined"].astype(bool)].copy()
    strict = behavioral.loc[behavioral["quality_status"].isin(STRICT_STATUSES)].copy()
    quarantined = observed.loc[observed["is_quarantined"].astype(bool)].copy()

    diagnostic_work = diagnostic.copy(); diagnostic_work["account_id"] = diagnostic_work["account_id"].astype(str)
    diagnostic_map = diagnostic_work.set_index("account_id").to_dict("index")
    survival_work = survival.copy(); survival_work["account_id"] = survival_work["account_id"].astype(str)
    survival_map = survival_work.drop_duplicates("account_id").set_index("account_id").to_dict("index")
    tax_main = taxonomy.loc[taxonomy["quality_population"].eq("MAIN")].copy()
    tax_main["account_id"] = tax_main["account_id"].astype(str)
    tax_map = tax_main.drop_duplicates("account_id").set_index("account_id").to_dict("index")
    strict_accounts = set(taxonomy.loc[taxonomy["quality_population"].eq("STRICT"), "account_id"].astype(str))
    full_main = journeys.loc[journeys["quality_population"].eq("MAIN") & journeys["journey_scope"].eq("FULL_OBSERVED_JOURNEY")].copy()
    full_main["account_id"] = full_main["account_id"].astype(str)
    order_map = full_main.drop_duplicates("account_id").set_index("account_id")["same_day_order_dependency"].to_dict()
    event_groups = {key: group.sort_values(["event_time", "event_order_on_same_day", "event_id"]) for key, group in behavioral.groupby("account_id", sort=False)}
    strict_counts = strict.groupby("account_id").size().to_dict()
    quarantine_counts = quarantined.groupby("account_id").size().to_dict()

    rows: list[dict[str, Any]] = []
    for account_id in sorted(diagnostic_work["account_id"].unique()):
        base = diagnostic_map[account_id]
        group = event_groups.get(account_id, behavioral.iloc[0:0])
        main_count = int(len(group)); strict_count = int(strict_counts.get(account_id, 0))
        quality_coverage = strict_count / main_count if main_count else 0.0
        warnings = int(group["quality_status"].eq("VALID_WITH_WARNING").sum())
        warning_ratio = warnings / main_count if main_count else 1.0
        usage = group.loc[group["event_type"].eq("FEATURE_USED")]
        support = group.loc[group["event_type"].str.startswith("SUPPORT_TICKET")]
        support_open = support.loc[support["event_type"].eq("SUPPORT_TICKET_OPENED")]
        churn_times = group.loc[group["event_type"].eq("CHURN_RECORDED"), "event_time"].sort_values().tolist()
        react_times = group.loc[group["event_type"].eq("REACTIVATION_RECORDED"), "event_time"].sort_values().tolist()
        subscription_starts = group.loc[group["event_type"].eq("SUBSCRIPTION_STARTED")]
        account_created = group.loc[group["event_type"].eq("ACCOUNT_CREATED"), "event_time"].min()
        observed_start = group["event_time"].min() if len(group) else reference
        observed_days = max(int((reference - observed_start).total_seconds() // 86400), 0)

        metrics: dict[str, Any] = {}
        for days in (7, 30, 60, 90):
            usage_window = _window(usage, reference, days)
            support_window = _window(support_open, reference, days)
            metrics[f"usage_count_{days}d"] = float(usage_window["event_value_numeric"].fillna(1).sum())
            metrics[f"feature_event_count_{days}d"] = int(len(usage_window))
            metrics[f"distinct_features_{days}d"] = int(usage_window["event_value_category"].dropna().nunique())
            metrics[f"support_count_{days}d"] = int(len(support_window))

        resolution, satisfaction_available, satisfaction_mean = _support_resolution(support, reference)
        last_churn = churn_times[-1] if churn_times else pd.NaT
        last_reactivation = react_times[-1] if react_times else pd.NaT
        support_before_churn = support_open.loc[support_open["event_time"].le(last_churn)] if not pd.isna(last_churn) else support_open.iloc[0:0]
        support_gap = (last_churn - support_before_churn["event_time"].max()).total_seconds() / 86400.0 if len(support_before_churn) else np.nan
        usage_after_reactivation = usage.loc[usage["event_time"].gt(last_reactivation)] if not pd.isna(last_reactivation) else usage.iloc[0:0]
        subscriptions_after_reactivation = subscription_starts.loc[subscription_starts["event_time"].gt(last_reactivation)] if not pd.isna(last_reactivation) else subscription_starts.iloc[0:0]
        churn_after_reactivation = bool(churn_times and react_times and any(item > last_reactivation for item in churn_times))
        pre_registration = int(group["event_time"].lt(account_created).sum()) if not pd.isna(account_created) else 0
        assignment = group.loc[group["event_type"].eq("CHURN_RECORDED"), "churn_assignment_status"].fillna("").astype(str)
        churn_without_active = bool(assignment.str.contains("NO_ACTIVE|UNASSIGNED", regex=True).any())
        taxonomy_row = tax_map.get(account_id, {})
        stability = str(taxonomy_row.get("stability_status", "SENSITIVE"))
        if stability not in {"ROBUST", "SENSITIVE", "UNSTABLE"}: stability = "SENSITIVE"
        current_cutoff = pd.Timestamp(base["observation_end"]) == reference
        historical_mrr = float(subscription_starts["event_value_numeric"].dropna().max()) if len(subscription_starts["event_value_numeric"].dropna()) else 0.0
        associated_mrr = float(base.get("max_mrr", 0) or 0) if current_cutoff else historical_mrr
        row = {
            "account_id": account_id, "account_key": stable_key("acct", account_id),
            "reference_date": reference, "primary_outcome": _as_of_outcome(churn_times, react_times),
            "taxonomy_class": str(taxonomy_row.get("primary_journey_class", "UNCLASSIFIED")),
            "stability_status": stability,
            "quality_population": "MAIN_WITH_STRICT_SENSITIVITY" if account_id in strict_accounts else "MAIN_ONLY",
            "quality_coverage_ratio": float(quality_coverage), "warning_dependency_ratio": float(warning_ratio),
            "main_strict_divergence": float(abs(main_count - strict_count) / main_count) if main_count else 1.0,
            "strict_supported": account_id in strict_accounts, "same_day_order_dependency": str(order_map.get(account_id, "NONE")),
            "associated_mrr": associated_mrr, "observed_days": observed_days,
            "days_since_last_usage": _days_since(reference, usage["event_time"].max() if len(usage) else None),
            "days_since_last_support": _days_since(reference, support_open["event_time"].max() if len(support_open) else None),
            "mean_resolution_hours_90d": resolution, "satisfaction_available": satisfaction_available,
            "satisfaction_mean_90d": satisfaction_mean,
            "satisfaction_low_or_missing": (not satisfaction_available) or satisfaction_mean <= 3.5,
            "churn_count": len(churn_times), "days_since_last_churn": _days_since(reference, last_churn),
            "reactivation_count": len(react_times), "days_since_last_reactivation": _days_since(reference, last_reactivation),
            "subscription_count": int(subscription_starts["subscription_id"].dropna().nunique()),
            "has_subscription_overlap": bool(base.get("has_subscription_overlap", False)),
            "usage_after_last_reactivation_count": float(usage_after_reactivation["event_value_numeric"].fillna(1).sum()),
            "new_subscription_after_reactivation": bool(len(subscriptions_after_reactivation)),
            "churn_after_reactivation": churn_after_reactivation,
            "support_near_churn": bool(not pd.isna(support_gap) and support_gap <= 30),
            "days_support_before_churn": float(support_gap) if not pd.isna(support_gap) else np.nan,
            "relevant_quarantine_count": int(quarantine_counts.get(account_id, 0)),
            "pre_registration_event_count": pre_registration, "churn_without_active_subscription": churn_without_active,
            "timeline_inconsistent": bool(pre_registration or churn_without_active),
            **metrics,
        }
        row["requires_data_review"] = bool(
            row["quality_coverage_ratio"] < .4 or row["main_strict_divergence"] > .3
            or row["has_subscription_overlap"] or row["timeline_inconsistent"]
            or row["relevant_quarantine_count"] > 0
        )
        rows.append(row)

    result = pd.DataFrame(rows).sort_values("account_key").reset_index(drop=True)
    result["mrr_band"], thresholds = _mrr_band(result["associated_mrr"])
    accounting = {
        "reference_date": reference.isoformat(), "accounts": len(result),
        "events_at_or_before_cutoff": int(len(observed)), "events_after_cutoff_excluded": future_count,
        "behavioral_events": int(len(behavioral)), "strict_events": int(len(strict)),
        "quarantined_events_available_for_quality_only": int(len(quarantined)),
        "quarantined_behavioral_signals": 0, "mrr_band_thresholds": thresholds,
        "quality_coverage_definition": "VALID_EVENTS_DIVIDED_BY_MAIN_USABLE_EVENTS",
        "historical_cutoff_support": True,
    }
    return FeatureBuild(result, accounting)
