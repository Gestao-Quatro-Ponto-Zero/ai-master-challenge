from __future__ import annotations

from functools import lru_cache
from typing import Any

from services.database_service import query_one, query_rows


FILTER_FIELDS = {
    "plan_tier": "plan_tier",
    "industry": "industry",
    "country": "country",
    "referral_source": "referral_source",
    "is_trial": "is_trial",
    "status": "status",
    "billing_frequency": "billing_frequency",
    "auto_renew_flag": "auto_renew_flag",
    "reason_code": "latest_reason_code",
    "start_date": "start_date",
    "end_date": "end_date",
}


def normalize_filters(raw: dict[str, Any]) -> dict[str, Any]:
    allowed = set(FILTER_FIELDS)
    filters = {k: v for k, v in raw.items() if k in allowed and v not in ("", None)}
    invalid = sorted(set(raw) - allowed - {"page", "page_size", "search", "sort", "direction"})
    if invalid:
        raise ValueError("Filtros invalidos: " + ", ".join(invalid))

    for bool_field in ("is_trial", "auto_renew_flag"):
        if bool_field in filters:
            value = str(filters[bool_field]).lower()
            if value not in {"0", "1", "true", "false"}:
                raise ValueError(f"Filtro invalido para {bool_field}. Use 0 ou 1.")
            filters[bool_field] = 1 if value in {"1", "true"} else 0

    if "status" in filters and filters["status"] not in {"active", "churn"}:
        raise ValueError("Filtro status deve ser active ou churn.")

    return filters


def build_filter_clause(filters: dict[str, Any], alias: str = "b") -> tuple[str, dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, Any] = {}
    prefix = f"{alias}." if alias else ""

    for field, value in filters.items():
        if field == "start_date":
            clauses.append(f"date({prefix}signup_date) >= date(:start_date)")
            params["start_date"] = value
        elif field == "end_date":
            clauses.append(f"date({prefix}signup_date) <= date(:end_date)")
            params["end_date"] = value
        elif field == "status":
            clauses.append(f"{prefix}churned_account = :status_churn")
            params["status_churn"] = 1 if value == "churn" else 0
        elif field == "reason_code":
            clauses.append(f"{prefix}latest_reason_code = :reason_code")
            params["reason_code"] = value
        else:
            clauses.append(f"{prefix}{FILTER_FIELDS[field]} = :{field}")
            params[field] = value

    return (" AND " + " AND ".join(clauses)) if clauses else "", params


@lru_cache(maxsize=1)
def get_filter_options() -> dict[str, Any]:
    return {
        "plan_tier": _values("accounts", "plan_tier"),
        "industry": _values("accounts", "industry"),
        "country": _values("accounts", "country"),
        "referral_source": _values("accounts", "referral_source"),
        "billing_frequency": _values("subscriptions", "billing_frequency"),
        "reason_code": _values("churn_events", "reason_code"),
    }


def _values(table: str, column: str) -> list[str]:
    rows = query_rows(
        f"""
        SELECT DISTINCT {column} AS value
        FROM {table}
        WHERE {column} IS NOT NULL AND {column} <> ''
        ORDER BY {column}
        """
    )
    return [row["value"] for row in rows]


def get_kpis(raw_filters: dict[str, Any]) -> dict[str, Any]:
    filters = normalize_filters(raw_filters)
    clause, params = build_filter_clause(filters)
    row = query_one(
        f"""
        WITH base AS ({ACCOUNT_BASE_SQL}),
        ticket_account AS (
            SELECT account_id, COUNT(*) AS ticket_count
            FROM support_tickets
            GROUP BY account_id
        ),
        reactivated AS (
            SELECT account_id, COUNT(*) AS reactivation_count
            FROM churn_events
            WHERE is_reactivation = 1
            GROUP BY account_id
        ),
        filtered AS (
            SELECT b.*
            FROM base b
            WHERE 1=1 {clause}
        )
        SELECT
            COUNT(*) AS total_accounts,
            SUM(CASE WHEN churned_account = 0 THEN 1 ELSE 0 END) AS active_accounts,
            SUM(CASE WHEN churned_account = 1 THEN 1 ELSE 0 END) AS churned_accounts,
            ROUND(100.0 * SUM(CASE WHEN churned_account = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS churn_rate,
            ROUND(SUM(CASE WHEN churned_account = 0 THEN mrr_amount ELSE 0 END), 2) AS active_mrr,
            ROUND(SUM(CASE WHEN churned_account = 0 THEN arr_amount ELSE 0 END), 2) AS active_arr,
            ROUND(SUM(CASE WHEN churned_account = 1 THEN mrr_amount ELSE 0 END), 2) AS lost_mrr,
            ROUND(SUM(CASE WHEN churned_account = 1 THEN arr_amount ELSE 0 END), 2) AS lost_arr,
            ROUND(AVG(CASE WHEN mrr_amount > 0 THEN mrr_amount END), 2) AS average_monthly_ticket,
            COALESCE((SELECT SUM(ticket_count) FROM ticket_account t JOIN filtered f ON f.account_id = t.account_id), 0) AS total_tickets,
            COALESCE((SELECT COUNT(*) FROM reactivated r JOIN filtered f ON f.account_id = r.account_id), 0) AS reactivated_accounts
        FROM filtered
        """,
        params,
    )
    high_risk = query_one(
        f"""
        WITH base AS ({ACCOUNT_BASE_SQL})
        SELECT COUNT(*) AS high_risk_accounts
        FROM base b
        WHERE churned_account = 0 {clause}
        """,
        params,
    )
    data = row or {}
    data["high_risk_accounts"] = high_risk["high_risk_accounts"] if high_risk else 0
    return data


