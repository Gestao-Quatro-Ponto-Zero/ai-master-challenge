"""Registro de versões: pasta artifacts/v{versão}/, ponteiro CURRENT e tabela model_versions (via repositório)."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from lead_core.persistence import Database, ModelVersionRepository

CURRENT_FILE = "CURRENT"


class ModelRegistry:
    def __init__(self, artifact_dir: str | Path, db_path: str | Path, versions: ModelVersionRepository | None = None):
        self.artifact_dir = Path(artifact_dir)
        self.db_path = Path(db_path)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.versions = versions or ModelVersionRepository(Database(self.db_path))

    # ------------------------------------------------------------------ leitura
    def version_dir(self, version: str) -> Path:
        return self.artifact_dir / f"v{version}"

    def current_version(self) -> str | None:
        p = self.artifact_dir / CURRENT_FILE
        return p.read_text().strip() if p.exists() else None

    def active(self) -> dict | None:
        return self.versions.active()

    def list(self) -> list[dict]:
        return self.versions.list()

    def next_version(self, now: datetime) -> str:
        prefix = f"{now:%Y.%m}."
        used = self.versions.versions_with_prefix(prefix)
        used += [p.name[1:] for p in self.artifact_dir.glob(f"v{prefix}*")]
        n = max([int(v.rsplit(".", 1)[1]) for v in used] + [0]) + 1
        return f"{prefix}{n}"

    # ------------------------------------------------------------------ escrita
    def register(self, version: str, engine: str, trained_at: str, reference_date: str, metrics: dict) -> None:
        self.versions.register(version, engine, trained_at, reference_date, str(self.version_dir(version)), metrics)

    def promote(self, version: str) -> None:
        """Aposenta a versão ativa, ativa a nova e atualiza o ponteiro CURRENT (troca atômica de arquivo)."""
        if not self.version_dir(version).exists():
            raise FileNotFoundError(f"Artefatos da versão {version} não existem")
        self.versions.promote(version)
        tmp = self.artifact_dir / f".{CURRENT_FILE}.tmp"
        tmp.write_text(version)
        os.replace(tmp, self.artifact_dir / CURRENT_FILE)

    def reject(self, version: str, reason: str) -> None:
        self.versions.reject(version, reason)
