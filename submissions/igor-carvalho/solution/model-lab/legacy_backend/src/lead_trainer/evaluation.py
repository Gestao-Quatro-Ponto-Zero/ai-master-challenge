"""Backtest temporal (mesmo protocolo dos notebooks) e portão de qualidade para promover versões."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from lead_core.calibration import apply_calibration

from .calibration import fit_calibration
from .training import build_test, build_train, fit_gbm


def lift_at(y: np.ndarray, p: np.ndarray, frac: float = 0.2) -> float:
    k = max(1, int(len(y) * frac))
    idx = np.argsort(-p, kind="stable")[:k]
    return float(y[idx].mean() / y.mean())


def revenue_capture(rank_score: np.ndarray, realized: np.ndarray, frac: float = 0.2) -> float:
    k = max(1, int(len(realized) * frac))
    idx = np.argsort(-rank_score, kind="stable")[:k]
    total = realized.sum()
    return float(realized[idx].sum() / total) if total > 0 else float("nan")


def evaluate(test: pd.DataFrame, p: np.ndarray) -> dict:
    y, p = test["won"].to_numpy(), np.clip(p, 1e-4, 1 - 1e-4)
    realized = test["close_value"].fillna(0).to_numpy()
    return {
        "n_test": int(len(y)), "base_rate": float(y.mean()),
        "auc": float(roc_auc_score(y, p)), "pr_auc": float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, p)), "lift_top20": lift_at(y, p),
        "revenue_capture_top20": revenue_capture(p * test["price"].to_numpy(), realized),
    }


def bootstrap_auc_ci(y: np.ndarray, p: np.ndarray, n_boot: int = 300, seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() != y[i].max():
            vals.append(roc_auc_score(y[i], p[i]))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def backtest(df: pd.DataFrame, snapshots: list[pd.Timestamp]) -> dict:
    """Treina em cada foto T usando só o passado e mede no futuro. Retorna média ponderada por n_test."""
    per_snapshot, ys, ps = [], [], []
    for T in snapshots:
        train, test = build_train(df, T), build_test(df, T)
        if train.empty or len(test) < 30 or test["won"].nunique() < 2:
            continue
        fit = fit_gbm(train)
        cal = fit_calibration(fit.validation_y, fit.validation_p, fit.train_base_rate)
        p_raw = fit.predict(test)
        m = evaluate(test, apply_calibration(p_raw, cal))
        m["auc"] = float(roc_auc_score(test["won"], p_raw))
        m["snapshot"] = T.date().isoformat()
        per_snapshot.append(m)
        ys.append(test["won"].to_numpy())
        ps.append(p_raw)
    if not per_snapshot:
        return {"per_snapshot": [], "auc": None, "auc_ci95": None}

    w = np.array([m["n_test"] for m in per_snapshot], dtype=float)
    keys = ["auc", "pr_auc", "brier", "lift_top20", "revenue_capture_top20", "base_rate"]
    avg = {k: float(np.average([m[k] for m in per_snapshot], weights=w)) for k in keys}
    lo, hi = bootstrap_auc_ci(np.concatenate(ys), np.concatenate(ps))
    return {"per_snapshot": per_snapshot, **avg, "auc_ci95": [lo, hi], "n_test": int(w.sum())}


def quality_gate(candidate: dict, active: dict | None, tolerance: float = 0.005) -> tuple[bool, str]:
    """Promove só se o AUC é significativamente acima do acaso e não piora o modelo ativo além da tolerância."""
    if candidate.get("auc") is None:
        return False, "backtest sem dados suficientes"
    if candidate["auc_ci95"][0] <= 0.5:
        return False, f"AUC não é significativamente maior que o acaso (IC95% inferior {candidate['auc_ci95'][0]:.3f})"
    if active and active.get("auc") is not None and candidate["auc"] < active["auc"] - tolerance:
        return False, f"AUC {candidate['auc']:.3f} pior que a versão ativa {active['auc']:.3f}"
    return True, "ok"
