#!/usr/bin/env python3
"""Reproduce A01 descriptive comparisons and explicitly assumed effort scenarios."""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import importlib.util
from itertools import combinations, product
import json
import math
from pathlib import Path
import platform
import random


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("support_audit", Path(__file__).with_name("audit_data.py"))
AUDIT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AUDIT)
DIMENSIONS = ("Ticket Channel", "Ticket Priority", "Ticket Type")
STATUSES = {"Closed", "Open", "Pending Customer Response"}


def rounded(value):
    return round(value, 6) if value is not None else None


def ratio(numerator, denominator):
    return rounded(numerator / denominator) if denominator else None


def rating(row):
    value = AUDIT.number(row["Customer Satisfaction Rating"])
    return int(value) if value is not None and value in range(1, 6) else None


def quality_groups(rows):
    groups = defaultdict(list)
    for row in rows:
        if row["Ticket Description"].strip():
            groups[AUDIT.normalize(row["Ticket Description"])].append(row["Ticket Type"])
    duplicate = {key for key, labels in groups.items() if len(labels) > 1}
    conflict = {key for key, labels in groups.items() if len(set(labels)) > 1}
    return duplicate, conflict


def summarize(rows, duplicate=(), conflict=()):
    counts = Counter(row["Ticket Status"] for row in rows)
    if set(counts) - STATUSES:
        raise ValueError("Unexpected ticket status; review the population before analysis")
    all_rated = [row for row in rows if rating(row) is not None]
    closed_ratings = [rating(row) for row in all_rated if row["Ticket Status"] == "Closed"]
    scores = Counter(closed_ratings)
    total, closed, rated = len(rows), counts["Closed"], len(closed_ratings)
    return {
        "tickets": total, "open": counts["Open"], "pending_customer_response": counts["Pending Customer Response"],
        "closed": closed, "nonclosed": total - closed,
        "nonclosed_share": ratio(total - closed, total), "closed_share": ratio(closed, total),
        "missing_first_response_field": sum(not row["First Response Time"].strip() for row in rows),
        "valid_rated_all": len(all_rated), "rated_closed": rated,
        "rated_nonclosed": len(all_rated) - rated, "unrated_closed": closed - rated,
        "invalid_nonblank_ratings": sum(bool(row["Customer Satisfaction Rating"].strip()) and rating(row) is None for row in rows),
        "csat_coverage_all": ratio(len(all_rated), total), "csat_coverage_closed": ratio(rated, closed),
        "csat_mean": rounded(sum(closed_ratings) / rated) if rated else None,
        "csat_median": AUDIT.quantile(closed_ratings, .5),
        "low_csat_count": scores[1] + scores[2], "low_csat_share": ratio(scores[1] + scores[2], rated),
        **{f"score_{i}": scores[i] for i in range(1, 6)},
        "duplicate_description_rows": sum(AUDIT.normalize(row["Ticket Description"]) in duplicate for row in rows),
        "conflicting_type_rows": sum(AUDIT.normalize(row["Ticket Description"]) in conflict for row in rows),
    }


def segments(rows):
    duplicate, conflict = quality_groups(rows)
    result = [{"grouping": "overall", **dict.fromkeys(DIMENSIONS, ""), **summarize(rows, duplicate, conflict)}]
    levels = {key: sorted({row[key] for row in rows}) for key in DIMENSIONS}
    for width in range(1, 4):
        for fields in combinations(DIMENSIONS, width):
            groups = defaultdict(list)
            for row in rows:
                groups[tuple(row[key] for key in fields)].append(row)
            for values in product(*(levels[key] for key in fields)):
                result.append({"grouping": " + ".join(fields), **dict.fromkeys(DIMENSIONS, ""),
                               **dict(zip(fields, values)), **summarize(groups[values], duplicate, conflict)})
    return result


def mean_variation(values, labels):
    """Between-group score variation / total variation; a descriptive mean effect."""
    if not values:
        return 0.0
    overall = sum(values) / len(values)
    total = sum((value - overall) ** 2 for value in values)
    groups = defaultdict(list)
    for value, label in zip(values, labels):
        groups[label].append(value)
    between = sum(len(group) * (sum(group) / len(group) - overall) ** 2 for group in groups.values())
    return between / total if total else 0.0


def association(rows, field, repeats, seed):
    closed = [row for row in rows if row["Ticket Status"] == "Closed" and rating(row) is not None]
    values, labels = [rating(row) for row in closed], [row[field] for row in closed]
    observed = mean_variation(values, labels)
    rng = random.Random(seed)
    shuffled = values[:]
    exceed = 0
    for _ in range(repeats):
        rng.shuffle(shuffled)
        exceed += mean_variation(shuffled, labels) >= observed - 1e-12
    return {"field": field, "rated_closed": len(values), "mean_variation_fraction": rounded(observed),
            "permutation_p": (exceed + 1) / (repeats + 1), "permutations": repeats, "seed": seed}


def holm_adjust(pvalues):
    """Control the three predeclared comparisons; preserve original order."""
    output = [0.0] * len(pvalues)
    previous = 0.0
    for rank, index in enumerate(sorted(range(len(pvalues)), key=pvalues.__getitem__)):
        previous = min(1.0, max(previous, (len(pvalues) - rank) * pvalues[index]))
        output[index] = previous
    return output


