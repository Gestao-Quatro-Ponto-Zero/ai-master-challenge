#!/usr/bin/env python3
"""Reconstruct date-based customer and subscription churn, with explicit caveats.

The source schema describes a blank subscription end_date as active and a
nonblank end_date as ended. Results are therefore conditional on that
interpretation; event/flag disagreement is reported, never silently resolved.
Only the Python standard library is required.
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
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def load_sources(data_dir: Path) -> dict[str, list[dict[str, str]]]:
    missing = [name for name in FILES.values() if not (data_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing source CSV files in {data_dir}: {', '.join(missing)}")
    return {key: read_rows(data_dir / filename) for key, filename in FILES.items()}


def active_subscription_rows(subscriptions: list[dict[str, str]], when: date) -> list[dict[str, str]]:
    """Apply source-documented [start_date, end_date) lifecycle semantics."""
    result = []
    for row in subscriptions:
        start, end = parse_date(row.get("start_date")), parse_date(row.get("end_date"))
        if start is not None and start <= when and (end is None or end > when):
            result.append(row)
    return result


def _merged_intervals(rows: list[dict[str, str]], start: date, stop: date) -> list[tuple[date, date]]:
    intervals = []
    for row in rows:
        lo, hi = parse_date(row.get("start_date")), parse_date(row.get("end_date"))
        if lo is None or (hi is not None and hi <= lo) or lo >= stop or (hi is not None and hi <= start):
            continue
        intervals.append((max(lo, start), min(hi or stop, stop)))
    intervals.sort()
    merged: list[list[date]] = []
    for lo, hi in intervals:
        if not merged or lo > merged[-1][1]:
            merged.append([lo, hi])
        elif hi > merged[-1][1]:
            merged[-1][1] = hi
    return [(lo, hi) for lo, hi in merged]


def _annual_record(year: int, accounts: list[dict[str, str]], subscriptions: list[dict[str, str]], events: list[dict[str, str]]) -> dict[str, Any]:
    start, stop = date(year, 1, 1), date(year + 1, 1, 1)
    opening_rows, closing_rows = active_subscription_rows(subscriptions, start), active_subscription_rows(subscriptions, stop)
    opening = {r["account_id"] for r in opening_rows}
    closing = {r["account_id"] for r in closing_rows}
    subs_by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in subscriptions:
        subs_by_account[row["account_id"]].append(row)
    first_start: dict[str, date] = {}
    for row in subscriptions:
        value = parse_date(row.get("start_date"))
        if value is not None and (row["account_id"] not in first_start or value < first_start[row["account_id"]]):
            first_start[row["account_id"]] = value
    observed_first_start = {account for account, value in first_start.items() if start <= value < stop}
    first_observed_acquisitions_active_at_close = {
        account for account in observed_first_start & closing if account not in opening and first_start[account] > start
    }


    first_start_cohort_active_at_close = observed_first_start & closing
    first_start_cohort_inactive_at_close = observed_first_start - closing
    boundary_starts_at_close = {
        account for account, value in first_start.items() if value == stop and account in closing
    }
    date_inferred_reactivations = {
        account for account in (closing - opening)
        if first_start.get(account, stop) < start
        and any((d := parse_date(row.get("start_date"))) is not None and start < d < stop for row in subs_by_account[account])
    }

    gross_exits: set[str] = set()
    reactivated: set[str] = set()
    for account in opening:
        intervals = _merged_intervals(subs_by_account[account], start, stop)
        # Opening eligibility implies at least one interval starts at/before start.
        has_gap = (
            not intervals
            or intervals[0][0] > start
            or any(intervals[index][0] > intervals[index - 1][1] for index in range(1, len(intervals)))
            or intervals[-1][1] < stop
        )
        if has_gap:
            gross_exits.add(account)
            if intervals and intervals[-1][1] == stop:
                reactivated.add(account)

    end_lost = opening - closing
    annual_events = []
    subscription_end_rows = []
    for row in subscriptions:
        end_date = parse_date(row.get("end_date"))
        if end_date is not None and start <= end_date < stop:
            subscription_end_rows.append(row)
    for row in events:
        event_date = parse_date(row.get("churn_date"))
        if event_date is not None and start <= event_date < stop:
            annual_events.append(row)
    nonreact_accounts = {r["account_id"] for r in annual_events if not truth(r.get("is_reactivation"))}
    reactivation_marked_accounts = {r["account_id"] for r in annual_events if truth(r.get("is_reactivation"))}
    flag_true = {r["account_id"] for r in accounts if truth(r.get("churn_flag"))}
    opening_flagged = opening & flag_true
    opening_nonreact_event = opening & nonreact_accounts

    opening_sub_ids = {r["subscription_id"] for r in opening_rows}
    opening_sub_flagged = sum(truth(r.get("churn_flag")) for r in opening_rows)
    closing_sub_ids = {r["subscription_id"] for r in closing_rows}
    ended_opening_subs = opening_sub_ids - closing_sub_ids
    denominator = len(opening)
    return {
        "year": year,
        "date_rule": "start_date <= snapshot_date and (end_date is null or end_date > snapshot_date)",
        "interval_semantics": "[start_date, end_date); blank end_date treated as open-ended per source README",
        "opening_accounts": len(opening),
        "opening_subscription_rows": len(opening_rows),
        "closing_accounts": len(closing),
        "closing_subscription_rows": len(closing_rows),
        "accounts_first_subscription_started_during_year": len(observed_first_start),
        "first_subscription_cohort_active_at_year_end": len(first_start_cohort_active_at_close),
        "first_subscription_cohort_inactive_at_year_end": len(first_start_cohort_inactive_at_close),
        "first_observed_acquisitions_active_at_year_end": len(first_observed_acquisitions_active_at_close),
        "accounts_starting_exactly_at_closing_boundary": len(boundary_starts_at_close),
        "date_inferred_reactivations_active_at_year_end": len(date_inferred_reactivations),
        "gross_opening_account_exits_any_gap": len(gross_exits),
        "reactivated_opening_accounts_after_gap": len(reactivated),
        "opening_accounts_inactive_at_year_end": len(end_lost),
        "classical_logo_churn_rate_gross_exit": (len(gross_exits) / denominator) if denominator else None,
        "classical_logo_churn_rate_year_end_lost": (len(end_lost) / denominator) if denominator else None,
        "opening_subscription_ids": len(opening_sub_ids),
        "opening_subscriptions_with_churn_flag": opening_sub_flagged,
        "subscription_end_rows_during_year": len(subscription_end_rows),
        "opening_subscriptions_not_active_at_year_end": len(ended_opening_subs),
        "subscription_churn_rate_opening_cohort": (len(ended_opening_subs) / len(opening_sub_ids)) if opening_sub_ids else None,
        "event_rows": len(annual_events),
        "reactivation_marked_event_rows": sum(truth(r.get("is_reactivation")) for r in annual_events),
        "event_accounts_any": len({r["account_id"] for r in annual_events}),
        "nonreactivation_event_accounts": len(nonreact_accounts),
        "reactivation_marked_event_accounts": len(reactivation_marked_accounts),
        "opening_accounts_with_account_churn_flag": len(opening_flagged),
        "opening_accounts_with_nonreactivation_event": len(opening_nonreact_event),
        "opening_accounts_with_reactivation_marked_event": len(opening & reactivation_marked_accounts),
        "movement_equation": {
            "opening": len(opening),
            "first_observed_new": len(first_observed_acquisitions_active_at_close),
            "reactivated_previously_seen": len(date_inferred_reactivations),
            "lost_at_year_end": len(end_lost),
            "boundary_starts_at_close": len(boundary_starts_at_close),
            "calculated_closing": len(opening) + len(first_observed_acquisitions_active_at_close) + len(date_inferred_reactivations) + len(boundary_starts_at_close) - len(end_lost),
            "observed_closing": len(closing),
            "residual": len(closing) - (len(opening) + len(first_observed_acquisitions_active_at_close) + len(date_inferred_reactivations) + len(boundary_starts_at_close) - len(end_lost)),
            "note": "Flow identity includes distinct first-observed additions active at close, prior-history returns active at close, date-boundary starts, and opening accounts inactive at close. It does not count within-period transient flows.",
        },
        "evidence_status": "CONDITIONAL_DATE_RECONSTRUCTION" if denominator else "UNDEFINED_ZERO_OPENING_BASE",
        "assumptions": [
            "end_date is treated as effective relationship termination, per source README; this is not independently verified.",
            "A logo is active when any linked subscription row is active; 1:N rows are collapsed to distinct account_id.",
            "Invalid non-positive subscription intervals are excluded from interval continuity; they remain counted in source QA.",
            "This is not a verified finance or customer-success churn KPI because event and flag definitions materially disagree.",
        ],
    }


def _monthly_series(subscriptions: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Calculate distinct-logo and subscription exit rates by month boundary."""
    subs_by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in subscriptions:
        subs_by_account[row["account_id"]].append(row)
    result = []
    year, month = 2023, 1
    while (year, month) <= (2024, 12):
        start = date(year, month, 1)
        stop = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
        opening_rows = active_subscription_rows(subscriptions, start)
        closing_rows = active_subscription_rows(subscriptions, stop)
        opening = {r["account_id"] for r in opening_rows}
        closing = {r["account_id"] for r in closing_rows}
        exits, reactivations = set(), set()
        for account in opening:
            intervals = _merged_intervals(subs_by_account[account], start, stop)
            has_gap = (
                not intervals
                or intervals[0][0] > start
                or any(intervals[index][0] > intervals[index - 1][1] for index in range(1, len(intervals)))
                or intervals[-1][1] < stop
            )
            if has_gap:
                exits.add(account)
                if intervals and intervals[-1][1] == stop:
                    reactivations.add(account)
        opening_ids = {r["subscription_id"] for r in opening_rows}
        closing_ids = {r["subscription_id"] for r in closing_rows}
        result.append({
            "month": f"{year:04d}-{month:02d}",
            "opening_accounts": len(opening),
            "gross_logo_exits_any_interval_gap": len(exits),
            "accounts_reactivated_after_gap": len(reactivations),
            "closing_accounts": len(closing),
            "logo_churn_rate": len(exits) / len(opening) if opening else None,
            "opening_subscriptions": len(opening_ids),
            "opening_subscriptions_not_active_at_next_boundary": len(opening_ids - closing_ids),
            "subscription_churn_rate": len(opening_ids - closing_ids) / len(opening_ids) if opening_ids else None,
            "evidence_status": "CONDITIONAL_DATE_RECONSTRUCTION" if opening else "UNDEFINED_ZERO_OPENING_BASE",
        })
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return result


