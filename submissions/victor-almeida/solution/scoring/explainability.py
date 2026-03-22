"""
Geracao de textos explicativos para o Score Breakdown.

Cada deal recebe um breakdown dict com scores, pesos e textos humanos
que explicam POR QUE o deal tem aquele score.
"""

from __future__ import annotations

from scoring.constants import WEIGHTS


# ---------------------------------------------------------------------------
# Component detail generators
# ---------------------------------------------------------------------------


def generate_stage_detail(deal_stage: str) -> str:
    """Gera texto explicativo para o componente de stage."""
    if deal_stage == "Prospecting":
        return "Deal em Prospecting — ainda em qualificacao"
    if deal_stage == "Engaging":
        return "Deal em Engaging — ja qualificado"
    return f"Deal em {deal_stage}"


def generate_value_detail(score: float, product: str, value: float) -> str:
    """Gera texto explicativo para o componente de valor esperado."""
    if score > 75:
        return f"Valor alto ({product}, ${value:,.0f})"
    if score >= 25:
        return f"Valor medio ({product}, ${value:,.0f})"
    return f"Valor baixo ({product}, ${value:,.0f})"


def generate_velocity_detail(
    deal_stage: str,
    days: int | None,
    label: str,
    ratio: float | None,
    reference: int | None,
) -> str:
    """Gera texto explicativo para o componente de velocidade."""
    if deal_stage == "Prospecting":
        return "Em Prospecting — sem dados temporais disponiveis"

    if label == "saudavel":
        return f"{days} dias em Engaging (saudavel, ref: {reference} dias)"
    if label == "atencao":
        return f"{days} dias em Engaging — ficando lento (ref: {reference} dias)"
    if label == "alerta":
        return f"Parado ha {days} dias — risco de esfriar"
    if label == "candidato_zumbi":
        return f"Parado ha {days} dias — {ratio}x acima do esperado"
    if label == "quase_morto":
        return f"ALERTA: {days} dias parado — {ratio}x acima do esperado"
    if label == "sem_referencia":
        return "Sem dados temporais para avaliar velocidade"

    return f"{days} dias em {deal_stage}"


def generate_seller_fit_detail(metadata: dict) -> str:
    """Gera texto explicativo para o componente de seller fit."""
    reason = metadata.get("reason", "")

    if reason == "sem_setor":
        return "Deal sem conta associada — fit neutro"
    if reason == "dados_insuficientes":
        n = metadata.get("n", 0)
        min_deals = metadata.get("min", 5)
        return f"Poucos deals neste setor para avaliar fit ({n} de {min_deals} necessarios)"
    if reason == "sem_referencia_time":
        return "Sem referencia do time neste setor"
    if reason == "calculado":
        seller_wr = metadata.get("seller_wr", 0.0)
        team_wr = metadata.get("team_wr", 0.0)
        if seller_wr > team_wr:
            return (
                f"Seu WR neste setor ({seller_wr:.1%}) esta acima da media do time ({team_wr:.1%})"
            )
        return (
            f"Seu WR neste setor ({seller_wr:.1%}) esta abaixo da media do time ({team_wr:.1%})"
        )

    return "Informacao de seller fit indisponivel"


def generate_account_health_detail(metadata: dict) -> str:
    """Gera texto explicativo para o componente de saude da conta."""
    reason = metadata.get("reason", "")

    if reason == "sem_conta":
        return "Deal sem conta associada — saude neutra"
    if reason == "dados_insuficientes":
        n = metadata.get("n", 0)
        return f"Pouco historico desta conta ({n} deals)"
    if reason == "calculado":
        winrate = metadata.get("winrate", 0.0)
        total = metadata.get("total", 0)
        losses = metadata.get("losses", 0)
        recent_losses = metadata.get("recent_losses", 0)

        if winrate >= 0.65:
            return f"Conta com bom historico ({winrate:.1%} WR em {total} deals)"
        if winrate >= 0.40:
            return f"Conta com historico mediano ({winrate:.1%} WR em {total} deals)"

        detail = f"Conta com historico desfavoravel ({winrate:.1%} WR, {losses} perdidos)"
        if recent_losses > 0:
            detail += f" — {recent_losses} perdas recentes"
        return detail

    return "Informacao de saude da conta indisponivel"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _generate_zombie_detail(
    is_zombie: bool,
    is_critical_zombie: bool,
    days: int | None,
    ratio: float | None,
) -> str:
    """Gera texto explicativo para flags de deal zumbi."""
    if is_critical_zombie:
        return f"ZUMBI CRITICO: {days} dias parado ({ratio}x ref) — alto valor inflando pipeline"
    if is_zombie:
        return f"ZUMBI: {days} dias parado ({ratio}x acima da referencia de 88 dias)"
    return ""


