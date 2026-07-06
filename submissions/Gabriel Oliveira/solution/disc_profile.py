"""Inferencia DISC explicavel para Lead Scorer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


DISC_VALUES = {"D", "I", "S", "C", "indefinido"}


@dataclass
class DiscInference:
    disc_profile: str
    disc_confidence: int
    disc_rationale: str
    buying_signals: list[str]
    pain_points: list[str]
    objections: list[str]


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def infer_disc_profile(lead_row: pd.Series, today: pd.Timestamp) -> DiscInference:
    """Infere DISC com confianca 0-100 e racional em linguagem comercial.

    Regras usam apenas colunas reais:
    - deal_stage, engage_date, close_value
    - revenue, employees, acquisition_channel, has_trial
    - industry, product
    """
    stage = _safe_text(lead_row.get("deal_stage")).strip()
    channel = _safe_text(lead_row.get("acquisition_channel")).lower()
    industry = _safe_text(lead_row.get("industry"))
    product = _safe_text(lead_row.get("product"))
    revenue = _safe_float(lead_row.get("revenue"), 0.0)
    employees = _safe_float(lead_row.get("employees"), 0.0)
    close_value = _safe_float(lead_row.get("close_value"), 0.0)
    has_trial = bool(lead_row.get("has_trial", False))

    engage_date = pd.to_datetime(lead_row.get("engage_date"), errors="coerce")
    age_days = -1
    if pd.notna(engage_date):
        age_days = int((today - engage_date).days)

    missing_critical = []
    if not stage:
        missing_critical.append("deal_stage")
    if close_value <= 0:
        missing_critical.append("close_value")

    d_score = 0
    i_score = 0
    s_score = 0
    c_score = 0

    # Dominancia (D): foco em resultado, velocidade e impacto
    if stage == "Engaging":
        d_score += 2
    if close_value >= 10000:
        d_score += 2
    if revenue >= 2_000_000:
        d_score += 2
    if 0 <= age_days <= 45:
        d_score += 1

    # Influencia (I): abertura relacional e resposta a prova social
    if channel in {"social", "referral", "webinar"}:
        i_score += 2
    if has_trial:
        i_score += 1
    if stage == "Engaging":
        i_score += 1
    if 0 < close_value < 10000:
        i_score += 1

    # Estabilidade (S): ritmo constante, previsibilidade, seguranca
    if age_days >= 45:
        s_score += 2
    if has_trial:
        s_score += 1
    if stage == "Prospecting":
        s_score += 1
    if industry in {"Education", "Healthcare", "Public Sector"}:
        s_score += 1

    # Conformidade (C): criterio, risco e justificativa tecnica
    if revenue >= 3_000_000:
        c_score += 2
    if employees >= 500:
        c_score += 2
    if stage == "Prospecting":
        c_score += 1
    if channel in {"outbound", "partner"}:
        c_score += 1

    profile_scores = {"D": d_score, "I": i_score, "S": s_score, "C": c_score}
    ordered = sorted(profile_scores.items(), key=lambda x: x[1], reverse=True)
    best_profile, best_score = ordered[0]
    second_score = ordered[1][1]

    if missing_critical or best_score <= 1:
        reason = "Dados criticos insuficientes para inferencia robusta"
        if missing_critical:
            reason += f": {', '.join(missing_critical)}"
        return DiscInference(
            disc_profile="indefinido",
            disc_confidence=35,
            disc_rationale=(
                "Perfil DISC indefinido com os dados atuais. "
                f"{reason}. Recomendacao: confirmar contexto da oportunidade antes do contato."
            ),
            buying_signals=["Necessita validacao adicional"],
            pain_points=["Falta de sinal comportamental consistente"],
            objections=["Risco de abordagem desalinhada sem contexto"],
        )

    confidence = int(min(95, max(45, 55 + best_score * 8 + (best_score - second_score) * 5)))

    rational_map = {
        "D": (
            "Lead orientado a resultado e velocidade. "
            "Sinais: estagio avancado e potencial de impacto financeiro relevante."
        ),
        "I": (
            "Lead tende a responder melhor a abordagem relacional e narrativa de ganhos rapidos. "
            "Sinais: canal com componente social e abertura para conversa."
        ),
        "S": (
            "Lead favorece previsibilidade e seguranca na decisao. "
            "Sinais: ciclo mais longo e necessidade de reduzir risco percebido."
        ),
        "C": (
            "Lead tende a decisao analitica e comparativa. "
            "Sinais: conta maior, mais stakeholders e necessidade de justificativa tecnica."
        ),
    }

    signals = [
        f"Estagio atual: {stage or 'nao informado'}",
        f"Produto em pauta: {product or 'nao informado'}",
        f"Valor esperado: {close_value:,.0f}",
    ]

    pain_map = {
        "D": ["Percepcao de lentidao no processo", "Falta de clareza sobre impacto imediato"],
        "I": ["Mensagem fria ou impessoal", "Pouca clareza de proximo passo"],
        "S": ["Mudanca brusca sem seguranca", "Risco operacional nao enderecado"],
        "C": ["Argumento sem dados", "Ausencia de criterio de comparacao"],
    }
    objections_map = {
        "D": ["Nao vejo ganho rapido suficiente"],
        "I": ["Nao senti confianca no relacionamento"],
        "S": ["Ainda nao me sinto seguro para avancar"],
        "C": ["Falta evidencia tecnica para decidir"],
    }

    return DiscInference(
        disc_profile=best_profile,
        disc_confidence=confidence,
        disc_rationale=rational_map[best_profile],
        buying_signals=signals,
        pain_points=pain_map[best_profile],
        objections=objections_map[best_profile],
    )


def build_lead_profile(lead_row: pd.Series, today: pd.Timestamp) -> dict[str, Any]:
    """Constroi objeto de perfil do lead para follow-up e ganchos."""
    disc = infer_disc_profile(lead_row, today=today)

    engage_date = pd.to_datetime(lead_row.get("engage_date"), errors="coerce")
    days_in_stage = None
    if pd.notna(engage_date):
        days_in_stage = max(0, int((today - engage_date).days))

    profile = {
        "lead_id": _safe_text(lead_row.get("opportunity_id")),
        "lead_name": _safe_text(lead_row.get("account")) or None,
        "segment": _safe_text(lead_row.get("industry")) or None,
        "deal_stage": _safe_text(lead_row.get("deal_stage")) or None,
        "days_in_stage": days_in_stage,
        "close_value": _safe_float(lead_row.get("close_value"), 0.0),
        "owner": _safe_text(lead_row.get("sales_agent")) or None,
        "manager": _safe_text(lead_row.get("manager")) or None,
        "region": _safe_text(lead_row.get("regional_office")) or None,
        "disc_profile": disc.disc_profile,
        "disc_confidence": disc.disc_confidence,
        "disc_rationale": disc.disc_rationale,
        "pain_points": disc.pain_points,
        "objections": disc.objections,
        "buying_signals": disc.buying_signals,
        "next_best_action": None,
        "industry": _safe_text(lead_row.get("industry")) or None,
        "acquisition_channel": _safe_text(lead_row.get("acquisition_channel")) or None,
        "has_trial": bool(lead_row.get("has_trial", False)),
        "product": _safe_text(lead_row.get("product")) or None,
    }

    if profile["disc_profile"] not in DISC_VALUES:
        profile["disc_profile"] = "indefinido"
    return profile
