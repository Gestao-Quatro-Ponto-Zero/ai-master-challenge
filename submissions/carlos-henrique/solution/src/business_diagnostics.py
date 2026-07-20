"""Descriptive product, support, revenue, cohort and attention diagnostics."""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
import pandas as pd

from churn_diagnostics import usable_events


MIN_GROUP_SIZE = 20


def _json_number(value: Any) -> float | None:
    return None if pd.isna(value) else float(value)


def data_health(
    events: pd.DataFrame,
    quarantine: pd.DataFrame,
    episodes: pd.DataFrame,
) -> dict[str, Any]:
    valid = int(events["quality_status"].eq("VALID").sum())
    warnings = int(events["quality_status"].eq("VALID_WITH_WARNING").sum())
    quarantined = int(len(quarantine))
    generated = valid + warnings + quarantined
    active_accounts = int(events["account_id"].nunique())
    quarantined_accounts = int(quarantine["account_id"].nunique())
    periods = events.assign(period=events["event_time"].dt.to_period("Q").astype(str))
    return {
        "methodology": "Data-health metrics use quarantine only as exclusion and coverage evidence, never as business behavior.",
        "population": "All generated Phase 2 events for quality; usable population for analytical coverage.",
        "eligible_generated_events": generated,
        "valid_events": valid,
        "warning_events": warnings,
        "quarantined_events": quarantined,
        "analytical_coverage_ratio": float((valid + warnings) / generated),
        "strict_coverage_ratio": float(valid / generated),
        "quarantine_ratio": float(quarantined / generated),
        "warning_ratio_among_usable": float(warnings / (valid + warnings)),
        "accounts_with_usable_event": active_accounts,
        "accounts_affected_by_quarantine": quarantined_accounts,
        "subscriptions_with_warning": int(episodes["quality_status"].eq("VALID_WITH_WARNING").sum()),
        "episodes": int(len(episodes)),
        "overlapping_episode_ratio": float(episodes["has_overlap"].mean()),
        "coverage_by_event_type": [
            {
                "event_type": event_type,
                "usable_events": int(len(group)),
                "valid_events": int(group["quality_status"].eq("VALID").sum()),
                "warning_events": int(group["quality_status"].eq("VALID_WITH_WARNING").sum()),
                "accounts": int(group["account_id"].nunique()),
            }
            for event_type, group in events.groupby("event_type", sort=True)
        ],
        "coverage_by_period": [
            {"period": period, "usable_events": int(len(group)), "accounts": int(group["account_id"].nunique())}
            for period, group in periods.groupby("period", sort=True)
        ],
        "coverage_by_account": {
            "accounts": active_accounts,
            "events_per_account_min": int(events.groupby("account_id").size().min()),
            "events_per_account_median": float(events.groupby("account_id").size().median()),
            "events_per_account_max": int(events.groupby("account_id").size().max()),
        },
        "limitations": [
            "Analytical coverage measures usability of this dataset, not customer or business quality.",
            "One event may carry multiple warning flags.",
        ],
    }


