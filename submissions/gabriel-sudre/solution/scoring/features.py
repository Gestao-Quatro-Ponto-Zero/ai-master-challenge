import os
import pandas as pd
import numpy as np
import math

# Configurable: use dataset max date for challenge, today() for production
_ref = os.getenv("REFERENCE_DATE", "2017-12-31")
REFERENCE_DATE = pd.Timestamp(_ref) if _ref != "auto" else pd.Timestamp.now()

DEFAULT_WEIGHTS = {
    "pipeline_aging": 0.22,
    "potential_value": 0.18,
    "win_rate_combined": 0.15,      # collapsed sector + product + account
    "account_fit": 0.12,
    "repeat_customer": 0.10,
    "agent_load": 0.10,             # pipeline concentration (NEW)
    "win_rate_account": 0.08,       # account-specific with confidence
    "agent_performance": 0.05,      # reduced from 0.12
}

CLAMP_MIN = 0.05
CLAMP_MAX = 0.95


def _clamp(value: float) -> float:
    return max(CLAMP_MIN, min(CLAMP_MAX, value))


def _safe_win_rate(won: int, total: int, default: float = 0.5) -> float:
    if total == 0:
        return default
    return won / total


def compute_global_stats(pipeline: pd.DataFrame, accounts: pd.DataFrame,
                         products: pd.DataFrame, teams: pd.DataFrame) -> dict:
    closed = pipeline[pipeline["deal_stage"].isin(["Won", "Lost"])]

    # Win rates by sector
    sector_map = accounts.set_index("id")["sector"].to_dict()
    closed_with_sector = closed.copy()
    closed_with_sector["sector"] = closed_with_sector["account_id"].map(sector_map)
    sector_stats = closed_with_sector.groupby("sector").apply(
        lambda g: _safe_win_rate((g["deal_stage"] == "Won").sum(), len(g)),
        include_groups=False,
    ).to_dict()

    # Win rates by product
    product_stats = closed.groupby("product_id").apply(
        lambda g: _safe_win_rate((g["deal_stage"] == "Won").sum(), len(g)),
        include_groups=False,
    ).to_dict()

    # Win rates by account (with deal count for confidence)
    account_deal_counts = closed.groupby("account_id").size().to_dict()
    account_stats = closed.groupby("account_id").apply(
        lambda g: _safe_win_rate((g["deal_stage"] == "Won").sum(), len(g)),
        include_groups=False,
    ).to_dict()

    # Win rates by agent
    agent_stats = closed.groupby("sales_agent_id").apply(
        lambda g: _safe_win_rate((g["deal_stage"] == "Won").sum(), len(g)),
        include_groups=False,
    ).to_dict()

    global_win_rate = _safe_win_rate(
        (closed["deal_stage"] == "Won").sum(), len(closed)
    )

    # Repeat customers
    won = pipeline[pipeline["deal_stage"] == "Won"]
    repeat_counts = won.groupby("account_id").size().to_dict()

    # Avg cycle
    engaging_history = closed[closed["engage_date"].notna() & closed["close_date"].notna()].copy()
    engaging_history["cycle_days"] = (engaging_history["close_date"] - engaging_history["engage_date"]).dt.days
    avg_cycle_by_product = engaging_history.groupby("product_id")["cycle_days"].mean().to_dict()
    global_avg_cycle = engaging_history["cycle_days"].mean() if len(engaging_history) > 0 else 60

    # Pipeline aging stats from ACTIVE deals
    active_engaging = pipeline[(pipeline["deal_stage"] == "Engaging") & pipeline["engage_date"].notna()]
    active_days = (REFERENCE_DATE - active_engaging["engage_date"]).dt.days
    aging_median = float(active_days.median()) if len(active_days) > 0 else 100
    aging_iqr = float(active_days.quantile(0.75) - active_days.quantile(0.25)) if len(active_days) > 0 else 100

    # Product prices
    max_price = products["sales_price"].max()
    product_prices = products.set_index("id")["sales_price"].to_dict()

    # Account fit - log-based
    max_revenue = accounts["revenue"].max()
    max_employees = accounts["employees"].max()
    log_max_revenue = math.log1p(float(max_revenue)) if pd.notna(max_revenue) and max_revenue else 1.0
    log_max_employees = math.log1p(float(max_employees)) if pd.notna(max_employees) and max_employees else 1.0

    # Repeat customer log
    max_repeats = max(repeat_counts.values()) if repeat_counts else 1
    log_max_repeats = math.log1p(max_repeats)

    # Agent pipeline load (active deals per agent)
    active = pipeline[pipeline["deal_stage"].isin(["Engaging", "Prospecting"])]
    agent_load = active.groupby("sales_agent_id").size().to_dict()
    avg_agent_load = float(np.mean(list(agent_load.values()))) if agent_load else 1
    std_agent_load = float(np.std(list(agent_load.values()))) if agent_load else 1
    max_agent_load = max(agent_load.values()) if agent_load else 1
    min_agent_load = min(agent_load.values()) if agent_load else 1

    # Medians for deals without account (fallback values)
    accounts_lookup = accounts.set_index("id").to_dict("index")
    all_rev = [float(v.get("revenue") or 0) for v in accounts_lookup.values() if pd.notna(v.get("revenue")) and v.get("revenue")]
    all_emp = [float(v.get("employees") or 0) for v in accounts_lookup.values() if pd.notna(v.get("employees")) and v.get("employees")]
    median_account_fit_rev = math.log1p(float(np.median(all_rev))) / log_max_revenue if all_rev and log_max_revenue > 0 else 0.5
    median_account_fit_emp = math.log1p(float(np.median(all_emp))) / log_max_employees if all_emp and log_max_employees > 0 else 0.5
    median_account_fit = (median_account_fit_rev + median_account_fit_emp) / 2

    all_repeats = list(repeat_counts.values())
    median_repeat = math.log1p(float(np.median(all_repeats))) / log_max_repeats if all_repeats and log_max_repeats > 0 else 0.5

    return {
        "sector_map": sector_map,
        "sector_stats": sector_stats,
        "product_stats": product_stats,
        "account_stats": account_stats,
        "account_deal_counts": account_deal_counts,
        "agent_stats": agent_stats,
        "global_win_rate": global_win_rate,
        "repeat_counts": repeat_counts,
        "avg_cycle_by_product": avg_cycle_by_product,
        "global_avg_cycle": global_avg_cycle,
        "aging_median": aging_median,
        "aging_iqr": aging_iqr,
        "product_prices": product_prices,
        "max_price": max_price,
        "log_max_price": math.log1p(float(max_price)) if max_price else 1.0,
        "max_revenue": max_revenue,
        "max_employees": max_employees,
        "log_max_revenue": log_max_revenue,
        "log_max_employees": log_max_employees,
        "log_max_repeats": log_max_repeats,
        "accounts_lookup": accounts_lookup,
        "agent_load": agent_load,
        "avg_agent_load": avg_agent_load,
        "std_agent_load": max(std_agent_load, 1),
        "max_agent_load": max_agent_load,
        "min_agent_load": min_agent_load,
        "median_account_fit": median_account_fit,
        "median_repeat": median_repeat,
    }


