#!/usr/bin/env python3
"""Reproducible business-driver diagnostics over the five original RavenStack CSVs.

Uses only the Python standard library. Outputs are descriptive, label-conditioned
diagnostics; they are not churn rates, risk probabilities, or causal estimates.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

MODULE = Path(__file__).resolve().parent
SOLUTION = MODULE.parents[1]
DEFAULT_DATA = SOLUTION / "data" / "raw"
DEFAULT_OUTPUT = MODULE / "outputs"
TABLES = {
    "accounts": "ravenstack_accounts.csv",
    "subscriptions": "ravenstack_subscriptions.csv",
    "usage": "ravenstack_feature_usage.csv",
    "tickets": "ravenstack_support_tickets.csv",
    "events": "ravenstack_churn_events.csv",
}
LABELS = ("account_flag", "any_event", "nonreactivation_event", "subscription_flag_account")
SEGMENT_FIELDS = ("referral_source", "industry", "country", "plan_tier", "is_trial")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def flag(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 4) if values else None


def median(values: list[float]) -> float | None:
    return round(statistics.median(values), 4) if values else None


def wilson(success: int, total: int, z: float = 1.959963984540054) -> list[float] | None:
    if not total:
        return None
    p = success / total
    d = 1 + z * z / total
    center = (p + z * z / (2 * total)) / d
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def labels_for(account: dict[str, Any]) -> dict[str, bool]:
    return {key: bool(account[key]) for key in LABELS}


def run(data_dir: Path, output_dir: Path) -> dict[str, Any]:
    missing = [name for name in TABLES.values() if not (data_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing source CSV(s) under {data_dir}: {', '.join(missing)}")
    accounts = read_csv(data_dir / TABLES["accounts"])
    subscriptions = read_csv(data_dir / TABLES["subscriptions"])
    usage = read_csv(data_dir / TABLES["usage"])
    tickets = read_csv(data_dir / TABLES["tickets"])
    events = read_csv(data_dir / TABLES["events"])
    account_by_id = {row["account_id"]: row for row in accounts}
    subs_by_id = {row["subscription_id"]: row for row in subscriptions}

    event_by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in events:
        event_by_account[row["account_id"]].append(row)
    sub_flag_accounts = {row["account_id"] for row in subscriptions if flag(row["churn_flag"])}
    account_labels: dict[str, dict[str, bool]] = {}
    for row in accounts:
        account_id = row["account_id"]
        account_labels[account_id] = {
            "account_flag": flag(row["churn_flag"]),
            "any_event": bool(event_by_account.get(account_id)),
            "nonreactivation_event": any(not flag(e["is_reactivation"]) for e in event_by_account.get(account_id, [])),
            "subscription_flag_account": account_id in sub_flag_accounts,
        }

    # Use subscription ID as the many-to-one join key, then preserve source-row grain.
    usage_by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    valid_usage: list[dict[str, Any]] = []
    usage_by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
    usage_by_year_account: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    usage_year_source: dict[int, list[dict[str, Any]]] = defaultdict(list)
    invalid_temporal_rows = Counter()
    seen_usage_ids: set[str] = set()
    for row in usage:
        first_source_occurrence = row["usage_id"] not in seen_usage_ids
        seen_usage_ids.add(row["usage_id"])
        sub = subs_by_id.get(row["subscription_id"])
        if not sub or sub["account_id"] not in account_by_id:
            invalid_temporal_rows["unmatched_subscription"] += 1
            continue
        use_date, start, end = (parse_date(row.get("usage_date")), parse_date(sub.get("start_date")), parse_date(sub.get("end_date")))
        if not use_date:
            invalid_temporal_rows["missing_or_invalid_date"] += 1
            continue
        enriched = {**row, "account_id": sub["account_id"], "_usage": number(row.get("usage_count")) or 0.0,
                    "_duration": number(row.get("usage_duration_secs")), "_errors": number(row.get("error_count")) or 0.0,
                    "_date": use_date, "_first_source_occurrence": first_source_occurrence}
        # Preserve all date-valid source usage for calendar-volume comparisons.
        # Temporal eligibility is added as a separate sensitivity below.
        usage_by_month[use_date.strftime("%Y-%m")].append(enriched)
        usage_year_source[use_date.year].append(enriched)
        usage_by_year_account[use_date.year][sub["account_id"]] += enriched["_usage"]
        if not start:
            invalid_temporal_rows["missing_or_invalid_subscription_start"] += 1
            continue
        if use_date < start:
            invalid_temporal_rows["before_subscription_start"] += 1
            continue
        if end and use_date > end:
            invalid_temporal_rows["after_subscription_end"] += 1
            continue
        valid_usage.append(enriched)
        usage_by_account[sub["account_id"]].append(enriched)

    # Group observed ticket facts at account grain before comparing accounts.
    tickets_by_account: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in tickets:
        tickets_by_account[row["account_id"]].append(row)
    ticket_groups: dict[str, dict[str, Any]] = {}
    for label in LABELS:
        positive_ids = {aid for aid, labs in account_labels.items() if labs[label]}
        for group_name, ids in (("positive", positive_ids), ("negative", set(account_by_id) - positive_ids)):
            group_tickets = [t for aid in ids for t in tickets_by_account.get(aid, [])]
            scores = [number(t.get("satisfaction_score")) for t in group_tickets]
            scores = [v for v in scores if v is not None]
            first = [number(t.get("first_response_time_minutes")) for t in group_tickets]
            first = [v for v in first if v is not None]
            resolution = [number(t.get("resolution_time_hours")) for t in group_tickets]
            resolution = [v for v in resolution if v is not None]
            esc = [flag(t.get("escalation_flag")) for t in group_tickets if t.get("escalation_flag") not in (None, "")]
            # Account-cluster means: each account contributes one average, regardless of ticket volume.
            account_score_means = []
            account_escalation_rates = []
            for aid in ids:
                its = tickets_by_account.get(aid, [])
                av = [number(t.get("satisfaction_score")) for t in its]
                av = [v for v in av if v is not None]
                if av:
                    account_score_means.append(statistics.fmean(av))
                ev = [flag(t.get("escalation_flag")) for t in its if t.get("escalation_flag") not in (None, "")]
                if ev:
                    account_escalation_rates.append(statistics.fmean(ev))
            ticket_groups[f"{label}:{group_name}"] = {
                "label": label, "group": group_name, "account_count": len(ids),
                "accounts_with_tickets": len({t["account_id"] for t in group_tickets}), "ticket_rows": len(group_tickets),
                "satisfaction_mean_ticket": mean(scores), "satisfaction_scored_tickets": len(scores),
                "satisfaction_missing_tickets": sum(not t.get("satisfaction_score") for t in group_tickets),
                "satisfaction_mean_account_average": mean(account_score_means), "accounts_with_satisfaction": len(account_score_means),
                "first_response_median_minutes": median(first), "first_response_n": len(first),
                "resolution_median_hours": median(resolution), "resolution_n": len(resolution),
                "escalated_ticket_rows": sum(esc), "escalation_ticket_rows_n": len(esc),
                "mean_account_escalation_rate": mean(account_escalation_rates), "accounts_with_escalation_data": len(account_escalation_rates),
            }

    label_totals = {label: sum(labs[label] for labs in account_labels.values()) for label in LABELS}
    disagreement_count = sum(len({labs[label] for label in LABELS}) > 1 for labs in account_labels.values())
    crosstabs = {}
    for left, right in (("account_flag", "any_event"), ("account_flag", "nonreactivation_event"),
                        ("account_flag", "subscription_flag_account"), ("any_event", "nonreactivation_event")):
        crosstabs[f"{left}_vs_{right}"] = {
            f"{int(a)}:{int(b)}": sum(labs[left] == a and labs[right] == b for labs in account_labels.values())
            for a in (True, False) for b in (True, False)
        }

    segment_rows = []
    for field in SEGMENT_FIELDS:
        by_value: dict[str, list[str]] = defaultdict(list)
        for row in accounts:
            by_value[row.get(field) or "(missing)"].append(row["account_id"])
        for value, ids in by_value.items():
            for label in LABELS:
                positives = sum(account_labels[aid][label] for aid in ids)
                segment_rows.append({"dimension": field, "segment": value, "label": label, "accounts": len(ids),
                                     "positive_accounts": positives, "prevalence": round(positives / len(ids), 4),
                                     "wilson_95": wilson(positives, len(ids)), "small_sample": len(ids) < 30})
    # Subscription billing cadence stays at subscription-row grain and explicitly uses its own label.
    by_billing: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in subscriptions:
        by_billing[row.get("billing_frequency") or "(missing)"].append(row)
    subscription_segments = []
    for value, rows in by_billing.items():
        positive = sum(flag(r.get("churn_flag")) for r in rows)
        subscription_segments.append({"dimension": "billing_frequency", "segment": value, "label": "subscription_churn_flag",
                                      "subscriptions": len(rows), "flagged_subscriptions": positive,
                                      "prevalence": round(positive / len(rows), 4) if rows else None,
                                      "wilson_95": wilson(positive, len(rows))})

    # Cohorts summarize retrospective labels only; no retention rate or heatmap is emitted.
    cohorts: dict[str, list[str]] = defaultdict(list)
    bad_signup_dates = 0
    for row in accounts:
        dt = parse_date(row.get("signup_date"))
        if not dt:
            bad_signup_dates += 1
            continue
        quarter = (dt.month - 1) // 3 + 1
        cohorts[f"{dt.year}-Q{quarter}"].append(row["account_id"])
    max_event_date = max((parse_date(e.get("churn_date")) for e in events if parse_date(e.get("churn_date"))), default=None)
    cohort_rows = []
    for cohort, ids in sorted(cohorts.items()):
        ys = [int(cohort[:4]), int(cohort[-1])]
        quarter_start = date(ys[0], 3 * (ys[1] - 1) + 1, 1)
        age_days = (max_event_date - quarter_start).days if max_event_date else None
        rec = {"cohort": cohort, "accounts": len(ids), "event_window_days_from_cohort_start_to_last_event": age_days,
               "interpretation": "retrospective label mix only; not cohort retention"}
        for label in LABELS:
            positives = sum(account_labels[aid][label] for aid in ids)
            rec[f"{label}_accounts"] = positives
            rec[f"{label}_share"] = round(positives / len(ids), 4)
        cohort_rows.append(rec)
    first_subscription_date_by_account: dict[str, date] = {}
    for row in subscriptions:
        start = parse_date(row.get("start_date"))
        if start and row["account_id"] in account_by_id:
            previous = first_subscription_date_by_account.get(row["account_id"])
            if previous is None or start < previous:
                first_subscription_date_by_account[row["account_id"]] = start
    subscription_cohorts: dict[str, list[str]] = defaultdict(list)
    for aid, start in first_subscription_date_by_account.items():
        quarter = (start.month - 1) // 3 + 1
        subscription_cohorts[f"{start.year}-Q{quarter}"].append(aid)
    first_subscription_cohort_rows = []
    for cohort, ids in sorted(subscription_cohorts.items()):
        rec = {"cohort": cohort, "accounts": len(ids), "interpretation": "earliest listed subscription-start composition only; not verified first paid subscription or retention"}
        for label in LABELS:
            positives = sum(account_labels[aid][label] for aid in ids)
            rec[f"{label}_accounts"] = positives
            rec[f"{label}_share"] = round(positives / len(ids), 4)
        first_subscription_cohort_rows.append(rec)

    # Account-level valid-period use and feature adoption. These totals are not pre-event measures.
    usage_by_label = []
    for label in LABELS:
        for group, predicate in (("positive", True), ("negative", False)):
            ids = [aid for aid, labs in account_labels.items() if labs[label] == predicate]
            account_totals = [sum(x["_usage"] for x in usage_by_account.get(aid, [])) for aid in ids]
            used = [v for v in account_totals if v > 0]
            per_account_errors = [sum(x["_errors"] for x in usage_by_account.get(aid, [])) for aid in ids]
            usage_by_label.append({"label": label, "group": group, "accounts": len(ids), "accounts_with_valid_interval_usage": sum(v > 0 for v in account_totals),
                                  "valid_interval_usage_count_sum": round(sum(account_totals), 4),
                                  "mean_usage_count_per_account": mean(account_totals), "median_usage_count_per_account": median(account_totals),
                                  "mean_usage_count_among_users": mean(used), "mean_errors_per_account": mean(per_account_errors),
                                  "temporal_note": "valid subscription interval; not aligned to a verified cancellation window"})
    feature_accounts: dict[str, set[str]] = defaultdict(set)
    feature_rows: Counter[str] = Counter()
    feature_usage: Counter[str] = Counter()
    feature_errors: Counter[str] = Counter()
    feature_beta_rows: Counter[str] = Counter()
    for row in valid_usage:
        f = row["feature_name"] or "(missing)"
        feature_accounts[f].add(row["account_id"])
        feature_rows[f] += 1
        feature_usage[f] += row["_usage"]
        feature_errors[f] += row["_errors"]
        feature_beta_rows[f] += flag(row.get("is_beta_feature"))
    feature_adoption = [{"feature": f, "accounts": len(ids), "share_of_all_accounts": round(len(ids) / len(accounts), 4),
                         "valid_usage_rows": feature_rows[f], "usage_count_sum": round(feature_usage[f], 4),
                         "error_count_sum": feature_errors[f], "beta_usage_rows": feature_beta_rows[f]}
                        for f, ids in sorted(feature_accounts.items(), key=lambda item: (-len(item[1]), item[0]))]
    total_valid_usage = sum(x["_usage"] for x in valid_usage)
    by_account_usage = sorted(((aid, sum(x["_usage"] for x in rows)) for aid, rows in usage_by_account.items()), key=lambda x: (-x[1], x[0]))
    usage_id_counts = Counter(row["usage_id"] for row in usage)
    first_valid_usage_lags = []
    for aid, rows in usage_by_account.items():
        signup = parse_date(account_by_id[aid].get("signup_date"))
        if signup and rows:
            first_valid_usage_lags.append((min(row["_date"] for row in rows) - signup).days)
    unique_valid_rows: dict[str, dict[str, Any]] = {}
    for row in valid_usage:
        unique_valid_rows.setdefault(row["usage_id"], row)
    unique_valid_usage_sum = sum(row["_usage"] for row in unique_valid_rows.values())
    valid_rows_with_duplicate_ids = sum(usage_id_counts[row["usage_id"]] > 1 for row in valid_usage)
    valid_rows_after_first_source_occurrence = [row for row in valid_usage if row["_first_source_occurrence"]]
    usage_concentration = {"valid_interval_usage_rows": len(valid_usage), "accounts_with_any_valid_interval_usage": len(by_account_usage),
                           "accounts_without_valid_interval_usage": len(accounts) - len(by_account_usage),
                           "valid_interval_usage_count_sum": round(total_valid_usage, 4),
                           "valid_unique_usage_ids_with_any_valid_row": len(unique_valid_rows),
                           "valid_unique_usage_count_sum": round(unique_valid_usage_sum, 4),
                           "valid_rows_after_first_source_occurrence": len(valid_rows_after_first_source_occurrence),
                           "valid_usage_count_after_first_source_occurrence": round(sum(row["_usage"] for row in valid_rows_after_first_source_occurrence), 4),
                           "valid_rows_with_duplicate_ids": valid_rows_with_duplicate_ids,
                           "valid_rows_after_excluding_all_rows_in_duplicate_id_groups": len(valid_usage) - valid_rows_with_duplicate_ids,
                           "top_10_accounts_share": round(sum(x[1] for x in by_account_usage[:10]) / total_valid_usage, 4) if total_valid_usage else None,
                           "top_50_accounts_share": round(sum(x[1] for x in by_account_usage[:50]) / total_valid_usage, 4) if total_valid_usage else None,
                           "top_decile_accounts_share": round(sum(x[1] for x in by_account_usage[:max(1, math.ceil(len(by_account_usage) * .1))]) / total_valid_usage, 4) if total_valid_usage else None,
                           "valid_interval_rows_excluded_by_reason": dict(invalid_temporal_rows),
                           "duplicate_usage_id_groups": sum(count > 1 for count in usage_id_counts.values()),
                           "rows_in_duplicate_usage_id_groups": sum(count for count in usage_id_counts.values() if count > 1),
                           "excess_rows_after_one_per_usage_id": sum(count - 1 for count in usage_id_counts.values() if count > 1)}

    # Raw calendar trends answer the CEO's growth claim without pretending that
    # source rows form a valid pre-cancellation exposure window. Account-months
    # are normalized by observed accounts in each month; date-bounded values are
    # reported separately as a sensitivity.
    monthly_usage_trend = []
    observed_account_months_by_year: Counter[int] = Counter()
    for month, rows in sorted(usage_by_month.items()):
        accounts_observed = {row["account_id"] for row in rows}
        year = int(month[:4])
        observed_account_months_by_year[year] += len(accounts_observed)
        monthly_usage_trend.append({
            "month": month,
            "source_rows": len(rows),
            "distinct_accounts_observed": len(accounts_observed),
            "recorded_usage_count": round(sum(row["_usage"] for row in rows), 4),
            "rows_after_first_source_occurrence": sum(row["_first_source_occurrence"] for row in rows),
            "usage_count_after_first_source_occurrence": round(sum(row["_usage"] for row in rows if row["_first_source_occurrence"]), 4),
            "valid_interval_rows": sum(row["_date"] >= parse_date(subs_by_id[row["subscription_id"]].get("start_date")) and
                (not parse_date(subs_by_id[row["subscription_id"]].get("end_date")) or row["_date"] <= parse_date(subs_by_id[row["subscription_id"]].get("end_date")))
                for row in rows if row["subscription_id"] in subs_by_id),
            "valid_interval_usage_count": round(sum(row["_usage"] for row in valid_usage if row["_date"].strftime("%Y-%m") == month), 4),
            "interpretation": "Observed source-row volume; not a pre-churn adoption measure or proof of growth for every customer.",
        })
    yearly_usage_trend = []
    for year, rows in sorted(usage_year_source.items()):
        ids = {row["account_id"] for row in rows}
        deduped = [row for row in rows if row["_first_source_occurrence"]]
        valid_rows = [row for row in valid_usage if row["_date"].year == year]
        account_totals = list(usage_by_year_account[year].values())
        yearly_usage_trend.append({
            "year": year,
            "source_rows": len(rows),
            "distinct_accounts_observed": len(ids),
            "observed_account_months": observed_account_months_by_year[year],
            "recorded_usage_count": round(sum(row["_usage"] for row in rows), 4),
            "usage_count_per_observed_account_month": round(sum(row["_usage"] for row in rows) / observed_account_months_by_year[year], 4) if observed_account_months_by_year[year] else None,
            "mean_recorded_usage_count_per_account": mean(account_totals),
            "median_recorded_usage_count_per_account": median(account_totals),
            "source_rows_after_first_duplicate_occurrence": len(deduped),
            "usage_count_after_first_duplicate_occurrence": round(sum(row["_usage"] for row in deduped), 4),
            "valid_interval_rows": len(valid_rows),
            "valid_interval_distinct_accounts": len({row["account_id"] for row in valid_rows}),
            "valid_interval_usage_count": round(sum(row["_usage"] for row in valid_rows), 4),
            "classification": "DESCRIPTIVE_SOURCE_VOLUME; interval-bounded subset is a sensitivity, not a verified retention window.",
        })
    segment_usage_trend = []
    for field in SEGMENT_FIELDS:
        ids_by_segment: dict[str, list[str]] = defaultdict(list)
        for account in accounts:
            ids_by_segment[account.get(field) or "(missing)"].append(account["account_id"])
        for segment, ids in sorted(ids_by_segment.items()):
            previous_mean = None
            for year in sorted(usage_year_source):
                account_values = [usage_by_year_account[year].get(account_id, 0.0) for account_id in ids]
                current_mean = statistics.fmean(account_values) if account_values else None
                segment_usage_trend.append({
                    "dimension": field, "segment": segment, "year": year,
                    "account_denominator": len(ids), "accounts_with_observed_usage": sum(value > 0 for value in account_values),
                    "recorded_usage_count": round(sum(account_values), 4),
                    "mean_recorded_usage_count_per_segment_account": round(current_mean, 4) if current_mean is not None else None,
                    "median_recorded_usage_count_per_segment_account": median(account_values),
                    "prior_year_mean_recorded_usage_count_per_segment_account": round(previous_mean, 4) if previous_mean is not None else None,
                    "change_from_prior_year_pct": round((current_mean / previous_mean - 1) * 100, 4) if previous_mean else None,
                    "classification": "DESCRIPTIVE CALENDAR VOLUME; fixed account segment denominator, not exposure-adjusted adoption or a churn effect.",
                })
                previous_mean = current_mean

    event_date_before_signup = 0
    event_date_missing = 0
    event_dates = []
    for e in events:
        ed = parse_date(e.get("churn_date"))
        ad = parse_date(account_by_id.get(e["account_id"], {}).get("signup_date"))
        if ed:
            event_dates.append(ed)
            event_date_before_signup += bool(ad and ed < ad)
        else:
            event_date_missing += 1

    rankings = []
    for segment in segment_rows:
        if segment["accounts"] >= 30:
            rankings.append(segment)
    rankings.sort(key=lambda r: (r["label"], -r["prevalence"], -r["accounts"], r["dimension"], r["segment"]))

    # Specific records are investigation candidates only, selected by reconciliation or repeat event evidence.
    candidates = []
    for aid, acct in account_by_id.items():
        labs = account_labels[aid]
        if len(set(labs.values())) < 2 and len(event_by_account.get(aid, [])) < 3:
            continue
        ts = tickets_by_account.get(aid, [])
        account_usage = usage_by_account.get(aid, [])
        escalations = sum(flag(t.get("escalation_flag")) for t in ts if t.get("escalation_flag") not in (None, ""))
        candidates.append({"account_id": aid, "account_name": acct.get("account_name"), "industry": acct.get("industry"),
                           "country": acct.get("country"), "referral_source": acct.get("referral_source"),
                           "plan_tier": acct.get("plan_tier"), "seats": number(acct.get("seats")), "is_trial": flag(acct.get("is_trial")),
                           "labels": labs, "event_rows": len(event_by_account.get(aid, [])),
                           "nonreactivation_event_rows": sum(not flag(e.get("is_reactivation")) for e in event_by_account.get(aid, [])),
                           "ticket_rows": len(ts), "escalated_ticket_rows": escalations,
                           "valid_interval_usage_rows": len(account_usage), "valid_interval_usage_count": round(sum(u["_usage"] for u in account_usage), 4),
                           "selection_reason": "label disagreement and/or repeated event history; reconciliation candidate, not future-risk estimate"})
    candidates.sort(key=lambda r: (-r["event_rows"], -int(sum(r["labels"].values()) not in (0, 4)), -r["escalated_ticket_rows"], r["account_id"]))

    # Descriptive financial observations at original row grain only.
    mrr = [number(r.get("mrr_amount")) for r in subscriptions]
    mrr = [v for v in mrr if v is not None]
    arr = [number(r.get("arr_amount")) for r in subscriptions]
    arr = [v for v in arr if v is not None]
    refund = [number(e.get("refund_amount_usd")) for e in events]
    refund = [v for v in refund if v is not None]
    revenue = {"subscription_rows": len(subscriptions), "accounts_represented": len({s["account_id"] for s in subscriptions}),
               "mrr_recorded_rows_n": len(mrr), "mrr_row_min": min(mrr) if mrr else None, "mrr_row_median": median(mrr), "mrr_row_max": max(mrr) if mrr else None,
               "mrr_zero_rows": sum(v == 0 for v in mrr),
               "arr_recorded_rows_n": len(arr), "arr_row_min": min(arr) if arr else None, "arr_row_median": median(arr), "arr_row_max": max(arr) if arr else None,
               "arr_zero_rows": sum(v == 0 for v in arr),
               "mrr_row_sum_not_revenue": round(sum(mrr), 2), "arr_row_sum_not_revenue": round(sum(arr), 2),
               "refund_observed_sum_usd": round(sum(refund), 2), "refund_nonzero_event_rows": sum(v != 0 for v in refund),
               "current_mrr_lost_revenue_grr_nrr_ltv_exposure": None,
               "limitation": "multiple subscription rows per account, no reconciled snapshot/effective-date and no event-to-subscription link; sums are not current or lost revenue"}

    # Evidence-priority is qualitative and ordered by data strength and decision usefulness, not probability.
    hypotheses = [
        {"hypothesis": "Outcome and lifecycle instrumentation conflict", "classification": "VERIFIED_OBSERVATION", "evidence": f"{disagreement_count}/500 accounts disagree across at least one of four account-level indicators; account flag vs any event differs for {sum(v for k,v in crosstabs['account_flag_vs_any_event'].items() if k in ('1:0','0:1'))} accounts.", "counterevidence": "The four indicators do not have identical intended semantics, so disagreement is not automatically a source-system error.", "priority": "P0", "next_test": "Define eligible paid account/subscription state, cancellation, reactivation and effective timestamps; reconcile sampled records against source contracts."},
        {"hypothesis": "Acquisition/ICP mismatch", "classification": "CONDITIONAL_RESULT", "evidence": "Segment prevalences vary by label; see segment table with denominators, Wilson intervals and sample-size warnings.", "counterevidence": "Rankings change with label; acquisition cost, margin, value and temporal outcome are unavailable; composition can confound comparisons.", "priority": "P1", "next_test": "Recompute by acquisition cohort after valid outcome and exposure are instrumented; compare channel economics and retention."},
        {"hypothesis": "Weak activation or time-to-value", "classification": "UNKNOWN", "evidence": f"{len(valid_usage)} usage rows remain inside linked subscription intervals; first observed interval-valid usage is only a proxy.", "counterevidence": f"{sum(invalid_temporal_rows.values())} usage rows are excluded from the interval sensitivity and signup/onboarding timestamps are not a canonical activation event.", "priority": "P1", "next_test": "Instrument onboarding completion and first-value event tied to account/subscription, then monitor 7/30-day activation."},
        {"hypothesis": "Low or concentrated adoption", "classification": "CONDITIONAL_RESULT", "evidence": f"Among interval-valid usage, the top decile of accounts represents {usage_concentration['top_decile_accounts_share']:.1%} of recorded usage counts.", "counterevidence": "Usage count is not value realized; interval-valid use is still not a verified pre-cancellation window.", "priority": "P1", "next_test": "Define meaningful adoption by feature/use case and compare prospectively within eligible cohorts."},
        {"hypothesis": "Support friction", "classification": "CONDITIONAL_RESULT", "evidence": "Ticket outcomes are available by each alternative account label; account-cluster satisfaction and escalation summaries are included alongside ticket-row values.", "counterevidence": "Ticket volume is selected by support need; satisfaction is missing for 825/2,000 tickets and not time-aligned to cancellation.", "priority": "P2", "next_test": "Link ticket histories to reconciled cancellation dates; review escalations and conduct customer follow-up."},
        {"hypothesis": "Price/value mismatch", "classification": "UNKNOWN", "evidence": "Reason codes and subscription-row monetary fields can be described; price/budget codes occur in event records.", "counterevidence": "Reason codes are not causal proof; contract row semantics, realized value and customer willingness-to-pay are unavailable.", "priority": "P2", "next_test": "Validate reason codes in customer interviews and reconcile invoice/contract snapshots before price intervention."},
        {"hypothesis": "Product reliability or competitive gap", "classification": "UNKNOWN", "evidence": "Usage error counts and event reason codes are available as exploratory signals.", "counterevidence": "No product incident exposure, feature entitlement, release history or account-linked verified cancellation timeline.", "priority": "P2", "next_test": "Join telemetry to release/incident exposure and verify with a sampled customer review."},
    ]
    recommendations = [
        {"priority": 1, "action": "Reconcile the lifecycle and build a monthly eligible-account snapshot", "function": "RevOps + Data/Product Analytics", "target": "All accounts and subscription rows with conflicting state", "evidence": f"{disagreement_count}/500 accounts differ across outcome indicators; 600 event rows lack reliable subscription linkage.", "effort": "Medium; planning estimate only, not a measured cost", "success_metric": "Audited state coverage and stable eligible denominator by month", "validation": "Sample source contract/invoice records and compare against canonical account-subscription state", "impact": "Enables a valid churn rate and prevents misallocated intervention; financial impact not quantified."},
        {"priority": 2, "action": "Instrument activation and meaningful adoption on a shared timeline", "function": "Product Analytics + Customer Success", "target": "New accounts by acquisition channel, plan and trial status", "evidence": "Usage timestamps materially fall outside linked subscription intervals; current first use is only a proxy.", "effort": "Medium; event taxonomy and instrumentation work", "success_metric": "Coverage of signup, onboarding completion, first-value event and 7/30-day adoption", "validation": "Audit event ordering and cohort completeness before comparing activation rates", "impact": "Improves diagnosis and targeting; no churn reduction is claimed."},
        {"priority": 3, "action": "Run a small randomized adoption/support pilot after eligibility is reconciled", "function": "Customer Success + Analytics", "target": "Eligible accounts with verified active state and agreed low-adoption or unresolved-support criteria", "evidence": "Usage and ticket signals are available but not causal or temporally valid today.", "effort": "Low-to-medium pilot; cost per account must be estimated locally before launch", "success_metric": "90-day verified account retention; guardrails: satisfaction, escalations and service cost", "validation": "Account-level random assignment, stratified by plan/channel, intention-to-treat analysis", "impact": "Unknown until experiment; scenario tool is hypothetical only."},
    ]

    priority_groups = []
    all_priorities = sorted({t.get("priority") or "(missing)" for t in tickets})
    for label in LABELS:
        positive_ids = {aid for aid, labs in account_labels.items() if labs[label]}
        for group_name, ids in (("positive", positive_ids), ("negative", set(account_by_id) - positive_ids)):
            group_tickets = [t for aid in ids for t in tickets_by_account.get(aid, [])]
            for priority in all_priorities:
                rows = [t for t in group_tickets if (t.get("priority") or "(missing)") == priority]
                priority_groups.append({"label": label, "group": group_name, "priority": priority,
                                        "accounts": len({t["account_id"] for t in rows}), "ticket_rows": len(rows)})

    result = {
        "metadata": {"generated_by": "analysis/business_drivers/run.py", "source": "original five CSVs", "outcome_note": "All outcome prevalences are label-conditioned diagnostics, not historical churn rates or future-risk estimates.", "max_event_date": max_event_date.isoformat() if max_event_date else None},
        "record_counts": {"accounts": len(accounts), "subscriptions": len(subscriptions), "usage_rows": len(usage), "support_tickets": len(tickets), "event_rows": len(events)},
        "labels": {"account_positive_counts": label_totals, "accounts": len(accounts), "any_label_disagreement_accounts": disagreement_count, "pairwise_crosstabs": crosstabs,
                   "event_rows_before_signup": event_date_before_signup, "event_rows_missing_date": event_date_missing,
                   "event_rows_by_year": dict(sorted(Counter(str(parse_date(e.get("churn_date")).year) for e in events if parse_date(e.get("churn_date"))).items()))},
        "segments": segment_rows, "subscription_segments": subscription_segments,
        "segment_exploratory_rankings_min_30": rankings,
        "cohorts": {"definition": "account signup quarter", "rows": cohort_rows, "first_subscription_start_definition": "quarter of earliest listed subscription.start_date for each account; not verified first paid subscription",
                    "first_subscription_start_rows": first_subscription_cohort_rows, "retention_heatmap": None,
                    "status": "NOT_IDENTIFIABLE", "reason": "Outcome labels conflict, no eligible-at-risk history or complete customer-state intervals; rows show retrospective label composition only, not retention."},
        "usage": {"concentration": usage_concentration, "by_label": usage_by_label, "feature_adoption": feature_adoption,
                  "monthly_source_trend": monthly_usage_trend, "yearly_source_trend": yearly_usage_trend,
                  "segment_yearly_source_trend": segment_usage_trend,
                  "activation_proxy": {"status": "CONDITIONAL", "definition": "first usage row within a linked subscription's start/end bounds, compared with account signup date", "account_count_with_proxy": len(first_valid_usage_lags),
                                       "median_days_from_signup": median([float(v) for v in first_valid_usage_lags]),
                                       "accounts_first_use_before_signup": sum(v < 0 for v in first_valid_usage_lags),
                                       "accounts_first_use_within_7_days": sum(0 <= v <= 7 for v in first_valid_usage_lags),
                                       "accounts_first_use_within_30_days": sum(0 <= v <= 30 for v in first_valid_usage_lags),
                                       "limitation": "Not onboarding completion or time-to-value; subscription boundaries and signup are not a validated lifecycle timeline."}},
        "support": {"by_label": list(ticket_groups.values()), "ticket_priority_by_label": priority_groups,
                    "satisfaction_missing_all_tickets": sum(not t.get("satisfaction_score") for t in tickets),
                    "satisfaction_missing_share": round(sum(not t.get("satisfaction_score") for t in tickets)/len(tickets), 4) if tickets else None,
                    "interpretation": "ticket-row summaries and account-cluster means are descriptive; missingness and temporal order limit inference"},
        "revenue": revenue, "account_investigation_candidates": candidates[:30], "hypotheses": hypotheses, "recommendations": recommendations,
        "limitations": ["Synthetic public challenge data; observed associations do not establish business causality.",
                        "No eligible customer-month denominator or reconciled lifecycle history; logo/subscription/revenue churn rates and retention cohorts are not identifiable.",
                        "No account is assigned a calibrated future churn probability.",
                        "The account queue is for lifecycle/data review and is not a risk score.",
                        "Revenue row values and refund totals are not current recurring revenue or preventable loss."],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "business-investigation.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(output_dir / "segment-labels.csv", segment_rows)
    write_csv(output_dir / "signup-cohort-label-diagnostic.csv", cohort_rows)
    write_csv(output_dir / "usage-by-label.csv", usage_by_label)
    write_csv(output_dir / "feature-adoption-valid-interval.csv", feature_adoption)
    write_csv(output_dir / "account-investigation-candidates.csv", candidates[:30])
    return result


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA, help=f"Directory containing the five raw CSVs (default: {DEFAULT_DATA})")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT, help=f"Explicit output directory (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()
    result = run(args.data_dir, args.output_dir)
    print(json.dumps({"status": "ok", "records": result["record_counts"], "output_dir": str(args.output_dir),
                      "labels": result["labels"]["account_positive_counts"], "cohorts": len(result["cohorts"]["rows"]),
                      "account_candidates": len(result["account_investigation_candidates"])}, indent=2))


if __name__ == "__main__":
    main()
