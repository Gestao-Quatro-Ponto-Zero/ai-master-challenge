from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable


def _date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (TypeError, ValueError):
        return None


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_window(data_dir: Path) -> tuple[date | None, date | None]:
    fields_by_file = {
        "ravenstack_accounts.csv": ("signup_date",),
        "ravenstack_subscriptions.csv": ("start_date", "end_date"),
        "ravenstack_feature_usage.csv": ("usage_date",),
        "ravenstack_support_tickets.csv": ("submitted_at", "closed_at"),
        "ravenstack_churn_events.csv": ("churn_date",),
    }
    values: list[date] = []
    for filename, fields in fields_by_file.items():
        path = data_dir / filename
        if not path.exists():
            continue
        for row in _read(path):
            values.extend(d for field in fields if (d := _date(row.get(field))) is not None)
    return (min(values), max(values)) if values else (None, None)


def _merge_intervals(rows: Iterable[dict[str, str]], observation_end: date) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    invalid: list[dict[str, Any]] = []
    for row in rows:
        start, end = _date(row.get("start_date")), _date(row.get("end_date"))
        if not start:
            invalid.append({"subscription_id": row.get("subscription_id"), "reason": "invalid_or_missing_start_date"})
            continue
        # Candidate convention is [start_date, end_date): end_date is the first inactive day.
        # Null end dates are right-censored at the end of the observed window.
        exclusive_end = end if end and end <= observation_end else (observation_end + timedelta(days=1) if end is None or end > observation_end else end)
        if exclusive_end <= start:
            invalid.append({"subscription_id": row.get("subscription_id"), "reason": "nonpositive_interval", "start_date": start.isoformat(), "end_date": end.isoformat() if end else None})
            continue
        grouped[(row.get("account_id", ""), row.get("plan_tier", "UNKNOWN") or "UNKNOWN")].append({
            "account_id": row.get("account_id", ""), "plan_tier": row.get("plan_tier", "UNKNOWN") or "UNKNOWN",
            "start": start, "end_exclusive": exclusive_end, "subscription_ids": [row.get("subscription_id", "")],
            "source_rows": 1, "right_censored": end is None or end > observation_end,
        })

    merged: list[dict[str, Any]] = []
    for (account_id, plan), intervals in sorted(grouped.items()):
        intervals.sort(key=lambda item: (item["start"], item["end_exclusive"]))
        current: dict[str, Any] | None = None
        for interval in intervals:
            if current is None or interval["start"] > current["end_exclusive"]:
                if current is not None:
                    merged.append(current)
                current = interval.copy()
            else:
                current["end_exclusive"] = max(current["end_exclusive"], interval["end_exclusive"])
                current["subscription_ids"].extend(interval["subscription_ids"])
                current["source_rows"] += interval["source_rows"]
                current["right_censored"] = current["right_censored"] or interval["right_censored"]
        if current is not None:
            merged.append(current)
    return merged, invalid


def _period_key(day: date, period: str) -> str:
    if period == "DAILY":
        return day.isoformat()
    if period == "WEEKLY":
        iso = day.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    if period == "MONTHLY":
        return day.strftime("%Y-%m")
    if period == "QUARTERLY":
        return f"{day.year}-Q{(day.month - 1) // 3 + 1}"
    if period == "SEMIANNUAL":
        return f"{day.year}-H{1 if day.month <= 6 else 2}"
    if period == "ANNUAL":
        return str(day.year)
    raise ValueError(f"Unsupported period: {period}")


