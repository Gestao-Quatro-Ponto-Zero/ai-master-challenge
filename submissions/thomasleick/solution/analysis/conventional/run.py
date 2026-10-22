#!/usr/bin/env python3
"""Reproducible descriptive analysis for the five RavenStack source tables.

Uses only the Python standard library. It intentionally reports label-specific
descriptive associations and does not estimate causal effects or probabilities.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import pathlib
import random
import statistics
from collections import Counter, defaultdict

TABLES = ("accounts", "subscriptions", "feature_usage", "support_tickets", "churn_events")
DEFAULT_DATA = pathlib.Path(__file__).resolve().parents[2] / "data" / "raw"
DEFAULT_OUT = pathlib.Path(__file__).resolve().parent / "outputs"


def read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def flag(s: str | None) -> bool:
    return (s or "").strip().lower() in {"true", "1", "yes"}


def num(s: str | None, default: float | None = None) -> float | None:
    if s is None or s.strip() == "":
        return default
    return float(s)


def date(s: str | None) -> dt.date | None:
    if not s:
        return None
    return dt.date.fromisoformat(s[:10])


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float | None, float | None]:
    if n == 0:
        return None, None
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return center - half, center + half


def mean_or_none(xs: list[float]) -> float | None:
    return statistics.mean(xs) if xs else None


def summarize_numeric(xs: list[float]) -> dict:
    if not xs:
        return {"n": 0, "mean": None, "median": None, "min": None, "max": None}
    s = sorted(xs)
    return {"n": len(s), "mean": statistics.mean(s), "median": statistics.median(s),
            "min": s[0], "max": s[-1], "p25": s[(len(s)-1)//4], "p75": s[3*(len(s)-1)//4]}


def bootstrap_mean_difference(positive: list[float], negative: list[float], seed: int) -> dict:
    """Account-level percentile bootstrap CI for positive minus negative means."""
    if len(positive) < 2 or len(negative) < 2:
        return {"positive_accounts_with_measure": len(positive), "negative_accounts_with_measure": len(negative),
                "mean_difference": None, "bootstrap_95_low": None, "bootstrap_95_high": None,
                "method": "account-level percentile bootstrap; requires >=2 accounts/group"}
    observed = statistics.mean(positive) - statistics.mean(negative)
    rng = random.Random(seed)
    draws = []
    for _ in range(2000):
        p = sum(positive[rng.randrange(len(positive))] for _ in positive) / len(positive)
        n = sum(negative[rng.randrange(len(negative))] for _ in negative) / len(negative)
        draws.append(p - n)
    draws.sort()
    return {"positive_accounts_with_measure": len(positive), "negative_accounts_with_measure": len(negative),
            "mean_difference": observed, "bootstrap_95_low": draws[49], "bootstrap_95_high": draws[1949],
            "method": "account-level percentile bootstrap, 2,000 resamples; descriptive, not causal"}


def write_csv(path: pathlib.Path, rows: list[dict], columns: list[str] | None = None) -> None:
    if columns is None:
        columns = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: json_cell(v) for k, v in row.items()})


def json_cell(v):
    if isinstance(v, (dict, list, tuple)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return v


def profile_table(name: str, rows: list[dict], path: pathlib.Path) -> dict:
    columns = list(rows[0]) if rows else []
    fields = {}
    for col in columns:
        present = [r.get(col, "") for r in rows if r.get(col, "") not in ("", None)]
        if col.endswith("_date") or col.endswith("_at"):
            inferred_type = "date/datetime"
        elif present and set(present) <= {"True", "False", "true", "false", "0", "1"}:
            inferred_type = "boolean-like"
        else:
            try:
                [float(v) for v in present]
                inferred_type = "numeric"
            except ValueError:
                inferred_type = "string/category"
        fields[col] = {"null_count": len(rows) - len(present),
                       "null_rate": (len(rows)-len(present))/len(rows) if rows else None,
                       "distinct_non_null": len(set(present)),
                       "inferred_type": inferred_type,
                       "top_values": Counter(present).most_common(8)}
        if present:
            try:
                numeric_values = [float(v) for v in present]
            except ValueError:
                numeric_values = None
            if numeric_values is not None:
                fields[col]["numeric_summary"] = summarize_numeric(numeric_values)
        if col.endswith("_date") or col.endswith("_at"):
            ds = [date(v) for v in present]
            fields[col]["date_min"] = min(ds).isoformat() if ds else None
            fields[col]["date_max"] = max(ds).isoformat() if ds else None
    id_fields = {}
    for c in [c for c in columns if c.endswith("_id")]:
        counts = Counter(r[c] for r in rows if r.get(c))
        groups = [v for v in counts.values() if v > 1]
        id_fields[c] = {"non_null": sum(counts.values()), "distinct": len(counts),
                        "duplicate_ids": len(groups), "rows_in_duplicate_groups": sum(groups),
                        "excess_rows": sum(groups)-len(groups)}
    duplicate_whole_rows = len(rows)-len({tuple(sorted(r.items())) for r in rows})
    return {"source": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "rows": len(rows), "columns": columns, "fields": fields,
            "id_checks": id_fields, "full_duplicate_rows": duplicate_whole_rows}


def account_label_segment(accounts: list[dict], labels: dict[str, set[str]], field: str) -> list[dict]:
    values = sorted({a.get(field, "") or "UNKNOWN" for a in accounts})
    out = []
    for label, positives in labels.items():
        for value in values:
            group = [a for a in accounts if (a.get(field, "") or "UNKNOWN") == value]
            k, n = sum(a["account_id"] in positives for a in group), len(group)
            lo, hi = wilson(k, n)
            out.append({"label": label, "dimension": field, "segment": value, "accounts": n,
                        "positive_accounts": k, "prevalence": k/n if n else None,
                        "wilson_95_low": lo, "wilson_95_high": hi,
                        "small_sample_flag": n < 30})
    return out


def group_summary(label: str, members: set[str], all_ids: set[str], by_account: dict[str, list[dict]],
                  numeric_fields: list[str], flags: list[str] = ()) -> list[dict]:
    result = []
    for group_name, ids in (("positive", members), ("negative", all_ids-members)):
        rows = [r for aid in ids for r in by_account.get(aid, [])]
        item = {"label": label, "group": group_name, "accounts": len(ids), "records": len(rows)}
        for field in numeric_fields:
            xs = [x for r in rows if (x := num(r.get(field))) is not None]
            item[field] = mean_or_none(xs)
            item[field + "_n"] = len(xs)
            item[field + "_missing"] = len(rows)-len(xs)
        for field in flags:
            item[field + "_count"] = sum(flag(r.get(field)) for r in rows)
            item[field + "_rate"] = (item[field + "_count"]/len(rows)) if rows else None
        result.append(item)
    return result


def build(data_dir: pathlib.Path) -> dict:
    paths = {name: data_dir / f"ravenstack_{name}.csv" for name in TABLES}
    missing = [p.name for p in paths.values() if not p.is_file()]
    if missing:
        raise FileNotFoundError("Missing required tables: " + ", ".join(missing))
    tables = {name: read_csv(path) for name, path in paths.items()}
    a, s, u, t, e = (tables[n] for n in TABLES)
    account_ids = {r["account_id"] for r in a}
    sub_by_id = {r["subscription_id"]: r for r in s}
    account_by_id = {r["account_id"]: r for r in a}
    subs_by_account: dict[str, list[dict]] = defaultdict(list)
    events_by_account: dict[str, list[dict]] = defaultdict(list)
    tickets_by_account: dict[str, list[dict]] = defaultdict(list)
    usage_by_account: dict[str, list[dict]] = defaultdict(list)
    for row in s:
        subs_by_account[row["account_id"]].append(row)
    for row in e:
        events_by_account[row["account_id"]].append(row)
    for row in t:
        tickets_by_account[row["account_id"]].append(row)
    orphans = {"subscriptions_account": 0, "events_account": 0, "tickets_account": 0,
               "usage_subscription": 0, "usage_account": 0}
    for row in s:
        orphans["subscriptions_account"] += row["account_id"] not in account_ids
    for row in e:
        orphans["events_account"] += row["account_id"] not in account_ids
    for row in t:
        orphans["tickets_account"] += row["account_id"] not in account_ids
    for row in u:
        sub = sub_by_id.get(row["subscription_id"])
        if sub is None:
            orphans["usage_subscription"] += 1
            continue
        if sub["account_id"] not in account_ids:
            orphans["usage_account"] += 1
        usage_by_account[sub["account_id"]].append(row)

    flag_ids = {r["account_id"] for r in a if flag(r.get("churn_flag"))}
    event_ids = set(events_by_account)
    nonreact_ids = {aid for aid, rows in events_by_account.items()
                    if any(not flag(r.get("is_reactivation")) for r in rows)}
    subscription_flag_accounts = {r["account_id"] for r in s if flag(r.get("churn_flag"))}
    labels = {"account_churn_flag": flag_ids, "any_event_account": event_ids,
              "has_nonreactivation_event": nonreact_ids,
              "subscription_churn_flag_account": subscription_flag_accounts}

    # Source data profile, preserving rows; duplicate IDs are counted, never silently dropped.
    profiles = {name: profile_table(name, tables[name], paths[name]) for name in TABLES}
    event_counts = Counter(r["account_id"] for r in e)
    repeated_event_accounts = [count for count in event_counts.values() if count > 1]
    usage_rows_per_subscription = Counter(r["subscription_id"] for r in u)
    key_cardinality = {
        "accounts_to_subscriptions": {"left_accounts": len(a), "right_subscription_rows": len(s),
            "distinct_subscription_accounts": len({r["account_id"] for r in s}),
            "subscriptions_per_account": summarize_numeric([float(len(subs_by_account[x])) for x in account_ids])},
        "subscriptions_to_usage": {"subscription_rows": len(s), "usage_rows": len(u),
            "subscriptions_with_usage": len({r["subscription_id"] for r in u}),
            "usage_rows_per_subscription": summarize_numeric([float(usage_rows_per_subscription.get(sid, 0)) for sid in sub_by_id])},
        "account_child_tables": {"accounts": len(a), "events": len(e), "tickets": len(t),
            "event_rows_per_account_with_events": summarize_numeric([float(len(v)) for v in events_by_account.values()]),
            "event_account_repetition": {"accounts_with_multiple_event_rows": len(repeated_event_accounts),
                "rows_in_repeated_account_groups": sum(repeated_event_accounts),
                "excess_event_rows_beyond_first_per_account": sum(repeated_event_accounts)-len(repeated_event_accounts)},
            "tickets_per_account_with_tickets": summarize_numeric([float(len(v)) for v in tickets_by_account.values()])},
        "orphan_rows": orphans}

    event_nonreact_rows = [r for r in e if not flag(r.get("is_reactivation"))]
    intersection = len(flag_ids & event_ids)
    confusion = {"account_flag_true_event_yes": intersection,
                 "account_flag_true_event_no": len(flag_ids-event_ids),
                 "account_flag_false_event_yes": len(event_ids-flag_ids),
                 "account_flag_false_event_no": len(account_ids-(flag_ids|event_ids))}
    label_overview = [{"label": name, "positive_accounts": len(ids), "accounts": len(account_ids),
                       "prevalence": len(ids)/len(account_ids), "definition": {
                           "account_churn_flag": "accounts.churn_flag supplied field; operational label, not historical rate",
                           "any_event_account": "account has >=1 churn_events row; includes reactivation rows",
                           "has_nonreactivation_event": "account has >=1 row where is_reactivation is false; not proof of final cancellation",
                           "subscription_churn_flag_account": "account has >=1 subscription row flagged churn_flag; not deduplicated subscription count"}[name]}
                      for name, ids in labels.items()]
    mismatch_sub_vs_end = sum(flag(r.get("churn_flag")) != bool(r.get("end_date")) for r in s)
    mismatch_acct_vs_sub = len(flag_ids ^ subscription_flag_accounts)
    label_disagreement = sum(len({aid in ids for ids in labels.values()}) > 1 for aid in account_ids)

    # Event timing is a count series only; no eligible customer-time denominator exists.
    events_month = Counter(r["churn_date"][:7] for r in e)
    event_month_rows = [{"month": m, "event_rows": events_month[m],
                         "unique_accounts": len({r["account_id"] for r in e if r["churn_date"].startswith(m)}),
                         "nonreactivation_rows": sum(not flag(r["is_reactivation"]) for r in e if r["churn_date"].startswith(m)),
                         "eligible_account_denominator": None, "churn_rate": None}
                        for m in sorted(events_month)]

    segmentation = []
    for field in ("plan_tier", "industry", "country", "referral_source", "is_trial", "seats"):
        segmentation.extend(account_label_segment(a, labels, field))
    # Subscription-grain result: subscription churn flag and one row per subscription.
    sub_segment = []
    for field in ("plan_tier", "billing_frequency", "is_trial", "auto_renew_flag"):
        for val in sorted({r.get(field, "") or "UNKNOWN" for r in s}):
            rows = [r for r in s if (r.get(field, "") or "UNKNOWN") == val]
            k, n = sum(flag(r.get("churn_flag")) for r in rows), len(rows)
            lo, hi = wilson(k, n)
            sub_segment.append({"label": "subscription_churn_flag_row", "dimension": field,
                "segment": val, "subscriptions": n, "positive_subscriptions": k,
                "prevalence": k/n if n else None, "wilson_95_low": lo,
                "wilson_95_high": hi, "small_sample_flag": n < 30})

    # Usage aggregations: account-level first prevents multiplying customer metrics by tickets/events.
    usage_dups = Counter(r["usage_id"] for r in u if r.get("usage_id"))
    duplicate_ids = {k for k, v in usage_dups.items() if v > 1}
    first_by_usage = {}
    for row in u:
        first_by_usage.setdefault(row["usage_id"], row)
    unique_usage = list(first_by_usage.values())
    usage_temporal = {"rows": len(u), "duplicate_usage_ids": len(duplicate_ids),
        "rows_in_duplicate_id_groups": sum(usage_dups[x] for x in duplicate_ids),
        "excess_rows": sum(usage_dups[x]-1 for x in duplicate_ids),
        "usage_before_subscription_start": 0, "usage_after_subscription_end": 0,
        "usage_within_observed_subscription_interval": 0,
        "valid_interval_rows_after_first_duplicate_id_row": 0,
        "unique_features": len({r["feature_name"] for r in u}),
        "feature_counts": dict(Counter(r["feature_name"] for r in u)),
        "all_usage_count": sum(int(r["usage_count"]) for r in u),
        "beta_rows": sum(flag(r["is_beta_feature"]) for r in u),
        "error_count_sum": sum(int(r["error_count"]) for r in u)}
    for row in u:
        sub = sub_by_id[row["subscription_id"]]
        ud, sd, ed = date(row["usage_date"]), date(sub["start_date"]), date(sub.get("end_date"))
        if ud and sd and ud < sd:
            usage_temporal["usage_before_subscription_start"] += 1
        elif ud and ed and ud > ed:
            usage_temporal["usage_after_subscription_end"] += 1
        else:
            usage_temporal["usage_within_observed_subscription_interval"] += 1
    for row in unique_usage:
        sub = sub_by_id[row["subscription_id"]]
        ud, sd, ed = date(row["usage_date"]), date(sub["start_date"]), date(sub.get("end_date"))
        if ud and sd and ud >= sd and (ed is None or ud <= ed):
            usage_temporal["valid_interval_rows_after_first_duplicate_id_row"] += 1
    usage_account_rows = {}
    for aid in account_ids:
        rows = usage_by_account.get(aid, [])
        per_feature = Counter()
        for r in rows:
            per_feature[r["feature_name"]] += 1
        valid_rows = []
        for r in rows:
            sub = sub_by_id[r["subscription_id"]]
            ud, sd, ed = date(r["usage_date"]), date(sub["start_date"]), date(sub.get("end_date"))
            if ud and sd and ud >= sd and (ed is None or ud <= ed):
                valid_rows.append(r)
        usage_account_rows[aid] = {"all_rows": rows, "valid_rows": valid_rows, "unique_features": len(per_feature),
            "usage_sum": sum(int(r["usage_count"]) for r in rows),
            "valid_usage_sum": sum(int(r["usage_count"]) for r in valid_rows),
            "errors": sum(int(r["error_count"]) for r in rows),
            "beta_rows": sum(flag(r["is_beta_feature"]) for r in rows),
            "session_seconds": sum(int(r["usage_duration_secs"]) for r in rows)}
    usage_groups = []
    usage_differences = []
    for lname, ids in labels.items():
        for group, selected in (("positive", ids), ("negative", account_ids-ids)):
            metrics = {}
            for key in ("usage_sum", "valid_usage_sum", "unique_features", "errors", "beta_rows", "session_seconds"):
                vals = [float(usage_account_rows[aid][key]) for aid in sorted(selected)]
                metrics[key] = summarize_numeric(vals)
            usage_groups.append({"label": lname, "group": group, "accounts": len(selected), "metrics": metrics})
        for key in ("usage_sum", "valid_usage_sum", "unique_features", "errors", "beta_rows", "session_seconds"):
            pos = [float(usage_account_rows[aid][key]) for aid in sorted(ids)]
            neg = [float(usage_account_rows[aid][key]) for aid in sorted(account_ids-ids)]
            usage_differences.append({"label": lname, "measure": key,
                **bootstrap_mean_difference(pos, neg, 7100 + sum(map(ord, lname+key)))})
    usage_features = []
    for feature in sorted({r["feature_name"] for r in u}):
        for lname, ids in labels.items():
            positive_accounts = 0
            positive_rows = 0
            for aid in ids:
                rows = usage_account_rows[aid]["all_rows"]
                n = sum(r["feature_name"] == feature for r in rows)
                positive_rows += n
                positive_accounts += n > 0
            usage_features.append({"feature_name": feature, "label": lname, "accounts_with_usage": positive_accounts,
                "positive_accounts": len(ids), "account_adoption": positive_accounts/len(ids) if ids else None,
                "usage_rows": positive_rows})

    # Support analyses preserve ticket grain and report missing score denominators.
    support_groups = []
    support_differences = []
    for lname, ids in labels.items():
        support_groups += group_summary(lname, ids, account_ids, tickets_by_account,
            ["resolution_time_hours", "first_response_time_minutes", "satisfaction_score"], ["escalation_flag"])
        for field in ("resolution_time_hours", "first_response_time_minutes", "satisfaction_score"):
            means = {}
            for aid in sorted(account_ids):
                vals = [float(r[field]) for r in tickets_by_account.get(aid, []) if r.get(field, "")]
                if vals:
                    means[aid] = statistics.mean(vals)
            positive = [means[aid] for aid in sorted(ids) if aid in means]
            negative = [means[aid] for aid in sorted(account_ids-ids) if aid in means]
            support_differences.append({"label": lname, "measure": field,
                **bootstrap_mean_difference(positive, negative, 9100 + sum(map(ord, lname+field)))})
    support_segment = []
    for field in ("industry", "plan_tier", "country", "referral_source"):
        for val in sorted({x.get(field, "") or "UNKNOWN" for x in a}):
            ids = {x["account_id"] for x in a if (x.get(field, "") or "UNKNOWN") == val}
            rows = [x for x in t if x["account_id"] in ids]
            scores = [float(x["satisfaction_score"]) for x in rows if x["satisfaction_score"]]
            support_segment.append({"dimension": field, "segment": val, "accounts": len(ids), "tickets": len(rows),
                "scores_n": len(scores), "score_missing": len(rows)-len(scores),
                "satisfaction_mean": mean_or_none(scores),
                "resolution_hours_mean": mean_or_none([float(x["resolution_time_hours"]) for x in rows]),
                "first_response_minutes_mean": mean_or_none([float(x["first_response_time_minutes"]) for x in rows]),
                "escalated_tickets": sum(flag(x["escalation_flag"]) for x in rows)})

    # Financial fields are subscription-row observations; accounts have 10 rows each.
    finance = {}
    for field in ("mrr_amount", "arr_amount"):
        xs = [float(r[field]) for r in s if r.get(field, "")]
        by_label = []
        for lname, ids in labels.items():
            rows = [r for r in s if r["account_id"] in ids]
            vals = [float(r[field]) for r in rows if r.get(field, "")]
            by_label.append({"label": lname, "account_positive_group": len(ids), "subscription_rows": len(rows),
                "nonmissing_rows": len(vals), "row_sum": sum(vals), "row_mean": mean_or_none(vals),
                "row_median": statistics.median(vals) if vals else None,
                "interpretation": "subscription-row contract field sum; not unique/current/at-risk recurring revenue"})
        finance[field] = {"rows": summarize_numeric(xs), "raw_subscription_row_sum": sum(xs),
                          "zero_rows": sum(x == 0 for x in xs),
                          "positive_rows": sum(x > 0 for x in xs), "label_comparisons": by_label}
    refunds = [float(r["refund_amount_usd"]) for r in e if r.get("refund_amount_usd")]
    finance["refund_amount_usd"] = {"event_row_sum": sum(refunds), "event_rows": len(e),
        "nonzero_event_rows": sum(x > 0 for x in refunds), "mean_per_event_row": mean_or_none(refunds),
        "interpretation": "observed field sum across event rows, not recurring revenue lost"}

    # Transparent exploratory account table; it ranks observed event volume, not future risk.
    rank_rows = []
    for aid, acct in account_by_id.items():
        erows = events_by_account.get(aid, [])
        nonreact = [r for r in erows if not flag(r["is_reactivation"])]
        tr = tickets_by_account.get(aid, [])
        scores = [float(r["satisfaction_score"]) for r in tr if r["satisfaction_score"]]
        sr = subs_by_account.get(aid, [])
        ur = usage_account_rows[aid]
        reasons = Counter(r["reason_code"] for r in nonreact)
        rank_rows.append({"account_id": aid, "account_name": acct["account_name"], "industry": acct["industry"],
            "country": acct["country"], "account_plan": acct["plan_tier"], "account_churn_flag": flag(acct["churn_flag"]),
            "any_event_rows": len(erows), "nonreactivation_event_rows": len(nonreact),
            "reactivation_event_rows": len(erows)-len(nonreact), "reason_counts_nonreactivation": dict(reasons),
            "tickets": len(tr), "mean_ticket_satisfaction": mean_or_none(scores), "scored_tickets": len(scores),
            "usage_rows_all_dates": len(ur["all_rows"]), "usage_count_all_dates": ur["usage_sum"],
            "subscription_rows": len(sr), "subscription_flag_rows": sum(flag(x["churn_flag"]) for x in sr),
            "explanation": "descriptive historical records only; event volume is not future churn risk"})
    rank_rows.sort(key=lambda r: (-r["nonreactivation_event_rows"], -r["any_event_rows"], r["account_id"]))
    for i, r in enumerate(rank_rows, 1):
        r["event_volume_rank"] = i

    # Decision recommendations link to observable evidence and use no claimed causal ROI.
    recs = [
        {"priority": 1, "action": "Instrument a canonical subscription lifecycle and monthly eligible-customer snapshot",
         "target": "Data/Product Operations", "evidence": "account flag (110), any-event label (352), non-reactivation-event label (339), and subscription-flag accounts (312) disagree; 4,514 subscription rows have no end_date while 486 are flagged ended",
         "benefit": "enables valid churn denominators, lifecycle reconciliation, and future experiments", "effort": "medium; estimate only after system inventory",
         "success_metric": "reconciled account/subscription state and timestamped eligible cohort coverage", "limitation": "dataset is synthetic and conflicting; cannot infer production system causes",
         "validation": "reconcile source-of-truth events and subscription states for a prospective cohort"},
        {"priority": 2, "action": "Use reason codes and account examples as interview prompts, not root-cause verdicts",
         "target": "Customer Success / Product", "evidence": "600 event rows include reason codes features=114, support=104, budget=104, unknown=95, competitor=92, pricing=91; reactivation rows included unless filtered",
         "benefit": "structured discovery of customer-reported friction", "effort": "low-to-medium; staff time not supplied",
         "success_metric": "coded, dated interviews linked to verified lifecycle outcomes", "limitation": "reason_code is self-reported/synthetic and is not causal evidence",
         "validation": "sample cancellation interviews and compare reason consistency with subsequent lifecycle"},
        {"priority": 3, "action": "Pilot an adoption/support outreach only after a prospective eligibility rule is defined",
         "target": "Customer Success / Support", "evidence": "all-time usage per account and ticket satisfaction are descriptive and not temporally aligned; mean satisfaction 3.980 among event accounts (815 scored of 1,395 tickets) vs 3.983 among no-event accounts (360/605)",
         "benefit": "test whether targeted outreach changes retained-customer outcomes", "effort": "pilot staffing and cost unknown; budget should be set by owner",
         "success_metric": "pre-registered 90-day account retention plus guardrails for support satisfaction and cost", "limitation": "no causal uplift or recoverable revenue can be estimated from current data",
         "validation": "randomize eligible accounts to outreach vs usual care, stratify by plan and baseline usage, analyze intention-to-treat"},
    ]

    # Report-level evidence statements; summary contains raw calculated tables.
    summary = {
        "metadata": {"analysis": "conventional-descriptive-v1",
            "input_directory": data_dir.name, "libraries": ["Python standard library"],
            "source_hashes": {name: profiles[name]["sha256"] for name in TABLES}},
        "table_profiles": profiles, "key_cardinality": key_cardinality,
        "labels": {"overview": label_overview, "account_flag_event_crosstab": confusion,
            "account_vs_subscription_flag_xor_accounts": mismatch_acct_vs_sub,
            "account_flag_vs_any_event_xor_accounts": len(flag_ids ^ event_ids),
            "account_flag_vs_nonreactivation_event_xor_accounts": len(flag_ids ^ nonreact_ids),
            "any_pairwise_label_disagreement_among_accounts": label_disagreement,
            "subscription_flag_vs_nonempty_end_date_mismatched_rows": mismatch_sub_vs_end,
            "event_reactivation_rows": sum(flag(r["is_reactivation"]) for r in e),
            "event_nonreactivation_rows": len(event_nonreact_rows),
            "event_rows_by_year": dict(sorted(Counter(r["churn_date"][:4] for r in e).items())),
            "event_rows_by_month": event_month_rows,
            "reason_code_counts_all_event_rows": dict(Counter(r["reason_code"] for r in e)),
            "reason_code_counts_nonreactivation_rows": dict(Counter(r["reason_code"] for r in event_nonreact_rows)),
            "unique_accounts_by_reason_nonreactivation": {k: len({r["account_id"] for r in event_nonreact_rows if r["reason_code"] == k})
                 for k in sorted({r["reason_code"] for r in event_nonreact_rows})}},
        "segmentation": {"account_level": segmentation, "subscription_level": sub_segment},
        "support": {"by_label_and_group": support_groups, "account_level_bootstrap_differences": support_differences,
            "by_account_segment": support_segment,
            "ticket_rows": len(t), "missing_satisfaction_tickets": sum(not r["satisfaction_score"] for r in t)},
        "usage": {"integrity_and_timing": usage_temporal, "by_label_and_group": usage_groups,
            "account_level_bootstrap_differences": usage_differences, "feature_adoption": usage_features},
        "revenue": finance, "account_event_volume_ranking": rank_rows,
        "recommendations": recs,
        "limitations": ["All five tables are synthetic according to the supplied dataset README.",
            "Account churn flag, subscription churn flag, event history, and end_date do not reconcile.",
            "No reliable eligible-customer time denominator or historical snapshot is present; event counts are not churn rates.",
            "Event rows include reactivations and repeated account events; reason codes are not causal proof.",
            "Usage and support comparisons are all-time/cross-sectional unless explicitly filtered; temporal sequence is not a defensible pre-churn design.",
            "Subscription financial rows are repeated contract records; sums are not current MRR/ARR, lost revenue, or recoverable revenue.",
            "No calibrated risk model or causal intervention effect is estimated."]}
    return summary, rank_rows, segmentation, sub_segment, usage_groups, usage_features, support_groups, support_segment


def svg_charts(summary: dict, out: pathlib.Path) -> list[str]:
    labels = summary["labels"]["overview"]
    # Simple local SVG output, no plotting dependency and no claim of precision beyond counts.
    colors = ["#c39a43", "#53462d", "#8f7440", "#bdb4a2"]
    width, height, x0, y0, chart_w = 860, 360, 260, 62, 520
    maxv = max(x["positive_accounts"] for x in labels) or 1
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#171714"/>',
             '<text x="32" y="34" fill="#f4efe3" font-family="Arial" font-size="20">Account positives differ by churn label</text>']
    for i, row in enumerate(labels):
        y = y0 + i*68
        lines += [f'<text x="32" y="{y+24}" fill="#eee7d9" font-family="Arial" font-size="14">{row["label"]}</text>',
                  f'<rect x="{x0}" y="{y}" width="{chart_w}" height="30" rx="4" fill="#33322d"/>',
                  f'<rect x="{x0}" y="{y}" width="{chart_w*row["positive_accounts"]/maxv:.1f}" height="30" rx="4" fill="{colors[i%len(colors)]}"/>',
                  f'<text x="{x0+chart_w+12}" y="{y+21}" fill="#f4efe3" font-family="Arial" font-size="14">{row["positive_accounts"]} / {row["accounts"]} ({row["prevalence"]:.1%})</text>']
    lines.append('</svg>')
    (out/"label-definition-comparison.svg").write_text("\n".join(lines)+"\n", encoding="utf-8")
    years = summary["labels"]["event_rows_by_year"]
    maxy = max(years.values()) or 1
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="720" height="320" viewBox="0 0 720 320">',
             '<rect width="100%" height="100%" fill="#171714"/>',
             '<text x="28" y="32" fill="#f4efe3" font-family="Arial" font-size="19">Event rows by recorded year (not churn rates)</text>']
    for i, (year, count) in enumerate(sorted(years.items())):
        x = 170+i*210
        h = 190*count/maxy
        y = 260-h
        lines += [f'<rect x="{x}" y="{y:.1f}" width="100" height="{h:.1f}" fill="{colors[i%len(colors)]}"/>',
                  f'<text x="{x+34}" y="284" fill="#eee7d9" font-family="Arial" font-size="16">{year}</text>',
                  f'<text x="{x+36}" y="{y-9:.1f}" fill="#f4efe3" font-family="Arial" font-size="16">{count}</text>']
    lines.append('</svg>')
    (out/"event-rows-by-year.svg").write_text("\n".join(lines)+"\n", encoding="utf-8")
    return ["label-definition-comparison.svg", "event-rows-by-year.svg"]


def make_report(summary: dict) -> str:
    lab = summary["labels"]["overview"]
    cross = summary["labels"]["account_flag_event_crosstab"]
    prof = summary["table_profiles"]
    counts = ", ".join(f"{n}: {prof[n]['rows']:,} rows" for n in TABLES)
    reason = summary["labels"]["reason_code_counts_all_event_rows"]
    u = summary["usage"]["integrity_and_timing"]
    sh = summary["support"]
    def sup(label, group): return next(x for x in sh["by_label_and_group"] if x["label"]==label and x["group"]==group)
    se = sup("any_event_account", "positive")
    sn = sup("any_event_account", "negative")
    use_pos = next(x for x in summary["usage"]["by_label_and_group"] if x["label"]=="any_event_account" and x["group"]=="positive")
    use_neg = next(x for x in summary["usage"]["by_label_and_group"] if x["label"]=="any_event_account" and x["group"]=="negative")
    use_diff = next(x for x in summary["usage"]["account_level_bootstrap_differences"] if x["label"]=="any_event_account" and x["measure"]=="usage_sum")
    sat_diff = next(x for x in sh["account_level_bootstrap_differences"] if x["label"]=="any_event_account" and x["measure"]=="satisfaction_score")
    seg = summary["segmentation"]["account_level"]
    devtools = next(x for x in seg if x["label"]=="account_churn_flag" and x["dimension"]=="industry" and x["segment"]=="DevTools")
    partner = next(x for x in seg if x["label"]=="any_event_account" and x["dimension"]=="referral_source" and x["segment"]=="partner")
    uk = next(x for x in seg if x["label"]=="has_nonreactivation_event" and x["dimension"]=="country" and x["segment"]=="UK")
    annual = next(x for x in summary["segmentation"]["subscription_level"] if x["dimension"]=="billing_frequency" and x["segment"]=="annual")
    monthly = next(x for x in summary["segmentation"]["subscription_level"] if x["dimension"]=="billing_frequency" and x["segment"]=="monthly")
    top_accounts = summary["account_event_volume_ranking"][:3]
    rev = summary["revenue"]
    rec = "\n".join(f"{r['priority']}. **{r['action']}** — {r['evidence']}. Success: {r['success_metric']}. Validation: {r['validation']}." for r in summary["recommendations"])
    return f'''# Conventional churn analysis — RavenStack

## Executive conclusion

The data do not establish a conventional churn rate or a causal root cause. They contain several incompatible churn labels: **{lab[0]['positive_accounts']}** accounts with the supplied account flag, **{lab[1]['positive_accounts']}** with any event row, **{lab[2]['positive_accounts']}** with at least one non-reactivation event, and **{lab[3]['positive_accounts']}** represented by a flagged subscription. Only **{cross['account_flag_true_event_yes']}** accounts are positive under both the account flag and any-event definition. These differences are material and label-dependent.

The event record volume rises from **{summary['labels']['event_rows_by_year'].get('2023',0)}** in 2023 to **{summary['labels']['event_rows_by_year'].get('2024',0)}** in 2024, but there is no monthly eligible-account denominator; this is event volume, not an increasing churn rate. Usage and support data do not provide a defensible pre-cancellation window, while subscription revenue rows cannot be interpreted as unique current or lost revenue.

## Respostas às três perguntas do CEO

### Pergunta 1 — O que está causando o churn?

**Causa não identificada.** The event table records reason codes: {', '.join(f'{k}={v}' for k,v in sorted(reason.items()))}. These are event-row descriptions, include reactivations and repeated accounts, and do not prove causal mechanisms. By any-event account membership, mean recorded ticket satisfaction is {se['satisfaction_score']:.3f} ({se['satisfaction_score_n']}/{se['records']} scored tickets; {se['satisfaction_score_missing']} missing) versus {sn['satisfaction_score']:.3f} ({sn['satisfaction_score_n']}/{sn['records']}; {sn['satisfaction_score_missing']} missing) among other accounts. This cross-sectional difference is negligible descriptively and non-temporal; it does not establish no support effect. Usage comparisons are also cross-sectional and are distorted by lifecycle timestamp inconsistencies.

At account grain, the all-time usage-count mean is {use_pos['metrics']['usage_sum']['mean']:.1f} across {use_pos['accounts']} event-history accounts and {use_neg['metrics']['usage_sum']['mean']:.1f} across {use_neg['accounts']} other accounts; the account-level bootstrap 95% interval for the mean difference (event minus no-event) is [{use_diff['bootstrap_95_low']:.1f}, {use_diff['bootstrap_95_high']:.1f}]. This descriptive interval cannot establish temporal order or causality. For ticket satisfaction, account-cluster bootstrap difference is {sat_diff['mean_difference']:.3f}, 95% interval [{sat_diff['bootstrap_95_low']:.3f}, {sat_diff['bootstrap_95_high']:.3f}], with scored-account denominators {sat_diff['positive_accounts_with_measure']} vs {sat_diff['negative_accounts_with_measure']}; ticket-level score denominators above remain the observed score counts.

To identify causes, RavenStack would need reconciled prospective subscription states, dated exposure windows before cancellation, consistent outcome definitions, and a design that addresses confounding; reason codes should be verified through customer interviews.

### Pergunta 2 — Quais segmentos e contas estão mais em risco?

The accompanying `segment-account-labels.csv` compares account attributes under all four account-level definitions with denominators and Wilson 95% intervals. Examples: DevTools has the highest account-flag prevalence among industries ({devtools['positive_accounts']}/{devtools['accounts']} = {devtools['prevalence']:.1%}); partner-referred accounts have {partner['positive_accounts']}/{partner['accounts']} = {partner['prevalence']:.1%} with any event; and UK accounts have {uk['positive_accounts']}/{uk['accounts']} = {uk['prevalence']:.1%} with a non-reactivation event. These are label-conditioned exploratory comparisons and not stable predictive risk. At subscription grain, churn flags are nearly flat by billing frequency: annual {annual['positive_subscriptions']}/{annual['subscriptions']} = {annual['prevalence']:.1%}, monthly {monthly['positive_subscriptions']}/{monthly['subscriptions']} = {monthly['prevalence']:.1%}. Segments with fewer than 30 observations are flagged for caution.

`account-event-volume-ranking.csv` lists identifiable accounts and signals, ordered only by observed non-reactivation event count. The top event-volume records include {', '.join(f"{x['account_id']} ({x['nonreactivation_event_rows']} events)" for x in top_accounts)}. These are examples of repeated observed records for reconciliation, not accounts forecast to churn or confirmed currently at risk.

### Pergunta 3 — O que a empresa deveria fazer?

{rec}

No financial benefit or ROI is claimed. Staff effort and intervention cost were not supplied; exposure and recoverable recurring revenue remain **UNKNOWN**.

## Conventional Analysis vs. The Churn Paradox

- **Confirmed from current CSVs:** 500 accounts, 5,000 subscriptions, 25,000 usage rows, 2,000 tickets, 600 event rows; hashes are recorded in `outputs/analysis-summary.json`.
- **Label sensitivity:** account flag 110; any-event account 352; at least one non-reactivation event 339; and 312 distinct accounts with at least one flagged subscription (486 subscription rows are flagged). These are distinct account/subscription grains.
- **Reconciliation of the previously reported 312 discrepancy:** the current CSVs produce 312 accounts with different values between the account flag and any-event membership (symmetric difference), while account flag vs subscription-flag membership differs for {summary['labels']['account_vs_subscription_flag_xor_accounts']} accounts. Thus 312 is specifically the account-flag/any-event disagreement count; it is not the number with account-vs-subscription disagreement. Across all four account-level indicators, {summary['labels']['any_pairwise_label_disagreement_among_accounts']} of 500 accounts differ on at least one label.
- **Robust limitation:** annual event rows are not rates and financial row sums are not recurring revenue lost. The label conflict and chronology issues are confirmed, while their meanings depend on which fields are compared.
- **Conclusions changed by label:** segments and account comparisons vary with outcome definition; inspect the complete output CSVs before prioritizing a segment.
- **Not confirmed:** increasing churn rate, satisfaction/usage causality, root cause, recurring revenue loss, preventable exposure, model performance, intervention uplift.

## Data and method

Source tables: {counts}. Current SHA-256 values are in the output summary. Joins use account IDs or subscription IDs and retain the natural grain. Account metrics are aggregated per account before comparison; tickets/events/subscriptions are not joined into one fan-out table. Duplicate usage IDs are retained in raw totals and separately quantified: **{u['duplicate_usage_ids']} IDs, {u['rows_in_duplicate_id_groups']} rows in duplicate-ID groups, {u['excess_rows']} excess rows**. Valid-interval usage is a sensitivity only; the interval convention is start_date ≤ usage_date ≤ end_date, or no end bound where end_date is blank. It does not repair the source chronology.

The account-level label is the dataset's supplied `accounts.churn_flag`. Event labels are (1) any account with an event including reactivation and (2) any account with at least one event where `is_reactivation` is false. The second does not mean final churn. Subscription-level results use the source subscription churn flag. Wilson intervals describe binomial proportions under each observed label; they do not correct selection, synthetic generation, or label error.

Subscription financial columns are analyzed at source-row grain. Across {rev['mrr_amount']['rows']['n']:,} rows, recorded MRR values range ${rev['mrr_amount']['rows']['min']:,.0f}–${rev['mrr_amount']['rows']['max']:,.0f} (median ${rev['mrr_amount']['rows']['median']:,.0f}); ARR values range ${rev['arr_amount']['rows']['min']:,.0f}–${rev['arr_amount']['rows']['max']:,.0f} (median ${rev['arr_amount']['rows']['median']:,.0f}). There are {rev['mrr_amount']['zero_rows']} zero-valued rows. The table has repeated contract rows per account and mixed lifecycle states; even the raw row sums (${rev['mrr_amount']['raw_subscription_row_sum']:,.0f} MRR field, ${rev['arr_amount']['raw_subscription_row_sum']:,.0f} ARR field) are not unique/current/at-risk revenue. The observed event refund field sum is ${rev['refund_amount_usd']['event_row_sum']:,.2f}, across {rev['refund_amount_usd']['event_rows']} event rows, and is not lost recurring revenue.

## Outputs

- `outputs/data-profile.json`: schema, nulls, duplicate keys, hashes and table sizes.
- `outputs/analysis-summary.json`: definitions, counts, comparisons and limitations.
- `outputs/segment-account-labels.csv`, `outputs/segment-subscription-label.csv`.
- `outputs/usage-by-label.csv`, `outputs/feature-adoption.csv`.
- `outputs/support-by-label.csv`, `outputs/support-by-segment.csv`.
- `outputs/account-event-volume-ranking.csv`.
- `outputs/label-definition-comparison.svg`, `outputs/event-rows-by-year.svg`.

## Reproduction and limitations

From the standalone `solution/` directory: `python analysis/conventional/run.py --data-dir data/raw --output-dir analysis/conventional/outputs`. Run tests with `python -m unittest discover -s analysis/conventional/tests -v`. The implementation uses Python standard library only. No calibrated prediction or causal inference was attempted; there is no suitable event-time cohort or temporal holdout.
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=pathlib.Path, default=DEFAULT_DATA,
                        help="directory containing the five original RavenStack CSV files")
    parser.add_argument("--output-dir", type=pathlib.Path, default=DEFAULT_OUT,
                        help="explicit output directory (default: this module's outputs/)")
    args = parser.parse_args(argv)
    result = build(args.data_dir)
    summary, rank, seg, subseg, ug, features, support, supportseg = result
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/"data-profile.json").write_text(json.dumps(summary["table_profiles"], indent=2, default=str)+"\n", encoding="utf-8")
    (args.output_dir/"analysis-summary.json").write_text(json.dumps(summary, indent=2, default=str)+"\n", encoding="utf-8")
    write_csv(args.output_dir/"segment-account-labels.csv", seg)
    write_csv(args.output_dir/"segment-subscription-label.csv", subseg)
    write_csv(args.output_dir/"usage-by-label.csv", ug)
    write_csv(args.output_dir/"feature-adoption.csv", features)
    write_csv(args.output_dir/"support-by-label.csv", support)
    write_csv(args.output_dir/"support-by-segment.csv", supportseg)
    write_csv(args.output_dir/"account-event-volume-ranking.csv", rank)
    svg_charts(summary, args.output_dir)
    report_path = pathlib.Path(__file__).resolve().parent/"reports"/"conventional-churn-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(make_report(summary), encoding="utf-8")
    print(json.dumps({"status":"complete", "tables": {n: summary["table_profiles"][n]["rows"] for n in TABLES},
                      "labels": summary["labels"]["overview"], "output_dir": str(args.output_dir),
                      "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
