"""Ajuste da calibração por encolhimento. Se não superar uma probabilidade constante (Brier), a
probabilidade NÃO deve ser exibida (calibration.useful = False) e o modelo vale só pelo ranking."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import brier_score_loss

from lead_core.calibration import apply_calibration

ALPHAS = (0.1, 0.25, 0.5, 0.75, 1.0)   # alpha mínimo 0.1 preserva o ranking (alpha=0 o apagaria)


def fit_calibration(y_val: np.ndarray, p_val: np.ndarray, base_rate: float) -> dict:
    center = float(np.mean(p_val))
    brier_const = float(brier_score_loss(y_val, np.full(len(y_val), base_rate)))
    best_alpha, best_brier = ALPHAS[0], np.inf
    for alpha in ALPHAS:
        cal = {"alpha": alpha, "center": center, "base": base_rate}
        b = float(brier_score_loss(y_val, apply_calibration(p_val, cal)))
        if b < best_brier:
            best_alpha, best_brier = alpha, b
    return {
        "method": "shrink_to_base", "alpha": best_alpha, "center": center, "base": float(base_rate),
        "brier_calibrated": best_brier, "brier_constant": brier_const,
        "useful": bool(best_brier < brier_const),
    }
