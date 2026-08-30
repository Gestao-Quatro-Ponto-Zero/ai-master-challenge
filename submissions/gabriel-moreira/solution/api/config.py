"""Configuração da API a partir de variáveis de ambiente, com padrões
seguros para desenvolvimento local."""

from __future__ import annotations

import os
from pathlib import Path

_HERE = Path(__file__).resolve()
_ROOT = _HERE.parents[2] if len(_HERE.parents) > 2 else _HERE.parent

DEFAULT_DATA_DIR = _ROOT / "data"
DEFAULT_EXPORT_PATH = _HERE.parent / "data" / "processed_pipeline.csv"
# Artefatos de análise vendedor x produto / vendedor x setor — mesmo local
# do deliverable histórico da submissão (pipeline-api spec, Requirement
# "Exportação da análise de carga e fit"), regravados a cada carga.
DEFAULT_ANALYSIS_BY_PRODUCT_PATH = _ROOT / "analysis_by_product_detailed.csv"
DEFAULT_ANALYSIS_BY_SECTOR_PATH = _ROOT / "analysis_by_sector_detailed.csv"


def _get_data_dir() -> Path:
    return Path(os.environ.get("LEAD_SCORER_DATA_DIR", str(DEFAULT_DATA_DIR)))


def _get_export_path() -> Path:
    return Path(os.environ.get("LEAD_SCORER_EXPORT_PATH", str(DEFAULT_EXPORT_PATH)))


def _get_analysis_by_product_path() -> Path:
    return Path(
        os.environ.get("LEAD_SCORER_ANALYSIS_BY_PRODUCT_PATH", str(DEFAULT_ANALYSIS_BY_PRODUCT_PATH))
    )


def _get_analysis_by_sector_path() -> Path:
    return Path(
        os.environ.get("LEAD_SCORER_ANALYSIS_BY_SECTOR_PATH", str(DEFAULT_ANALYSIS_BY_SECTOR_PATH))
    )


def _get_cors_origins() -> list[str]:
    raw = os.environ.get(
        "LEAD_SCORER_CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class Settings:
    def __init__(self) -> None:
        self.data_dir = _get_data_dir()
        self.export_path = _get_export_path()
        self.analysis_by_product_path = _get_analysis_by_product_path()
        self.analysis_by_sector_path = _get_analysis_by_sector_path()
        self.cors_origins = _get_cors_origins()


settings = Settings()
