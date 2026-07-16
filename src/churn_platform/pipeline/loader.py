"""SPEC-2 REQ-2-001: Load genérico (CSV, JSON, Parquet)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

LOADERS = {
    ".csv": pd.read_csv,
    ".json": pd.read_json,
    ".parquet": pd.read_parquet,
    ".pqt": pd.read_parquet,
}


def resolve_source_path(raw: str, base_dir: str | None = None) -> Path:
    path = Path(raw)
    if not path.is_absolute() and base_dir:
        path = Path(base_dir) / path
    return path.resolve()


def load_source(
    source_config: dict[str, Any],
    base_dir: str | None = None,
) -> pd.DataFrame:
    path = resolve_source_path(source_config["path"], base_dir)
    suffix = path.suffix.lower()
    loader = LOADERS.get(suffix)

    if loader is None:
        raise ValueError(f"Formato não suportado: {suffix}. Use: {list(LOADERS.keys())}")

    logger.info("Carregando %s (%s)", path.name, suffix)
    df = loader(path)
    logger.info("  → %s linhas × %s colunas", len(df), len(df.columns))
    return df


def load_all_sources(
    config: dict[str, Any],
    base_dir: str | None = None,
) -> dict[str, pd.DataFrame]:
    sources_config = config.get("sources", {})
    sources: dict[str, pd.DataFrame] = {}

    for name, cfg in sources_config.items():
        sources[name] = load_source(cfg, base_dir)

    return sources