def build_ledger(subscriptions: list[dict[str, str]], observation_start: date | None = None, observation_end: date | None = None) -> dict[str, Any]:
    valid_dates = [_date(row.get("start_date")) for row in subscriptions]
    valid_dates += [_date(row.get("end_date")) for row in subscriptions]
    observed = [value for value in valid_dates if value]
    if not observed:
        return {"metadata": {"status": "UNKNOWN", "reason": "No valid subscription dates."}, "daily": [], "periods": {}, "movements": [], "invalid_intervals": []}
    start = observation_start or min(_date(row.get("start_date")) for row in subscriptions if _date(row.get("start_date")))
    end = observation_end or max(observed)
    intervals, invalid = _merge_intervals(subscriptions, end)
    starts: dict[date, list[dict[str, Any]]] = defaultdict(list)
    ends: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for interval in intervals:
        if interval["start"] <= end and interval["end_exclusive"] > start:
            starts[max(interval["start"], start)].append(interval)
            if interval["end_exclusive"] <= end:
                ends[interval["end_exclusive"]].append(interval)

    active: set[tuple[str, str]] = set()
    ever_active: set[tuple[str, str]] = set()
    ever_customers: set[str] = set()
    lost_relations: set[tuple[str, str]] = set()
    lost_customers: set[str] = set()
    daily: list[dict[str, Any]] = []
    movements: list[dict[str, Any]] = []
    active_snapshots: dict[date, set[tuple[str, str]]] = {}
    customer_snapshots: dict[date, set[str]] = {}
    day = start
    while day <= end:
        opening = set(active)
        opening_customers = {account for account, _ in active}
        previously_seen_customers = set(ever_customers)
        ended_today = ends.get(day, [])
        ending_keys = {(row["account_id"], row["plan_tier"]) for row in ended_today}
        # A merged key can only have one interval active at a time. Remove before starts.
        for key in ending_keys:
            active.discard(key)
        new_count = react_count = 0
        for row in starts.get(day, []):
            key = (row["account_id"], row["plan_tier"])
            if key in active:
                continue
            if key in lost_relations:
                react_count += 1
                movements.append({"date": day.isoformat(), "type": "PLAN_RELATION_REACTIVATION", "account_id": key[0], "plan_tier": key[1]})
            elif key not in ever_active:
                new_count += 1
                movements.append({"date": day.isoformat(), "type": "NEW_PLAN_RELATIONSHIP", "account_id": key[0], "plan_tier": key[1]})
            active.add(key)
            ever_active.add(key)
            ever_customers.add(key[0])
            lost_relations.discard(key)
        lost_today = [key for key in ending_keys if key in opening and key not in active]
        # In normal merged intervals, ending and starting the same key on the same day was joined.
        # A gap that ends today is a true date-derived loss; later starts are reactivations.
        for key in lost_today:
            lost_relations.add(key)
            movements.append({"date": day.isoformat(), "type": "PLAN_RELATION_LOSS", "account_id": key[0], "plan_tier": key[1]})
        closing_customers = {account for account, _ in active}
        customer_losses = opening_customers - closing_customers
        customer_joins = closing_customers - opening_customers
        opening_portfolios: dict[str, int] = defaultdict(int)
        closing_portfolios: dict[str, int] = defaultdict(int)
        for account, _ in opening:
            opening_portfolios[account] += 1
        for account, _ in active:
            closing_portfolios[account] += 1
        # Expansion/contraction counts compare customers who remain commercially covered all day;
        # full customer acquisition/loss is counted separately in its own movement category.
        portfolio_accounts = opening_customers & closing_customers
        expansion_accounts = sum(closing_portfolios[a] > opening_portfolios[a] for a in portfolio_accounts)
        contraction_accounts = sum(closing_portfolios[a] < opening_portfolios[a] for a in portfolio_accounts)
        for account in portfolio_accounts:
            delta = closing_portfolios[account] - opening_portfolios[account]
            if delta > 0:
                movements.append({"date": day.isoformat(), "type": "PORTFOLIO_EXPANSION", "account_id": account, "plan_count_delta": delta})
            elif delta < 0:
                movements.append({"date": day.isoformat(), "type": "PORTFOLIO_CONTRACTION", "account_id": account, "plan_count_delta": delta})
        # Customer lifecycle types derive from whether the account had ever held any plan relation.
        for account in customer_losses:
            lost_customers.add(account)
            movements.append({"date": day.isoformat(), "type": "CUSTOMER_CHURN", "account_id": account})
        customer_reactivations = [account for account in customer_joins if account in lost_customers]
        # Correct first-time acquisition using the cumulative customer set before this date.
        new_customers = sum(1 for account in customer_joins if account not in previously_seen_customers)
        previous_ever = previously_seen_customers
        for account in customer_joins:
            if account not in previous_ever and account not in lost_customers:
                movements.append({"date": day.isoformat(), "type": "NEW_CUSTOMER", "account_id": account})
        for account in customer_reactivations:
            lost_customers.discard(account)
            movements.append({"date": day.isoformat(), "type": "CUSTOMER_REACTIVATION", "account_id": account})
        if not customer_losses and not customer_joins:
            pass
        closing = set(active)
        active_snapshots[day] = closing
        customer_snapshots[day] = closing_customers
        opening_count = len(opening)
        daily.append({
            "date": day.isoformat(), "opening_plan_relations": opening_count,
            "plan_relation_losses": len(lost_today), "new_plan_relationships": new_count,
            "plan_relation_reactivations": react_count, "closing_plan_relations": len(closing),
            "retained_plan_relationships": len(opening & closing),
            "daily_plan_churn_rate_pct": (len(lost_today) / opening_count * 100) if opening_count else None,
            "opening_customers": len(opening_customers), "customer_churn": len(customer_losses),
            "new_customers": new_customers, "customer_reactivations": len(customer_reactivations),
            "closing_customers": len(closing_customers),
            "portfolio_expansion_accounts": expansion_accounts, "portfolio_contraction_accounts": contraction_accounts,
            "daily_customer_churn_rate_pct": (len(customer_losses) / len(opening_customers) * 100) if opening_customers else None,
        })
        day += timedelta(days=1)
    return {
        "metadata": {"status": "CONDITIONAL_DATE_RECONSTRUCTION", "grain": "ACCOUNT × PLAN_TIER × CIVIL_DAY", "observation_start": start.isoformat(), "observation_end": end.isoformat(), "earliest_subscription_start": min(_date(row.get("start_date")) for row in subscriptions if _date(row.get("start_date"))).isoformat(), "interval_rule": "[start_date, end_date); null end_date is right-censored through observation_end", "actual_product_identity": "NOT_IDENTIFIABLE", "plan_identity": "PLAN-LEVEL PROXY", "timezone": "UNKNOWN; source dates are date-only"},
        "daily": daily, "movements": movements, "intervals": intervals, "invalid_intervals": invalid,
        "active_snapshots": active_snapshots, "customer_snapshots": customer_snapshots,
    }


