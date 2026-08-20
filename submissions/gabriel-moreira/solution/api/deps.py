"""Dependências FastAPI: estado da aplicação e data de referência opcional
— reutilizadas por toda rota de dados.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from fastapi import HTTPException, Request

from state import AppState


def get_app_state(request: Request) -> AppState:
    return request.app.state.app_state


def get_as_of(as_of: Optional[str] = None) -> Optional[pd.Timestamp]:
    if as_of is None:
        return None
    try:
        return pd.Timestamp(as_of)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="data de referência inválida") from None