def _group_metrics(accounts: pd.DataFrame, metrics: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for outcome, group in accounts.groupby("primary_outcome", sort=True):
        item: dict[str, Any] = {
            "outcome": outcome,
            "accounts": int(len(group)),
            "denominator_accounts": int(len(accounts)),
        }
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce")
            item[metric] = {
                "mean": _json_number(values.mean()),
                "median": _json_number(values.median()),
                "q1": _json_number(values.quantile(0.25)),
                "q3": _json_number(values.quantile(0.75)),
                "missing_ratio": float(values.isna().mean()),
            }
        rows.append(item)
    return rows


def product_usage_diagnostics(
    accounts: pd.DataFrame,
    events: pd.DataFrame,
) -> dict[str, Any]:
    cutoffs = accounts.set_index("account_id")["feature_cutoff_time"]
    usage = usable_events(events).loc[lambda x: x["event_type"].eq("FEATURE_USED")].copy()
    usage = usage.loc[
        usage.apply(lambda row: row["event_time"] <= cutoffs.get(row["account_id"], pd.Timestamp.min), axis=1)
    ]
    all_accounts = int(len(accounts))
    feature_presence = (
        usage.groupby("event_value_category")["account_id"].nunique().sort_values(ascending=False)
    )
    pre_churn_ids = set(accounts.loc[accounts["churn_count"].gt(0), "account_id"])
    churn_presence = (
        usage.loc[usage["account_id"].isin(pre_churn_ids)]
        .groupby("event_value_category")["account_id"].nunique()
        .sort_values(ascending=False)
    )
    metrics = [
        "feature_event_count_lifetime", "feature_event_count_90d", "feature_event_count_30d",
        "active_days_90d", "distinct_features_90d", "usage_intensity_per_active_day",
        "days_since_last_feature_use", "top_feature_share_lifetime", "usage_change_30d_vs_prior_60d",
    ]
    return {
        "methodology": "Usage is aggregated at account grain and limited to each account's first-churn cutoff or observation_end.",
        "population": "VALID + VALID_WITH_WARNING; quarantine excluded",
        "denominator_accounts": all_accounts,
        "accounts_without_usage_30d": int(accounts["feature_event_count_30d"].eq(0).sum()),
        "observed_share_without_usage_30d": float(accounts["feature_event_count_30d"].eq(0).mean()),
        "accounts_single_feature_lifetime": int(accounts["distinct_features_lifetime"].eq(1).sum()),
        "feature_rank_by_account_presence": [
            {"feature": str(name), "accounts": int(value), "observed_share": float(value / all_accounts)}
            for name, value in feature_presence.items()
        ],
        "feature_rank_before_first_churn": [
            {
                "feature": str(name),
                "accounts": int(value),
                "denominator_churned_accounts": int(len(pre_churn_ids)),
                "observed_share": float(value / len(pre_churn_ids)) if pre_churn_ids else None,
            }
            for name, value in churn_presence.items()
        ],
        "metrics_by_outcome": _group_metrics(accounts, metrics),
        "limitations": [
            "Feature names are structured product categories; no free text is used.",
            "Differences are associations and do not establish an outcome mechanism.",
            "Quarantined usage substantially limits coverage.",
        ],
    }


def support_diagnostics(accounts: pd.DataFrame, events: pd.DataFrame) -> dict[str, Any]:
    active = usable_events(events)
    opens = active.loc[active["event_type"].eq("SUPPORT_TICKET_OPENED")]
    closes = active.loc[active["event_type"].eq("SUPPORT_TICKET_CLOSED")]
    churn = active.loc[active["event_type"].eq("CHURN_RECORDED"), ["account_id", "event_time"]]
    first_churn = churn.groupby("account_id")["event_time"].min()
    near = post = 0
    for _, ticket in opens.iterrows():
        boundary = first_churn.get(ticket["account_id"], pd.NaT)
        if pd.notna(boundary):
            delta = (boundary.normalize() - ticket["event_time"].normalize()).days
            near += int(0 <= delta <= 30)
            post += int(ticket["event_time"] > boundary)
    open_ids = set(opens["source_record_id"].dropna().astype(str))
    close_ids = set(closes["source_record_id"].dropna().astype(str))

    satisfaction = pd.to_numeric(closes["event_value_numeric"], errors="coerce")
    return {
        "methodology": "Pre-cutoff account features use only openings/closures available by cutoff; post-churn counts are separate descriptive evidence.",
        "population": "VALID + VALID_WITH_WARNING; quarantine excluded",
        "denominator_accounts": int(len(accounts)),
        "usable_ticket_open_events": int(len(opens)),
        "usable_ticket_close_events": int(len(closes)),
        "tickets_without_usable_close": int(len(open_ids - close_ids)),
        "closures_without_usable_open": int(len(close_ids - open_ids)),
        "satisfaction_available": int(satisfaction.notna().sum()),
        "accounts_with_recurring_support": int(accounts["support_ticket_count_lifetime"].ge(2).sum()),
        "observed_recurring_support_proportion": float(accounts["support_ticket_count_lifetime"].ge(2).mean()),
        "satisfaction_missing": int(satisfaction.isna().sum()),
        "ticket_opened_within_30d_before_first_churn": near,
        "ticket_opened_after_first_churn": post,
        "metrics_by_outcome": _group_metrics(
            accounts,
            [
                "support_ticket_count_lifetime", "support_ticket_count_30d",
                "support_ticket_count_60d", "support_ticket_count_90d",
                "mean_ticket_resolution_hours", "median_ticket_resolution_hours", "satisfaction_mean",
            ],
        ),
        "limitations": [
            "Support is account-grain and cannot be attributed uniquely to one subscription.",
            "Resolution is looked up only for usable closure events available before cutoff.",
            "Ticket proximity is descriptive and not causal.",
        ],
    }


def _mrr_band(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce").fillna(0)
    if numeric.nunique() < 4:
        return pd.Series("ALL", index=series.index, dtype="string")
    return pd.qcut(numeric.rank(method="first"), 4, labels=["Q1_LOW", "Q2", "Q3", "Q4_HIGH"]).astype("string")


def revenue_diagnostics(accounts: pd.DataFrame, subscriptions: pd.DataFrame) -> dict[str, Any]:
    by_outcome = []
    for outcome, group in accounts.groupby("primary_outcome", sort=True):
        by_outcome.append(
            {
                "outcome": outcome,
                "accounts": int(len(group)),
                "mrr_at_account_cutoff": float(group["total_mrr_current"].sum()),
                "median_mrr_at_account_cutoff": float(group["total_mrr_current"].median()),
            }
        )
    churned = accounts["churn_count"].gt(0)
    reactivated = accounts["is_reactivated"]
    open_mask = subscriptions["is_censored_episode"]
    recent_churn = accounts["last_churn_time"].notna() & (
        (accounts["observation_end"] - accounts["last_churn_time"]).dt.days.le(90)
    )
    no_recent_usage = accounts["feature_event_count_30d"].eq(0)
    return {
        "methodology": "MRR is descriptive. Account MRR is the sum active at that account's cutoff; episode MRR is not called lost or saved revenue.",
        "population": "Usable account features and all governed subscription episodes",
        "denominator_accounts": int(len(accounts)),
        "denominator_episodes": int(len(subscriptions)),
        "mrr_at_account_cutoffs_total": float(accounts["total_mrr_current"].sum()),
        "episode_mrr_total": float(subscriptions["mrr"].fillna(0).sum()),
        "mrr_associated_with_churned_accounts": float(accounts.loc[churned, "total_mrr_current"].sum()),
        "mrr_associated_with_reactivated_accounts": float(accounts.loc[reactivated, "total_mrr_current"].sum()),
        "mrr_associated_with_open_episodes": float(subscriptions.loc[open_mask, "mrr"].fillna(0).sum()),
        "mrr_associated_with_closed_episodes": float(subscriptions.loc[~open_mask, "mrr"].fillna(0).sum()),
        "mrr_in_accounts_with_multiple_subscriptions": float(
            accounts.loc[accounts["subscription_count"].gt(1), "total_mrr_current"].sum()
        ),
        "mrr_by_outcome": by_outcome,
        "mrr_band_definition": "Quartiles of account MRR active at the account-specific cutoff; stable rank tie-breaking.",
        "mrr_associated_with_recent_churn_90d": float(accounts.loc[recent_churn, "total_mrr_current"].sum()),
        "mrr_associated_with_no_usage_30d": float(accounts.loc[no_recent_usage, "total_mrr_current"].sum()),
        "mrr_bands": [
            {
                "band": band,
                "accounts": int(len(group)),
                "mrr": float(group["total_mrr_current"].sum()),
                "churn_observed_accounts": int(group["churn_count"].gt(0).sum()),
            }
            for band, group in accounts.assign(mrr_band=_mrr_band(accounts["total_mrr_current"]))
            .groupby("mrr_band", observed=True, sort=True)
        ],
        "limitations": [
            "MRR fields are associations at observed cutoffs and do not prove realized loss or recovery.",
            "Overlapping episodes can make episode-level MRR non-additive as account exposure.",
        ],
    }


def _cohort_rows(accounts: pd.DataFrame, cohort_type: str, values: pd.Series) -> list[dict[str, Any]]:
    work = accounts.assign(_cohort=values.fillna("MISSING").astype(str))
    rows: list[dict[str, Any]] = []
    for cohort, group in work.groupby("_cohort", sort=True):
        size = len(group)
        rows.append(
            {
                "cohort_type": cohort_type,
                "cohort": cohort,
                "accounts": int(size),
                "churn_observed_accounts": int(group["churn_count"].gt(0).sum()),
                "observed_churn_proportion": float(group["churn_count"].gt(0).mean()),
                "recurring_churn_accounts": int(group["churn_count"].ge(2).sum()),
                "reactivated_accounts": int(group["is_reactivated"].sum()),
                "mrr_at_cutoff": float(group["total_mrr_current"].sum()),
                "median_active_days_90d": float(group["active_days_90d"].median()),
                "median_support_tickets_90d": float(group["support_ticket_count_90d"].median()),
                "mean_quality_coverage_ratio": float(group["quality_coverage_ratio"].mean()),
                "sample_status": "OK" if size >= MIN_GROUP_SIZE else "SMALL_SAMPLE",
            }
        )
    return rows


def cohort_diagnostics(accounts: pd.DataFrame, episodes: pd.DataFrame) -> dict[str, Any]:
    first_episode = episodes.sort_values(["episode_start", "subscription_id"]).groupby("account_id").first()
    first_month = accounts["account_id"].map(first_episode["episode_start"].dt.to_period("M").astype(str))
    initial_plan = accounts["account_id"].map(first_episode["plan"])
    initial_usage = pd.cut(
        accounts["initial_usage_event_count_30d"],
        bins=[-1, 0, 2, 5, np.inf],
        labels=["NONE", "LOW_1_2", "MEDIUM_3_5", "HIGH_6_PLUS"],
    ).astype("string")
    cohorts: list[dict[str, Any]] = []
    cohorts += _cohort_rows(accounts, "signup_month", accounts["observation_start"].dt.to_period("M").astype(str))
    cohorts += _cohort_rows(accounts, "signup_quarter", accounts["observation_start"].dt.to_period("Q").astype(str))
    cohorts += _cohort_rows(accounts, "first_subscription_month", first_month)
    cohorts += _cohort_rows(accounts, "initial_plan", initial_plan)
    cohorts += _cohort_rows(accounts, "mrr_band", _mrr_band(accounts["total_mrr_current"]))
    cohorts += _cohort_rows(accounts, "initial_usage_intensity", initial_usage)
    return {
        "methodology": "Descriptive cohorts at account grain; observed proportions are not temporal rates.",
        "population": "VALID + VALID_WITH_WARNING account features; quarantine excluded",
        "minimum_group_size": MIN_GROUP_SIZE,
        "cohorts": cohorts,
        "groups": len(cohorts),
        "small_sample_groups": int(sum(row["sample_status"] == "SMALL_SAMPLE" for row in cohorts)),
        "limitations": [
            "Unequal follow-up and administrative censoring affect comparisons.",
            "Groups below the minimum remain available but are not promoted as principal findings.",
        ],
    }


def build_attention_segments(accounts: pd.DataFrame) -> pd.DataFrame:
    """Return no more than five aggregate operational situations, never a score."""

    high_mrr = accounts["total_mrr_current"].ge(accounts["total_mrr_current"].quantile(0.75))
    low_usage = accounts["feature_event_count_30d"].le(accounts["feature_event_count_30d"].quantile(0.25))
    recent_churn = accounts["last_churn_time"].notna() & (
        (accounts["observation_end"] - accounts["last_churn_time"]).dt.days.le(90)
    )
    definitions: list[tuple[str, pd.Series, str, str, str, str]] = [
        (
            "HIGH_MRR_RECENT_CHURN", high_mrr & recent_churn,
            "MRR at cutoff in top quartile and last usable churn within 90 days of observation_end.",
            "Review commercial status and timeline with Customer Success.", "HIGH",
            "MRR is associated exposure, not proven loss.",
        ),
        (
            "REACTIVATED_HIGH_VALUE", high_mrr & accounts["is_reactivated"],
            "Explicit usable reactivation and MRR at cutoff in top quartile.",
            "Investigate conditions around return and subsequent experience.", "HIGH",
            "Post-reactivation evidence is descriptive.",
        ),
        (
            "RECURRING_CHURN_ACCOUNT", accounts["churn_count"].ge(2),
            "At least two usable churn events.",
            "Review recurring lifecycle and eligibility for temporal analysis.", "HIGH",
            "Many churn events carry warnings and need sensitivity controls.",
        ),
        (
            "LOW_USAGE_HIGH_MRR", high_mrr & low_usage,
            "Top-quartile MRR at cutoff and bottom-quartile 30-day usage events.",
            "Validate adoption context before any retention outreach.", "MEDIUM",
            "Low measured usage may reflect data coverage rather than low adoption.",
        ),
        (
            "DATA_QUALITY_REVIEW_REQUIRED", accounts["quality_coverage_ratio"].lt(0.5),
            "Less than 50% of generated account events are analytically usable.",
            "Prioritize upstream temporal-data remediation before account-level action.", "HIGH",
            "This is a data-governance segment, not a customer-risk signal.",
        ),
    ]
    rows = []
    for name, mask, definition, action, priority, limitation in definitions:
        subset = accounts.loc[mask]
        rows.append(
            {
                "segment_name": name,
                "account_count": int(len(subset)),
                "associated_mrr": float(subset["total_mrr_current"].sum()),
                "definition": definition,
                "evidence": f"{len(subset)} of {len(accounts)} accounts ({len(subset) / len(accounts):.2%}).",
                "limitations": limitation,
                "recommended_action": action,
                "priority_level": priority,
            }
        )
    return pd.DataFrame(rows)
