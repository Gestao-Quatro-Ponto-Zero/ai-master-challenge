"""
Bronze layer ingestion: reads raw CSVs, adds metadata, writes Parquet.
No business transformations — preserve source data as-is.
"""
import logging
from pathlib import Path

import duckdb

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
BRONZE_DIR = Path("data/bronze")

CSV_TABLE_MAP = {
    "ravenstack_accounts.csv": "bronze_accounts",
    "ravenstack_subscriptions.csv": "bronze_subscriptions",
    "ravenstack_feature_usage.csv": "bronze_feature_usage",
    "ravenstack_support_tickets.csv": "bronze_support_tickets",
    "ravenstack_churn_events.csv": "bronze_churn_events",
}


def ingest_table(con: duckdb.DuckDBPyConnection, csv_path: Path, table_name: str) -> int:
    out_path = BRONZE_DIR / f"{table_name}.parquet"
    source_file = csv_path.name

    con.execute(f"""
        COPY (
            SELECT
                *,
                NOW()::TIMESTAMP AS _ingested_at,
                '{source_file}' AS _source_file
            FROM read_csv_auto('{csv_path}', header=true)
        )
        TO '{out_path}' (FORMAT PARQUET)
    """)

    row_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{out_path}')").fetchone()[0]
    log.info("%-35s → %s  (%s rows)", source_file, out_path.name, f"{row_count:,}")
    return row_count


def main() -> None:
    BRONZE_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    total = 0
    for csv_name, table_name in CSV_TABLE_MAP.items():
        csv_path = RAW_DIR / csv_name
        if not csv_path.exists():
            log.warning("CSV not found, skipping: %s", csv_path)
            continue
        n = ingest_table(con, csv_path, table_name)
        total += n

    log.info("Bronze complete — %s total rows across %s files", f"{total:,}", len(CSV_TABLE_MAP))
    con.close()


if __name__ == "__main__":
    main()
