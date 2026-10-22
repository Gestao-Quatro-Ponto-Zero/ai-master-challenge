"""Rotas do pipeline: lista de deals abertos e detalhe de um deal."""

from fastapi import APIRouter, Depends, HTTPException

from app.esquemas import DealDetalhe, ListaDeals
from app.servicos.consultas import Filtros, detalhar_deal, listar_deals

roteador = APIRouter(prefix="/api", tags=["pipeline"])


@roteador.get("/pipeline", response_model=ListaDeals)
def obter_pipeline(filtros: Filtros = Depends()):
    """Deals abertos, do mais para o menos prioritário. Todos os filtros são opcionais."""
    deals = listar_deals(filtros)
    return {"total": len(deals), "deals": deals}


@roteador.get("/deals/{id_deal}", response_model=DealDetalhe)
def obter_deal(id_deal: str):
    """Detalhe de um deal aberto, com a explicação do score."""
    deal = detalhar_deal(id_deal)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal não encontrado ou já fechado")
    return deal
