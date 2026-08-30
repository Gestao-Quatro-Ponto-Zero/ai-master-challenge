"""Reprodução da ausência de efeito de produto sobre a duração do ciclo —
Requirement "Reprodução da ausência de efeito de produto sobre a duração
do ciclo".

Teste de permutação (semente fixa) sobre a dispersão das MEDIANAS de
duração de ciclo por produto — testa se URGÊNCIA (que usa uma curva
global) está descartando um efeito de produto real — e a taxa de
resolução em 30 dias por produto e faixa de idade, para comparação direta
com a taxa global usada em produção.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

SEED = 20260820
N_PERMUTATIONS = 2000
AGE_BANDS = [0, 45, 88, 138]


def _dispersion_of_medians(duration: np.ndarray, groups: np.ndarray) -> float:
    df = pd.DataFrame({"duration": duration, "group": groups})
    medians = df.groupby("group")["duration"].median()
    return float(medians.max() - medians.min())


@dataclass(frozen=True)
class CycleDurationPermutationResult:
    dispersao_observada: float
    dispersao_nula_media: float
    p_valor: float


def run(closed: pd.DataFrame, n_permutations: int = N_PERMUTATIONS) -> CycleDurationPermutationResult:
    """Valor-p bicaudal: fração dos embaralhamentos cuja dispersão fica tão
    longe da média nula quanto a observada, em qualquer direção — a
    hipótese aqui não é "produto aumenta a dispersão", é "produto explica
    a dispersão observada, seja ela maior OU MENOR que o ruído amostral"
    (o achado real é que a dispersão observada é menor que a nula)."""
    duration = (closed["close_date"] - closed["engage_date"]).dt.days.to_numpy(dtype=float)
    groups = closed["product"].to_numpy()

    observed = _dispersion_of_medians(duration, groups)

    rng = np.random.default_rng(SEED)
    null_dispersions = np.empty(n_permutations)
    for i in range(n_permutations):
        shuffled = rng.permutation(groups)
        null_dispersions[i] = _dispersion_of_medians(duration, shuffled)

    null_mean = float(null_dispersions.mean())
    distancia_observada = abs(observed - null_mean)
    p_valor = float(
        (1 + np.sum(np.abs(null_dispersions - null_mean) >= distancia_observada))
        / (len(null_dispersions) + 1)
    )  # add-one: ver `permutation_tests._p_valor`

    return CycleDurationPermutationResult(
        dispersao_observada=observed,
        dispersao_nula_media=null_mean,
        p_valor=p_valor,
    )


def resolution_rate_by_product_and_age(
    closed: pd.DataFrame, bands: list[int] = AGE_BANDS
) -> pd.DataFrame:
    """Taxa de resolução em 30 dias (P(resolve em <30d | ainda aberto na
    idade t)) por produto e faixa de idade, com uma linha GLOBAL por faixa
    para comparação direta com a taxa usada em produção (constants.RISCO_BREAKPOINTS)."""
    df = closed.copy()
    df["duration"] = (df["close_date"] - df["engage_date"]).dt.days

    rows: list[dict] = []
    for lo, hi in zip(bands, bands[1:]):
        for produto, sub in df.groupby("product"):
            em_risco = sub[sub["duration"] >= lo]
            n = len(em_risco)
            resolvidos = int((em_risco["duration"] < lo + 30).sum())
            rows.append(
                {
                    "product": produto,
                    "faixa": f"{lo}-{hi}",
                    "n_em_risco": n,
                    "taxa_resolucao_30d": resolvidos / n if n else None,
                }
            )
        em_risco_global = df[df["duration"] >= lo]
        n_global = len(em_risco_global)
        resolvidos_global = int((em_risco_global["duration"] < lo + 30).sum())
        rows.append(
            {
                "product": "GLOBAL",
                "faixa": f"{lo}-{hi}",
                "n_em_risco": n_global,
                "taxa_resolucao_30d": resolvidos_global / n_global if n_global else None,
            }
        )
    return pd.DataFrame(rows)
