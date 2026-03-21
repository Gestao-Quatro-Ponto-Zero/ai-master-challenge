"""Fonte de dados da camada HTTP: dataset oficial (CSV) vs snapshot demo (JSON).

CRP-REAL-01: modo padrão `real_dataset` para o produto principal; `demo_dataset` apenas
para testes determinísticos e desenvolvimento controlado.

CRP-REAL-02: modo real delegado ao pipeline em `src/serving/opportunity_pipeline.py`.
"""

from __future__ import annotations

import json
import os
import pathlib
from typing import Any

from src.serving.opportunity_pipeline import (
    build_serving_opportunities,
    serving_opportunities_to_api_rows,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEMO_OPPORTUNITIES_PATH = ROOT / "data" / "demo-opportunities.json"

MODE_REAL = "real_dataset"
MODE_DEMO = "demo_dataset"

ENV_DATA_SOURCE_MODE = "LEAD_SCORER_DATA_SOURCE_MODE"


def get_data_source_mode() -> str:
    """Retorna modo de fonte para serving HTTP (lido do ambiente a cada chamada)."""
    raw = (os.environ.get(ENV_DATA_SOURCE_MODE) or MODE_REAL).strip().lower()
    if raw == MODE_DEMO:
        return MODE_DEMO
    return MODE_REAL


def load_opportunity_rows_for_serving() -> list[dict[str, Any]]:
    """Linhas para `src.api.app`: id, title, seller, manager, region, deal_stage, amount."""
    if get_data_source_mode() == MODE_DEMO:
        return json.loads(DEMO_OPPORTUNITIES_PATH.read_text(encoding="utf-8"))
    ops = build_serving_opportunities()
    return serving_opportunities_to_api_rows(ops)
