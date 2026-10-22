from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from schemas.contracts import Finding

DATASETS = {
    "accounts": "ravenstack_accounts.csv",
    "subscriptions": "ravenstack_subscriptions.csv",
    "usage": "ravenstack_feature_usage.csv",
    "tickets": "ravenstack_support_tickets.csv",
    "churn_events": "ravenstack_churn_events.csv",
}


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.lower().eq("true")


def rounded(value: Any, digits: int = 4) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), digits)


def build_analysis(data_dir: Path | str) -> dict[str, Any]:
    """Load all source tables once; aggregate event, account and usage facts separately."""
    root = Path(data_dir)
    missing = [filename for filename in DATASETS.values() if not (root / filename).is_file()]
    if missing:
        raise FileNotFoundError(f"Required source CSVs missing from {root}: {', '.join(missing)}")
    tables = {name: pd.read_csv(root / filename) for name, filename in DATASETS.items()}
    accounts, subs, usage, tickets, events = (
        tables[name] for name in ("accounts", "subscriptions", "usage", "tickets", "churn_events")
    )
    date_columns = {
        "accounts": ["signup_date"],
        "subscriptions": ["start_date", "end_date"],
        "usage": ["usage_date"],
        "tickets": ["submitted_at", "closed_at"],
        "churn_events": ["churn_date"],
    }
    for name, columns in date_columns.items():
        for column in columns:
            tables[name][column] = pd.to_datetime(tables[name][column], errors="coerce")
    accounts["_flag"] = as_bool(accounts["churn_flag"])
    subs["_active_record"] = subs["end_date"].isna()
    events["_reactivation"] = as_bool(events["is_reactivation"])

    event_counts = events.groupby("account_id").size().rename("churn_event_count")
    account_view = accounts.merge(event_counts, on="account_id", how="left", validate="one_to_one")
    account_view["churn_event_count"] = account_view["churn_event_count"].fillna(0).astype(int)
    account_view["event_account"] = account_view["churn_event_count"].gt(0)
    account_view["status_comparison"] = "neither"
    account_view.loc[account_view["_flag"] & account_view["event_account"], "status_comparison"] = "flag_and_event"
    account_view.loc[account_view["_flag"] & ~account_view["event_account"], "status_comparison"] = "flag_without_event"
    account_view.loc[~account_view["_flag"] & account_view["event_account"], "status_comparison"] = "event_without_flag"

    active_subs = subs.loc[subs["_active_record"]]
    active_rollup = active_subs.groupby("account_id").agg(
        active_subscription_rows=("subscription_id", "size"), active_record_mrr_sum=("mrr_amount", "sum")
    )
    account_view = account_view.merge(active_rollup, on="account_id", how="left", validate="one_to_one")
    account_view["active_subscription_rows"] = account_view["active_subscription_rows"].fillna(0).astype(int)
    account_view["active_record_mrr_sum"] = account_view["active_record_mrr_sum"].fillna(0.0)

    usage_join = usage.merge(
        subs[["subscription_id", "account_id", "start_date", "end_date"]],
        on="subscription_id", how="left", validate="many_to_one"
    )
    usage_join["_before_start"] = usage_join["usage_date"].lt(usage_join["start_date"])
    usage_join["_after_end"] = usage_join["end_date"].notna() & usage_join["usage_date"].gt(usage_join["end_date"])
    event_accounts = set(events["account_id"].dropna())
    ticket_is_event_account = tickets["account_id"].isin(event_accounts)
    event_scores = tickets.loc[ticket_is_event_account, "satisfaction_score"].dropna()
    no_event_scores = tickets.loc[~ticket_is_event_account, "satisfaction_score"].dropna()
    satisfaction = tickets["satisfaction_score"].dropna()

    support_comparison = []
    for label, mask in (
        ("accounts_with_any_event", ticket_is_event_account),
        ("accounts_without_event", ~ticket_is_event_account),
    ):
        group = tickets.loc[mask]
        first_response = pd.to_numeric(group["first_response_time_minutes"], errors="coerce").dropna()
        resolution = pd.to_numeric(group["resolution_time_hours"], errors="coerce").dropna()
        group_scores = pd.to_numeric(group["satisfaction_score"], errors="coerce").dropna()
        escalation_present = group["escalation_flag"].notna()
        escalation_values = as_bool(group.loc[escalation_present, "escalation_flag"])
        support_comparison.append({
            "group": label,
            "accounts": int(group["account_id"].nunique()),
            "ticket_rows": len(group),
            "first_response_n": len(first_response),
            "first_response_median_minutes": rounded(first_response.median()),
            "resolution_n": len(resolution),
            "resolution_median_hours": rounded(resolution.median()),
            "satisfaction_n": len(group_scores),
            "satisfaction_mean": rounded(group_scores.mean()),
            "satisfaction_missing": int(group["satisfaction_score"].isna().sum()),
            "escalation_n": len(escalation_values),
            "escalated_tickets": int(escalation_values.sum()),
            "escalation_rate": rounded(escalation_values.mean()),
        })


    def segment_points(field: str) -> list[dict[str, Any]]:
        points = []
        for name, group in account_view.groupby(field, dropna=False):
            n = len(group)
            flag_count = int(group["_flag"].sum())
            event_count = int(group["event_account"].sum())
            points.append({
                "name": "Unknown" if pd.isna(name) else str(name), "accounts": n,
                "churn_flag_true": flag_count, "churn_flag_rate": round(flag_count / n, 6),
                "event_accounts": event_count, "event_account_rate": round(event_count / n, 6),
            })
        return sorted(points, key=lambda row: row["name"])

    months = sorted(
        set(events["churn_date"].dropna().dt.to_period("M").astype(str))
        | set(usage_join["usage_date"].dropna().dt.to_period("M").astype(str))
        | set(tickets["submitted_at"].dropna().dt.to_period("M").astype(str))
    )
    monthly = []
    for month in months:
        event_month = events.loc[events["churn_date"].dt.to_period("M").astype("string").eq(month)]
        usage_month = usage_join.loc[usage_join["usage_date"].dt.to_period("M").astype("string").eq(month)]
        ticket_month = tickets.loc[tickets["submitted_at"].dt.to_period("M").astype("string").eq(month)]
        scores = ticket_month["satisfaction_score"].dropna()
        monthly.append({
            "month": month, "churn_event_rows": len(event_month),
            "unique_event_accounts": int(event_month["account_id"].nunique()),
            "nonreactivation_event_rows": int((~event_month["_reactivation"]).sum()),
            "reactivation_event_rows": int(event_month["_reactivation"].sum()),
            "usage_rows": len(usage_month), "usage_accounts": int(usage_month["account_id"].nunique()),
            "usage_count": int(usage_month["usage_count"].sum()),
            "ticket_count": len(ticket_month), "satisfaction_n": len(scores),
            "satisfaction_mean": rounded(scores.mean()) if len(scores) else None,
        })

    yearly = events.assign(year=events["churn_date"].dt.year).groupby("year")
    yearly_rows = yearly.size().to_dict()
    yearly_accounts = yearly["account_id"].nunique().to_dict()
    reason_frame = events.groupby("reason_code", dropna=False).agg(
        event_rows=("churn_event_id", "size"), unique_accounts=("account_id", "nunique"),
        recorded_refunds_usd=("refund_amount_usd", "sum")
    ).reset_index()
    reasons = [{
        "reason": "Unknown" if pd.isna(row.reason_code) else str(row.reason_code),
        "event_rows": int(row.event_rows), "unique_accounts": int(row.unique_accounts),
        "recorded_refunds_usd": rounded(row.recorded_refunds_usd, 2),
        "interpretation": "Descriptive code only; not a verified causal explanation.",
    } for row in reason_frame.itertuples(index=False)]

    start_by_account = subs.groupby("account_id")["start_date"].min()
    end_by_account = subs.loc[subs["end_date"].notna()].groupby("account_id")["end_date"].max()
    spans = events.merge(start_by_account.rename("min_start"), on="account_id", how="left")
    spans = spans.merge(end_by_account.rename("max_end"), on="account_id", how="left")
    spans = spans.loc[spans["max_end"].notna()]
    outside_span = int((spans["churn_date"].lt(spans["min_start"]) | spans["churn_date"].gt(spans["max_end"])).sum())
    exact_end_matches = events.merge(
        subs.loc[subs["end_date"].notna(), ["account_id", "end_date"]],
        left_on=["account_id", "churn_date"], right_on=["account_id", "end_date"], how="inner"
    )["churn_event_id"].nunique()
    crosstab = {
        "flag_true_event_yes": int((account_view["_flag"] & account_view["event_account"]).sum()),
        "flag_true_event_no": int((account_view["_flag"] & ~account_view["event_account"]).sum()),
        "flag_false_event_yes": int((~account_view["_flag"] & account_view["event_account"]).sum()),
        "flag_false_event_no": int((~account_view["_flag"] & ~account_view["event_account"]).sum()),
    }
    event_2023, event_2024 = int(yearly_rows.get(2023, 0)), int(yearly_rows.get(2024, 0))
    findings = [
        Finding(id="label_conflict", title="Churn labels do not reconcile",
            statement="Event history and account status produce materially different customer counts.",
            evidence=[f"{len(events)} event rows across {events['account_id'].nunique()} accounts",
                f"{int(accounts['_flag'].sum())} account churn flags",
                f"{crosstab['flag_false_event_yes']} event accounts have churn_flag=False"],
            interpretation="Do not use either label as validated logo churn until the lifecycle contract is clarified.", confidence="HIGH"),
        Finding(id="raw_event_growth", title="Recorded event volume rises sharply",
            statement=f"The CSV has {event_2023} event rows in 2023 and {event_2024} in 2024.",
            evidence=["Counts are event rows, not eligible-account churn rates",
                f"Unique accounts by year: {yearly_accounts.get(2023, 0)} and {yearly_accounts.get(2024, 0)}"],
            interpretation="This supports growth in recorded events only; denominator, censoring and reactivation handling are unresolved.", confidence="HIGH"),
        Finding(id="usage_not_matching", title="Raw usage totals do not rise at the same pace",
            statement="Monthly usage rows and usage_count remain in a similar range across the observed window.",
            evidence=[f"{int(usage['usage_count'].sum())} total usage count across {len(usage)} rows",
                f"{int(usage_join['_before_start'].sum())} usage rows precede subscription start"],
            interpretation="Invalidly timed records prevent a reliable per-active-account engagement trend.", confidence="HIGH"),
        Finding(id="satisfaction_missing", title="Ticket satisfaction is similar in an all-time split",
            statement="Mean recorded scores are nearly the same for accounts with and without any churn event.",
            evidence=[f"Any-event accounts: n={len(event_scores)}, mean={rounded(event_scores.mean())}",
                f"No-event accounts: n={len(no_event_scores)}, mean={rounded(no_event_scores.mean())}",
                f"Missing ticket scores: {int(tickets['satisfaction_score'].isna().sum())}/{len(tickets)}"],
            interpretation="This is not a pre-churn comparison and does not establish a trend or causal protection.", confidence="MEDIUM"),
    ]
    usage_id_counts = usage["usage_id"].dropna().value_counts()
    duplicate_usage_ids = usage_id_counts.loc[usage_id_counts > 1]

    return {
        "dataset": {"source": "Kaggle: rivalytics/saas-subscription-and-churn-analytics-dataset",
            "synthetic": True, "window": "2023-01 to 2024-12",
            "license_note": "Challenge README states MIT; dataset README says MIT-like and requests credit to River @ Rivalytics."},
        "record_counts": {name: len(frame) for name, frame in tables.items()},
        "metrics": {
            "logo_churn_rate": {"value": None, "status": "UNKNOWN",
                "definition": "Distinct paying accounts lost during period / eligible paying accounts at period start.",
                "denominator": "Not reconstructable: event/account flags conflict and eligibility history is absent."},
            "subscription_end_row_share": {"value": rounded((~subs["_active_record"]).mean(), 6),
                "status": "DESCRIPTIVE_ONLY", "definition": "Rows with non-null end_date / all subscription rows; not a period churn rate.",
                "denominator": f"{int((~subs['_active_record']).sum())}/{len(subs)} subscription rows."},
            "gross_revenue_churn": {"value": None, "status": "UNKNOWN",
                "definition": "Starting recurring revenue lost to cancellations and contraction / starting recurring revenue.",
                "denominator": "No reliable account-period MRR bridge or clean event-to-subscription mapping."},
            "gross_revenue_retention": {"value": None, "status": "UNKNOWN",
                "definition": "Starting recurring revenue retained excluding expansion / starting recurring revenue.",
                "denominator": "No defensible opening and closing recurring revenue snapshots."},
            "net_revenue_retention": {"value": None, "status": "UNKNOWN",
                "definition": "Starting recurring revenue retained including expansion / starting recurring revenue.",
                "denominator": "No defensible opening and closing recurring revenue snapshots."},
            "recorded_refunds_usd": {"value": rounded(events["refund_amount_usd"].sum(), 2),
                "status": "OBSERVED_FIELD_SUM", "definition": "Sum of refund_amount_usd over churn event rows.",
                "denominator": f"{int(events['refund_amount_usd'].notna().sum())}/{len(events)} rows; not recurring revenue lost."},
            "recorded_ticket_satisfaction_mean": {"value": rounded(satisfaction.mean()),
                "status": "OBSERVED_NONMISSING_TICKETS", "definition": "Mean non-null satisfaction_score over all ticket rows.",
                "denominator": f"{len(satisfaction)}/{len(tickets)} ticket rows."},
        },
        "data_quality": {
            "account_churn_flags_true": int(accounts["_flag"].sum()), "event_accounts": int(events["account_id"].nunique()),
            "event_reactivation_rows": int(events["_reactivation"].sum()), "account_flag_event_crosstab": crosstab,
            "subscription_active_rows_null_end_date": int(subs["end_date"].isna().sum()),
            "accounts_with_any_active_subscription_row": int(active_rollup.index.nunique()),
            "active_record_mrr_sum_currency_unconfirmed": rounded(active_subs["mrr_amount"].sum(), 2),
            "active_record_mrr_note": "Record sum only; not a revenue exposure measure or verified current MRR.",
            "usage_duplicate_ids": int(len(duplicate_usage_ids)),
            "usage_rows_in_duplicate_id_groups": int(duplicate_usage_ids.sum()),
            "usage_duplicate_excess_rows": int(duplicate_usage_ids.sum() - len(duplicate_usage_ids)),
            "usage_rows_before_subscription_start": int(usage_join["_before_start"].sum()),
            "usage_rows_after_subscription_end": int(usage_join["_after_end"].sum()),
            "events_exactly_matching_subscription_end_date": int(exact_end_matches),
            "events_outside_account_subscription_span_where_end_exists": outside_span,
            "ticket_satisfaction_missing": int(tickets["satisfaction_score"].isna().sum()),
        },
        "monthly": monthly, "reasons": reasons, "support_comparison": support_comparison,
        "segments": {field: segment_points(field) for field in ["industry", "country", "referral_source", "plan_tier"]},
        "findings": [item.model_dump() for item in findings],
        "methodology": [
            "Event rows, unique event accounts, account churn flags, and ended subscription rows are reported separately.",
            "Usage and ticket tables are aggregated at their entity level; one-to-many joins are validated.",
            "Monthly event counts are not called churn rates without eligible-account denominators and clean lifecycle history.",
            "Refund sums are not treated as recurring revenue loss.",
            "No predictive model or causal intervention estimate is emitted.",
        ],
        "_internal": {"account_view": account_view, "events": events, "subs": subs},
    }
