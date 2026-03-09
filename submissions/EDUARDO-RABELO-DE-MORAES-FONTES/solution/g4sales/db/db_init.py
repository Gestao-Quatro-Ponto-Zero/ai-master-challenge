import csv
import sqlite3
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "data" / "sales.sqlite3"

PRODUCT_ALIASES = {
    "GTXPro": "GTX Pro",
}


def to_int(value: str) -> Optional[int]:
    value = (value or "").strip()
    if not value:
        return None
    return int(value)


def to_float(value: str) -> Optional[float]:
    value = (value or "").strip()
    if not value:
        return None
    return float(value)


def normalize_product(value: str) -> Optional[str]:
    value = (value or "").strip()
    if not value:
        return None
    return PRODUCT_ALIASES.get(value, value)


def create_tables(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            account TEXT PRIMARY KEY,
            sector TEXT,
            year_established INTEGER,
            revenue REAL,
            employees INTEGER,
            office_location TEXT,
            subsidiary_of TEXT
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            product TEXT PRIMARY KEY,
            series TEXT,
            sales_price REAL
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sales_teams (
            sales_agent TEXT PRIMARY KEY,
            manager TEXT,
            regional_office TEXT
        );
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sales_pipeline (
            opportunity_id TEXT PRIMARY KEY,
            sales_agent TEXT,
            product TEXT,
            account TEXT,
            deal_stage TEXT,
            engage_date TEXT,
            close_date TEXT,
            close_value REAL,
            FOREIGN KEY (sales_agent) REFERENCES sales_teams (sales_agent),
            FOREIGN KEY (product) REFERENCES products (product),
            FOREIGN KEY (account) REFERENCES accounts (account)
        );
        """
    )


def import_accounts(conn: sqlite3.Connection) -> None:
    path = DATA_DIR / "accounts.csv"
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            rows.append(
                (
                    (r["account"] or "").strip(),
                    (r["sector"] or "").strip() or None,
                    to_int(r["year_established"]),
                    to_float(r["revenue"]),
                    to_int(r["employees"]),
                    (r["office_location"] or "").strip() or None,
                    (r["subsidiary_of"] or "").strip() or None,
                )
            )

    conn.executemany(
        """
        INSERT OR IGNORE INTO accounts (
            account, sector, year_established, revenue, employees, office_location, subsidiary_of
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        rows,
    )


def import_products(conn: sqlite3.Connection) -> None:
    path = DATA_DIR / "products.csv"
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            rows.append(
                (
                    (r["product"] or "").strip(),
                    (r["series"] or "").strip() or None,
                    to_float(r["sales_price"]),
                )
            )

    conn.executemany(
        """
        INSERT OR IGNORE INTO products (product, series, sales_price)
        VALUES (?, ?, ?);
        """,
        rows,
    )


def import_sales_teams(conn: sqlite3.Connection) -> None:
    path = DATA_DIR / "sales_teams.csv"
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            rows.append(
                (
                    (r["sales_agent"] or "").strip(),
                    (r["manager"] or "").strip() or None,
                    (r["regional_office"] or "").strip() or None,
                )
            )

    conn.executemany(
        """
        INSERT OR IGNORE INTO sales_teams (sales_agent, manager, regional_office)
        VALUES (?, ?, ?);
        """,
        rows,
    )


def import_sales_pipeline(conn: sqlite3.Connection) -> None:
    path = DATA_DIR / "sales_pipeline.csv"
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            product = normalize_product(r["product"])
            account = (r["account"] or "").strip() or None
            close_date = (r["close_date"] or "").strip() or None
            close_value = to_float(r["close_value"])

            rows.append(
                (
                    (r["opportunity_id"] or "").strip(),
                    (r["sales_agent"] or "").strip() or None,
                    product,
                    account,
                    (r["deal_stage"] or "").strip() or None,
                    (r["engage_date"] or "").strip() or None,
                    close_date,
                    close_value,
                )
            )

    conn.executemany(
        """
        INSERT OR IGNORE INTO sales_pipeline (
            opportunity_id, sales_agent, product, account, deal_stage, engage_date, close_date, close_value
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        rows,
    )


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        create_tables(conn)
        import_accounts(conn)
        import_products(conn)
        import_sales_teams(conn)
        import_sales_pipeline(conn)
        conn.commit()

    print(f"Banco inicializado com sucesso em: {DB_PATH}")


if __name__ == "__main__":
    init_db()
