from __future__ import annotations

from datetime import date, datetime
from typing import Any

from services.dashboard_service import ACCOUNT_BASE_SQL, build_filter_clause, normalize_filters
from services.database_service import query_rows


RISK_WEIGHTS = {
    "no_recent_usage": 18,
    "low_usage_volume": 12,
    "usage_drop": 12,
    "high_error_rate": 14,
    "many_errors": 8,
    "many_tickets": 10,
    "urgent_tickets": 8,
    "slow_response": 6,
    "slow_resolution": 5,
    "escalation": 7,
    "low_satisfaction": 10,
    "downgrade": 8,
    "auto_renew_off": 7,
    "trial": 5,
    "monthly_billing": 4,
}


def risk_label(score: float) -> str:
    if score >= 80:
        return "critico"
    if score >= 60:
        return "alto"
    if score >= 30:
        return "medio"
    return "baixo"


def get_risk_accounts(raw_filters: dict[str, Any]) -> list[dict[str, Any]]:
    filters = normalize_filters(raw_filters)
    clause, params = build_filter_clause(filters, alias="b")
    rows = query_rows(
        f"""
        WITH base AS ({ACCOUNT_BASE_SQL}),
        usage_account AS (
            SELECT
                s.account_id,
                COUNT(fu.usage_id) AS usage_events,
                SUM(COALESCE(fu.usage_count, 0)) AS usage_volume,
                SUM(COALESCE(fu.usage_duration_secs, 0)) AS usage_duration_secs,
                SUM(COALESCE(fu.error_count, 0)) AS errors,
                MAX(fu.usage_date) AS last_usage_date,
                SUM(CASE WHEN date(fu.usage_date) >= date((SELECT MAX(usage_date) FROM feature_usage), '-30 day') THEN COALESCE(fu.usage_count, 0) ELSE 0 END) AS usage_recent,
                SUM(CASE WHEN date(fu.usage_date) < date((SELECT MAX(usage_date) FROM feature_usage), '-30 day')
                          AND date(fu.usage_date) >= date((SELECT MAX(usage_date) FROM feature_usage), '-60 day')
                         THEN COALESCE(fu.usage_count, 0) ELSE 0 END) AS usage_previous
            FROM subscriptions s
            LEFT JOIN feature_usage fu ON fu.subscription_id = s.subscription_id
            GROUP BY s.account_id
        ),
        ticket_account AS (
            SELECT
                account_id,
                COUNT(*) AS ticket_count,
                SUM(CASE WHEN lower(COALESCE(priority, '')) IN ('urgent', 'high', 'critical') THEN 1 ELSE 0 END) AS urgent_tickets,
                AVG(first_response_time_minutes) AS avg_first_response_minutes,
                AVG(resolution_time_hours) AS avg_resolution_hours,
                AVG(satisfaction_score) AS avg_satisfaction,
                SUM(COALESCE(escalation_flag, 0)) AS escalations
            FROM support_tickets
            GROUP BY account_id
        )
        SELECT
            b.account_id,
            b.account_name,
            b.industry,
            b.country,
            b.plan_tier,
            b.mrr_amount AS mrr,
            b.arr_amount AS arr,
            b.billing_frequency,
            b.auto_renew_flag,
            b.downgrade_flag,
            b.is_trial,
            b.churned_account,
            COALESCE(ua.usage_events, 0) AS usage_events,
            COALESCE(ua.usage_volume, 0) AS usage_volume,
            COALESCE(ua.usage_duration_secs, 0) AS usage_duration_secs,
            COALESCE(ua.errors, 0) AS errors,
            ua.last_usage_date,
            COALESCE(ua.usage_recent, 0) AS usage_recent,
            COALESCE(ua.usage_previous, 0) AS usage_previous,
            COALESCE(ta.ticket_count, 0) AS ticket_count,
            COALESCE(ta.urgent_tickets, 0) AS urgent_tickets,
            ROUND(COALESCE(ta.avg_first_response_minutes, 0), 2) AS avg_first_response_minutes,
            ROUND(COALESCE(ta.avg_resolution_hours, 0), 2) AS avg_resolution_hours,
            ROUND(COALESCE(ta.avg_satisfaction, 0), 2) AS avg_satisfaction,
            COALESCE(ta.escalations, 0) AS escalations
        FROM base b
        LEFT JOIN usage_account ua ON ua.account_id = b.account_id
        LEFT JOIN ticket_account ta ON ta.account_id = b.account_id
        WHERE 1=1 {clause}
        """,
        params,
    )
    scored = [_score_account(row) for row in rows]
    return sorted(scored, key=lambda item: item["priority_score"], reverse=True)


