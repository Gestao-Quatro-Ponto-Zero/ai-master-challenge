"""Reprodução da ausência de sinal das curvas de aging por produto —
Requirement "Reprodução da ausência de sinal das curvas de aging por
produto".

Validação cruzada 5-fold, semente fixa: compara `logloss`/`brier` fora da
amostra do prior global achatado contra a curva de aging GLOBAL (a usada
em produção) e curvas repartidas por produto, com e sem encolhimento —
reproduz o achado central: a curva global vence todas as alternativas
particionadas por produto, e ao menos um produto não tem amostra
suficiente para calibrar uma curva própria.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

SEED = 20260820
N_FOLDS = 5
# Faixas de idade em dias — mesmos pontos usados para demonstrar o achado
# na análise original (docs/decisions-log.md, entrada 2026-08-20).
AGE_BANDS = [0, 14, 45, 57, 88, 110, 120, 138]
# Força de encolhimento da variante "por produto, com encolhimento" — não
# recalibrada à parte de K_PRODUTO, mesma ordem de grandeza.
K_ENCOLHIMENTO = 4.0


def _band(age: pd.Series) -> pd.Series:
    return pd.cut(age, AGE_BANDS, include_lowest=True)


def _logloss(y: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _brier(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean((y - p) ** 2))


@dataclass(frozen=True)
class ModelScore:
    nome: str
    logloss: float
    brier: float


@dataclass(frozen=True)
class AgingByProductReport:
    scores: list[ModelScore]
    amostra_por_produto_faixa: pd.DataFrame

    def score(self, nome: str) -> ModelScore:
        return next(s for s in self.scores if s.nome == nome)

    @property
    def existe_celula_com_uma_observacao(self) -> bool:
        return bool((self.amostra_por_produto_faixa.fillna(0) == 1).any().any())


def build_report(closed: pd.DataFrame) -> AgingByProductReport:
    df = closed.copy()
    df["age"] = (df["close_date"] - df["engage_date"]).dt.days
    df["won"] = (df["deal_stage"] == "Won").astype(float)
    df["faixa"] = _band(df["age"])
    df = df.dropna(subset=["faixa"]).reset_index(drop=True)

    y_all = df["won"].to_numpy()
    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)

    acumulado: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {
        "prior_global": [],
        "curva_global": [],
        "curva_por_produto_bruta": [],
        "curva_por_produto_encolhida": [],
    }

    for train_idx, test_idx in kf.split(df):
        train = df.iloc[train_idx]
        test = df.iloc[test_idx]
        y_test = y_all[test_idx]
        prior = float(train["won"].mean())

        taxa_global_faixa = train.groupby("faixa", observed=True)["won"].mean()
        stats_produto_faixa = train.groupby(["product", "faixa"], observed=True)["won"].agg(["mean", "size"])

        p_global_flat = np.full(len(test), prior)
        p_curva_global = np.array(
            [float(taxa_global_faixa.get(faixa, prior)) for faixa in test["faixa"]]
        )

        def _bruto(row: pd.Series) -> float:
            key = (row["product"], row["faixa"])
            if key in stats_produto_faixa.index:
                return float(stats_produto_faixa.loc[key, "mean"])
            return float(taxa_global_faixa.get(row["faixa"], prior))

        def _encolhida(row: pd.Series) -> float:
            banda_prior = float(taxa_global_faixa.get(row["faixa"], prior))
            key = (row["product"], row["faixa"])
            if key not in stats_produto_faixa.index:
                return banda_prior
            n = float(stats_produto_faixa.loc[key, "size"])
            rate = float(stats_produto_faixa.loc[key, "mean"])
            return (n * rate + K_ENCOLHIMENTO * banda_prior) / (n + K_ENCOLHIMENTO)

        p_bruto = test.apply(_bruto, axis=1).to_numpy(dtype=float)
        p_encolhida = test.apply(_encolhida, axis=1).to_numpy(dtype=float)

        acumulado["prior_global"].append((y_test, p_global_flat))
        acumulado["curva_global"].append((y_test, p_curva_global))
        acumulado["curva_por_produto_bruta"].append((y_test, p_bruto))
        acumulado["curva_por_produto_encolhida"].append((y_test, p_encolhida))

    scores = [
        ModelScore(
            nome=nome,
            logloss=float(np.mean([_logloss(y, p) for y, p in folds])),
            brier=float(np.mean([_brier(y, p) for y, p in folds])),
        )
        for nome, folds in acumulado.items()
    ]

    amostra = df.groupby(["product", "faixa"], observed=True).size().unstack(fill_value=0)

    return AgingByProductReport(scores=scores, amostra_por_produto_faixa=amostra)
