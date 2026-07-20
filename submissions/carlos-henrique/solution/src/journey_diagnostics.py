"""Aggregate descriptive journeys without sequence mining or graph inference."""

from __future__ import annotations

from collections import Counter
from itertools import groupby
from typing import Any, Iterable

import pandas as pd

from churn_diagnostics import usable_events


MAX_SEQUENCE_LENGTH = 12


def collapse_consecutive(event_types: Iterable[str], limit: int = MAX_SEQUENCE_LENGTH) -> tuple[str, ...]:
    """Collapse consecutive duplicates while preserving deterministic order."""

    return tuple(key for key, _ in groupby(event_types))[:limit]


def _rank(sequences: list[tuple[str, ...]], denominator: int, top_n: int = 10) -> list[dict[str, Any]]:
    counts = Counter(sequences)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], " > ".join(item[0])))[:top_n]
    return [
        {
            "sequence": list(sequence),
            "account_support": int(count),
            "relative_support": float(count / denominator) if denominator else None,
            "denominator_accounts": int(denominator),
        }
        for sequence, count in ordered
    ]


def _ordered(group: pd.DataFrame) -> pd.DataFrame:
    return group.sort_values(["event_time", "event_order_on_same_day", "event_id"])


def build_journey_summary(events: pd.DataFrame, strict: bool = False) -> dict[str, Any]:
    """Build full, pre-churn, churn-reactivation and post-reactivation summaries."""

    active = usable_events(events, strict=strict)
    full: list[tuple[str, ...]] = []
    pre_churn: list[tuple[str, ...]] = []
    between: list[tuple[str, ...]] = []
    after: list[tuple[str, ...]] = []
    full_denominator = pre_denominator = between_denominator = after_denominator = 0
    for _, group in active.groupby("account_id", sort=True):
        group = _ordered(group)
        full_sequence = collapse_consecutive(group["event_type"].astype(str))
        if full_sequence:
            full.append(full_sequence)
            full_denominator += 1
        churn_times = list(group.loc[group["event_type"].eq("CHURN_RECORDED"), "event_time"])
        react_times = list(group.loc[group["event_type"].eq("REACTIVATION_RECORDED"), "event_time"])
        if churn_times:
            prefix = group.loc[group["event_time"].le(churn_times[0])]
            sequence = collapse_consecutive(prefix["event_type"].astype(str))
            if sequence:
                pre_churn.append(sequence)
                pre_denominator += 1
        valid_pair = next(
            ((c, r) for c in churn_times for r in react_times if r > c),
            None,
        )
        if valid_pair:
            churn_time, react_time = valid_pair
            interval = group.loc[group["event_time"].between(churn_time, react_time, inclusive="both")]
            sequence = collapse_consecutive(interval["event_type"].astype(str))
            if sequence:
                between.append(sequence)
                between_denominator += 1
            post = group.loc[group["event_time"].ge(react_time)]
            post_sequence = collapse_consecutive(post["event_type"].astype(str))
            if post_sequence:
                after.append(post_sequence)
                after_denominator += 1
    return {
        "methodology": "Consecutive duplicates collapsed; stable event ordering; maximum length 12; no formal sequence mining.",
        "population": "VALID only" if strict else "VALID + VALID_WITH_WARNING; quarantine excluded",
        "same_day_limitation": "Technical ordering is deterministic but not causal or intraday evidence.",
        "top_complete_journeys": _rank(full, full_denominator),
        "top_pre_first_churn_prefixes": _rank(pre_churn, pre_denominator),
        "top_churn_to_reactivation_sequences": _rank(between, between_denominator),
        "top_post_reactivation_sequences": _rank(after, after_denominator),
        "denominators": {
            "complete_accounts": full_denominator,
            "accounts_with_first_churn": pre_denominator,
            "accounts_with_churn_reactivation_pair": between_denominator,
            "accounts_with_post_reactivation_sequence": after_denominator,
        },
        "limitations": [
            "Sequences are descriptive aggregates, not causal patterns.",
            "Length truncation may hide later events in high-activity accounts.",
            "Warning sensitivity is reported separately.",
        ],
    }
