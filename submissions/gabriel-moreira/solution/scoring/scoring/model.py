"""PRIORIDADE = p̂ x VALOR x URGÊNCIA — os três componentes e sua composição.

Este módulo implementa só a aritmética por oportunidade. `pipeline.py`
orquestra a aplicação em lote sobre o dataset carregado, e `reference.py`
usa as mesmas funções para calcular a distribuição de referência de SCORE.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field

from . import constants, curves, setor as setor_mod


@dataclass(frozen=True)
class ScoringContext:
    """Pré-calculado uma vez sobre os negócios FECHADOS: p̂_produto
    (encolhimento hierárquico), o contexto de `mult_setor` (encolhimento
    produto×setor) e os três insumos de SUPORTE de CONFIANÇA — idades de
    negócios ganhos (ordenadas, para busca binária), contagem de negócios
    fechados por produto e o lookup de célula produto×setor.
    """

    p_hat_by_product: dict[str, float]
    ages_won_ordenadas: list[float] = field(default_factory=list)
    product_closed_counts: dict[str, int] = field(default_factory=dict)
    setor_ctx: setor_mod.MultSetorContext | None = None

    def p_hat_produto(self, product: str) -> float:
        return self.p_hat_by_product.get(product, constants.GLOBAL_WIN_RATE_CALIBRACAO)

    def s_idade(self, age_days: float) -> float:
        """Fração saturada de negócios ganhos dentro de +/-SUPORTE_JANELA_IDADE_DIAS
        da idade informada — a evidência de precedente histórico para esta idade."""
        janela = constants.SUPORTE_JANELA_IDADE_DIAS
        lo = bisect.bisect_left(self.ages_won_ordenadas, age_days - janela)
        hi = bisect.bisect_right(self.ages_won_ordenadas, age_days + janela)
        n = hi - lo
        return min(1.0, n / constants.SUPORTE_SATURACAO_N)

    def s_produto(self, product: str) -> float:
        """Fração saturada de negócios fechados do produto — evidência de fundo."""
        n = self.product_closed_counts.get(product, 0)
        return min(1.0, n / constants.SUPORTE_SATURACAO_N)

    def s_celula(self, product: str, sector: str | None) -> float:
        """Fração saturada de negócios fechados de calibração na célula
        produto×setor — 0 quando o setor é desconhecido ou a célula não
        tem histórico."""
        if self.setor_ctx is None:
            return 0.0
        n = setor_mod.n_celula(self.setor_ctx, product, sector)
        return min(1.0, n / constants.SUPORTE_SATURACAO_N)

    def mult_setor(self, product: str, sector: str | None) -> float:
        """1,0 (neutro) quando o setor é desconhecido ou o contexto de
        setor ainda não foi construído — nunca inventa ajuste a partir de
        dado ausente."""
        if self.setor_ctx is None:
            return 1.0
        return setor_mod.mult_setor(self.setor_ctx, product, sector)

    def n_celula(self, product: str, sector: str | None) -> int:
        """Tamanho amostral (negócios fechados de calibração) da célula
        produto×setor — consumido pela frase de `mult_setor` em
        `explicacao.fatores_score`."""
        if self.setor_ctx is None:
            return 0
        return setor_mod.n_celula(self.setor_ctx, product, sector)


def p_hat(
    ctx: ScoringContext,
    product: str,
    stage: str,
    age_days: float | None,
    sector: str | None = None,
) -> float:
    """p̂ ajustado pela idade, conforme o estágio, com `mult_setor` aplicado
    por último sobre o resultado já composto.

    - Prospecting: p̂_produto sem ajuste de idade (sem `engage_date`).
    - Engaging, idade > 138: reverte ao prior global (censura).
    - Engaging, idade <= 138: p̂_produto ajustado por p_ganho(min(idade,120)).
    - Em todos os casos: multiplicado por `mult_setor(product, sector)` —
      1,0 (neutro) quando o setor é desconhecido.
    """
    produto_p_hat = ctx.p_hat_produto(product)

    if stage == "Prospecting":
        base = produto_p_hat
    else:
        if age_days is None:
            raise ValueError("age_days é obrigatório para oportunidades em Engaging")

        if age_days > constants.CENSURA_DIAS:
            base = constants.CENSURA_P_HAT
        else:
            # Normaliza pela taxa ORGÂNICA — p_ganho(0) foi calibrado sobre
            # os negócios fechados organicamente, é essa a base da curva,
            # não a taxa de calibração (que alimenta apenas p̂_produto).
            base = produto_p_hat * curves.p_ganho(age_days) / constants.GLOBAL_WIN_RATE_ORGANICO

    return base * ctx.mult_setor(product, sector)


def urgencia(stage: str, age_days: float | None) -> float:
    """URGÊNCIA = risco(idade), com os casos especiais de Prospecting/censura."""
    if stage == "Prospecting":
        return constants.PROSPECTING_URGENCIA

    if age_days is None:
        raise ValueError("age_days é obrigatório para oportunidades em Engaging")

    if age_days > constants.CENSURA_DIAS:
        return constants.CENSURA_URGENCIA

    return curves.risco(age_days)


def mult_porte(porte: str | None) -> float:
    if porte is None:
        return constants.MULT_PORTE_DESCONHECIDO
    return constants.MULT_PORTE.get(porte, constants.MULT_PORTE_DESCONHECIDO)


def preco_tabela(product: str) -> float:
    """Preço de tabela do produto, sem multiplicador de porte."""
    p = constants.PRECO_TABELA.get(product)
    if p is None:
        raise KeyError(f"produto fora do catálogo: {product!r}")
    return p


def valor(product: str, porte: str | None) -> float:
    """VALOR = preço_tabela(produto) x mult_porte(porte)."""
    preco = preco_tabela(product)
    return round(preco * mult_porte(porte), 2)


def prioridade(p_hat_value: float, valor_value: float, urgencia_value: float) -> float:
    """PRIORIDADE = p̂ x VALOR x URGÊNCIA, arredondada ao centavo."""
    return round(p_hat_value * valor_value * urgencia_value, 2)


@dataclass(frozen=True)
class Componentes:
    p_hat: float
    preco_tabela: float
    valor: float
    urgencia: float
    prioridade: float


def score_componentes(
    ctx: ScoringContext,
    product: str,
    stage: str,
    age_days: float | None,
    porte: str | None,
    sector: str | None = None,
) -> Componentes:
    """Calcula os três componentes e PRIORIDADE para uma oportunidade."""
    p = p_hat(ctx, product, stage, age_days, sector)
    pt = preco_tabela(product)
    v = valor(product, porte)
    u = urgencia(stage, age_days)
    return Componentes(p_hat=p, preco_tabela=pt, valor=v, urgencia=u, prioridade=prioridade(p, v, u))
