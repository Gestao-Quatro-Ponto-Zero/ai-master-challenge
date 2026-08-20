"""Requirement "Indicadores agregados do funil"."""

from __future__ import annotations

from typing import Optional

import pandas as pd
from auth.scope import Scope
from deps import get_app_state, get_as_of, get_scope
from fastapi import APIRouter, Depends
from schemas import KpisOut
from state import AppState

router = APIRouter(tags=["indicadores"])


@router.get("/kpis", response_model=KpisOut)
def get_kpis(
    as_of: Optional[pd.Timestamp] = Depends(get_as_of),
    scope: Scope = Depends(get_scope),
    app_state: AppState = Depends(get_app_state),
):
    pipeline = app_state.dataset.pipeline
    in_scope = pipeline[pipeline["sales_agent"].isin(scope.sales_agents)]
    won = in_scope[in_scope["deal_stage"] == "Won"]

    scored = app_state.scored_as_of(as_of)
    scored_in_scope = scored[scored["sales_agent"].isin(scope.sales_agents)]

    datas = pd.concat(
        [in_scope["engage_date"].dropna(), in_scope["close_date"].dropna()]
    )
    data_inicio = datas.min() if not datas.empty else None
    data_fim = datas.max() if not datas.empty else None

    idade_maxima = (
        scored_in_scope["age_days"].max() if not scored_in_scope.empty else None
    )
    idade_maxima = None if pd.isna(idade_maxima) else float(idade_maxima)

    return KpisOut(
        total_oportunidades=int(len(in_scope)),
        receita_ganha=float(won["close_value"].sum()),
        valor_esperado_aberto=float(scored_in_scope["prioridade"].sum()),
        total_desistir=int((scored_in_scope["estado"] == "desistir").sum()),
        maior_negocio_fechado=float(won["close_value"].max()) if not won.empty else 0.0,
        data_inicio=str(data_inicio.date()) if data_inicio is not None else "",
        data_fim=str(data_fim.date()) if data_fim is not None else "",
        idade_maxima_aberta=idade_maxima,
        identidade=scope.identity,
        papel=scope.role,
    )
