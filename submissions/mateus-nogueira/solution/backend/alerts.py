"""
Smart alerts: classify deals into alert categories and priority buckets.
Based on RevOps stale deal detection playbook ("2x avg stage time").
"""

from backend.data_loader import store


def classify_alert(deal: dict) -> dict | None:
    """
    Classify a deal into an alert category.
    Returns dict with type, label, icon, color, reason, actions.
    Returns None if no alert applies.
    """
    score = deal.get("score", 0)
    stage = deal.get("deal_stage", "")
    days = deal.get("days_in_pipeline", 0) or 0
    product = deal.get("product", "")
    sales_price = deal.get("sales_price") or 0
    agent = deal.get("sales_agent", "")

    if stage not in ("Prospecting", "Engaging"):
        return None

    avg_won = store.avg_days_won
    twice_avg = avg_won * 2

    # Priority order matters — return first match
    # Hot/Quick Win first (positive signals override time-based alerts)

    # 1. Hot opportunity (score alto + recente = prioridade máxima)
    if score >= 75 and stage == "Engaging" and days <= 40:
        return {
            "type": "hot",
            "label": "Oportunidade Quente",
            "icon": "flame",
            "color": "green",
            "reason": f"Pontuação alta ({score}) + oportunidade recente ({days:.0f} dias). Janela ideal de fechamento.",
            "actions": [
                "Priorizar esta oportunidade — agendar contato imediato",
                "Preparar proposta comercial",
                "Envolver o decisor se necessário",
            ],
        }

    # 2. Quick win (exige Engaging — Prospecting ainda não foi engajado)
    if score >= 70 and stage == "Engaging" and sales_price <= 1100 and days <= 30:
        return {
            "type": "quick_win",
            "label": "Vitoria Rapida",
            "icon": "zap",
            "color": "blue",
            "reason": f"Boa pontuação ({score}), produto acessível (${sales_price:,.0f}), oportunidade recente ({days:.0f}d). Fechamento rápido provável.",
            "actions": [
                "Fechar rapidamente para gerar ritmo de vendas",
                "Simplificar o processo de aprovação",
            ],
        }

    # 3. Stale deal (RevOps: > 2x avg stage time)
    if stage == "Engaging" and days > twice_avg:
        return {
            "type": "stale",
            "label": "Parado",
            "icon": "pause",
            "color": "gray",
            "reason": f"Há {days:.0f} dias em engajamento — mais de 2x a média ({avg_won:.0f}d). Negócios acima de 2x o tempo médio devem ser reavaliados.",
            "actions": [
                "Reavaliar se esta oportunidade ainda é viável",
                "Considerar reciclar o lead para nutrição",
                "Conversar com o prospect para entender o bloqueio",
            ],
        }

    # 4. Cooling deal (approaching 2x avg)
    if stage == "Engaging" and avg_won < days <= twice_avg:
        agent_stats = store.agent_stats.get(agent, {})
        agent_wr = agent_stats.get("win_rate", 0.5)
        return {
            "type": "cooling",
            "label": "Esfriando",
            "icon": "thermometer",
            "color": "orange",
            "reason": f"Há {days:.0f} dias no pipeline — acima da média de fechamento ({avg_won:.0f}d). Vendedor {agent} converte {agent_wr:.0%} dos negócios.",
            "actions": [
                "Contato urgente — a oportunidade está esfriando",
                "Revisar objeções levantadas pelo prospect",
                "Considerar oferta especial ou desconto para acelerar",
            ],
        }

    # 5. At risk (low score)
    if score < 35 and stage == "Engaging":
        return {
            "type": "at_risk",
            "label": "Em Risco",
            "icon": "alert-triangle",
            "color": "red",
            "reason": f"Pontuação baixa ({score}). Múltiplos fatores indicam baixa probabilidade de fechamento.",
            "actions": [
                "Reavaliar a abordagem de venda",
                "Verificar se o produto é adequado para este cliente",
                "Considerar redirecionar esforços para oportunidades com melhor potencial",
            ],
        }

    return None


