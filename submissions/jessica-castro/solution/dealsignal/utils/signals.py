"""
DealSignal — Signal intelligence utilities.

Converts raw model feature contributions into human-readable signals
and engine scores for the Streamlit UI.
"""

from __future__ import annotations

import re
from typing import Optional

import pandas as pd

# ── Feature → Engine mapping ─────────────────────────────────────────────────

FEATURE_TO_ENGINE: dict[str, str] = {
    # Seller Power — V1 + V2
    "agent_win_rate":          "Seller Power",
    "agent_avg_deal_value":    "Seller Power",
    "seller_win_rate":         "Seller Power",
    "seller_rank_percentile":  "Seller Power",
    "seller_pipeline_load":    "Seller Power",
    # Deal Momentum
    "days_since_engage":       "Deal Momentum",
    "log_days_since_engage":   "Deal Momentum",
    "pipeline_velocity":       "Deal Momentum",
    # Product Performance
    "product_win_rate":        "Product Performance",
    "product_avg_deal_value":  "Product Performance",
    "product_rank_percentile": "Product Performance",
    # Deal Size
    "effective_value":         "Deal Size",
    "deal_value_percentile":   "Deal Size",
    # Stagnation Risk
    "is_stale_flag":              "Stagnation Risk",
    "is_very_old_deal":           "Stagnation Risk",
    "deal_age_percentile":        "Stagnation Risk",
    "deal_age_vs_pipeline_avg":   "Stagnation Risk",
    "seller_overloaded_flag":     "Stagnation Risk",
}

# ── Natural language explanations per feature ─────────────────────────────────

FEATURE_EXPLANATIONS: dict[str, str] = {
    # Seller Power
    "agent_win_rate":          "Este vendedor possui taxa de fechamento acima da média do time.",
    "agent_avg_deal_value":    "Este vendedor fecha deals de alto valor com consistência.",
    "seller_win_rate":         "Este vendedor possui alta taxa de fechamento histórica.",
    "seller_rank_percentile":  "Vendedor bem posicionado em relação ao time — forte histórico.",
    "seller_pipeline_load":    "Vendedor com muitos deals simultâneos — atenção distribuída.",
    # Deal Momentum
    "days_since_engage":       "Engajamento recente indica deal ativo e com bom momentum.",
    "log_days_since_engage":   "Deal com muito tempo no pipeline — risco de estagnação.",
    "pipeline_velocity":       "Deal avançando lentamente pelo funil.",
    # Product Performance
    "product_win_rate":        "Este produto tem alta taxa de conversão histórica.",
    "product_avg_deal_value":  "Produto associado a deals de alto ticket médio.",
    "product_rank_percentile": "Produto com bom ranking histórico de conversão.",
    # Account Strength
    "digital_maturity_index":  "Empresa com presença digital forte e maturidade tecnológica.",
    "digital_presence_score":  "Alta presença digital — empresa fácil de engajar online.",
    "revenue_per_employee":    "Empresa com alta geração de receita por colaborador.",
    "company_age":             "Empresa estabelecida com histórico sólido no mercado.",
    # Deal Size
    "effective_value":         "Deal de alto valor — prioridade estratégica.",
    "deal_value_percentile":   "Este deal está entre os maiores do pipeline.",
    # Stagnation Risk
    "is_stale_flag":              "Deal parado há muito tempo — risco de estagnação no pipeline.",
    "is_very_old_deal":           "Deal muito antigo — requer atenção imediata para reativar.",
    "deal_age_percentile":        "Deal entre os mais antigos do pipeline — risco de perda por inatividade.",
    "deal_age_vs_pipeline_avg":   "Deal mais velho que a média do pipeline.",
    "seller_overloaded_flag":     "Vendedor com muitos deals simultâneos — atenção distribuída.",
}

# ── Parsing ───────────────────────────────────────────────────────────────────

_FACTOR_RE = re.compile(r"([+-]?\w+)\(([+-][\d.]+)\)")


def parse_factors(s: str) -> list[tuple[str, float]]:
    """Parse a top_contributing_factors string into (feature, value) pairs.

    Input:  "+agent_win_rate(+0.19), -pipeline_velocity(-0.12)"
    Output: [("agent_win_rate", 0.19), ("pipeline_velocity", -0.12)]
    Sorted by abs(value) descending.
    """
    if not s or pd.isna(s):
        return []
    pairs = []
    for m in _FACTOR_RE.finditer(str(s)):
        feat = m.group(1).lstrip("+-")
        val = float(m.group(2))
        pairs.append((feat, val))
    return sorted(pairs, key=lambda x: abs(x[1]), reverse=True)


# ── Signals ───────────────────────────────────────────────────────────────────

def get_signals(s: str, max_signals: int = 3) -> list[tuple[str, str]]:
    """Convert a top_contributing_factors string to a list of signal badges.

    Returns list of (badge_text, sentiment) where:
      sentiment = "positive" | "negative" | "neutral"
    badge_text = "🟢 Seller Power" | "🔴 Deal Momentum" etc.

    Deduplicates by engine — only the strongest factor per engine is shown.
    """
    factors = parse_factors(s)
    seen_engines: set[str] = set()
    signals: list[tuple[str, str]] = []

    for feat, val in factors:
        engine = FEATURE_TO_ENGINE.get(feat)
        if engine is None:
            continue
        if engine in seen_engines:
            continue
        seen_engines.add(engine)

        if val > 0.05:
            emoji, sentiment = "🟢", "positive"
        elif val < -0.05:
            emoji, sentiment = "🔴", "negative"
        else:
            emoji, sentiment = "🟡", "neutral"

        signals.append((f"{emoji} {engine}", sentiment))
        if len(signals) >= max_signals:
            break

    return signals


# ── Engine scores ─────────────────────────────────────────────────────────────

# Maps engine name → (feature_col, invert)
# invert=True means lower feature value = better score (e.g. days_since_engage)
_ENGINE_FEATURES: dict[str, tuple[str, bool]] = {
    "Seller Power":        ("seller_win_rate",        False),  # V2: usa seller_win_rate
    "Deal Momentum":       ("days_since_engage",       True),  # invert: menos dias = melhor
    "Product Performance": ("product_rank_percentile", False), # V2: usa percentil de produto
    "Stagnation Risk":     ("deal_age_percentile",     True),  # invert: mais velho = pior
}


def compute_engine_scores(
    row: pd.Series,
    df: pd.DataFrame,
) -> dict[str, int]:
    """Compute 0–100 engine scores for a single deal row.

    Uses percentile rank within the full (filtered) dataset so scores
    are relative to the visible pipeline, not absolute values.
    """
    scores: dict[str, int] = {}
    for engine, (feat, invert) in _ENGINE_FEATURES.items():
        if feat not in df.columns or feat not in row.index:
            scores[engine] = 50  # default when feature not available
            continue
        col = pd.to_numeric(df[feat], errors="coerce").dropna()
        val = pd.to_numeric(row[feat], errors="coerce")
        if pd.isna(val) or len(col) == 0:
            scores[engine] = 50
            continue
        percentile = int((col <= val).mean() * 100)
        scores[engine] = (100 - percentile) if invert else percentile
    return scores
