def calculate_score(deal):
    score = 0
    reasons = []
    actions = []

    # 1. ICP Fit
    if deal["icp_fit"] == "high":
        score += 20
        reasons.append("Alto fit com ICP")
    elif deal["icp_fit"] == "medium":
        score += 10
        reasons.append("Fit médio com ICP")

    # 2. Dor / impacto
    if deal["pain_level"] == "high":
        score += 25
        reasons.append("Dor crítica com alto impacto")
    elif deal["pain_level"] == "medium":
        score += 15
        reasons.append("Dor relevante")

    # 3. Urgência / timing
    if deal["urgency"] == "high":
        score += 20
        reasons.append("Timing urgente")
    elif deal["urgency"] == "medium":
        score += 10
        reasons.append("Timing moderado")

    # 4. Estágio do funil
    stage_scores = {
        "discovery": 5,
        "engaging": 10,
        "proposal": 20,
        "negotiation": 18
    }
    score += stage_scores.get(deal["stage"], 0)
    reasons.append(f"Estágio: {deal['stage']}")

    # 5. Autoridade / risco
    if not deal["has_decision_maker"]:
        score -= 15
        reasons.append("Sem decisor envolvido")
        actions.append("Mapear e acessar decisor")

    # 6. Atividade recente
    if deal["last_activity_days"] <= 3:
        score += 10
        reasons.append("Atividade recente")
    elif deal["last_activity_days"] > 10:
        score -= 10
        reasons.append("Deal parado")
        actions.append("Reengajar cliente imediatamente")

    # Prioridade final
    if score >= 70:
        priority = "Alta"
        actions.append("Atacar hoje")
    elif score >= 40:
        priority = "Média"
        actions.append("Acompanhar de perto")
    else:
        priority = "Baixa"
        actions.append("Baixa prioridade no momento")

    return {
        "score": score,
        "priority": priority,
        "reasons": reasons,
        "actions": actions
    }
