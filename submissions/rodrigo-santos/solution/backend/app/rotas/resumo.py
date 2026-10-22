"""Rotas de apoio da tela: números do topo, filtros, regras e validação do score."""

from fastapi import APIRouter, Depends

from app.esquemas import OpcoesFiltro, RegrasPontuacao, Resumo, Validacao
from app.servicos.consultas import Filtros, montar_resumo, opcoes_filtro, resumir_validacao
from app.servicos.pontuacao import regras_pontuacao

roteador = APIRouter(prefix="/api", tags=["resumo"])


@roteador.get("/resumo", response_model=Resumo)
def obter_resumo(filtros: Filtros = Depends()):
    """Indicadores do recorte filtrado (mesmos filtros do pipeline)."""
    return montar_resumo(filtros)


@roteador.get("/filtros", response_model=OpcoesFiltro)
def obter_opcoes_filtro():
    """Valores possíveis para cada filtro da tela."""
    return opcoes_filtro()


@roteador.get("/regras", response_model=RegrasPontuacao)
def obter_regras():
    """Como o score é calculado (pesos, faixas de prioridade e prazos)."""
    return regras_pontuacao()


@roteador.get("/validacao", response_model=Validacao)
def obter_validacao():
    """Resultado do backtest: o score teria apontado os negócios certos no passado?"""
    return resumir_validacao()
