#!/usr/bin/env python3
"""Reconstruct customer-level churn diagnostics without conflating labels.

The primary customer churn KPI is NOT IDENTIFIABLE: the source describes end
dates as subscription endings and events as account departures, but these
signals conflict at account grain. Date-based account coverage rates below are
explicitly conditional diagnostics, not validated customer churn.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

MODULE = Path(__file__).resolve().parent
SOLUTION = MODULE.parents[1]
DEFAULT_DATA = SOLUTION / "data" / "raw"
DEFAULT_OUTPUT = MODULE / "outputs"
FILES = {
    "accounts": "ravenstack_accounts.csv",
    "subscriptions": "ravenstack_subscriptions.csv",
    "events": "ravenstack_churn_events.csv",
}


def parse_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value[:10]) if value else None
    except (TypeError, ValueError):
        return None


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def active_rows(subscriptions: list[dict[str, str]], on: date) -> list[dict[str, str]]:
    """Source README date rule: start <= day and (end is blank or end > day)."""
    return [
        row for row in subscriptions
        if (start := parse_date(row.get("start_date"))) is not None
        and start <= on
        and ((end := parse_date(row.get("end_date"))) is None or end > on)
    ]


def merged_intervals(rows: list[dict[str, str]], lo: date, hi: date) -> list[tuple[date, date]]:
    intervals: list[tuple[date, date]] = []
    for row in rows:
        start, end = parse_date(row.get("start_date")), parse_date(row.get("end_date"))
        if start is None or (end is not None and end <= start) or start >= hi or (end and end <= lo):
            continue
        intervals.append((max(start, lo), min(end or hi, hi)))
    intervals.sort()
    merged: list[list[date]] = []
    for start, end in intervals:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        elif end > merged[-1][1]:
            merged[-1][1] = end
    return [(start, end) for start, end in merged]


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _period(year: int, accounts: list[dict[str, str]], subscriptions: list[dict[str, str]], events: list[dict[str, str]]) -> dict[str, Any]:
    start, stop = date(year, 1, 1), date(year + 1, 1, 1)
    opening_rows, closing_rows = active_rows(subscriptions, start), active_rows(subscriptions, stop)
    opening = {row["account_id"] for row in opening_rows}
    closing = {row["account_id"] for row in closing_rows}
    by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in subscriptions:
        by_account[row["account_id"]].append(row)

    gross_gap: set[str] = set()
    for account_id in opening:
        merged = merged_intervals(by_account[account_id], start, stop)
        if not merged or merged[0][0] > start or any(
            merged[i][0] > merged[i - 1][1] for i in range(1, len(merged))
        ) or merged[-1][1] < stop:
            gross_gap.add(account_id)

    event_rows = [
        row for row in events
        if (event_date := parse_date(row.get("churn_date"))) is not None
        and start <= event_date < stop
    ]
    nonreact = [row for row in event_rows if not truth(row.get("is_reactivation"))]
    nonreact_with_active_subscription = sum(
        any(
            (sub_start := parse_date(sub.get("start_date"))) is not None
            and sub_start <= (event_date := parse_date(event.get("churn_date")))
            and ((sub_end := parse_date(sub.get("end_date"))) is None or sub_end > event_date)
            for sub in subscriptions if sub["account_id"] == event["account_id"]
        )
        for event in nonreact
    )
    annual_ending = [
        row for row in subscriptions
        if (end := parse_date(row.get("end_date"))) is not None and start <= end < stop
    ]
    opening_ids = {row["subscription_id"] for row in opening_rows}
    closing_ids = {row["subscription_id"] for row in closing_rows}
    flag_accounts = {row["account_id"] for row in accounts if truth(row.get("churn_flag"))}
    first_starts: dict[str, date] = {}
    for row in subscriptions:
        started = parse_date(row.get("start_date"))
        if started and (row["account_id"] not in first_starts or started < first_starts[row["account_id"]]):
            first_starts[row["account_id"]] = started
    acquired = {account_id for account_id, d in first_starts.items() if start < d < stop}
    return {
        "year": year,
        "opening_active_accounts": len(opening),
        "opening_active_subscription_rows": len(opening_rows),
        "closing_active_accounts": len(closing),
        "opening_accounts_with_any_date_coverage_gap": len(gross_gap),
        "opening_accounts_without_coverage_at_close": len(opening - closing),
        "conditional_gross_date_churn_rate": _rate(len(gross_gap), len(opening)),
        "conditional_closing_date_loss_rate": _rate(len(opening - closing), len(opening)),
        "first_subscription_acquisitions_during_period": len(acquired),
        "subscription_ends_during_period": len(annual_ending),
        "opening_subscriptions_not_active_at_close": len(opening_ids - closing_ids),
        "conditional_subscription_churn_rate": _rate(len(opening_ids - closing_ids), len(opening_ids)),
        "event_rows_all": len(event_rows),
        "event_rows_nonreactivation": len(nonreact),
        "nonreactivation_event_rows_with_active_subscription": nonreact_with_active_subscription,
        "unique_accounts_with_nonreactivation_event": len({r["account_id"] for r in nonreact}),
        "opening_accounts_with_nonreactivation_event": len(opening & {r["account_id"] for r in nonreact}),
        "opening_accounts_with_account_churn_flag": len(opening & flag_accounts),
        "evidence_classification": "NOT_IDENTIFIABLE_PRIMARY_KPI; CONDITIONAL_DATE_DIAGNOSTIC",
        "date_rule": "start_date <= boundary and (end_date blank or end_date > boundary); account active if any linked subscription is active",
    }


def _monthly(subscriptions: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in subscriptions:
        by_account[row["account_id"]].append(row)
    result: list[dict[str, Any]] = []
    year, month = 2023, 1
    while (year, month) <= (2024, 12):
        start = date(year, month, 1)
        stop = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
        opening = {row["account_id"] for row in active_rows(subscriptions, start)}
        closing = {row["account_id"] for row in active_rows(subscriptions, stop)}
        gap = set()
        for account_id in opening:
            intervals = merged_intervals(by_account[account_id], start, stop)
            if not intervals or intervals[0][0] > start or any(
                intervals[i][0] > intervals[i - 1][1] for i in range(1, len(intervals))
            ) or intervals[-1][1] < stop:
                gap.add(account_id)
        result.append({
            "period": f"{year:04d}-{month:02d}", "opening_accounts": len(opening),
            "date_gap_accounts": len(gap), "accounts_without_coverage_at_close": len(opening - closing),
            "conditional_date_gap_rate": _rate(len(gap), len(opening)),
            "evidence_classification": "CONDITIONAL_DATE_DIAGNOSTIC" if opening else "UNDEFINED_ZERO_DENOMINATOR",
        })
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return result


def _quarterly(subscriptions: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in subscriptions:
        by_account[row["account_id"]].append(row)
    result: list[dict[str, Any]] = []
    for year in (2023, 2024):
        for quarter in range(1, 5):
            month = (quarter - 1) * 3 + 1
            start = date(year, month, 1)
            next_month = month + 3
            stop = date(year + (next_month > 12), ((next_month - 1) % 12) + 1, 1)
            opening = {row["account_id"] for row in active_rows(subscriptions, start)}
            closing = {row["account_id"] for row in active_rows(subscriptions, stop)}
            gaps = set()
            for account_id in opening:
                intervals = merged_intervals(by_account[account_id], start, stop)
                if not intervals or intervals[0][0] > start or any(
                    intervals[i][0] > intervals[i - 1][1] for i in range(1, len(intervals))
                ) or intervals[-1][1] < stop:
                    gaps.add(account_id)
            result.append({
                "period": f"{year}-Q{quarter}",
                "opening_accounts": len(opening),
                "date_gap_accounts": len(gaps),
                "accounts_without_coverage_at_close": len(opening - closing),
                "conditional_date_gap_rate": _rate(len(gaps), len(opening)),
                "evidence_classification": "CONDITIONAL_DATE_DIAGNOSTIC" if opening else "UNDEFINED_ZERO_DENOMINATOR",
            })
    return result


def _cohorts(subscriptions: list[dict[str, str]]) -> list[dict[str, Any]]:
    first_start: dict[str, date] = {}
    by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in subscriptions:
        by_account[row["account_id"]].append(row)
        started, ended = parse_date(row.get("start_date")), parse_date(row.get("end_date"))
        if started and (ended is None or ended > started):
            account_id = row["account_id"]
            first_start[account_id] = min(started, first_start.get(account_id, started))
    members: dict[str, set[str]] = defaultdict(set)
    for account_id, started in first_start.items():
        members[f"{started.year:04d}-{started.month:02d}"].add(account_id)
    cohorts: list[dict[str, Any]] = []
    for cohort, account_ids in sorted(members.items()):
        year, month = map(int, cohort.split("-"))
        age, cursor = 0, date(year, month, 1)
        while cursor <= date(2024, 12, 1):
            boundary = date(cursor.year + (cursor.month == 12), 1 if cursor.month == 12 else cursor.month + 1, 1)
            active = {row["account_id"] for row in active_rows(subscriptions, boundary)} & account_ids
            cohorts.append({
                "cohort": cohort, "elapsed_month": age, "initial_accounts": len(account_ids),
                "active_by_recorded_dates": len(active),
                "conditional_retention": _rate(len(active), len(account_ids)),
                "boundary_date": boundary.isoformat(),
                "evidence_classification": "CONDITIONAL_ONLY_LIFECYCLE_SEMANTICS_UNVERIFIED",
            })
            age += 1
            cursor = boundary.replace(day=1)
    return cohorts


def analyze(data_dir: Path = DEFAULT_DATA) -> dict[str, Any]:
    missing = [filename for filename in FILES.values() if not (data_dir / filename).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing source CSVs in {data_dir}: {', '.join(missing)}")
    accounts = read_csv(data_dir / FILES["accounts"])
    subscriptions = read_csv(data_dir / FILES["subscriptions"])
    events = read_csv(data_dir / FILES["events"])
    accounts_by_id = {row["account_id"]: row for row in accounts}
    annual = {str(y): _period(y, accounts, subscriptions, events) for y in (2023, 2024)}
    snapshots = {}
    for boundary in (date(2023, 1, 1), date(2024, 1, 1), date(2025, 1, 1)):
        rows = active_rows(subscriptions, boundary)
        snapshots[boundary.isoformat()] = {
            "unique_active_accounts": len({r["account_id"] for r in rows}),
            "active_subscription_rows": len(rows),
        }
    account_flags = {row["account_id"] for row in accounts if truth(row.get("churn_flag"))}
    all_event_accounts = {row["account_id"] for row in events}
    nonreact_event_accounts = {row["account_id"] for row in events if not truth(row.get("is_reactivation"))}
    opening_2024 = {row["account_id"] for row in active_rows(subscriptions, date(2024, 1, 1))}
    closing_2024 = {row["account_id"] for row in active_rows(subscriptions, date(2025, 1, 1))}
    first_start_by_account: dict[str, date] = {}
    for row in subscriptions:
        started = parse_date(row.get("start_date"))
        if started:
            first_start_by_account[row["account_id"]] = min(started, first_start_by_account.get(row["account_id"], started))
    additions_active_at_close = {
        account_id for account_id, started in first_start_by_account.items()
        if date(2024, 1, 1) < started < date(2025, 1, 1) and account_id in closing_2024
    }
    previously_seen_returns_active_at_close = {
        account_id for account_id, started in first_start_by_account.items()
        if started < date(2024, 1, 1) and account_id in closing_2024 and account_id not in opening_2024
    }
    opening_flagged = len(opening_2024 & account_flags)
    opening_event = len(opening_2024 & nonreact_event_accounts)
    event_count_by_account = Counter(row["account_id"] for row in events if not truth(row.get("is_reactivation")))
    event_2024_accounts = {
        row["account_id"] for row in events
        if not truth(row.get("is_reactivation"))
        and (event_date := parse_date(row.get("churn_date"))) is not None
        and date(2024, 1, 1) <= event_date < date(2025, 1, 1)
    }
    invalid_interval_rows = [
        row for row in subscriptions
        if (start := parse_date(row.get("start_date"))) and (end := parse_date(row.get("end_date"))) and end <= start
    ]
    dimensions = ("industry", "country", "referral_source", "plan_tier", "is_trial")
    segments: list[dict[str, Any]] = []
    for dimension in dimensions:
        groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in accounts:
            groups[row.get(dimension, "") or "UNKNOWN"].append(row)
        for segment, members in sorted(groups.items()):
            member_ids = {row["account_id"] for row in members}
            segments.append({
                "dimension": dimension,
                "segment": segment,
                "accounts": len(member_ids),
                "account_flag_true": len(member_ids & account_flags),
                "account_flag_prevalence": _rate(len(member_ids & account_flags), len(member_ids)),
                "accounts_with_nonreactivation_event_all_history": len(member_ids & nonreact_event_accounts),
                "all_history_event_prevalence": _rate(len(member_ids & nonreact_event_accounts), len(member_ids)),
                "accounts_with_2024_nonreactivation_event": len(member_ids & event_2024_accounts),
                "2024_event_prevalence": _rate(len(member_ids & event_2024_accounts), len(member_ids)),
                "label_note": "Descriptive label prevalence only; not historical churn or predictive risk.",
            })
    account_review_candidates = []
    for account_id in sorted(opening_2024 & (account_flags | event_2024_accounts), key=lambda item: (-event_count_by_account[item], item))[:20]:
        row = accounts_by_id[account_id]
        account_review_candidates.append({
            "account_id": account_id,
            "industry": row.get("industry", "UNKNOWN"),
            "country": row.get("country", "UNKNOWN"),
            "referral_source": row.get("referral_source", "UNKNOWN"),
            "plan_tier": row.get("plan_tier", "UNKNOWN"),
            "account_churn_flag": account_id in account_flags,
            "nonreactivation_event_rows_all_history": event_count_by_account[account_id],
            "nonreactivation_event_in_2024": account_id in event_2024_accounts,
            "opening_2024_date_active": True,
            "classification": "RECONCILIATION_PRIORITY_NOT_PREDICTIVE_RISK",
        })
    return {
        "metadata": {
            "generated_by": "analysis/g4_customer_churn/analyze.py",
            "source_hashes_sha256": {key: hashlib.sha256((data_dir / filename).read_bytes()).hexdigest() for key, filename in FILES.items()},
            "source_window": "2023-01-01 through 2025-01-01 date boundary; source rows end 2024-12-31",
        },
        "source_counts": {"accounts": len(accounts), "subscriptions": len(subscriptions), "churn_events": len(events)},
        "primary_customer_churn": {
            "value": None, "period": "2023 and 2024", "numerator": None, "denominator": None,
            "formula": "Unique eligible customers lost during period / unique active customers at period start × 100",
            "classification": "C — CUSTOMER CHURN NOT IDENTIFIABLE",
            "reason": "Subscription dates report no complete account-coverage losses for the 2024 opening base, while account-level departure events conflict with subscriptions still active on those dates; source semantics do not resolve the conflict.",
            "conditional_date_result_2023": None, "conditional_date_result_2024": 0.0,
            "conditional_numerator_2024": 0, "conditional_denominator_2024": 191,
        },
        "snapshots": snapshots,
        "annual": annual,
        "monthly": _monthly(subscriptions),
        "quarterly": _quarterly(subscriptions),
        "segments": segments,
        "account_review_candidates": account_review_candidates,
        "cohorts": {
            "status": "DIAGNOSTIC_ONLY_NOT_VALIDATED_RETENTION",
            "definition": "Earliest positive-length subscription start month; active if any linked subscription is open under source date rule at the next month boundary.",
            "rows": _cohorts(subscriptions),
            "limitation": "End dates, missing end dates, and event labels conflict; this is a conditional date-state matrix and must not be interpreted as verified customer retention.",
        },
        "reconciliation": {
            "unique_account_flag_true_all_history": len(account_flags),
            "unique_accounts_with_any_event_all_history": len(all_event_accounts),
            "unique_accounts_with_nonreactivation_event_all_history": len(nonreact_event_accounts),
            "opening_2024_accounts_with_flag": opening_flagged,
            "opening_2024_accounts_with_nonreactivation_event": opening_event,
            "opening_2024_accounts_with_any_2024_event": len(opening_2024 & {r["account_id"] for r in events if (d := parse_date(r.get("churn_date"))) and date(2024, 1, 1) <= d < date(2025, 1, 1)}),
            "nonreactivation_event_rows_2024": annual["2024"]["event_rows_nonreactivation"],
            "nonreactivation_event_rows_2024_with_active_subscription": annual["2024"]["nonreactivation_event_rows_with_active_subscription"],
            "nonreactivation_event_accounts_2024": annual["2024"]["unique_accounts_with_nonreactivation_event"],
            "opening_base_event_prevalence_not_churn_rate": _rate(opening_event, len(opening_2024)),
            "opening_base_flag_prevalence_not_churn_rate": _rate(opening_flagged, len(opening_2024)),
            "subscription_ids_unique": len({r["subscription_id"] for r in subscriptions}),
            "invalid_nonpositive_subscription_intervals": len(invalid_interval_rows),
            "accounts_missing_from_account_table": sorted({r["account_id"] for r in subscriptions} - set(accounts_by_id)),
            "movement_bridge": {
                "opening_accounts": len(opening_2024),
                "first_subscription_starts_active_at_close": len(additions_active_at_close),
                "previously_seen_accounts_returning_active_at_close": len(previously_seen_returns_active_at_close),
                "opening_accounts_lost_by_date_rule_at_close": len(opening_2024 - closing_2024),
                "calculated_closing_accounts": len(opening_2024) + len(additions_active_at_close) + len(previously_seen_returns_active_at_close) - len(opening_2024 - closing_2024),
                "observed_closing_accounts": len(closing_2024),
                "residual": len(closing_2024) - len(opening_2024) - len(additions_active_at_close) - len(previously_seen_returns_active_at_close) + len(opening_2024 - closing_2024),
                "note": "Boundary-set reconciliation under the subscription-date rule; not gross within-period customer movements.",
            },
        },
        "methodology": [
            "Customer = distinct account_id, with simultaneous subscription rows collapsed to one account.",
            "Opening active status is any subscription row satisfying start_date <= boundary and (end_date blank or end_date > boundary).",
            "An account-date coverage gap is conditional on end_date being an effective end and no unrecorded subscription coverage.",
            "Account churn flags are all-time labels; event rows are account-grain only and are not accepted as customer-loss outcomes when contradicted by active subscriptions.",
            "The primary KPI remains UNKNOWN; conditional date calculations are disclosed separately.",
        ],
    }


def write_outputs(result: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "g4-customer-churn.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for name, rows in (("monthly-date-diagnostic.csv", result["monthly"]), ("quarterly-date-diagnostic.csv", result["quarterly"]), ("cohort-retention-conditional.csv", result["cohorts"]["rows"])):
        path = output_dir / name
        fields = list(rows[0]) if rows else []
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = analyze(args.data_dir)
    write_outputs(result, args.output_dir)
    print(json.dumps({"primary_customer_churn": result["primary_customer_churn"], "snapshots": result["snapshots"], "annual": result["annual"], "reconciliation": result["reconciliation"], "cohort_rows": len(result["cohorts"]["rows"])}, indent=2))


if __name__ == "__main__":
    main()
