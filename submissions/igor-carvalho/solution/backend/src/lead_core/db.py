"""Acesso ao SQLite. O esquema é o arquivo sql/schema_v1.sql e NÃO muda (sem migrações)."""
from __future__ import annotations

import hashlib
import re
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

SQL_DIR = Path(__file__).parent / "sql"
SCHEMA_FILE = SQL_DIR / "schema_v1.sql"
SCHEMA_HASH_FILE = SQL_DIR / "schema_v1.sha256"
SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def schema_sha256() -> str:
    return hashlib.sha256(SCHEMA_FILE.read_bytes()).hexdigest()


def slugify(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def session(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str | Path) -> None:
    """Cria as tabelas se não existirem (idempotente). Nunca altera tabelas existentes."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with session(db_path) as conn:
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT OR IGNORE INTO schema_info (id, version, applied_at) VALUES (1, ?, ?)",
            (SCHEMA_VERSION, utc_now()),
        )
