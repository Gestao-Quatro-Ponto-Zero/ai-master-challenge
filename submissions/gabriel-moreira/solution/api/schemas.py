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
    preco_tabela: float
    valor: float
    urgencia: float
    score: float
    confianca: float
    completude: float
    suporte: float
    sem_precedente: bool
    razao_confianca: str
    estado: str
    estado_label: str
    plano_de_acao: str
    # Requirement "Sinalizador de sobrecarga na listagem de oportunidades"
    # — booleano só; o vendedor sugerido nunca aparece nesta listagem.
    sobrecarregado: bool


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


RESSALVA_FIT = (
    "Nesta base não se encontra afinidade vendedor×produto: a diferença observada "
    "entre vendedores não se distingue de acaso, e o que resta depois de descontar "
    "o desempenho geral de cada vendedor e a dificuldade de cada produto também não. "
    "É ausência de sinal, não prova de que a afinidade não exista — de todo modo, o "
    "fit ordena candidatos à redistribuição de carga e não mede mérito "
    "(testes de permutação, ver validation/)."
)


class FitOut(BaseModel):
    """Fit histórico do vendedor numa dimensão (produto ou setor).
    `disponivel=False` — nunca zero, nunca a média global, nunca o fit da
    outra dimensão — quando a informação de base (setor) é desconhecida."""

    disponivel: bool
    valor: Optional[float] = None
    n: Optional[int] = None


class SugestaoOut(BaseModel):
    """Sugestão de redistribuição — informativa; nada é reatribuído.
    `disponivel=False` quando o pool de elegíveis do escritório esgota."""

    disponivel: bool
    sales_agent: Optional[str] = None
    fit_produto: Optional[FitOut] = None
    fit_setor: Optional[FitOut] = None


class LimitacaoScoreOut(BaseModel):
    """Uma limitação metodológica que incide sobre o score DESTA
    oportunidade. `componentes` traz as chaves canônicas dos números
    afetados (`p_hat`/`valor`/`urgencia`/`score`/`confianca`), para que a
    interface marque o número em si; `impacto` diz o que muda nele —
    limitação sem impacto concreto vira decoração (Requirement
    "Limitações metodológicas do score da oportunidade").
    """

    id: str
    componentes: list[str]
    rotulo_curto: str
    titulo: str
    impacto: str


class DealDetailOut(OportunidadeOut):
    conta: ContaOut
    prioridade: float
    plano_de_acao_passos: list[str]
    score_fatores: list[str]
    # Requirement "Fit e sugestão no detalhe da oportunidade".
    fit_produto: FitOut
    fit_setor: FitOut
    ressalva_fit: str = RESSALVA_FIT
    # Só o que incide sobre esta oportunidade — uma lista que nunca muda
    # deixa de ser lida.
    limitacoes: list[LimitacaoScoreOut]
    sugestao: Optional[SugestaoOut] = None


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
    total_revisao_lote: int
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
    confianca_mediana: float


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
    preco_tabela: float
    valor: float
    urgencia: float
    prioridade: float
    score: float
    confianca: float
    completude: float
    suporte: float
    sem_precedente: bool
    razao_confianca: str
    estado: str
    estado_label: str
    plano_de_acao: str
    plano_de_acao_passos: list[str]
    score_fatores: list[str]


class CargaVendedorOut(BaseModel):
    sales_agent: str
    contagem: int
    razao: Optional[float] = None
    sobrecarregado: bool


class CargaEstadoOut(BaseModel):
    estado: str
    media_escritorio: float
    vendedores: list[CargaVendedorOut]


class CargaEscritorioOut(BaseModel):
    regional_office: str
    estados: list[CargaEstadoOut]


class CargaEnvelopeOut(BaseModel):
    escritorios: list[CargaEscritorioOut]


class OportunidadeSobrecarregadaOut(BaseModel):
    opportunity_id: str
    sales_agent: str
    regional_office: Optional[str] = None
    product: str
    account: Optional[str] = None
    sector: Optional[str] = None
    estado: str
    contagem: int
    media_escritorio: float
    razao: Optional[float] = None
    # Fit do vendedor ATUAL — para comparação lado a lado com `sugestao`
    # (pipeline-ui spec, Requirement "Aba de sobrecarga").
    fit_produto: FitOut
    fit_setor: FitOut
    sugestao: SugestaoOut


class SobrecarregadosEnvelopeOut(BaseModel):
    items: list[OportunidadeSobrecarregadaOut]
    total: int
    page: int
    page_size: int
    total_pages: int