def get_suggested_action(deal: dict) -> dict:
    """
    Return a suggested action for EVERY deal.
    If the deal has an alert, derives the action from it.
    Otherwise, falls back to score_label-based actions.
    """
    alert = deal.get("alert")
    score = deal.get("score", 0)
    score_label = deal.get("score_label", "Frio")
    stage = deal.get("deal_stage", "")
    days = deal.get("days_in_pipeline", 0) or 0

    # If deal has an alert, use its context for a more specific action
    if alert:
        action_map = {
            "hot": {
                "action": "Ligar agora",
                "detail": "Janela ideal de fechamento — agende contato imediato",
                "icon": "flame",
                "color": "green",
                "urgency": "alta",
            },
            "quick_win": {
                "action": "Fechar rápido",
                "detail": "Produto acessível + boa pontuação — simplifique a aprovação",
                "icon": "zap",
                "color": "blue",
                "urgency": "alta",
            },
            "cooling": {
                "action": "Follow-up urgente",
                "detail": "Oportunidade esfriando — retome contato e revise objeções",
                "icon": "thermometer",
                "color": "orange",
                "urgency": "alta",
            },
            "stale": {
                "action": "Reavaliar ou descartar",
                "detail": "Parado há muito tempo — converse com o prospect ou recicle o lead",
                "icon": "pause",
                "color": "gray",
                "urgency": "baixa",
            },
            "at_risk": {
                "action": "Mudar abordagem",
                "detail": "Baixa probabilidade — reavalie produto e perfil do cliente",
                "icon": "alert-triangle",
                "color": "red",
                "urgency": "media",
            },
        }
        return action_map.get(alert["type"], _fallback_action(score_label, stage, days))

    # Fallback: action based on score label
    return _fallback_action(score_label, stage, days)


def _fallback_action(score_label: str, stage: str, days: float) -> dict:
    """Generate a suggested action based on score label when no alert exists."""
    if score_label == "Quente":
        return {
            "action": "Avançar para proposta",
            "detail": "Pontuação alta — prepare proposta e busque o decisor",
            "icon": "arrow-up",
            "color": "green",
            "urgency": "alta",
        }
    elif score_label == "Morno":
        if stage == "Prospecting":
            return {
                "action": "Iniciar engajamento",
                "detail": "Bom potencial — faça o primeiro contato e qualifique",
                "icon": "message",
                "color": "yellow",
                "urgency": "media",
            }
        return {
            "action": "Agendar follow-up",
            "detail": "Potencial moderado — mantenha contato e nutra o relacionamento",
            "icon": "calendar",
            "color": "yellow",
            "urgency": "media",
        }
    elif score_label == "Frio":
        return {
            "action": "Qualificar melhor",
            "detail": "Potencial baixo — investigue se há fit real antes de investir mais tempo",
            "icon": "search",
            "color": "orange",
            "urgency": "baixa",
        }
    else:  # Congelado
        return {
            "action": "Considerar descarte",
            "detail": "Probabilidade muito baixa — redirecione esforços para deals melhores",
            "icon": "x-circle",
            "color": "red",
            "urgency": "baixa",
        }


def assign_priority_bucket(deal: dict) -> str:
    """
    Assign a deal to a priority bucket for the Monday Morning view.
    Returns: 'fechar_agora', 'nutrir', or 'repensar'.
    """
    score = deal.get("score", 0)
    stage = deal.get("deal_stage", "")
    days = deal.get("days_in_pipeline", 0) or 0

    if stage not in ("Prospecting", "Engaging"):
        return "historico"

    alert = deal.get("alert")
    alert_type = alert["type"] if alert else None

    # Deals marcados como stale/cooling não devem ir para "fechar_agora"
    if alert_type in ("stale", "cooling"):
        return "repensar" if score < 40 else "nutrir"

    if score >= 70 and stage == "Engaging" and days <= 60:
        return "fechar_agora"
    elif score >= 40:
        return "nutrir"
    else:
        return "repensar"


def enrich_deals_with_alerts(deals: list[dict]) -> list[dict]:
    """Add alert, priority_bucket, and suggested_action to each deal."""
    for deal in deals:
        alert = classify_alert(deal)
        deal["alert"] = alert
        deal["priority_bucket"] = assign_priority_bucket(deal)
        deal["suggested_action"] = get_suggested_action(deal)
    return deals
