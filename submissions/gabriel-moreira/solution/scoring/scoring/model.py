"""PRIORIDADE = p̂ x VALOR x URGÊNCIA — os três componentes e sua composição.

Este módulo implementa só a aritmética por oportunidade. `pipeline.py`
orquestra a aplicação em lote sobre o dataset carregado, e `reference.py`
usa as mesmas funções para calcular a distribuição de referência de SCORE.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import constants, curves


@dataclass(frozen=True)
class ScoringContext:
    """p̂_produto pré-calculado por produto (encolhimento hierárquico)."""

    p_hat_by_product: dict[str, float]

    def p_hat_produto(self, product: str) -> float:
        return self.p_hat_by_product.get(product, constants.GLOBAL_WIN_RATE)


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
    """
    produto_p_hat = ctx.p_hat_produto(product)

    if stage == "Prospecting":
        return produto_p_hat

    if age_days is None:
        raise ValueError("age_days é obrigatório para oportunidades em Engaging")

    if age_days > constants.CENSURA_DIAS:
        return constants.CENSURA_P_HAT

    return produto_p_hat * curves.p_ganho(age_days) / constants.GLOBAL_WIN_RATE


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


def valor(product: str, porte: str | None) -> float:
    """VALOR = preço_tabela(produto) x mult_porte(porte)."""
    preco = constants.PRECO_TABELA.get(product)
    if preco is None:
        raise KeyError(f"produto fora do catálogo: {product!r}")
    return round(preco * mult_porte(porte), 2)


def prioridade(p_hat_value: float, valor_value: float, urgencia_value: float) -> float:
    """PRIORIDADE = p̂ x VALOR x URGÊNCIA, arredondada ao centavo."""
    return round(p_hat_value * valor_value * urgencia_value, 2)


@dataclass(frozen=True)
class Componentes:
    p_hat: float
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
    v = valor(product, porte)
    u = urgencia(stage, age_days)
    return Componentes(p_hat=p, valor=v, urgencia=u, prioridade=prioridade(p, v, u))
