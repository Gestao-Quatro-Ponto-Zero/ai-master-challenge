"""Repositório da entidade User."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from ...db import slugify, utc_now
from ..database import Database
from ..models import User
from ._common import as_dict


def users_from_tables(tables: dict | None, now: str | None = None) -> list[dict]:
    """Usuários do MVP a partir das tabelas do modelo: admin 'revops', vendedores e managers."""
    now = now or utc_now()
    rows = [{"user_key": "revops", "full_name": "RevOps", "role": "revops", "manager": None,
             "regional_office": None, "created_at": now}]
    managers: dict[str, str] = {}
    for name, info in (tables or {}).get("agents", {}).items():
        rows.append({"user_key": slugify(name), "full_name": name, "role": "seller", "manager": info["manager"],
                     "regional_office": info["regional_office"], "created_at": now})
        managers.setdefault(info["manager"], info["regional_office"])
    rows += [{"user_key": slugify(n), "full_name": n, "role": "manager", "manager": None, "regional_office": o,
              "created_at": now} for n, o in managers.items()]
    return rows


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_active(self, user_key: str) -> dict | None:
        with self.db.session() as s:
            u = s.execute(select(User).where(User.user_key == user_key, User.is_active == 1)).scalar_one_or_none()
            return None if u is None else as_dict(u)

    def add_missing(self, rows: list[dict]) -> int:
        """Insere só os que não existem (idempotente). Devolve quantos foram criados."""
        if not rows:
            return 0
        with self.db.session() as s:
            result = s.execute(sqlite_insert(User).values(rows).on_conflict_do_nothing())
            return int(result.rowcount or 0)

    def seed_from_tables(self, tables: dict | None) -> int:
        return self.add_missing(users_from_tables(tables))

    def count(self) -> int:
        with self.db.session() as s:
            return len(s.execute(select(User.user_key)).all())
