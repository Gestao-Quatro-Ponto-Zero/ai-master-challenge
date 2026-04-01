import pandas as pd
import numpy as np
import math
from scoring.features import (
    DEFAULT_WEIGHTS,
    REFERENCE_DATE,
    CLAMP_MIN,
    CLAMP_MAX,
    compute_global_stats,
    explain_features,
)


def _vclamp(series: pd.Series) -> pd.Series:
    return series.clip(CLAMP_MIN, CLAMP_MAX)


def score_deal(features: dict, weights: dict = None) -> float:
    w = weights or DEFAULT_WEIGHTS
    score = sum(w.get(k, 0) * v for k, v in features.items() if k in w)
    return round(score * 100, 1)


def _vectorized_score(active: pd.DataFrame, stats: dict, weights: dict = None) -> pd.DataFrame:
    w = weights or DEFAULT_WEIGHTS
    gwr = max(stats["global_win_rate"], 0.01)

    # --- pipeline_aging: sigmoid, Prospecting = 0.30 ---
    engaging_mask = (active["deal_stage"] == "Engaging") & active["engage_date"].notna()
    days = (REFERENCE_DATE - active["engage_date"]).dt.days.fillna(0)
    median = stats["aging_median"]
    iqr = max(stats["aging_iqr"], 1)
    z = (days - median) / (iqr * 0.75)
    pipeline_aging = _vclamp(1 / (1 + np.exp(z)))
    pipeline_aging = pipeline_aging.where(engaging_mask, 0.30)

    # --- win_rate_combined: collapsed sector + product ---
    sector = active["account_id"].map(stats["sector_map"]).fillna("indefinido")
    sector_wr = sector.map(stats["sector_stats"]).fillna(gwr)
    product_wr = active["product_id"].map(stats["product_stats"]).fillna(gwr)
    combined_wr = (sector_wr + product_wr) / 2
    deviation = (combined_wr - gwr) / gwr
    win_rate_combined = _vclamp(0.5 + deviation * 8)

    # --- win_rate_account: confidence-weighted ---
    account_wr = active["account_id"].map(stats["account_stats"]).fillna(gwr)
    account_deals = active["account_id"].map(stats["account_deal_counts"]).fillna(0)
    confidence = (account_deals / 10).clip(upper=1)
    deviation = (account_wr - gwr) / gwr
    win_rate_account = _vclamp(0.5 + deviation * 6 * confidence)

    # --- potential_value: log scale × account context ---
    log_max = stats["log_max_price"]
    prices = active["product_id"].map(stats["product_prices"]).fillna(0)
    price_norm = np.log1p(prices.astype(float)) / log_max if log_max > 0 else prices * 0

    # Account revenue factor
    acct_rev_raw = active["account_id"].map(
        {k: float(v.get("revenue") or 0) if not (isinstance(v.get("revenue"), float) and np.isnan(v.get("revenue", 0) or 0)) else 0 for k, v in stats["accounts_lookup"].items()}
    ).fillna(0)
    log_mr = stats["log_max_revenue"] if stats["log_max_revenue"] > 0 else 1.0
    acct_factor = np.log1p(acct_rev_raw) / log_mr
    has_acct_mask = acct_rev_raw > 0

    # Blend: 70% price + 30% price*account for known accounts, 85% price for unknown
    potential_value = pd.Series(price_norm * 0.85, index=active.index)
    potential_value = potential_value.where(
        ~has_acct_mask,
        price_norm * 0.7 + (price_norm * acct_factor) * 0.3
    )
    potential_value = _vclamp(potential_value)

    # --- account_fit: log-based, median fallback for no-account ---
    acct_rev = active["account_id"].map(
        {k: float(v.get("revenue") or 0) if not (isinstance(v.get("revenue"), float) and np.isnan(v.get("revenue", 0) or 0)) else 0 for k, v in stats["accounts_lookup"].items()}
    ).fillna(0)
    acct_emp = active["account_id"].map(
        {k: float(v.get("employees") or 0) if not (isinstance(v.get("employees"), float) and np.isnan(v.get("employees", 0) or 0)) else 0 for k, v in stats["accounts_lookup"].items()}
    ).fillna(0)
    log_mr = stats["log_max_revenue"] if stats["log_max_revenue"] > 0 else 1.0
    log_me = stats["log_max_employees"] if stats["log_max_employees"] > 0 else 1.0
    rev_norm = np.log1p(acct_rev) / log_mr
    emp_norm = np.log1p(acct_emp) / log_me
    account_fit = _vclamp((rev_norm + emp_norm) / 2)
    # Below-median fallback for deals with no real account data
    no_account_mask = acct_rev == 0
    account_fit = account_fit.where(~no_account_mask, stats["median_account_fit"] * 0.6)

    # --- agent_performance: symmetric, reduced ---
    agent_wr = active["sales_agent_id"].map(stats["agent_stats"]).fillna(gwr)
    deviation = (agent_wr - gwr) / gwr
    agent_performance = _vclamp(0.5 + deviation * 3)

    # --- agent_load: deviation from team average (extremes = risk) ---
    load = active["sales_agent_id"].map(stats["agent_load"]).fillna(stats["avg_agent_load"])
    avg_load = stats["avg_agent_load"]
    std_load = stats["std_agent_load"]
    z_score = (load - avg_load).abs() / std_load
    agent_load = _vclamp(1 / (1 + z_score))

    # --- repeat_customer: log scale, median fallback ---
    log_max_rep = stats["log_max_repeats"] if stats["log_max_repeats"] > 0 else 1.0
    repeats = active["account_id"].map(stats["repeat_counts"]).fillna(0)
    repeat_customer = _vclamp(np.log1p(repeats) / log_max_rep)
    # Below-median fallback for no-account deals
    no_repeat_no_account = (repeats == 0) & no_account_mask
    repeat_customer = repeat_customer.where(~no_repeat_no_account, stats["median_repeat"] * 0.5)

    # --- Weighted score ---
    score = (
        w["pipeline_aging"] * pipeline_aging +
        w["win_rate_combined"] * win_rate_combined +
        w["win_rate_account"] * win_rate_account +
        w["potential_value"] * potential_value +
        w["account_fit"] * account_fit +
        w["agent_performance"] * agent_performance +
        w["agent_load"] * agent_load +
        w["repeat_customer"] * repeat_customer
    ) * 100

    active = active.copy()
    active["score"] = score.round(1)

    active["_f_pipeline_aging"] = pipeline_aging
    active["_f_win_rate_combined"] = win_rate_combined
    active["_f_win_rate_account"] = win_rate_account
    active["_f_potential_value"] = potential_value
    active["_f_account_fit"] = account_fit
    active["_f_agent_performance"] = agent_performance
    active["_f_agent_load"] = agent_load
    active["_f_repeat_customer"] = repeat_customer

    return active


