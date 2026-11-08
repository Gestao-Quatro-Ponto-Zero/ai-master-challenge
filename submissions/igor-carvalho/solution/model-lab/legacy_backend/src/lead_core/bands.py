"""Faixas de ação e score 0-100 (plano 3.5). Limiares vêm do model card, nunca do código."""
from __future__ import annotations

import numpy as np

from .constants import FOCUS_SCORE, FOLLOW_UP_SCORE


def duration_thresholds(durations) -> dict:
    """P50, P90 e máximo das durações de deals JÁ fechados (usadas só para faixas, nunca como feature)."""
    d = np.asarray(list(durations), dtype=float)
    if d.size == 0:
        return {"typical_p50": 0, "stale_days": 0, "review_days": 0}
    return {
        "typical_p50": int(round(np.percentile(d, 50))),
        "stale_days": int(round(np.percentile(d, 90))),
        "review_days": int(d.max()),
    }


def score_from_ev(ev: np.ndarray, reference_sorted: np.ndarray) -> np.ndarray:
    """Percentil (0-100) do valor esperado entre os deals não-zumbis de referência."""
    ev = np.asarray(ev, dtype=float)
    if reference_sorted.size == 0:
        return np.zeros(ev.shape, dtype=int)
    pos = np.searchsorted(reference_sorted, ev, side="right")
    return np.clip(np.rint(100.0 * pos / reference_sorted.size), 0, 100).astype(int)


def assign_band(stage: str, age_days: float | None, score: float | None, thr: dict) -> str:
    if stage == "Prospecting":
        return "prospecting"
    if age_days is not None and age_days > thr["review_days"]:
        return "review"
    if age_days is not None and age_days > thr["stale_days"]:
        return "stale_risk"
    if score is not None and score >= thr.get("focus_score", FOCUS_SCORE):
        return "focus"
    if score is not None and score >= thr.get("follow_up_score", FOLLOW_UP_SCORE):
        return "follow_up"
    return "low"


def priority_level(score: int | None) -> str | None:
    """Nível mostrado ao vendedor (Alta/Média/Baixa)."""
    if score is None:
        return None
    return "Alta" if score >= FOCUS_SCORE else ("Média" if score >= FOLLOW_UP_SCORE else "Baixa")
