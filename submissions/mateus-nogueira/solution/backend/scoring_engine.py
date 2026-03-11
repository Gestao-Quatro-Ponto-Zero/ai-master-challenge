"""
Scoring engine: hybrid scoring with 5 explainable components (0-100).
Calibrated on historical Won/Lost data following RevOps best practices.
"""

import math
from backend.data_loader import store


def normalize(value: float, min_val: float, max_val: float) -> float:
    """Normalize a value to 0-1 range, clamped."""
    if max_val == min_val:
        return 0.5
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def score_product_fit(product: str, sector: str | None) -> dict:
    """
    Component 1: Product Fit (0-25 pts)
    Based on historical win rate for product × sector combination.
    RevOps Explicit Scoring (Fit) framework.
    """
    max_score = 25

    # Global min/max win rates for normalization
    all_wr = list(store.product_sector_winrate.values()) + list(store.product_winrate.values())
    wr_min = min(all_wr) if all_wr else 0.5
    wr_max = max(all_wr) if all_wr else 0.7

    if sector and (product, sector) in store.product_sector_winrate:
        combo_wr = store.product_sector_winrate[(product, sector)]
        score = normalize(combo_wr, wr_min, wr_max) * max_score
        overall_wr = store.product_winrate.get(product, store.overall_winrate)
        if combo_wr > overall_wr:
            detail = f"{product} converte {combo_wr:.0%} no setor {sector} (acima da média geral de {overall_wr:.0%})"
        else:
            detail = f"{product} converte {combo_wr:.0%} no setor {sector} (média geral: {overall_wr:.0%})"
    elif product in store.product_winrate:
        product_wr = store.product_winrate[product]
        score = normalize(product_wr, wr_min, wr_max) * max_score * 0.85
        if sector:
            detail = f"{product} converte {product_wr:.0%} no geral (poucos dados para o setor {sector})"
        else:
            detail = f"{product} converte {product_wr:.0%} no geral (conta não identificada)"
    else:
        score = max_score * 0.5
        detail = f"Produto {product}: dados insuficientes para avaliação"

    return {"name": "Adequação do Produto", "score": round(score, 1), "max": max_score, "detail": detail}


def score_pipeline_timing(deal_stage: str, days_in_pipeline: float | None) -> dict:
    """
    Component 2: Pipeline Timing (0-25 pts)
    Based on days in pipeline vs historical averages.
    Strongest predictive signal in the dataset.
    """
    max_score = 25

    if deal_stage == "Prospecting" or days_in_pipeline is None:
        score = 20.0
        detail = "Lead em prospecção — alto potencial, ainda não engajado"
        return {"name": "Tempo no Pipeline", "score": score, "max": max_score, "detail": detail}

    days = float(days_in_pipeline)
    avg_won = store.avg_days_won

    # Piecewise scoring curve
    if days <= 30:
        score = 25.0
        detail = f"Há {days:.0f} dias em engajamento — dentro da janela ideal de venda"
    elif days <= avg_won:
        score = 25.0 - (days - 30) / (avg_won - 30) * 7  # 25 -> 18
        detail = f"Há {days:.0f} dias no pipeline (média de fechamento: {avg_won:.0f} dias — ainda em bom ritmo)"
    elif days <= 80:
        score = 18.0 - (days - avg_won) / (80 - avg_won) * 8  # 18 -> 10
        detail = f"Há {days:.0f} dias — passou a média de {avg_won:.0f} dias dos negócios ganhos"
    elif days <= 120:
        score = 10.0 - (days - 80) / 40 * 7  # 10 -> 3
        detail = f"Há {days:.0f} dias — muito acima da média ({avg_won:.0f}d). Risco de esfriar"
    else:
        score = max(0.0, 3.0 - (days - 120) / 60 * 3)  # 3 -> 0
        detail = f"Há {days:.0f} dias — extremamente acima da média. Considerar reavaliação"

    return {"name": "Tempo no Pipeline", "score": round(max(0, score), 1), "max": max_score, "detail": detail}


