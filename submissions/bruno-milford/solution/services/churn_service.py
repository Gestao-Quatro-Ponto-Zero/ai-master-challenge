from __future__ import annotations

from typing import Any

from services.database_service import query_rows
from services.dashboard_service import build_filter_clause, normalize_filters


def get_churn_timeline(raw_filters: dict[str, Any]) -> dict[str, Any]:
    filters = normalize_filters(raw_filters)
    clause, params = build_filter_clause(filters, alias="b")
    rows = query_rows(
        f"""
        WITH base AS ({ACCOUNT_BASE_SQL})
        SELECT
            strftime('%Y-%m', ce.churn_date) AS month,
            COUNT(*) AS churn_events,
            ROUND(SUM(COALESCE(b.mrr_amount, 0)), 2) AS lost_mrr
        FROM churn_events ce
        JOIN base b ON b.account_id = ce.account_id
        WHERE ce.is_reactivation = 0 {clause}
        GROUP BY month
        ORDER BY month
        """,
        params,
    )
    return {"timeline": rows}


def get_churn_reasons(raw_filters: dict[str, Any]) -> dict[str, Any]:
    filters = normalize_filters(raw_filters)
    clause, params = build_filter_clause(filters, alias="b")
    return {
        "reasons": query_rows(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT
                COALESCE(ce.reason_code, 'Unknown') AS reason_code,
                COUNT(*) AS churn_events,
                ROUND(SUM(COALESCE(ce.refund_amount_usd, 0)), 2) AS refund_amount_usd,
                ROUND(SUM(COALESCE(b.mrr_amount, 0)), 2) AS lost_mrr
            FROM churn_events ce
            JOIN base b ON b.account_id = ce.account_id
            WHERE ce.is_reactivation = 0 {clause}
            GROUP BY COALESCE(ce.reason_code, 'Unknown')
            ORDER BY churn_events DESC
            """,
            params,
        )
    }


def get_churn_segments(raw_filters: dict[str, Any]) -> dict[str, Any]:
    filters = normalize_filters(raw_filters)
    clause, params = build_filter_clause(filters, alias="b")
    result = {}
    for field in ("plan_tier", "industry", "country"):
        result[field] = query_rows(
            f"""
            WITH base AS ({ACCOUNT_BASE_SQL})
            SELECT
                COALESCE({field}, 'Unknown') AS segment,
                COUNT(*) AS total_accounts,
                SUM(churned_account) AS churned_accounts,
                ROUND(100.0 * SUM(churned_account) / NULLIF(COUNT(*), 0), 2) AS churn_rate
            FROM base b
            WHERE 1=1 {clause}
            GROUP BY COALESCE({field}, 'Unknown')
            ORDER BY churn_rate DESC, churned_accounts DESC
            """,
            params,
        )
    return result


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
