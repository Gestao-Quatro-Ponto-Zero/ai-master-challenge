"""
Gold layer aggregation: reads silver Parquets, builds 5 analytical tables
with risk scores, churn drivers, feature retention, and support health.
"""
import logging
from pathlib import Path

import duckdb

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SILVER_DIR = Path("data/silver")
GOLD_DIR = Path("data/gold")


BRONZE_DIR = Path("data/bronze")


def _bronze(name: str) -> str:
    return str(BRONZE_DIR / f"{name}.parquet")


def _silver(name: str) -> str:
    return str(SILVER_DIR / f"{name}.parquet")


def _out(name: str) -> Path:
    return GOLD_DIR / f"{name}.parquet"


def build_dashboard_fact(con: duckdb.DuckDBPyConnection) -> int:
    """
    One row per (account × year_month).
    Joins subscriptions + accounts + plans + usage + support + churn.
    Computes risk_score inline.
    """
    out = _out("gold_dashboard_fact")

    # Pre-register views for readability
    con.execute(f"CREATE OR REPLACE VIEW v_sub   AS SELECT * FROM read_parquet('{_silver('fct_subscription')}')")
    con.execute(f"CREATE OR REPLACE VIEW v_acc   AS SELECT * FROM read_parquet('{_silver('dim_account')}')")
    con.execute(f"CREATE OR REPLACE VIEW v_plan  AS SELECT * FROM read_parquet('{_silver('dim_plan')}')")
    con.execute(f"CREATE OR REPLACE VIEW v_usage AS SELECT * FROM read_parquet('{_silver('fct_feature_usage')}')")
    con.execute(f"CREATE OR REPLACE VIEW v_tkt   AS SELECT * FROM read_parquet('{_silver('fct_support_ticket')}')")
    con.execute(f"CREATE OR REPLACE VIEW v_churn AS SELECT * FROM read_parquet('{_silver('fct_churn_event')}')")

    con.execute(f"""
        COPY (
            WITH

            -- One row per subscription per year-month active
            sub_months AS (
                SELECT
                    s.subscription_id,
                    s.account_id,
                    s.plan_id,
                    s.mrr,
                    s.arr,
                    s.has_downgrade,
                    s.churn_flag,
                    s.start_date,
                    s.end_date,
                    STRFTIME(s.start_date, '%Y-%m') AS year_month
                FROM v_sub s
            ),

            -- Top feature per (account × year_month)
            usage_per_feature AS (
                SELECT
                    s.account_id,
                    STRFTIME(u.date_id, '%Y-%m') AS year_month,
                    u.feature_name,
                    SUM(u.usage_count) AS feature_usage_total
                FROM v_usage u
                JOIN v_sub s ON u.subscription_id = s.subscription_id
                GROUP BY s.account_id, STRFTIME(u.date_id, '%Y-%m'), u.feature_name
            ),
            top_feature_per_account AS (
                SELECT account_id, year_month, feature_name AS top_feature
                FROM usage_per_feature
                QUALIFY ROW_NUMBER() OVER (PARTITION BY account_id, year_month ORDER BY feature_usage_total DESC) = 1
            ),

            -- Aggregate usage per (account × year_month)
            usage_agg AS (
                SELECT
                    s.account_id,
                    STRFTIME(u.date_id, '%Y-%m') AS year_month,
                    SUM(u.usage_count)             AS total_usage_count,
                    SUM(u.usage_duration)          AS total_usage_duration,
                    SUM(u.error_count)             AS total_error_count,
                    COUNT(DISTINCT u.feature_name) AS distinct_features_used
                FROM v_usage u
                JOIN v_sub s ON u.subscription_id = s.subscription_id
                GROUP BY s.account_id, STRFTIME(u.date_id, '%Y-%m')
            ),

            -- Aggregate support per (account × year_month)
            support_agg AS (
                SELECT
                    account_id,
                    STRFTIME(date_id, '%Y-%m')          AS year_month,
                    COUNT(*)                             AS ticket_count,
                    AVG(resolution_time)                AS avg_resolution_time,
                    AVG(first_response_time)            AS avg_first_response_time,
                    AVG(satisfaction_score)             AS avg_satisfaction_score,
                    SUM(CASE WHEN is_escalated THEN 1 ELSE 0 END) AS escalated_tickets
                FROM v_tkt
                GROUP BY account_id, STRFTIME(date_id, '%Y-%m')
            ),

            -- Segment usage averages for risk signal computation
            seg_usage_avg AS (
                SELECT
                    a.industry,
                    STRFTIME(u.date_id, '%Y-%m')   AS year_month,
                    AVG(u.usage_count)              AS avg_usage_count,
                    AVG(CASE WHEN u.usage_count > 0
                             THEN CAST(u.error_count AS FLOAT) / u.usage_count
                             ELSE 0 END)            AS avg_error_rate
                FROM v_usage u
                JOIN v_sub s  ON u.subscription_id = s.subscription_id
                JOIN v_acc a  ON s.account_id = a.account_id
                GROUP BY a.industry, STRFTIME(u.date_id, '%Y-%m')
            ),

            -- Base: one row per (account × year_month) from subscriptions
            base AS (
                SELECT DISTINCT
                    sm.account_id,
                    sm.year_month,
                    sm.plan_id,
                    sm.mrr,
                    sm.arr,
                    sm.has_downgrade  AS has_downgrade_in_period,
                    sm.churn_flag
                FROM sub_months sm
            ),

            -- Churn events per (account × year_month)
            churn_in_period AS (
                SELECT
                    account_id,
                    STRFTIME(date_id, '%Y-%m') AS year_month,
                    TRUE                        AS churned_in_period,
                    reason_code                 AS churn_reason_code
                FROM v_churn
            )

            SELECT
                b.account_id,
                b.year_month,
                a.industry,
                a.country,
                a.acquisition_channel,
                p.plan_name,
                p.billing_frequency,
                a.is_trial,

                -- Financial
                b.mrr,
                b.arr,
                b.has_downgrade_in_period,
                COALESCE(c.churned_in_period, FALSE)    AS churned_in_period,
                c.churn_reason_code,
                CASE WHEN c.churned_in_period THEN b.mrr ELSE 0.0 END AS mrr_lost,

                -- Usage
                COALESCE(u.total_usage_count, 0)        AS total_usage_count,
                COALESCE(u.total_usage_duration, 0.0)   AS total_usage_duration,
                COALESCE(u.total_error_count, 0)        AS total_error_count,
                COALESCE(u.distinct_features_used, 0)   AS distinct_features_used,
                tf.top_feature,
                CASE WHEN COALESCE(u.total_usage_count, 0) > 0
                     THEN CAST(u.total_error_count AS FLOAT) / u.total_usage_count
                     ELSE 0.0 END                       AS error_rate,

                -- Support
                COALESCE(t.ticket_count, 0)             AS ticket_count,
                t.avg_resolution_time,
                t.avg_first_response_time,
                t.avg_satisfaction_score,
                COALESCE(t.escalated_tickets, 0)        AS escalated_tickets,

                -- Risk signals
                CASE WHEN COALESCE(u.total_usage_count, 0) < 0.2 * COALESCE(su.avg_usage_count, 1)
                     THEN TRUE ELSE FALSE END           AS signal_low_usage,
                CASE WHEN (CASE WHEN COALESCE(u.total_usage_count, 0) > 0
                                THEN CAST(u.total_error_count AS FLOAT) / u.total_usage_count
                                ELSE 0 END)
                          > 2.0 * COALESCE(su.avg_error_rate, 0)
                     THEN TRUE ELSE FALSE END           AS signal_high_errors,
                CASE WHEN COALESCE(t.avg_satisfaction_score, 5.0) < 3.0
                          OR COALESCE(t.escalated_tickets, 0) > 0
                     THEN TRUE ELSE FALSE END           AS signal_bad_support,
                b.has_downgrade_in_period               AS signal_downgrade,

                -- risk_score: sum of signals × 0.25
                (
                    CAST(CASE WHEN COALESCE(u.total_usage_count, 0) < 0.2 * COALESCE(su.avg_usage_count, 1)
                              THEN 1 ELSE 0 END AS FLOAT) +
                    CAST(CASE WHEN (CASE WHEN COALESCE(u.total_usage_count, 0) > 0
                                        THEN CAST(u.total_error_count AS FLOAT) / u.total_usage_count
                                        ELSE 0 END)
                                   > 2.0 * COALESCE(su.avg_error_rate, 0)
                              THEN 1 ELSE 0 END AS FLOAT) +
                    CAST(CASE WHEN COALESCE(t.avg_satisfaction_score, 5.0) < 3.0
                                   OR COALESCE(t.escalated_tickets, 0) > 0
                              THEN 1 ELSE 0 END AS FLOAT) +
                    CAST(b.has_downgrade_in_period AS FLOAT)
                ) * 0.25                                AS risk_score,

                CASE
                    WHEN ((
                        CAST(CASE WHEN COALESCE(u.total_usage_count, 0) < 0.2 * COALESCE(su.avg_usage_count, 1) THEN 1 ELSE 0 END AS FLOAT) +
                        CAST(CASE WHEN (CASE WHEN COALESCE(u.total_usage_count, 0) > 0 THEN CAST(u.total_error_count AS FLOAT) / u.total_usage_count ELSE 0 END) > 2.0 * COALESCE(su.avg_error_rate, 0) THEN 1 ELSE 0 END AS FLOAT) +
                        CAST(CASE WHEN COALESCE(t.avg_satisfaction_score, 5.0) < 3.0 OR COALESCE(t.escalated_tickets, 0) > 0 THEN 1 ELSE 0 END AS FLOAT) +
                        CAST(b.has_downgrade_in_period AS FLOAT)
                    ) * 0.25) < 0.25  THEN 'low'
                    WHEN ((
                        CAST(CASE WHEN COALESCE(u.total_usage_count, 0) < 0.2 * COALESCE(su.avg_usage_count, 1) THEN 1 ELSE 0 END AS FLOAT) +
                        CAST(CASE WHEN (CASE WHEN COALESCE(u.total_usage_count, 0) > 0 THEN CAST(u.total_error_count AS FLOAT) / u.total_usage_count ELSE 0 END) > 2.0 * COALESCE(su.avg_error_rate, 0) THEN 1 ELSE 0 END AS FLOAT) +
                        CAST(CASE WHEN COALESCE(t.avg_satisfaction_score, 5.0) < 3.0 OR COALESCE(t.escalated_tickets, 0) > 0 THEN 1 ELSE 0 END AS FLOAT) +
                        CAST(b.has_downgrade_in_period AS FLOAT)
                    ) * 0.25) < 0.50  THEN 'medium'
                    WHEN ((
                        CAST(CASE WHEN COALESCE(u.total_usage_count, 0) < 0.2 * COALESCE(su.avg_usage_count, 1) THEN 1 ELSE 0 END AS FLOAT) +
                        CAST(CASE WHEN (CASE WHEN COALESCE(u.total_usage_count, 0) > 0 THEN CAST(u.total_error_count AS FLOAT) / u.total_usage_count ELSE 0 END) > 2.0 * COALESCE(su.avg_error_rate, 0) THEN 1 ELSE 0 END AS FLOAT) +
                        CAST(CASE WHEN COALESCE(t.avg_satisfaction_score, 5.0) < 3.0 OR COALESCE(t.escalated_tickets, 0) > 0 THEN 1 ELSE 0 END AS FLOAT) +
                        CAST(b.has_downgrade_in_period AS FLOAT)
                    ) * 0.25) < 0.75  THEN 'high'
                    ELSE 'critical'
                END                                     AS risk_tier

            FROM base b
            JOIN v_acc a   ON b.account_id = a.account_id
            JOIN v_plan p  ON b.plan_id    = p.plan_id
            LEFT JOIN usage_agg u                ON b.account_id = u.account_id AND b.year_month = u.year_month
            LEFT JOIN top_feature_per_account tf ON b.account_id = tf.account_id AND b.year_month = tf.year_month
            LEFT JOIN support_agg t              ON b.account_id = t.account_id AND b.year_month = t.year_month
            LEFT JOIN churn_in_period c          ON b.account_id = c.account_id AND b.year_month = c.year_month
            LEFT JOIN seg_usage_avg su           ON a.industry   = su.industry  AND b.year_month = su.year_month
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("gold_dashboard_fact: %s rows", f"{n:,}")
    return n


def build_account_risk(con: duckdb.DuckDBPyConnection) -> int:
    """One row per active account (not churned). Includes risk signals and recommended action."""
    out = _out("gold_account_risk")

    con.execute(f"CREATE OR REPLACE VIEW v_acc_raw AS SELECT * FROM read_parquet('{_silver('dim_account')}')")

    con.execute(f"""
        COPY (
            WITH latest AS (
                SELECT
                    account_id,
                    year_month,
                    mrr,
                    signal_low_usage,
                    signal_high_errors,
                    signal_bad_support,
                    signal_downgrade,
                    risk_score,
                    risk_tier,
                    total_usage_count,
                    avg_satisfaction_score,
                    escalated_tickets,
                    ticket_count
                FROM read_parquet('{_out("gold_dashboard_fact")}')
                QUALIFY ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY year_month DESC) = 1
            ),

            -- Days since last usage per account
            last_usage AS (
                SELECT
                    s.account_id,
                    MAX(u.date_id) AS last_usage_date
                FROM read_parquet('{_silver("fct_feature_usage")}') u
                JOIN read_parquet('{_silver("fct_subscription")}') s ON u.subscription_id = s.subscription_id
                GROUP BY s.account_id
            ),

            -- Accounts that have not churned
            active_accounts AS (
                SELECT account_id
                FROM read_parquet('{_silver("fct_subscription")}')
                WHERE churn_flag = FALSE
            )

            SELECT
                l.account_id,
                ar.account_name,
                a.industry,
                a.country,
                l.mrr,
                l.risk_score,
                l.risk_tier,
                l.signal_low_usage,
                l.signal_high_errors,
                l.signal_bad_support,
                l.signal_downgrade,
                DATEDIFF('day', lu.last_usage_date, CURRENT_DATE) AS days_since_last_usage,
                l.ticket_count AS open_tickets,
                l.avg_satisfaction_score AS last_satisfaction_score,
                CASE l.risk_tier
                    WHEN 'critical' THEN 'Immediate CS intervention'
                    WHEN 'high'     THEN 'Proactive outreach + feature review'
                    WHEN 'medium'   THEN 'Check-in + usage nudge'
                    ELSE                 'Monitor'
                END AS recommended_action,
                NOW()::TIMESTAMP AS _calculated_at
            FROM latest l
            JOIN (
                SELECT account_id, account_name
                FROM read_parquet('{_bronze("bronze_accounts")}')
            ) ar ON l.account_id = ar.account_id
            JOIN v_acc_raw a ON l.account_id = a.account_id
            LEFT JOIN last_usage lu ON l.account_id = lu.account_id
            WHERE l.account_id IN (SELECT account_id FROM active_accounts)
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("gold_account_risk: %s rows", f"{n:,}")

    dist = con.execute(f"""
        SELECT risk_tier, COUNT(*) AS cnt
        FROM read_parquet('{out}')
        GROUP BY risk_tier ORDER BY cnt DESC
    """).fetchall()
    log.info("  risk_tier distribution: %s", {t: c for t, c in dist})
    return n


def build_churn_drivers(con: duckdb.DuckDBPyConnection) -> int:
    """Churn aggregated by (year_month × segment_type × segment_value)."""
    out = _out("gold_churn_drivers")
    df_path = str(_out("gold_dashboard_fact"))

    con.execute(f"""
        COPY (
            WITH df AS (SELECT * FROM read_parquet('{df_path}'))
            SELECT year_month, 'industry' AS segment_type, industry AS segment_value,
                   SUM(CASE WHEN churned_in_period THEN 1 ELSE 0 END) AS churned_accounts,
                   COUNT(DISTINCT account_id)                           AS total_accounts,
                   CAST(SUM(CASE WHEN churned_in_period THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(DISTINCT account_id), 0) AS churn_rate,
                   SUM(mrr_lost)                                        AS mrr_lost,
                   MODE(churn_reason_code)                              AS top_reason_code
            FROM df GROUP BY year_month, industry

            UNION ALL

            SELECT year_month, 'country', country,
                   SUM(CASE WHEN churned_in_period THEN 1 ELSE 0 END),
                   COUNT(DISTINCT account_id),
                   CAST(SUM(CASE WHEN churned_in_period THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(DISTINCT account_id), 0),
                   SUM(mrr_lost), MODE(churn_reason_code)
            FROM df GROUP BY year_month, country

            UNION ALL

            SELECT year_month, 'channel', acquisition_channel,
                   SUM(CASE WHEN churned_in_period THEN 1 ELSE 0 END),
                   COUNT(DISTINCT account_id),
                   CAST(SUM(CASE WHEN churned_in_period THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(DISTINCT account_id), 0),
                   SUM(mrr_lost), MODE(churn_reason_code)
            FROM df GROUP BY year_month, acquisition_channel

            UNION ALL

            SELECT year_month, 'plan', plan_name,
                   SUM(CASE WHEN churned_in_period THEN 1 ELSE 0 END),
                   COUNT(DISTINCT account_id),
                   CAST(SUM(CASE WHEN churned_in_period THEN 1 ELSE 0 END) AS FLOAT) / NULLIF(COUNT(DISTINCT account_id), 0),
                   SUM(mrr_lost), MODE(churn_reason_code)
            FROM df GROUP BY year_month, plan_name

            ORDER BY year_month, segment_type, churn_rate DESC
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("gold_churn_drivers: %s rows", f"{n:,}")
    return n


def build_feature_retention(con: duckdb.DuckDBPyConnection) -> int:
    """Per (feature × year_month): avg usage for retained vs churned accounts."""
    out = _out("gold_feature_retention")

    con.execute(f"""
        COPY (
            WITH usage_labeled AS (
                SELECT
                    u.feature_name,
                    STRFTIME(u.date_id, '%Y-%m') AS year_month,
                    u.usage_count,
                    u.error_count,
                    -- Mark if account churned in same year_month
                    CASE WHEN c.account_id IS NOT NULL THEN 'churned' ELSE 'retained' END AS cohort
                FROM read_parquet('{_silver("fct_feature_usage")}') u
                JOIN read_parquet('{_silver("fct_subscription")}') s ON u.subscription_id = s.subscription_id
                LEFT JOIN (
                    SELECT account_id, STRFTIME(date_id, '%Y-%m') AS churn_ym
                    FROM read_parquet('{_silver("fct_churn_event")}')
                ) c ON s.account_id = c.account_id
                       AND STRFTIME(u.date_id, '%Y-%m') = c.churn_ym
            )
            SELECT
                feature_name,
                year_month,
                AVG(CASE WHEN cohort = 'retained' THEN CAST(usage_count AS FLOAT) END) AS retained_avg_usage,
                AVG(CASE WHEN cohort = 'churned'  THEN CAST(usage_count AS FLOAT) END) AS churned_avg_usage,
                AVG(CASE WHEN cohort = 'retained' THEN CAST(error_count AS FLOAT) END) AS retained_avg_errors,
                AVG(CASE WHEN cohort = 'churned'  THEN CAST(error_count AS FLOAT) END) AS churned_avg_errors,
                AVG(CASE WHEN cohort = 'retained' THEN CAST(usage_count AS FLOAT) END) /
                    NULLIF(AVG(CASE WHEN cohort = 'churned' THEN CAST(usage_count AS FLOAT) END), 0) AS retention_lift,
                NOW()::TIMESTAMP AS _calculated_at
            FROM usage_labeled
            GROUP BY feature_name, year_month
            ORDER BY feature_name, year_month
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("gold_feature_retention: %s rows", f"{n:,}")
    return n


def build_support_health(con: duckdb.DuckDBPyConnection) -> int:
    """Per (year_month × industry): support KPIs + churn rate among high-ticket accounts."""
    out = _out("gold_support_health")

    con.execute(f"""
        COPY (
            WITH account_industry AS (
                SELECT account_id, industry
                FROM read_parquet('{_silver("dim_account")}')
            ),
            tickets AS (
                SELECT
                    t.ticket_id,
                    t.account_id,
                    STRFTIME(t.date_id, '%Y-%m') AS year_month,
                    t.resolution_time,
                    t.first_response_time,
                    t.satisfaction_score,
                    t.is_escalated,
                    a.industry
                FROM read_parquet('{_silver("fct_support_ticket")}') t
                JOIN account_industry a ON t.account_id = a.account_id
            ),
            churned AS (
                SELECT account_id, STRFTIME(date_id, '%Y-%m') AS year_month
                FROM read_parquet('{_silver("fct_churn_event")}')
            ),
            accounts_per_industry_month AS (
                SELECT industry, year_month, COUNT(DISTINCT account_id) AS total_accounts
                FROM (
                    SELECT a.industry, STRFTIME(s.start_date, '%Y-%m') AS year_month, a.account_id
                    FROM read_parquet('{_silver("fct_subscription")}') s
                    JOIN account_industry a ON s.account_id = a.account_id
                ) sub GROUP BY industry, year_month
            ),
            high_ticket_accounts AS (
                SELECT account_id, year_month, industry, COUNT(*) AS ticket_cnt
                FROM tickets
                GROUP BY account_id, year_month, industry
                HAVING COUNT(*) >= 3
            )
            SELECT
                t.year_month,
                t.industry,
                AVG(t.resolution_time)                                      AS avg_resolution_time,
                AVG(t.first_response_time)                                  AS avg_first_response_time,
                AVG(t.satisfaction_score)                                   AS avg_satisfaction_score,
                AVG(CAST(t.is_escalated AS FLOAT))                          AS escalation_rate,
                CAST(COUNT(DISTINCT t.account_id) AS FLOAT) /
                    NULLIF(MAX(ai.total_accounts), 0)                       AS pct_accounts_with_ticket,
                -- churn rate among accounts with 3+ tickets
                CAST(COUNT(DISTINCT CASE WHEN hta.account_id IS NOT NULL
                                          AND c.account_id  IS NOT NULL
                                         THEN t.account_id END) AS FLOAT) /
                    NULLIF(COUNT(DISTINCT hta.account_id), 0)               AS churn_rate_high_tickets,
                NOW()::TIMESTAMP                                            AS _calculated_at
            FROM tickets t
            LEFT JOIN accounts_per_industry_month ai ON t.industry = ai.industry AND t.year_month = ai.year_month
            LEFT JOIN high_ticket_accounts hta ON t.account_id = hta.account_id AND t.year_month = hta.year_month
            LEFT JOIN churned c ON t.account_id = c.account_id AND t.year_month = c.year_month
            GROUP BY t.year_month, t.industry
            ORDER BY t.year_month, t.industry
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("gold_support_health: %s rows", f"{n:,}")
    return n


def main() -> None:
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    build_dashboard_fact(con)
    build_account_risk(con)
    build_churn_drivers(con)
    build_feature_retention(con)
    build_support_health(con)

    log.info("Gold complete — 5 tables written to %s", GOLD_DIR)
    con.close()


if __name__ == "__main__":
    main()
