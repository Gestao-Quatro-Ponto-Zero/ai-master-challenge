import pandas as pd


def _safe_float(value) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def calculate_score(row, thresholds: dict) -> dict:
    score = 0
    reasons = []
    actions = []

    revenue = _safe_float(row.get("revenue"))
    close_value = _safe_float(row.get("close_value"))
    deal_stage = str(row.get("deal_stage", "")).strip()

    revenue_p75 = thresholds["revenue_p75"]
    revenue_p40 = thresholds["revenue_p40"]
    close_value_p75 = thresholds["close_value_p75"]
    close_value_p40 = thresholds["close_value_p40"]

    # 1. ICP aproximado pela receita da conta, calibrado por distribuição real
    if revenue >= revenue_p75:
        score += 25
        reasons.append("Conta no grupo de maior receita (alto potencial)")
    elif revenue >= revenue_p40:
        score += 10
        reasons.append("Conta com receita intermediária")
    else:
        score -= 5
        reasons.append("Conta com menor receita relativa")

    # 2. Impacto financeiro aproximado pelo valor do deal, calibrado por distribuição real
    if close_value >= close_value_p75:
        score += 25
        reasons.append("Deal no grupo de maior valor (alto impacto)")
    elif close_value >= close_value_p40:
        score += 15
        reasons.append("Deal com valor intermediário")
    else:
        score += 5
        reasons.append("Deal de menor valor relativo")

    # 3. Estágio do funil — somente estágios ativos
    stage_scores = {
        "Prospecting": 5,
        "Engaging": 10,
        "Proposal": 20,
        "Negotiating": 25,
    }

    if deal_stage in stage_scores:
        score += stage_scores[deal_stage]
        reasons.append(f"Estágio ativo: {deal_stage}")
    elif deal_stage in {"Won", "Lost"}:
        reasons.append(f"Estágio final: {deal_stage} (fora da priorização ativa)")
    else:
        reasons.append(f"Estágio não mapeado: {deal_stage}")

    # Classificação final
    if score >= 80:
        priority = "Alta"
        actions.append("Priorizar fechamento imediato")
    elif score >= 50:
        priority = "Média"
        actions.append("Nutrir e avançar")
    else:
        priority = "Baixa"
        actions.append("Baixa prioridade")

    return {
        "score": score,
        "priority": priority,
        "reasons": reasons,
        "actions": actions,
    }
