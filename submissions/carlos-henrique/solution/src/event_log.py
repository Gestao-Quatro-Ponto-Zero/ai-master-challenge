"""Build the auditable RavenStack temporal event log and subscription episodes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from data_loader import load_all
from event_rules import (
    DERIVATION_SOURCE,
    QUALITY_QUARANTINED,
    event_id_for,
    event_order,
    episode_id_for,
)
from temporal_quality import (
    account_event_flags,
    add_post_churn_quality,
    add_same_day_quality,
    annotate_recurrence,
    annotate_usage_duplicates,
    churn_event_flags,
    finalize_quality,
    flag_counts,
    parse_timestamp,
    subscription_event_flags,
    ticket_event_flags,
    usage_event_flags,
)


SOLUTION_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROCESSED_DIR = SOLUTION_ROOT / "data" / "processed"

EVENT_COLUMNS = [
    "event_id",
    "account_id",
    "subscription_id",
    "event_time",
    "event_type",
    "event_subtype",
    "event_value_numeric",
    "event_value_category",
    "source_table",
    "source_record_id",
    "source_row_number",
    "derivation_type",
    "derivation_rule",
    "quality_status",
    "quality_flags",
    "is_quarantined",
    "is_post_churn",
    "is_pre_subscription",
    "is_post_subscription",
    "episode_id",
    "event_order_on_same_day",
    "candidate_subscription_id",
    "churn_assignment_status",
    "churn_sequence_number",
    "reactivation_sequence_number",
    "previous_churn_time",
    "next_churn_time",
    "days_since_previous_churn",
]

EPISODE_COLUMNS = [
    "episode_id",
    "account_id",
    "subscription_id",
    "episode_start",
    "episode_end",
    "episode_status",
    "plan",
    "mrr",
    "previous_subscription_id",
    "next_subscription_id",
    "is_post_churn_start",
    "has_churn_during_episode",
    "has_reactivation_during_episode",
    "has_overlap",
    "quality_status",
    "quality_flags",
]


@dataclass
class BuildResult:
    """All deterministic data products and reconciliation inputs from one build."""

    event_log: pd.DataFrame
    quarantined_events: pd.DataFrame
    subscription_episodes: pd.DataFrame
    reconciliation: dict[str, Any]
    temporal_quality: dict[str, Any]
    duplicate_summary: dict[str, Any]


def _safe_string(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    normalized = str(value).strip()
    return normalized or None


def _safe_float(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _source_rows(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Add physical CSV row provenance and split secondary exact duplicates."""

    work = frame.copy()
    original_columns = list(frame.columns)
    work["_source_row_number"] = np.arange(2, len(work) + 2, dtype="int64")
    duplicate_mask = work.duplicated(subset=original_columns, keep="first")
    return work.loc[~duplicate_mask].copy(), work.loc[duplicate_mask].copy()


def _account_signup_lookup(accounts: pd.DataFrame) -> dict[str, pd.Timestamp]:
    lookup: dict[str, pd.Timestamp] = {}
    for _, row in accounts.iterrows():
        account_id = _safe_string(row.get("account_id"))
        signup = parse_timestamp(row.get("signup_date"))
        if account_id is not None and not pd.isna(signup):
            lookup[account_id] = signup
    return lookup


def _subscription_lookup(subscriptions: pd.DataFrame) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    for _, row in subscriptions.iterrows():
        subscription_id = _safe_string(row.get("subscription_id"))
        if subscription_id is not None:
            lookup[subscription_id] = row.to_dict()
    return lookup


