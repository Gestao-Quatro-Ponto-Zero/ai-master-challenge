from datetime import datetime
import pandas as pd


def _safe_float(value) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_date(value):
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.to_pydatetime()


def calculate_score(row):
    score = 0
    reasons = []
    actions = []

    revenue = _safe_float(row.get("revenue"))
    close_value = _safe_float(row.get("close_value"))
    deal_stage = str(row.get("deal_stage", "")).strip()

    engage_date = _parse_date(row.get("engage_date"))
    close_date = _parse_date(row.get("close_date"))

    # 1. ICP aproximado pela receita da conta
    if revenue > 1_000_000:
        score += 25
        reasons.append("Empresa grande (alto potencial)")
    elif revenue > 300_000:
        score += 10
        reasons.append("Empresa média")
    else:
        score -= 5
        reasons.append("Empresa pequena")

    # 2. Impacto financeiro aproximado pelo valor do deal
    if close_value > 3000:
        score += 25
        reasons.append("Alto valor (impacto relevante)")
    elif close_value > 1000:
        score += 15
        reasons.append("Valor médio")
    else:
        score += 5
        reasons.append("Baixo valor")

    # 3. Estágio do funil
    stage_scores = {
        "Prospecting": 5,
        "Engaging": 10,
        "Won": 30,
        "Lost": -20,
    }
    score += stage_scores.get(deal_stage, 0)
    reasons.append(f"Estágio: {deal_stage}")

    # 4. Timing baseado no ciclo entre engage e close
    if engage_date and close_date:
        days = (close_date - engage_date).days

        if days <= 10:
            score += 20
            reasons.append("Ciclo rápido (urgente)")
        elif days <= 30:
            score += 10
            reasons.append("Ciclo médio")
        else:
            score -= 5
            reasons.append("Ciclo lento")
    else:
        reasons.append("Sem datas suficientes para avaliar timing")

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
