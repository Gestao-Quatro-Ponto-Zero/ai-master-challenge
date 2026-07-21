from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

from config import DATABASE_PATH, REQUIRED_TABLES


class DatabaseValidationError(RuntimeError):
    pass


def generated_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_database(database_path: Path = DATABASE_PATH) -> None:
    if not database_path.exists():
        raise DatabaseValidationError(
            "Banco SQLite nao encontrado. Esperado em database/ravenstack.db."
        )

    connection = sqlite3.connect(database_path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    finally:
        connection.close()

    missing = sorted(REQUIRED_TABLES - tables)
    if missing:
        raise DatabaseValidationError(
            "Tabelas ausentes no SQLite: " + ", ".join(missing)
        )


@contextmanager
def get_connection(database_path: Path = DATABASE_PATH):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def query_df(sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    import pandas as pd

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        return pd.read_sql_query(sql, connection, params=params or {})
    finally:
        connection.close()


def query_rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(sql, params or {}).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def query_one(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(sql, params or {}).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def response_payload(data: Any, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "metadata": {
            "generated_at": generated_at(),
            "filters": filters or {},
        },
    }


def clean_number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number == float("inf") or number == float("-inf"):
        return default
    return number
