"""Governed transition, n-gram, prefix/suffix, and outcome comparisons."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable

import pandas as pd


MIN_ACCOUNT_SUPPORT = 10
MIN_RELATIVE_SUPPORT = 0.02
MIN_GROUP_SIZE = 20


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    return [tuple(tokens[index:index + n]) for index in range(max(len(tokens) - n + 1, 0))]


def _dependency(pattern: tuple[str, ...], tokens: list[str], dates: list[pd.Timestamp]) -> str:
    same_day = 0
    total = 0
    for index in range(len(tokens) - len(pattern) + 1):
        if tuple(tokens[index:index + len(pattern)]) != pattern:
            continue
        total += 1
        if any(
            pd.Timestamp(dates[pos]).normalize() == pd.Timestamp(dates[pos + 1]).normalize()
            for pos in range(index, index + len(pattern) - 1)
        ):
            same_day += 1
    if same_day == 0:
        return "NONE"
    return "HIGH" if total and same_day / total >= 0.5 else "PARTIAL"


def _group_records(records: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        grouped[(row["quality_population"], row["journey_scope"], row["outcome"])].append(row)
    return grouped


def transition_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped = _group_records(records)
    reference: dict[tuple[str, str, tuple[str, str]], float] = {}
    for population in ("MAIN", "STRICT"):
        scopes = sorted({row["journey_scope"] for row in records if row["quality_population"] == population})
        for scope in scopes:
            scoped = [row for row in records if row["quality_population"] == population and row["journey_scope"] == scope]
            support: Counter[tuple[str, str]] = Counter()
            for row in scoped:
                support.update(set(ngrams(row["_tokens"], 2)))
            for pattern, count in support.items():
                reference[(population, scope, pattern)] = count / len(scoped) if scoped else 0.0
    for (population, scope, outcome), group in sorted(grouped.items()):
        occurrences: Counter[tuple[str, str]] = Counter()
        supporters: Counter[tuple[str, str]] = Counter()
        source_counts: Counter[str] = Counter()
        dependencies: dict[tuple[str, str], set[str]] = defaultdict(set)
        for record in group:
            patterns = ngrams(record["_tokens"], 2)
            occurrences.update(patterns)
            supporters.update(set(patterns))
            source_counts.update(pattern[0] for pattern in patterns)
            for pattern in set(patterns):
                dependencies[pattern].add(_dependency(pattern, record["_tokens"], record["_dates"]))
        for pattern in sorted(occurrences):
            relative = supporters[pattern] / len(group)
            ref = reference.get((population, scope, pattern), 0.0)
            dep_set = dependencies[pattern]
            dependency = "HIGH" if "HIGH" in dep_set else ("PARTIAL" if "PARTIAL" in dep_set else "NONE")
            rows.append({
                "source_event": pattern[0], "target_event": pattern[1],
                "journey_scope": scope, "outcome": outcome, "quality_population": population,
                "account_support": supporters[pattern], "transition_count": occurrences[pattern],
                "denominator_accounts": len(group), "relative_support": relative,
                "source_conditional_probability": occurrences[pattern] / source_counts[pattern[0]] if source_counts[pattern[0]] else None,
                "lift_vs_population": relative / ref if ref else None,
                "same_day_dependency": dependency,
                "small_sample": len(group) < MIN_GROUP_SIZE or supporters[pattern] < MIN_ACCOUNT_SUPPORT,
                "limitations": ["DESCRIPTIVE_NOT_CAUSAL"] + (["SMALL_SAMPLE"] if len(group) < MIN_GROUP_SIZE else []),
            })
    return annotate_stability(rows, ("journey_scope", "outcome", "source_event", "target_event"))


def ngram_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (population, scope, outcome), group in sorted(_group_records(records).items()):
        for representation, sizes in (("COLLAPSED", range(2, 6)), ("RAW_BIGRAM_SENSITIVITY", (2,))):
            support: Counter[tuple[str, ...]] = Counter()
            occurrences: Counter[tuple[str, ...]] = Counter()
            dependency: dict[tuple[str, ...], set[str]] = defaultdict(set)
            for record in group:
                tokens = record["_tokens"] if representation == "COLLAPSED" else record["_raw_tokens"]
                dates = record["_dates"] if representation == "COLLAPSED" else record["_raw_dates"]
                for n in sizes:
                    pats = ngrams(tokens, n)
                    occurrences.update(pats)
                    support.update(set(pats))
                    for pat in set(pats):
                        dependency[pat].add(_dependency(pat, tokens, dates))
            for pattern in sorted(occurrences):
                rate = support[pattern] / len(group)
                dep_set = dependency[pattern]
                dep = "HIGH" if "HIGH" in dep_set else ("PARTIAL" if "PARTIAL" in dep_set else "NONE")
                rows.append({
                    "pattern": list(pattern), "pattern_label": " -> ".join(pattern), "n": len(pattern),
                    "representation": representation, "journey_scope": scope, "outcome": outcome,
                    "quality_population": population, "account_support": support[pattern],
                    "absolute_occurrences": occurrences[pattern], "denominator_accounts": len(group),
                    "relative_support": rate, "same_day_dependency": dep,
                    "small_sample": len(group) < MIN_GROUP_SIZE or support[pattern] < MIN_ACCOUNT_SUPPORT,
                    "passes_primary_filter": support[pattern] >= MIN_ACCOUNT_SUPPORT and rate >= MIN_RELATIVE_SUPPORT and len(group) >= MIN_GROUP_SIZE and dep != "HIGH",
                    "discriminative_ratio": None,
                    "limitations": ["DESCRIPTIVE_NOT_CAUSAL"] + (["ORDER_DEPENDENCY_HIGH"] if dep == "HIGH" else []),
                })
    return annotate_stability(rows, ("journey_scope", "outcome", "representation", "pattern_label"))


def annotate_stability(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    index = {tuple(row[key] for key in keys): row for row in rows if row["quality_population"] == "STRICT"}
    output = []
    for row in rows:
        if row["quality_population"] != "MAIN":
            continue
        item = dict(row)
        other = index.get(tuple(row[key] for key in keys))
        principal = int(row["account_support"])
        strict = 0 if other is None else int(other["account_support"])
        main_rate = float(row["relative_support"])
        strict_rate = 0.0 if other is None else float(other["relative_support"])
        ratio = strict_rate / main_rate if main_rate else None
        dependency = row.get("same_day_dependency", "NONE")
        if other and ratio is not None and 0.80 <= ratio <= 1.25 and dependency != "HIGH" and not row["small_sample"]:
            status = "ROBUST"
        elif other and ratio is not None and 0.50 <= ratio <= 2.0 and dependency != "HIGH":
            status = "SENSITIVE"
        else:
            status = "UNSTABLE"
        item.update({"principal_support": principal, "strict_support": strict, "strict_denominator_accounts": 0 if other is None else int(other["denominator_accounts"]), "strict_relative_support": strict_rate, "principal_strict_ratio": ratio, "stability_status": status})
        output.append(item)
    return output


def pre_churn_analysis(records: list[dict[str, Any]], observation_end: pd.Timestamp) -> list[dict[str, Any]]:
    """Compare fixed-window suffixes using observation_end as non-churn pseudo-cutoff."""
    output = []
    full = [row for row in records if row["journey_scope"] == "FULL_OBSERVED_JOURNEY"]
    for population in ("MAIN", "STRICT"):
        scoped = [row for row in full if row["quality_population"] == population]
        groups = {"CHURN_OBSERVED": [], "NO_CHURN_OBSERVED": []}
        for row in scoped:
            churn_positions = [i for i, token in enumerate(row["_tokens"]) if token == "CHURN"]
            label = "CHURN_OBSERVED" if churn_positions else "NO_CHURN_OBSERVED"
            cutoff = row["_dates"][churn_positions[0]] if churn_positions else observation_end
            groups[label].append((row, pd.Timestamp(cutoff)))
        for window in (7, 30, 60, 90):
            patterns_by_group: dict[str, Counter[tuple[str, ...]]] = {}
            for label, members in groups.items():
                counts: Counter[tuple[str, ...]] = Counter()
                for row, cutoff in members:
                    tokens = [token for token, date in zip(row["_tokens"], row["_dates"]) if cutoff - pd.Timedelta(days=window) <= date <= cutoff]
                    pats = {tuple(tokens[-size:]) for size in (2, 3, 5) if len(tokens) >= size}
                    counts.update(pats)
                patterns_by_group[label] = counts
            all_patterns = sorted(set(patterns_by_group["CHURN_OBSERVED"]) | set(patterns_by_group["NO_CHURN_OBSERVED"]))
            for pattern in all_patterns:
                churn_n, control_n = len(groups["CHURN_OBSERVED"]), len(groups["NO_CHURN_OBSERVED"])
                churn_support = patterns_by_group["CHURN_OBSERVED"][pattern]
                control_support = patterns_by_group["NO_CHURN_OBSERVED"][pattern]
                churn_rate = churn_support / churn_n if churn_n else None
                control_rate = control_support / control_n if control_n else None
                output.append({
                    "quality_population": population, "window_days": window,
                    "suffix_length": len(pattern), "pattern": list(pattern), "pattern_label": " -> ".join(pattern),
                    "churn_support": churn_support, "churn_denominator": churn_n, "churn_rate": churn_rate,
                    "non_churn_support": control_support, "non_churn_denominator": control_n, "non_churn_rate": control_rate,
                    "absolute_difference": None if churn_rate is None or control_rate is None else churn_rate - control_rate,
                    "discriminative_ratio": None if churn_rate is None or not control_rate else churn_rate / control_rate,
                    "exposure_control": f"FIXED_{window}D_WINDOW_WITH_OBSERVATION_END_PSEUDO_CUTOFF",
                    "limitations": ["DESCRIPTIVE_NOT_CAUSAL", "PSEUDO_CUTOFF_FOR_CENSORED"],
                })
    return annotate_stability_pre_churn(output)


def annotate_stability_pre_churn(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = ("window_days", "suffix_length", "pattern_label")
    strict = {tuple(row[k] for k in keys): row for row in rows if row["quality_population"] == "STRICT"}
    output = []
    for row in rows:
        if row["quality_population"] != "MAIN":
            continue
        item = dict(row)
        other = strict.get(tuple(row[k] for k in keys))
        main_diff = row["absolute_difference"]
        strict_diff = None if other is None else other["absolute_difference"]
        same_direction = main_diff is not None and strict_diff is not None and main_diff * strict_diff >= 0
        if other and same_direction and abs(strict_diff - main_diff) <= 0.05:
            status = "ROBUST"
        elif other and same_direction:
            status = "SENSITIVE"
        else:
            status = "UNSTABLE"
        item.update({
            "principal_support": row["churn_support"], "strict_support": 0 if other is None else other["churn_support"],
            "stability_status": status, "same_day_dependency": "NONE",
        })
        output.append(item)
    return output


def prefix_suffix_patterns(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in records:
        tokens = row["_tokens"]
        for kind, selected in (("PREFIX", tokens), ("SUFFIX", tokens)):
            for length in range(2, min(6, len(tokens)) + 1):
                pattern = selected[:length] if kind == "PREFIX" else selected[-length:]
                output.append({"population": row["quality_population"], "scope": row["journey_scope"], "outcome": row["outcome"], "kind": kind, "pattern": tuple(pattern)})
    counts: Counter[tuple[Any, ...]] = Counter((r["population"], r["scope"], r["outcome"], r["kind"], r["pattern"]) for r in output)
    denominators: Counter[tuple[Any, ...]] = Counter((r["quality_population"], r["journey_scope"], r["outcome"]) for r in records)
    return [{"quality_population": k[0], "journey_scope": k[1], "outcome": k[2], "pattern_type": k[3], "pattern": list(k[4]), "account_support": v, "denominator_accounts": denominators[(k[0], k[1], k[2])], "relative_support": v / denominators[(k[0], k[1], k[2])]} for k, v in sorted(counts.items())]