def compute_features(deal: pd.Series, stats: dict) -> dict:
    features = {}
    gwr = max(stats["global_win_rate"], 0.01)

    # --- pipeline_aging: sigmoid decay ---
    if deal["deal_stage"] == "Engaging" and pd.notna(deal["engage_date"]):
        days_in_engaging = (REFERENCE_DATE - deal["engage_date"]).days
        median = stats["aging_median"]
        iqr = max(stats["aging_iqr"], 1)
        z = (days_in_engaging - median) / (iqr * 0.75)
        features["pipeline_aging"] = _clamp(1 / (1 + math.exp(z)))
    else:
        # Prospecting = below neutral (colder than Engaging median)
        features["pipeline_aging"] = 0.30

    # --- win_rate_combined: collapsed sector + product (weighted avg) ---
    sector = stats["sector_map"].get(deal["account_id"], "indefinido")
    sector_wr = stats["sector_stats"].get(sector, gwr)
    product_wr = stats["product_stats"].get(deal["product_id"], gwr)
    combined_wr = (sector_wr + product_wr) / 2
    deviation = (combined_wr - gwr) / gwr
    features["win_rate_combined"] = _clamp(0.5 + deviation * 8)

    # --- win_rate_account: confidence-weighted ---
    account_wr = stats["account_stats"].get(deal["account_id"], gwr)
    account_deals = stats["account_deal_counts"].get(deal["account_id"], 0)
    confidence = min(1, account_deals / 10)
    deviation = (account_wr - gwr) / gwr
    features["win_rate_account"] = _clamp(0.5 + deviation * 6 * confidence)

    # --- potential_value: log scale × account context ---
    price = stats["product_prices"].get(deal["product_id"], 0)
    price_norm = math.log1p(float(price)) / stats["log_max_price"] if stats["log_max_price"] > 0 else 0

    # Enrich with account context: bigger account + expensive product = higher potential
    acct_temp = stats["accounts_lookup"].get(deal["account_id"], {})
    rev_temp = acct_temp.get("revenue")
    has_acct = pd.notna(rev_temp) and rev_temp is not None and float(rev_temp or 0) > 0
    if has_acct:
        acct_factor = math.log1p(float(rev_temp)) / stats["log_max_revenue"] if stats["log_max_revenue"] > 0 else 0.5
        # Blend: 70% product price + 30% account context
        raw = price_norm * 0.7 + (price_norm * acct_factor) * 0.3
    else:
        raw = price_norm * 0.85  # slight penalty for unknown account

    features["potential_value"] = _clamp(raw)

    # --- account_fit: log-based, median fallback for no-account deals ---
    acct = stats["accounts_lookup"].get(deal["account_id"], {})
    rev = acct.get("revenue")
    emp = acct.get("employees")
    has_account = pd.notna(rev) and rev is not None and float(rev) > 0

    if has_account:
        rev = float(rev) if pd.notna(rev) and rev is not None else 0.0
        emp = float(emp) if pd.notna(emp) and emp is not None else 0.0
        rev_norm = math.log1p(rev) / stats["log_max_revenue"] if stats["log_max_revenue"] > 0 else 0
        emp_norm = math.log1p(emp) / stats["log_max_employees"] if stats["log_max_employees"] > 0 else 0
        features["account_fit"] = _clamp((rev_norm + emp_norm) / 2)
    else:
        # Below median — penalize lack of info, not neutral
        features["account_fit"] = stats["median_account_fit"] * 0.6

    # --- agent_performance: symmetric, reduced influence ---
    agent_wr = stats["agent_stats"].get(deal["sales_agent_id"], gwr)
    deviation = (agent_wr - gwr) / gwr
    features["agent_performance"] = _clamp(0.5 + deviation * 3)

    # --- agent_load: deviation from team average (extremes = risk) ---
    load = stats["agent_load"].get(deal["sales_agent_id"], stats["avg_agent_load"])
    avg_load = stats["avg_agent_load"]
    std_load = stats["std_agent_load"]
    # Both extremes are bad: too many deals = overloaded, too few = idle/underperforming
    # Optimal is near the average. Score decreases as deviation increases.
    z_score = abs(load - avg_load) / std_load
    features["agent_load"] = _clamp(1 / (1 + z_score))

    # --- repeat_customer: log scale, median fallback ---
    repeats = stats["repeat_counts"].get(deal["account_id"], 0)
    if repeats > 0:
        features["repeat_customer"] = _clamp(
            math.log1p(repeats) / stats["log_max_repeats"] if stats["log_max_repeats"] > 0 else 0
        )
    elif not has_account:
        features["repeat_customer"] = stats["median_repeat"] * 0.5
    else:
        features["repeat_customer"] = CLAMP_MIN

    return features


