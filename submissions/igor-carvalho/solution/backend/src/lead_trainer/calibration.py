"""Ajuste do deslocamento de nível da probabilidade de ganhar em 30 dias (ver lead_core.calibration).

O shift é escolhido para que a média das probabilidades na janela de validação (a mais recente) seja igual à taxa
observada nela. Se isso não superar uma probabilidade constante (Brier) fora da amostra, a probabilidade NÃO deve
ser exibida (calibration.useful = False) e o modelo vale só pelo ranking. A taxa de ganho em 30 dias varia muito
de uma janela para outra, então este resultado costuma ser "não útil", e isso é informação, não erro."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import brier_score_loss

from lead_core.calibration import apply_calibration, logit

MIN_ROWS_FOR_HOLDOUT = 200   # abaixo disso não há como separar uma metade para medir fora da amostra
MAX_SHIFT = 4.0              # limite em log-odds (fator de ~55 nas odds) contra janelas degeneradas


def fit_shift(y: np.ndarray, p: np.ndarray) -> float:
    """Shift s tal que mean(sigmoid(logit(p) + s)) == mean(y) (bisecção; a média é monótona em s)."""
    z, target = logit(p), float(np.mean(y))
    lo, hi = -MAX_SHIFT, MAX_SHIFT
    for _ in range(50):
        mid = (lo + hi) / 2
        if float(np.mean(1.0 / (1.0 + np.exp(-(z + mid))))) > target:
            hi = mid
        else:
            lo = mid
    return float((lo + hi) / 2)


def fit_calibration(y_val: np.ndarray, p_val: np.ndarray, base_rate: float) -> dict:
    """y_val/p_val em ordem cronológica. A utilidade é medida na 2ª metade da validação (shift ajustado só na 1ª)
    contra uma probabilidade constante igual à taxa base do treino; o ajuste final usa a validação inteira."""
    y, p = np.asarray(y_val, dtype=float), np.asarray(p_val, dtype=float)
    half = len(y) // 2
    holdout = len(y) >= MIN_ROWS_FOR_HOLDOUT
    fit_y, fit_p, ev_y, ev_p = (y[:half], p[:half], y[half:], p[half:]) if holdout else (y, p, y, p)

    probe = {"method": "level_shift", "shift": fit_shift(fit_y, fit_p)}
    brier_cal = float(brier_score_loss(ev_y, apply_calibration(ev_p, probe), labels=[0, 1]))
    brier_const = float(brier_score_loss(ev_y, np.full(len(ev_y), base_rate), labels=[0, 1]))
    return {
        "method": "level_shift", "shift": fit_shift(y, p), "base": float(base_rate),
        "brier_calibrated": brier_cal, "brier_constant": brier_const, "useful": bool(brier_cal < brier_const),
        "evaluated": "out_of_sample" if holdout else "in_sample",
    }
