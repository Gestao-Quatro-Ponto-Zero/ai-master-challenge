#!/usr/bin/env python3
"""Produce a deterministic, aggregate-only D01 audit from hash-locked CSV files."""

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
CUSTOMER_COLUMNS = [
    "Ticket ID", "Customer Name", "Customer Email", "Customer Age", "Customer Gender",
    "Product Purchased", "Date of Purchase", "Ticket Type", "Ticket Subject",
    "Ticket Description", "Ticket Status", "Resolution", "Ticket Priority", "Ticket Channel",
    "First Response Time", "Time to Resolution", "Customer Satisfaction Rating",
]
NUMERIC = {"Ticket ID", "Customer Age", "Customer Satisfaction Rating"}
TIMESTAMPS = {"First Response Time", "Time to Resolution"}


def sha256(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def present(value):
    return bool(value.strip())


def timestamp(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except ValueError:
        return None


def quantile(values, fraction):
    ordered = sorted(values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower), 6)


def distribution(values):
    return {"n": len(values), "min": min(values) if values else None,
            "median": quantile(values, .5), "p95": quantile(values, .95),
            "max": max(values) if values else None}


def normalize(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def text_profile(rows, column, label):
    texts = [row[column] for row in rows if present(row[column])]
    groups = defaultdict(list)
    for row in rows:
        if present(row[column]):
            groups[normalize(row[column])].append(row[label])
    repeated = [labels for labels in groups.values() if len(labels) > 1]
    conflicts = [labels for labels in repeated if len(set(labels)) > 1]
    return {
        "nonempty_rows": len(texts), "exact_unique_texts": len(set(texts)),
        "normalized_unique_texts": len(groups),
        "normalization": "Unicode NFKC, casefold, collapse whitespace; punctuation retained",
        "normalized_duplicate_groups": len(repeated),
        "rows_in_normalized_duplicate_groups": sum(map(len, repeated)),
        "normalized_duplicate_excess_rows": sum(len(labels) - 1 for labels in repeated),
        "conflicting_label_groups": len(conflicts),
        "rows_in_conflicting_label_groups": sum(map(len, conflicts)),
        "label_column": label, "characters": distribution([len(t) for t in texts]),
        "words": distribution([len(t.split()) for t in texts]),
        "rows_with_unfilled_braces": sum(bool(re.search(r"\{[^{}]+\}", t)) for t in texts),
    }


def schema_profile(rows, columns):
    profiles = []
    for column in columns:
        values = [row[column] for row in rows if present(row[column])]
        profile = {"name": column, "missing": len(rows) - len(values),
                   "nonmissing": len(values), "unique_nonmissing": len(set(values))}
        if column in NUMERIC:
            parsed = [number(v) for v in values]
            profile.update({"observed_kind": "numeric", "invalid": parsed.count(None),
                            "distribution": distribution([v for v in parsed if v is not None])})
        elif column in TIMESTAMPS or column == "Date of Purchase":
            parsed = [timestamp(v) for v in values] if column in TIMESTAMPS else []
            if column == "Date of Purchase":
                for value in values:
                    try:
                        parsed.append(datetime.strptime(value, "%Y-%m-%d"))
                    except ValueError:
                        parsed.append(None)
            valid = [v for v in parsed if v is not None]
            profile.update({"observed_kind": "naive_datetime" if column in TIMESTAMPS else "date",
                            "invalid": parsed.count(None),
                            "min": min(valid).isoformat() if valid else None,
                            "max": max(valid).isoformat() if valid else None})
        else:
            profile["observed_kind"] = "string"
        profiles.append(profile)
    return profiles


def customer_audit(rows):
    statuses = {}
    for status in sorted({row["Ticket Status"] for row in rows}):
        group = [row for row in rows if row["Ticket Status"] == status]
        statuses[status] = {"rows": len(group), **{
            column + " present": sum(present(row[column]) for row in group)
            for column in ["First Response Time", "Time to Resolution", "Resolution", "Customer Satisfaction Rating"]}}
    deltas = []
    for row in rows:
        first, closed = timestamp(row["First Response Time"]), timestamp(row["Time to Resolution"])
        if first is not None and closed is not None:
            deltas.append((closed - first).total_seconds() / 3600)
    valid_ratings = [number(row["Customer Satisfaction Rating"]) for row in rows
                     if present(row["Customer Satisfaction Rating"])]
    closed_count = sum(row["Ticket Status"] == "Closed" for row in rows)
    return {
        "ticket_id_duplicate_excess": len(rows) - len({row["Ticket ID"] for row in rows}),
        "categories": {column: dict(sorted(Counter(row[column] for row in rows).items()))
                       for column in ["Ticket Status", "Ticket Type", "Ticket Priority", "Ticket Channel"]},
        "coverage_by_status": statuses,
        "satisfaction": {"observed": len(valid_ratings), "total_rows": len(rows),
                         "closed_rows": closed_count,
                         "outside_integer_1_to_5_or_invalid": sum(v is None or v not in range(1, 6) for v in valid_ratings),
                         "distribution": dict(sorted(Counter(row["Customer Satisfaction Rating"] for row in rows
                                                              if present(row["Customer Satisfaction Rating"])).items()))},
        "time_fields": {"stored_as": "timezone-unspecified timestamps, not numeric durations",
                        "ticket_created_at_available": False,
                        "first_response_latency_identifiable": False,
                        "full_resolution_duration_identifiable": False,
                        "paired_rows": len(deltas), "resolution_before_first_response": sum(v < 0 for v in deltas),
                        "equal_timestamps": sum(v == 0 for v in deltas),
                        "response_to_resolution_hours_all_pairs": distribution(deltas),
                        "response_to_resolution_hours_nonnegative_only": distribution([v for v in deltas if v >= 0]),
                        "warning": "A post-response interval is not ticket lifetime or active effort; negative pairs are retained and counted, not corrected"},
        "description": text_profile(rows, "Ticket Description", "Ticket Type"),
        "resolution": text_profile(rows, "Resolution", "Ticket Type"),
        "email_domain_counts": dict(sorted(Counter(row["Customer Email"].rsplit("@", 1)[-1]
                                                    for row in rows if present(row["Customer Email"])).items())),
    }


def read_csv(path, expected):
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != expected:
            raise ValueError(f"Unexpected schema in {path.name}: {reader.fieldnames}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"Malformed CSV row in {path.name}")
    return rows


def audit(root=ROOT):
    manifest_path = root / "data/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    result = {"schema_version": 1, "python": platform.python_version(),
              "manifest_sha256": sha256(manifest_path), "audit_script_sha256": sha256(Path(__file__)),
              "missing_definition": "empty or whitespace-only CSV cells; no imputation",
              "quantiles": "linear interpolation at (n-1)*q", "datasets": {}}
    for key in ["customer_support", "it_service"]:
        entry = manifest["datasets"][key]
        path = (root / entry["file"]["path"]).resolve()
        if not path.is_relative_to(root.resolve()) or sha256(path) != entry["file"]["sha256"]:
            raise ValueError(f"{key}: CSV path/hash differs from manifest")
        columns = CUSTOMER_COLUMNS if key == "customer_support" else ["Document", "Topic_group"]
        rows = read_csv(path, columns)
        details = customer_audit(rows) if key == "customer_support" else {
            "class_counts": dict(sorted(Counter(row["Topic_group"] for row in rows).items())),
            "document": text_profile(rows, "Document", "Topic_group")}
        result["datasets"][key] = {
            "version": entry["version"], "file_sha256": sha256(path), "bytes": path.stat().st_size,
            "rows": len(rows), "columns": schema_profile(rows, columns),
            "exact_duplicate_excess_rows": len(rows) - len({tuple(row[c] for c in columns) for row in rows}),
            **details}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/audit.json")
    args = parser.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"Audit saved: {args.output}")
