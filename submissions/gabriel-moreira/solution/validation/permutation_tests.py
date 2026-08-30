"""Testes de permutação por atributo firmográfico — Requirement "Testes de
permutação por atributo".

Compara a dispersão observada das taxas de ganho por categoria com a
dispersão sob rótulos embaralhados, semente fixa, para vendedor, produto,
setor e conta.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

SEED = 20260819
N_PERMUTATIONS = 2000


@dataclass(frozen=True)
class PermutationResult:
    atributo: str
    dispersao_observada: float
    dispersao_nula_media: float
    p_valor: float


def _dispersion(labels: np.ndarray, groups: np.ndarray) -> float:
    """Desvio-padrão (ponderado por n) das taxas de ganho por categoria."""
    df = pd.DataFrame({"won": labels, "group": groups})
    rates = df.groupby("group")["won"].mean()
    counts = df.groupby("group")["won"].size()
    weighted_mean = np.average(rates, weights=counts)
    return float(np.sqrt(np.average((rates - weighted_mean) ** 2, weights=counts)))


def _p_valor(null_dispersions: np.ndarray, observed: float) -> float:
    """p = (1 + #{nula >= observada}) / (B + 1) — correção add-one.

    `média(nula >= observada)` devolveria 0,000 quando nenhuma das B
    permutações alcança a dispersão real, e 0 é impossível como
    probabilidade: com B reamostragens não se distingue "nunca acontece" de
    "acontece menos de 1 vez em B". A correção add-one (Davison & Hinkley;
    Phipson & Smyth 2010) trata a amostra observada como uma das
    permutações possíveis e devolve um p sempre positivo, com piso
    1/(B+1) — o que este teste consegue afirmar, e nada além disso.
    """
    return float((1 + np.sum(null_dispersions >= observed)) / (len(null_dispersions) + 1))


def formata_p(p_valor: float, casas: int = 3) -> str:
    """Formata um p-valor sem nunca imprimir '0,000'.

    Arredondar 0,0005 para três casas produz '0.000', que é exatamente a
    leitura que a correção add-one existe para impedir: quem lê '0,000'
    entende "probabilidade zero", e o teste nunca afirmou isso. Abaixo do
    que as casas pedidas conseguem representar, devolve '<0,001'.
    """
    piso = 10 ** (-casas)
    return f"<{piso:.{casas}f}" if p_valor < piso else f"{p_valor:.{casas}f}"


def permutation_test(closed: pd.DataFrame, attribute: str, n_permutations: int = N_PERMUTATIONS) -> PermutationResult:
    subset = closed.dropna(subset=[attribute])
    labels = (subset["deal_stage"] == "Won").to_numpy(dtype=float)
    groups = subset[attribute].to_numpy()

    observed = _dispersion(labels, groups)

    rng = np.random.default_rng(SEED)
    null_dispersions = np.empty(n_permutations)
    for i in range(n_permutations):
        shuffled = rng.permutation(labels)
        null_dispersions[i] = _dispersion(shuffled, groups)

    p_valor = _p_valor(null_dispersions, observed)

    return PermutationResult(
        atributo=attribute,
        dispersao_observada=observed,
        dispersao_nula_media=float(null_dispersions.mean()),
        p_valor=p_valor,
    )


def run_all(closed: pd.DataFrame) -> list[PermutationResult]:
    """Task 6.3 — os quatro atributos candidatos: vendedor, produto, setor, conta."""
    attributes = [
        ("sales_agent", "vendedor"),
        ("product", "produto"),
        ("sector", "setor"),
        ("account", "conta"),
    ]
    results = []
    for col, _label in attributes:
        results.append(permutation_test(closed, col))
    return results