def get_revenue(raw_filters: dict[str, Any]) -> dict[str, Any]:
    filters = normalize_filters(raw_filters)
    clause, params = build_filter_clause(filters)
    return {
        "mrr_by_plan": _segment_sum("plan_tier", "mrr_amount", 0, clause, params),
        "arr_by_industry": _segment_sum("industry", "arr_amount", 0, clause, params),
        "lost_mrr_by_plan": _segment_sum("plan_tier", "mrr_amount", 1, clause, params),
        "mrr_bands": query_rows(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT
                CASE
                    WHEN mrr_amount < 500 THEN '< $500'
                    WHEN mrr_amount < 2000 THEN '$500-$1,999'
                    WHEN mrr_amount < 5000 THEN '$2,000-$4,999'
                    WHEN mrr_amount < 10000 THEN '$5,000-$9,999'
                    ELSE '$10,000+'
                END AS band,
                COUNT(*) AS accounts
            FROM base b
            WHERE 1=1 {clause}
            GROUP BY band
            ORDER BY MIN(mrr_amount)
            """,
            params,
        ),
    }


def _segment_sum(field: str, metric: str, churned: int, clause: str, params: dict[str, Any]):
    segment_params = dict(params, churned=churned)
    return query_rows(
        f"""
        WITH base AS ({ACCOUNT_BASE_SQL})
        SELECT COALESCE({field}, 'Unknown') AS segment, ROUND(SUM(COALESCE({metric}, 0)), 2) AS value
        FROM base b
        WHERE churned_account = :churned {clause}
        GROUP BY COALESCE({field}, 'Unknown')
        ORDER BY value DESC
        """,
        segment_params,
    )


def get_usage(raw_filters: dict[str, Any]) -> dict[str, Any]:
    filters = normalize_filters(raw_filters)
    clause, params = build_filter_clause(filters, alias="b")
    return {
        "features": query_rows(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT
                fu.feature_name,
                SUM(COALESCE(fu.usage_count, 0)) AS usage_count,
                ROUND(AVG(COALESCE(fu.usage_duration_secs, 0)), 2) AS avg_duration_secs,
                SUM(COALESCE(fu.error_count, 0)) AS errors
            FROM feature_usage fu
            JOIN subscriptions s ON s.subscription_id = fu.subscription_id
            JOIN base b ON b.account_id = s.account_id
            WHERE 1=1 {clause}
            GROUP BY fu.feature_name
            ORDER BY usage_count DESC
            LIMIT 12
            """,
            params,
        ),
        "active_vs_churn": query_rows(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT
                CASE WHEN b.churned_account = 1 THEN 'Churn' ELSE 'Ativas' END AS status,
                ROUND(AVG(COALESCE(fu.usage_count, 0)), 2) AS avg_usage_count,
                ROUND(AVG(COALESCE(fu.error_count, 0)), 2) AS avg_errors
            FROM base b
            LEFT JOIN subscriptions s ON s.account_id = b.account_id
            LEFT JOIN feature_usage fu ON fu.subscription_id = s.subscription_id
            WHERE 1=1 {clause}
            GROUP BY b.churned_account
            """,
            params,
        ),
        "timeline": query_rows(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT strftime('%Y-%m', fu.usage_date) AS month, SUM(COALESCE(fu.usage_count, 0)) AS usage_count
            FROM feature_usage fu
            JOIN subscriptions s ON s.subscription_id = fu.subscription_id
            JOIN base b ON b.account_id = s.account_id
            WHERE 1=1 {clause}
            GROUP BY month
            ORDER BY month
            """,
            params,
        ),
        "beta": query_rows(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT CASE WHEN fu.is_beta_feature = 1 THEN 'Beta' ELSE 'Geral' END AS feature_type,
                   SUM(COALESCE(fu.usage_count, 0)) AS usage_count,
                   SUM(COALESCE(fu.error_count, 0)) AS errors
            FROM feature_usage fu
            JOIN subscriptions s ON s.subscription_id = fu.subscription_id
            JOIN base b ON b.account_id = s.account_id
            WHERE 1=1 {clause}
            GROUP BY fu.is_beta_feature
            """,
            params,
        ),
    }


def get_support(raw_filters: dict[str, Any]) -> dict[str, Any]:
    filters = normalize_filters(raw_filters)
    clause, params = build_filter_clause(filters, alias="b")
    return {
        "priority": query_rows(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT COALESCE(st.priority, 'Unknown') AS priority, COUNT(*) AS tickets
            FROM support_tickets st
            JOIN base b ON b.account_id = st.account_id
            WHERE 1=1 {clause}
            GROUP BY COALESCE(st.priority, 'Unknown')
            ORDER BY tickets DESC
            """,
            params,
        ),
        "summary": query_one(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT
                ROUND(AVG(st.first_response_time_minutes), 2) AS avg_first_response_minutes,
                ROUND(AVG(st.resolution_time_hours), 2) AS avg_resolution_hours,
                ROUND(AVG(st.satisfaction_score), 2) AS avg_satisfaction,
                ROUND(100.0 * SUM(COALESCE(st.escalation_flag, 0)) / NULLIF(COUNT(*), 0), 2) AS escalation_rate
            FROM support_tickets st
            JOIN base b ON b.account_id = st.account_id
            WHERE 1=1 {clause}
            """,
            params,
        ),
        "active_vs_churn": query_rows(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT CASE WHEN b.churned_account = 1 THEN 'Churn' ELSE 'Ativas' END AS status,
                   COUNT(st.ticket_id) AS tickets,
                   ROUND(AVG(st.satisfaction_score), 2) AS avg_satisfaction
            FROM base b
            LEFT JOIN support_tickets st ON st.account_id = b.account_id
            WHERE 1=1 {clause}
            GROUP BY b.churned_account
            """,
            params,
        ),
    }


