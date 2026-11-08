"""Formas de ordenar o pipeline aberto numa data T, todas point-in-time (só usam o que se sabia em T).

- champion   : réplica exata do score de produção (mesmas funções do backend: LightGBM 'won', calibração,
               EV = p_win x preço, percentil 0-100, faixas). Nada é reimplementado.
- price_only : só o preço de tabela (linha de base: mostra quanto do score atual é só ticket).
- challenger : LightGBM com o alvo "ganho em até H dias a partir de hoje" (p_h). O alvo é observável para
               TODO deal aberto, inclusive os parados que nunca fecham (viram 0), o que remove o viés de
               censura do modelo atual. Duas leituras: p_h (conversão) e p_h x preço (receita em H dias).
"""
from __future__ import annotations

import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from .backend import use_backend_code

use_backend_code()
from lead_core.bands import duration_thresholds, score_from_ev  # noqa: E402
from lead_core.constants import (  # noqa: E402
    CAT_FEATURES, FOCUS_SCORE, FOLLOW_UP_SCORE, LGBM_PARAMS, NUM_FEATURES, TRAIN_START_OFFSET_DAYS,
)
from lead_core.features import add_history_features, apply_tables, build_history_tables, open_snapshot  # noqa: E402
from lead_trainer.calibration import fit_calibration  # noqa: E402
from lead_trainer.pipeline import _make_bundle, _reference_distribution, closed_durations, score_open_deals  # noqa: E402
from lead_trainer.training import build_train, fit_gbm  # noqa: E402

warnings.filterwarnings("ignore")
HORIZON = 30


def _logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


# ----------------------------------------------------------------------------- campeão (produção)
def champion(df: pd.DataFrame, T: pd.Timestamp) -> pd.DataFrame:
    """Pontua como a produção faria em T. Retorna só Engaging, com score, band, p_win, ev."""
    fit = fit_gbm(build_train(df, T))
    cal = fit_calibration(fit.validation_y, fit.validation_p, fit.train_base_rate)
    snap = open_snapshot(df, T)
    tables = build_history_tables(df, T, snap)
    thr = {**duration_thresholds(closed_durations(df, T)), "focus_score": FOCUS_SCORE,
           "follow_up_score": FOLLOW_UP_SCORE}
    bundle = _make_bundle(fit, cal, tables, {"version": "lab", "thresholds": thr})
    bundle.ref_ev = _reference_distribution(bundle, apply_tables(snap, tables))
    # score_open_deals também pontua Prospecting pelo estágio ATUAL do df; filtramos para Engaging em T.
    sc = score_open_deals(df[df["engage_date"].notna()], T, bundle)
    sc = sc[sc["stage"] == "Engaging"].set_index("opportunity_id")
    sc.attrs["thresholds"] = thr
    return sc


# ----------------------------------------------------------------------------- desafiante
EXTRA_FEATURES = ["age_vs_max_cycle"]   # idade / P99 do ciclo dos deals fechados até a data


def _add_cycle(s: pd.DataFrame, df: pd.DataFrame, Tk: pd.Timestamp) -> pd.DataFrame:
    closed = df[df["won"].notna() & (df["close_date"] <= Tk)]
    # P99 e não o máximo: um zumbi antigo fechado numa limpeza de carteira não pode mover a régua
    mx = float((closed["close_date"] - closed["engage_date"]).dt.days.quantile(0.99) or 1)
    return s.assign(age_vs_max_cycle=s["age_days"] / max(mx, 1.0))


def _label_h(snap: pd.DataFrame, Tk: pd.Timestamp, h: int) -> np.ndarray:
    return ((snap["won"] == 1) & (snap["close_date"] <= Tk + pd.Timedelta(days=h))).astype(int).to_numpy()


def _matrix(f: pd.DataFrame, cats: dict) -> pd.DataFrame:
    X = f[NUM_FEATURES + EXTRA_FEATURES + CAT_FEATURES].copy()
    for c in CAT_FEATURES:
        X[c] = pd.Categorical(X[c].astype(str), categories=cats[c])
    return X


def build_train_h(df: pd.DataFrame, T: pd.Timestamp, h: int = HORIZON) -> pd.DataFrame:
    """Fotos semanais até T-h: em cada foto, todos os deals abertos, alvo = ganhou em até h dias."""
    start = df["close_date"].min() + pd.Timedelta(days=TRAIN_START_OFFSET_DAYS)
    rows = []
    for Tk in pd.date_range(start, T - pd.Timedelta(days=h), freq="7D"):
        s = _add_cycle(add_history_features(open_snapshot(df, Tk), df, Tk), df, Tk)
        s["y"] = _label_h(s, Tk, h)
        rows.append(s)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


class Challenger:
    def __init__(self, h: int = HORIZON):
        self.h = h

    def fit(self, df: pd.DataFrame, T: pd.Timestamp) -> "Challenger":
        tr = build_train_h(df, T, self.h)
        self.cats = {c: sorted(tr[c].dropna().astype(str).unique()) for c in CAT_FEATURES}
        snaps = np.sort(tr["snapshot"].unique())
        val = (tr["snapshot"] >= snaps[int(len(snaps) * 0.75)]).to_numpy()
        X, y = _matrix(tr, self.cats), tr["y"].to_numpy()
        # Parada antecipada por AUC (ordenação): o logloss piora só porque a taxa base muda com o tempo.
        probe = lgb.LGBMClassifier(n_estimators=800, **LGBM_PARAMS).fit(
            X[~val], y[~val], eval_set=[(X[val], y[val])], eval_metric="auc",
            callbacks=[lgb.early_stopping(50, first_metric_only=True, verbose=False)])
        self.best = max(int(probe.best_iteration_ or 0), 50)
        # Calibração de Platt na janela de validação (mais recente): corrige o nível da probabilidade.
        pv = probe.predict_proba(X[val], num_iteration=self.best)[:, 1]
        self.platt = LogisticRegression().fit(_logit(pv).reshape(-1, 1), y[val])
        self.model = lgb.LGBMClassifier(n_estimators=self.best, **LGBM_PARAMS).fit(X, y)
        self.train_rows, self.train_rate = len(tr), float(y.mean())
        return self

    def score(self, df: pd.DataFrame, T: pd.Timestamp) -> pd.DataFrame:
        snap = _add_cycle(add_history_features(open_snapshot(df, T), df, T), df, T)
        p = self.platt.predict_proba(_logit(self.model.predict_proba(_matrix(snap, self.cats))[:, 1]).reshape(-1, 1))[:, 1]
        ev = p * snap["price"].to_numpy(dtype=float)
        out = snap[["opportunity_id", "sales_agent", "product", "price", "age_days"]].copy()
        out["p_h"], out["ev_h"] = p, ev
        out["score_conv"] = score_from_ev(p, np.sort(p))      # percentil da chance de ganhar em H dias
        out["score_rev"] = score_from_ev(ev, np.sort(ev))     # percentil da receita esperada em H dias
        return out.set_index("opportunity_id")


def price_only(df: pd.DataFrame, T: pd.Timestamp) -> pd.Series:
    s = open_snapshot(df, T)
    return s.set_index("opportunity_id")["price"].astype(float)