def score_account_quality(account: str | None, sector: str | None,
                          revenue: float | None, employees: float | None) -> dict:
    """
    Component 3: Account Quality (0-20 pts)
    Firmographic scoring following RevOps Explicit Scoring framework.
    """
    max_score = 20

    if not account or account == "" or (isinstance(account, float) and math.isnan(account)):
        return {
            "name": "Qualidade da Conta",
            "score": 5.0,
            "max": max_score,
            "detail": "Conta não identificada — pontuação neutra aplicada",
        }

    parts = []
    total = 0.0

    # a) Revenue score (0-5 pts)
    if revenue is not None and not _is_nan(revenue):
        rev_score = normalize(revenue, store.revenue_min, store.revenue_max) * 5
        total += rev_score
        parts.append(f"receita ${revenue:.0f}M")
    else:
        total += 2.5
        parts.append("receita não informada")

    # b) Employees score (0-3 pts)
    if employees is not None and not _is_nan(employees):
        emp_score = normalize(employees, store.employees_min, store.employees_max) * 3
        total += emp_score
        parts.append(f"{employees:.0f} funcionarios")
    else:
        total += 1.5

    # c) Historical win rate at account (0-8 pts) — strongest signal
    acct_stats = store.account_stats.get(account)
    if acct_stats:
        acct_wrs = [s["win_rate"] for s in store.account_stats.values()]
        acct_wr_min = min(acct_wrs)
        acct_wr_max = max(acct_wrs)
        wr = acct_stats["win_rate"]
        wr_score = normalize(wr, acct_wr_min, acct_wr_max) * 8
        total += wr_score

        if wr > store.overall_winrate:
            parts.append(f"taxa de conversão histórica {wr:.0%} (acima da média)")
        else:
            parts.append(f"taxa de conversão histórica {wr:.0%}")
    else:
        total += 4.0
        parts.append("sem histórico de negócios")

    # d) Deal volume at account (0-4 pts) — relationship depth
    if acct_stats and acct_stats["total_deals"] > 0:
        max_vol = max(s["total_deals"] for s in store.account_stats.values())
        vol_score = (math.log1p(acct_stats["total_deals"]) / math.log1p(max_vol)) * 4
        total += vol_score
    else:
        total += 1.0

    detail = f"{account}: {', '.join(parts)}"
    return {"name": "Qualidade da Conta", "score": round(min(total, max_score), 1), "max": max_score, "detail": detail}


def score_agent_performance(agent: str) -> dict:
    """
    Component 4: Agent Performance (0-20 pts)
    Based on individual agent's win rate, deal volume, and average deal size.
    """
    max_score = 20
    stats = store.agent_stats.get(agent)

    if not stats:
        return {
            "name": "Desempenho do Vendedor",
            "score": 10.0,
            "max": max_score,
            "detail": f"{agent}: sem histórico de negócios fechados",
        }

    parts = []
    total = 0.0

    # a) Win rate (0-12 pts)
    wr = stats["win_rate"]
    wr_score = normalize(wr, store.agent_wr_min, store.agent_wr_max) * 12
    total += wr_score

    if wr >= store.agent_wr_max * 0.95:
        parts.append(f"taxa de conversão {wr:.0%} (melhor da equipe)")
    elif wr > store.overall_winrate:
        parts.append(f"taxa de conversão {wr:.0%} (acima da média)")
    else:
        parts.append(f"taxa de conversão {wr:.0%}")

    # b) Deal volume confidence (0-4 pts)
    vol_score = min(stats["total_deals"] / store.agent_volume_max, 1.0) * 4
    total += vol_score

    # c) Average deal value (0-4 pts)
    if stats["avg_deal_value"] > 0:
        val_score = normalize(
            stats["avg_deal_value"],
            store.agent_avg_val_min,
            store.agent_avg_val_max,
        ) * 4
        total += val_score
        parts.append(f"ticket médio ${stats['avg_deal_value']:,.0f}")
    else:
        total += 2.0

    detail = f"{agent}: {', '.join(parts)}"
    return {"name": "Desempenho do Vendedor", "score": round(min(total, max_score), 1), "max": max_score, "detail": detail}


