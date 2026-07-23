"""Governed account-level survival and landmark datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


MAIN_QUALITY = frozenset({"VALID", "VALID_WITH_WARNING"})
STRICT_QUALITY = frozenset({"VALID"})
FORBIDDEN_COLUMNS = frozenset(
    {"account_name", "churn_flag", "feedback_text", "reason_code", "refund_amount_usd"}
)


@dataclass(frozen=True)
class LandmarkBuild:
    dataset: pd.DataFrame
    accounting: dict[str, int]


def usable_events(events: pd.DataFrame, strict: bool = False) -> pd.DataFrame:
    """Return the authorized event population with quarantine excluded."""

    required = {"quality_status", "is_quarantined", "event_time", "account_id", "event_type"}
    if not required.issubset(events.columns):
        raise ValueError(f"Event log is missing: {sorted(required - set(events.columns))}")
    statuses = STRICT_QUALITY if strict else MAIN_QUALITY
    active = events.loc[
        events["quality_status"].isin(statuses) & ~events["is_quarantined"].astype(bool)
    ].copy()
    # Parquet-backed Arrow strings are efficient on disk but costly for the
    # repeated, tiny account slices required by temporal boundary checks.
    for column in ("account_id", "event_id", "event_type", "quality_status", "subscription_id", "event_value_category", "source_record_id"):
        if column in active.columns:
            active[column] = active[column].astype("object")
    active["event_time"] = pd.to_datetime(active["event_time"], errors="raise")
    return active.sort_values(
        ["account_id", "event_time", "event_order_on_same_day", "event_id"]
    ).reset_index(drop=True)


def _numeric_band(value: float | int | None, kind: str) -> str:
    if value is None or pd.isna(value):
        return "MISSING"
    number = float(value)
    if kind == "mrr":
        if number <= 0:
            return "ZERO"
        if number < 500:
            return "LOW_LT_500"
        if number < 2_000:
            return "MID_500_1999"
        return "HIGH_GE_2000"
    if number <= 0:
        return "NONE"
    if number <= 2:
        return "LOW_1_2"
    if number <= 5:
        return "MID_3_5"
    return "HIGH_GE_6"


def _subscription_band(count: int) -> str:
    if count <= 0:
        return "NONE"
    if count == 1:
        return "ONE"
    if count <= 4:
        return "TWO_TO_FOUR"
    return "FIVE_PLUS"


def _quality_label(frame: pd.DataFrame) -> str:
    return "INCLUDES_WARNING" if frame["quality_status"].eq("VALID_WITH_WARNING").any() else "VALID_ONLY"


def _first_event_time(frame: pd.DataFrame, event_type: str) -> pd.Timestamp | pd.NaT:
    values = frame.loc[frame["event_type"].eq(event_type), "event_time"]
    return pd.NaT if values.empty else pd.Timestamp(values.min())


def build_account_survival_dataset(
    account_features: pd.DataFrame,
    events: pd.DataFrame,
    episodes: pd.DataFrame,
    *,
    strict: bool = False,
    origin: str = "subscription",
    observation_end: pd.Timestamp | str | None = None,
) -> pd.DataFrame:
    """Build one governed row per Phase 3 account.

    Behavioral bands describe a fixed 30-day window and are reserved for
    landmark analysis; ordinary grouped curves use baseline-only attributes.
    """

    if origin not in {"subscription", "signup"}:
        raise ValueError("origin must be 'subscription' or 'signup'")
    if account_features["account_id"].duplicated().any():
        raise ValueError("Account features must contain one row per account_id.")
    feature_work = account_features.copy()
    feature_work["account_id"] = feature_work["account_id"].astype("object")
    active = usable_events(events, strict=strict)
    boundary = pd.Timestamp(observation_end) if observation_end is not None else active["event_time"].max()
    authorized_subscriptions = set(
        active.loc[active["event_type"].eq("SUBSCRIPTION_STARTED"), "subscription_id"].dropna().astype(str)
    )
    episode_work = episodes.loc[episodes["subscription_id"].astype(str).isin(authorized_subscriptions)].copy()
    for column in ("account_id", "subscription_id", "plan"):
        episode_work[column] = episode_work[column].astype("object")
    episode_work["episode_start"] = pd.to_datetime(episode_work["episode_start"], errors="coerce")
    episode_work["episode_end"] = pd.to_datetime(episode_work["episode_end"], errors="coerce")
    account_lookup = feature_work.set_index("account_id")
    event_groups = {str(key): value for key, value in active.groupby("account_id", sort=False)}
    episode_groups = {str(key): value for key, value in episode_work.groupby("account_id", sort=False)}
    rows: list[dict[str, Any]] = []

    for account_id in sorted(map(str, feature_work["account_id"])):
        account = event_groups.get(account_id, active.iloc[0:0])
        account_episodes = episode_groups.get(account_id, episode_work.iloc[0:0]).sort_values(
            ["episode_start", "subscription_id"]
        )
        exposure_type = "SUBSCRIPTION_STARTED" if origin == "subscription" else "ACCOUNT_CREATED"
        exposure_start = _first_event_time(account, exposure_type)
        exclusion_reason: str | None = None
        if pd.isna(exposure_start):
            exclusion_reason = "NO_VALID_SUBSCRIPTION_START" if origin == "subscription" else "NO_VALID_SIGNUP"
        elif exposure_start > boundary:
            exclusion_reason = "EXPOSURE_AFTER_OBSERVATION_END"

        churns = account.loc[account["event_type"].eq("CHURN_RECORDED")].copy()
        pre_exposure_churn_count = 0
        first_churn = pd.NaT
        if pd.notna(exposure_start):
            pre_exposure_churn_count = int(churns["event_time"].lt(exposure_start).sum())
            eligible_churns = churns.loc[churns["event_time"].ge(exposure_start), "event_time"]
            if not eligible_churns.empty:
                first_churn = pd.Timestamp(eligible_churns.min())

        exposure_end = first_churn if pd.notna(first_churn) else boundary
        duration_days: float | None = None
        event_observed: int | None = None
        if exclusion_reason is None:
            duration_days = float((exposure_end - exposure_start).total_seconds() / 86_400)
            if duration_days < 0:
                exclusion_reason = "NEGATIVE_DURATION"
                duration_days = None
            else:
                event_observed = int(pd.notna(first_churn))

        endpoint = exposure_end if exclusion_reason is None else boundary
        baseline_episodes = account_episodes.loc[account_episodes["episode_start"].le(exposure_start)] if pd.notna(exposure_start) else account_episodes.iloc[0:0]
        observed_episodes = account_episodes.loc[account_episodes["episode_start"].le(endpoint)]
        active_at_baseline = baseline_episodes.loc[
            baseline_episodes["episode_end"].isna() | baseline_episodes["episode_end"].ge(exposure_start)
        ] if pd.notna(exposure_start) else baseline_episodes
        first_plan = baseline_episodes.iloc[0]["plan"] if len(baseline_episodes) else None
        baseline_mrr = float(baseline_episodes.iloc[0]["mrr"]) if len(baseline_episodes) and pd.notna(baseline_episodes.iloc[0]["mrr"]) else None
        latest_plan = observed_episodes.iloc[-1]["plan"] if len(observed_episodes) else first_plan

        if pd.notna(exposure_start):
            behavior_end = min(exposure_start + pd.Timedelta(days=30), endpoint)
            behavior = account.loc[account["event_time"].between(exposure_start, behavior_end, inclusive="both")]
        else:
            behavior = account.iloc[0:0]
        usage = behavior.loc[behavior["event_type"].eq("FEATURE_USED")]
        support = behavior.loc[behavior["event_type"].eq("SUPPORT_TICKET_OPENED")]
        used_until_endpoint = account.loc[account["event_time"].le(endpoint)]
        feature_row = account_lookup.loc[account_id]
        quality_ratio = pd.to_numeric(pd.Series([feature_row.get("quality_coverage_ratio")]), errors="coerce").iloc[0]
        rows.append(
            {
                "account_id": account_id,
                "exposure_start": exposure_start,
                "exposure_end": exposure_end if exclusion_reason is None else pd.NaT,
                "duration_days": duration_days,
                "event_observed": event_observed,
                "censoring_status": "EXCLUDED" if exclusion_reason else ("EVENT_OBSERVED" if event_observed else "RIGHT_CENSORED"),
                "first_churn_time": first_churn,
                "observation_end": boundary,
                "primary_outcome": "FIRST_CHURN_OBSERVED" if event_observed == 1 else ("RIGHT_CENSORED" if exclusion_reason is None else "EXCLUDED"),
                "first_plan": first_plan,
                "latest_plan": latest_plan,
                "baseline_mrr": baseline_mrr,
                "mrr_band": _numeric_band(baseline_mrr, "mrr"),
                "initial_usage_band": _numeric_band(len(usage), "count"),
                "support_band": _numeric_band(len(support), "count"),
                "subscription_count_band": _subscription_band(len(baseline_episodes)),
                "has_subscription_overlap": bool(len(active_at_baseline) > 1),
                "quality_population": _quality_label(used_until_endpoint) if len(used_until_endpoint) else "NO_USABLE_EVENTS",
                "quality_coverage_ratio": None if pd.isna(quality_ratio) else float(quality_ratio),
                "same_day_event": bool(event_observed == 1 and duration_days == 0),
                "exclusion_reason": exclusion_reason,
                "is_eligible": exclusion_reason is None,
                "time_origin": "FIRST_SUBSCRIPTION_START" if origin == "subscription" else "ACCOUNT_SIGNUP_TIME",
                "pre_exposure_churn_count": pre_exposure_churn_count,
                "behavior_window_days": 30,
                "behavior_group_use": "LANDMARK_ONLY",
            }
        )

    result = pd.DataFrame(rows).sort_values("account_id").reset_index(drop=True)
    result["event_observed"] = result["event_observed"].astype("Int64")
    if len(result) > 500 or result["account_id"].duplicated().any():
        raise AssertionError("Survival dataset violates the governed account grain.")
    eligible = result.loc[result["is_eligible"]]
    if eligible["duration_days"].lt(0).any() or not eligible["event_observed"].isin([0, 1]).all():
        raise AssertionError("Invalid duration or endpoint coding in the eligible population.")
    if not FORBIDDEN_COLUMNS.isdisjoint(result.columns):
        raise AssertionError("A prohibited privacy or leakage field entered the survival dataset.")
    return result


def build_landmark_dataset(
    survival_dataset: pd.DataFrame,
    events: pd.DataFrame,
    episodes: pd.DataFrame,
    raw_support: pd.DataFrame,
    landmark_days: int,
    *,
    strict: bool = False,
) -> LandmarkBuild:
    """Build a fixed-window landmark cohort without post-landmark features."""

    if landmark_days not in {30, 60, 90}:
        raise ValueError("Authorized landmarks are 30, 60 and 90 days.")
    active = usable_events(events, strict=strict)
    authorized_subscriptions = set(
        active.loc[active["event_type"].eq("SUBSCRIPTION_STARTED"), "subscription_id"].dropna().astype(str)
    )
    episode_work = episodes.loc[episodes["subscription_id"].astype(str).isin(authorized_subscriptions)].copy()
    for column in ("account_id", "subscription_id", "plan"):
        episode_work[column] = episode_work[column].astype("object")
    episode_work["episode_start"] = pd.to_datetime(episode_work["episode_start"], errors="coerce")
    episode_work["episode_end"] = pd.to_datetime(episode_work["episode_end"], errors="coerce")
    support = raw_support[["ticket_id", "resolution_time_hours"]].copy()
    support["resolution_time_hours"] = pd.to_numeric(support["resolution_time_hours"], errors="coerce")
    resolution_map = support.drop_duplicates("ticket_id").set_index("ticket_id")["resolution_time_hours"].to_dict()
    event_groups = {str(key): value for key, value in active.groupby("account_id", sort=False)}
    episode_groups = {str(key): value for key, value in episode_work.groupby("account_id", sort=False)}
    rows: list[dict[str, Any]] = []
    accounting = {
        "source_accounts": int(len(survival_dataset)),
        "ineligible_at_origin": 0,
        "churn_before_or_on_landmark": 0,
        "not_observable_to_landmark": 0,
        "included": 0,
    }

    for row in survival_dataset.itertuples(index=False):
        if not bool(row.is_eligible):
            accounting["ineligible_at_origin"] += 1
            continue
        exposure = pd.Timestamp(row.exposure_start)
        landmark_time = exposure + pd.Timedelta(days=landmark_days)
        if int(row.event_observed) == 1 and pd.Timestamp(row.first_churn_time) <= landmark_time:
            accounting["churn_before_or_on_landmark"] += 1
            continue
        if pd.Timestamp(row.observation_end) < landmark_time:
            accounting["not_observable_to_landmark"] += 1
            continue
        account_id = str(row.account_id)
        account = event_groups.get(account_id, active.iloc[0:0])
        window = account.loc[account["event_time"].between(exposure, landmark_time, inclusive="both")]
        usage = window.loc[window["event_type"].eq("FEATURE_USED")]
        support_open = window.loc[window["event_type"].eq("SUPPORT_TICKET_OPENED")]
        support_closed = window.loc[window["event_type"].eq("SUPPORT_TICKET_CLOSED")]
        resolutions = support_closed["source_record_id"].astype(str).map(resolution_map).dropna()
        satisfaction = pd.to_numeric(support_closed["event_value_numeric"], errors="coerce").dropna()
        account_episodes = episode_groups.get(account_id, episode_work.iloc[0:0])
        started = account_episodes.loc[account_episodes["episode_start"].le(landmark_time)]
        active_at_landmark = started.loc[started["episode_end"].isna() | started["episode_end"].gt(landmark_time)]
        endpoint = pd.Timestamp(row.exposure_end)
        duration_after = float((endpoint - landmark_time).total_seconds() / 86_400)
        rows.append(
            {
                "account_id": account_id,
                "landmark_days": landmark_days,
                "landmark_time": landmark_time,
                "duration_after_landmark": duration_after,
                "event_observed_after_landmark": int(row.event_observed),
                "usage_count_landmark": float(pd.to_numeric(usage["event_value_numeric"], errors="coerce").fillna(0).sum()),
                "active_days_landmark": int(usage["event_time"].dt.normalize().nunique()),
                "distinct_features_landmark": int(usage["event_value_category"].nunique()),
                "support_count_landmark": int(len(support_open)),
                "mean_resolution_hours_landmark": float(resolutions.mean()) if len(resolutions) else None,
                "satisfaction_mean_landmark": float(satisfaction.mean()) if len(satisfaction) else None,
                "mrr_at_landmark": float(active_at_landmark["mrr"].fillna(0).sum()),
                "subscription_count_at_landmark": int(len(started)),
                "quality_population": _quality_label(window) if len(window) else "VALID_ONLY",
                "usage_band_landmark": _numeric_band(len(usage), "count"),
                "support_band_landmark": _numeric_band(len(support_open), "count"),
            }
        )
        accounting["included"] += 1

    result = pd.DataFrame(rows).sort_values("account_id").reset_index(drop=True)
    if len(result) and (result["duration_after_landmark"].lt(0).any() or result["account_id"].duplicated().any()):
        raise AssertionError("Landmark output violates duration or grain rules.")
    if not FORBIDDEN_COLUMNS.isdisjoint(result.columns):
        raise AssertionError("A prohibited field entered a landmark dataset.")
    if sum(accounting[key] for key in accounting if key != "source_accounts") != accounting["source_accounts"]:
        raise AssertionError("Landmark population accounting does not reconcile.")
    return LandmarkBuild(result, accounting)
