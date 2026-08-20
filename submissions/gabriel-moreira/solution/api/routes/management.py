"""Requirement "Rollup de gestão" — restrito a Supervisor/Manager."""

from __future__ import annotations

from typing import Optional

import pandas as pd
from auth.scope import Scope
from deps import get_app_state, get_as_of, get_scope
from fastapi import APIRouter, Depends, HTTPException
from schemas import ProdutoEsforcoOut, RollupLinhaOut, RollupOut
from scoring import constants
from state import AppState

router = APIRouter(tags=["gestão"])


def _por_estado(sub: pd.DataFrame) -> dict[str, int]:
    counts = sub["estado"].value_counts()
    return {estado_key: int(counts.get(estado_key, 0)) for estado_key in constants.ESTADOS}


def _linhas_por_nivel(scored: pd.DataFrame, coluna: str, nivel: str) -> list[RollupLinhaOut]:
    linhas: list[RollupLinhaOut] = []
    for chave, sub in scored.groupby(coluna):
        linhas.append(
            RollupLinhaOut(
                chave=str(chave),
                nivel=nivel,
                n_abertas=int(len(sub)),
                valor_esperado=float(sub["prioridade"].sum()),
                por_estado=_por_estado(sub),
            )
        )
    return linhas


@router.get("/rollup", response_model=RollupOut)
def get_rollup(
    as_of: Optional[pd.Timestamp] = Depends(get_as_of),
    scope: Scope = Depends(get_scope),
    app_state: AppState = Depends(get_app_state),
):
    if scope.role == "sales_agent":
        raise HTTPException(
            403, detail="rollup comparativo não está disponível para Sales Agent"
        )

    scored = app_state.scored_as_of(as_of)
    scored_in_scope = scored[scored["sales_agent"].isin(scope.sales_agents)]

    linhas = _linhas_por_nivel(scored_in_scope, "sales_agent", "sales_agent")
    if scope.role == "manager":
        linhas += _linhas_por_nivel(scored_in_scope, "manager", "supervisor")
        linhas += _linhas_por_nivel(scored_in_scope, "regional_office", "regional_office")

    receita_total = float(
        app_state.dataset.pipeline.loc[
            app_state.dataset.pipeline["deal_stage"] == "Won", "close_value"
        ].sum()
    )
    esforco: list[ProdutoEsforcoOut] = []
    for product, sub in scored_in_scope.groupby("product"):
        receita_produto = float(
            app_state.dataset.pipeline.loc[
                (app_state.dataset.pipeline["deal_stage"] == "Won")
                & (app_state.dataset.pipeline["product"] == product),
                "close_value",
            ].sum()
        )
        participacao = receita_produto / receita_total if receita_total else 0.0
        esforco.append(
            ProdutoEsforcoOut(
                product=product,
                n_oportunidades=int(len(sub)),
                participacao_receita_historica=round(participacao, 4),
            )
        )

    return RollupOut(linhas=linhas, esforco_por_produto=esforco)
