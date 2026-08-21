"""Serialização compartilhada de fit/sugestão — usada pelo detalhe da
oportunidade (`routes/deals.py`) e pela listagem de sobrecarregados
(`routes/carga.py`), para que os dois nunca divirjam na forma como
apresentam a mesma informação."""

from __future__ import annotations

from typing import Optional

from schemas import FitOut, SugestaoOut
from scoring.carga import CargaVendedorEstado
from scoring.fit import Candidato, FitContext, FitValue, fit_produto, fit_setor, suggest_candidate


def fit_out(fv: Optional[FitValue]) -> FitOut:
    if fv is None:
        return FitOut(disponivel=False)
    return FitOut(disponivel=True, valor=round(fv.valor, 4), n=fv.n)


def candidato_to_sugestao(candidato: Optional[Candidato]) -> SugestaoOut:
    if candidato is None:
        return SugestaoOut(disponivel=False)
    return SugestaoOut(
        disponivel=True,
        sales_agent=candidato.sales_agent,
        fit_produto=fit_out(candidato.fit_produto),
        fit_setor=fit_out(candidato.fit_setor),
    )


def fit_para_vendedor(fit_ctx: FitContext, sales_agent: str, product: str, sector: Optional[str]) -> tuple[FitOut, FitOut]:
    return fit_out(fit_produto(fit_ctx, sales_agent, product)), fit_out(fit_setor(fit_ctx, sales_agent, sector))


def sugestao_para_oportunidade(
    fit_ctx: FitContext,
    carga_index: dict[tuple[str, str], CargaVendedorEstado],
    sales_agent: str,
    regional_office: Optional[str],
    estado: str,
    product: str,
    sector: Optional[str],
) -> SugestaoOut:
    if regional_office is None:
        return SugestaoOut(disponivel=False)
    candidato = suggest_candidate(fit_ctx, carga_index, sales_agent, regional_office, estado, product, sector)
    return candidato_to_sugestao(candidato)
