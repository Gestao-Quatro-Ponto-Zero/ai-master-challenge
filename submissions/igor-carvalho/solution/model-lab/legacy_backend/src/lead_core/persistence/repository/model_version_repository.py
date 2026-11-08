"""Repositório da entidade ModelVersion."""
from __future__ import annotations

import json

from sqlalchemy import select, update

from ...db import utc_now
from ..database import Database
from ..models import ModelVersion
from ._common import as_dict


class ModelVersionRepository:
    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def _out(m: ModelVersion | None) -> dict | None:
        if m is None:
            return None
        d = as_dict(m, exclude=("metrics_json",))
        d["metrics"] = json.loads(m.metrics_json)
        return d

    def register(self, version: str, engine: str, trained_at: str, reference_date: str, artifact_path: str,
                 metrics: dict) -> None:
        with self.db.session() as s:
            s.add(ModelVersion(version=version, engine=engine, trained_at=trained_at, reference_date=reference_date,
                               artifact_path=artifact_path, metrics_json=json.dumps(metrics, ensure_ascii=False),
                               status="candidate"))

    def get(self, version: str) -> dict | None:
        with self.db.session() as s:
            return self._out(s.get(ModelVersion, version))

    def active(self) -> dict | None:
        with self.db.session() as s:
            return self._out(s.execute(select(ModelVersion).where(ModelVersion.status == "active")).scalar_one_or_none())

    def list(self) -> list[dict]:
        with self.db.session() as s:
            rows = s.execute(select(ModelVersion).order_by(ModelVersion.trained_at.desc(),
                                                           ModelVersion.version.desc())).scalars()
            return [self._out(r) for r in rows]

    def versions_with_prefix(self, prefix: str) -> list[str]:
        with self.db.session() as s:
            return list(s.execute(select(ModelVersion.version).where(ModelVersion.version.like(prefix + "%"))).scalars())

    def promote(self, version: str) -> None:
        """Aposenta a versão ativa e ativa a escolhida (mesma transação; o índice parcial garante 1 ativa)."""
        with self.db.session() as s:
            if s.get(ModelVersion, version) is None:
                raise KeyError(f"Versão {version} não registrada")
            s.execute(update(ModelVersion).where(ModelVersion.status == "active").values(status="retired"))
            s.execute(update(ModelVersion).where(ModelVersion.version == version)
                      .values(status="active", promoted_at=utc_now(), reject_reason=None))

    def reject(self, version: str, reason: str) -> None:
        with self.db.session() as s:
            s.execute(update(ModelVersion).where(ModelVersion.version == version)
                      .values(status="rejected", reject_reason=reason))
