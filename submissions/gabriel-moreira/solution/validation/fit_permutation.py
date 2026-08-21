"""Reprodução da ausência de sinal do fit por vendedor — Requirement
"Reprodução da ausência de sinal do fit por vendedor".

Teste de permutação (semente fixa) sobre a dispersão da taxa de vitória
por célula vendedor x produto (e vendedor x setor): embaralha os rótulos
de vendedor mantendo produto/setor fixos por linha — controla pelo mix de
produtos que cada vendedor efetivamente vende — e compara a dispersão
real com a dispersão sob rótulos aleatórios.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

SEED = 20260821
N_PERMUTATIONS = 2000


@dataclass(frozen=True)
class FitPermutationResult:
    dimensao: str
    n_celulas: int
    dispersao_observada: float
    dispersao_nula_media: float
    p_valor: float

    @property
    def distinguivel_de_acaso(self) -> bool:
        return self.p_valor < 0.05


def _dispersion(vendor_codes: np.ndarray, dim_codes: np.ndarray, labels: np.ndarray, n_dims: int, n_vendors: int) -> float:
    group_id = vendor_codes * n_dims + dim_codes
    n_groups = n_vendors * n_dims
    sums = np.bincount(group_id, weights=labels, minlength=n_groups)
    counts = np.bincount(group_id, minlength=n_groups)
    mask = counts > 0
    rates = sums[mask] / counts[mask]
    c = counts[mask]
    weighted_mean = np.average(rates, weights=c)
    return float(np.sqrt(np.average((rates - weighted_mean) ** 2, weights=c)))


def _run(closed: pd.DataFrame, dim_col: str, dimensao_label: str, n_permutations: int) -> FitPermutationResult:
    subset = closed.dropna(subset=[dim_col])
    labels = (subset["deal_stage"] == "Won").to_numpy(dtype=float)
    vendor_codes, vendor_uniques = pd.factorize(subset["sales_agent"])
    dim_codes, dim_uniques = pd.factorize(subset[dim_col])
    n_vendors = len(vendor_uniques)
    n_dims = len(dim_uniques)

    observed = _dispersion(vendor_codes, dim_codes, labels, n_dims, n_vendors)

    rng = np.random.default_rng(SEED)
    null_dispersions = np.empty(n_permutations)
    for i in range(n_permutations):
        shuffled = rng.permutation(vendor_codes)
        null_dispersions[i] = _dispersion(shuffled, dim_codes, labels, n_dims, n_vendors)

    p_valor = float(np.mean(null_dispersions >= observed))
    n_celulas = int((np.bincount(vendor_codes * n_dims + dim_codes, minlength=n_vendors * n_dims) > 0).sum())

    return FitPermutationResult(
        dimensao=dimensao_label,
        n_celulas=n_celulas,
        dispersao_observada=observed,
        dispersao_nula_media=float(null_dispersions.mean()),
        p_valor=p_valor,
    )


def run_produto(closed: pd.DataFrame, n_permutations: int = N_PERMUTATIONS) -> FitPermutationResult:
    return _run(closed, "product", "produto", n_permutations)


def run_setor(closed: pd.DataFrame, n_permutations: int = N_PERMUTATIONS) -> FitPermutationResult:
    return _run(closed, "sector", "setor", n_permutations)
