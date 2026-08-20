"""Requirements "Listagem de oportunidades por estado" e "Filtros de listagem"."""

from __future__ import annotations

from typing import Optional

import pandas as pd
from auth.scope import Scope, resolve_scoped_agents
from deps import get_app_state, get_as_of, get_scope
from fastapi import APIRouter, Depends, HTTPException
from scoring import constants
from serialize import df_to_records
from state import AppState

router = APIRouter(tags=["oportunidades"])


@router.get("/deals")
def list_deals(
    estado: Optional[str] = None,
    sales_agent: Optional[str] = None,
    manager: Optional[str] = None,
    regional_office: Optional[str] = None,
    product: Optional[str] = None,
    confianca: Optional[str] = None,
    idade_min: Optional[float] = None,
    idade_max: Optional[float] = None,
    as_of: Optional[pd.Timestamp] = Depends(get_as_of),
    scope: Scope = Depends(get_scope),
    app_state: AppState = Depends(get_app_state),
):
    if estado is not None and estado not in constants.ESTADOS:
        raise HTTPException(
            422, detail=f"estado inválido; valores válidos: {list(constants.ESTADOS)}"
        )
    if confianca is not None and confianca not in constants.CONFIANCA_NIVEIS:
        raise HTTPException(
            422,
            detail=f"confiança inválida; valores válidos: {list(constants.CONFIANCA_NIVEIS)}",
        )

    scoped_agents = resolve_scoped_agents(
        app_state.dataset, scope, sales_agent, manager, regional_office
    )

    df = app_state.scored_as_of(as_of)
    df = df[df["sales_agent"].isin(scoped_agents)]

    if estado is not None:
        df = df[df["estado"] == estado]
    if product is not None:
        df = df[df["product"] == product]
    if confianca is not None:
        df = df[df["confianca"] == confianca]
    if idade_min is not None:
        df = df[df["age_days"] >= idade_min]
    if idade_max is not None:
        df = df[df["age_days"] <= idade_max]

    df = df.sort_values("score", ascending=False)
    return df_to_records(df)
