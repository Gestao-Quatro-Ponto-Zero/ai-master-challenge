#!/usr/bin/env python3
"""Reproduce descriptive, non-causal RavenStack aggregates from the source CSVs."""

import argparse
import csv
import datetime as dt
import json
import pathlib
import statistics
from collections import Counter, defaultdict


def read_table(root: pathlib.Path, name: str) -> list[dict[str, str]]:
    with (root / f"ravenstack_{name}.csv").open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def truth(value: str) -> bool:
    return value.lower() == "true"


def month(value: str) -> str:
    return dt.date.fromisoformat(value[:10]).strftime("%Y-%m")


def build_summary(root: pathlib.Path) -> dict:
    accounts = read_table(root, "accounts")
    subscriptions = read_table(root, "subscriptions")
    usage_rows = read_table(root, "feature_usage")
    tickets = read_table(root, "support_tickets")
    events = read_table(root, "churn_events")

    accounts_by_id = {row["account_id"]: row for row in accounts}
    subscriptions_by_id = {row["subscription_id"]: row for row in subscriptions}
    events_by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    subscriptions_by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    usage_by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    tickets_by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in events:
        events_by_account[row["account_id"]].append(row)
    for row in subscriptions:
        subscriptions_by_account[row["account_id"]].append(row)
    for row in usage_rows:
        subscription = subscriptions_by_id.get(row["subscription_id"])
        if subscription is None:
            raise ValueError(f"Usage row refers to unknown subscription_id {row['subscription_id']}")
        usage_by_account[subscription["account_id"]].append(row)
    for row in tickets:
        tickets_by_account[row["account_id"]].append(row)

    event_accounts = set(events_by_account)
    flags = {row["account_id"]: truth(row["churn_flag"]) for row in accounts}
    usage_id_counts = Counter(row["usage_id"] for row in usage_rows if row["usage_id"])
    duplicate_id_counts = {key: count for key, count in usage_id_counts.items() if count > 1}

    all_months = sorted(
        {month(row["churn_date"]) for row in events}
        | {month(row["usage_date"]) for row in usage_rows}
        | {month(row["submitted_at"]) for row in tickets}
    )
    monthly = {}
    for current_month in all_months:
        month_events = [row for row in events if month(row["churn_date"]) == current_month]
        month_usage = [row for row in usage_rows if month(row["usage_date"]) == current_month]
        month_tickets = [row for row in tickets if month(row["submitted_at"]) == current_month]
        scores = [float(row["satisfaction_score"]) for row in month_tickets if row["satisfaction_score"]]
        monthly[current_month] = {
            "event_rows": len(month_events),
            "unique_event_accounts": len({row["account_id"] for row in month_events}),
            "nonreactivation_rows": sum(not truth(row["is_reactivation"]) for row in month_events),
            "usage_rows": len(month_usage),
            "usage_count_sum": sum(int(row["usage_count"]) for row in month_usage),
            "usage_accounts": len({subscriptions_by_id[row["subscription_id"]]["account_id"] for row in month_usage}),
            "tickets": len(month_tickets),
            "satisfaction_n": len(scores),
            "satisfaction_mean": round(statistics.mean(scores), 6) if scores else None,
        }

    industry_comparison = {}
    for industry in sorted({row["industry"] for row in accounts}):
        group = [row for row in accounts if row["industry"] == industry]
        flag_count = sum(flags[row["account_id"]] for row in group)
        event_count = sum(row["account_id"] in event_accounts for row in group)
        industry_comparison[industry] = {
            "accounts": len(group),
            "flag_true": flag_count,
            "flag_rate": round(flag_count / len(group), 6),
            "any_event": event_count,
            "event_account_rate": round(event_count / len(group), 6),
        }

    flag_event = {
        "flag_true_event_yes": sum(value and key in event_accounts for key, value in flags.items()),
        "flag_true_event_no": sum(value and key not in event_accounts for key, value in flags.items()),
        "flag_false_event_yes": sum(not value and key in event_accounts for key, value in flags.items()),
        "flag_false_event_no": sum(not value and key not in event_accounts for key, value in flags.items()),
    }
    usage_by_account_total = {
        account_id: sum(int(row["usage_count"]) for row in usage_by_account[account_id])
        for account_id in accounts_by_id
    }
    usage_groups = {}
    for label, account_ids in (
        ("any_event", event_accounts),
        ("no_event", set(accounts_by_id) - event_accounts),
    ):
        values = [usage_by_account_total[account_id] for account_id in account_ids]
        usage_groups[label] = {
            "accounts": len(values),
            "mean_account_usage_count": round(statistics.mean(values), 6),
            "median_account_usage_count": statistics.median(values),
        }

    support = {}
    for label, account_ids in (
        ("event_accounts", event_accounts),
        ("no_event_accounts", set(accounts_by_id) - event_accounts),
    ):
        group_tickets = [row for row in tickets if row["account_id"] in account_ids]
        scores = [float(row["satisfaction_score"]) for row in group_tickets if row["satisfaction_score"]]
        support[label] = {
            "ticket_rows": len(group_tickets),
            "satisfaction_n": len(scores),
            "satisfaction_missing": len(group_tickets) - len(scores),
            "satisfaction_mean": round(statistics.mean(scores), 6) if scores else None,
        }

    refunds = sum(float(row["refund_amount_usd"] or 0) for row in events)
    ended_subscriptions = sum(bool(row["end_date"]) for row in subscriptions)
    open_ended_account_count = sum(
        any(not row["end_date"] for row in subscriptions_by_account[account_id])
        for account_id in accounts_by_id
    )
    usage_before_start = 0
    usage_after_end = 0
    for row in usage_rows:
        subscription = subscriptions_by_id[row["subscription_id"]]
        usage_date = dt.date.fromisoformat(row["usage_date"])
        if usage_date < dt.date.fromisoformat(subscription["start_date"]):
            usage_before_start += 1
        if subscription["end_date"] and usage_date > dt.date.fromisoformat(subscription["end_date"]):
            usage_after_end += 1

    return {
        "definitions": {
            "event_accounts": "unique account_id with at least one event, regardless of reactivation or date",
            "account_flag": "accounts.churn_flag as supplied; not reconciled to events",
            "monthly_event_counts": "event rows by churn_date month; not a rate",
            "usage_account_total": "sum of usage_count across linked subscriptions and all dates; not time-normalized",
            "duplicate_usage_ids": "distinct non-null usage_id values appearing more than once",
            "usage_rows_in_duplicate_id_groups": "all rows belonging to a duplicated usage_id group",
            "usage_duplicate_excess_rows": "rows beyond the first row for each duplicated usage_id",
        },
        "counts": {
            "accounts": len(accounts),
            "account_flag_true": sum(flags.values()),
            "event_rows": len(events),
            "event_unique_accounts": len(event_accounts),
            "event_reactivation_rows": sum(truth(row["is_reactivation"]) for row in events),
            "event_nonreactivation_rows": sum(not truth(row["is_reactivation"]) for row in events),
            "subscription_rows": len(subscriptions),
            "subscription_ended_rows": ended_subscriptions,
            "account_with_any_open_ended_subscription_row": open_ended_account_count,
            "usage_rows": len(usage_rows),
            "usage_duplicate_ids": len(duplicate_id_counts),
            "usage_rows_in_duplicate_id_groups": sum(duplicate_id_counts.values()),
            "usage_duplicate_excess_rows": sum(duplicate_id_counts.values()) - len(duplicate_id_counts),
            "usage_before_subscription_start": usage_before_start,
            "usage_after_subscription_end": usage_after_end,
            "tickets": len(tickets),
            "tickets_missing_satisfaction": sum(not row["satisfaction_score"] for row in tickets),
        },
        "flag_event_crosstab": flag_event,
        "event_rows_by_year": dict(sorted(Counter(row["churn_date"][:4] for row in events).items())),
        "unique_event_accounts_by_year": {
            year: len({row["account_id"] for row in events if row["churn_date"].startswith(year)})
            for year in sorted({row["churn_date"][:4] for row in events})
        },
        "industry_flags_and_event_comparison": industry_comparison,
        "all_time_usage_by_event_membership": usage_groups,
        "support_satisfaction_by_event_membership": support,
        "event_reason_counts": dict(Counter(row["reason_code"] for row in events)),
        "refund_amount_usd_sum": round(refunds, 2),
        "monthly": monthly,
    }


def main() -> None:
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
    required = (
        "accounts",
        "subscriptions",
        "feature_usage",
        "support_tickets",
        "churn_events",
    )
    missing = [f"ravenstack_{name}.csv" for name in required if not (args.data_dir / f"ravenstack_{name}.csv").is_file()]
    if missing:
        parser.error(f"missing required CSV files in {args.data_dir}: {', '.join(missing)}")
    serialized = json.dumps(build_summary(args.data_dir), indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
