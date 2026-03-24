"""
scorer.py — Aplica os coeficientes do modelo para calcular score 0-10 por deal.

Lógica:
  - Busca WRs nas lookup tables geradas pelo train.py
  - Aplica regressão logística (prob = sigmoid(X_scaled @ coefs + intercept))
  - Converte probabilidade para PERCENTIL dentro do pipeline (escala 0-10)
  - Deals com n_agent_product < MIN_DEALS_FOR_SCORE → sem score (alerta)
  - Quando sector é None: não usa na equação, repondera as 2 features disponíveis
  - Faixas pós-percentil: Alta 7-10 | Média 4-6 | Baixa 0-3
"""

import json
import math
import os
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_coefficients.json")

_model: dict = {}


def _load_model():
    global _model
    if not _model:
        with open(MODEL_PATH, encoding="utf-8") as f:
            _model = json.load(f)
    return _model


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def _clean_sector(sector) -> Optional[str]:
    """Retorna None se sector for ausente ou NaN."""
    if sector is None:
        return None
    if isinstance(sector, float) and math.isnan(sector):
        return None
    return str(sector)


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def _get_ap_wr(m: dict, agent: str, product: str) -> tuple[Optional[float], int]:
    """Retorna (wr, n) para agente x produto."""
    for row in m["ap_stats"]:
        if row["sales_agent"] == agent and row["product"] == product:
            return row["wr_agent_product"], int(row["n_agent_product"])
    return None, 0


def _get_recent_wr(m: dict, agent: str) -> Optional[float]:
    for row in m["recent_stats"]:
        if row["sales_agent"] == agent:
            return row["wr_agent_recent"]
    return None


def _get_sector_wr(m: dict, agent: str, sector: Optional[str]) -> Optional[float]:
    if not sector:
        return None
    for row in m["sector_stats"]:
        if row["sales_agent"] == agent and row["sector"] == sector:
            return row["wr_agent_sector"]
    return None


# ---------------------------------------------------------------------------
# Score de um único deal
# ---------------------------------------------------------------------------

def score_deal(agent: str, product: str, sector: Optional[str] = None) -> dict:
    """
    Retorna dict com:
      score          : float 0-10  (percentil; None se sem dados suficientes)
      _raw_prob      : float 0-1   (probabilidade real para exibir como "X% de chance")
      tier           : 'Alta' | 'Média' | 'Baixa' | None
      has_score      : bool
      alert          : bool   (True quando sem score)
      sector_is_real : bool   (False quando sector é None ou sem histórico)
      wr_breakdown   : dict com as features usadas
      n_deals        : int   (base histórica do combo principal)
    """
    m = _load_model()
    min_n = m["min_deals_for_score"]

    sector = _clean_sector(sector)
    wr_ap, n_ap = _get_ap_wr(m, agent, product)
    wr_recent = _get_recent_wr(m, agent)
    wr_sector = _get_sector_wr(m, agent, sector)

    sector_is_real = wr_sector is not None

    # Sem dados suficientes → alerta
    if n_ap < min_n or wr_ap is None or wr_recent is None:
        return {
            "score": None,
            "_raw_prob": None,
            "tier": None,
            "has_score": False,
            "alert": True,
            "alert_reason": (
                f"Apenas {n_ap} deals históricos para {agent} × {product} "
                f"(mínimo: {min_n})"
            ),
            "sector_is_real": sector_is_real,
            "wr_breakdown": {
                "wr_agent_product": wr_ap,
                "wr_agent_recent": wr_recent,
                "wr_agent_sector": wr_sector,
            },
            "n_deals": n_ap,
        }

    mean = np.array(m["scaler_mean"])
    std = np.array(m["scaler_std"])
    coefs = [
        m["coefficients"]["wr_agent_product"],
        m["coefficients"]["wr_agent_recent"],
        m["coefficients"]["wr_agent_sector"],
    ]

    if sector_is_real:
        # 3 features disponíveis
        features = np.array([wr_ap, wr_recent, wr_sector])
        X_s = (features - mean) / std
        logit = float(np.dot(X_s, coefs)) + m["intercept"]
    else:
        # Reponderar: usar apenas as 2 features disponíveis (sem setor fabricado)
        features_2 = np.array([wr_ap, wr_recent])
        mean_2 = mean[:2]
        std_2 = std[:2]
        coefs_2 = coefs[:2]
        X_s_2 = (features_2 - mean_2) / std_2
        logit = float(np.dot(X_s_2, coefs_2)) + m["intercept"]

    prob = _sigmoid(logit)

    # Tier e score provisórios — serão substituídos por percentil em score_pipeline()
    raw_score = round(prob * 10, 1)
    raw_score = max(0.0, min(10.0, raw_score))

    if raw_score >= 7:
        tier = "Alta"
    elif raw_score >= 4:
        tier = "Média"
    else:
        tier = "Baixa"

    return {
        "score": raw_score,        # Será substituído pelo percentil
        "_raw_prob": prob,          # Probabilidade real (0-1) para exibição
        "tier": tier,               # Será recalculado após percentil
        "has_score": True,
        "alert": False,
        "alert_reason": None,
        "sector_is_real": sector_is_real,
        "wr_breakdown": {
            "wr_agent_product": round(wr_ap, 4),
            "wr_agent_recent": round(wr_recent, 4),
            "wr_agent_sector": round(wr_sector, 4) if sector_is_real else None,
        },
        "n_deals": n_ap,
    }