def scenario(case):
    rates = {"eligible_share", "assisted_share", "review_share", "error_share"}
    amounts = {"tickets", "manual_minutes", "assisted_minutes", "review_minutes", "rework_minutes", "fixed_minutes", "hourly_value_brl"}
    for field in rates | amounts:
        value = case[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"Invalid nonnegative finite scenario input: {field}")
        if field in rates and value > 1:
            raise ValueError(f"Scenario share outside [0,1]: {field}")
    covered = case["tickets"] * case["eligible_share"] * case["assisted_share"]
    gross = covered * (case["manual_minutes"] - case["assisted_minutes"])
    review = covered * case["review_share"] * case["review_minutes"]
    rework = covered * case["error_share"] * case["rework_minutes"]
    net = (gross - review - rework - case["fixed_minutes"]) / 60
    break_even = (case["assisted_minutes"] + case["review_share"] * case["review_minutes"] +
                  case["error_share"] * case["rework_minutes"] + case["fixed_minutes"] / covered) if covered else None
    return {"name": case["name"], "assumptions": case, "assisted_cases": rounded(covered),
            "baseline_triage_hours_all_cases": rounded(case["tickets"] * case["manual_minutes"] / 60),
            "gross_minutes_saved": rounded(gross), "incremental_review_minutes": rounded(review),
            "incremental_rework_minutes": rounded(rework), "fixed_minutes": case["fixed_minutes"],
            "net_capacity_hours": rounded(net), "capacity_value_at_assumed_rate_brl": rounded(net * case["hourly_value_brl"]),
            "break_even_manual_minutes_per_assisted_case": rounded(break_even)}


def diagnose(root=ROOT):
    config_path, manifest_path = root / "data/diagnosis-assumptions.json", root / "data/manifest.json"
    config, manifest = json.loads(config_path.read_text()), json.loads(manifest_path.read_text())
    if config.get("schema_version") != 1:
        raise ValueError("Unsupported diagnosis configuration")
    for field in ["display_min_tickets", "display_min_rated_closed", "permutation_repeats", "permutation_seed"]:
        if type(config[field]) is not int or config[field] < 1:
            raise ValueError(f"Diagnosis configuration requires positive integer: {field}")
    if config["permutation_repeats"] > 99999:
        raise ValueError("Permutation repeats exceed the supported analysis budget")
    entry = manifest["datasets"]["customer_support"]["file"]
    path = (root / entry["path"]).resolve()
    if not path.is_relative_to(root.resolve()) or AUDIT.sha256(path) != entry["sha256"]:
        raise ValueError("Customer CSV path/hash differs from manifest")
    rows = AUDIT.read_csv(path, AUDIT.CUSTOMER_COLUMNS)
    table = segments(rows)
    tests = [association(rows, field, config["permutation_repeats"], config["permutation_seed"] + i)
             for i, field in enumerate(DIMENSIONS)]
    for test, adjusted in zip(tests, holm_adjust([test["permutation_p"] for test in tests])):
        test["holm_adjusted_p"] = rounded(adjusted)
    triple = [item for item in table if item["grouping"] == " + ".join(DIMENSIONS)]
    supported = [item for item in triple if item["tickets"] >= config["display_min_tickets"]]
    rated = [item for item in supported if item["rated_closed"] >= config["display_min_rated_closed"]]
    key = lambda item: tuple(item[field] for field in DIMENSIONS)
    result = {
        "schema_version": 1, "python": platform.python_version(),
        "source_sha256": {"data/manifest.json": AUDIT.sha256(manifest_path),
                          entry["path"]: AUDIT.sha256(path), "data/diagnosis-assumptions.json": AUDIT.sha256(config_path),
                          "solution/diagnose_support.py": AUDIT.sha256(Path(__file__)),
                          "solution/audit_data.py": AUDIT.sha256(Path(__file__).with_name("audit_data.py"))},
        "definitions": {"population": "All original customer-support records; no deduplication, imputation or timestamp repair",
                        "segments": "Each grouping is a separate partition of the same records; do not sum across different grouping types",
                        "satisfaction": "Valid integer scores 1-5 from Closed rows only; full population and closed coverage reported separately",
                        "low_csat": "Scores 1 or 2; descriptive convention, not business SLA",
                        "association": "Between-group mean score variation divided by total score variation; means assume equal score spacing",
                        "permutation": f"Shuffle closed ratings across fixed groups; (exceedances+1)/({config['permutation_repeats']}+1); Holm correction over three predeclared one-way tests",
                        "inference_limits": "Exploratory exchangeability assumption; repeated content and unknown generator/provenance limit population inference; no causal or predictive claim",
                        "scenario": "Assumed monthly capacity, not measured labor/cash savings; all assisted cases receive human review in these examples"},
        "overall": table[0], "single_dimension_groups": [item for item in table if item["grouping"] in DIMENSIONS],
        "associations": tests,
        "combination_display": {"total_combinations": len(triple), "min_tickets": config["display_min_tickets"],
                                "min_rated_closed": config["display_min_rated_closed"],
                                "supported_combinations": len(supported), "rated_supported_combinations": len(rated),
                                "largest_nonclosed_share": sorted(supported, key=lambda item: (-item["nonclosed_share"], -item["tickets"], key(item)))[:5],
                                "lowest_csat_mean": sorted(rated, key=lambda item: (item["csat_mean"], -item["rated_closed"], key(item)))[:5],
                                "warning": "Descriptive extremes selected from many groups; no independent test of their ranking"},
        "scenarios": [scenario(case) for case in config["scenarios"]],
    }
    return result, table


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/diagnosis.json")
    parser.add_argument("--segments", type=Path, default=ROOT / "data/diagnosis-segments.csv")
    args = parser.parse_args()
    result, table = diagnose()
    args.segments.parent.mkdir(parents=True, exist_ok=True)
    with args.segments.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(table[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(table)
    result["segments_csv_sha256"] = AUDIT.sha256(args.segments)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"Diagnosis saved: {args.output}; {len(table)} aggregate segment rows")
