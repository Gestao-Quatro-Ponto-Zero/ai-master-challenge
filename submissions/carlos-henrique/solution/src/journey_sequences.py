"""Governed account journey construction and temporal scope controls."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pandas as pd

from churn_diagnostics import classify_account_outcomes


AUTHORIZED_EVENTS = (
    "ACCOUNT_CREATED",
    "SUBSCRIPTION_STARTED",
    "SUBSCRIPTION_ENDED",
    "FEATURE_USED",
    "SUPPORT_TICKET_OPENED",
    "SUPPORT_TICKET_CLOSED",
    "CHURN_RECORDED",
    "REACTIVATION_RECORDED",
)
REDUCED_EVENT_MAP = {
    "ACCOUNT_CREATED": "ACCOUNT",
    "SUBSCRIPTION_STARTED": "SUBSCRIPTION_START",
    "SUBSCRIPTION_ENDED": "SUBSCRIPTION_END",
    "FEATURE_USED": "FEATURE",
    "SUPPORT_TICKET_OPENED": "SUPPORT_OPEN",
    "SUPPORT_TICKET_CLOSED": "SUPPORT_CLOSE",
    "CHURN_RECORDED": "CHURN",
    "REACTIVATION_RECORDED": "REACTIVATION",
}
LANDMARKS = (30, 60, 90)


@dataclass(frozen=True)
class JourneyBuild:
    dataset: pd.DataFrame
    records: list[dict[str, Any]]
    accounting: dict[str, Any]


def usable_events(events: pd.DataFrame, strict: bool = False) -> pd.DataFrame:
    statuses = {"VALID"} if strict else {"VALID", "VALID_WITH_WARNING"}
    required = {
        "event_id", "account_id", "event_time", "event_type", "event_order_on_same_day",
        "quality_status", "is_quarantined",
    }
    if not required.issubset(events.columns):
        raise ValueError(f"Event log is missing: {sorted(required - set(events.columns))}")
    result = events.loc[
        events["quality_status"].isin(statuses)
        & ~events["is_quarantined"].astype(bool)
        & events["event_type"].isin(AUTHORIZED_EVENTS)
    ].copy()
    for column in ("event_id", "account_id", "event_type", "quality_status"):
        result[column] = result[column].astype("object")
    result["event_time"] = pd.to_datetime(result["event_time"], errors="raise")
    return result.sort_values(
        ["account_id", "event_time", "event_order_on_same_day", "event_id"]
    ).reset_index(drop=True)


def collapse_consecutive(tokens: list[str], dates: list[pd.Timestamp]) -> tuple[list[str], list[pd.Timestamp]]:
    collapsed_tokens: list[str] = []
    collapsed_dates: list[pd.Timestamp] = []
    for token, date in zip(tokens, dates):
        if not collapsed_tokens or token != collapsed_tokens[-1]:
            collapsed_tokens.append(token)
            collapsed_dates.append(pd.Timestamp(date))
    return collapsed_tokens, collapsed_dates


def same_day_dependency(tokens: list[str], dates: list[pd.Timestamp]) -> str:
    if len(tokens) < 2:
        return "NONE"
    relevant = sum(
        left.normalize() == right.normalize() and source != target
        for source, target, left, right in zip(tokens, tokens[1:], dates, dates[1:])
    )
    if relevant == 0:
        return "NONE"
    return "HIGH" if relevant >= 2 and relevant / (len(tokens) - 1) >= 0.5 else "PARTIAL"


def _time_buckets(tokens: list[str], dates: list[pd.Timestamp]) -> list[dict[str, Any]]:
    rows = pd.DataFrame({"token": tokens, "date": [value.normalize() for value in dates]})
    output: list[dict[str, Any]] = []
    for date, group in rows.groupby("date", sort=True):
        counts = group["token"].value_counts().sort_index()
        output.append(
            {
                "date": pd.Timestamp(date).date().isoformat(),
                "events": [
                    {"event": str(event), "count": int(count)}
                    for event, count in counts.items()
                ],
            }
        )
    return output


def _record(
    account_id: str,
    scope: str,
    quality_population: str,
    frame: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    outcome: str,
    quality_coverage_ratio: float | None,
    interval_count: int = 1,
) -> dict[str, Any] | None:
    selected = frame.loc[frame["event_time"].between(start, end, inclusive="both")].copy()
    if selected.empty:
        return None
    raw_types = selected["event_type"].astype(str).tolist()
    reduced = [REDUCED_EVENT_MAP[value] for value in raw_types]
    dates = [pd.Timestamp(value) for value in selected["event_time"]]
    collapsed, collapsed_dates = collapse_consecutive(reduced, dates)
    dependency = same_day_dependency(collapsed, collapsed_dates)
    raw_length = len(reduced)
    return {
        "account_id": account_id,
        "journey_scope": scope,
        "quality_population": quality_population,
        "journey_start": pd.Timestamp(start),
        "journey_end": pd.Timestamp(end),
        "outcome": outcome,
        "raw_sequence": json.dumps(raw_types, separators=(",", ":")),
        "collapsed_sequence": json.dumps(collapsed, separators=(",", ":")),
        "time_bucketed_sequence": json.dumps(_time_buckets(reduced, dates), separators=(",", ":"), sort_keys=True),
        "raw_length": raw_length,
        "collapsed_length": len(collapsed),
        "distinct_event_types": len(set(reduced)),
        "observed_days": max(int((pd.Timestamp(end).normalize() - pd.Timestamp(start).normalize()).days), 0),
        "repeated_event_ratio": float((raw_length - len(collapsed)) / raw_length),
        "same_day_order_dependency": dependency,
        "contains_churn": "CHURN" in collapsed,
        "contains_reactivation": "REACTIVATION" in collapsed,
        "churn_sequence_number": int(pd.to_numeric(selected.get("churn_sequence_number"), errors="coerce").max()) if "churn_sequence_number" in selected and pd.to_numeric(selected["churn_sequence_number"], errors="coerce").notna().any() else 0,
        "reactivation_sequence_number": int(pd.to_numeric(selected.get("reactivation_sequence_number"), errors="coerce").max()) if "reactivation_sequence_number" in selected and pd.to_numeric(selected["reactivation_sequence_number"], errors="coerce").notna().any() else 0,
        "quality_coverage_ratio": quality_coverage_ratio,
        "interval_count": interval_count,
        "source_event_count": raw_length,
        "source_contract": "EVENT_LOG_PHASE2_ACTIVE_ONLY",
        "_tokens": collapsed,
        "_dates": collapsed_dates,
        "_raw_tokens": reduced,
        "_raw_dates": dates,
    }


def _strict_outcomes(active: pd.DataFrame) -> dict[str, str]:
    outcomes = classify_account_outcomes(active)
    return dict(zip(outcomes["account_id"].astype(str), outcomes["primary_outcome"].astype(str)))


def build_account_journeys(
    events: pd.DataFrame,
    account_features: pd.DataFrame,
    *,
    strict: bool = False,
    observation_end: pd.Timestamp | str | None = None,
) -> JourneyBuild:
    """Build stable journey representations for all authorized scopes."""

    active = usable_events(events, strict=strict)
    boundary = pd.Timestamp(observation_end) if observation_end is not None else active["event_time"].max()
    quality_population = "STRICT" if strict else "MAIN"
    feature_work = account_features.copy()
    feature_work["account_id"] = feature_work["account_id"].astype(str)
    quality = feature_work.set_index("account_id")["quality_coverage_ratio"].to_dict()
    outcomes = _strict_outcomes(active) if strict else feature_work.set_index("account_id")["primary_outcome"].astype(str).to_dict()
    groups = {str(key): value for key, value in active.groupby("account_id", sort=False)}
    records: list[dict[str, Any]] = []
    empty_scopes: dict[str, int] = {}

    def add(account_id: str, scope: str, frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp, interval_count: int = 1) -> None:
        record = _record(
            account_id, scope, quality_population, frame, start, end,
            outcomes.get(account_id, "NO_CHURN_OBSERVED"),
            None if pd.isna(quality.get(account_id)) else float(quality[account_id]),
            interval_count,
        )
        if record is None:
            empty_scopes[scope] = empty_scopes.get(scope, 0) + 1
        else:
            records.append(record)

    for account_id in sorted(groups):
        frame = groups[account_id]
        start = pd.Timestamp(frame["event_time"].min())
        add(account_id, "FULL_OBSERVED_JOURNEY", frame, start, boundary)
        churns = frame.loc[frame["event_type"].eq("CHURN_RECORDED"), "event_time"].tolist()
        reactivations = frame.loc[frame["event_type"].eq("REACTIVATION_RECORDED"), "event_time"].tolist()
        subscriptions = frame.loc[frame["event_type"].eq("SUBSCRIPTION_STARTED"), "event_time"].tolist()
        if churns:
            add(account_id, "PRE_FIRST_CHURN", frame, start, pd.Timestamp(churns[0]))
        if len(churns) >= 2:
            add(
                account_id, "BETWEEN_RECURRING_CHURNS", frame,
                pd.Timestamp(churns[0]), pd.Timestamp(churns[-1]), len(churns) - 1,
            )
        pair: tuple[pd.Timestamp, pd.Timestamp] | None = None
        for churn in churns:
            later = [pd.Timestamp(value) for value in reactivations if pd.Timestamp(value) > pd.Timestamp(churn)]
            if later:
                pair = (pd.Timestamp(churn), min(later))
                break
        if pair is not None:
            add(account_id, "BETWEEN_CHURN_AND_REACTIVATION", frame, pair[0], pair[1])
        if reactivations:
            reactivation = pd.Timestamp(reactivations[0])
            later_churns = [pd.Timestamp(value) for value in churns if pd.Timestamp(value) > reactivation]
            post_end = min(later_churns) if later_churns else boundary
            add(account_id, "POST_REACTIVATION", frame, reactivation, post_end)
        if subscriptions:
            subscription_start = pd.Timestamp(subscriptions[0])
            for landmark in LANDMARKS:
                landmark_end = subscription_start + pd.Timedelta(days=landmark)
                if landmark_end <= boundary:
                    add(account_id, f"LANDMARK_{landmark}D_JOURNEY", frame, subscription_start, landmark_end)

    if not records:
        raise ValueError("No non-empty journeys were produced.")
    public_columns = [key for key in records[0] if not key.startswith("_")]
    dataset = pd.DataFrame([{key: row[key] for key in public_columns} for row in records])
    dataset = dataset.sort_values(["account_id", "journey_scope", "quality_population"]).reset_index(drop=True)
    key = ["account_id", "journey_scope", "quality_population"]
    if dataset.duplicated(key).any():
        raise AssertionError("Journey grain is not unique.")
    if dataset["raw_length"].le(0).any():
        raise AssertionError("Empty journeys cannot enter the analytical dataset.")
    forbidden = {"account_name", "feedback_text", "churn_flag"}
    if not forbidden.isdisjoint(dataset.columns):
        raise AssertionError("A privacy or leakage field entered account journeys.")
    return JourneyBuild(
        dataset=dataset,
        records=records,
        accounting={
            "population": quality_population,
            "accounts_with_usable_events": len(groups),
            "journey_rows": len(dataset),
            "rows_by_scope": dataset["journey_scope"].value_counts().sort_index().to_dict(),
            "empty_scopes_not_silently_discarded": empty_scopes,
            "quarantined_events_used": 0,
            "observation_end": boundary.isoformat(),
        },
    )


def assign_length_bands(
    dataset: pd.DataFrame, thresholds: tuple[float, float] | None = None
) -> tuple[pd.DataFrame, tuple[float, float]]:
    result = dataset.copy()
    reference = result.loc[
        result["journey_scope"].eq("FULL_OBSERVED_JOURNEY")
        & result["quality_population"].eq("MAIN"), "raw_length"
    ]
    if thresholds is None:
        thresholds = (float(reference.quantile(1 / 3)), float(reference.quantile(2 / 3)))
    low, high = thresholds
    result["journey_length_band"] = pd.cut(
        result["raw_length"], bins=[-1, low, high, float("inf")],
        labels=["SHORT_JOURNEY", "MEDIUM_JOURNEY", "LONG_JOURNEY"], include_lowest=True,
    ).astype("object")
    return result, thresholds