def aggregate_periods(
    ledger: dict[str, Any],
    periods: tuple[str, ...] = ("WEEKLY", "MONTHLY", "QUARTERLY", "SEMIANNUAL", "ANNUAL"),
    account_dimensions: dict[str, dict[str, str]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    daily_rows = ledger.get("daily", [])
    snapshots: dict[date, set[tuple[str, str]]] = ledger.get("active_snapshots", {})
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = {name: defaultdict(list) for name in periods}
    for row in daily_rows:
        d = date.fromisoformat(row["date"])
        for name in periods:
            grouped[name][_period_key(d, name)].append(row)
    out: dict[str, list[dict[str, Any]]] = {}
    for name, buckets in grouped.items():
        records = []
        for key, rows in buckets.items():
            first, last = date.fromisoformat(rows[0]["date"]), date.fromisoformat(rows[-1]["date"])
            opening = snapshots.get(first - timedelta(days=1), set())
            if not opening:
                # The first observable day has an empty pre-window opening population by construction.
                opening = set()
            closing = snapshots.get(last, set())
            gross_losses = sum(r["plan_relation_losses"] for r in rows)
            initial_loss_any = {tuple((m["account_id"], m["plan_tier"])) for m in ledger["movements"] if m["type"] == "PLAN_RELATION_LOSS" and first.isoformat() <= m["date"] <= last.isoformat() and (m["account_id"], m["plan_tier"]) in opening}
            opening_customers = ledger["customer_snapshots"].get(first - timedelta(days=1), set())
            closing_customers = ledger["customer_snapshots"].get(last, set())
            opening_customer_loss_any = {m["account_id"] for m in ledger["movements"] if m["type"] == "CUSTOMER_CHURN" and first.isoformat() <= m["date"] <= last.isoformat() and m["account_id"] in opening_customers}
            opening_customer_loss_close = opening_customers - closing_customers
            plan_reactivations = [m for m in ledger["movements"] if m["type"] == "PLAN_RELATION_REACTIVATION" and first.isoformat() <= m["date"] <= last.isoformat()]
            period_plan_losses = [m for m in ledger["movements"] if m["type"] == "PLAN_RELATION_LOSS" and first.isoformat() <= m["date"] <= last.isoformat()]
            period_plan_starts = [m for m in ledger["movements"] if m["type"] == "NEW_PLAN_RELATIONSHIP" and first.isoformat() <= m["date"] <= last.isoformat()]
            plan_names = sorted({plan for _, plan in opening | closing} | {m["plan_tier"] for m in period_plan_losses + period_plan_starts + plan_reactivations})
            plan_segments = []
            for plan in plan_names:
                opening_plan = {key for key in opening if key[1] == plan}
                closing_plan = {key for key in closing if key[1] == plan}
                opening_loss_plan = {key for key in initial_loss_any if key[1] == plan}
                plan_segments.append({
                    "plan_tier": plan,
                    "opening_relations": len(opening_plan),
                    "new_relations": sum(m["plan_tier"] == plan for m in period_plan_starts),
                    "reactivations": sum(m["plan_tier"] == plan for m in plan_reactivations),
                    "gross_loss_events": sum(m["plan_tier"] == plan for m in period_plan_losses),
                    "opening_relations_lost_any_time": len(opening_loss_plan),
                    "opening_relations_lost_at_close": len(opening_plan - closing_plan),
                    "closing_relations": len(closing_plan),
                    "opening_cohort_loss_rate_pct": len(opening_loss_plan) / len(opening_plan) * 100 if opening_plan else None,
                })
            account_segments: dict[str, list[dict[str, Any]]] = {}
            dimensions = account_dimensions or {}
            period_movements = [movement for movement in ledger["movements"] if first.isoformat() <= movement["date"] <= last.isoformat()]
            flow_counts: dict[str, dict[str, Counter[str]]] = {
                dimension: defaultdict(Counter) for dimension in ("industry", "country", "referral_source")
            }
            movement_accounts: set[str] = set()
            for movement in period_movements:
                account_id = movement["account_id"]
                movement_accounts.add(account_id)
                for dimension in flow_counts:
                    label = str(dimensions.get(account_id, {}).get(dimension) or "UNKNOWN")
                    flow_counts[dimension][label][movement["type"]] += 1
            for dimension in ("industry", "country", "referral_source"):
                period_accounts = opening_customers | closing_customers | movement_accounts
                labels = sorted({str(dimensions.get(account, {}).get(dimension) or "UNKNOWN") for account in period_accounts})
                segment_rows = []
                for label in labels:
                    segment_open = {account for account in opening_customers if str(dimensions.get(account, {}).get(dimension) or "UNKNOWN") == label}
                    segment_close = {account for account in closing_customers if str(dimensions.get(account, {}).get(dimension) or "UNKNOWN") == label}
                    segment_open_relations = {key for key in opening if key[0] in segment_open}
                    segment_close_relations = {key for key in closing if key[0] in segment_close}
                    segment_loss_accounts = opening_customer_loss_any & segment_open
                    segment_loss_relations = initial_loss_any & segment_open_relations
                    segment_rows.append({
                        "segment": label,
                        "opening_customers": len(segment_open),
                        "new_customers": flow_counts[dimension][label]["NEW_CUSTOMER"],
                        "customer_reactivations": flow_counts[dimension][label]["CUSTOMER_REACTIVATION"],
                        "opening_customers_lost_any_time": len(segment_loss_accounts),
                        "opening_customers_lost_at_close": len(segment_open - segment_close),
                        "closing_customers": len(segment_close),
                        "opening_customer_loss_rate_pct": len(segment_loss_accounts) / len(segment_open) * 100 if segment_open else None,
                        "opening_plan_relations": len(segment_open_relations),
                        "new_plan_relationships": flow_counts[dimension][label]["NEW_PLAN_RELATIONSHIP"],
                        "plan_reactivations": flow_counts[dimension][label]["PLAN_RELATION_REACTIVATION"],
                        "gross_plan_loss_events": flow_counts[dimension][label]["PLAN_RELATION_LOSS"],
                        "opening_relations_lost_any_time": len(segment_loss_relations),
                        "opening_relations_lost_at_close": len(segment_open_relations - segment_close_relations),
                        "closing_plan_relations": len(segment_close_relations),
                        "opening_plan_loss_rate_pct": len(segment_loss_relations) / len(segment_open_relations) * 100 if segment_open_relations else None,
                    })
                account_segments[dimension] = segment_rows
            upgrades = [m for m in ledger["movements"] if m["type"] == "POSSIBLE_UPGRADE" and first.isoformat() <= m["date"] <= last.isoformat()]
            downgrades = [m for m in ledger["movements"] if m["type"] == "POSSIBLE_DOWNGRADE" and first.isoformat() <= m["date"] <= last.isoformat()]
            expansions = [m for m in ledger["movements"] if m["type"] == "PORTFOLIO_EXPANSION" and first.isoformat() <= m["date"] <= last.isoformat()]
            contractions = [m for m in ledger["movements"] if m["type"] == "PORTFOLIO_CONTRACTION" and first.isoformat() <= m["date"] <= last.isoformat()]
            records.append({
                "period": key, "period_type": name, "start_date": first.isoformat(), "end_date": last.isoformat(),
                "opening_plan_relations": len(opening), "new_plan_relationships": sum(r["new_plan_relationships"] for r in rows),
                "reactivated_plan_relationships": sum(r["plan_relation_reactivations"] for r in rows),
                "gross_plan_relation_loss_events": gross_losses,
                "opening_relations_lost_any_time": len(initial_loss_any),
                "opening_relations_lost_at_close": len(opening - closing),
                "opening_relations_lost_then_active_at_close": len(initial_loss_any - (opening - closing)),
                "unique_plan_relations_with_loss_events": len({(m["account_id"], m["plan_tier"]) for m in ledger["movements"] if m["type"] == "PLAN_RELATION_LOSS" and first.isoformat() <= m["date"] <= last.isoformat()}),
                "closing_plan_relations": len(closing), "net_change": len(closing) - len(opening),
                "plan_relation_bridge_residual": len(opening) - gross_losses + sum(r["new_plan_relationships"] for r in rows) + len(plan_reactivations) - len(closing),
                "opening_cohort_churn_any_pct": len(initial_loss_any) / len(opening) * 100 if opening else None,
                "opening_cohort_churn_at_close_pct": len(opening - closing) / len(opening) * 100 if opening else None,
                "opening_customers": len(opening_customers), "closing_customers": len(closing_customers),
                "opening_customers_lost_any_time": len(opening_customer_loss_any),
                "opening_customers_lost_at_close": len(opening_customer_loss_close),
                "opening_cohort_customer_churn_any_pct": len(opening_customer_loss_any) / len(opening_customers) * 100 if opening_customers else None,
                "opening_cohort_customer_churn_at_close_pct": len(opening_customer_loss_close) / len(opening_customers) * 100 if opening_customers else None,
                "gross_customer_churn_events": sum(r["customer_churn"] for r in rows),
                "new_customers": sum(r["new_customers"] for r in rows),
                "customer_reactivations": sum(r["customer_reactivations"] for r in rows),
                "customer_bridge_residual": len(opening_customers) + sum(r["new_customers"] for r in rows) + sum(r["customer_reactivations"] for r in rows) - sum(r["customer_churn"] for r in rows) - len(closing_customers),
                "plan_reactivations": len(plan_reactivations), "possible_upgrade_candidates": len(upgrades),
                "possible_downgrade_candidates": len(downgrades), "portfolio_expansion_events": len(expansions),
                "portfolio_contraction_events": len(contractions), "plan_segments": plan_segments,
                "account_segments": account_segments,
                "methodology": "All period values aggregate the daily reconstructed ledger; percentages are period-cohort measures, not averages of daily rates.",
            })
        out[name] = records
    return out


def _event_reconciliation(data_dir: Path, ledger: dict[str, Any]) -> dict[str, Any]:
    events_path = data_dir / "ravenstack_churn_events.csv"
    events = _read(events_path)
    loss_days: dict[date, set[str]] = defaultdict(set)
    loss_dates_by_account: dict[str, list[date]] = defaultdict(list)
    for movement in ledger["movements"]:
        if movement["type"] == "PLAN_RELATION_LOSS":
            loss_date = date.fromisoformat(movement["date"])
            loss_days[loss_date].add(movement["account_id"])
            loss_dates_by_account[movement["account_id"]].append(loss_date)
    windows = (0, 1, 7, 30, 60)
    summary = {"event_rows": len(events), "rows_on_account_plan_loss_date": 0, "unique_event_accounts": len({x["account_id"] for x in events}), "ambiguous_account_only_linkage": True, "window_counts": {str(window): 0 for window in windows}, "by_reason": {}}
    for event in events:
        d = _date(event.get("churn_date"))
        reason = event.get("reason_code") or "UNKNOWN"
        bucket = summary["by_reason"].setdefault(reason, {"event_rows": 0, "rows_on_plan_loss_date": 0, "window_counts": {str(window): 0 for window in windows}, "accounts": set()})
        bucket["event_rows"] += 1
        bucket["accounts"].add(event.get("account_id", ""))
        exact = bool(d and event.get("account_id") in loss_days.get(d, set()))
        if exact:
            summary["rows_on_account_plan_loss_date"] += 1
            bucket["rows_on_plan_loss_date"] += 1
        distances = [abs((d - loss_date).days) for loss_date in loss_dates_by_account.get(event.get("account_id", ""), [])] if d else []
        nearest = min(distances) if distances else None
        for window in windows:
            if nearest is not None and nearest <= window:
                summary["window_counts"][str(window)] += 1
                bucket["window_counts"][str(window)] += 1
    for value in summary["by_reason"].values():
        value["unique_accounts"] = len(value.pop("accounts"))
    summary["events_without_same_day_account_plan_loss"] = len(events) - summary["rows_on_account_plan_loss_date"]
    return summary


def _classify_plan_transitions(ledger: dict[str, Any], subscriptions: list[dict[str, str]]) -> dict[str, Any]:
    # Tier ordering is a scenario assumption inferred from names, not a source-defined contract hierarchy.
    rank = {"Basic": 1, "Pro": 2, "Enterprise": 3}
    intervals = ledger["intervals"]
    candidates: list[dict[str, Any]] = []
    all_windows = (0, 1, 7, 30)
    for ending in intervals:
        loss_day = ending["end_exclusive"]
        if ending["right_censored"] or loss_day > date.fromisoformat(ledger["metadata"]["observation_end"]):
            continue
        account, outgoing = ending["account_id"], ending["plan_tier"]
        for incoming_interval in intervals:
            if incoming_interval["account_id"] != account or incoming_interval["plan_tier"] == outgoing:
                continue
            incoming = incoming_interval["plan_tier"]
            incoming_day = incoming_interval["start"]
            if incoming_day < loss_day < incoming_interval["end_exclusive"]:
                delta, timing = 0, "LOWER_OR_HIGHER_PLAN_ALREADY_ACTIVE_AT_LOSS"
            elif incoming_day == loss_day:
                delta, timing = 0, "NEW_PLAN_START_SAME_DAY_AS_LOSS"
            else:
                delta, timing = (incoming_day - loss_day).days, "NEW_PLAN_START_AFTER_LOSS"
                if delta < 0 or delta > max(all_windows):
                    continue
            if incoming not in rank or outgoing not in rank:
                direction = "UNCLASSIFIED_TRANSITION"
            else:
                direction = "POSSIBLE_DOWNGRADE" if rank[incoming] < rank[outgoing] else "POSSIBLE_UPGRADE" if rank[incoming] > rank[outgoing] else "UNCLASSIFIED_TRANSITION"
            candidates.append({"date": loss_day.isoformat(), "type": direction, "account_id": account, "from_plan": outgoing, "to_plan": incoming, "days_between_loss_and_start": delta, "transition_timing": timing, "classification": "POSSIBLE; no contract linkage or verified tier hierarchy"})
    for candidate in candidates:
        ledger["movements"].append(candidate)
    upgrade_rows = [row for row in subscriptions if str(row.get("upgrade_flag", "")).strip().lower() in {"true", "1", "yes"}]
    downgrade_rows = [row for row in subscriptions if str(row.get("downgrade_flag", "")).strip().lower() in {"true", "1", "yes"}]
    both_rows = [row for row in subscriptions if row in upgrade_rows and row in downgrade_rows]
    source_flags = {
        "reported_upgrade_flag_rows": sum(str(row.get("upgrade_flag", "")).strip().lower() in {"true", "1", "yes"} for row in subscriptions),
        "reported_downgrade_flag_rows": sum(str(row.get("downgrade_flag", "")).strip().lower() in {"true", "1", "yes"} for row in subscriptions),
        "accounts_with_reported_upgrade_flag": len({row.get("account_id") for row in upgrade_rows}),
        "accounts_with_reported_downgrade_flag": len({row.get("account_id") for row in downgrade_rows}),
        "rows_with_both_reported_flags": len(both_rows),
    }
    window_summary = {}
    for window in all_windows:
        selected = [row for row in candidates if row["days_between_loss_and_start"] <= window]
        window_summary[str(window)] = {
            "possible_upgrade_pairs": sum(row["type"] == "POSSIBLE_UPGRADE" for row in selected),
            "possible_downgrade_pairs": sum(row["type"] == "POSSIBLE_DOWNGRADE" for row in selected),
            "unique_accounts": len({row["account_id"] for row in selected}),
        }
    return {"classification": "POSSIBLE_ONLY", "assumed_plan_order": rank, "plan_order_evidence": "No documented rank field; labels Basic/Pro/Enterprise suggest an ordering but it is not verified. Candidate directions are not confirmed migrations.", "source_flags": source_flags, "windows_days": window_summary, "candidate_transitions": candidates}


def analyze(data_dir: Path) -> dict[str, Any]:
    data_dir = Path(data_dir)
    subscriptions = _read(data_dir / "ravenstack_subscriptions.csv")
    accounts = {row["account_id"]: row for row in _read(data_dir / "ravenstack_accounts.csv")}
    window_start, window_end = _source_window(data_dir)
    ledger = build_ledger(subscriptions, window_start, window_end)
    transition_analysis = _classify_plan_transitions(ledger, subscriptions)
    periods = aggregate_periods(ledger, account_dimensions=accounts)
    event_rows_by_month: dict[str, list[dict[str, str]]] = defaultdict(list)
    for event in _read(data_dir / "ravenstack_churn_events.csv"):
        event_day = _date(event.get("churn_date"))
        if event_day:
            event_rows_by_month[event_day.strftime("%Y-%m")].append(event)
    for period in periods.get("MONTHLY", []):
        event_rows = event_rows_by_month.get(period["period"], [])
        nonreactivation_rows = [event for event in event_rows if str(event.get("is_reactivation", "")).strip().lower() not in {"true", "1", "yes"}]
        period.update({
            "recorded_event_rows": len(event_rows),
            "recorded_event_accounts": len({event.get("account_id") for event in event_rows if event.get("account_id")}),
            "recorded_nonreactivation_event_rows": len(nonreactivation_rows),
            "recorded_reactivation_event_rows": len(event_rows) - len(nonreactivation_rows),
            "recorded_events_per_opening_customer_pct": len(event_rows) / period["opening_customers"] * 100 if period["opening_customers"] else None,
            "recorded_event_interpretation": "Event-row frequency normalized by date-reconstructed opening customers; not a churn rate or event-to-customer causal match.",
        })
    annual_monthly_summary: dict[str, dict[str, Any]] = {}
    for year in sorted({row["period"][:4] for row in periods.get("MONTHLY", [])}):
        year_months = [row for row in periods["MONTHLY"] if row["period"].startswith(year)]
        account_months = sum(row["opening_customers"] for row in year_months)
        relation_months = sum(row["opening_plan_relations"] for row in year_months)
        total_events = sum(row["recorded_event_rows"] for row in year_months)
        total_losses = sum(row["gross_plan_relation_loss_events"] for row in year_months)
        annual_monthly_summary[year] = {
            "months": len(year_months),
            "opening_customers_first_month": year_months[0]["opening_customers"],
            "closing_customers_last_month": year_months[-1]["closing_customers"],
            "opening_account_months": account_months,
            "new_customers": sum(row["new_customers"] for row in year_months),
            "customer_reactivations": sum(row["customer_reactivations"] for row in year_months),
            "complete_customer_loss_events": sum(row["gross_customer_churn_events"] for row in year_months),
            "opening_plan_relations_first_month": year_months[0]["opening_plan_relations"],
            "closing_plan_relations_last_month": year_months[-1]["closing_plan_relations"],
            "opening_plan_relation_months": relation_months,
            "new_plan_relationships": sum(row["new_plan_relationships"] for row in year_months),
            "plan_reactivations": sum(row["reactivated_plan_relationships"] for row in year_months),
            "gross_plan_loss_events": total_losses,
            "opening_cohort_plan_losses_sum": sum(row["opening_relations_lost_any_time"] for row in year_months),
            "recorded_event_rows": total_events,
            "recorded_event_rows_per_100_opening_account_months": total_events / account_months * 100 if account_months else None,
            "customer_coverage_loss_events_per_100_opening_account_months": sum(row["gross_customer_churn_events"] for row in year_months) / account_months * 100 if account_months else None,
            "plan_loss_events_per_100_opening_relation_months": total_losses / relation_months * 100 if relation_months else None,
            "classification": "Conditional exposure-normalized descriptions from date-reconstructed monthly openings; not certified churn rates.",
        }
    event_reconciliation = _event_reconciliation(data_dir, ledger)
    plan_bridge_failures = [row["date"] for row in ledger["daily"] if row["opening_plan_relations"] - row["plan_relation_losses"] + row["new_plan_relationships"] + row["plan_relation_reactivations"] != row["closing_plan_relations"]]
    customer_bridge_failures = [row["date"] for row in ledger["daily"] if row["opening_customers"] + row["new_customers"] + row["customer_reactivations"] - row["customer_churn"] != row["closing_customers"]]
    customer_snapshot_by_date = {d.isoformat(): {account for account, _ in keys} for d, keys in ledger["active_snapshots"].items()}
    plan_loss_movements = [m for m in ledger["movements"] if m["type"] == "PLAN_RELATION_LOSS"]
    loss_accounts_retained = {m["account_id"] for m in plan_loss_movements if m["account_id"] in customer_snapshot_by_date.get(m["date"], set())}
    loss_accounts_fully_lost = {m["account_id"] for m in plan_loss_movements if m["account_id"] not in customer_snapshot_by_date.get(m["date"], set())}
    plan_totals: dict[str, dict[str, Any]] = defaultdict(lambda: {"source_subscription_rows": 0, "distinct_accounts": 0, "loss_events": 0, "new_relations": 0, "reactivations": 0})
    for row in subscriptions:
        plan_totals[row.get("plan_tier") or "UNKNOWN"]["source_subscription_rows"] += 1
    accounts_by_plan: dict[str, set[str]] = defaultdict(set)
    for interval in ledger["intervals"]:
        accounts_by_plan[interval["plan_tier"]].add(interval["account_id"])
    for plan, plan_accounts in accounts_by_plan.items():
        plan_totals[plan]["distinct_accounts"] = len(plan_accounts)
    initial_2024 = ledger["active_snapshots"].get(date(2023, 12, 31), set())
    closing_2024 = ledger["active_snapshots"].get(date(2024, 12, 31), set())
    for plan, counts in plan_totals.items():
        opening_keys = {key for key in initial_2024 if key[1] == plan}
        closing_keys = {key for key in closing_2024 if key[1] == plan}
        lost_any = {(m["account_id"], m["plan_tier"]) for m in ledger["movements"] if m["type"] == "PLAN_RELATION_LOSS" and m["date"].startswith("2024-") and m["plan_tier"] == plan} & opening_keys
        counts["opening_2024_relations"] = len(opening_keys)
        counts["opening_2024_relations_lost_any_time"] = len(lost_any)
        counts["opening_2024_relations_lost_at_close"] = len(opening_keys - closing_keys)
        counts["closing_2024_relations"] = len(closing_keys)
        counts["opening_2024_cohort_loss_pct"] = len(lost_any) / len(opening_keys) * 100 if opening_keys else None
    for move in ledger["movements"]:
        plan = move.get("plan_tier")
        if not plan:
            continue
        key = {"PLAN_RELATION_LOSS": "loss_events", "NEW_PLAN_RELATIONSHIP": "new_relations", "PLAN_RELATION_REACTIVATION": "reactivations"}.get(move["type"])
        if key:
            plan_totals[plan][key] += 1
    losses_by_account: dict[str, int] = defaultdict(int)
    customer_loss_accounts = {m["account_id"] for m in ledger["movements"] if m["type"] == "CUSTOMER_CHURN"}
    for movement in ledger["movements"]:
        if movement["type"] == "PLAN_RELATION_LOSS":
            losses_by_account[movement["account_id"]] += 1
    segment_summary: dict[str, list[dict[str, Any]]] = {}
    for dimension in ("industry", "country", "referral_source", "plan_tier", "is_trial"):
        buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {"accounts": set(), "accounts_with_plan_loss": set(), "accounts_with_customer_loss": set(), "plan_loss_events": 0})
        for account_id, account in accounts.items():
            bucket = buckets[str(account.get(dimension) or "UNKNOWN")]
            bucket["accounts"].add(account_id)
            if losses_by_account.get(account_id, 0):
                bucket["accounts_with_plan_loss"].add(account_id)
                bucket["plan_loss_events"] += losses_by_account[account_id]
            if account_id in customer_loss_accounts:
                bucket["accounts_with_customer_loss"].add(account_id)
        segment_summary[dimension] = [{"segment": label, "account_denominator": len(value["accounts"]), "accounts_with_plan_loss": len(value["accounts_with_plan_loss"]), "plan_loss_events": value["plan_loss_events"], "accounts_with_customer_loss": len(value["accounts_with_customer_loss"]), "evidence": "CONDITIONAL_DATE_RECONSTRUCTION"} for label, value in sorted(buckets.items())]
    account_movements = []
    for account_id in sorted(set(losses_by_account) | customer_loss_accounts):
        account = accounts.get(account_id, {})
        account_movements.append({"account_id": account_id, "industry": account.get("industry"), "country": account.get("country"), "referral_source": account.get("referral_source"), "account_plan_tier": account.get("plan_tier"), "plan_loss_events": losses_by_account.get(account_id, 0), "complete_customer_loss_events": sum(1 for m in ledger["movements"] if m["type"] == "CUSTOMER_CHURN" and m["account_id"] == account_id), "classification": "DATE-RECONCILIATION CANDIDATE; not future risk"})
    account_movements.sort(key=lambda row: (-row["complete_customer_loss_events"], -row["plan_loss_events"], row["account_id"]))
    source_files = [data_dir / name for name in ("ravenstack_accounts.csv", "ravenstack_subscriptions.csv", "ravenstack_feature_usage.csv", "ravenstack_support_tickets.csv", "ravenstack_churn_events.csv")]
    boundary_snapshots = {}
    for boundary in (date(2023, 1, 1), date(2024, 1, 1), date(2024, 12, 31)):
        relations = ledger["active_snapshots"].get(boundary, set())
        boundary_snapshots[boundary.isoformat()] = {"unique_active_accounts": len({account for account, _ in relations}), "account_plan_proxy_relations": len(relations), "classification": "DATE-RECONSTRUCTED SNAPSHOT; conditional on interval semantics"}
    boundary_snapshots["2024-01-01"]["ledger_opening_accounts_before_date_transitions"] = len({account for account, _ in ledger["active_snapshots"].get(date(2023, 12, 31), set())})
    result: dict[str, Any] = {
        "metadata": {**ledger["metadata"], "source_hashes_sha256": {path.name: _sha256(path) for path in source_files}, "source_schema": {path.name: list(_read(path)[0].keys()) for path in source_files}}, "summary": {
            "daily_rows": len(ledger["daily"]), "plan_relation_loss_events": sum(r["plan_relation_losses"] for r in ledger["daily"]),
            "new_plan_relationships": sum(r["new_plan_relationships"] for r in ledger["daily"]),
            "plan_relation_reactivations": sum(r["plan_relation_reactivations"] for r in ledger["daily"]),
            "customer_churn_events": sum(r["customer_churn"] for r in ledger["daily"]),
            "new_customers": sum(r["new_customers"] for r in ledger["daily"]),
            "customer_reactivations": sum(r["customer_reactivations"] for r in ledger["daily"]),
            "portfolio_expansion_events": sum(r["portfolio_expansion_accounts"] for r in ledger["daily"]),
            "portfolio_contraction_events": sum(r["portfolio_contraction_accounts"] for r in ledger["daily"]),
            "possible_upgrade_pairs_30d": transition_analysis["windows_days"]["30"]["possible_upgrade_pairs"],
            "possible_downgrade_pairs_30d": transition_analysis["windows_days"]["30"]["possible_downgrade_pairs"],
            "unique_accounts_with_plan_loss": len({m["account_id"] for m in plan_loss_movements}),
            "plan_loss_events_with_customer_retained": sum(m["account_id"] in customer_snapshot_by_date.get(m["date"], set()) for m in plan_loss_movements),
            "plan_loss_events_with_complete_customer_loss": sum(m["account_id"] not in customer_snapshot_by_date.get(m["date"], set()) for m in plan_loss_movements),
            "unique_accounts_retaining_other_plan_after_loss": len(loss_accounts_retained),
            "unique_accounts_losing_all_plans": len(loss_accounts_fully_lost),
            "unique_accounts_with_portfolio_expansion": len({m["account_id"] for m in ledger["movements"] if m["type"] == "PORTFOLIO_EXPANSION"}),
            "unique_accounts_with_portfolio_contraction": len({m["account_id"] for m in ledger["movements"] if m["type"] == "PORTFOLIO_CONTRACTION"}),
            "source_reported_upgrade_flag_rows": transition_analysis["source_flags"]["reported_upgrade_flag_rows"],
            "source_reported_downgrade_flag_rows": transition_analysis["source_flags"]["reported_downgrade_flag_rows"],
            "invalid_intervals": len(ledger["invalid_intervals"]), "merged_plan_relation_intervals": len(ledger["intervals"]),
            "plan_bridge_failure_days": len(plan_bridge_failures), "customer_bridge_failure_days": len(customer_bridge_failures),
        },
        "reconciliation": {"daily_plan_bridge_failures": plan_bridge_failures, "daily_customer_bridge_failures": customer_bridge_failures},
        "calendar_boundary_snapshots": boundary_snapshots,
        "annual_monthly_summary": annual_monthly_summary,
        "periods": periods, "event_reconciliation": event_reconciliation,
        "plan_transition_analysis": transition_analysis,
        "plan_proxy_summary": [{"plan_tier": k, **v} for k, v in sorted(plan_totals.items())],
        "segment_summary": segment_summary, "account_movement_candidates": account_movements,
        "financial_metrics": {"status": "UNKNOWN", "revenue_expansion": None, "revenue_contraction": None, "gross_revenue_churn": None, "net_revenue_churn": None, "reason": "MRR/ARR are recorded per subscription row without verified currency, effective period, row-version/snapshot semantics, or an authoritative account-plan billing ledger. Aggregating them as recurring revenue would risk duplicate or incompatible contract values."},
        "daily": ledger["daily"], "movements": ledger["movements"], "invalid_intervals": ledger["invalid_intervals"],
        "assumptions": [
            "No stable product/service identifier exists; plan_tier is used only as a PLAN-LEVEL PROXY.",
            "The source description says end_date means ended and null means active; commercial effective-date semantics remain unverified.",
            "Intervals use civil-date [start_date, end_date); end_date is treated as the first inactive date under an explicit candidate convention.",
            "Rows with null end_date are right-censored at the last observed source date, not treated as verified active beyond it.",
            "Overlapping or adjacent rows for the same account and plan are merged; distinct plan transitions are not asserted to be product migration.",
            "Daily rates are date-reconstructed conditional metrics, not commercially verified customer/product churn.",
            "Events join by account and date only; no product/event foreign key exists, so a same-day match is contextual, not causal linkage.",
        ],
    }
    return result


def write_outputs(data_dir: Path, output_dir: Path) -> dict[str, Any]:
    result = analyze(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "daily-portfolio-churn.json").write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    for period, rows in result["periods"].items():
        if not rows:
            continue
        with (output_dir / f"{period.lower()}-portfolio-summary.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    monthly_segments = [
        {"period": row["period"], **segment}
        for row in result["periods"].get("MONTHLY", [])
        for segment in row.get("plan_segments", [])
    ]
    if monthly_segments:
        with (output_dir / "monthly-plan-segment-summary.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(monthly_segments[0]))
            writer.writeheader()
            writer.writerows(monthly_segments)
    monthly_account_segments = [
        {"period": row["period"], "dimension": dimension, **segment}
        for row in result["periods"].get("MONTHLY", [])
        for dimension, segments in row.get("account_segments", {}).items()
        for segment in segments
    ]
    if monthly_account_segments:
        with (output_dir / "monthly-account-segment-summary.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(monthly_account_segments[0]))
            writer.writeheader()
            writer.writerows(monthly_account_segments)
    if result.get("annual_monthly_summary"):
        rows = [{"year": year, **values} for year, values in result["annual_monthly_summary"].items()]
        with (output_dir / "annual-monthly-summary.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    with (output_dir / "daily-ledger.csv").open("w", newline="", encoding="utf-8") as f:
        rows = result["daily"]
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    with (output_dir / "movement-ledger.csv").open("w", newline="", encoding="utf-8") as f:
        rows = result["movements"]
        if rows:
            fields = list(dict.fromkeys(key for row in rows for key in row))
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    with (output_dir / "plan-proxy-summary.csv").open("w", newline="", encoding="utf-8") as f:
        rows = result["plan_proxy_summary"]
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return result