# ---------------------------------------------------------------------------
# Score de um DataFrame inteiro de deals abertos
# ---------------------------------------------------------------------------

def score_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe DataFrame de deals abertos (com colunas sales_agent, product, sector).
    Retorna o mesmo DataFrame enriquecido com colunas de score.
    Converte probabilidades brutas para percentil dentro do pipeline (escala 0-10).
    """
    from scipy.stats import percentileofscore

    results = df.apply(
        lambda row: score_deal(
            row["sales_agent"],
            row["product"],
            _clean_sector(row.get("sector")),
        ),
        axis=1,
    )
    results_df = pd.DataFrame(results.tolist())
    combined = pd.concat([df.reset_index(drop=True), results_df], axis=1)

    # Converte _raw_prob para percentil (0-10)
    scored_mask = combined["_raw_prob"].notna()
    if scored_mask.sum() > 0:
        all_probs = combined.loc[scored_mask, "_raw_prob"].tolist()
        combined.loc[scored_mask, "score"] = combined.loc[scored_mask, "_raw_prob"].apply(
            lambda p: round(percentileofscore(all_probs, p) / 10, 1)
        )
        # Recalcula tiers com base no score percentil
        def _tier_from_percentile(s: float) -> str:
            if s >= 7:
                return "Alta"
            if s >= 4:
                return "Média"
            return "Baixa"

        combined.loc[scored_mask, "tier"] = combined.loc[scored_mask, "score"].apply(
            _tier_from_percentile
        )

    return combined


# ---------------------------------------------------------------------------
# Detecção de risco por prazo
# ---------------------------------------------------------------------------

def flag_deadline_risk(df: pd.DataFrame, days: int = 7) -> pd.DataFrame:
    """
    Adiciona coluna 'deadline_risk': True para deals com close_date nos próximos
    `days` dias E score baixo (tier == 'Baixa' ou sem score).
    """
    today = pd.Timestamp(date.today())
    cutoff = today + timedelta(days=days)

    df = df.copy()
    df["close_date_ts"] = pd.to_datetime(df["close_date"], errors="coerce")

    df["deadline_risk"] = (
        df["close_date_ts"].between(today, cutoff, inclusive="both") &
        (df["tier"].isin(["Baixa"]) | df["alert"])
    )
    df.drop(columns=["close_date_ts"], inplace=True)
    return df
