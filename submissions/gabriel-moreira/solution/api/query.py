"""Módulo de consulta compartilhado sobre o funil pontuado.

Aplica filtros (organização, produto, estado, confiança, idade), ordenação
com desempate por `opportunity_id` e paginação — usado por `/deals`,
`/kpis`, `/rollup` e a exportação de identificadores filtrados. Um só
lugar decide "quais linhas, em que ordem"; os endpoints só variam o que
fazem com o resultado (design.md, decisão 8).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import pandas as pd
from fastapi import HTTPException
from scoring import constants

SORT_CAMPOS: dict[str, str] = {
    "score": "score",
    "prioridade": "prioridade",
    "age_days": "age_days",
    "estado": "estado",
}
SORT_VALIDOS = ("score", "prioridade", "age_days", "estado")

# Ordem de urgência do ESTADO (constants.ESTADOS), não alfabética — "estado"
# ascendente começa em foco_urgente, o mais urgente.
_ESTADO_ORDEM: dict[str, int] = {estado: i for i, estado in enumerate(constants.ESTADOS)}
ORDER_VALIDOS = ("asc", "desc")


def validar_estados(estado: Optional[list[str]]) -> tuple[str, ...]:
    if not estado:
        return ()
    invalidos = [e for e in estado if e not in constants.ESTADOS]
    if invalidos:
        raise HTTPException(
            422, detail=f"estado inválido; valores válidos: {list(constants.ESTADOS)}"
        )
    return tuple(estado)


def validar_confianca(confianca: Optional[str]) -> Optional[str]:
    if confianca is not None and confianca not in constants.CONFIANCA_NIVEIS:
        raise HTTPException(
            422,
            detail=f"confiança inválida; valores válidos: {list(constants.CONFIANCA_NIVEIS)}",
        )
    return confianca


def validar_sort(sort: str) -> str:
    if sort not in SORT_VALIDOS:
        raise HTTPException(422, detail=f"sort inválido; valores válidos: {list(SORT_VALIDOS)}")
    return sort


def validar_order(order: str) -> str:
    if order not in ORDER_VALIDOS:
        raise HTTPException(422, detail=f"order inválido; valores válidos: {list(ORDER_VALIDOS)}")
    return order


@dataclass(frozen=True)
class DealFilters:
    estados: tuple[str, ...] = ()
    sales_agent: str | None = None
    manager: str | None = None
    regional_office: str | None = None
    product: str | None = None
    confianca: str | None = None
    idade_min: float | None = None
    idade_max: float | None = None

    @property
    def idade_ativo(self) -> bool:
        return self.idade_min is not None or self.idade_max is not None


def apply_org_filters(df: pd.DataFrame, filters: DealFilters) -> pd.DataFrame:
    """Vendedor, gerente, escritório e produto — comuns a qualquer consulta
    sobre o funil, aberto ou fechado."""
    if filters.sales_agent is not None:
        df = df[df["sales_agent"] == filters.sales_agent]
    if filters.manager is not None:
        df = df[df["manager"] == filters.manager]
    if filters.regional_office is not None:
        df = df[df["regional_office"] == filters.regional_office]
    if filters.product is not None:
        df = df[df["product"] == filters.product]
    return df


def _apply_idade_filter(df: pd.DataFrame, filters: DealFilters) -> pd.DataFrame:
    if not filters.idade_ativo:
        return df
    mask = df["age_days"].notna()
    if filters.idade_min is not None:
        mask &= df["age_days"] >= filters.idade_min
    if filters.idade_max is not None:
        mask &= df["age_days"] <= filters.idade_max
    return df[mask]


def apply_open_filters(
    df_aberto: pd.DataFrame, filters: DealFilters, *, include_estado: bool = True
) -> pd.DataFrame:
    """Filtros que só existem para o funil aberto: organização/produto,
    estado (opcional, omitido para calcular a contagem que ignora o
    próprio filtro), confiança e idade."""
    df = apply_org_filters(df_aberto, filters)
    if include_estado and filters.estados:
        df = df[df["estado"].isin(filters.estados)]
    if filters.confianca is not None:
        df = df[df["confianca"] == filters.confianca]
    df = _apply_idade_filter(df, filters)
    return df


def contagem_por_estado(df_aberto: pd.DataFrame, filters: DealFilters) -> dict[str, int]:
    """Contagem por ESTADO do recorte, ignorando o próprio filtro de estado."""
    sem_filtro_de_estado = apply_open_filters(df_aberto, filters, include_estado=False)
    counts = sem_filtro_de_estado["estado"].value_counts()
    return {estado_key: int(counts.get(estado_key, 0)) for estado_key in constants.ESTADOS}


def contagem_sem_idade_excluidas(df_aberto: pd.DataFrame, filters: DealFilters) -> int:
    """Quantas oportunidades sem idade conhecida (Prospecting) ficaram fora
    do recorte por causa do filtro de idade ativo — aplica os demais
    filtros (organização, estado, confiança), mas não o de idade."""
    if not filters.idade_ativo:
        return 0
    base = apply_org_filters(df_aberto, filters)
    if filters.estados:
        base = base[base["estado"].isin(filters.estados)]
    if filters.confianca is not None:
        base = base[base["confianca"] == filters.confianca]
    return int(base["age_days"].isna().sum())


def sort_df(df: pd.DataFrame, sort: str, order: str) -> pd.DataFrame:
    """Ordena por SCORE, PRIORIDADE, idade ou ESTADO, com desempate obrigatório
    por `opportunity_id` — sem ele, páginas sucessivas de um recorte com
    empates podem repetir ou pular oportunidades (design.md, decisão 8).
    ESTADO ordena pela urgência de `constants.ESTADOS` (foco_urgente primeiro
    em ordem ascendente), não alfabeticamente."""
    campo = SORT_CAMPOS.get(sort, "score")
    ascending = order == "asc"
    if campo == "estado":
        chave = df["estado"].map(_ESTADO_ORDEM)
        df = df.assign(_estado_ordem=chave)
        return df.sort_values(
            ["_estado_ordem", "opportunity_id"], ascending=[ascending, True], kind="mergesort"
        ).drop(columns="_estado_ordem")
    return df.sort_values(
        [campo, "opportunity_id"], ascending=[ascending, True], kind="mergesort"
    )


@dataclass(frozen=True)
class Pagina:
    items: pd.DataFrame
    total: int
    page: int
    page_size: int
    total_pages: int


def paginate(df_ordenado: pd.DataFrame, page: int, page_size: int) -> Pagina:
    total = len(df_ordenado)
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    end = start + page_size
    return Pagina(
        items=df_ordenado.iloc[start:end],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
