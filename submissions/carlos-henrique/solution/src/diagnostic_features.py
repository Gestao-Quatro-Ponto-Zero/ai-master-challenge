"""Leakage-controlled account and subscription diagnostic feature tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from churn_diagnostics import classify_account_outcomes, usable_events


WINDOW_DAYS = (7, 30, 60, 90)


@dataclass(frozen=True)
class FeatureBuild:
    accounts: pd.DataFrame
    subscriptions: pd.DataFrame
    observation_end: pd.Timestamp


def _window(frame: pd.DataFrame, cutoff: pd.Timestamp, days: int) -> pd.DataFrame:
    lower = cutoff.normalize() - pd.Timedelta(days=days - 1)
    return frame.loc[frame["event_time"].between(lower, cutoff, inclusive="both")]


def _days_since(cutoff: pd.Timestamp, values: pd.Series) -> float | None:
    values = pd.to_datetime(values, errors="coerce").dropna()
    return None if values.empty else float((cutoff.normalize() - values.max().normalize()).days)


def _flags_contain(values: pd.Series, token: str | None = None) -> bool:
    values = values.fillna("").astype(str)
    if token is None:
        return bool(values.str.len().gt(0).any())
    return bool(values.str.contains(token, regex=False).any())


def _overlap_counts(episodes: pd.DataFrame, boundary: pd.Timestamp) -> dict[str, int]:
    """Count episode intersections observed no later than the supplied boundary."""

    counts = {str(value): 0 for value in episodes["episode_id"]}
    ordered = episodes.loc[episodes["episode_start"].le(boundary)].sort_values(
        ["episode_start", "subscription_id"]
    )
    indexes = list(ordered.index)
    for position, left_index in enumerate(indexes):
        left = ordered.loc[left_index]
        left_end = min(
            pd.to_datetime(left["episode_end"]) if pd.notna(left["episode_end"]) else boundary,
            boundary,
        )
        for right_index in indexes[position + 1 :]:
            right = ordered.loc[right_index]
            if right["episode_start"] > left_end:
                break
            right_end = min(
                pd.to_datetime(right["episode_end"]) if pd.notna(right["episode_end"]) else boundary,
                boundary,
            )
            if left["episode_start"] <= right_end and right["episode_start"] <= left_end:
                counts[str(left["episode_id"])] += 1
                counts[str(right["episode_id"])] += 1
    return counts


def _support_resolution_map(raw_support: pd.DataFrame | None) -> dict[str, float]:
    if raw_support is None:
        return {}
    required = {"ticket_id", "resolution_time_hours"}
    if not required.issubset(raw_support.columns):
        raise ValueError("Raw support data lacks the governed resolution fields.")
    work = raw_support[["ticket_id", "resolution_time_hours"]].copy()
    if work["ticket_id"].duplicated().any():
        raise ValueError("ticket_id must be unique before resolution lookup.")
    numeric = pd.to_numeric(work["resolution_time_hours"], errors="coerce")
    return {
        str(ticket): float(value)
        for ticket, value in zip(work["ticket_id"], numeric)
        if pd.notna(value) and float(value) >= 0
    }


def build_account_features(
    events: pd.DataFrame,
    episodes: pd.DataFrame,
    quarantined_events: pd.DataFrame | None = None,
    raw_support: pd.DataFrame | None = None,
    strict: bool = False,
) -> pd.DataFrame:
    """Build one leakage-controlled row per account at its diagnostic cutoff."""

    active = usable_events(events, strict=strict)
    if active.empty:
        raise ValueError("No usable events for the requested population.")
    observation_end = pd.to_datetime(active["event_time"]).max()
    outcomes = classify_account_outcomes(active).set_index("account_id")
    resolution_map = _support_resolution_map(raw_support)
    generated = pd.concat([events, quarantined_events], ignore_index=True) if quarantined_events is not None else events
    rows: list[dict[str, Any]] = []

    active_groups = {
        str(account_id): group.sort_values(["event_time", "event_order_on_same_day", "event_id"])
        for account_id, group in active.groupby("account_id", sort=False)
    }
    episode_groups = {
        str(account_id): group.sort_values(["episode_start", "subscription_id"])
        for account_id, group in episodes.groupby("account_id", sort=False)
    }
    generated_counts = generated.groupby("account_id", sort=False).size().to_dict()
    usable_all = events.loc[
        events["quality_status"].isin({"VALID", "VALID_WITH_WARNING"})
        & ~events["is_quarantined"].astype(bool)
    ]
    usable_counts = usable_all.groupby("account_id", sort=False).size().to_dict()

    for account_id, outcome in outcomes.iterrows():
        account = active_groups[str(account_id)]
        observation_start = pd.to_datetime(account["event_time"]).min()
        cutoff = outcome["first_churn_time"] if pd.notna(outcome["first_churn_time"]) else observation_end
        cutoff = pd.Timestamp(cutoff)
        pre = account.loc[account["event_time"].le(cutoff)].copy()
        usage = pre.loc[pre["event_type"].eq("FEATURE_USED")]
        support_open = pre.loc[pre["event_type"].eq("SUPPORT_TICKET_OPENED")]
        support_closed = pre.loc[pre["event_type"].eq("SUPPORT_TICKET_CLOSED")]
        episode_source = episode_groups.get(str(account_id), episodes.iloc[0:0])
        account_episodes = episode_source.loc[episode_source["episode_start"].le(cutoff)]
        overlap_counts = _overlap_counts(account_episodes, cutoff)
        active_at_cutoff = account_episodes.loc[
            account_episodes["episode_end"].isna() | account_episodes["episode_end"].gt(cutoff)
        ]
        closed_at_cutoff = account_episodes.loc[account_episodes["episode_end"].le(cutoff)]
        resolutions = support_closed["source_record_id"].astype(str).map(resolution_map).dropna()
        satisfaction = pd.to_numeric(support_closed["event_value_numeric"], errors="coerce").dropna()
        generated_count = int(generated_counts.get(account_id, generated_counts.get(str(account_id), 0)))
        usable_count = int(usable_counts.get(account_id, usable_counts.get(str(account_id), 0)))
        feature_counts = usage["event_value_category"].value_counts()
        total_usage = float(pd.to_numeric(usage["event_value_numeric"], errors="coerce").fillna(0).sum())
        top_share = float(feature_counts.max() / feature_counts.sum()) if feature_counts.sum() else None
        row: dict[str, Any] = {
            **outcome.to_dict(),
            "account_id": account_id,
            "observation_start": observation_start,
            "observation_end": observation_end,
            "feature_cutoff_time": cutoff,
            "observed_days": int(max((cutoff.normalize() - observation_start.normalize()).days, 0)),
            "subscription_count": int(len(account_episodes)),
            "active_subscription_count_at_observation_end": int(len(active_at_cutoff)),
            "closed_subscription_count": int(len(closed_at_cutoff)),
            "overlapping_subscription_count": int(sum(v > 0 for v in overlap_counts.values())),
            "total_mrr_current": float(active_at_cutoff["mrr"].fillna(0).sum()),
            "max_mrr": float(account_episodes["mrr"].max()) if len(account_episodes) else None,
            "mean_mrr": float(account_episodes["mrr"].mean()) if len(account_episodes) else None,
            "first_plan": account_episodes.iloc[0]["plan"] if len(account_episodes) else None,
            "latest_plan": account_episodes.iloc[-1]["plan"] if len(account_episodes) else None,
            "feature_event_count_lifetime": int(len(usage)),
            "distinct_features_lifetime": int(usage["event_value_category"].nunique()),
            "active_days_lifetime": int(usage["event_time"].dt.normalize().nunique()),
            "feature_usage_count_lifetime": total_usage,
            "usage_intensity_per_active_day": float(total_usage / usage["event_time"].dt.normalize().nunique()) if len(usage) else 0.0,
            "top_feature_share_lifetime": top_share,
            "support_ticket_count_lifetime": int(len(support_open)),
            "closed_ticket_count_lifetime": int(len(support_closed)),
            "mean_ticket_resolution_hours": float(resolutions.mean()) if len(resolutions) else None,
            "median_ticket_resolution_hours": float(resolutions.median()) if len(resolutions) else None,
            "satisfaction_mean": float(satisfaction.mean()) if len(satisfaction) else None,
            "satisfaction_latest": float(satisfaction.iloc[-1]) if len(satisfaction) else None,
            "days_since_last_feature_use": _days_since(cutoff, usage["event_time"]),
            "days_since_last_support_ticket": _days_since(cutoff, support_open["event_time"]),
            "has_usage_warning": _flags_contain(usage["quality_flags"]),
            "has_support_warning": _flags_contain(pd.concat([support_open, support_closed])["quality_flags"]),
            "has_subscription_overlap": bool(any(v > 0 for v in overlap_counts.values())),
            "quality_coverage_ratio": float(usable_count / generated_count) if generated_count else None,
        }
        for days in WINDOW_DAYS:
            use_window = _window(usage, cutoff, days)
            support_window = _window(support_open, cutoff, days)
            row[f"feature_event_count_{days}d"] = int(len(use_window))
            row[f"distinct_features_{days}d"] = int(use_window["event_value_category"].nunique())
            row[f"active_days_{days}d"] = int(use_window["event_time"].dt.normalize().nunique())
            row[f"feature_usage_count_{days}d"] = float(
                pd.to_numeric(use_window["event_value_numeric"], errors="coerce").fillna(0).sum()
            )
            row[f"support_ticket_count_{days}d"] = int(len(support_window))
        initial_boundary = min(cutoff, observation_start + pd.Timedelta(days=29))
        row["initial_usage_event_count_30d"] = int(
            len(usage.loc[usage["event_time"].between(observation_start, initial_boundary, inclusive="both")])
        )
        row["usage_change_30d_vs_prior_60d"] = float(
            row["feature_event_count_30d"] - (row["feature_event_count_90d"] - row["feature_event_count_30d"]) / 2
        )
        rows.append(row)

    result = pd.DataFrame(rows).sort_values("account_id").reset_index(drop=True)
    forbidden = {"churn_flag", "account_name", "feedback_text", "reason_code", "refund_amount_usd"}
    if not forbidden.isdisjoint(result.columns):
        raise AssertionError("A prohibited leakage or privacy field entered account features.")
    if result["account_id"].duplicated().any():
        raise AssertionError("Account feature grain is not unique.")
    return result


def build_subscription_features(
    events: pd.DataFrame,
    episodes: pd.DataFrame,
    raw_support: pd.DataFrame | None = None,
    strict: bool = False,
) -> pd.DataFrame:
    """Build one row per episode; support is contextual at account/interval grain."""

    active = usable_events(events, strict=strict)
    observation_end = pd.to_datetime(active["event_time"]).max()
    resolution_map = _support_resolution_map(raw_support)
    rows: list[dict[str, Any]] = []
    account_event_groups = {
        str(account_id): group
        for account_id, group in active.groupby("account_id", sort=False)
    }
    usage_event_groups = {
        str(subscription_id): group
        for subscription_id, group in active.loc[active["event_type"].eq("FEATURE_USED")].groupby("subscription_id", sort=False)
    }
    overlap_by_episode: dict[str, int] = {}
    for _, group in episodes.groupby("account_id", sort=True):
        overlap_by_episode.update(_overlap_counts(group, observation_end))

    for _, episode in episodes.sort_values(["account_id", "episode_start", "subscription_id"]).iterrows():
        start = pd.Timestamp(episode["episode_start"])
        natural_end = pd.Timestamp(episode["episode_end"]) if pd.notna(episode["episode_end"]) else observation_end
        boundary = min(natural_end, observation_end)
        account_source = account_event_groups.get(str(episode["account_id"]), active.iloc[0:0])
        account_events = account_source.loc[
            account_source["event_time"].between(start, boundary, inclusive="both")
        ]
        usage_source = usage_event_groups.get(str(episode["subscription_id"]), active.iloc[0:0])
        usage = usage_source.loc[
            usage_source["event_time"].between(start, boundary, inclusive="both")
        ]
        support_open = account_events.loc[account_events["event_type"].eq("SUPPORT_TICKET_OPENED")]
        support_closed = account_events.loc[account_events["event_type"].eq("SUPPORT_TICKET_CLOSED")]
        resolutions = support_closed["source_record_id"].astype(str).map(resolution_map).dropna()
        rows.append(
            {
                "episode_id": episode["episode_id"],
                "account_id": episode["account_id"],
                "subscription_id": episode["subscription_id"],
                "episode_start": start,
                "episode_end": episode["episode_end"],
                "episode_duration_days": int(max((boundary.normalize() - start.normalize()).days, 0)),
                "observed_duration_days": int(max((boundary.normalize() - start.normalize()).days, 0)),
                "episode_status": episode["episode_status"],
                "plan": episode["plan"],
                "mrr": episode["mrr"],
                "has_churn_during_episode": bool(account_events["event_type"].eq("CHURN_RECORDED").any()),
                "has_reactivation_during_episode": bool(account_events["event_type"].eq("REACTIVATION_RECORDED").any()),
                "usage_event_count": int(len(usage)),
                "usage_active_days": int(usage["event_time"].dt.normalize().nunique()),
                "distinct_features_used": int(usage["event_value_category"].nunique()),
                "support_ticket_count": int(len(support_open)),
                "mean_resolution_hours": float(resolutions.mean()) if len(resolutions) else None,
                "overlap_count": int(overlap_by_episode.get(str(episode["episode_id"]), 0)),
                "quality_status": episode["quality_status"],
                "quality_flags": episode["quality_flags"],
                "is_censored_episode": bool(pd.isna(episode["episode_end"]) or episode["episode_end"] > observation_end),
            }
        )
    result = pd.DataFrame(rows).sort_values("episode_id").reset_index(drop=True)
    if result["episode_id"].duplicated().any():
        raise AssertionError("Episode feature grain is not unique.")
    return result


def build_feature_tables(
    events: pd.DataFrame,
    episodes: pd.DataFrame,
    quarantined_events: pd.DataFrame,
    raw_support: pd.DataFrame | None = None,
    strict: bool = False,
) -> FeatureBuild:
    active = usable_events(events, strict=strict)
    return FeatureBuild(
        accounts=build_account_features(events, episodes, quarantined_events, raw_support, strict),
        subscriptions=build_subscription_features(events, episodes, raw_support, strict),
        observation_end=pd.to_datetime(active["event_time"]).max(),
    )
