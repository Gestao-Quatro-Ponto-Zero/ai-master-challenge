def calculate_score(deal):
    score = 0
    reasons = []
    actions = []

    # 1. ICP Fit
    if deal["icp_fit"] == "high":
        score += 25
        reasons.append("Cliente ideal (ICP perfeito)")
    elif deal["icp_fit"] == "medium":
        score += 10
        reasons.append("Fit razoável com ICP")
    else:
        score -= 10
        reasons.append("Fora do ICP")

    # 2. Dor / impacto
    if deal["pain_level"] == "high":
        score += 30
        reasons.append("Dor crítica (perda real de dinheiro)")
    elif deal["pain_level"] == "medium":
        score += 15
        reasons.append("Dor relevante")
    else:
        reasons.append("Baixa dor")

    # 3. Urgência / timing
    if deal["urgency"] == "high":
        score += 20
        reasons.append("Timing urgente")
    elif deal["urgency"] == "medium":
        score += 10
        reasons.append("Interesse ativo")
    else:
        score -= 5
        reasons.append("Sem urgência clara")

    # 4. Estágio do funil
    stage_scores = {
        "discovery": 5,
        "engaging": 10,
        "proposal": 20,
        "negotiation": 25,
    }
    stage_score = stage_scores.get(deal["stage"], 0)
    score += stage_score
    reasons.append(f"Estágio: {deal['stage']}")

    # 5. Autoridade / risco
    if not deal["has_decision_maker"]:
        score -= 20
        reasons.append("Sem decisor envolvido")
        actions.append("Mapear e envolver o decisor")
    else:
        score += 10
        reasons.append("Decisor envolvido")

    # 6. Atividade recente
    if deal["last_activity_days"] <= 3:
        score += 10
        reasons.append("Atividade recente")
    elif deal["last_activity_days"] > 10:
        score -= 15
        reasons.append("Deal esfriando")
        actions.append("Reengajar urgente")

    # Classificação final
    if score >= 80:
        priority = "Alta"
        actions.append("Prioridade máxima: tentar fechar")
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
