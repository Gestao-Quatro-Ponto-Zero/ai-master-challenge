"""Requirements "Análise de carga e sobrecarga por escritório" e
"Listagem de oportunidades de vendedores sobrecarregados" (pipeline-api
spec)."""

from __future__ import annotations

import math
from typing import Optional

import pandas as pd
from deps import get_app_state, get_as_of
from fastapi import APIRouter, Depends, Query
from fit_view import fit_para_vendedor, sugestao_para_oportunidade
from schemas import (
    CargaEnvelopeOut,
    CargaEscritorioOut,
    CargaEstadoOut,
    CargaVendedorOut,
    OportunidadeSobrecarregadaOut,
    SobrecarregadosEnvelopeOut,
)
from scoring.carga import CARGA_ESTADOS
from serialize import clean_value
from state import AppState

router = APIRouter(tags=["carga"])


@router.get("/carga", response_model=CargaEnvelopeOut)
def get_carga(
    regional_office: Optional[str] = None,
    estado: Optional[str] = None,
    as_of: Optional[pd.Timestamp] = Depends(get_as_of),
    app_state: AppState = Depends(get_app_state),
):
    carga = app_state.carga_as_of(as_of)
    if regional_office is not None:
        carga = [c for c in carga if c.regional_office == regional_office]
    if estado is not None:
        carga = [c for c in carga if c.estado == estado]

    por_escritorio: dict[str, dict[str, list]] = {}
    medias: dict[tuple[str, str], float] = {}
    for item in carga:
        por_escritorio.setdefault(item.regional_office, {}).setdefault(item.estado, []).append(item)
        medias[(item.regional_office, item.estado)] = item.media_escritorio

    escritorios = []
    for office in sorted(por_escritorio):
        estados_out = []
        for estado_key in CARGA_ESTADOS:
            itens = por_escritorio[office].get(estado_key)
            if not itens:
                continue
            vendedores = sorted(
                (
                    CargaVendedorOut(
                        sales_agent=i.sales_agent, contagem=i.contagem, razao=i.razao, sobrecarregado=i.sobrecarregado
                    )
                    for i in itens
                ),
                key=lambda v: v.sales_agent,
            )
            estados_out.append(
                CargaEstadoOut(
                    estado=estado_key,
                    media_escritorio=medias[(office, estado_key)],
                    vendedores=vendedores,
                )
            )
        escritorios.append(CargaEscritorioOut(regional_office=office, estados=estados_out))

    return CargaEnvelopeOut(escritorios=escritorios)


@router.get("/deals/sobrecarregados", response_model=SobrecarregadosEnvelopeOut)
def list_sobrecarregados(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    as_of: Optional[pd.Timestamp] = Depends(get_as_of),
    app_state: AppState = Depends(get_app_state),
):
    scored = app_state.scored_com_carga_as_of(as_of)
    carga_index = app_state.carga_index_as_of(as_of)

    sobrecarregadas = scored[scored["sobrecarregado"]].sort_values(
        ["regional_office", "sales_agent", "opportunity_id"], kind="mergesort"
    )

    total = len(sobrecarregadas)
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    pagina = sobrecarregadas.iloc[start : start + page_size]

    items = []
    for _, row in pagina.iterrows():
        item = carga_index[(row["sales_agent"], row["estado"])]
        sector = clean_value(row.get("sector"))
        fit_produto_out, fit_setor_out = fit_para_vendedor(
            app_state.fit_ctx, row["sales_agent"], row["product"], sector
        )
        sugestao = sugestao_para_oportunidade(
            app_state.fit_ctx,
            carga_index,
            row["sales_agent"],
            row.get("regional_office"),
            row["estado"],
            row["product"],
            sector,
        )
        items.append(
            OportunidadeSobrecarregadaOut(
                opportunity_id=row["opportunity_id"],
                sales_agent=row["sales_agent"],
                regional_office=clean_value(row.get("regional_office")),
                product=row["product"],
                account=clean_value(row.get("account")),
                sector=sector,
                estado=row["estado"],
                contagem=item.contagem,
                media_escritorio=item.media_escritorio,
                razao=item.razao,
                fit_produto=fit_produto_out,
                fit_setor=fit_setor_out,
                sugestao=sugestao,
            )
        )

    return SobrecarregadosEnvelopeOut(
        items=items, total=total, page=page, page_size=page_size, total_pages=total_pages
    )
