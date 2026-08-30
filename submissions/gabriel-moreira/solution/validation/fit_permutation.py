"""Reprodução da ausência de sinal do fit por vendedor — Requirement
"Reprodução da ausência de sinal do fit por vendedor".

Dois nulos, porque são duas perguntas diferentes:

`GLOBAL` embaralha os rótulos de vendedor sobre todas as linhas, com
produto/setor fixos por linha. Responde "a identidade do vendedor importa
em algum grau?" — e o efeito PRINCIPAL de vendedor entra inteiro na
estatística, porque embaralhar destrói também o efeito principal. Este
nulo NÃO controla pelo mix de produtos de cada vendedor: o embaralhamento
é exatamente o que desfaz esse mix.

`ADITIVO` é o nulo que a palavra "fit" exige. Fit significa afinidade
vendedor×produto — este vendedor vai bem NESTE produto, acima do que o
desempenho geral dele e a dificuldade geral do produto já explicam. Para
testar isso, o nulo precisa PRESERVAR os dois efeitos principais e negar
só a interação: ajustamos logit(ganho) = α + β_vendedor + γ_produto e
simulamos desfechos desse modelo (bootstrap paramétrico), comparando a
dispersão real com a dispersão gerada por um mundo sem nenhuma afinidade.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm

from permutation_tests import _p_valor

SEED = 20260821
N_PERMUTATIONS = 2000


@dataclass(frozen=True)
class FitPermutationResult:
    dimensao: str
    n_celulas: int
    dispersao_observada: float
    dispersao_nula_media: float
    p_valor: float
    #: Nulo ADITIVO — preserva os efeitos principais de vendedor e de
    #: produto/setor e nega só a interação. É este par que responde "existe
    #: fit?"; o par acima responde apenas "vendedor importa em algum grau?".
    dispersao_nula_aditiva_media: float
    p_valor_aditivo: float

    @property
    def distinguivel_de_acaso(self) -> bool:
        """Nulo GLOBAL: vendedor importa em algum grau (efeito principal +
        interação, sem separar os dois)."""
        return self.p_valor < 0.05

    @property
    def fit_distinguivel_de_acaso(self) -> bool:
        """Nulo ADITIVO: existe afinidade vendedor×dimensão ALÉM dos efeitos
        principais — a única leitura que a palavra "fit" autoriza."""
        return self.p_valor_aditivo < 0.05


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

    p_valor = _p_valor(null_dispersions, observed)
    n_celulas = int((np.bincount(vendor_codes * n_dims + dim_codes, minlength=n_vendors * n_dims) > 0).sum())

    null_aditivas = _null_aditivo(
        vendor_codes, dim_codes, labels, n_dims, n_vendors, n_permutations
    )
    p_valor_aditivo = _p_valor(null_aditivas, observed)

    return FitPermutationResult(
        dimensao=dimensao_label,
        n_celulas=n_celulas,
        dispersao_observada=observed,
        dispersao_nula_media=float(null_dispersions.mean()),
        p_valor=p_valor,
        dispersao_nula_aditiva_media=float(null_aditivas.mean()),
        p_valor_aditivo=p_valor_aditivo,
    )


def _null_aditivo(
    vendor_codes: np.ndarray,
    dim_codes: np.ndarray,
    labels: np.ndarray,
    n_dims: int,
    n_vendors: int,
    n_simulacoes: int,
) -> np.ndarray:
    """Bootstrap paramétrico sob o modelo aditivo — o nulo do FIT.

    Ajusta logit(ganho) = α + β_vendedor + γ_dimensão (sem termo de
    interação), toma a probabilidade ajustada de cada negócio real e
    sorteia desfechos dela. Cada réplica é um mundo em que vendedores
    diferem entre si, produtos diferem entre si, e NENHUM vendedor tem
    afinidade com produto nenhum. A dispersão real acima dessa nula é o
    que sobra para a interação — e só isso é fit.
    """
    design = pd.get_dummies(
        pd.DataFrame({"v": vendor_codes.astype(str), "d": dim_codes.astype(str)}),
        drop_first=True,
    ).astype(float)
    ajuste = sm.GLM(labels, sm.add_constant(design), family=sm.families.Binomial()).fit()
    mu = np.asarray(ajuste.fittedvalues)

    rng = np.random.default_rng(SEED)
    nulas = np.empty(n_simulacoes)
    for i in range(n_simulacoes):
        simulado = (rng.random(len(mu)) < mu).astype(float)
        nulas[i] = _dispersion(vendor_codes, dim_codes, simulado, n_dims, n_vendors)
    return nulas


def run_produto(closed: pd.DataFrame, n_permutations: int = N_PERMUTATIONS) -> FitPermutationResult:
    return _run(closed, "product", "produto", n_permutations)


def run_setor(closed: pd.DataFrame, n_permutations: int = N_PERMUTATIONS) -> FitPermutationResult:
    return _run(closed, "sector", "setor", n_permutations)