def _event(
    *,
    account_id: object,
    subscription_id: object,
    event_time: object,
    event_type: str,
    event_subtype: object,
    event_value_numeric: object,
    event_value_category: object,
    source_table: str,
    source_record_id: object,
    source_row_number: int,
    derivation_rule: str,
    quality_flags: Iterable[str],
    episode_id: object = None,
    candidate_subscription_id: object = None,
    churn_assignment_status: object = None,
) -> dict[str, object]:
    timestamp = parse_timestamp(event_time)
    flags = set(quality_flags)
    return {
        "event_id": event_id_for(
            source_table=source_table,
            source_record_id=source_record_id,
            source_row_number=source_row_number,
            event_type=event_type,
            event_time=timestamp,
        ),
        "account_id": _safe_string(account_id),
        "subscription_id": _safe_string(subscription_id),
        "event_time": timestamp,
        "event_type": event_type,
        "event_subtype": _safe_string(event_subtype),
        "event_value_numeric": _safe_float(event_value_numeric),
        "event_value_category": _safe_string(event_value_category),
        "source_table": source_table,
        "source_record_id": _safe_string(source_record_id),
        "source_row_number": int(source_row_number),
        "derivation_type": DERIVATION_SOURCE,
        "derivation_rule": derivation_rule,
        "quality_status": None,
        "quality_flags": None,
        "is_quarantined": False,
        "is_post_churn": False,
        "is_pre_subscription": "PRE_SUBSCRIPTION_USAGE" in flags,
        "is_post_subscription": "POST_SUBSCRIPTION_USAGE" in flags,
        "episode_id": _safe_string(episode_id),
        "event_order_on_same_day": event_order(event_type),
        "candidate_subscription_id": _safe_string(candidate_subscription_id),
        "churn_assignment_status": _safe_string(churn_assignment_status),
        "churn_sequence_number": pd.NA,
        "reactivation_sequence_number": pd.NA,
        "previous_churn_time": pd.NaT,
        "next_churn_time": pd.NaT,
        "days_since_previous_churn": pd.NA,
        "_quality_flags": flags,
    }


def build_subscription_episodes(
    subscriptions: pd.DataFrame,
    churn_events: pd.DataFrame,
) -> pd.DataFrame:
    """Create one episode per source subscription without automatic merging."""

    source_rows, _ = _source_rows(subscriptions)
    churn_copy = churn_events.copy()
    churn_copy["_time"] = pd.to_datetime(churn_copy["churn_date"], errors="coerce")
    churn_copy["_is_reactivation"] = churn_copy["is_reactivation"].fillna(False).astype(bool)
    episodes: list[dict[str, object]] = []

    for _, row in source_rows.iterrows():
        account_id = _safe_string(row.get("account_id"))
        subscription_id = _safe_string(row.get("subscription_id"))
        start = parse_timestamp(row.get("start_date"))
        end = parse_timestamp(row.get("end_date"))
        flags: set[str] = set()
        if account_id is None or subscription_id is None:
            flags.add("MISSING_REQUIRED_ID")
        if pd.isna(start):
            flags.add("INVALID_TIMESTAMP")
        if not pd.isna(start) and not pd.isna(end) and end < start:
            flags.add("END_BEFORE_START")

        account_churn = churn_copy.loc[
            churn_copy["account_id"].astype(str).eq(str(account_id))
            & churn_copy["_time"].notna()
        ]
        churn_only = account_churn.loc[~account_churn["_is_reactivation"]]
        reactivation_only = account_churn.loc[account_churn["_is_reactivation"]]
        first_churn = churn_only["_time"].min() if not churn_only.empty else pd.NaT
        is_post_churn_start = bool(
            not pd.isna(start) and not pd.isna(first_churn) and start > first_churn
        )
        interval_end = end if not pd.isna(end) else pd.Timestamp.max.normalize()
        has_churn = bool(
            not pd.isna(start)
            and churn_only["_time"].between(start, interval_end, inclusive="both").any()
        )
        has_reactivation = bool(
            not pd.isna(start)
            and reactivation_only["_time"].between(start, interval_end, inclusive="both").any()
        )
        if pd.isna(end) and (has_churn or is_post_churn_start):
            flags.add("OPEN_SUBSCRIPTION_AFTER_CHURN")

        episodes.append(
            {
                "episode_id": episode_id_for(account_id, subscription_id),
                "account_id": account_id,
                "subscription_id": subscription_id,
                "episode_start": start,
                "episode_end": end,
                "episode_status": "OPEN" if pd.isna(end) else "CLOSED",
                "plan": _safe_string(row.get("plan_tier")),
                "mrr": _safe_float(row.get("mrr_amount")),
                "previous_subscription_id": None,
                "next_subscription_id": None,
                "is_post_churn_start": is_post_churn_start,
                "has_churn_during_episode": has_churn,
                "has_reactivation_during_episode": has_reactivation,
                "has_overlap": False,
                "_quality_flags": flags,
            }
        )

    frame = pd.DataFrame(episodes)
    for _, group in frame.groupby("account_id", sort=False, dropna=False):
        ordered = group.sort_values(["episode_start", "subscription_id"], na_position="last")
        indexes = list(ordered.index)
        for position, index in enumerate(indexes):
            if position > 0:
                frame.at[index, "previous_subscription_id"] = frame.at[indexes[position - 1], "subscription_id"]
            if position + 1 < len(indexes):
                frame.at[index, "next_subscription_id"] = frame.at[indexes[position + 1], "subscription_id"]
        for left_position, left_index in enumerate(indexes):
            left_start = parse_timestamp(frame.at[left_index, "episode_start"])
            left_end = parse_timestamp(frame.at[left_index, "episode_end"])
            if pd.isna(left_start):
                continue
            left_boundary = left_end if not pd.isna(left_end) else pd.Timestamp.max.normalize()
            for right_index in indexes[left_position + 1 :]:
                right_start = parse_timestamp(frame.at[right_index, "episode_start"])
                right_end = parse_timestamp(frame.at[right_index, "episode_end"])
                if pd.isna(right_start):
                    continue
                right_boundary = right_end if not pd.isna(right_end) else pd.Timestamp.max.normalize()
                if left_start <= right_boundary and right_start <= left_boundary:
                    frame.at[left_index, "has_overlap"] = True
                    frame.at[right_index, "has_overlap"] = True
                    frame.at[left_index, "_quality_flags"].add("MULTIPLE_ACTIVE_SUBSCRIPTIONS")
                    frame.at[right_index, "_quality_flags"].add("MULTIPLE_ACTIVE_SUBSCRIPTIONS")

    frame["quality_flags"] = frame["_quality_flags"].map(
        lambda flags: "|".join(sorted(flags))
    )
    from event_rules import classify_quality  # local import avoids a wider public surface

    frame["quality_status"] = frame["_quality_flags"].map(classify_quality)
    frame = frame.drop(columns=["_quality_flags"])
    return frame[EPISODE_COLUMNS].sort_values(
        ["account_id", "episode_start", "subscription_id"], na_position="last"
    ).reset_index(drop=True)


