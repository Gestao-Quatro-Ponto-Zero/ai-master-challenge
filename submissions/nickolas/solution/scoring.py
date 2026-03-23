def calculate_score(deal):
    score = 0
    reasons = []
    actions = []

    # 1. ICP Fit (QUEM é o cliente)
    if deal["icp_fit"] == "high":
        score += 25
        reasons.append("Cliente ideal (ICP perfeito)")
    elif deal["icp_fit"] == "medium":
        score += 10
        reasons.append("Fit razoável com ICP")
    else:
        score -= 10
        reasons.append("Fora do ICP")

    # 2. Dor (O TAMANHO DO PROBLEMA)
    if deal["pain_level"] == "high":
        score += 30
        reasons.append("Dor crítica (perda real de dinheiro)")
    elif deal["pain_level"] == "medium":
        score += 15
        reasons.append("Dor relevante")
    else:
        score += 0
        reasons.append("Baixa dor (pouca urgência real)")

    # 3. Timing (QUANDO ele quer resolver)
    if deal["urgency"] == "high":
        score += 20
        reasons.append("Cliente quer resolver agora")
    elif deal["urgency"] == "medium":
        score += 10
        reasons.append("Interesse ativo")
    else:
        score -= 5
        reasons.append("Sem urgência clara")

    # 4. Estágio do funil (QUÃO PERTO DA VENDA)
    stage_scores = {
        "discovery": 5,
        "engaging": 10,
        "proposal": 20,
        "negotiation": 25
    }

    stage_score = stage_scores.get(deal["stage"], 0)
    score += stage_score
    reasons.append(f"Estágio: {deal['stage']}")

    # 5. Autoridade (TEM QUEM DECIDE?)
    if not deal["has_decision_maker"]:
        score -= 20
        reasons.append("Sem decisor → alto risco de travar")
        actions.append("Mapear decisor e envolver ASAP")
    else:
        score += 10
        reasons.append("Decisor envolvido")

    # 6. Atividade (DEAL VIVO OU MORTO?)
    if deal["last_activity_days"] <= 3:
        score += 10
        reasons.append("Deal ativo recentemente")
    elif deal["last_activity_days"] > 10:
        score -= 15
        reasons.append("Deal esfriando")
        actions.append("Reengajar urgente")

    # 🎯 Classificação final
    if score >= 80:
        priority = "🔥 Alta"
        actions.append("Prioridade máxima: tentar fechar")
    elif score >= 50:
        priority = "⚡ Média"
        actions.append("Nutrir e avançar")
    else:
        priority = "🧊 Baixa"
        actions.append("Baixa prioridade")

    return {
        "score": score,
        "priority": priority,
        "reasons": reasons,
        "actions": actions
    }