def explain_features(features: dict, deal: pd.Series, stats: dict,
                     products: pd.DataFrame, accounts: pd.DataFrame,
                     teams: pd.DataFrame) -> list[dict]:
    explanations = []

    product_name = products.loc[products["id"] == deal["product_id"], "name"].iloc[0] if len(products[products["id"] == deal["product_id"]]) > 0 else "?"
    account_name = accounts.loc[accounts["id"] == deal["account_id"], "name"].iloc[0] if len(accounts[accounts["id"] == deal["account_id"]]) > 0 else "?"
    sector = stats["sector_map"].get(deal["account_id"], "?")

    # pipeline_aging
    if deal["deal_stage"] == "Engaging" and pd.notna(deal["engage_date"]):
        days = (REFERENCE_DATE - deal["engage_date"]).days
        if features["pipeline_aging"] >= 0.6:
            explanations.append({"factor": "Tempo no pipeline", "impact": "positive",
                                 "text": f"Em Negociação há {days} dias — abaixo da mediana. Oportunidade recente."})
        elif features["pipeline_aging"] >= 0.35:
            explanations.append({"factor": "Tempo no pipeline", "impact": "neutral",
                                 "text": f"Em Negociação há {days} dias — tempo dentro do esperado."})
        else:
            explanations.append({"factor": "Tempo no pipeline", "impact": "negative",
                                 "text": f"Em Negociação há {days} dias — acima da mediana. Risco de estagnação."})
    elif deal["deal_stage"] == "Prospecting":
        explanations.append({"factor": "Tempo no pipeline", "impact": "negative",
                             "text": "Em Prospecção — ainda sem engajamento ativo. Prioridade menor."})

    # win_rate_combined
    combined = features["win_rate_combined"]
    sector_wr = stats["sector_stats"].get(sector, stats["global_win_rate"])
    product_wr = stats["product_stats"].get(deal["product_id"], stats["global_win_rate"])
    avg_wr = (sector_wr + product_wr) / 2 * 100
    if combined >= 0.55:
        explanations.append({"factor": "Conversão setor + produto", "impact": "positive",
                             "text": f"Combinação {sector} + {product_name} tem conversão de {avg_wr:.0f}% (acima da média)"})
    elif combined < 0.45:
        explanations.append({"factor": "Conversão setor + produto", "impact": "negative",
                             "text": f"Combinação {sector} + {product_name} tem conversão de {avg_wr:.0f}% (abaixo da média)"})
    else:
        explanations.append({"factor": "Conversão setor + produto", "impact": "neutral",
                             "text": f"Combinação {sector} + {product_name} tem conversão de {avg_wr:.0f}%"})

    # account history
    repeats = stats["repeat_counts"].get(deal["account_id"], 0)
    if repeats > 0:
        account_wr = stats["account_stats"].get(deal["account_id"], stats["global_win_rate"])
        explanations.append({"factor": "Histórico da conta", "impact": "positive",
                             "text": f"{account_name} já comprou {repeats}x ({account_wr*100:.0f}% conversão)"})
    elif account_name == "(Não definida)":
        explanations.append({"factor": "Conta", "impact": "negative",
                             "text": "Conta ainda não definida — priorize identificar o prospect"})
    else:
        explanations.append({"factor": "Conta nova", "impact": "neutral",
                             "text": f"Primeira oportunidade com {account_name}"})

    # potential value
    price = stats["product_prices"].get(deal["product_id"], 0)
    if features["potential_value"] >= 0.8:
        explanations.append({"factor": "Valor potencial", "impact": "positive",
                             "text": f"Produto de alto valor (R${price:,.0f})"})
    elif features["potential_value"] >= 0.5:
        explanations.append({"factor": "Valor potencial", "impact": "neutral",
                             "text": f"Produto de valor médio (R${price:,.0f})"})
    else:
        explanations.append({"factor": "Valor potencial", "impact": "neutral",
                             "text": f"Produto de baixo ticket (R${price:,.0f})"})

    # agent load
    load = stats["agent_load"].get(deal["sales_agent_id"], 0)
    avg_load = stats["avg_agent_load"]
    if features["agent_load"] >= 0.65:
        explanations.append({"factor": "Carga do vendedor", "impact": "positive",
                             "text": f"Vendedor com {load} oportunidades (média do time: {avg_load:.0f}) — carga equilibrada"})
    elif features["agent_load"] < 0.35:
        if load > avg_load:
            explanations.append({"factor": "Carga do vendedor", "impact": "negative",
                                 "text": f"Vendedor com {load} oportunidades (média: {avg_load:.0f}) — acima da média, risco de falta de foco"})
        else:
            explanations.append({"factor": "Carga do vendedor", "impact": "negative",
                                 "text": f"Vendedor com {load} oportunidades (média: {avg_load:.0f}) — abaixo da média"})

    # account fit
    if features["account_fit"] >= 0.6:
        explanations.append({"factor": "Porte da empresa", "impact": "positive",
                             "text": f"{account_name} é uma empresa de grande porte"})
    elif features["account_fit"] < 0.3:
        explanations.append({"factor": "Porte da empresa", "impact": "neutral",
                             "text": f"{account_name} é uma empresa de menor porte"})

    return explanations