def _generate_events(
    frames: Mapping[str, pd.DataFrame],
    episodes: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, dict[str, int]], dict[str, int]]:
    accounts, accounts_exact = _source_rows(frames["accounts"])
    subscriptions, subscriptions_exact = _source_rows(frames["subscriptions"])
    tickets, tickets_exact = _source_rows(frames["support_tickets"])
    churn, churn_exact = _source_rows(frames["churn_events"])
    usage, duplicate_summary = annotate_usage_duplicates(frames["feature_usage"])
    usage_exact = usage.loc[usage["_drop_exact_duplicate"]].copy()
    usage = usage.loc[~usage["_drop_exact_duplicate"]].copy()

    signup_lookup = _account_signup_lookup(accounts)
    subscription_lookup = _subscription_lookup(subscriptions)
    episode_lookup = episodes.set_index("subscription_id")["episode_id"].to_dict()
    records: list[dict[str, object]] = []

    for _, row in accounts.iterrows():
        flags = account_event_flags(row.get("account_id"), row.get("signup_date"), signup_lookup)
        records.append(
            _event(
                account_id=row.get("account_id"),
                subscription_id=None,
                event_time=row.get("signup_date"),
                event_type="ACCOUNT_CREATED",
                event_subtype="SOURCE_SIGNUP",
                event_value_numeric=None,
                event_value_category=None,
                source_table="accounts",
                source_record_id=row.get("account_id"),
                source_row_number=row["_source_row_number"],
                derivation_rule="accounts.signup_date -> ACCOUNT_CREATED",
                quality_flags=flags,
            )
        )

    for _, row in subscriptions.iterrows():
        subscription_id = row.get("subscription_id")
        episode_id = episode_lookup.get(str(subscription_id))
        start_flags = subscription_event_flags(
            account_id=row.get("account_id"),
            subscription_id=subscription_id,
            event_time=row.get("start_date"),
            start_time=row.get("start_date"),
            end_time=row.get("end_date"),
            event_type="SUBSCRIPTION_STARTED",
            account_signup=signup_lookup,
        )
        records.append(
            _event(
                account_id=row.get("account_id"),
                subscription_id=subscription_id,
                event_time=row.get("start_date"),
                event_type="SUBSCRIPTION_STARTED",
                event_subtype="SOURCE_START",
                event_value_numeric=row.get("mrr_amount"),
                event_value_category=row.get("plan_tier"),
                source_table="subscriptions",
                source_record_id=subscription_id,
                source_row_number=row["_source_row_number"],
                derivation_rule="subscriptions.start_date -> SUBSCRIPTION_STARTED",
                quality_flags=start_flags,
                episode_id=episode_id,
            )
        )
        if not pd.isna(row.get("end_date")):
            end_flags = subscription_event_flags(
                account_id=row.get("account_id"),
                subscription_id=subscription_id,
                event_time=row.get("end_date"),
                start_time=row.get("start_date"),
                end_time=row.get("end_date"),
                event_type="SUBSCRIPTION_ENDED",
                account_signup=signup_lookup,
            )
            records.append(
                _event(
                    account_id=row.get("account_id"),
                    subscription_id=subscription_id,
                    event_time=row.get("end_date"),
                    event_type="SUBSCRIPTION_ENDED",
                    event_subtype="SOURCE_END",
                    event_value_numeric=None,
                    event_value_category=row.get("plan_tier"),
                    source_table="subscriptions",
                    source_record_id=subscription_id,
                    source_row_number=row["_source_row_number"],
                    derivation_rule="non-null subscriptions.end_date -> SUBSCRIPTION_ENDED",
                    quality_flags=end_flags,
                    episode_id=episode_id,
                )
            )

    for _, row in usage.iterrows():
        subscription_id = _safe_string(row.get("subscription_id"))
        subscription = subscription_lookup.get(str(subscription_id))
        account_id = subscription.get("account_id") if subscription is not None else None
        flags = usage_event_flags(
            account_id=account_id,
            subscription_id=subscription_id,
            event_time=row.get("usage_date"),
            account_signup=signup_lookup,
            subscriptions_by_id=subscription_lookup,
        )
        flags.update(row["_duplicate_flags"])
        records.append(
            _event(
                account_id=account_id,
                subscription_id=subscription_id,
                event_time=row.get("usage_date"),
                event_type="FEATURE_USED",
                event_subtype="BETA" if bool(row.get("is_beta_feature")) else "STANDARD",
                event_value_numeric=row.get("usage_count"),
                event_value_category=row.get("feature_name"),
                source_table="feature_usage",
                source_record_id=row.get("usage_id"),
                source_row_number=row["_source_row_number"],
                derivation_rule="feature_usage.usage_date with account resolved by validated subscription FK",
                quality_flags=flags,
                episode_id=episode_lookup.get(str(subscription_id)),
            )
        )

    for _, row in tickets.iterrows():
        open_flags = ticket_event_flags(
            account_id=row.get("account_id"),
            event_time=row.get("submitted_at"),
            opened_time=row.get("submitted_at"),
            event_type="SUPPORT_TICKET_OPENED",
            account_signup=signup_lookup,
        )
        records.append(
            _event(
                account_id=row.get("account_id"),
                subscription_id=None,
                event_time=row.get("submitted_at"),
                event_type="SUPPORT_TICKET_OPENED",
                event_subtype=row.get("priority"),
                event_value_numeric=None,
                event_value_category=row.get("priority"),
                source_table="support_tickets",
                source_record_id=row.get("ticket_id"),
                source_row_number=row["_source_row_number"],
                derivation_rule="support_tickets.submitted_at -> SUPPORT_TICKET_OPENED",
                quality_flags=open_flags,
            )
        )
        if not pd.isna(row.get("closed_at")):
            close_flags = ticket_event_flags(
                account_id=row.get("account_id"),
                event_time=row.get("closed_at"),
                opened_time=row.get("submitted_at"),
                event_type="SUPPORT_TICKET_CLOSED",
                account_signup=signup_lookup,
            )
            escalation = "ESCALATED" if bool(row.get("escalation_flag")) else "NOT_ESCALATED"
            records.append(
                _event(
                    account_id=row.get("account_id"),
                    subscription_id=None,
                    event_time=row.get("closed_at"),
                    event_type="SUPPORT_TICKET_CLOSED",
                    event_subtype=escalation,
                    event_value_numeric=row.get("satisfaction_score"),
                    event_value_category=escalation,
                    source_table="support_tickets",
                    source_record_id=row.get("ticket_id"),
                    source_row_number=row["_source_row_number"],
                    derivation_rule="non-null support_tickets.closed_at -> SUPPORT_TICKET_CLOSED",
                    quality_flags=close_flags,
                )
            )

    for _, row in churn.iterrows():
        is_reactivation = bool(row.get("is_reactivation"))
        event_type = "REACTIVATION_RECORDED" if is_reactivation else "CHURN_RECORDED"
        flags, assignment = churn_event_flags(
            account_id=row.get("account_id"),
            event_time=row.get("churn_date"),
            event_type=event_type,
            account_signup=signup_lookup,
            subscriptions=subscriptions,
        )
        records.append(
            _event(
                account_id=row.get("account_id"),
                subscription_id=None,
                event_time=row.get("churn_date"),
                event_type=event_type,
                event_subtype="EXPLICIT_REACTIVATION" if is_reactivation else "EXPLICIT_CHURN",
                event_value_numeric=None,
                event_value_category=None,
                source_table="churn_events",
                source_record_id=row.get("churn_event_id"),
                source_row_number=row["_source_row_number"],
                derivation_rule="churn_events.is_reactivation selects explicit churn or reactivation event",
                quality_flags=flags,
                candidate_subscription_id=assignment.candidate_subscription_id,
                churn_assignment_status=assignment.status,
            )
        )

    events = pd.DataFrame(records)
    events = finalize_quality(events)
    events = annotate_recurrence(events)
    events = finalize_quality(events)
    events = add_post_churn_quality(events)
    events = add_same_day_quality(events)
    events = finalize_quality(events)

    exact_frames = {
        "accounts": accounts_exact,
        "subscriptions": subscriptions_exact,
        "feature_usage": usage_exact,
        "support_tickets": tickets_exact,
        "churn_events": churn_exact,
    }
    source_frames = {
        "accounts": frames["accounts"],
        "subscriptions": frames["subscriptions"],
        "feature_usage": frames["feature_usage"],
        "support_tickets": frames["support_tickets"],
        "churn_events": frames["churn_events"],
    }
    opportunities = {
        "accounts": len(frames["accounts"]),
        "subscriptions": len(frames["subscriptions"])
        + int(frames["subscriptions"]["end_date"].notna().sum()),
        "feature_usage": len(frames["feature_usage"]),
        "support_tickets": len(frames["support_tickets"])
        + int(frames["support_tickets"]["closed_at"].notna().sum()),
        "churn_events": len(frames["churn_events"]),
    }
    exact_opportunities = {
        "accounts": len(accounts_exact),
        "subscriptions": len(subscriptions_exact)
        + int(subscriptions_exact.get("end_date", pd.Series(dtype=object)).notna().sum()),
        "feature_usage": len(usage_exact),
        "support_tickets": len(tickets_exact)
        + int(tickets_exact.get("closed_at", pd.Series(dtype=object)).notna().sum()),
        "churn_events": len(churn_exact),
    }
    reconciliation_inputs: dict[str, dict[str, int]] = {}
    for source, source_frame in source_frames.items():
        source_events = events.loc[events["source_table"].eq(source)]
        active = int(source_events["quality_status"].ne(QUALITY_QUARANTINED).sum())
        quarantined = int(source_events["quality_status"].eq(QUALITY_QUARANTINED).sum())
        difference = opportunities[source] - active - quarantined - exact_opportunities[source]
        reconciliation_inputs[source] = {
            "source_records": int(len(source_frame)),
            "eligible_source_records": int(len(source_frame) - len(exact_frames[source])),
            "event_opportunities": int(opportunities[source]),
            "events_generated": int(len(source_events)),
            "active_events": active,
            "quarantined_events": quarantined,
            "records_without_applicable_event": 0,
            "exact_duplicate_rows_removed": int(len(exact_frames[source])),
            "exact_duplicate_event_opportunities_removed": int(exact_opportunities[source]),
            "unexplained_difference": int(difference),
        }
    return events, reconciliation_inputs, duplicate_summary


