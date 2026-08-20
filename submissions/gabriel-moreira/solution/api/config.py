"""Configuração da API a partir de variáveis de ambiente, com padrões
seguros para desenvolvimento local."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_EXPORT_PATH = Path(__file__).resolve().parent / "data" / "processed_pipeline.csv"


def _get_data_dir() -> Path:
    return Path(os.environ.get("LEAD_SCORER_DATA_DIR", str(DEFAULT_DATA_DIR)))


def _get_export_path() -> Path:
    return Path(os.environ.get("LEAD_SCORER_EXPORT_PATH", str(DEFAULT_EXPORT_PATH)))


def _get_cors_origins() -> list[str]:
    raw = os.environ.get(
        "LEAD_SCORER_CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class Settings:
    def __init__(self) -> None:
        self.data_dir = _get_data_dir()
        self.export_path = _get_export_path()
        self.cors_origins = _get_cors_origins()


settings = Settings()
