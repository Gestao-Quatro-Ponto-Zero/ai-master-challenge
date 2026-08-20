"""Requirements "Download do dataset processado" e "Exportação de
identificadores filtrados" — ambos abertos a qualquer cliente."""

from __future__ import annotations

import io
from typing import Optional

import pandas as pd
from deps import get_app_state, get_as_of
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse, StreamingResponse
from query import DealFilters, apply_open_filters, validar_confianca, validar_estados
from state import AppState

router = APIRouter(tags=["exportação"])


@router.get("/export/csv")
def download_processed_dataset(app_state: AppState = Depends(get_app_state)):
    return FileResponse(
        app_state.settings.export_path,
        media_type="text/csv",
        filename="pipeline_processado.csv",
    )


@router.get("/export/deal-ids")
def export_filtered_deal_ids(
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
    """Identificadores do recorte filtrado inteiro, sem paginação — usado
    pela exportação em massa da interface, que não pode ficar limitada à
    página carregada."""
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

    recorte = apply_open_filters(app_state.scored_as_of(as_of), filters)

    buffer = io.StringIO()
    recorte[["opportunity_id"]].to_csv(buffer, index=False)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=oportunidades_filtradas.csv"},
    )
