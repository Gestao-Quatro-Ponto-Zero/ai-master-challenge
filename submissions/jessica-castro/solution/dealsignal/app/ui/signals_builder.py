"""
DealSignal UI — Signal and engine detail builders.

Constructs the structured signal payload consumed by the deal panel renderer.
All functions are pure (no Streamlit calls); they only manipulate data.
"""

import pandas as pd

from config.constants import RATING_EMOJI
from app.ui.formatters import format_currency, _engine_interpretation, _engine_position
from utils.signals import (
    FEATURE_EXPLANATIONS,
    FEATURE_TO_ENGINE,
    compute_engine_scores,
    parse_factors,
)


def build_display_dataframe(scored_df: pd.DataFrame) -> pd.DataFrame:
    """Returns a compact display DataFrame for the pipeline table."""
    out = pd.DataFrame()
    out["opportunity_id"] = scored_df["opportunity_id"].values
    out["Conta"]    = scored_df["account"].values
    out["Produto"]  = scored_df["product"].values
    out["_win_prob"] = (scored_df["win_probability"].values * 100).round(1)
    out["Valor"]    = scored_df["effective_value"].apply(format_currency).values
    out["Rec. Esperada"] = scored_df["expected_revenue"].apply(format_currency).values
    out["Rating"] = scored_df["deal_rating"].apply(
        lambda r: f"{RATING_EMOJI.get(r, '')} {r}"
    ).values
    out["Etapa"] = scored_df["deal_stage"].values
    return out


def build_top_seller_benchmark(df: pd.DataFrame, min_deals: int = 10) -> dict:
    """Returns aggregated metrics for the best seller (highest win rate with ≥ min_deals)."""
    win_rate_col = "seller_win_rate" if "seller_win_rate" in df.columns else "agent_win_rate"
    agg = (
        df.groupby("sales_agent")
        .agg(
            deals       =("sales_agent",      "count"),
            win_rate    =(win_rate_col,        "mean"),
            exp_revenue =("expected_revenue",  "mean"),
            eff_value   =("effective_value",   "mean"),
            win_prob    =("win_probability",   "mean"),
        )
        .reset_index()
    )
    candidates = agg[agg["deals"] >= min_deals]
    if candidates.empty:
        return {}
    best = candidates.loc[candidates["win_rate"].idxmax()]
    return {
        "name":        best["sales_agent"],
        "deals":       int(best["deals"]),
        "win_rate":    best["win_rate"],
        "exp_revenue": best["exp_revenue"],
        "eff_value":   best["eff_value"],
        "win_prob":    best["win_prob"],
    }


