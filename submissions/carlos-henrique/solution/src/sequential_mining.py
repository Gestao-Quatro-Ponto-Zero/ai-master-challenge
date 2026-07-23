"""Small, deterministic frequent-subsequence miner with governed gaps."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Iterable

import pandas as pd


MIN_SUPPORT_ACCOUNTS = 15
MAX_PATTERN_LENGTH = 5
MAX_GAP_EVENTS = 5
MAX_GAP_DAYS = 90


def _valid_indices(
    tokens: list[str], dates: list[pd.Timestamp], length: int,
    max_gap_events: int, max_gap_days: int,
) -> Iterable[tuple[int, ...]]:
    def extend(prefix: tuple[int, ...]) -> Iterable[tuple[int, ...]]:
        if len(prefix) == length:
            yield prefix
            return
        start = 0 if not prefix else prefix[-1] + 1
        stop = len(tokens) if not prefix else min(len(tokens), prefix[-1] + max_gap_events + 2)
        for index in range(start, stop):
            if prefix and (pd.Timestamp(dates[index]) - pd.Timestamp(dates[prefix[-1]])).days > max_gap_days:
                continue
            yield from extend(prefix + (index,))
    yield from extend(())


def account_subsequences(
    tokens: list[str], dates: list[pd.Timestamp], *, max_pattern_length: int = MAX_PATTERN_LENGTH,
    max_gap_events: int = MAX_GAP_EVENTS, max_gap_days: int = MAX_GAP_DAYS,
) -> set[tuple[str, ...]]:
    """Return unique governed subsequences for one account (length >= 2)."""
    found: set[tuple[str, ...]] = set()
    for length in range(2, min(max_pattern_length, len(tokens)) + 1):
        for indices in _valid_indices(tokens, dates, length, max_gap_events, max_gap_days):
            found.add(tuple(tokens[index] for index in indices))
    return found


def _proper_subsequences(pattern: tuple[str, ...]) -> set[tuple[str, ...]]:
    return {
        tuple(pattern[index] for index in indices)
        for size in range(2, len(pattern))
        for indices in combinations(range(len(pattern)), size)
    }


def mine_frequent_sequences(
    sequences: dict[str, tuple[list[str], list[pd.Timestamp]]], *,
    min_support_accounts: int = MIN_SUPPORT_ACCOUNTS,
    max_pattern_length: int = MAX_PATTERN_LENGTH,
    max_gap_events: int = MAX_GAP_EVENTS,
    max_gap_days: int = MAX_GAP_DAYS,
    closed_patterns_only: bool = True,
) -> dict[str, object]:
    """Mine account-supported patterns and prune non-closed candidates."""
    supporters: dict[tuple[str, ...], set[str]] = defaultdict(set)
    for account_id in sorted(sequences):
        tokens, dates = sequences[account_id]
        for pattern in account_subsequences(
            tokens, dates, max_pattern_length=max_pattern_length,
            max_gap_events=max_gap_events, max_gap_days=max_gap_days,
        ):
            supporters[pattern].add(account_id)
    frequent = {pattern: ids for pattern, ids in supporters.items() if len(ids) >= min_support_accounts}
    before = len(frequent)
    non_closed: set[tuple[str, ...]] = set()
    if closed_patterns_only:
        for superpattern, ids in frequent.items():
            for smaller in _proper_subsequences(superpattern):
                if smaller in frequent and frequent[smaller] == ids:
                    non_closed.add(smaller)
    kept = {pattern: ids for pattern, ids in frequent.items() if pattern not in non_closed}
    denominator = len(sequences)
    patterns = []
    for pattern, ids in sorted(kept.items(), key=lambda item: (-len(item[1]), -len(item[0]), item[0])):
        generic = len(set(pattern)) == 1 or all(token == "FEATURE" for token in pattern)
        patterns.append({
            "pattern": list(pattern),
            "pattern_label": " -> ".join(pattern),
            "length": len(pattern),
            "account_support": len(ids),
            "denominator_accounts": denominator,
            "relative_support": len(ids) / denominator if denominator else None,
            "coverage": len(ids) / denominator if denominator else None,
            "confidence": len(ids) / denominator if denominator else None,
            "lift": None,
            "leverage": None,
            "outcome_prevalence": None,
            "discriminative_ratio": None,
            "same_day_dependency": "PARTIAL",
            "is_generic": generic,
            "limitations": ["DESCRIPTIVE_NOT_CAUSAL", "NONCONTIGUOUS_ORDER_DEPENDENCY_CONSERVATIVELY_PARTIAL"] + (["GENERIC_PATTERN"] if generic else []),
        })
    return {
        "parameters": {
            "min_support_accounts": min_support_accounts,
            "max_pattern_length": max_pattern_length,
            "max_gap_events": max_gap_events,
            "max_gap_days": max_gap_days,
            "closed_patterns_only": closed_patterns_only,
        },
        "denominator_accounts": denominator,
        "patterns_before_pruning": before,
        "patterns_after_pruning": len(kept),
        "redundancy_removed": before - len(kept),
        "patterns": patterns,
    }


def annotate_population_stability(main: dict[str, object], strict: dict[str, object]) -> list[dict[str, object]]:
    strict_map = {tuple(row["pattern"]): row for row in strict["patterns"]}  # type: ignore[index]
    output = []
    for row in main["patterns"]:  # type: ignore[index]
        item = dict(row)
        other = strict_map.get(tuple(row["pattern"]))
        main_rate = row["relative_support"] or 0.0
        strict_rate = 0.0 if other is None else (other["relative_support"] or 0.0)
        ratio = strict_rate / main_rate if main_rate else None
        if other is not None and ratio is not None and 0.80 <= ratio <= 1.25:
            status = "ROBUST"
        elif other is not None and ratio is not None and 0.50 <= ratio <= 2.0:
            status = "SENSITIVE"
        else:
            status = "UNSTABLE"
        item.update({
            "principal_support": row["account_support"],
            "strict_support": 0 if other is None else other["account_support"],
            "principal_strict_ratio": ratio,
            "warning_dependency_ratio": None if main_rate == 0 else max(main_rate - strict_rate, 0) / main_rate,
            "stability_status": status,
        })
        output.append(item)
    return output
