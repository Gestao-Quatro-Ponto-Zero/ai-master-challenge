"""Calibração por encolhimento: p_cal = base + alpha * (p_raw - centro). Só a parte de aplicar vive aqui;
quem ajusta (treino) está em lead_trainer.calibration."""
from __future__ import annotations

import numpy as np


def apply_calibration(p_raw, cal: dict) -> np.ndarray:
    p = np.asarray(p_raw, dtype=float)
    return np.clip(cal["base"] + cal["alpha"] * (p - cal["center"]), 0.01, 0.99)
