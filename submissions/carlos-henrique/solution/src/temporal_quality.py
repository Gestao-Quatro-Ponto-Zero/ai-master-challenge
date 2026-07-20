"""Temporal validation and reconciliation helpers for the canonical event log."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from event_rules import (
    QUALITY_QUARANTINED,
    classify_quality,
    serialize_flags,
)


@dataclass(frozen=True)
class ChurnAssignment:
    """Conservative account-churn to subscription candidate result."""

    candidate_subscription_id: str | None
    status: str
    active_candidate_count: int


def parse_timestamp(value: object) -> pd.Timestamp | pd.NaT:
    """Parse a source timestamp to timezone-naive datetime64 semantics."""

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return pd.NaT
    timestamp = pd.Timestamp(parsed)
    if timestamp.tzinfo is not None:
        timestamp = timestamp.tz_localize(None)
    return timestamp


def missing_identifier(value: object) -> bool:
    """Return whether a required source identifier is missing or blank."""

    return value is None or pd.isna(value) or not str(value).strip()


def account_event_flags(
    account_id: object,
    event_time: object,
    account_signup: Mapping[str, pd.Timestamp],
) -> set[str]:
    """Validate required account identity, timestamp, and account precedence."""

    flags: set[str] = set()
    if missing_identifier(account_id):
        flags.add("MISSING_REQUIRED_ID")
    timestamp = parse_timestamp(event_time)
    if pd.isna(timestamp):
        flags.add("INVALID_TIMESTAMP")
        return flags
    signup = account_signup.get(str(account_id))
    if signup is None:
        flags.add("MISSING_REQUIRED_ID")
    elif timestamp < signup:
        flags.add("PRE_ACCOUNT_EVENT")
    return flags


def usage_event_flags(
    *,
    account_id: object,
    subscription_id: object,
    event_time: object,
    account_signup: Mapping[str, pd.Timestamp],
    subscriptions_by_id: Mapping[str, Mapping[str, object]],
) -> set[str]:
    """Validate a feature-usage record against its account and episode bounds."""

    flags = account_event_flags(account_id, event_time, account_signup)
    if missing_identifier(subscription_id):
        flags.add("MISSING_REQUIRED_ID")
        return flags
    subscription = subscriptions_by_id.get(str(subscription_id))
    if subscription is None:
        flags.add("MISSING_REQUIRED_ID")
        return flags
    timestamp = parse_timestamp(event_time)
    if pd.isna(timestamp):
        return flags
    start = parse_timestamp(subscription.get("start_date"))
    end = parse_timestamp(subscription.get("end_date"))
    if pd.isna(start):
        flags.add("INVALID_TIMESTAMP")
    elif timestamp < start:
        flags.add("PRE_SUBSCRIPTION_USAGE")
    if not pd.isna(end) and timestamp > end:
        flags.add("POST_SUBSCRIPTION_USAGE")
    return flags


def subscription_event_flags(
    *,
    account_id: object,
    subscription_id: object,
    event_time: object,
    start_time: object,
    end_time: object,
    event_type: str,
    account_signup: Mapping[str, pd.Timestamp],
) -> set[str]:
    """Validate subscription identity and chronology for start/end events."""

    flags = account_event_flags(account_id, event_time, account_signup)
    if missing_identifier(subscription_id):
        flags.add("MISSING_REQUIRED_ID")
    start = parse_timestamp(start_time)
    end = parse_timestamp(end_time)
    if event_type == "SUBSCRIPTION_STARTED" and pd.isna(start):
        flags.add("INVALID_TIMESTAMP")
    if event_type == "SUBSCRIPTION_ENDED":
        if pd.isna(end):
            flags.add("INVALID_TIMESTAMP")
        if not pd.isna(start) and not pd.isna(end) and end < start:
            flags.add("END_BEFORE_START")
    return flags


def ticket_event_flags(
    *,
    account_id: object,
    event_time: object,
    opened_time: object,
    event_type: str,
    account_signup: Mapping[str, pd.Timestamp],
) -> set[str]:
    """Validate support opening/closure chronology."""

    flags = account_event_flags(account_id, event_time, account_signup)
    event_timestamp = parse_timestamp(event_time)
    opened_timestamp = parse_timestamp(opened_time)
    if event_type == "SUPPORT_TICKET_CLOSED":
        if pd.isna(event_timestamp):
            flags.add("INVALID_TIMESTAMP")
        if not pd.isna(event_timestamp) and not pd.isna(opened_timestamp):
            if event_timestamp < opened_timestamp:
                flags.add("CLOSE_BEFORE_OPEN")
    return flags


def active_subscriptions_at(
    subscriptions: pd.DataFrame,
    account_id: object,
    event_time: object,
) -> pd.DataFrame:
    """Return subscriptions active at a timestamp without inventing linkage."""

    timestamp = parse_timestamp(event_time)
    if pd.isna(timestamp) or missing_identifier(account_id):
        return subscriptions.iloc[0:0].copy()
    account_rows = subscriptions.loc[
        subscriptions["account_id"].astype(str) == str(account_id)
    ].copy()
    starts = pd.to_datetime(account_rows["start_date"], errors="coerce")
    ends = pd.to_datetime(account_rows["end_date"], errors="coerce")
    mask = starts.le(timestamp) & (ends.isna() | ends.ge(timestamp))
    return account_rows.loc[mask]


def assign_churn_subscription(
    subscriptions: pd.DataFrame,
    account_id: object,
    event_time: object,
) -> ChurnAssignment:
    """Classify candidate attribution while avoiding false subscription links."""

    timestamp = parse_timestamp(event_time)
    active = active_subscriptions_at(subscriptions, account_id, timestamp)
    if len(active) == 1:
        return ChurnAssignment(str(active.iloc[0]["subscription_id"]), "EXACT_ACTIVE_MATCH", 1)
    if len(active) > 1:
        return ChurnAssignment(None, "MULTIPLE_ACTIVE_CANDIDATES", len(active))

    account_rows = subscriptions.loc[
        subscriptions["account_id"].astype(str) == str(account_id)
    ].copy()
    starts = pd.to_datetime(account_rows["start_date"], errors="coerce")
    prior = account_rows.loc[starts.le(timestamp)] if not pd.isna(timestamp) else account_rows.iloc[0:0]
    if len(prior) == 1:
        return ChurnAssignment(None, "SINGLE_PRIOR_SUBSCRIPTION", 0)
    if len(prior) == 0:
        return ChurnAssignment(None, "NO_ACTIVE_SUBSCRIPTION", 0)
    return ChurnAssignment(None, "AMBIGUOUS", 0)


def churn_event_flags(
    *,
    account_id: object,
    event_time: object,
    event_type: str,
    account_signup: Mapping[str, pd.Timestamp],
    subscriptions: pd.DataFrame,
) -> tuple[set[str], ChurnAssignment]:
    """Validate churn/reactivation context and return conservative attribution."""

    flags = account_event_flags(account_id, event_time, account_signup)
    assignment = assign_churn_subscription(subscriptions, account_id, event_time)
    timestamp = parse_timestamp(event_time)
    account_rows = subscriptions.loc[
        subscriptions["account_id"].astype(str) == str(account_id)
    ]
    starts = pd.to_datetime(account_rows["start_date"], errors="coerce")
    if not pd.isna(timestamp) and not starts.empty and timestamp < starts.min():
        flags.add("CHURN_BEFORE_FIRST_SUBSCRIPTION")
    if assignment.status in {"SINGLE_PRIOR_SUBSCRIPTION", "NO_ACTIVE_SUBSCRIPTION", "AMBIGUOUS"}:
        flags.add("CHURN_WITHOUT_ACTIVE_SUBSCRIPTION")
    if assignment.status in {"MULTIPLE_ACTIVE_CANDIDATES", "AMBIGUOUS"}:
        flags.add("AMBIGUOUS_CHURN_SUBSCRIPTION")
    if assignment.status == "MULTIPLE_ACTIVE_CANDIDATES":
        flags.add("MULTIPLE_ACTIVE_SUBSCRIPTIONS")
    if event_type == "REACTIVATION_RECORDED":
        # A prior churn is checked after all churn-source records are materialized.
        pass
    return flags, assignment


def annotate_usage_duplicates(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Preserve distinct duplicate IDs/keys and mark removable exact duplicates."""

    work = frame.copy()
    source_columns = list(frame.columns)
    work["_source_row_number"] = np.arange(2, len(work) + 2, dtype="int64")
    work["_drop_exact_duplicate"] = work.duplicated(subset=source_columns, keep="first")
    source_duplicate = work.duplicated(subset=["usage_id"], keep=False)
    candidate_duplicate = work.duplicated(
        subset=["subscription_id", "usage_date", "feature_name"], keep=False
    )
    duplicate_flags: list[set[str]] = []
    for position in range(len(work)):
        flags: set[str] = set()
        if bool(source_duplicate.iloc[position]):
            flags.add("DUPLICATE_SOURCE_ID")
        if bool(candidate_duplicate.iloc[position]):
            flags.add("DUPLICATE_CANDIDATE_KEY")
        if bool(work.iloc[position]["_drop_exact_duplicate"]):
            flags.add("EXACT_DUPLICATE")
        duplicate_flags.append(flags)
    work["_duplicate_flags"] = duplicate_flags
    summary = {
        "exact_duplicate_rows_removed": int(work["_drop_exact_duplicate"].sum()),
        "duplicate_source_id_rows": int(source_duplicate.sum()),
        "duplicate_candidate_key_rows": int(candidate_duplicate.sum()),
    }
    # Excess counts are computed explicitly to avoid conflating affected rows with duplicates.
    summary["duplicate_source_id_excess"] = int(
        work.duplicated(subset=["usage_id"], keep="first").sum()
    )
    summary["duplicate_candidate_key_excess"] = int(
        work.duplicated(
            subset=["subscription_id", "usage_date", "feature_name"], keep="first"
        ).sum()
    )
    return work, summary


