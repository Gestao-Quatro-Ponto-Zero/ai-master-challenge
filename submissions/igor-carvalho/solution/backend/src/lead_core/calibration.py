"""Calibração da probabilidade bruta do modelo. Só a parte de aplicar vive aqui; quem ajusta (treino) está em
lead_trainer.calibration.

- ``level_shift`` (modelos atuais): p = sigmoid(logit(p_raw) + shift). Corrige só o NÍVEL da probabilidade para a
  taxa recente de ganho em 30 dias, sem mexer na inclinação, para não alterar o equilíbrio entre chance e preço
  no valor esperado (um Platt com inclinação livre chegou a esticar o logit 12x em algumas datas).
- ``shrink_to_base`` (artefatos antigos): p = base + alpha * (p_raw - centro). Mantido para carregar versões antigas.
"""
from __future__ import annotations

import numpy as np


def logit(p) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def apply_calibration(p_raw, cal: dict) -> np.ndarray:
    p = np.asarray(p_raw, dtype=float)
    if cal.get("method") == "level_shift":
        return np.clip(1.0 / (1.0 + np.exp(-(logit(p) + cal["shift"]))), 0.001, 0.99)
    return np.clip(cal["base"] + cal["alpha"] * (p - cal["center"]), 0.01, 0.99)
