"""Acesso somente-leitura ao código do campeão (legacy_backend/src): põe src no sys.path e copia os CSVs para um workspace isolado."""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Código do modelo ANTIGO (campeão), congelado aqui: o backend de produção passou a usar o modelo de 30 dias
# (feature age_vs_cycle, outro alvo), então importar o backend atual duplicaria colunas e deixaria de ser o campeão.
DEFAULT_BACKEND = HERE.parent / "legacy_backend"
REAL_BACKEND = HERE.parent.parent / "backend"
CSV_FILES = ("sales_pipeline.csv", "sales_teams.csv", "products.csv", "accounts.csv")


def backend_dir() -> Path:
    return Path(os.environ.get("G4_LAB_BACKEND", DEFAULT_BACKEND)).resolve()


def use_backend_code() -> Path:
    src = backend_dir() / "src"
    if not (src / "lead_trainer").exists():
        raise FileNotFoundError(f"backend/src não encontrado em {src} (defina G4_LAB_BACKEND)")
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    return src


def source_data_dir() -> Path:
    return Path(os.environ.get("G4_LAB_DATA", REAL_BACKEND / "data")).resolve()


def fingerprint(folder: Path) -> dict[str, str]:
    """Hash dos arquivos de origem: o lab confere no fim que nada foi alterado."""
    return {f: hashlib.sha256((folder / f).read_bytes()).hexdigest() for f in CSV_FILES if (folder / f).exists()}


def make_workspace(root: Path) -> Path:
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    for f in CSV_FILES:
        shutil.copy2(source_data_dir() / f, data / f)
    return data