def build_engine_details(row: pd.Series, df: pd.DataFrame, engine_scores: dict) -> dict:
    """Builds per-engine metric dicts with interpretation texts for the deal panel."""
    agent   = row.get("sales_agent", "—")
    product = row.get("product", "—")

    # ── Seller Power ──────────────────────────────────────────────────────────
    # Prefer V2 seller_win_rate; fall back to V1 agent_win_rate
    agent_wr = pd.to_numeric(
        row.get("seller_win_rate") if "seller_win_rate" in row.index else row.get("agent_win_rate"),
        errors="coerce",
    )
    seller_rank = pd.to_numeric(row.get("seller_rank_percentile"), errors="coerce")
    seller_load = pd.to_numeric(row.get("seller_pipeline_load"), errors="coerce")
    agent_deals = df[df["sales_agent"] == agent]
    agent_exp   = agent_deals["expected_revenue"].mean() if len(agent_deals) else None
    agent_eff   = agent_deals["effective_value"].mean()  if len(agent_deals) else None
    agent_wp    = agent_deals["win_probability"].mean()  if len(agent_deals) else None
    top         = build_top_seller_benchmark(df)
    sp_score    = engine_scores.get("Seller Power", 50)

    # ── Deal Momentum ─────────────────────────────────────────────────────────
    days_eng = pd.to_numeric(row.get("days_since_engage"), errors="coerce")
    is_stale = int(row.get("is_stale_flag", 0)) if pd.notna(row.get("is_stale_flag")) else 0
    if pd.notna(days_eng) and days_eng <= 7:
        momentum_status = "Acelerado"
    elif pd.notna(days_eng) and days_eng < 45:
        momentum_status = "Adequado"
    else:
        momentum_status = "Lento"
    dm_score = engine_scores.get("Deal Momentum", 50)

    # ── Product Performance ───────────────────────────────────────────────────
    prod_wr    = pd.to_numeric(row.get("product_win_rate"), errors="coerce")
    prod_rank  = pd.to_numeric(row.get("product_rank_percentile"), errors="coerce")
    prod_deals = df[df["product"] == product]
    prod_exp   = prod_deals["expected_revenue"].mean() if len(prod_deals) else None
    pp_score   = engine_scores.get("Product Performance", 50)

    # ── Stagnation Risk ───────────────────────────────────────────────────────
    age_pct      = pd.to_numeric(row.get("deal_age_percentile"), errors="coerce")
    pipeline_avg = df["days_since_engage"].mean()
    sr_score     = engine_scores.get("Stagnation Risk", 50)

    return {
        "Seller Power": {
            "metrics": [
                ("Vendedor",               agent),
                ("Taxa de conversão (V2)", f"{agent_wr:.0%}" if pd.notna(agent_wr) else "—"),
                ("Percentil no time",      f"{seller_rank * 100:.0f}º" if pd.notna(seller_rank) else "—"),
                ("Deals em aberto",        f"{int(seller_load)}" if pd.notna(seller_load) else "—"),
                ("Posição no time",        _engine_position(sp_score)),
            ],
            "benchmark":   top,
            "agent_stats": {
                "name":        agent,
                "deals":       len(agent_deals),
                "win_rate":    agent_wr,
                "exp_revenue": agent_exp,
                "eff_value":   agent_eff,
                "win_prob":    agent_wp,
            },
            "interpretation": _engine_interpretation("Seller Power", sp_score),
        },
        "Deal Momentum": {
            "metrics": [
                ("Estágio atual",       row.get("deal_stage", "—")),
                ("Sem contato há",      f"{int(days_eng)} dias" if pd.notna(days_eng) else "—"),
                ("Ritmo do Deal",       momentum_status),
                ("Deal parado",         "⚠️ Sim" if is_stale else "✅ Não"),
                ("Posição no pipeline", _engine_position(dm_score)),
                ("Data de engajamento", str(row.get("engage_date", "—"))[:10]),
            ],
            "interpretation": _engine_interpretation("Deal Momentum", dm_score),
        },
        "Product Performance": {
            "metrics": [
                ("Produto",                     product),
                ("Taxa de conversão histórica", f"{prod_wr:.0%}" if pd.notna(prod_wr) else "—"),
                ("Ranking do produto",          f"{prod_rank * 100:.0f}º percentil" if pd.notna(prod_rank) else "—"),
                ("Posição entre os produtos",   _engine_position(pp_score)),
                ("Deals com este produto",      str(len(prod_deals))),
                ("Receita esperada média",      format_currency(prod_exp) if prod_exp else "—"),
            ],
            "interpretation": _engine_interpretation("Product Performance", pp_score),
        },
        "Stagnation Risk": {
            "metrics": [
                ("Dias no pipeline",         f"{int(days_eng)} dias" if pd.notna(days_eng) else "—"),
                ("Percentil de idade",       f"{age_pct * 100:.0f}º percentil" if pd.notna(age_pct) else "—"),
                ("Deal parado (flag)",       "⚠️ Sim" if is_stale else "✅ Não"),
                ("Média do pipeline",        f"{pipeline_avg:.0f} dias"),
                ("Posição (saúde da idade)", _engine_position(sr_score)),
            ],
            "interpretation": _engine_interpretation("Stagnation Risk", sr_score),
        },
    }


def build_signals_for_deal(row: pd.Series, df: pd.DataFrame) -> dict:
    """Builds the full structured signal payload for a single deal row."""
    factors_raw = row.get("top_contributing_factors", "")
    factors = parse_factors(str(factors_raw) if pd.notna(factors_raw) else "")

    seen_engines: set = set()
    positive_signals = []
    risk_signals = []
    for feat, val in factors:
        engine = FEATURE_TO_ENGINE.get(feat)
        if not engine or engine in seen_engines:
            continue
        seen_engines.add(engine)
        desc  = FEATURE_EXPLANATIONS.get(feat, feat)
        entry = {"title": engine, "description": desc}
        if val > 0.05:
            positive_signals.append(entry)
        elif val < -0.05:
            risk_signals.append(entry)

    engine_scores = compute_engine_scores(row, df)
    return {
        "positive_signals": positive_signals[:3],
        "risk_signals":     risk_signals[:3],
        "rating_engines":   engine_scores,
        "model_factors":    factors,
        "engine_details":   build_engine_details(row, df, engine_scores),
    }
