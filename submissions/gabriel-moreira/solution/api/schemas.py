"""Modelos Pydantic de request/response da API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class IdentitiesOut(BaseModel):
    sales_agents: list[str]
    supervisors: list[str]
    managers: list[str]


class IdentifyIn(BaseModel):
    name: str = Field(..., min_length=1)


class TokenOut(BaseModel):
    token: str
    role: str
    identity: str


class OportunidadeOut(BaseModel):
    opportunity_id: str
    sales_agent: str
    manager: Optional[str] = None
    regional_office: Optional[str] = None
    product: str
    account: Optional[str] = None
    sector: Optional[str] = None
    porte: Optional[str] = None
    deal_stage: str
    age_days: Optional[float] = None
    p_hat: float
    valor: float
    urgencia: float
    prioridade: float
    score: float
    confianca: str
    razao_confianca: str
    estado: str
    estado_label: str
    plano_de_acao: str


class KpisOut(BaseModel):
    total_oportunidades: int
    receita_ganha: float
    valor_esperado_aberto: float
    total_desistir: int
    maior_negocio_fechado: float
    data_inicio: str
    data_fim: str
    idade_maxima_aberta: Optional[float] = None
    identidade: str
    papel: str


class RollupLinhaOut(BaseModel):
    chave: str
    nivel: str  # "sales_agent" | "supervisor" | "regional_office"
    n_abertas: int
    valor_esperado: float
    por_estado: dict[str, int]


class ProdutoEsforcoOut(BaseModel):
    product: str
    n_oportunidades: int
    participacao_receita_historica: float


class RollupOut(BaseModel):
    linhas: list[RollupLinhaOut]
    esforco_por_produto: list[ProdutoEsforcoOut]


class ScoreAvulsaIn(BaseModel):
    product: str
    age_days: Optional[float] = Field(default=None, ge=0)
    porte: Optional[str] = None


class ScoreAvulsaOut(BaseModel):
    product: str
    porte: Optional[str] = None
    age_days: Optional[float] = None
    p_hat: float
    valor: float
    urgencia: float
    prioridade: float
    score: float
    confianca: str
    razao_confianca: str
    estado: str
    estado_label: str
    plano_de_acao: str
