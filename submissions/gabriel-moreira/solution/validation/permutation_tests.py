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

    p_valor = float(np.mean(null_dispersions >= observed))

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
