"""Requirement "Rollup de gestão" — acessível a qualquer cliente."""

from __future__ import annotations

from typing import Optional

import pandas as pd
from deps import get_app_state, get_as_of
from fastapi import APIRouter, Depends
from query import DealFilters, apply_org_filters
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
    sales_agent: Optional[str] = None,
    manager: Optional[str] = None,
    regional_office: Optional[str] = None,
    product: Optional[str] = None,
    as_of: Optional[pd.Timestamp] = Depends(get_as_of),
    app_state: AppState = Depends(get_app_state),
):
    filters = DealFilters(
        sales_agent=sales_agent,
        manager=manager,
        regional_office=regional_office,
        product=product,
    )

    scored = apply_org_filters(app_state.scored_as_of(as_of), filters)

    linhas = _linhas_por_nivel(scored, "sales_agent", "sales_agent")
    linhas += _linhas_por_nivel(scored, "manager", "manager")
    linhas += _linhas_por_nivel(scored, "regional_office", "regional_office")

    pipeline_org = apply_org_filters(app_state.dataset.pipeline, filters)
    receita_total = float(
        pipeline_org.loc[pipeline_org["deal_stage"] == "Won", "close_value"].sum()
    )
    esforco: list[ProdutoEsforcoOut] = []
    for product_key, sub in scored.groupby("product"):
        receita_produto = float(
            pipeline_org.loc[
                (pipeline_org["deal_stage"] == "Won") & (pipeline_org["product"] == product_key),
                "close_value",
            ].sum()
        )
        participacao = receita_produto / receita_total if receita_total else 0.0
        esforco.append(
            ProdutoEsforcoOut(
                product=product_key,
                n_oportunidades=int(len(sub)),
                participacao_receita_historica=round(participacao, 4),
            )
        )

    return RollupOut(linhas=linhas, esforco_por_produto=esforco)
