"""Requirement "Indicadores agregados do funil"."""

from __future__ import annotations

from typing import Optional

import pandas as pd
from deps import get_app_state, get_as_of
from fastapi import APIRouter, Depends, Query
from query import DealFilters, apply_open_filters, apply_org_filters, validar_confianca, validar_estados
from schemas import KpisOut
from state import AppState

router = APIRouter(tags=["indicadores"])


@router.get("/kpis", response_model=KpisOut)
def get_kpis(
    estado: Optional[list[str]] = Query(default=None),
    sales_agent: Optional[str] = None,
    manager: Optional[str] = None,
    regional_office: Optional[str] = None,
    product: Optional[str] = None,
    confianca: Optional[str] = None,
    idade_min: Optional[float] = None,
    idade_max: Optional[float] = None,
    as_of: Optional[pd.Timestamp] = Depends(get_as_of),
    app_state: AppState = Depends(get_app_state),
):
    estados = validar_estados(estado)
    confianca = validar_confianca(confianca)

    filters = DealFilters(
        estados=estados,
        sales_agent=sales_agent,
        manager=manager,
        regional_office=regional_office,
        product=product,
        confianca=confianca,
        idade_min=idade_min,
        idade_max=idade_max,
    )

    # Indicadores históricos (receita ganha, maior negócio fechado): só
    # filtros de organização/produto — ESTADO, CONFIANÇA e idade não se
    # aplicam a negócios já fechados (design.md, decisão 3).
    pipeline_org = apply_org_filters(app_state.dataset.pipeline, filters)
    won = pipeline_org[pipeline_org["deal_stage"] == "Won"]

    # Indicadores do funil aberto: todos os filtros.
    scored = app_state.scored_as_of(as_of)
    aberto = apply_open_filters(scored, filters)

    datas = pd.concat([pipeline_org["engage_date"].dropna(), pipeline_org["close_date"].dropna()])
    data_inicio = datas.min() if not datas.empty else None
    data_fim = datas.max() if not datas.empty else None

    idade_maxima = aberto["age_days"].max() if not aberto.empty else None
    idade_maxima = None if idade_maxima is None or pd.isna(idade_maxima) else float(idade_maxima)

    return KpisOut(
        total_oportunidades=int(len(aberto)),
        receita_ganha=float(won["close_value"].sum()),
        valor_esperado_aberto=float(aberto["prioridade"].sum()),
        total_desistir=int((aberto["estado"] == "desistir").sum()),
        maior_negocio_fechado=float(won["close_value"].max()) if not won.empty else 0.0,
        data_inicio=str(data_inicio.date()) if data_inicio is not None else "",
        data_fim=str(data_fim.date()) if data_fim is not None else "",
        idade_maxima_aberta=idade_maxima,
    )
