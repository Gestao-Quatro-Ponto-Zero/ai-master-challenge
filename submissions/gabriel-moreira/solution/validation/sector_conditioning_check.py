"""Reprodução da ausência de sinal do condicionamento por setor —
Requirement "Reprodução da ausência de sinal do condicionamento por
setor".

Validação cruzada 5-fold, semente fixa: compara `logloss`/`brier` fora da
amostra do prior global achatado contra condicionar `p̂` por produto (com
encolhimento, como em produção) e por produto×setor (com e sem
encolhimento) — reproduz o achado central desta calibração: condicionar
por setor é PIOR que não condicionar, porque as células de produto×setor
não têm amostra suficiente para sustentar a diferenciação.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scoring import constants
from scoring.shrinkage import (
    GroupCounts,
    level_stats,
    p_hat_produto,
    product_group_counts,
    product_sector_group_counts,
)
from sklearn.model_selection import KFold

SEED = 20260820
N_FOLDS = 5


def _logloss(y: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _brier(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean((y - p) ** 2))


def _rate_produto_setor(
    groups: dict[tuple[str, str], GroupCounts], key: tuple[str, str], k: float, prior: float
) -> float:
    g = groups.get(key)
    if g is None or g.n == 0 or k == float("inf"):
        return prior
    return (g.n * g.rate + k * prior) / (g.n + k)


@dataclass(frozen=True)
class ModelScore:
    nome: str
    logloss: float
    brier: float


@dataclass(frozen=True)
class SectorConditioningReport:
    scores: list[ModelScore]
    n_celulas_produto_setor: int
    tamanhos_celula: list[int]

    @property
    def mediana_tamanho_celula(self) -> float:
        return float(np.median(self.tamanhos_celula)) if self.tamanhos_celula else 0.0

    def score(self, nome: str) -> ModelScore:
        return next(s for s in self.scores if s.nome == nome)


def build_report(
    closed: pd.DataFrame, k_produto: float = constants.K_PRODUTO
) -> SectorConditioningReport:
    df = closed.dropna(subset=["sector"]).reset_index(drop=True)
    y_all = (df["deal_stage"] == "Won").astype(float).to_numpy()

    acumulado: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {
        "prior_global": [],
        "produto_encolhido": [],
        "produto_setor_encolhido": [],
        "produto_setor_bruto": [],
    }

    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    for train_idx, test_idx in kf.split(df):
        train = df.iloc[train_idx]
        test = df.iloc[test_idx]
        y_test = y_all[test_idx]
        prior = float((train["deal_stage"] == "Won").mean())

        prod_counts = product_group_counts(train)
        ps_counts = product_sector_group_counts(train)
        ps_stats = level_stats(ps_counts, prior)

        p_global = np.full(len(test), prior)
        p_produto = np.array(
            [p_hat_produto(row.product, prod_counts, prior, k_produto) for row in test.itertuples()]
        )
        p_ps_encolhido = np.array(
            [
                _rate_produto_setor(ps_counts, (row.product, row.sector), ps_stats.k, prior)
                for row in test.itertuples()
            ]
        )
        p_ps_bruto = np.array(
            [_rate_produto_setor(ps_counts, (row.product, row.sector), 0.0, prior) for row in test.itertuples()]
        )

        acumulado["prior_global"].append((y_test, p_global))
        acumulado["produto_encolhido"].append((y_test, p_produto))
        acumulado["produto_setor_encolhido"].append((y_test, p_ps_encolhido))
        acumulado["produto_setor_bruto"].append((y_test, p_ps_bruto))

    scores = [
        ModelScore(
            nome=nome,
            logloss=float(np.mean([_logloss(y, p) for y, p in folds])),
            brier=float(np.mean([_brier(y, p) for y, p in folds])),
        )
        for nome, folds in acumulado.items()
    ]

    todas_ps_counts = product_sector_group_counts(df)
    tamanhos = [g.n for g in todas_ps_counts.values()]

    return SectorConditioningReport(
        scores=scores,
        n_celulas_produto_setor=len(todas_ps_counts),
        tamanhos_celula=tamanhos,
    )
