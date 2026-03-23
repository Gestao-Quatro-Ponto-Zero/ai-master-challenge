from datetime import datetime

def calculate_score(deal, account):
    score = 0
    reasons = []
    actions = []

    # =========================
    # 1. ICP (baseado na conta)
    # =========================
    if account["revenue"] > 1000000:
        score += 25
        reasons.append("Empresa grande (alto potencial)")
    elif account["revenue"] > 300000:
        score += 10
        reasons.append("Empresa média")
    else:
        score -= 5
        reasons.append("Empresa pequena")

    # =========================
    # 2. Valor do deal (proxy de dor)
    # =========================
    if deal["close_value"] > 3000:
        score += 25
        reasons.append("Alto valor (impacto relevante)")
    elif deal["close_value"] > 1000:
        score += 15
        reasons.append("Valor médio")
    else:
        score += 5
        reasons.append("Baixo valor")

    # =========================
    # 3. Estágio do funil
    # =========================
    stage_scores = {
        "Prospecting": 5,
        "Engaging": 10,
        "Won": 30,
        "Lost": -20,
    }

    stage = deal["deal_stage"]
    score += stage_scores.get(stage, 0)
    reasons.append(f"Estágio: {stage}")

    # =========================
    # 4. Tempo até fechamento (timing)
    # =========================
    if deal["engage_date"] and deal["close_date"]:
        engage = datetime.strptime(deal["engage_date"], "%Y-%m-%d")
        close = datetime.strptime(deal["close_date"], "%Y-%m-%d")

        days = (close - engage).days

        if days <= 10:
            score += 20
            reasons.append("Ciclo rápido (urgente)")
        elif days <= 30:
            score += 10
            reasons.append("Ciclo médio")
        else:
            score -= 5
            reasons.append("Ciclo lento")

    # =========================
    # Classificação final
    # =========================
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
