"""
DealSignal UI — AI Insight layer.

Combines similarity-based historical context, Friction Engine, and Next Best Action
Engine to generate deal insights. The AI layer only communicates — the system decides.

Architecture:
  similarity search → context builder → friction engine → NBA engine
      → AI (text only) + deterministic narrative
"""

import os

import pandas as pd
import streamlit as st

from app.ui.formatters import format_currency
from config.constants import ENGINE_SCORE_MODERATE, ENGINE_SCORE_STRONG
from engine.next_best_action import (
    build_deal_narrative,
    build_nba_prompt,
    choose_next_action,
    identify_friction,
)

_ENGINE_LABELS_PT = {
    "Seller Power":        "Força do Vendedor",
    "Deal Momentum":       "Momento do Deal",
    "Product Performance": "Desempenho do Produto",
    "Stagnation Risk":     "Risco de Estagnação",
}


# ── Similarity search ─────────────────────────────────────────────────────────

def find_similar_deals(row: pd.Series, df: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
    """
    Returns the top_n most similar deals from df, excluding the current deal.

    Similarity formula (weights sum to 1.0):
      product_match    * 0.4
      value_similarity * 0.3
      office_match     * 0.2
      stage_match      * 0.1
    """
    opp_id  = row.get("opportunity_id")
    product = row.get("product", "")
    value   = float(row.get("effective_value") or 0)
    office  = row.get("office", "")
    stage   = row.get("deal_stage", "")

    others = df[df["opportunity_id"] != opp_id].copy()
    if others.empty:
        return others

    val_col          = pd.to_numeric(others["effective_value"], errors="coerce").fillna(0)
    denom            = val_col.combine(value, max).replace(0, 1)
    product_match    = (others["product"] == product).astype(float)
    value_similarity = 1.0 - ((val_col - value).abs() / denom).clip(upper=1.0)
    office_match     = (others["office"] == office).astype(float)
    stage_match      = (others["deal_stage"] == stage).astype(float)

    others["_sim"] = (
        product_match    * 0.4
        + value_similarity * 0.3
        + office_match     * 0.2
        + stage_match      * 0.1
    )
    return others.nlargest(top_n, "_sim").drop(columns="_sim")


# ── Context builder ───────────────────────────────────────────────────────────

def build_insight_context(
    row: pd.Series,
    similar: pd.DataFrame,
    signal_payload: dict,
) -> dict:
    """
    Assembles the numeric/textual context used by both the friction engine
    and the AI prompt builder.
    """
    engines = signal_payload.get("rating_engines", {})
    risks   = signal_payload.get("risk_signals", [])

    sim_count        = len(similar)
    win_col          = pd.to_numeric(similar.get("win_probability", pd.Series(dtype=float)), errors="coerce")
    win_rate_similar = float((win_col >= 0.65).mean()) if sim_count > 0 else 0.0

    seller_wr  = row.get("seller_win_rate", None)
    seller_pct = row.get("seller_rank_percentile", None)
    product_wr = row.get("product_win_rate", None)
    days_since = row.get("days_since_engage", None)

    strong_engines = [_ENGINE_LABELS_PT.get(k, k) for k, v in engines.items() if v >= ENGINE_SCORE_STRONG]
    weak_engines   = [_ENGINE_LABELS_PT.get(k, k) for k, v in engines.items() if v < ENGINE_SCORE_MODERATE]
    top_positive   = strong_engines[:2] or ["—"]
    top_risk       = weak_engines[:1] or ([r["description"] for r in risks[:1]] if risks else ["—"])

    # Friction engine fields — semantically renamed
    win_prob          = float(row.get("win_probability") or 0.0)
    is_stale          = int(row.get("is_stale_flag", 0))
    digital_maturity  = row.get("digital_maturity_index", None)
    # stagnation_health: HIGH = deal is fresh (good); LOW = deal is old/stale (bad)
    stagnation_health = engines.get("Stagnation Risk", 50)

    return {
        # Similarity context
        "similar_count":    sim_count,
        "win_rate_similar": win_rate_similar,
        # Seller / product
        "seller_win_rate":  float(seller_wr)  if seller_wr  is not None and pd.notna(seller_wr)  else None,
        "seller_rank_pct":  float(seller_pct) if seller_pct is not None and pd.notna(seller_pct) else None,
        "product_win_rate": float(product_wr) if product_wr is not None and pd.notna(product_wr) else None,
        # Engine scores
        "engine_scores":    engines,
        # Factor summaries
        "top_positive":     ", ".join(top_positive),
        "top_risk":         ", ".join(top_risk),
        # Deal metadata
        "deal_stage":       str(row.get("deal_stage", "—")),
        "days_since_engage": int(days_since) if days_since is not None and pd.notna(days_since) else None,
        "is_stale_flag":    is_stale,
        "product":          str(row.get("product", "—")),
        "sales_agent":      str(row.get("sales_agent", "—")),
        "effective_value":  row.get("effective_value", None),
        # Friction engine fields
        "win_prob":          win_prob,
        "sp":                engines.get("Seller Power", 50),
        "dm":                engines.get("Deal Momentum", 50),
        "pp":                engines.get("Product Performance", 50),
        "stagnation_health": stagnation_health,
        "is_stale":          is_stale,
        "seller_rank_pct":   float(seller_pct) if seller_pct is not None and pd.notna(seller_pct) else None,
        "digital_maturity":  float(digital_maturity) if digital_maturity is not None and pd.notna(digital_maturity) else None,
    }


# ── Fallback insight (rule-based) ─────────────────────────────────────────────

def _fallback_insight(row: pd.Series, signal_payload: dict, action_text: str = "") -> str:
    """Rule-based insight used when Groq API is unavailable."""
    prob    = float(row.get("win_probability", 0.0))
    value   = row.get("effective_value", None)
    agent   = row.get("sales_agent", "")
    product = row.get("product", "")

    engines = signal_payload.get("rating_engines", {})
    risks   = signal_payload.get("risk_signals", [])
    strong  = [(k, v) for k, v in engines.items() if v >= ENGINE_SCORE_STRONG]
    weak    = [(k, v) for k, v in engines.items() if v < ENGINE_SCORE_MODERATE]

    seller_wr  = row.get("seller_win_rate", None)
    seller_pct = row.get("seller_rank_percentile", None)
    product_wr = row.get("product_win_rate", None)

    engine_labels = {
        "Seller Power": "Força do Vendedor", "Deal Momentum": "Momento do Deal",
        "Product Performance": "Desempenho do Produto", "Stagnation Risk": "Risco de Estagnação",
    }

    parts = []
    if prob >= 0.65:
        val_str = f" de {format_currency(value)}" if value else ""
        parts.append(f"Este deal{val_str} apresenta <b>{round(prob * 100)}%</b> de probabilidade de fechamento.")
    else:
        parts.append(f"Probabilidade moderada de fechamento ({round(prob * 100)}%).")

    if strong:
        names = [f"{engine_labels.get(k, k)} ({v})" for k, v in strong]
        parts.append(f"Motores com maior contribuição: {', '.join(names)}.")

    if seller_wr is not None and pd.notna(seller_wr) and seller_pct is not None and pd.notna(seller_pct):
        if float(seller_pct) >= 0.7:
            parts.append(
                f"{agent} tem taxa de conversão de {float(seller_wr):.0%} "
                f"e está no top {(1 - float(seller_pct)) * 100:.0f}% do time."
            )

    if product_wr is not None and pd.notna(product_wr):
        product_pct = row.get("product_rank_percentile", None)
        if product_pct is not None and pd.notna(product_pct) and float(product_pct) >= 0.7:
            parts.append(
                f"O produto {product} tem histórico sólido ({float(product_wr):.0%} de conversão, "
                f"top {(1 - float(product_pct)) * 100:.0f}% do portfólio)."
            )

    if weak:
        risk_names = [engine_labels.get(k, k) for k, _ in weak]
        parts.append(f"Atenção em: {', '.join(risk_names)}.")
    elif risks:
        parts.append(risks[0]["description"])

    if action_text:
        parts.append(f"\nPróximo passo\n{action_text}")

    return " ".join(parts)


# ── Cached LLM call ───────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def generate_ai_insight(
    opportunity_id: str,
    _row_tuple: tuple,
    _df_hash: int,
    signal_payload_str: str,
) -> tuple:
    """
    Calls Groq API to generate the AI insight text.

    Cache keys: opportunity_id + row hash + df hash + serialized payload.
    Narrative is NOT generated here — it is always deterministic (see get_ai_insight).

    Returns:
        (insight_text, friction, friction_label, confidence, action_text, is_ai)
        — all str/bool primitives, compatible with st.cache_data
    """
    import json

    row            = pd.Series(dict(_row_tuple))
    signal_payload = json.loads(signal_payload_str)
    ctx            = signal_payload.get("_ai_context", {})
    friction_payload = signal_payload.get("_friction_payload", {})
    action_payload   = signal_payload.get("_action_payload", {})

    friction      = friction_payload.get("friction", "valor")
    friction_label = friction_payload.get("label", "Proposta de Valor")
    confidence    = friction_payload.get("confidence", "Baixo")
    action_text   = action_payload.get("action_text", "")

    api_key = None
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        return (
            _fallback_insight(row, signal_payload, action_text),
            friction, friction_label, confidence, action_text, False,
        )

    try:
        from groq import Groq  # type: ignore
        if not ctx or not friction_payload or not action_payload:
            return (
                _fallback_insight(row, signal_payload, action_text),
                friction, friction_label, confidence, action_text, False,
            )

        prompt = build_nba_prompt(ctx, friction_payload, action_payload)
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.4,
        )
        insight_text = response.choices[0].message.content.strip()
        return (insight_text, friction, friction_label, confidence, action_text, True)
    except Exception:
        return (
            _fallback_insight(row, signal_payload, action_text),
            friction, friction_label, confidence, action_text, False,
        )