def score_deal_value(product: str, close_value: float | None, deal_stage: str) -> dict:
    """
    Component 5: Deal Value Alignment (0-10 pts)
    How close the expected/actual value is to the product's list price.
    """
    max_score = 10
    sales_price = store.product_prices.get(product, 0)

    if deal_stage in ("Prospecting", "Engaging") or close_value is None or _is_nan(close_value) or close_value == 0:
        # For active deals, default based on product price tier
        if sales_price >= 5000:
            score = 8.0
            detail = f"Produto premium (${sales_price:,.0f}) — alto potencial de receita"
        elif sales_price >= 500:
            score = 7.0
            detail = f"Produto de valor intermediário (${sales_price:,.0f})"
        else:
            score = 6.0
            detail = f"Produto de entrada (${sales_price:,.0f}) — volume é o diferencial"
        return {"name": "Valor da Oportunidade", "score": score, "max": max_score, "detail": detail}

    # For closed deals with actual close_value
    if sales_price > 0:
        ratio = close_value / sales_price
        if 0.85 <= ratio <= 1.15:
            score = 10.0
            detail = f"Valor ${close_value:,.0f} alinhado com o preço de tabela ${sales_price:,.0f}"
        elif 0.70 <= ratio <= 1.30:
            score = 7.0
            detail = f"Valor ${close_value:,.0f} com leve desvio do preço ${sales_price:,.0f}"
        else:
            score = 4.0
            detail = f"Valor ${close_value:,.0f} muito diferente do preço de tabela ${sales_price:,.0f}"
    else:
        score = 5.0
        detail = "Preço de referência indisponível"

    return {"name": "Valor da Oportunidade", "score": score, "max": max_score, "detail": detail}


def calculate_score(row: dict) -> dict:
    """
    Calculate total score (0-100) for a deal with all 5 component breakdowns.
    Returns dict with score, label, components, and estimated_value.
    """
    components = [
        score_product_fit(row.get("product", ""), row.get("sector")),
        score_pipeline_timing(row.get("deal_stage", ""), row.get("days_in_pipeline")),
        score_account_quality(
            row.get("account"), row.get("sector"),
            row.get("revenue"), row.get("employees"),
        ),
        score_agent_performance(row.get("sales_agent", "")),
        score_deal_value(
            row.get("product", ""), row.get("close_value"),
            row.get("deal_stage", ""),
        ),
    ]

    total = sum(c["score"] for c in components)
    total = round(min(100, max(0, total)), 1)

    # Score label
    if total >= 75:
        label = "Quente"
    elif total >= 55:
        label = "Morno"
    elif total >= 35:
        label = "Frio"
    else:
        label = "Congelado"

    # Estimated value for active deals
    sales_price = store.product_prices.get(row.get("product", ""), 0)
    if row.get("deal_stage") in ("Prospecting", "Engaging"):
        estimated_value = round(sales_price * (total / 100), 2)
    else:
        estimated_value = row.get("close_value", 0) or 0

    return {
        "score": total,
        "label": label,
        "components": components,
        "estimated_value": estimated_value,
    }