def add_same_day_quality(events: pd.DataFrame) -> pd.DataFrame:
    """Mark events whose same-day sequence needs the documented technical tie-break."""

    work = events.copy()
    valid_times = pd.to_datetime(work["event_time"], errors="coerce")
    day_key = valid_times.dt.normalize()
    group_size = work.groupby([work["account_id"].astype(str), day_key])["event_id"].transform("size")
    for index in work.index[group_size.gt(1)]:
        work.at[index, "_quality_flags"].add("SAME_DAY_ORDER_ASSIGNED")
    return work


def annotate_recurrence(events: pd.DataFrame) -> pd.DataFrame:
    """Retain recurrent churn and explicit reactivation sequence metadata."""

    work = events.copy()
    for column in (
        "churn_sequence_number",
        "reactivation_sequence_number",
        "previous_churn_time",
        "next_churn_time",
        "days_since_previous_churn",
    ):
        work[column] = pd.NA

    churn_mask = work["event_type"].eq("CHURN_RECORDED")
    churn_rows = work.loc[churn_mask].sort_values(
        ["account_id", "event_time", "source_row_number", "event_id"]
    )
    for _, group in churn_rows.groupby("account_id", sort=False):
        ordered = list(group.index)
        times = [parse_timestamp(work.at[index, "event_time"]) for index in ordered]
        for sequence, index in enumerate(ordered, start=1):
            work.at[index, "churn_sequence_number"] = sequence
            if sequence > 1:
                work.at[index, "previous_churn_time"] = times[sequence - 2]
                work.at[index, "days_since_previous_churn"] = (
                    times[sequence - 1] - times[sequence - 2]
                ).days
            if sequence < len(ordered):
                work.at[index, "next_churn_time"] = times[sequence]

    reactivation_mask = work["event_type"].eq("REACTIVATION_RECORDED")
    reactivation_rows = work.loc[reactivation_mask].sort_values(
        ["account_id", "event_time", "source_row_number", "event_id"]
    )
    valid_churn = work.loc[churn_mask & work["quality_status"].ne(QUALITY_QUARANTINED)].copy()
    valid_churn["event_time"] = pd.to_datetime(valid_churn["event_time"], errors="coerce")
    for _, group in reactivation_rows.groupby("account_id", sort=False):
        for sequence, index in enumerate(group.index, start=1):
            work.at[index, "reactivation_sequence_number"] = sequence
            event_time = parse_timestamp(work.at[index, "event_time"])
            prior = valid_churn.loc[
                valid_churn["account_id"].astype(str).eq(str(work.at[index, "account_id"]))
                & valid_churn["event_time"].le(event_time)
            ]
            if prior.empty:
                work.at[index, "_quality_flags"].add("REACTIVATION_WITHOUT_PRIOR_CHURN")
            else:
                previous = pd.Timestamp(prior["event_time"].max())
                work.at[index, "previous_churn_time"] = previous
                work.at[index, "days_since_previous_churn"] = (event_time - previous).days
    return work


