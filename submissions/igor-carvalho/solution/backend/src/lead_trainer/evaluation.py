"""Backtest temporal e portão de qualidade para promover versões.

Em cada data T o modelo treina só com o passado e é medido no que aconteceu nos 30 dias seguintes. As métricas
são as que o vendedor sente: a receita capturada pelo topo da lista e o acerto dos 5 primeiros de cada carteira.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from lead_core.bands import duration_thresholds
from lead_core.calibration import apply_calibration
from lead_core.constants import (
    BACKTEST_PROTOCOL, BACKTEST_SNAPSHOT_COUNT, BACKTEST_SPACING_DAYS, HORIZON_DAYS, TARGET_COL,
)

from .calibration import fit_calibration
from .training import build_test, build_train, fit_gbm

AVERAGED = ["auc", "pr_auc", "brier", "lift_top20", "revenue_capture_top20", "revenue_capture_price_only_top20",
            "seller_top5_win_rate", "stale_share_top20", "base_rate"]


def rolling_snapshots(reference: pd.Timestamp, count: int = BACKTEST_SNAPSHOT_COUNT,
                      spacing_days: int = BACKTEST_SPACING_DAYS, horizon_days: int = HORIZON_DAYS) -> list[pd.Timestamp]:
    """As últimas `count` fotos cujo desfecho de `horizon_days` já é conhecido: ref - horizonte - k * espaçamento."""
    last = pd.Timestamp(reference) - pd.Timedelta(days=horizon_days)
    return sorted(last - pd.Timedelta(days=spacing_days * k) for k in range(count))


def lift_at(y: np.ndarray, p: np.ndarray, frac: float = 0.2) -> float:
    k = max(1, int(len(y) * frac))
    idx = np.argsort(-p, kind="stable")[:k]
    return float(y[idx].mean() / y.mean())


def revenue_capture(rank_score: np.ndarray, realized: np.ndarray, frac: float = 0.2) -> float:
    k = max(1, int(len(realized) * frac))
    idx = np.argsort(-rank_score, kind="stable")[:k]
    total = realized.sum()
    return float(realized[idx].sum() / total) if total > 0 else float("nan")


def seller_topk_rate(test: pd.DataFrame, rank_score: np.ndarray, k: int = 5) -> float:
    """Visão do vendedor: dos k primeiros da carteira DELE, quantos viraram ganho no horizonte."""
    d = test.assign(_rank=rank_score).sort_values("_rank", ascending=False, kind="stable")
    return float(d.groupby("sales_agent").head(k)[TARGET_COL].mean())


def evaluate(test: pd.DataFrame, p: np.ndarray, stale_days: float | None = None) -> dict:
    y, p = test[TARGET_COL].to_numpy(), np.clip(p, 1e-4, 1 - 1e-4)
    price = test["price"].to_numpy(dtype=float)
    realized = test["realized_30d"].to_numpy(dtype=float)
    ev = p * price
    top = np.argsort(-ev, kind="stable")[:max(1, int(len(y) * 0.2))]
    return {
        "n_test": int(len(y)), "base_rate": float(y.mean()),
        "auc": float(roc_auc_score(y, p)), "pr_auc": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)), "lift_top20": lift_at(y, p),
        "revenue_capture_top20": revenue_capture(ev, realized),
        "revenue_capture_price_only_top20": revenue_capture(price, realized),   # linha de base: ordenar só pelo ticket
        "seller_top5_win_rate": seller_topk_rate(test, ev),
        "stale_share_top20": float((test["age_days"].to_numpy()[top] > stale_days).mean()) if stale_days else float("nan"),
    }


def bootstrap_auc_ci(y: np.ndarray, p: np.ndarray, n_boot: int = 300, seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() != y[i].max():
            vals.append(roc_auc_score(y[i], p[i]))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def _stale_days(df: pd.DataFrame, T: pd.Timestamp) -> float:
    closed = df[df["won"].notna() & (df["close_date"] <= T)]
    return duration_thresholds((closed["close_date"] - closed["engage_date"]).dt.days)["stale_days"]


def backtest(df: pd.DataFrame, snapshots: list[pd.Timestamp]) -> dict:
    """Treina em cada foto T usando só o passado e mede nos 30 dias seguintes. Média ponderada por n_test.
    Fotos cujo desfecho de 30 dias ainda não é conhecido nos dados são ignoradas."""
    data_end = max(df["engage_date"].max(), df["close_date"].max())
    per_snapshot, ys, ps = [], [], []
    for T in snapshots:
        if T + pd.Timedelta(days=HORIZON_DAYS) > data_end:
            continue
        train, test = build_train(df, T), build_test(df, T)
        if train.empty or len(test) < 30 or test[TARGET_COL].nunique() < 2 or train[TARGET_COL].nunique() < 2:
            continue
        fit = fit_gbm(train)
        cal = fit_calibration(fit.validation_y, fit.validation_p, fit.train_base_rate)
        p_raw = fit.predict(test)
        m = evaluate(test, apply_calibration(p_raw, cal), _stale_days(df, T))
        m["auc"] = float(roc_auc_score(test[TARGET_COL], p_raw))
        m["snapshot"] = T.date().isoformat()
        per_snapshot.append(m)
        ys.append(test[TARGET_COL].to_numpy())
        ps.append(p_raw)
    meta = {"protocol": BACKTEST_PROTOCOL, "horizon_days": HORIZON_DAYS}
    if not per_snapshot:
        return {"per_snapshot": [], "auc": None, "auc_ci95": None, **meta}

    w = np.array([m["n_test"] for m in per_snapshot], dtype=float)
    avg = {k: float(np.nanmean([np.nan if m[k] is None else m[k] for m in per_snapshot])) if k == "stale_share_top20"
           else float(np.average([m[k] for m in per_snapshot], weights=w)) for k in AVERAGED}
    lo, hi = bootstrap_auc_ci(np.concatenate(ys), np.concatenate(ps))
    return {"per_snapshot": per_snapshot, **avg, "auc_ci95": [lo, hi], "n_test": int(w.sum()), **meta}


def quality_gate(candidate: dict, active: dict | None, tolerance: float = 0.01) -> tuple[bool, str]:
    """Promove só se: (1) o AUC é significativamente acima do acaso; (2) a receita capturada no topo supera a de
    ordenar só pelo preço (o defeito do score antigo); (3) não piora a versão ativa além da tolerância, quando as
    duas foram medidas pelo mesmo protocolo (a janela do backtest anda um dia por dia; a tolerância absorve isso)."""
    if candidate.get("auc") is None:
        return False, "backtest sem dados suficientes"
    if candidate["auc_ci95"][0] <= 0.5:
        return False, f"AUC não é significativamente maior que o acaso (IC95% inferior {candidate['auc_ci95'][0]:.3f})"
    cap, price_only = candidate.get("revenue_capture_top20"), candidate.get("revenue_capture_price_only_top20")
    if cap is not None and price_only is not None and cap <= price_only:
        return False, f"receita no topo ({cap:.3f}) não supera ordenar só pelo preço ({price_only:.3f})"
    comparable = active and active.get("auc") is not None and active.get("protocol") == candidate.get("protocol")
    if comparable and candidate["auc"] < active["auc"] - tolerance:
        return False, f"AUC {candidate['auc']:.3f} pior que a versão ativa {active['auc']:.3f}"
    return True, "ok"