# ── Public wrapper ────────────────────────────────────────────────────────────

def get_ai_insight(
    row: pd.Series,
    df: pd.DataFrame,
    signal_payload: dict,
) -> dict:
    """
    Orchestrates the full insight pipeline:
      similarity → context → friction engine → NBA engine → AI text → narrative

    Returns a dict with all display-ready fields.
    Narrative is always deterministic (never from AI in this version).
    """
    import json

    similar          = find_similar_deals(row, df)
    ctx              = build_insight_context(row, similar, signal_payload)
    friction_payload = identify_friction(ctx)
    action_payload   = choose_next_action(friction_payload["friction"], ctx)
    narrative_text   = build_deal_narrative(ctx, friction_payload)

    payload_with_ctx = {
        **signal_payload,
        "_ai_context":       ctx,
        "_friction_payload": friction_payload,
        "_action_payload":   action_payload,
    }

    row_tuple          = tuple(sorted(row.to_dict().items()))
    df_hash            = hash(df["opportunity_id"].astype(str).sort_values().str.cat())
    signal_payload_str = json.dumps(payload_with_ctx, default=str)

    result = generate_ai_insight(
        opportunity_id=str(row.get("opportunity_id", "")),
        _row_tuple=row_tuple,
        _df_hash=df_hash,
        signal_payload_str=signal_payload_str,
    )

    return {
        "insight_text":    result[0],
        "narrative_text":  narrative_text,
        "friction":        result[1],
        "friction_label":  result[2],
        "confidence":      result[3],
        "action_text":     result[4],
        "is_ai":           result[5],
    }
