"""Montagem das bases de treino/teste (point-in-time) e ajuste do LightGBM com parada antecipada temporal.

Alvo: "este deal vira Won nos próximos 30 dias, a partir da foto?". Ele existe para TODO deal aberto na foto,
inclusive os que ficam parados para sempre (viram 0). Treinar só com deals que já fecharam fazia o modelo achar
que deal velho é melhor: perdidos morrem rápido e ganhos demoram, e quem nunca fecha nunca aparecia.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from lead_core.constants import (
    CAT_FEATURES, GAP_DAYS, HORIZON_DAYS, LGBM_EARLY_STOPPING, LGBM_MAX_ESTIMATORS, LGBM_MIN_ESTIMATORS,
    LGBM_PARAMS, NUM_FEATURES, TARGET_COL, TRAIN_START_OFFSET_DAYS, VALIDATION_FRACTION_OF_SNAPSHOTS,
)
from lead_core.features import add_history_features, open_snapshot

warnings.filterwarnings("ignore", message=".*eval_set.*")   # aviso de depreciação do LightGBM 4.x


def train_start(df: pd.DataFrame) -> pd.Timestamp:
    return df["close_date"].min() + pd.Timedelta(days=TRAIN_START_OFFSET_DAYS)


def won_within(snap: pd.DataFrame, T: pd.Timestamp, horizon_days: int = HORIZON_DAYS) -> pd.Series:
    """1 se o deal fechou como Won em até `horizon_days` depois da foto T; 0 caso contrário (perdeu OU segue aberto)."""
    return ((snap["won"] == 1) & (snap["close_date"] <= T + pd.Timedelta(days=horizon_days))).astype(int)


def build_train(df: pd.DataFrame, T: pd.Timestamp, gap_days: int = GAP_DAYS) -> pd.DataFrame:
    """Fotos semanais até T - gap: todos os deals abertos em cada foto, com o desfecho de 30 dias já conhecido em T.

    Sem vazamento: a feature da foto Tk usa só o passado de Tk, e o rótulo só olha até Tk + 30 <= T.
    """
    rows = []
    for Tk in pd.date_range(train_start(df), T - pd.Timedelta(days=gap_days), freq="7D"):
        snap = add_history_features(open_snapshot(df, Tk), df, Tk)
        snap[TARGET_COL] = won_within(snap, Tk)
        rows.append(snap)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_test(df: pd.DataFrame, T: pd.Timestamp, horizon_days: int = HORIZON_DAYS) -> pd.DataFrame:
    """Pipeline aberto em T com o que aconteceu nos `horizon_days` seguintes (T + horizonte deve estar no passado)."""
    snap = add_history_features(open_snapshot(df, T), df, T)
    snap[TARGET_COL] = won_within(snap, T, horizon_days)
    snap["realized_30d"] = np.where(snap[TARGET_COL] == 1, snap["close_value"].fillna(0.0), 0.0)
    return snap.reset_index(drop=True)


@dataclass
class FittedModel:
    model: lgb.LGBMClassifier
    cats: dict[str, list[str]]
    best_iteration: int
    validation_y: np.ndarray
    validation_p: np.ndarray       # previsões do modelo "probe" na janela de validação (usadas na calibração)
    train_base_rate: float

    def predict(self, feats: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(_matrix(feats, self.cats))[:, 1]


def _matrix(feats: pd.DataFrame, cats: dict[str, list[str]]) -> pd.DataFrame:
    X = feats[NUM_FEATURES + CAT_FEATURES].copy()
    for col in CAT_FEATURES:
        X[col] = pd.Categorical(X[col], categories=cats[col])
    return X


def fit_gbm(train: pd.DataFrame) -> FittedModel:
    if train.empty or TARGET_COL not in train or train[TARGET_COL].nunique() < 2:
        raise ValueError("Base de treino vazia ou com uma única classe")
    cats = {c: sorted(train[c].dropna().astype(str).unique()) for c in CAT_FEATURES}
    X, y = _matrix(train, cats), train[TARGET_COL].to_numpy()

    snaps = np.sort(train["snapshot"].unique())
    cut = snaps[min(int(len(snaps) * VALIDATION_FRACTION_OF_SNAPSHOTS), len(snaps) - 1)]
    val = (train["snapshot"] >= cut).to_numpy()
    if val.sum() < 20 or (~val).sum() < 20 or len(np.unique(y[val])) < 2:
        val = np.arange(len(y)) >= int(len(y) * VALIDATION_FRACTION_OF_SNAPSHOTS)

    # A parada usa o AUC (metric="auc" em LGBM_PARAMS): o logloss piora na janela recente só porque a taxa
    # base muda no tempo, e parava o modelo com poucas árvores. O nível da probabilidade é ajustado na calibração.
    probe = lgb.LGBMClassifier(n_estimators=LGBM_MAX_ESTIMATORS, **LGBM_PARAMS)
    probe.fit(X[~val], y[~val], eval_set=[(X[val], y[val])],
              callbacks=[lgb.early_stopping(LGBM_EARLY_STOPPING, verbose=False)])
    best = max(int(probe.best_iteration_ or 0), LGBM_MIN_ESTIMATORS)
    final = lgb.LGBMClassifier(n_estimators=best, **LGBM_PARAMS).fit(X, y)
    return FittedModel(
        model=final, cats=cats, best_iteration=best, validation_y=y[val],
        validation_p=probe.predict_proba(X[val], num_iteration=best)[:, 1], train_base_rate=float(y[~val].mean()),
    )
