"""Faixas de ação e score 0-100 (plano 3.5). Limiares vêm do model card, nunca do código."""
from __future__ import annotations

import numpy as np

from .constants import FOCUS_SCORE, FOLLOW_UP_SCORE, REVIEW_QUANTILE, STALE_QUANTILE


def cycle_quantile(durations, q: float) -> float | None:
    """Percentil q (0-1) das durações de deals já fechados; None se não há nenhum."""
    d = np.asarray(list(durations), dtype=float)
    d = d[~np.isnan(d)]
    return float(np.percentile(d, q * 100)) if d.size else None


def duration_thresholds(durations) -> dict:
    """P50, P90 (stale) e P99 (review/zumbi) das durações de deals JÁ fechados. Só para faixas e para a
    feature de idade relativa ao ciclo; a duração do próprio deal nunca entra no modelo."""
    d = list(durations)
    if not len(d):
        return {"typical_p50": 0, "stale_days": 0, "review_days": 0}
    return {
        "typical_p50": int(round(cycle_quantile(d, 0.5))),
        "stale_days": int(round(cycle_quantile(d, STALE_QUANTILE))),
        "review_days": int(round(cycle_quantile(d, REVIEW_QUANTILE))),
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


def displayed_score(band: str, score: int, thr: dict) -> int | None:
    """Score que o vendedor vê. Zumbi não tem score; "Decidir agora" mantém o score só para ordenar a fila,
    mas nunca chega à prioridade Alta (fica abaixo do corte de Foco)."""
    if band == "review":
        return None
    if band == "stale_risk":
        return min(int(score), thr.get("focus_score", FOCUS_SCORE) - 1)
    return int(score)


def priority_level(score: int | None) -> str | None:
    """Nível mostrado ao vendedor (Alta/Média/Baixa)."""
    if score is None:
        return None
    return "Alta" if score >= FOCUS_SCORE else ("Média" if score >= FOLLOW_UP_SCORE else "Baixa")
