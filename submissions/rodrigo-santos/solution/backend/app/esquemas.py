"""
Formato das respostas da API (validado e documentado automaticamente em /docs).
"""

from pydantic import BaseModel, Field


class DealResumo(BaseModel):
    """Dados de um negócio exibidos no quadro/lista do pipeline."""

    id: str
    etapa: str = Field(description="Prospecting ou Engaging")
    situacao: str = Field(description="ativo, prospeccao ou parado")
    vendedor: str
    manager: str
    escritorio: str
    conta: str
    conta_informada: bool
    setor: str | None
    produto: str
    valor: float = Field(description="Preço de tabela do produto (US$)")
    chance: float = Field(description="Chance de fechar usada no valor esperado (0 a 1)")
    valor_esperado: float = Field(description="chance × valor (US$)")
    dias_aberto: int | None = Field(description="Dias desde o início da negociação")
    score: int = Field(description="Prioridade de 0 a 100")
    prioridade: str = Field(description="Alta, Média ou Baixa")
    parado: bool = Field(description="Aberto há mais tempo que qualquer negócio do histórico")
    motivo_principal: str = Field(description="Frase curta com o que mais explica o score")


class ParteScore(BaseModel):
    """Pontos que uma parte deu ao negócio. A soma dos pontos de todas as partes é o score."""

    chave: str = Field(description="situacao, valor ou reta_final")
    nome: str
    pontos: int
    maximo: int = Field(description="Máximo de pontos que a parte pode dar")
    explicacao: str


class Motivo(BaseModel):
    texto: str
    tipo: str = Field(description="positivo, negativo ou neutro")


class DealDetalhe(DealResumo):
    """Negócio com a explicação completa do score."""

    partes: list[ParteScore]
    motivos: list[Motivo]
    sugestao: str


class ListaDeals(BaseModel):
    total: int
    deals: list[DealResumo]


class Resumo(BaseModel):
    """Números do topo da tela (respeitando os filtros)."""

    total_abertos: int
    qtd_prioridade_alta: int
    qtd_ativos: int = Field(description="Em negociação e dentro do prazo histórico")
    qtd_parados: int
    valor_esperado_total: float


class RegrasPontuacao(BaseModel):
    """Regras atuais do score, para explicar a lógica ao vendedor."""

    pontos_maximos: dict[str, int] = Field(description="Pontos máximos por parte (somam 100)")
    pontos_prospeccao: int
    limite_alta: int
    limite_media: int
    taxa_vitoria_geral: float
    ciclo_mediano_dias: int
    limite_dias: int
    preco_minimo: float
    preco_maximo: float


class PrioridadeValidada(BaseModel):
    prioridade: str
    negocios: int
    taxa_vitoria: float
    receita_media: float


class AtributoTestado(BaseModel):
    atributo: str
    auc_medio: float = Field(description="0,5 = sorteio; 1,0 = acerta sempre")


class Validacao(BaseModel):
    """Resultado do backtest com o histórico (ver app/servicos/validacao.py)."""

    datas_corte: list[str]
    parados: int
    parados_fechados_depois: int
    por_prioridade: list[PrioridadeValidada]
    atributos: list[AtributoTestado]


class OpcoesFiltro(BaseModel):
    """Valores disponíveis para os filtros da tela."""

    vendedores: list[str]
    managers: list[str]
    escritorios: list[str]
    produtos: list[str]
    prioridades: list[str]