def _score_account(row: dict[str, Any]) -> dict[str, Any]:
    today = _latest_known_date()
    signals: list[str] = []
    risk = 0
    usage_volume = float(row.get("usage_volume") or 0)
    errors = float(row.get("errors") or 0)
    error_rate = errors / usage_volume if usage_volume else (1 if errors else 0)
    usage_recent = float(row.get("usage_recent") or 0)
    usage_previous = float(row.get("usage_previous") or 0)

    days_since_last_usage = None
    if row.get("last_usage_date"):
        parsed = _parse_date(row["last_usage_date"])
        if parsed:
            days_since_last_usage = max((today - parsed).days, 0)

    if days_since_last_usage is None or days_since_last_usage > 45:
        risk += RISK_WEIGHTS["no_recent_usage"]
        signals.append("sem uso recente")
    if usage_volume < 50:
        risk += RISK_WEIGHTS["low_usage_volume"]
        signals.append("baixo volume de uso")
    if usage_previous > 0 and usage_recent < usage_previous * 0.65:
        risk += RISK_WEIGHTS["usage_drop"]
        signals.append("queda de uso recente")
    if error_rate > 0.18:
        risk += RISK_WEIGHTS["high_error_rate"]
        signals.append("taxa de erro elevada")
    if errors >= 20:
        risk += RISK_WEIGHTS["many_errors"]
        signals.append("muitos erros")
    if row["ticket_count"] >= 5:
        risk += RISK_WEIGHTS["many_tickets"]
        signals.append("muitos tickets")
    if row["urgent_tickets"] > 0:
        risk += RISK_WEIGHTS["urgent_tickets"]
        signals.append("tickets urgentes")
    if row["avg_first_response_minutes"] > 180:
        risk += RISK_WEIGHTS["slow_response"]
        signals.append("primeira resposta lenta")
    if row["avg_resolution_hours"] > 72:
        risk += RISK_WEIGHTS["slow_resolution"]
        signals.append("resolucao lenta")
    if row["escalations"] > 0:
        risk += RISK_WEIGHTS["escalation"]
        signals.append("ticket escalado")
    if 0 < row["avg_satisfaction"] < 3.5:
        risk += RISK_WEIGHTS["low_satisfaction"]
        signals.append("baixa satisfacao")
    if row["downgrade_flag"]:
        risk += RISK_WEIGHTS["downgrade"]
        signals.append("downgrade recente")
    if not row["auto_renew_flag"]:
        risk += RISK_WEIGHTS["auto_renew_off"]
        signals.append("renovacao automatica desligada")
    if row["is_trial"]:
        risk += RISK_WEIGHTS["trial"]
        signals.append("trial")
    if str(row["billing_frequency"]).lower() == "monthly":
        risk += RISK_WEIGHTS["monthly_billing"]
        signals.append("cobranca mensal")

    risk_score = min(round(risk, 2), 100)
    mrr = float(row.get("mrr") or 0)
    value_score = min(round((mrr / 12000) * 100, 2), 100)
    priority_score = round((risk_score * 0.7) + (value_score * 0.3), 2)

    row.update(
        {
            "days_since_last_usage": days_since_last_usage,
            "risk_score": risk_score,
            "value_score": value_score,
            "priority_score": priority_score,
            "risk_classification": risk_label(risk_score),
            "risk_signals": "; ".join(signals) if signals else "sem sinais relevantes",
            "status": "churn" if row["churned_account"] else "ativa",
        }
    )
    return row


def _latest_known_date() -> date:
    rows = query_rows("SELECT MAX(usage_date) AS max_date FROM feature_usage")
    parsed = _parse_date(rows[0]["max_date"]) if rows and rows[0]["max_date"] else None
    return parsed or date.today()


def _parse_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value[:10]).date()
    except (TypeError, ValueError):
        return None
