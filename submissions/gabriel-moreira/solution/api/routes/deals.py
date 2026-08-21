"""Requirements "Listagem de oportunidades por estado", "Filtros de
listagem", "Detalhe de uma oportunidade" e "Opções de filtro"."""

from __future__ import annotations

from typing import Optional

import pandas as pd
from deps import get_app_state, get_as_of
from fastapi import APIRouter, Depends, HTTPException, Query
from query import (
    DealFilters,
    apply_open_filters,
    contagem_por_estado,
    contagem_sem_idade_excluidas,
    paginate,
    sort_df,
    validar_confianca,
    validar_estados,
    validar_order,
    validar_sort,
)
from serialize import clean_value, df_to_records
from schemas import (
    ContaOut,
    DealDetailOut,
    DealsEnvelopeOut,
    FilterOptionsOut,
    FiltroGerenteOut,
    FiltroVendedorOut,
    OportunidadeOut,
)
from scoring import constants
from scoring.pipeline import score_row
from state import AppState

router = APIRouter(tags=["oportunidades"])


@router.get("/deals", response_model=DealsEnvelopeOut)
def list_deals(
    estado: Optional[list[str]] = Query(default=None),
    sales_agent: Optional[str] = None,
    manager: Optional[str] = None,
    regional_office: Optional[str] = None,
    product: Optional[str] = None,
    confianca_min: Optional[float] = None,
    confianca_max: Optional[float] = None,
    idade_min: Optional[float] = None,
    idade_max: Optional[float] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    sort: str = Query(default="score"),
    order: str = Query(default="desc"),
    as_of: Optional[pd.Timestamp] = Depends(get_as_of),
    app_state: AppState = Depends(get_app_state),
):
    estados = validar_estados(estado)
    confianca_min = validar_confianca(confianca_min)
    confianca_max = validar_confianca(confianca_max)
    sort = validar_sort(sort)
    order = validar_order(order)

    filters = DealFilters(
        estados=estados,
        sales_agent=sales_agent,
        manager=manager,
        regional_office=regional_office,
        product=product,
        confianca_min=confianca_min,
        confianca_max=confianca_max,
        idade_min=idade_min,
        idade_max=idade_max,
    )

    df_aberto = app_state.scored_as_of(as_of)
    recorte = apply_open_filters(df_aberto, filters)
    recorte_ordenado = sort_df(recorte, sort, order)
    pagina = paginate(recorte_ordenado, page, page_size)

    return DealsEnvelopeOut(
        items=[OportunidadeOut(**row) for row in df_to_records(pagina.items)],
        total=pagina.total,
        page=pagina.page,
        page_size=pagina.page_size,
        total_pages=pagina.total_pages,
        contagem_por_estado=contagem_por_estado(df_aberto, filters),
        excluidas_idade_desconhecida=contagem_sem_idade_excluidas(df_aberto, filters),
    )


@router.get("/filter-options", response_model=FilterOptionsOut)
def get_filter_options(app_state: AppState = Depends(get_app_state)):
    df_aberto = app_state.default_scored

    vendedores_df = df_aberto[["sales_agent", "manager", "regional_office"]].drop_duplicates(
        subset="sales_agent"
    )
    vendedores = [
        FiltroVendedorOut(nome=row["sales_agent"], manager=row["manager"], regional_office=row["regional_office"])
        for row in df_to_records(vendedores_df.sort_values("sales_agent"))
    ]

    gerentes_df = df_aberto[["manager", "regional_office"]].dropna(subset=["manager"]).drop_duplicates(
        subset="manager"
    )
    gerentes = [
        FiltroGerenteOut(nome=row["manager"], regional_office=row["regional_office"])
        for row in df_to_records(gerentes_df.sort_values("manager"))
    ]

    escritorios = sorted(df_aberto["regional_office"].dropna().unique().tolist())
    produtos = sorted(df_aberto["product"].dropna().unique().tolist())

    idades_conhecidas = df_aberto["age_days"].dropna()
    idade_min = float(idades_conhecidas.min()) if not idades_conhecidas.empty else None
    idade_max = float(idades_conhecidas.max()) if not idades_conhecidas.empty else None

    return FilterOptionsOut(
        vendedores=vendedores,
        gerentes=gerentes,
        escritorios=escritorios,
        produtos=produtos,
        idade_min=idade_min,
        idade_max=idade_max,
    )


def _age_days(row: pd.Series, as_of: pd.Timestamp) -> Optional[float]:
    if row["deal_stage"] != "Engaging" or pd.isna(row["engage_date"]):
        return None
    return float((as_of - row["engage_date"]).days)


@router.get("/deals/{opportunity_id}", response_model=DealDetailOut)
def get_deal_detail(
    opportunity_id: str,
    as_of: Optional[pd.Timestamp] = Depends(get_as_of),
    app_state: AppState = Depends(get_app_state),
):
    pipeline = app_state.dataset.pipeline
    aberto = pipeline[pipeline["deal_stage"].isin(constants.DEAL_STAGES_ABERTOS)]
    matches = aberto[aberto["opportunity_id"] == opportunity_id]
    if matches.empty:
        raise HTTPException(404, detail="oportunidade não encontrada no funil aberto")
    row = matches.iloc[0]

    resolved_as_of = as_of if as_of is not None else app_state.default_as_of
    age_days = _age_days(row, resolved_as_of)
    has_account = bool(row.get("account")) and not pd.isna(row.get("account"))
    porte = constants.classificar_porte(row.get("employees"))
    has_sector = has_account and not pd.isna(row.get("sector"))
    has_team = not pd.isna(row.get("manager"))

    result = score_row(
        app_state.ctx,
        app_state.ref,
        app_state.ages_won_ordenadas,
        product=row["product"],
        stage=row["deal_stage"],
        age_days=age_days,
        has_account=has_account,
        porte=porte,
        has_sector=has_sector,
        has_team=has_team,
    )

    conta = ContaOut(
        vinculada=has_account,
        sector=clean_value(row.get("sector")) if has_account else None,
        porte=porte,
        revenue=float(row["revenue"]) if has_account and not pd.isna(row.get("revenue")) else None,
        employees=float(row["employees"]) if has_account and not pd.isna(row.get("employees")) else None,
        year_established=int(row["year_established"])
        if has_account and not pd.isna(row.get("year_established"))
        else None,
        office_location=clean_value(row.get("office_location")) if has_account else None,
    )

    return DealDetailOut(
        opportunity_id=row["opportunity_id"],
        sales_agent=row["sales_agent"],
        manager=clean_value(row.get("manager")),
        regional_office=clean_value(row.get("regional_office")),
        product=row["product"],
        account=clean_value(row.get("account")) if has_account else None,
        sector=clean_value(row.get("sector")) if has_account else None,
        porte=porte,
        deal_stage=row["deal_stage"],
        age_days=age_days,
        conta=conta,
        **result,
    )