def score_all_deals() -> list[dict]:
    """
    Score all deals in the enriched pipeline.
    Returns list of deal dicts with scores attached.
    """
    results = []
    df = store.df_enriched

    for _, row in df.iterrows():
        row_dict = row.to_dict()
        score_result = calculate_score(row_dict)

        deal = {
            "opportunity_id": row_dict.get("opportunity_id", ""),
            "sales_agent": row_dict.get("sales_agent", ""),
            "product": row_dict.get("product", ""),
            "account": row_dict.get("account") if not _is_nan(row_dict.get("account")) else None,
            "deal_stage": row_dict.get("deal_stage", ""),
            "engage_date": _format_date(row_dict.get("engage_date")),
            "close_date": _format_date(row_dict.get("close_date")),
            "close_value": row_dict.get("close_value") if not _is_nan(row_dict.get("close_value")) else None,
            "days_in_pipeline": int(row_dict["days_in_pipeline"]) if not _is_nan(row_dict.get("days_in_pipeline")) else 0,
            "sector": row_dict.get("sector") if not _is_nan(row_dict.get("sector")) else None,
            "revenue": row_dict.get("revenue") if not _is_nan(row_dict.get("revenue")) else None,
            "employees": int(row_dict.get("employees")) if not _is_nan(row_dict.get("employees")) else None,
            "manager": row_dict.get("manager") if not _is_nan(row_dict.get("manager")) else None,
            "regional_office": row_dict.get("regional_office") if not _is_nan(row_dict.get("regional_office")) else None,
            "sales_price": row_dict.get("sales_price") if not _is_nan(row_dict.get("sales_price")) else None,
            "series": row_dict.get("series") if not _is_nan(row_dict.get("series")) else None,
            "score": score_result["score"],
            "score_label": score_result["label"],
            "components": score_result["components"],
            "estimated_value": score_result["estimated_value"],
        }
        results.append(deal)

    # Print calibration summary
    active = [d for d in results if d["deal_stage"] in ("Prospecting", "Engaging")]
    won = [d for d in results if d["deal_stage"] == "Won"]
    lost = [d for d in results if d["deal_stage"] == "Lost"]

    print(f"\n[ScoringEngine] Scored {len(results)} deals total")
    print(f"  Active deals: {len(active)}")
    _print_distribution("  Active", active)
    print(f"  Won deals (validation): {len(won)}")
    _print_distribution("  Won", won)
    print(f"  Lost deals (validation): {len(lost)}")
    _print_distribution("  Lost", lost)

    # RevOps calibration: what % of Won deals score above our thresholds?
    if won:
        won_scores = [d["score"] for d in won]
        pct_above_75 = sum(1 for s in won_scores if s >= 75) / len(won_scores) * 100
        pct_above_55 = sum(1 for s in won_scores if s >= 55) / len(won_scores) * 100
        print(f"\n  [Calibracao RevOps]")
        print(f"    {pct_above_75:.1f}% dos Won com score >= 75 (Quente)")
        print(f"    {pct_above_55:.1f}% dos Won com score >= 55 (Morno+)")

    if lost:
        lost_scores = [d["score"] for d in lost]
        pct_below_35 = sum(1 for s in lost_scores if s < 35) / len(lost_scores) * 100
        print(f"    {pct_below_35:.1f}% dos Lost com score < 35 (Congelado)")

    return results


def _print_distribution(prefix: str, deals: list):
    """Print score distribution summary."""
    if not deals:
        return
    labels = {"Quente": 0, "Morno": 0, "Frio": 0, "Congelado": 0}
    for d in deals:
        labels[d["score_label"]] = labels.get(d["score_label"], 0) + 1
    parts = [f"{k}: {v}" for k, v in labels.items()]
    print(f"  {prefix} distribution: {', '.join(parts)}")


def _is_nan(value) -> bool:
    """Check if a value is NaN (works for float and other types)."""
    if value is None:
        return True
    try:
        return math.isnan(float(value))
    except (ValueError, TypeError):
        return False


def _format_date(value) -> str | None:
    """Format a pandas Timestamp to ISO date string."""
    if value is None or (hasattr(value, 'isnull') and value.isnull()):
        return None
    try:
        import pandas as pd
        if pd.isna(value):
            return None
        return str(value.date()) if hasattr(value, 'date') else str(value)[:10]
    except (ValueError, TypeError):
        return None
