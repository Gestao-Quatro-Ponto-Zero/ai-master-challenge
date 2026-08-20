"""Encolhimento hierárquico (empirical Bayes) para p̂_produto.

`compute_k` e `level_stats` são a fórmula genérica ("k = variância_esperada_
por_acaso / variância_em_excesso"), reutilizada por `validation/
shrinkage_check.py` para reproduzir o cálculo nos quatro níveis da
hierarquia (conta×produto, produto×setor, produto, global) e demonstrar o
colapso automático. O motor de scoring em si usa apenas o resultado
congelado (constants.K_PRODUTO) para o nível de produto — os níveis
conta×produto e produto×setor colapsam nos dados calibrados e não
contribuem, então nunca são lidos aqui.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from . import constants


@dataclass(frozen=True)
class GroupCounts:
    n: int
    wins: int

    @property
    def rate(self) -> float:
        return self.wins / self.n if self.n else 0.0


@dataclass(frozen=True)
class LevelStats:
    """Estatísticas de um nível da hierarquia de encolhimento."""

    n_groups: int
    var_observada: float
    var_esperada_por_acaso: float
    var_em_excesso: float
    k: float

    @property
    def colapsa(self) -> bool:
        return math.isinf(self.k)


def compute_k(var_esperada_por_acaso: float, var_em_excesso: float) -> float:
    """k = variância_esperada_por_acaso / variância_em_excesso.

    Colapsa para infinito quando a variância em excesso é <= 0 — o nível
    não carrega sinal além do que já é esperado por amostragem, e deve
    ceder inteiramente para o nível acima (sem intervenção manual).
    """
    if var_em_excesso <= 0:
        return math.inf
    return var_esperada_por_acaso / var_em_excesso


def level_stats(groups: dict[object, GroupCounts], p_prior: float) -> LevelStats:
    """Calcula variância observada, esperada por acaso e k para um nível.

    variância_esperada_por_acaso é a média, entre os grupos, da variância
    binomial individual p(1-p)/n_i — a estimativa correta de ruído amostral
    quando o tamanho dos grupos varia (evita subestimar o ruído em grupos
    pequenos ao usar apenas o tamanho médio). variância_observada é a
    variância populacional (ddof=0) das taxas brutas por grupo.
    """
    items = [g for g in groups.values() if g.n > 0]
    m = len(items)
    if m == 0:
        return LevelStats(0, 0.0, 0.0, 0.0, math.inf)

    rates = [g.rate for g in items]
    mean_rate = sum(rates) / m
    var_observada = sum((r - mean_rate) ** 2 for r in rates) / m

    var_esperada_por_acaso = sum(
        p_prior * (1 - p_prior) / g.n for g in items
    ) / m

    var_em_excesso = var_observada - var_esperada_por_acaso
    k = compute_k(var_esperada_por_acaso, var_em_excesso)

    return LevelStats(
        n_groups=m,
        var_observada=var_observada,
        var_esperada_por_acaso=var_esperada_por_acaso,
        var_em_excesso=var_em_excesso,
        k=k,
    )


def product_group_counts(closed: pd.DataFrame) -> dict[str, GroupCounts]:
    """Conta n/vitórias por produto sobre os negócios fechados (Won/Lost)."""
    groups: dict[str, GroupCounts] = {}
    for product, sub in closed.groupby("product"):
        n = len(sub)
        wins = int((sub["deal_stage"] == "Won").sum())
        groups[product] = GroupCounts(n=n, wins=wins)
    return groups


def product_sector_group_counts(closed: pd.DataFrame) -> dict[tuple[str, str], GroupCounts]:
    with_sector = closed.dropna(subset=["sector"])
    groups: dict[tuple[str, str], GroupCounts] = {}
    for (product, sector), sub in with_sector.groupby(["product", "sector"]):
        n = len(sub)
        wins = int((sub["deal_stage"] == "Won").sum())
        groups[(product, sector)] = GroupCounts(n=n, wins=wins)
    return groups


def account_product_group_counts(closed: pd.DataFrame) -> dict[tuple[str, str], GroupCounts]:
    with_account = closed.dropna(subset=["account"])
    groups: dict[tuple[str, str], GroupCounts] = {}
    for (account, product), sub in with_account.groupby(["account", "product"]):
        n = len(sub)
        wins = int((sub["deal_stage"] == "Won").sum())
        groups[(account, product)] = GroupCounts(n=n, wins=wins)
    return groups


def p_hat_produto(
    product: str,
    product_counts: dict[str, GroupCounts],
    global_win_rate: float = constants.GLOBAL_WIN_RATE,
    k: float = constants.K_PRODUTO,
) -> float:
    """p̂_produto = (n*taxa_produto + k*taxa_global) / (n + k).

    Produto sem negócios fechados na base (nunca deveria acontecer com o
    catálogo de 7 produtos, mas defensivo para pontuação avulsa de produto
    fora do histórico) encolhe inteiramente para a taxa global.
    """
    counts = product_counts.get(product)
    if counts is None or counts.n == 0:
        return global_win_rate
    return (counts.n * counts.rate + k * global_win_rate) / (counts.n + k)