# ---------------------------------------------------------------------------
# Main breakdown assembler
# ---------------------------------------------------------------------------


def generate_score_breakdown(
    score_final: float,
    score_stage: float,
    score_value: float,
    score_velocity: float,
    score_seller_fit: float,
    score_account_health: float,
    deal_stage: str,
    product: str,
    effective_value: float,
    velocity_days: int | None,
    velocity_label: str,
    velocity_ratio: float | None,
    velocity_reference: int | None,
    seller_fit_metadata: dict,
    account_health_metadata: dict,
    is_zombie: bool,
    is_critical_zombie: bool,
) -> dict:
    """Monta o dict completo de breakdown para um deal.

    Retorna estrutura com score final, componentes detalhados e flags.
    """
    return {
        "score_final": score_final,
        "components": {
            "stage": {
                "score": score_stage,
                "weight": WEIGHTS["stage"],
                "weighted": round(score_stage * WEIGHTS["stage"], 1),
                "detail": generate_stage_detail(deal_stage),
            },
            "expected_value": {
                "score": round(score_value, 1),
                "weight": WEIGHTS["expected_value"],
                "weighted": round(score_value * WEIGHTS["expected_value"], 1),
                "detail": generate_value_detail(score_value, product, effective_value),
            },
            "velocity": {
                "score": score_velocity,
                "weight": WEIGHTS["velocity"],
                "weighted": round(score_velocity * WEIGHTS["velocity"], 1),
                "detail": generate_velocity_detail(
                    deal_stage, velocity_days, velocity_label, velocity_ratio, velocity_reference
                ),
                "ratio": velocity_ratio,
                "label": velocity_label,
            },
            "seller_fit": {
                "score": score_seller_fit,
                "weight": WEIGHTS["seller_fit"],
                "weighted": round(score_seller_fit * WEIGHTS["seller_fit"], 1),
                "detail": generate_seller_fit_detail(seller_fit_metadata),
            },
            "account_health": {
                "score": score_account_health,
                "weight": WEIGHTS["account_health"],
                "weighted": round(score_account_health * WEIGHTS["account_health"], 1),
                "detail": generate_account_health_detail(account_health_metadata),
            },
        },
        "flags": {
            "is_zombie": is_zombie,
            "is_critical_zombie": is_critical_zombie,
            "zombie_detail": (
                _generate_zombie_detail(is_zombie, is_critical_zombie, velocity_days, velocity_ratio)
                if is_zombie
                else None
            ),
        },
    }


# ---------------------------------------------------------------------------
# Summary text generator
# ---------------------------------------------------------------------------


def generate_summary_text(breakdown: dict) -> str:
    """Gera resumo em uma linha combinando informacoes-chave do breakdown."""
    score = breakdown["score_final"]
    components = breakdown["components"]

    stage_detail = components["stage"]["detail"]
    velocity = components["velocity"]
    value_detail = components["expected_value"]["detail"]

    days = velocity.get("ratio") is not None
    velocity_label = velocity.get("label", "")

    # Build velocity snippet
    if velocity_label and velocity_label != "sem_referencia":
        velocity_snippet = velocity["detail"]
    else:
        velocity_snippet = stage_detail

    # Pick the most informative secondary detail
    seller_fit_detail = components["seller_fit"]["detail"]
    account_health_detail = components["account_health"]["detail"]

    # Prefer whichever has a stronger signal (not neutral/default)
    if "neutro" not in seller_fit_detail and "indisponivel" not in seller_fit_detail:
        secondary = seller_fit_detail
    elif "neutra" not in account_health_detail and "indisponivel" not in account_health_detail:
        secondary = account_health_detail
    else:
        secondary = ""

    parts = [f"Score {score:.0f}", velocity_snippet, value_detail]
    if secondary:
        parts.append(secondary)

    return " — ".join(parts[:2]) + ". " + ". ".join(parts[2:]) + "."