def get_deal_explanations(deal: pd.Series, stats: dict,
                          products: pd.DataFrame, accounts: pd.DataFrame,
                          teams: pd.DataFrame) -> list[dict]:
    features = {col[3:]: deal[col] for col in deal.index if col.startswith("_f_")}
    return explain_features(features, deal, stats, products, accounts, teams)


def score_pipeline(pipeline: pd.DataFrame, accounts: pd.DataFrame,
                   products: pd.DataFrame, teams: pd.DataFrame,
                   weights: dict = None) -> pd.DataFrame:
    active = pipeline[pipeline["deal_stage"].isin(["Engaging", "Prospecting"])].copy()
    if active.empty:
        return active

    stats = compute_global_stats(pipeline, accounts, products, teams)
    active = _vectorized_score(active, stats, weights)

    product_map = products.set_index("id")["name"].to_dict()
    account_map = accounts.set_index("id")["name"].to_dict()
    agent_map = teams.set_index("id")["sales_agent"].to_dict()
    manager_map = teams.set_index("id")["manager"].to_dict()
    office_map = teams.set_index("id")["regional_office"].to_dict()
    price_map = products.set_index("id")["sales_price"].to_dict()

    active["product_name"] = active["product_id"].map(product_map)
    active["account_name"] = active["account_id"].map(account_map)
    active["agent_name"] = active["sales_agent_id"].map(agent_map)
    active["manager_name"] = active["sales_agent_id"].map(manager_map)
    active["regional_office"] = active["sales_agent_id"].map(office_map)
    active["potential_value"] = active["product_id"].map(price_map)

    active = active.sort_values("score", ascending=False).reset_index(drop=True)
    active.attrs["_scoring_stats"] = stats

    return active


def get_pipeline_metrics(pipeline: pd.DataFrame, scored: pd.DataFrame) -> dict:
    closed = pipeline[pipeline["deal_stage"].isin(["Won", "Lost"])]
    won = pipeline[pipeline["deal_stage"] == "Won"]

    total_won = len(won)
    total_closed = len(closed)
    win_rate = (total_won / total_closed * 100) if total_closed > 0 else 0
    avg_ticket = won["close_value"].mean() if total_won > 0 else 0
    total_potential = scored["potential_value"].sum() if not scored.empty else 0
    active_count = len(scored)
    at_risk = len(scored[scored["score"] < 40]) if not scored.empty else 0

    return {
        "win_rate": round(win_rate, 1),
        "avg_ticket": round(float(avg_ticket), 2),
        "total_potential": round(float(total_potential), 2),
        "active_deals": active_count,
        "at_risk": at_risk,
        "total_won_value": round(float(won["close_value"].sum()), 2),
    }