def get_reactivation(raw_filters: dict[str, Any]) -> dict[str, Any]:
    filters = normalize_filters(raw_filters)
    clause, params = build_filter_clause(filters, alias="b")
    return {
        "total": query_one(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT COUNT(*) AS reactivation_events
            FROM churn_events ce
            JOIN base b ON b.account_id = ce.account_id
            WHERE ce.is_reactivation = 1 {clause}
            """,
            params,
        ),
        "timeline": query_rows(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT strftime('%Y-%m', ce.churn_date) AS month, COUNT(*) AS reactivations
            FROM churn_events ce
            JOIN base b ON b.account_id = ce.account_id
            WHERE ce.is_reactivation = 1 {clause}
            GROUP BY month
            ORDER BY month
            """,
            params,
        ),
        "by_plan": query_rows(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT b.plan_tier AS segment, COUNT(*) AS reactivations
            FROM churn_events ce
            JOIN base b ON b.account_id = ce.account_id
            WHERE ce.is_reactivation = 1 {clause}
            GROUP BY b.plan_tier
            ORDER BY reactivations DESC
            """,
            params,
        ),
    }


ACCOUNT_BASE_SQL = """
WITH ranked_subscriptions AS (
    SELECT
        s.*,
        ROW_NUMBER() OVER (
            PARTITION BY s.account_id
            ORDER BY
                CASE WHEN s.end_date IS NULL OR s.end_date = '' THEN 0 ELSE 1 END,
                date(s.start_date) DESC,
                s.subscription_id DESC
        ) AS rn
    FROM subscriptions s
),
latest_churn_event AS (
    SELECT
        ce.*,
        ROW_NUMBER() OVER (
            PARTITION BY ce.account_id
            ORDER BY date(ce.churn_date) DESC, ce.churn_event_id DESC
        ) AS rn
    FROM churn_events ce
)
SELECT
    a.account_id,
    a.account_name,
    a.industry,
    a.country,
    a.signup_date,
    a.referral_source,
    COALESCE(rs.plan_tier, a.plan_tier) AS plan_tier,
    COALESCE(rs.seats, a.seats, 0) AS seats,
    COALESCE(rs.is_trial, a.is_trial, 0) AS is_trial,
    COALESCE(rs.mrr_amount, 0) AS mrr_amount,
    COALESCE(rs.arr_amount, 0) AS arr_amount,
    COALESCE(rs.billing_frequency, '') AS billing_frequency,
    COALESCE(rs.auto_renew_flag, 0) AS auto_renew_flag,
    COALESCE(rs.upgrade_flag, 0) AS upgrade_flag,
    COALESCE(rs.downgrade_flag, 0) AS downgrade_flag,
    rs.subscription_id AS current_subscription_id,
    CASE
        WHEN lce.is_reactivation = 1 THEN 0
        WHEN lce.churn_event_id IS NOT NULL THEN 1
        WHEN COALESCE(a.churn_flag, 0) = 1 THEN 1
        ELSE 0
    END AS churned_account,
    COALESCE(lce.reason_code, '') AS latest_reason_code,
    lce.churn_date AS latest_churn_date
FROM accounts a
LEFT JOIN ranked_subscriptions rs
    ON rs.account_id = a.account_id AND rs.rn = 1
LEFT JOIN latest_churn_event lce
    ON lce.account_id = a.account_id AND lce.rn = 1
"""
