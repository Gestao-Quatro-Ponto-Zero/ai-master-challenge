from __future__ import annotations

from typing import Any

from services.dashboard_service import ACCOUNT_BASE_SQL, build_filter_clause, normalize_filters
from services.database_service import query_one, query_rows
from services.risk_service import get_risk_accounts


def list_accounts(raw_filters: dict[str, Any]) -> list[dict[str, Any]]:
    filters = normalize_filters(raw_filters)
    search = (raw_filters.get("search") or "").strip()
    clause, params = build_filter_clause(filters, alias="b")
    if search:
        clause += " AND (b.account_name LIKE :search OR b.account_id LIKE :search)"
        params["search"] = f"%{search}%"
    return query_rows(
        f"""
        WITH base AS ({ACCOUNT_BASE_SQL})
        SELECT
            b.account_id, b.account_name, b.industry, b.country, b.signup_date,
            b.referral_source, b.plan_tier, b.seats, b.is_trial,
            b.mrr_amount AS mrr, b.arr_amount AS arr,
            b.billing_frequency, b.auto_renew_flag,
            CASE WHEN b.churned_account = 1 THEN 'churn' ELSE 'ativa' END AS status,
            b.latest_reason_code
        FROM base b
        WHERE 1=1 {clause}
        ORDER BY b.account_name
        """,
        params,
    )


def get_account_detail(account_id: str) -> dict[str, Any] | None:
    if not account_id or len(account_id) > 64:
        return None

    account = query_one(
        f"""
        WITH base AS ({ACCOUNT_BASE_SQL})
        SELECT * FROM base WHERE account_id = :account_id
        """,
        {"account_id": account_id},
    )
    if not account:
        return None

    risk = next(
        (item for item in get_risk_accounts({}) if item["account_id"] == account_id),
        None,
    )
    subscriptions = query_rows(
        "SELECT * FROM subscriptions WHERE account_id = :account_id ORDER BY date(start_date) DESC",
        {"account_id": account_id},
    )
    tickets = query_rows(
        "SELECT * FROM support_tickets WHERE account_id = :account_id ORDER BY datetime(submitted_at) DESC",
        {"account_id": account_id},
    )
    churn_events = query_rows(
        "SELECT * FROM churn_events WHERE account_id = :account_id ORDER BY date(churn_date) DESC",
        {"account_id": account_id},
    )
    usage = query_rows(
        """
        SELECT fu.feature_name,
               COUNT(*) AS events,
               SUM(COALESCE(fu.usage_count, 0)) AS usage_count,
               SUM(COALESCE(fu.usage_duration_secs, 0)) AS duration_secs,
               SUM(COALESCE(fu.error_count, 0)) AS errors
        FROM feature_usage fu
        JOIN subscriptions s ON s.subscription_id = fu.subscription_id
        WHERE s.account_id = :account_id
        GROUP BY fu.feature_name
        ORDER BY usage_count DESC
        """,
        {"account_id": account_id},
    )
    timeline = _build_timeline(account, subscriptions, tickets, churn_events)
    return {
        "account": account,
        "risk": risk,
        "subscriptions": subscriptions,
        "tickets": tickets,
        "churn_events": churn_events,
        "usage": usage,
        "timeline": timeline,
    }


def _build_timeline(account, subscriptions, tickets, churn_events):
    events = [{"date": account.get("signup_date"), "type": "cadastro", "label": "Cadastro da conta"}]
    for sub in subscriptions:
        events.append({"date": sub.get("start_date"), "type": "assinatura", "label": f"Inicio {sub.get('plan_tier')}"})
        if sub.get("upgrade_flag"):
            events.append({"date": sub.get("start_date"), "type": "upgrade", "label": "Upgrade"})
        if sub.get("downgrade_flag"):
            events.append({"date": sub.get("start_date"), "type": "downgrade", "label": "Downgrade"})
        if sub.get("end_date"):
            events.append({"date": sub.get("end_date"), "type": "encerramento", "label": "Fim da assinatura"})
    for ticket in tickets:
        events.append({"date": ticket.get("submitted_at"), "type": "ticket", "label": f"Ticket {ticket.get('priority')}"})
    for churn in churn_events:
        label = "Reativacao" if churn.get("is_reactivation") else f"Churn: {churn.get('reason_code') or 'Unknown'}"
        events.append({"date": churn.get("churn_date"), "type": "reativacao" if churn.get("is_reactivation") else "churn", "label": label})
    return sorted([event for event in events if event["date"]], key=lambda item: item["date"])
