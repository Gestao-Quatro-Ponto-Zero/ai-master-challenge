"""Carrega o modelo ativo e os deals já pontuados (somente leitura, em memória). Troca atômica no reload."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from lead_core.bundle import SCORED_FILE, ModelBundle

from .errors import model_not_ready


@dataclass(frozen=True)
class LoadedModel:
    bundle: ModelBundle
    deals: pd.DataFrame        # indexado por opportunity_id


class ScoreStore:
    def __init__(self, artifact_dir: Path):
        self.artifact_dir = Path(artifact_dir)
        self._state: LoadedModel | None = None
        self._lock = threading.Lock()

    def reload(self) -> str | None:
        """Lê o ponteiro CURRENT e carrega a versão. Se não houver, fica 'não pronto'. Retorna a versão."""
        pointer = self.artifact_dir / "CURRENT"
        if not pointer.exists():
            with self._lock:
                self._state = None
            return None
        version = pointer.read_text().strip()
        folder = self.artifact_dir / f"v{version}"
        bundle = ModelBundle.load(folder)
        deals = pd.read_parquet(folder / SCORED_FILE).set_index("opportunity_id", drop=False)
        with self._lock:
            self._state = LoadedModel(bundle, deals)
        return version

    @property
    def tables(self) -> dict | None:
        return self._state.bundle.tables if self._state else None

    @property
    def ready(self) -> bool:
        return self._state is not None

    def require(self) -> LoadedModel:
        state = self._state
        if state is None:
            raise model_not_ready()
        return state

    def sellers_of_manager(self, manager: str) -> frozenset[str]:
        if self._state is None:
            return frozenset()
        agents = self._state.bundle.tables["agents"]
        return frozenset(a for a, info in agents.items() if info["manager"] == manager)
