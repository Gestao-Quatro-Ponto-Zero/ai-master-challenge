"""Montagem das bases de treino/teste (point-in-time) e ajuste do LightGBM com parada antecipada temporal."""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from lead_core.constants import (
    CAT_FEATURES, GAP_DAYS, LGBM_EARLY_STOPPING, LGBM_MAX_ESTIMATORS, LGBM_PARAMS, NUM_FEATURES,
    TRAIN_START_OFFSET_DAYS, VALIDATION_FRACTION_OF_SNAPSHOTS,
)
from lead_core.features import add_history_features, open_snapshot

warnings.filterwarnings("ignore", message=".*eval_set.*")   # aviso de depreciação do LightGBM 4.x


def train_start(df: pd.DataFrame) -> pd.Timestamp:
    return df["close_date"].min() + pd.Timedelta(days=TRAIN_START_OFFSET_DAYS)


def build_train(df: pd.DataFrame, T: pd.Timestamp, gap_days: int = GAP_DAYS) -> pd.DataFrame:
    """Fotos semanais até T-gap. O label só entra se o deal já tinha fechado até T."""
    rows = []
    for Tk in pd.date_range(train_start(df), T - pd.Timedelta(days=gap_days), freq="7D"):
        snap = add_history_features(open_snapshot(df, Tk), df, Tk)
        known = snap["won"].notna() & (snap["close_date"] <= T)
        rows.append(snap[known])
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_test(df: pd.DataFrame, T: pd.Timestamp) -> pd.DataFrame:
    """Pipeline aberto em T com o desfecho que aconteceu depois (só quem fechou depois tem label)."""
    snap = add_history_features(open_snapshot(df, T), df, T)
    return snap[snap["won"].notna()].reset_index(drop=True)


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
    if train.empty or train["won"].nunique() < 2:
        raise ValueError("Base de treino vazia ou com uma única classe")
    cats = {c: sorted(train[c].dropna().astype(str).unique()) for c in CAT_FEATURES}
    X, y = _matrix(train, cats), train["won"].to_numpy()

    snaps = np.sort(train["snapshot"].unique())
    cut = snaps[min(int(len(snaps) * VALIDATION_FRACTION_OF_SNAPSHOTS), len(snaps) - 1)]
    val = (train["snapshot"] >= cut).to_numpy()
    if val.sum() < 20 or (~val).sum() < 20 or len(np.unique(y[val])) < 2:
        val = np.arange(len(y)) >= int(len(y) * VALIDATION_FRACTION_OF_SNAPSHOTS)

    probe = lgb.LGBMClassifier(n_estimators=LGBM_MAX_ESTIMATORS, **LGBM_PARAMS)
    probe.fit(X[~val], y[~val], eval_set=[(X[val], y[val])],
              callbacks=[lgb.early_stopping(LGBM_EARLY_STOPPING, verbose=False)])
    best = max(int(probe.best_iteration_ or 0), 20)
    final = lgb.LGBMClassifier(n_estimators=best, **LGBM_PARAMS).fit(X, y)
    return FittedModel(
        model=final, cats=cats, best_iteration=best, validation_y=y[val],
        validation_p=probe.predict_proba(X[val])[:, 1], train_base_rate=float(y[~val].mean()),
    )
