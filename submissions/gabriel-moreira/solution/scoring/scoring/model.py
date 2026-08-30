"""PRIORIDADE = p̂ x VALOR x URGÊNCIA — os três componentes e sua composição.

Este módulo implementa só a aritmética por oportunidade. `pipeline.py`
orquestra a aplicação em lote sobre o dataset carregado, e `reference.py`
usa as mesmas funções para calcular a distribuição de referência de SCORE.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field

from . import constants, curves


@dataclass(frozen=True)
class ScoringContext:
    """Pré-calculado uma vez sobre os negócios FECHADOS: p̂_produto
    (encolhimento hierárquico) e os dois insumos de SUPORTE de CONFIANÇA —
    idades de negócios ganhos (ordenadas, para busca binária) e contagem
    de negócios fechados por produto.

    Setor não entra aqui: nem em p̂ (o nível produto×setor colapsa e a
    validação cruzada o rejeita — ver `constants.py`), nem em suporte.
    """

    p_hat_by_product: dict[str, float]
    ages_won_ordenadas: list[float] = field(default_factory=list)
    product_closed_counts: dict[str, int] = field(default_factory=dict)

    def p_hat_produto(self, product: str) -> float:
        return self.p_hat_by_product.get(product, constants.GLOBAL_WIN_RATE)

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


def p_hat(
    ctx: ScoringContext,
    product: str,
    stage: str,
    age_days: float | None,
) -> float:
    """p̂ ajustado pela idade, conforme o estágio.

    - Prospecting: p̂_produto sem ajuste de idade (sem `engage_date`).
    - Engaging, idade > 138: reverte ao prior global (censura).
    - Engaging, idade <= 138: p̂_produto ajustado por p_ganho(min(idade,120)).

    Produto e idade são os únicos insumos: setor foi testado e removido
    (ver `constants.py`).
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
            # Normaliza por GLOBAL_WIN_RATE porque p_ganho(0) é essa mesma
            # taxa: a curva diz quanto a idade desloca a chance a partir da
            # base, então dividir devolve um multiplicador centrado em 1,0.
            base = produto_p_hat * curves.p_ganho(age_days) / constants.GLOBAL_WIN_RATE

    return base


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
) -> Componentes:
    """Calcula os três componentes e PRIORIDADE para uma oportunidade."""
    p = p_hat(ctx, product, stage, age_days)
    pt = preco_tabela(product)
    v = valor(product, porte)
    u = urgencia(stage, age_days)
    return Componentes(p_hat=p, preco_tabela=pt, valor=v, urgencia=u, prioridade=prioridade(p, v, u))