def add_post_churn_quality(events: pd.DataFrame) -> pd.DataFrame:
    """Mark events strictly after the first usable churn without claiming causality."""

    work = events.copy()
    work["is_post_churn"] = False
    churns = work.loc[
        work["event_type"].eq("CHURN_RECORDED")
        & work["quality_status"].ne(QUALITY_QUARANTINED)
    ].copy()
    churns["event_time"] = pd.to_datetime(churns["event_time"], errors="coerce")
    first_churn = churns.groupby(churns["account_id"].astype(str))["event_time"].min().to_dict()
    for index, row in work.iterrows():
        first = first_churn.get(str(row["account_id"]))
        timestamp = parse_timestamp(row["event_time"])
        if first is not None and not pd.isna(timestamp) and timestamp > first:
            work.at[index, "is_post_churn"] = True
            if row["event_type"] in {"SUPPORT_TICKET_OPENED", "SUPPORT_TICKET_CLOSED"}:
                work.at[index, "_quality_flags"].add("POST_CHURN_EVENT")
    return work


def finalize_quality(events: pd.DataFrame) -> pd.DataFrame:
    """Serialize flags and refresh canonical status/quarantine fields."""

    work = events.copy()
    work["quality_flags"] = work["_quality_flags"].map(serialize_flags)
    work["quality_status"] = work["_quality_flags"].map(classify_quality)
    work["is_quarantined"] = work["quality_status"].eq(QUALITY_QUARANTINED)
    return work


def flag_counts(serialized_flags: Iterable[str]) -> dict[str, int]:
    """Aggregate delimited flags without exposing record identifiers."""

    counter: Counter[str] = Counter()
    for value in serialized_flags:
        for flag in str(value).split("|"):
            if flag:
                counter[flag] += 1
    return dict(sorted(counter.items()))
