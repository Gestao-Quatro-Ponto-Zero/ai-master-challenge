"""Engine + sessões SQLAlchemy sobre o SQLite. O esquema é criado pelo SQL congelado (db.init_db), nunca pelo ORM."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from ..db import init_db


def _pragmas(dbapi_conn, _record) -> None:
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute("PRAGMA journal_mode = WAL")
    cur.close()


class Database:
    """Uma conexão por sessão (NullPool): seguro com a API e o treinador acessando o mesmo arquivo."""

    def __init__(self, path: str | Path, create_schema: bool = True):
        self.path = Path(path)
        if create_schema:
            init_db(self.path)                      # idempotente; usa schema_v1.sql
        self.engine = create_engine(f"sqlite:///{self.path}", poolclass=NullPool, connect_args={"timeout": 30})
        event.listen(self.engine, "connect", _pragmas)

    @contextmanager
    def session(self) -> Iterator[Session]:
        s = Session(self.engine, expire_on_commit=False)
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    def dispose(self) -> None:
        self.engine.dispose()