def reconstruct(data_dir: Path = DEFAULT_DATA) -> dict[str, Any]:
    sources = load_sources(data_dir)
    accounts, subscriptions, events = sources["accounts"], sources["subscriptions"], sources["events"]
    accounts_by_id = {r["account_id"]: r for r in accounts}
    subs_by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in subscriptions:
        subs_by_account[row["account_id"]].append(row)
    invalid_intervals = [r for r in subscriptions if parse_date(r.get("start_date")) and parse_date(r.get("end_date")) and parse_date(r["end_date"]) <= parse_date(r["start_date"])]
    duplicate_subscription_ids = {k: n for k, n in Counter(r["subscription_id"] for r in subscriptions).items() if n > 1}
    duplicate_accounts = {k: n for k, n in Counter(r["account_id"] for r in subscriptions).items() if n > 1}
    snapshot_dates = [date(2023, 1, 1), date(2024, 1, 1), date(2025, 1, 1)]
    snapshots = {}
    for snap in snapshot_dates:
        active = active_subscription_rows(subscriptions, snap)
        snapshots[snap.isoformat()] = {
            "active_accounts": len({r["account_id"] for r in active}),
            "active_subscription_rows": len(active),
            "accounts_with_multiple_active_subscription_rows": sum(n > 1 for n in Counter(r["account_id"] for r in active).values()),
        }
    annual = {str(year): _annual_record(year, accounts, subscriptions, events) for year in (2023, 2024)}

    # Cohort retention uses first valid subscription start and any active linked
    # subscription at the month boundary. This is a conditional reconstruction,
    # not an event-reconciled or observed contractual retention series.
    valid_subscriptions = [r for r in subscriptions if parse_date(r.get("start_date")) and (parse_date(r.get("end_date")) is None or parse_date(r["end_date"]) > parse_date(r["start_date"]))]
    first_valid: dict[str, date] = {}
    for row in valid_subscriptions:
        d = parse_date(row["start_date"])
        if row["account_id"] not in first_valid or d < first_valid[row["account_id"]]:
            first_valid[row["account_id"]] = d
    cohort_members: dict[str, set[str]] = defaultdict(set)
    for account, d in first_valid.items():
        cohort_members[f"{d.year:04d}-{d.month:02d}"].add(account)
    retention: list[dict[str, Any]] = []
    for cohort, members in sorted(cohort_members.items()):
        y, m = map(int, cohort.split("-"))
        age, month = 0, date(y, m, 1)
        while month <= date(2024, 12, 1):
            boundary = date(month.year + (month.month == 12), 1 if month.month == 12 else month.month + 1, 1)
            active = active_subscription_rows(subscriptions, boundary)
            active_accounts = {r["account_id"] for r in active} & members
            retention.append({"cohort": cohort, "elapsed_month": age, "initial_accounts": len(members), "active_accounts": len(active_accounts), "retention_rate": len(active_accounts) / len(members) if members else None, "snapshot_date": boundary.isoformat()})
            age += 1
            month = boundary.replace(day=1)
    latest_by_cohort = {}
    for row in retention:
        latest_by_cohort[row["cohort"]] = row

    event_vs_date = {}
    for year in (2023, 2024):
        start, stop = date(year, 1, 1), date(year + 1, 1, 1)
        rows = [r for r in events if (d := parse_date(r.get("churn_date"))) is not None and start <= d < stop and not truth(r.get("is_reactivation"))]
        event_active = 0
        for row in rows:
            event_date = parse_date(row["churn_date"])
            if any(parse_date(s["start_date"]) is not None and parse_date(s["start_date"]) <= event_date and (parse_date(s.get("end_date")) is None or parse_date(s["end_date"]) > event_date) for s in subs_by_account.get(row["account_id"], [])):
                event_active += 1
        event_vs_date[str(year)] = {"nonreactivation_event_rows": len(rows), "rows_during_any_date_active_subscription": event_active, "rows_without_any_date_active_subscription": len(rows) - event_active}

    return {
        "metadata": {
            "generated_by": "analysis/historical_churn/reconstruct.py",
            "source_dir": "data/raw",
            "source_hashes_sha256": {key: hashlib.sha256((data_dir / filename).read_bytes()).hexdigest() for key, filename in FILES.items()},
            "latest_source_dates": {
                "subscription_start": max((parse_date(r.get("start_date")) for r in subscriptions if parse_date(r.get("start_date"))), default=None).isoformat() if subscriptions else None,
                "subscription_end": max((parse_date(r.get("end_date")) for r in subscriptions if parse_date(r.get("end_date"))), default=None).isoformat() if subscriptions else None,
                "churn_event": max((parse_date(r.get("churn_date")) for r in events if parse_date(r.get("churn_date"))), default=None).isoformat() if events else None,
            },
        },
        "source_counts": {"accounts": len(accounts), "subscriptions": len(subscriptions), "churn_events": len(events)},
        "snapshots": snapshots,
        "annual": annual,
        "monthly": _monthly_series(subscriptions),
        "cohorts": {
            "definition": "First valid subscription start month; active if any linked subscription spans the month-end boundary; conditional on recorded date semantics.",
            "status": "CONDITIONAL_DATE_RECONSTRUCTION",
            "rows": retention,
            "latest_by_cohort": list(latest_by_cohort.values()),
            "diagnostic": {
                "cohort_count": len(cohort_members),
                "cohort_month_points": len(retention),
                "points_below_100_percent": sum(row["retention_rate"] < 1 for row in retention),
                "minimum_date_rule_retention": min((row["retention_rate"] for row in retention), default=None),
                "latest_boundary_all_cohorts_active": all(row["retention_rate"] == 1 for row in latest_by_cohort.values()),
                "interim_gaps": [row for row in retention if row["retention_rate"] < 1],
            },
        },
        "event_date_conflicts": event_vs_date,
        "data_quality": {
            "unique_subscription_ids": len({r["subscription_id"] for r in subscriptions}),
            "duplicate_subscription_id_groups": len(duplicate_subscription_ids),
            "duplicate_subscription_id_group_rows": sum(duplicate_subscription_ids.values()),
            "duplicate_subscription_id_excess_rows": sum(n - 1 for n in duplicate_subscription_ids.values()),
            "accounts_with_multiple_subscription_rows": len(duplicate_accounts),
            "invalid_nonpositive_subscription_intervals": len(invalid_intervals),
            "invalid_interval_account_ids": sorted({r["account_id"] for r in invalid_intervals}),
            "account_flags_true": sum(truth(r.get("churn_flag")) for r in accounts),
            "accounts_with_any_event": len({r["account_id"] for r in events}),
            "accounts_with_nonreactivation_event": len({r["account_id"] for r in events if not truth(r.get("is_reactivation"))}),
            "accounts_with_subscription_churn_flag": len({r["account_id"] for r in subscriptions if truth(r.get("churn_flag"))}),
            "accounts_missing_account_row": sorted({r["account_id"] for r in subscriptions if r["account_id"] not in accounts_by_id}),
            "source_semantics": "Source README: blank end_date means active; subscription churn_flag means ended; account churn_flag means churned at any point; event churn_date described as when account left.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA, help="Directory containing original source CSV files (default: package data/raw).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT, help="Directory for generated JSON output (default: this module's outputs/).")
    args = parser.parse_args()
    result = reconstruct(args.data_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    target = args.output_dir / "historical-churn.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (args.output_dir / "annual-reconciliation.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["year", "opening_accounts", "accounts_first_subscription_started_during_year", "first_subscription_cohort_active_at_year_end", "first_subscription_cohort_inactive_at_year_end", "first_observed_acquisitions_active_at_year_end", "date_inferred_reactivations_active_at_year_end", "accounts_starting_exactly_at_closing_boundary", "gross_opening_account_exits_any_gap", "opening_accounts_inactive_at_year_end", "closing_accounts", "classical_logo_churn_rate_gross_exit", "opening_subscription_rows", "opening_subscriptions_with_churn_flag", "opening_subscriptions_not_active_at_year_end", "subscription_churn_rate_opening_cohort", "subscription_end_rows_during_year", "event_rows", "opening_accounts_with_nonreactivation_event", "opening_accounts_with_account_churn_flag", "movement_equation_residual"])
        writer.writeheader()
        for item in result["annual"].values():
            writer.writerow({
                "year": item["year"], "opening_accounts": item["opening_accounts"],
                "accounts_first_subscription_started_during_year": item["accounts_first_subscription_started_during_year"],
                "first_subscription_cohort_active_at_year_end": item["first_subscription_cohort_active_at_year_end"],
                "first_subscription_cohort_inactive_at_year_end": item["first_subscription_cohort_inactive_at_year_end"],
                "date_inferred_reactivations_active_at_year_end": item["date_inferred_reactivations_active_at_year_end"],
                "accounts_starting_exactly_at_closing_boundary": item["accounts_starting_exactly_at_closing_boundary"],
                "gross_opening_account_exits_any_gap": item["gross_opening_account_exits_any_gap"],
                "opening_accounts_inactive_at_year_end": item["opening_accounts_inactive_at_year_end"],
                "closing_accounts": item["closing_accounts"],
                "classical_logo_churn_rate_gross_exit": item["classical_logo_churn_rate_gross_exit"],
                "opening_subscription_rows": item["opening_subscription_rows"],
                "opening_subscriptions_with_churn_flag": item["opening_subscriptions_with_churn_flag"],
                "opening_subscriptions_not_active_at_year_end": item["opening_subscriptions_not_active_at_year_end"],
                "subscription_end_rows_during_year": item["subscription_end_rows_during_year"],
                "subscription_churn_rate_opening_cohort": item["subscription_churn_rate_opening_cohort"],
                "event_rows": item["event_rows"],
                "opening_accounts_with_nonreactivation_event": item["opening_accounts_with_nonreactivation_event"],
                "opening_accounts_with_account_churn_flag": item["opening_accounts_with_account_churn_flag"],
                "movement_equation_residual": item["movement_equation"]["residual"],
            })
    with (args.output_dir / "cohort-retention-conditional.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["cohort", "elapsed_month", "initial_accounts", "active_accounts", "retention_rate", "snapshot_date"])
        writer.writeheader()
        writer.writerows(result["cohorts"]["rows"])
    with (args.output_dir / "monthly-reconstruction.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result["monthly"][0]))
        writer.writeheader()
        writer.writerows(result["monthly"])
    print(f"Wrote {target}")
    print(json.dumps({"snapshots": result["snapshots"], "annual": result["annual"], "event_date_conflicts": result["event_date_conflicts"], "cohort_latest": result["cohorts"]["latest_by_cohort"]}, indent=2))


if __name__ == "__main__":
    main()
