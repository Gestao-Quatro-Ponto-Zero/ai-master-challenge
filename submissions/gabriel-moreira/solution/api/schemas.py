"""Modelos Pydantic de request/response da API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


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
    confianca_label: str
    razao_confianca: str
    estado: str
    estado_label: str
    plano_de_acao: str


class DealsEnvelopeOut(BaseModel):
    items: list[OportunidadeOut]
    total: int
    page: int
    page_size: int
    total_pages: int
    contagem_por_estado: dict[str, int]
    excluidas_idade_desconhecida: int


class ContaOut(BaseModel):
    vinculada: bool
    sector: Optional[str] = None
    porte: Optional[str] = None
    revenue: Optional[float] = None
    employees: Optional[float] = None
    year_established: Optional[int] = None
    office_location: Optional[str] = None


class DealDetailOut(OportunidadeOut):
    conta: ContaOut
    plano_de_acao_passos: list[str]


class FiltroVendedorOut(BaseModel):
    nome: str
    manager: Optional[str] = None
    regional_office: Optional[str] = None


class FiltroGerenteOut(BaseModel):
    nome: str
    regional_office: Optional[str] = None


class FilterOptionsOut(BaseModel):
    vendedores: list[FiltroVendedorOut]
    gerentes: list[FiltroGerenteOut]
    escritorios: list[str]
    produtos: list[str]
    idade_min: Optional[float] = None
    idade_max: Optional[float] = None


class KpisOut(BaseModel):
    total_oportunidades: int
    receita_ganha: float
    valor_esperado_aberto: float
    total_desistir: int
    maior_negocio_fechado: float
    data_inicio: str
    data_fim: str
    idade_maxima_aberta: Optional[float] = None
    indicadores_historicos: list[str] = Field(
        default_factory=lambda: ["receita_ganha", "maior_negocio_fechado"]
    )


class RollupLinhaOut(BaseModel):
    chave: str
    nivel: str  # "sales_agent" | "manager" | "regional_office"
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
    confianca_label: str
    razao_confianca: str
    estado: str
    estado_label: str
    plano_de_acao: str
    plano_de_acao_passos: list[str]
