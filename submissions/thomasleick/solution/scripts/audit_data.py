#!/usr/bin/env python3
"""Standard-library profile for the five original RavenStack CSVs."""
import argparse
import csv
import datetime as dt
import hashlib
import json
import pathlib
from collections import Counter

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--data-dir",
    type=pathlib.Path,
    default=pathlib.Path(__file__).resolve().parents[1] / "data" / "raw",
    help="directory containing the five RavenStack source CSVs (default: solution/data/raw)",
)
parser.add_argument(
    "--output",
    type=pathlib.Path,
    help="write JSON to this path; when omitted, print JSON to stdout",
)
args = parser.parse_args()
root = args.data_dir
required_files = [
    "ravenstack_accounts.csv",
    "ravenstack_subscriptions.csv",
    "ravenstack_feature_usage.csv",
    "ravenstack_support_tickets.csv",
    "ravenstack_churn_events.csv",
]
missing_files = [name for name in required_files if not (root / name).is_file()]
if missing_files:
    parser.error(f"missing required CSV files in {root}: {', '.join(missing_files)}")
profile = {}
for path in sorted(root.glob("ravenstack_*.csv")):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []
    fields = {}
    for column in columns:
        values = [row.get(column, "") or "" for row in rows]
        present = [value for value in values if value != ""]
        unique = set(present)
        if not present:
            kind = "empty"
        elif unique <= {"True", "False", "true", "false", "0", "1"}:
            kind = "bool-like"
        else:
            try:
                [int(value) for value in present]
                kind = "integer-like"
            except ValueError:
                try:
                    [float(value) for value in present]
                    kind = "numeric-like"
                except ValueError:
                    kind = "string"
        dates = []
        if "date" in column.lower() or column.endswith("_at"):
            for value in present:
                try:
                    dates.append(dt.datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat())
                except ValueError:
                    pass
        fields[column] = {
            "inferred_type": kind,
            "null_count": len(rows) - len(present),
            "null_rate": round((len(rows) - len(present)) / len(rows), 6) if rows else None,
            "distinct_non_null": len(unique),
            "examples": list(dict.fromkeys(present))[:4],
            "date_min": min(dates) if dates else None,
            "date_max": max(dates) if dates else None,
        }
    key_checks = {}
    for key in [column for column in columns if column.endswith("_id")]:
        ids = [row[key] for row in rows if row.get(key)]
        id_counts = Counter(ids)
        duplicate_groups = [count for count in id_counts.values() if count > 1]
        key_checks[key] = {
            "nonnull": len(ids),
            "distinct": len(id_counts),
            "duplicate_ids": len(duplicate_groups),
            "rows_in_duplicate_id_groups": sum(duplicate_groups),
            "excess_duplicate_rows": sum(duplicate_groups) - len(duplicate_groups),
        }
    profile[path.name] = {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "rows": len(rows),
        "columns": columns,
        "field_profiles": fields,
        "id_checks": key_checks,
        "full_duplicate_rows": len(rows) - len({tuple(row.items()) for row in rows}),
    }

tables = {}
for name in ("accounts", "subscriptions", "feature_usage", "support_tickets", "churn_events"):
    with (root / f"ravenstack_{name}.csv").open(newline="", encoding="utf-8-sig") as handle:
        tables[name] = list(csv.DictReader(handle))
account_ids = {row["account_id"] for row in tables["accounts"]}
subscription_ids = {row["subscription_id"] for row in tables["subscriptions"]}
relationships = {}
for child, field, parents in (
    ("subscriptions", "account_id", account_ids),
    ("support_tickets", "account_id", account_ids),
    ("churn_events", "account_id", account_ids),
    ("feature_usage", "subscription_id", subscription_ids),
):
    values = [row[field] for row in tables[child]]
    distribution = Counter(Counter(values).values())
    relationships[f"{child}.{field}"] = {
        "rows": len(values),
        "distinct_keys": len(set(values)),
        "orphan_rows": sum(value not in parents for value in values),
        "rows_per_key_counts": dict(sorted(distribution.items())),
    }
profile["relationships"] = relationships
serialized = json.dumps(profile, indent=2) + "\n"
if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized, encoding="utf-8")
    print(f"Wrote {args.output}")
else:
    print(serialized, end="")
