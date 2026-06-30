"""
scoring/engine.py
-----------------
Orquestra os fatores e produz o score final 0-100 para cada deal.

Score máximo raw: 110 pts (25+25+20+15+15+10)
Normalizado para 0-100 no output final.
"""

import pandas as pd

from .factors import (
    factor_stage,
    factor_velocity,
    factor_account_fit,
    factor_product_win_rate,
    factor_agent_performance,
    factor_notes_activity,
)

FACTOR_FUNCTIONS = [
    factor_stage,
    factor_velocity,
    factor_account_fit,
    factor_product_win_rate,
    factor_agent_performance,
    factor_notes_activity,
]

MAX_RAW_SCORE = 110  # soma dos max_points: 25+25+20+15+15+10


# ---------------------------------------------------------------------------
# Funções principais
# ---------------------------------------------------------------------------

def score_deal(deal: pd.Series, metrics: dict) -> dict:
    """
    Calcula o score completo de uma oportunidade.

    Retorna:
    {
        "score": int (0-100),
        "tier": "hot" | "warm" | "cold",
        "action": str,
        "action_urgency": "high" | "medium" | "low",
        "factors": [...]
    }
    """
    factor_results = [fn(deal, metrics) for fn in FACTOR_FUNCTIONS]

    raw_score = sum(f["points"] for f in factor_results)

    # Normaliza para 0-100
    score = round(min((raw_score / MAX_RAW_SCORE) * 100, 100))

    tier = _classify_tier(score)
    action, urgency = _recommend_action(score, tier, factor_results, deal)

    return {
        "score":          score,
        "tier":           tier,
        "action":         action,
        "action_urgency": urgency,
        "factors":        factor_results,
    }


def score_pipeline(pipeline: pd.DataFrame, metrics: dict) -> pd.DataFrame:
    """
    Aplica score_deal a todo o pipeline e retorna o DataFrame
    enriquecido, ordenado por score decrescente.
    """
    results = []
    for _, row in pipeline.iterrows():
        scored = score_deal(row, metrics)
        results.append({
            **row.to_dict(),
            "score":          scored["score"],
            "tier":           scored["tier"],
            "action":         scored["action"],
            "action_urgency": scored["action_urgency"],
            "factors":        scored["factors"],
        })

    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values("score", ascending=False)
    return result_df


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _classify_tier(score: int) -> str:
    if score >= 70:
        return "hot"
    elif score >= 45:
        return "warm"
    else:
        return "cold"


def _recommend_action(
    score: int,
    tier: str,
    factors: list[dict],
    deal: pd.Series,
) -> tuple[str, str]:
    """
    Gera ação recomendada baseada no score e nos sinais dos fatores.
    Retorna (ação: str, urgência: "high" | "medium" | "low")
    """
    velocity_factor = next((f for f in factors if "Velocidade" in f["label"]), None)
    notes_factor    = next((f for f in factors if "contato" in f["label"]), None)

    velocity_signal = velocity_factor["signal"] if velocity_factor else "neutral"
    notes_signal    = notes_factor["signal"]    if notes_factor    else "neutral"

    stage            = deal.get("deal_stage", "")
    days_in_pipeline = deal.get("days_in_pipeline", 0)
    account          = deal.get("account", "essa conta")

    if tier == "hot" and (velocity_signal == "warning" or notes_signal == "warning"):
        return (
            f"🔥 Ligue HOJE para {account} — deal prioritário precisa de atenção imediata.",
            "high",
        )

    if tier == "hot" and stage == "Engaging":
        return (
            f"✅ Agende o próximo passo com {account} esta semana — deal quente e no ritmo.",
            "high",
        )

    if tier == "hot" and stage == "Prospecting":
        return (
            f"📞 Avance {account} para Engaging — conta de alto potencial ainda em prospecção.",
            "high",
        )

    if tier == "warm" and (velocity_signal == "warning" or notes_signal == "warning"):
        return (
            f"⚠ Reative contato com {account} — deal mornou, mas ainda vale o esforço.",
            "medium",
        )

    if tier == "warm":
        return (
            f"📋 Monitore {account} — deal com potencial médio, mantenha cadência.",
            "medium",
        )

    if tier == "cold" and velocity_signal == "warning":
        return (
            f"❄ Considere arquivar ou recualificar {account} — baixo score e parado há {days_in_pipeline} dias.",
            "low",
        )

    return (
        f"🔍 Reavalie {account} — baixo score, foque em deals mais prioritários primeiro.",
        "low",
    )