def _sort_events(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    for column in ("event_time", "previous_churn_time", "next_churn_time"):
        work[column] = pd.to_datetime(work[column], errors="coerce")
    for column in ("churn_sequence_number", "reactivation_sequence_number", "days_since_previous_churn"):
        work[column] = pd.to_numeric(work[column], errors="coerce").astype("Int64")
    work = work.sort_values(
        [
            "event_time",
            "account_id",
            "event_order_on_same_day",
            "source_table",
            "source_row_number",
            "event_id",
        ],
        na_position="last",
        kind="mergesort",
    )
    return work[EVENT_COLUMNS].reset_index(drop=True)


def _build_reconciliation(
    source_reconciliation: Mapping[str, Mapping[str, int]],
    events: pd.DataFrame,
) -> dict[str, Any]:
    active = events["quality_status"].ne(QUALITY_QUARANTINED)
    quarantined = events["quality_status"].eq(QUALITY_QUARANTINED)
    by_type = events.groupby("event_type").size().sort_index().astype(int).to_dict()
    by_source = events.groupby("source_table").size().sort_index().astype(int).to_dict()
    return {
        "reconciliation_basis": "event_opportunities; optional end/close fields create additional opportunities",
        "sources": dict(source_reconciliation),
        "totals": {
            "source_records": int(sum(item["source_records"] for item in source_reconciliation.values())),
            "event_opportunities": int(sum(item["event_opportunities"] for item in source_reconciliation.values())),
            "events_generated": int(len(events)),
            "valid_events": int(events["quality_status"].eq("VALID").sum()),
            "warning_events": int(events["quality_status"].eq("VALID_WITH_WARNING").sum()),
            "quarantined_events": int(quarantined.sum()),
            "exact_duplicate_rows_removed": int(sum(item["exact_duplicate_rows_removed"] for item in source_reconciliation.values())),
            "exact_duplicate_event_opportunities_removed": int(sum(item["exact_duplicate_event_opportunities_removed"] for item in source_reconciliation.values())),
            "unexplained_difference": int(sum(item["unexplained_difference"] for item in source_reconciliation.values())),
        },
        "events_by_type": {str(key): int(value) for key, value in by_type.items()},
        "events_by_source": {str(key): int(value) for key, value in by_source.items()},
        "distinct_accounts_with_events": int(events["account_id"].nunique(dropna=True)),
        "distinct_subscriptions_with_events": int(events["subscription_id"].nunique(dropna=True)),
        "active_event_count": int(active.sum()),
    }


def _temporal_summary(
    frames: Mapping[str, pd.DataFrame],
    events: pd.DataFrame,
    episodes: pd.DataFrame,
) -> dict[str, Any]:
    quality_counts = events["quality_status"].value_counts().sort_index().astype(int).to_dict()
    type_counts = events["event_type"].value_counts().sort_index().astype(int).to_dict()
    source_quality: dict[str, dict[str, int]] = {}
    for source, group in events.groupby("source_table", sort=True):
        source_quality[str(source)] = {
            str(key): int(value)
            for key, value in group["quality_status"].value_counts().sort_index().items()
        }

    churns = events.loc[events["event_type"].eq("CHURN_RECORDED")].copy()
    reactivations = events.loc[events["event_type"].eq("REACTIVATION_RECORDED")].copy()
    churn_per_account = churns.groupby("account_id").size()
    total_accounts = int(len(frames["accounts"]))
    reactivation_times = reactivations.groupby("account_id")["event_time"].apply(list).to_dict()
    churn_without_later_reactivation = 0
    for _, row in churns.iterrows():
        later = [
            time
            for time in reactivation_times.get(row["account_id"], [])
            if not pd.isna(time) and pd.Timestamp(time) > pd.Timestamp(row["event_time"])
        ]
        if not later:
            churn_without_later_reactivation += 1

    assignment_counts = (
        events.loc[events["source_table"].eq("churn_events"), "churn_assignment_status"]
        .fillna("NA")
        .value_counts()
        .sort_index()
        .astype(int)
        .to_dict()
    )
    affected = events["quality_status"].ne("VALID")
    return {
        "quality_status_counts": {str(key): int(value) for key, value in quality_counts.items()},
        "quality_flag_counts": flag_counts(events["quality_flags"]),
        "event_type_counts": {str(key): int(value) for key, value in type_counts.items()},
        "inconsistencies_by_source": source_quality,
        "affected_accounts": int(events.loc[affected, "account_id"].nunique(dropna=True)),
        "affected_subscriptions": int(events.loc[affected, "subscription_id"].nunique(dropna=True)),
        "churn_recurrence": {
            "accounts_without_churn": int(total_accounts - len(churn_per_account)),
            "accounts_with_one_churn": int(churn_per_account.eq(1).sum()),
            "accounts_with_multiple_churns": int(churn_per_account.gt(1).sum()),
            "maximum_churns_per_account": int(churn_per_account.max()) if not churn_per_account.empty else 0,
            "churn_events_without_subsequent_reactivation": int(churn_without_later_reactivation),
        },
        "reactivation": {
            "events": int(len(reactivations)),
            "accounts": int(reactivations["account_id"].nunique(dropna=True)),
            "without_prior_churn": int(
                events["quality_flags"].str.contains("REACTIVATION_WITHOUT_PRIOR_CHURN", regex=False).sum()
            ),
        },
        "churn_subscription_assignment": {str(key): int(value) for key, value in assignment_counts.items()},
        "pre_account_events": int(events["quality_flags"].str.contains("PRE_ACCOUNT_EVENT", regex=False).sum()),
        "pre_subscription_events": int(events["is_pre_subscription"].sum()),
        "post_subscription_events": int(events["is_post_subscription"].sum()),
        "post_churn_events": int(events["is_post_churn"].sum()),
        "episodes": {
            "total": int(len(episodes)),
            "open": int(episodes["episode_status"].eq("OPEN").sum()),
            "closed": int(episodes["episode_status"].eq("CLOSED").sum()),
            "overlapping": int(episodes["has_overlap"].sum()),
            "quality_status_counts": {
                str(key): int(value)
                for key, value in episodes["quality_status"].value_counts().sort_index().items()
            },
        },
    }


def build_event_log(frames: Mapping[str, pd.DataFrame] | None = None) -> BuildResult:
    """Build all Phase 2 temporal products in memory."""

    source_frames = dict(frames) if frames is not None else load_all()[0]
    episodes = build_subscription_episodes(
        source_frames["subscriptions"], source_frames["churn_events"]
    )
    events, source_reconciliation, duplicate_summary = _generate_events(source_frames, episodes)
    reconciliation = _build_reconciliation(source_reconciliation, events)
    temporal_quality = _temporal_summary(source_frames, events, episodes)
    active = _sort_events(events.loc[events["quality_status"].ne(QUALITY_QUARANTINED)])
    quarantined = _sort_events(events.loc[events["quality_status"].eq(QUALITY_QUARANTINED)])
    return BuildResult(
        event_log=active,
        quarantined_events=quarantined,
        subscription_episodes=episodes,
        reconciliation=reconciliation,
        temporal_quality=temporal_quality,
        duplicate_summary=duplicate_summary,
    )


def write_parquet_outputs(
    result: BuildResult,
    processed_dir: Path | str = DEFAULT_PROCESSED_DIR,
) -> dict[str, Path]:
    """Write deterministic, compressed Parquet outputs without an index."""

    destination = Path(processed_dir)
    destination.mkdir(parents=True, exist_ok=True)
    outputs = {
        "event_log": destination / "event_log.parquet",
        "quarantined_events": destination / "quarantined_events.parquet",
        "subscription_episodes": destination / "subscription_episodes.parquet",
    }
    result.event_log.to_parquet(outputs["event_log"], index=False, compression="zstd")
    result.quarantined_events.to_parquet(
        outputs["quarantined_events"], index=False, compression="zstd"
    )
    result.subscription_episodes.to_parquet(
        outputs["subscription_episodes"], index=False, compression="zstd"
    )
    return outputs
