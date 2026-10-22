#!/usr/bin/env python3
"""Reconcile 2024 opening subscriptions and account-level churn events.

Only source-observable associations are produced. Churn-event rows link to
accounts, not subscriptions, so the module never assigns an event to a contract.
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
SNAPSHOT_START = date(2024, 1, 1)
SNAPSHOT_END = date(2025, 1, 1)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def active(row: dict[str, str], when: date) -> bool:
    start, end = parse_date(row.get("start_date")), parse_date(row.get("end_date"))
    return bool(start and start <= when and (end is None or end > when))


def _intervals(rows: list[dict[str, str]], begin: date, end: date) -> list[tuple[date, date]]:
    spans: list[tuple[date, date]] = []
    for row in rows:
        start, stop = parse_date(row.get("start_date")), parse_date(row.get("end_date"))
        if start is None or (stop is not None and stop <= start):
            continue
        lo, hi = max(start, begin), min(stop or end, end)
        if lo < hi:
            spans.append((lo, hi))
    spans.sort()
    merged: list[list[date]] = []
    for lo, hi in spans:
        if not merged or lo > merged[-1][1]:
            merged.append([lo, hi])
        elif hi > merged[-1][1]:
            merged[-1][1] = hi
    return [(lo, hi) for lo, hi in merged]


def _covered_all_year(rows: list[dict[str, str]]) -> bool:
    spans = _intervals(rows, SNAPSHOT_START, SNAPSHOT_END)
    return bool(spans and spans[0][0] == SNAPSHOT_START and spans[-1][1] == SNAPSHOT_END
                and all(spans[i][0] <= spans[i - 1][1] for i in range(1, len(spans))))


def _nearest_delta(event_date: date, ends: list[date]) -> int | None:
    return min((abs((event_date - end_date).days) for end_date in ends), default=None)


def _nearest_end(event_date: date, ends: list[date]) -> date | None:
    return min(ends, key=lambda end_date: abs((event_date - end_date).days), default=None)


def investigate(data_dir: Path = DEFAULT_DATA) -> dict[str, Any]:
    files = {
        "accounts": "ravenstack_accounts.csv",
        "subscriptions": "ravenstack_subscriptions.csv",
        "events": "ravenstack_churn_events.csv",
    }
    for filename in files.values():
        if not (data_dir / filename).is_file():
            raise FileNotFoundError(f"Missing required source: {data_dir / filename}")
    accounts = read_csv(data_dir / files["accounts"])
    subscriptions = read_csv(data_dir / files["subscriptions"])
    events = read_csv(data_dir / files["events"])
    account_by_id = {row["account_id"]: row for row in accounts}
    subs_by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in subscriptions:
        subs_by_account[row["account_id"]].append(row)

    opening_rows = [row for row in subscriptions if active(row, SNAPSHOT_START)]
    opening_ids = {row["subscription_id"] for row in opening_rows}
    opening_accounts = {row["account_id"] for row in opening_rows}
    ended = [row for row in opening_rows if row.get("end_date") and parse_date(row["end_date"]) is not None
             and parse_date(row["end_date"]) < SNAPSHOT_END]
    ended_accounts = {row["account_id"] for row in ended}
    annual_events = [row for row in events if (d := parse_date(row.get("churn_date"))) and SNAPSHOT_START <= d < SNAPSHOT_END]
    nonreact_events = [row for row in annual_events if not truth(row.get("is_reactivation"))]

    ended_inventory: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    financial_mrr = []
    financial_arr = []
    for row in sorted(ended, key=lambda item: (item["account_id"], item["subscription_id"])):
        aid = row["account_id"]
        end_date = parse_date(row.get("end_date"))
        peers = [other for other in subs_by_account[aid] if other["subscription_id"] != row["subscription_id"]]
        active_at_termination = [other for other in peers if end_date and active(other, end_date)]
        later_subs = [other for other in peers if (start := parse_date(other.get("start_date"))) and end_date and start > end_date]
        successor_or_replacement = [other for other in peers if end_date and (start := parse_date(other.get("start_date"))) and start >= end_date]
        account_rows = subs_by_account[aid]
        covered_all_year = _covered_all_year(account_rows)
        account_active_close = any(active(other, SNAPSHOT_END) for other in account_rows)
        any_active_at_end = bool(active_at_termination)
        nearest_successor_gap = min(
            ((parse_date(other["start_date"]) - end_date).days for other in successor_or_replacement
             if end_date and parse_date(other.get("start_date")) is not None), default=None)
        if any_active_at_end:
            primary = "other_subscription_active_at_termination"
        elif later_subs:
            primary = "later_subscription_after_gap"
        elif not account_active_close:
            primary = "no_successor_account_inactive_at_close"
        else:
            primary = "account_active_close_successor_timing_ambiguous"
        class_counts[primary] += 1
        if row.get("mrr_amount") not in (None, ""):
            financial_mrr.append(float(row["mrr_amount"]))
        if row.get("arr_amount") not in (None, ""):
            financial_arr.append(float(row["arr_amount"]))
        account = account_by_id.get(aid, {})
        related_events = [event for event in annual_events if event["account_id"] == aid]
        ended_inventory.append({
            "subscription_id": row["subscription_id"], "account_id": aid,
            "start_date": row.get("start_date"), "end_date": row.get("end_date"),
            "plan_tier": row.get("plan_tier"), "billing_frequency": row.get("billing_frequency"),
            "seats": _int(row.get("seats")), "mrr_amount_recorded": _float(row.get("mrr_amount")),
            "arr_amount_recorded": _float(row.get("arr_amount")), "subscription_churn_flag": truth(row.get("churn_flag")),
            "upgrade_flag": truth(row.get("upgrade_flag")), "downgrade_flag": truth(row.get("downgrade_flag")),
            "account_churn_flag": truth(account.get("churn_flag")), "account_plan_tier": account.get("plan_tier"),
            "industry": account.get("industry"), "country": account.get("country"), "referral_source": account.get("referral_source"),
            "account_subscription_rows": len(account_rows), "account_other_subscriptions": len(peers),
            "account_initial_plan_differs_from_ended_contract": bool(account.get("plan_tier") and row.get("plan_tier") and account.get("plan_tier") != row.get("plan_tier")),
            "account_observed_subscription_plan_tiers": sorted({other.get("plan_tier", "") for other in account_rows if other.get("plan_tier")}),
            "account_observed_subscription_seat_values": sorted({_int(other.get("seats")) for other in account_rows if _int(other.get("seats")) is not None}),
            "other_subscription_active_at_termination": any_active_at_end,
            "other_active_subscription_ids_at_termination": [other["subscription_id"] for other in active_at_termination],
            "later_subscriptions_after_termination": [other["subscription_id"] for other in later_subs],
            "successor_candidate_ids_unconfirmed": [other["subscription_id"] for other in successor_or_replacement],
            "nearest_successor_gap_days": nearest_successor_gap,
            "account_coverage_continuous_during_2024": covered_all_year,
            "account_active_2025_01_01_by_date": account_active_close,
            "annual_account_event_rows": len(related_events),
            "annual_account_nonreactivation_event_rows": sum(not truth(event.get("is_reactivation")) for event in related_events),
            "annual_account_reactivation_marked_rows": sum(truth(event.get("is_reactivation")) for event in related_events),
            "exclusive_case_class": primary,
            "classification_note": "Observed record pattern only; successor does not prove migration, replacement, or commercial continuity.",
        })

    ending_accounts = {row["account_id"] for row in subscriptions if active(row, SNAPSHOT_END)}
    account_case_matrix = []
    for aid in sorted(opening_accounts):
        rows = subs_by_account[aid]
        a = account_by_id.get(aid, {})
        evs = [row for row in annual_events if row["account_id"] == aid]
        account_case_matrix.append({
            "account_id": aid, "account_churn_flag": truth(a.get("churn_flag")),
            "any_subscription_churn_flag": any(truth(row.get("churn_flag")) for row in rows),
            "any_2024_event": bool(evs), "any_2024_nonreactivation_event": any(not truth(e.get("is_reactivation")) for e in evs),
            "any_2024_reactivation_marked_event": any(truth(e.get("is_reactivation")) for e in evs),
            "any_subscription_end_2024": any((d := parse_date(r.get("end_date"))) and SNAPSHOT_START <= d < SNAPSHOT_END for r in rows),
            "complete_2024_coverage_by_date": _covered_all_year(rows),
            "active_at_2025_01_01_by_date": aid in ending_accounts,
            "subscription_rows": len(rows),
            "nonreactivation_event_rows": sum(not truth(e.get("is_reactivation")) for e in evs),
        })

    end_dates_by_account: dict[str, list[date]] = defaultdict(list)
    for row in subscriptions:
        end_date = parse_date(row.get("end_date"))
        if end_date and SNAPSHOT_START <= end_date < SNAPSHOT_END:
            end_dates_by_account[row["account_id"]].append(end_date)

    conflict_inventory: list[dict[str, Any]] = []
    reason_groups: dict[str, Counter[str]] = defaultdict(Counter)
    segment_groups: dict[str, Counter[str]] = defaultdict(Counter)
    segment_conflict_accounts: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    window_totals = {days: 0 for days in (0, 7, 30, 60)}
    for row in sorted(nonreact_events, key=lambda item: (item.get("churn_date", ""), item["churn_event_id"])):
        aid = row["account_id"]
        event_date = parse_date(row.get("churn_date"))
        linked = subs_by_account[aid]
        active_rows = [sub for sub in linked if event_date and active(sub, event_date)]
        nearby = _nearest_delta(event_date, end_dates_by_account[aid]) if event_date else None
        nearest_end = _nearest_end(event_date, end_dates_by_account[aid]) if event_date else None
        for days in window_totals:
            if nearby is not None and nearby <= days:
                window_totals[days] += 1
        account = account_by_id.get(aid, {})
        reason = row.get("reason_code") or "(missing)"
        reason_groups[reason]["events"] += 1
        reason_groups[reason]["active_subscription_events"] += bool(active_rows)
        reason_groups[reason]["near_end_30d"] += nearby is not None and nearby <= 30
        reason_groups[reason]["active_and_near_end_30d"] += bool(active_rows) and nearby is not None and nearby <= 30
        for dimension in ("plan_tier", "industry", "country", "referral_source"):
            segment = account.get(dimension) or "(missing)"
            segment_groups[dimension][segment] += 1
            segment_groups[f"{dimension}__conflicting_active"] [segment] += bool(active_rows)
            if active_rows:
                segment_conflict_accounts[dimension][segment].add(aid)
        conflict_inventory.append({
            "churn_event_id": row["churn_event_id"], "account_id": aid, "churn_date": row.get("churn_date"),
            "reason_code": reason, "feedback_text": row.get("feedback_text") or None,
            "is_reactivation": False, "refund_amount_usd_recorded": _float(row.get("refund_amount_usd")),
            "account_churn_flag": truth(account.get("churn_flag")),
            "account_plan_tier": account.get("plan_tier"), "industry": account.get("industry"),
            "country": account.get("country"), "referral_source": account.get("referral_source"),
            "subscription_rows_for_account": len(linked), "active_subscription_count_on_event_date": len(active_rows),
            "active_subscription_ids_on_event_date": [sub["subscription_id"] for sub in active_rows],
            "same_account_subscription_end_dates_in_2024": [d.isoformat() for d in end_dates_by_account[aid]],
            "nearest_same_account_end_date": nearest_end.isoformat() if nearest_end else None,
            "nearest_end_date_difference_days": nearby,
            "event_days_after_nearest_end": (event_date - nearest_end).days if event_date and nearest_end else None,
            "within_0_days_of_end": nearby is not None and nearby <= 0,
            "within_7_days_of_end": nearby is not None and nearby <= 7,
            "within_30_days_of_end": nearby is not None and nearby <= 30,
            "within_60_days_of_end": nearby is not None and nearby <= 60,
            "event_subscription_link": "UNKNOWN: source event contains account_id only; active IDs are account-date context, not event foreign keys.",
        })

    # Keep the forensic payload scoped to the 443 actual conflicts. The 29
    # non-conflicting non-reactivation rows remain represented in period totals.
    conflict_inventory = [row for row in conflict_inventory if row["active_subscription_count_on_event_date"] > 0]

    reactivation_inventory: list[dict[str, Any]] = []
    for row in sorted((item for item in annual_events if truth(item.get("is_reactivation"))),
                      key=lambda item: (item.get("churn_date", ""), item["churn_event_id"])):
        aid = row["account_id"]
        event_date = parse_date(row.get("churn_date"))
        linked = subs_by_account[aid]
        active_rows = [sub for sub in linked if event_date and active(sub, event_date)]
        prior_ends = [parse_date(sub.get("end_date")) for sub in linked
                      if event_date and parse_date(sub.get("end_date")) and parse_date(sub.get("end_date")) <= event_date]
        later_starts = [parse_date(sub.get("start_date")) for sub in linked
                        if event_date and parse_date(sub.get("start_date")) and parse_date(sub.get("start_date")) > event_date]
        prior_nonreactivation = [item for item in events if item["account_id"] == aid
                                 and not truth(item.get("is_reactivation")) and item.get("churn_date", "") < row.get("churn_date", "")]
        account = account_by_id.get(aid, {})
        nearest_prior_end = max(prior_ends, default=None)
        reactivation_inventory.append({
            "churn_event_id": row["churn_event_id"], "account_id": aid, "churn_date": row.get("churn_date"),
            "reason_code": row.get("reason_code") or "(missing)", "feedback_text": row.get("feedback_text") or None,
            "account_churn_flag": truth(account.get("churn_flag")), "is_reactivation": True,
            "active_subscription_count_on_event_date": len(active_rows),
            "active_subscription_ids_on_event_date": [sub["subscription_id"] for sub in active_rows],
            "prior_subscription_end_dates_for_account": [end.isoformat() for end in sorted(prior_ends)],
            "nearest_prior_end_date": nearest_prior_end.isoformat() if nearest_prior_end else None,
            "days_since_nearest_prior_end": (event_date - nearest_prior_end).days if event_date and nearest_prior_end else None,
            "later_subscription_start_dates_for_account": [start.isoformat() for start in sorted(later_starts)],
            "prior_nonreactivation_event_ids": [item["churn_event_id"] for item in prior_nonreactivation],
            "event_subscription_link": "UNKNOWN: reactivation marker is account-level; no subscription foreign key exists.",
        })
    reactivation_summary = {
        "event_rows": len(reactivation_inventory),
        "distinct_accounts": len({row["account_id"] for row in reactivation_inventory}),
        "rows_with_active_subscription_on_event_date": sum(row["active_subscription_count_on_event_date"] > 0 for row in reactivation_inventory),
        "rows_after_any_same_account_subscription_end": sum(row["nearest_prior_end_date"] is not None for row in reactivation_inventory),
        "rows_with_later_same_account_subscription_start": sum(bool(row["later_subscription_start_dates_for_account"]) for row in reactivation_inventory),
        "rows_after_prior_nonreactivation_event": sum(bool(row["prior_nonreactivation_event_ids"]) for row in reactivation_inventory),
        "distinct_accounts_in_2024_opening_base": len({row["account_id"] for row in reactivation_inventory} & opening_accounts),
        "interpretation": "Source reactivation markers are observations only; contract continuity or a prior account-level cancellation cannot be established from the marker alone.",
    }

    reason_summary = []
    for reason, counts in sorted(reason_groups.items(), key=lambda item: (-item[1]["events"], item[0])):
        reason_summary.append({"reason_code": reason, "nonreactivation_event_rows": counts["events"],
                              "events_with_active_subscription": counts["active_subscription_events"],
                              "events_with_same_account_end_within_30d": counts["near_end_30d"],
                              "conflicting_events_with_same_account_end_within_30d": counts["active_and_near_end_30d"],
                              "share_of_conflicting_443": counts["active_subscription_events"] / sum(bool(row["active_subscription_count_on_event_date"]) for row in conflict_inventory)})
    segment_summary: dict[str, list[dict[str, Any]]] = {}
    source_segment_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for account in accounts:
        for dimension in ("plan_tier", "industry", "country", "referral_source"):
            source_segment_counts[dimension][account.get(dimension) or "(missing)"] += 1
    for dim, counts in segment_groups.items():
        if dim.endswith("__conflicting_active"):
            continue
        conflicting_counts = segment_groups[f"{dim}__conflicting_active"]
        segment_summary[dim] = [{"segment": name, "accounts_in_source_segment": source_segment_counts[dim][name],
                                 "accounts_with_conflicting_event": len(segment_conflict_accounts[dim][name]),
                                 "account_share_with_conflicting_event": len(segment_conflict_accounts[dim][name]) / source_segment_counts[dim][name] if source_segment_counts[dim][name] else None,
                                 "nonreactivation_event_rows": n,
                                 "active_subscription_event_rows": conflicting_counts[name],
                                 "share_of_472_nonreactivation_rows": n / len(nonreact_events) if nonreact_events else None,
                                 "share_of_443_conflicting_events": conflicting_counts[name] / sum(bool(row["active_subscription_count_on_event_date"]) for row in conflict_inventory)}
                                for name, n in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]

    refunds = [float(row["refund_amount_usd"]) for row in annual_events if row.get("refund_amount_usd") not in (None, "")]
    unique_event_accounts = {row["account_id"] for row in nonreact_events}
    accounts_multi = {aid for aid in unique_event_accounts if any(
        len([sub for sub in subs_by_account[aid] if active(sub, parse_date(event["churn_date"]))]) > 1
        for event in nonreact_events if event["account_id"] == aid and parse_date(event.get("churn_date"))
    )}
    events_multi_active = sum(row["active_subscription_count_on_event_date"] > 1 for row in conflict_inventory)
    opening_accounts_with_gap = [row["account_id"] for row in account_case_matrix if not row["complete_2024_coverage_by_date"]]
    conflicting_rows = [row for row in conflict_inventory if row["active_subscription_count_on_event_date"] > 0]
    conflicting_window_counts = {
        f"within_{days}_days": sum(row[f"within_{days}_days_of_end"] for row in conflicting_rows)
        for days in (0, 7, 30, 60)
    }
    event_accounts_summary: dict[str, dict[str, Any]] = {}
    for row in conflict_inventory:
        item = event_accounts_summary.setdefault(row["account_id"], {
            "account_id": row["account_id"], "industry": row["industry"], "country": row["country"],
            "referral_source": row["referral_source"], "account_plan_tier": row["account_plan_tier"],
            "account_churn_flag": row["account_churn_flag"], "nonreactivation_event_rows": 0,
            "active_subscription_event_rows": 0, "event_reasons": [], "subscription_end_dates_2024": [],
        })
        item["nonreactivation_event_rows"] += 1
        item["active_subscription_event_rows"] += row["active_subscription_count_on_event_date"] > 0
        item["event_reasons"].append(row["reason_code"])
        item["subscription_end_dates_2024"] = row["same_account_subscription_end_dates_in_2024"]
    event_account_examples = sorted(event_accounts_summary.values(), key=lambda row: (-row["nonreactivation_event_rows"], row["account_id"]))[:15]
    for item in event_account_examples:
        item["event_reasons"] = dict(Counter(item["event_reasons"]))
    output = {
        "metadata": {"source": "Original synthetic Rivalytics CSV files", "period": "2024 calendar year", "date_rule": "start_date <= event_date and (end_date is null or end_date > event_date)",
                     "generated_by": "analysis/contract_churn/investigate.py", "event_join_key": "account_id only; no event-to-subscription foreign key exists",
                     "files_sha256": {key: hashlib.sha256((data_dir / filename).read_bytes()).hexdigest() for key, filename in files.items()}},
        "revalidation": {"opening_accounts": len(opening_accounts), "opening_subscription_rows": len(opening_rows),
                         "opening_subscription_ids": len(opening_ids), "subscription_rows_ended_before_2025_boundary": len(ended),
                         "distinct_accounts_in_66": len(ended_accounts), "nonreactivation_event_rows": len(nonreact_events),
                         "nonreactivation_event_accounts": len(unique_event_accounts),
                         "events_with_any_active_subscription": sum(bool(row["active_subscription_count_on_event_date"]) for row in conflict_inventory),
                         "distinct_accounts_among_events_with_active_subscription": len({row["account_id"] for row in conflicting_rows}),
                         "events_with_multiple_active_subscriptions": events_multi_active,
                         "event_accounts_with_multiple_active_subscriptions_at_least_once": len(accounts_multi),
                         "conflicting_events_near_same_account_end": conflicting_window_counts,
                         "conflicting_events_without_same_account_end_within_30d": len(conflicting_rows) - conflicting_window_counts["within_30_days"],
                         "conflicting_events_without_same_account_end_within_60d": len(conflicting_rows) - conflicting_window_counts["within_60_days"],
                         "distinct_accounts_among_66_ended_opening_subscriptions": len(ended_accounts),
                         "ended_subscriptions_with_another_active_at_end": sum(bool(row["other_subscription_active_at_termination"]) for row in ended_inventory),
                         "ended_subscriptions_with_later_subscription_start": sum(bool(row["later_subscriptions_after_termination"]) for row in ended_inventory),
                         "ended_subscriptions_with_successor_start_on_or_after_end": sum(bool(row["successor_candidate_ids_unconfirmed"]) for row in ended_inventory),
                         "ended_subscriptions_with_upgrade_flag": sum(bool(row["upgrade_flag"]) for row in ended_inventory),
                         "ended_subscriptions_with_downgrade_flag": sum(bool(row["downgrade_flag"]) for row in ended_inventory),
                         "ended_subscriptions_with_plan_different_from_account_initial_plan": sum(bool(row["account_initial_plan_differs_from_ended_contract"]) for row in ended_inventory),
                         "ended_accounts_active_at_2025_boundary": len(ended_accounts & ending_accounts),
                         "opening_accounts_with_any_2024_coverage_gap": len(opening_accounts_with_gap),
                         "opening_accounts_lost_all_coverage_at_2025_boundary": len(opening_accounts - ending_accounts)},
        "ended_subscription_class_counts": dict(class_counts),
        "ended_subscriptions": ended_inventory,
        "event_end_proximity_counts": {"all_472_nonreactivation_events": {f"within_{days}_days": count for days, count in window_totals.items()},
                                       "443_events_with_active_subscription": conflicting_window_counts},
        "event_reasons": reason_summary,
        "event_segments": segment_summary,
        "event_account_investigation_examples": event_account_examples,
        "reactivation_summary": reactivation_summary,
        "reactivation_events": reactivation_inventory,
        "account_reconciliation": {
            "opening_accounts": len(opening_accounts), "account_churn_flag_true": sum(row["account_churn_flag"] for row in account_case_matrix),
            "accounts_with_subscription_churn_flag": sum(row["any_subscription_churn_flag"] for row in account_case_matrix),
            "accounts_with_nonreactivation_event": sum(row["any_2024_nonreactivation_event"] for row in account_case_matrix),
            "accounts_with_2024_subscription_end": sum(row["any_subscription_end_2024"] for row in account_case_matrix),
            "accounts_with_any_coverage_gap": len(opening_accounts_with_gap), "accounts_active_at_boundary": sum(row["active_at_2025_01_01_by_date"] for row in account_case_matrix),
            "cross_tab": _cross_tab(account_case_matrix),
            "account_rows": account_case_matrix,
        },
        "financial_descriptives": {
            "ended_opening_subscription_mrr_rows": len(financial_mrr), "mrr_min": min(financial_mrr) if financial_mrr else None,
            "mrr_median": _median(financial_mrr), "mrr_max": max(financial_mrr) if financial_mrr else None,
            "ended_opening_subscription_arr_rows": len(financial_arr), "arr_min": min(financial_arr) if financial_arr else None,
            "arr_median": _median(financial_arr), "arr_max": max(financial_arr) if financial_arr else None,
            "sum_mrr_rows_not_current_revenue": sum(financial_mrr), "sum_arr_rows_not_revenue_lost": sum(financial_arr),
            "event_refunds_2024_rows": len(refunds), "event_refunds_2024_nonzero_rows": sum(value != 0 for value in refunds),
            "event_refunds_2024_recorded_sum_usd": round(sum(refunds), 2),
            "conflicting_event_refund_rows": len(conflict_inventory),
            "conflicting_event_refund_nonzero_rows": sum((row["refund_amount_usd_recorded"] or 0) != 0 for row in conflict_inventory),
            "conflicting_event_refund_recorded_sum_usd": round(sum(row["refund_amount_usd_recorded"] or 0 for row in conflict_inventory), 2),
            "interpretation": "MRR/ARR are row attributes with unclear snapshot/version semantics; sums are shown only as non-authoritative row totals. Refunds belong to event rows and cannot be assigned to a subscription without an explicit key.",
        },
        "conflicting_events": conflict_inventory,
        "limitations": [
            "Source churn_events has account_id but no subscription_id, so event-to-contract matching is unavailable.",
            "A subscription end_date is documented as ended, but the source does not establish whether it is commercial termination, administrative row closure, or contract replacement.",
            "Multiple rows per account do not identify whether rows are separate products, versions, snapshots, or generated contract changes.",
            "A later subscription is a successor candidate only; migration/replacement is not directly recorded.",
            "The dataset is synthetic and no operational billing ledger or CRM lifecycle is available.",
            "Financial row MRR/ARR values cannot be treated as unique/current revenue or confirmed lost revenue.",
        ],
    }
    return output


def _float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def _int(value: str | None) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except ValueError:
        return None


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    middle = len(vals) // 2
    return vals[middle] if len(vals) % 2 else (vals[middle - 1] + vals[middle]) / 2


def _cross_tab(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    axes = ["account_churn_flag", "any_subscription_churn_flag", "any_2024_nonreactivation_event", "any_subscription_end_2024", "complete_2024_coverage_by_date", "active_at_2025_01_01_by_date"]
    result: dict[str, dict[str, int]] = {}
    for index, left in enumerate(axes):
        for right in axes[index + 1:]:
            counts = Counter(f"{row[left]}|{row[right]}" for row in rows)
            result[f"{left}_vs_{right}"] = dict(counts)
    return result


def write_outputs(result: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "contract-churn-forensics.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_csv(output_dir / "ended-opening-subscriptions-2024.csv", result["ended_subscriptions"])
    _write_csv(output_dir / "conflicting-nonreactivation-events-2024.csv", result["conflicting_events"])
    _write_csv(output_dir / "opening-account-reconciliation-2024.csv", result["account_reconciliation"]["account_rows"])
    _write_csv(output_dir / "reactivation-marked-events-2024.csv", result["reactivation_events"])


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value for key, value in row.items()})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = investigate(args.data_dir)
    write_outputs(result, args.output_dir)
    print(json.dumps({"output_dir": str(args.output_dir), "revalidation": result["revalidation"],
                      "case_counts": result["ended_subscription_class_counts"],
                      "event_end_proximity_counts": result["event_end_proximity_counts"],
                      "event_reasons": result["event_reasons"], "financial_descriptives": result["financial_descriptives"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
