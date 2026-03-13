"""
Silver layer transformation: reads bronze Parquets, cleans/types data,
builds star schema (4 dims + 4 facts), writes Parquet to data/silver/.
"""
import logging
from pathlib import Path

import duckdb

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")


def _parquet(name: str) -> str:
    return str(BRONZE_DIR / f"{name}.parquet")


def _out(name: str) -> Path:
    return SILVER_DIR / f"{name}.parquet"


def build_dim_date(con: duckdb.DuckDBPyConnection) -> int:
    """Generate a continuous date dimension covering all dates in the dataset."""
    out = _out("dim_date")
    con.execute(f"""
        COPY (
            WITH date_bounds AS (
                SELECT
                    MIN(min_date) AS start_date,
                    MAX(max_date) AS end_date
                FROM (
                    SELECT MIN(CAST(signup_date AS DATE))   AS min_date,
                           MAX(CAST(signup_date AS DATE))   AS max_date
                    FROM read_parquet('{_parquet("bronze_accounts")}')
                    UNION ALL
                    SELECT MIN(CAST(start_date AS DATE)),
                           MAX(CAST(start_date AS DATE))
                    FROM read_parquet('{_parquet("bronze_subscriptions")}')
                    UNION ALL
                    SELECT MIN(CAST(usage_date AS DATE)),
                           MAX(CAST(usage_date AS DATE))
                    FROM read_parquet('{_parquet("bronze_feature_usage")}')
                    UNION ALL
                    SELECT MIN(CAST(submitted_at AS DATE)),
                           MAX(CAST(submitted_at AS DATE))
                    FROM read_parquet('{_parquet("bronze_support_tickets")}')
                    UNION ALL
                    SELECT MIN(CAST(churn_date AS DATE)),
                           MAX(CAST(churn_date AS DATE))
                    FROM read_parquet('{_parquet("bronze_churn_events")}')
                ) bounds
            ),
            dates AS (
                SELECT UNNEST(generate_series(
                    start_date::TIMESTAMP,
                    end_date::TIMESTAMP,
                    INTERVAL 1 DAY
                ))::DATE AS date_id
                FROM date_bounds
            )
            SELECT
                date_id,
                YEAR(date_id)                                    AS year,
                QUARTER(date_id)                                 AS quarter,
                MONTH(date_id)                                   AS month,
                MONTHNAME(date_id)                               AS month_name,
                WEEK(date_id)                                    AS week,
                DAYOFWEEK(date_id)                               AS day_of_week,
                DAYOFWEEK(date_id) IN (0, 6)                     AS is_weekend
            FROM dates
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("dim_date: %s rows", f"{n:,}")
    return n


def build_dim_account(con: duckdb.DuckDBPyConnection) -> int:
    out = _out("dim_account")
    con.execute(f"""
        COPY (
            SELECT
                account_id,
                UPPER(TRIM(industry))       AS industry,
                UPPER(TRIM(country))        AS country,
                UPPER(TRIM(referral_source)) AS acquisition_channel,
                UPPER(TRIM(plan_tier))      AS plan_initial,
                CAST(is_trial AS BOOLEAN)   AS is_trial,
                NOW()::TIMESTAMP            AS _silver_processed_at
            FROM read_parquet('{_parquet("bronze_accounts")}')
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("dim_account: %s rows", f"{n:,}")
    return n


def build_dim_plan(con: duckdb.DuckDBPyConnection) -> int:
    out = _out("dim_plan")
    con.execute(f"""
        COPY (
            SELECT DISTINCT
                UPPER(TRIM(plan_tier)) || '_' || UPPER(TRIM(billing_frequency)) AS plan_id,
                UPPER(TRIM(plan_tier))       AS plan_name,
                UPPER(TRIM(billing_frequency)) AS billing_frequency
            FROM read_parquet('{_parquet("bronze_subscriptions")}')
            WHERE plan_tier IS NOT NULL
              AND billing_frequency IS NOT NULL
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("dim_plan: %s rows", f"{n:,}")
    return n


def build_dim_feature(con: duckdb.DuckDBPyConnection) -> int:
    out = _out("dim_feature")
    con.execute(f"""
        COPY (
            SELECT DISTINCT
                feature_name,
                MAX(CAST(is_beta_feature AS BOOLEAN)) AS is_beta
            FROM read_parquet('{_parquet("bronze_feature_usage")}')
            WHERE feature_name IS NOT NULL
            GROUP BY feature_name
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("dim_feature: %s rows", f"{n:,}")
    return n


def build_fct_subscription(con: duckdb.DuckDBPyConnection) -> int:
    out = _out("fct_subscription")
    con.execute(f"""
        COPY (
            SELECT
                subscription_id,
                account_id,
                UPPER(TRIM(plan_tier)) || '_' || UPPER(TRIM(billing_frequency)) AS plan_id,
                CAST(mrr_amount AS FLOAT)       AS mrr,
                CAST(arr_amount AS FLOAT)       AS arr,
                CAST(upgrade_flag AS BOOLEAN)   AS has_upgrade,
                CAST(downgrade_flag AS BOOLEAN) AS has_downgrade,
                CAST(start_date AS DATE)        AS start_date,
                TRY_CAST(end_date AS DATE)      AS end_date,
                CAST(churn_flag AS BOOLEAN)     AS churn_flag,
                CAST(is_trial AS BOOLEAN)       AS is_trial,
                NOW()::TIMESTAMP                AS _silver_processed_at
            FROM read_parquet('{_parquet("bronze_subscriptions")}')
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("fct_subscription: %s rows", f"{n:,}")
    return n


def build_fct_feature_usage(con: duckdb.DuckDBPyConnection) -> int:
    out = _out("fct_feature_usage")
    con.execute(f"""
        COPY (
            SELECT
                subscription_id,
                feature_name,
                CAST(usage_date AS DATE)            AS date_id,
                CAST(usage_count AS INT)            AS usage_count,
                CAST(usage_duration_secs AS FLOAT)  AS usage_duration,
                CAST(error_count AS INT)            AS error_count,
                NOW()::TIMESTAMP                    AS _silver_processed_at
            FROM read_parquet('{_parquet("bronze_feature_usage")}')
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("fct_feature_usage: %s rows", f"{n:,}")
    return n


def build_fct_support_ticket(con: duckdb.DuckDBPyConnection) -> int:
    out = _out("fct_support_ticket")
    con.execute(f"""
        COPY (
            SELECT
                ticket_id,
                account_id,
                CAST(submitted_at AS DATE)                          AS date_id,
                CAST(resolution_time_hours AS FLOAT)                AS resolution_time,
                CAST(first_response_time_minutes AS FLOAT) / 60.0  AS first_response_time,
                CAST(satisfaction_score AS FLOAT)                   AS satisfaction_score,
                CAST(escalation_flag AS BOOLEAN)                    AS is_escalated,
                UPPER(TRIM(priority))                               AS priority,
                NOW()::TIMESTAMP                                    AS _silver_processed_at
            FROM read_parquet('{_parquet("bronze_support_tickets")}')
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("fct_support_ticket: %s rows", f"{n:,}")
    return n


def build_fct_churn_event(con: duckdb.DuckDBPyConnection) -> int:
    out = _out("fct_churn_event")
    con.execute(f"""
        COPY (
            SELECT
                account_id,
                CAST(churn_date AS DATE)            AS date_id,
                UPPER(TRIM(reason_code))            AS reason_code,
                CAST(refund_amount_usd AS FLOAT)    AS refund_value,
                CAST(is_reactivation AS BOOLEAN)    AS is_reactivation,
                feedback_text,
                NOW()::TIMESTAMP                    AS _silver_processed_at
            FROM read_parquet('{_parquet("bronze_churn_events")}')
        )
        TO '{out}' (FORMAT PARQUET)
    """)
    n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out}')").fetchone()[0]
    log.info("fct_churn_event: %s rows", f"{n:,}")
    return n


def main() -> None:
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    # Dimensions first, then facts
    build_dim_date(con)
    build_dim_account(con)
    build_dim_plan(con)
    build_dim_feature(con)

    build_fct_subscription(con)
    build_fct_feature_usage(con)
    build_fct_support_ticket(con)
    build_fct_churn_event(con)

    log.info("Silver complete — 8 tables written to %s", SILVER_DIR)
    con.close()


if __name__ == "__main__":
    main()
