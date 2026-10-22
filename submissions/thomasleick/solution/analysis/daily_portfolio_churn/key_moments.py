"""Deterministic business moments derived from the daily portfolio ledger."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable


EVIDENCE = "CONDITIONAL_DATE_RECONSTRUCTION · PLAN-LEVEL PROXY"


def _month(value: str | None) -> str:
    return (value or "")[:7]


def _safe_int(value: Any) -> int:
    return int(value or 0)


def _account_movements(movements: list[dict[str, Any]], month: str, accepted: set[str]) -> tuple[list[dict[str, Any]], int]:
    grouped: dict[str, dict[str, Any]] = {}
    for movement in movements:
        if _month(movement.get("date")) != month or movement.get("type") not in accepted:
            continue
        account_id = movement.get("account_id")
        if not account_id:
            continue
        item = grouped.setdefault(account_id, {"account_id": account_id, "movement_types": set(), "plans": set(), "dates": set()})
        item["movement_types"].add(movement.get("type"))
        item["dates"].add(movement.get("date"))
        for key in ("plan_tier", "from_plan", "to_plan"):
            if movement.get(key):
                item["plans"].add(movement[key])
    result = [
        {
            "account_id": account_id,
            "movement_types": sorted(item["movement_types"]),
            "plans": sorted(item["plans"]),
            "dates": sorted(item["dates"]),
        }
        for account_id, item in sorted(grouped.items())
    ]
    return result[:20], len(result)


def _segments(row: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    plan_fields = {
        "loss": ("opening_relations_lost_any_time", "opening_relations"),
        "new_plan": ("new_relations", "opening_relations"),
        "plan_recovery": ("reactivations", "opening_relations"),
    }
    if kind in plan_fields:
        numerator_key, denominator_key = plan_fields[kind]
        for plan in row.get("plan_segments", []):
            numerator = _safe_int(plan.get(numerator_key))
            if numerator:
                denominator = _safe_int(plan.get(denominator_key))
                result.append({"dimension": "plan_tier", "segment": plan.get("plan_tier"), "numerator": numerator, "denominator": denominator, "rate_pct": round(numerator / denominator * 100, 4) if denominator else None})

    account_fields = {
        "loss": ("opening_relations_lost_any_time", "opening_plan_relations"),
        "new_customer": ("new_customers", "opening_customers"),
        "new_plan": ("new_plan_relationships", "opening_plan_relations"),
        "customer_recovery": ("customer_reactivations", "opening_customers"),
        "plan_recovery": ("plan_reactivations", "opening_plan_relations"),
        "contraction": ("portfolio_contractions", "opening_customers"),
    }
    if kind in account_fields:
        numerator_key, denominator_key = account_fields[kind]
        for dimension, segments in row.get("account_segments", {}).items():
            for segment in segments:
                numerator = _safe_int(segment.get(numerator_key))
                if numerator:
                    denominator = _safe_int(segment.get(denominator_key))
                    result.append({"dimension": dimension, "segment": segment.get("segment"), "numerator": numerator, "denominator": denominator, "rate_pct": round(numerator / denominator * 100, 4) if denominator else None})
    return sorted(result, key=lambda item: (-item["numerator"], item["dimension"], str(item["segment"])))[:12]


def _event_segments(month_events: list[dict[str, Any]], account_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    distinct = {str(row.get("account_id")) for row in month_events if row.get("account_id")}
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for account_id in distinct:
        profile = account_lookup.get(account_id, {})
        for dimension in ("industry", "country", "referral_source"):
            value = str(profile.get(dimension) or "Unknown")
            counts[dimension][value] += 1
    result = []
    for dimension, values in counts.items():
        for segment, count in values.most_common(4):
            result.append({"dimension": dimension, "segment": segment, "affected_accounts": count, "denominator": None, "interpretation": "Distinct accounts among recorded event accounts only; not a segment prevalence rate."})
    return sorted(result, key=lambda item: (-item["affected_accounts"], item["dimension"], item["segment"]))[:12]


def _month_event_rows(events: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        month = _month(event.get("churn_date"))
        if month and str(event.get("is_reactivation", "")).strip().lower() not in {"true", "1", "yes"}:
            result[month].append(event)
    return result


def build_key_moments(
    ledger: dict[str, Any],
    events: Iterable[dict[str, Any]] = (),
    accounts: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Return reproducible highlights. Peaks are descriptive maxima, never significance tests."""
    rows = sorted(ledger.get("periods", {}).get("MONTHLY", []), key=lambda item: item["period"])
    movements = ledger.get("movements", [])
    account_lookup = {str(row.get("account_id")): row for row in accounts if row.get("account_id")}
    event_rows = _month_event_rows(events)
    moments: list[dict[str, Any]] = []

    def add(
        kind: str,
        row: dict[str, Any],
        metric: str,
        value: int | float,
        numerator: int | None,
        denominator: int | None,
        criterion: str,
        explanation: str,
        action: str,
        *,
        comparison: dict[str, Any] | None = None,
        segment_kind: str | None = None,
        movement_types: set[str] | None = None,
        linked_events: list[dict[str, Any]] | None = None,
    ) -> None:
        month = row["period"]
        if linked_events is not None:
            related_accounts = sorted({str(item.get("account_id")) for item in linked_events if item.get("account_id")})
            account_details = [{"account_id": account_id, "movement_types": ["RECORDED_NONREACTIVATION_EVENT"], "plans": [], "dates": sorted({str(item.get("churn_date")) for item in linked_events if str(item.get("account_id")) == account_id})} for account_id in related_accounts]
            account_details = account_details[:20]
            related_segments = _event_segments(linked_events, account_lookup)
            account_count = len(related_accounts)
        else:
            account_details, account_count = _account_movements(movements, month, movement_types or set())
            related_segments = _segments(row, segment_kind or "")
            if not related_segments and movement_types:
                transition_counts: dict[tuple[str, str], set[str]] = defaultdict(set)
                for movement in movements:
                    if _month(movement.get("date")) != month or movement.get("type") not in movement_types:
                        continue
                    for field in ("plan_tier", "from_plan", "to_plan"):
                        if movement.get(field) and movement.get("account_id"):
                            transition_counts[(field, str(movement[field]))].add(str(movement["account_id"]))
                related_segments = [
                    {"dimension": field, "segment": plan, "numerator": len(ids), "denominator": None, "rate_pct": None, "interpretation": "Distinct accounts in candidate movement records; no population denominator or confirmed transition."}
                    for (field, plan), ids in sorted(transition_counts.items())
                ][:12]
        moments.append({
            "id": f"{kind.lower()}:{month}:{metric}",
            "type": kind,
            "month": month,
            "metric": metric,
            "value": round(float(value), 6) if isinstance(value, float) else int(value),
            "numerator": numerator,
            "denominator": denominator,
            "comparison": comparison or {"reference": "none", "note": "No comparable reference is available for this deterministic selector."},
            "criterion": criterion,
            "segments": related_segments,
            "accounts": account_details,
            "account_count": account_count,
            "accounts_truncated": account_count > len(account_details),
            "evidence_classification": EVIDENCE,
            "executive_explanation": explanation,
            "investigation_action": action,
        })

    # RATE_PEAK: valid opening denominators only. Exact ties are retained.
    valid_rate_rows = [row for row in rows if row.get("opening_plan_relations", 0) > 0 and row.get("opening_relations_lost_any_time") is not None]
    if valid_rate_rows:
        peak_rate = max(float(row["opening_cohort_churn_any_pct"]) for row in valid_rate_rows if row.get("opening_cohort_churn_any_pct") is not None)
        for row in valid_rate_rows:
            rate = row.get("opening_cohort_churn_any_pct")
            if rate is not None and abs(float(rate) - peak_rate) < 1e-10:
                i = rows.index(row)
                previous = rows[i - 1] if i > 0 else None
                add("RATE_PEAK", row, "opening_cohort_churn_any_pct", float(rate), _safe_int(row.get("opening_relations_lost_any_time")), _safe_int(row.get("opening_plan_relations")), "Maximum monthly opening-cohort plan-proxy loss rate among months with a positive opening denominator; ties are retained. Descriptive maximum, not statistical significance.", f"{row['opening_relations_lost_any_time']} of {row['opening_plan_relations']} opening account × plan-tier relations lost coverage at least once ({float(rate):.2f}%).", "Review the affected relation timelines and verify whether the corresponding contract actually ended.", comparison={"reference": "previous_month", "period": previous["period"] if previous else None, "value": previous.get("opening_cohort_churn_any_pct") if previous else None, "delta_percentage_points": round(float(rate) - float(previous["opening_cohort_churn_any_pct"]), 6) if previous and previous.get("opening_cohort_churn_any_pct") is not None else None, "series_maximum": round(peak_rate, 6)}, segment_kind="loss", movement_types={"PLAN_RELATION_LOSS", "CUSTOMER_CHURN"})

    # LOSS_VOLUME_PEAK: gross date-derived plan relation loss events (all relationship starts).
    peak_volume = max((_safe_int(row.get("gross_plan_relation_loss_events")) for row in rows), default=0)
    if peak_volume > 0:
        for row in rows:
            value = _safe_int(row.get("gross_plan_relation_loss_events"))
            if value == peak_volume:
                add("LOSS_VOLUME_PEAK", row, "gross_plan_relation_loss_events", value, value, None, "Maximum monthly count of distinct date-derived account × plan-tier coverage loss events; not limited to the opening cohort. Ties are retained.", f"{value} plan-proxy coverage loss events occurred in {row['period']}; this count can include relationships that began after month opening.", "Reconcile each event to the contract history and keep gross events separate from opening-cohort churn.", comparison={"reference": "monthly_maximum", "maximum": peak_volume, "opening_cohort_losses": _safe_int(row.get("opening_relations_lost_any_time")), "opening_denominator": _safe_int(row.get("opening_plan_relations"))}, segment_kind="loss", movement_types={"PLAN_RELATION_LOSS", "CUSTOMER_CHURN"})

    # ACQUISITION_CHANGE: largest absolute month-to-month changes in customer and plan additions.
    for metric, label, segment_kind, accepted in (
        ("new_customers", "new customer acquisitions", "new_customer", {"NEW_CUSTOMER"}),
        ("new_plan_relationships", "new account × plan-tier relationships", "new_plan", {"NEW_PLAN_RELATIONSHIP"}),
    ):
        changes = []
        for i in range(1, len(rows)):
            current, previous = rows[i], rows[i - 1]
            delta = _safe_int(current.get(metric)) - _safe_int(previous.get(metric))
            if delta:
                changes.append((abs(delta), current["period"], delta, current, previous))
        if changes:
            largest = max(item[0] for item in changes)
            for _, _, delta, current, previous in changes:
                if abs(delta) == largest:
                    add("ACQUISITION_CHANGE", current, metric, _safe_int(current.get(metric)), _safe_int(current.get(metric)), None, f"Largest absolute month-over-month change in {label} across the observed series; ties retained. This is a count change, not a statistically significant break.", f"{label.capitalize()} changed by {delta:+d} from {previous['period']} to {current['period']} ({_safe_int(previous.get(metric))} to {_safe_int(current.get(metric))}).", "Check campaign, onboarding and cohort composition records before interpreting this movement as acquisition-quality change.", comparison={"reference": "previous_month", "period": previous["period"], "value": _safe_int(previous.get(metric)), "delta": delta}, segment_kind=segment_kind, movement_types=accepted)

    # RECOVERY_MOMENT: maximum positive monthly counts for each unit, not a mixed total.
    for metric, label, movement_type, segment_kind in (
        ("customer_reactivations", "customer reactivations", "CUSTOMER_REACTIVATION", "customer_recovery"),
        ("plan_reactivations", "plan-proxy reactivations", "PLAN_RELATION_REACTIVATION", "plan_recovery"),
    ):
        peak = max((_safe_int(row.get(metric)) for row in rows), default=0)
        if peak:
            for row in rows:
                value = _safe_int(row.get(metric))
                if value == peak:
                    add("RECOVERY_MOMENT", row, metric, value, value, None, f"Maximum monthly count of {label} in this unit; ties retained. Not an event-count interpretation of account recovery.", f"{value} {label} were reconstructed in {row['period']}.", "Verify each return against a prior coverage gap and confirm the commercial lifecycle state.", comparison={"reference": "monthly_maximum", "maximum": peak}, segment_kind=segment_kind, movement_types={movement_type})

    # PORTFOLIO_CONTRACTION: portfolio count and possible transition candidates remain separate.
    for metric, label, movement_type in (
        ("portfolio_contraction_events", "portfolio contraction events", "PORTFOLIO_CONTRACTION"),
        ("possible_downgrade_candidates", "possible downgrade candidates", "POSSIBLE_DOWNGRADE"),
    ):
        peak = max((_safe_int(row.get(metric)) for row in rows), default=0)
        if peak:
            for row in rows:
                value = _safe_int(row.get(metric))
                if value == peak:
                    add("PORTFOLIO_CONTRACTION", row, metric, value, value, None, f"Maximum monthly {label} across the observed series; ties retained. A possible downgrade is not a confirmed migration or revenue contraction.", f"{value} {label} were recorded by the date-derived proxy in {row['period']}.", "Inspect source contract links, active parallel plans and documented plan hierarchy before classifying migration or financial contraction.", comparison={"reference": "monthly_maximum", "maximum": peak, "possible_downgrade_candidates": _safe_int(row.get("possible_downgrade_candidates")), "portfolio_contraction_events": _safe_int(row.get("portfolio_contraction_events"))}, segment_kind="contraction", movement_types={movement_type, "PLAN_RELATION_LOSS"})

    # RATE_VS_VOLUME_DIVERGENCE: count/rate move in opposite directions month over month.
    for i in range(1, len(rows)):
        current, previous = rows[i], rows[i - 1]
        old_rate, new_rate = previous.get("opening_cohort_churn_any_pct"), current.get("opening_cohort_churn_any_pct")
        old_volume, new_volume = _safe_int(previous.get("gross_plan_relation_loss_events")), _safe_int(current.get("gross_plan_relation_loss_events"))
        if old_rate is None or new_rate is None:
            continue
        delta_rate = float(new_rate) - float(old_rate)
        delta_volume = new_volume - old_volume
        if delta_rate * delta_volume < 0:
            add("RATE_VS_VOLUME_DIVERGENCE", current, "gross_loss_count_vs_opening_cohort_rate", float(new_rate), _safe_int(current.get("opening_relations_lost_any_time")), _safe_int(current.get("opening_plan_relations")), "Adjacent months have opposite directions in gross loss-event count and opening-cohort loss rate. Both denominators must be valid; descriptive divergence only.", f"Gross loss events changed {delta_volume:+d} ({old_volume} to {new_volume}) while the opening-cohort rate changed {delta_rate:+.2f} percentage points ({float(old_rate):.2f}% to {float(new_rate):.2f}%).", "Inspect base size and plan/customer composition; do not infer a retention improvement or deterioration from counts alone.", comparison={"reference": "previous_month", "period": previous["period"], "gross_loss_events_previous": old_volume, "gross_loss_events_current": new_volume, "gross_loss_delta": delta_volume, "rate_previous_pct": float(old_rate), "rate_current_pct": float(new_rate), "rate_delta_percentage_points": round(delta_rate, 6)}, segment_kind="loss", movement_types={"PLAN_RELATION_LOSS", "CUSTOMER_CHURN"})

    # DATA_QUALITY_EVENT: the largest count gap between non-reactivation event rows and date-based complete-account losses.
    data_quality_rows = []
    for row in rows:
        month_events = event_rows.get(row["period"], [])
        event_count = len(month_events)
        complete_loss = _safe_int(row.get("gross_customer_churn_events"))
        gap = event_count - complete_loss
        if gap > 0:
            data_quality_rows.append((gap, row["period"], event_count, complete_loss, row, month_events))
    if data_quality_rows:
        largest = max(item[0] for item in data_quality_rows)
        for gap, _, event_count, complete_loss, row, month_events in data_quality_rows:
            if gap == largest:
                add("DATA_QUALITY_EVENT", row, "nonreactivation_event_rows_minus_date_customer_losses", gap, event_count, None, "Largest positive monthly difference between recorded non-reactivation event rows and reconstructed complete-account coverage-loss events; no event-to-contract key is assumed.", f"{event_count} non-reactivation event rows contrast with {complete_loss} date-derived full-account loss events in {row['period']} (difference {gap}). These are different source units and do not reconcile as individual customer churn.", "Review event semantics and add a stable subscription/contract link plus effective lifecycle status.", comparison={"reference": "date_reconstruction", "recorded_nonreactivation_event_rows": event_count, "date_derived_complete_account_loss_events": complete_loss, "difference": gap}, linked_events=month_events)

    moments.sort(key=lambda item: (item["month"], item["type"], item["metric"], item["id"]))
    return {
        "classification": EVIDENCE,
        "months_analyzed": len(rows),
        "criteria_note": "Key moments are deterministic selectors over the observed monthly ledger. Peaks are descriptive, not significance tests; ties are retained; zero-denominator rates are excluded.",
        "moments": moments,
    }
