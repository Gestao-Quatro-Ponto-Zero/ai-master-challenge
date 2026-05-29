# scoring.py
"""Lead scoring logic — v3.

Two outputs per deal:
  * score (0-100): weighted priority signal. Weights renormalize per-deal when a
    feature is unavailable (e.g. freshness for Prospecting with no engage_date).
  * close_probability (0-1): cohort-derived. For Prospecting, the overall
    historical win rate (every deal was once a prospect). For Engaging,
    Won/(Won+Lost) among deals that ever reached Engaging.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

STALE_DAYS = 60            # Engaging older than this is stalled.
PROSPECT_STALE_DAYS = 90   # Prospecting older than this is stalled.

WEIGHTS = {
    "stage":           0.28,
    "freshness":       0.18,
    "account_size":    0.15,
    "deal_value":      0.16,
    "product_winrate": 0.15,
    "sector_winrate":  0.08,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

FEATURE_DESCRIPTIONS = {
    "stage":           {"weight": WEIGHTS["stage"],
                        "desc": "Cohort close-rate for the current stage."},
    "freshness":       {"weight": WEIGHTS["freshness"],
                        "desc": "Monotone decay: fresh = best, decays after ~30d. "
                                "Omitted (and weights renormalized) when no engage_date."},
    "account_size":    {"weight": WEIGHTS["account_size"],
                        "desc": "Avg of revenue + headcount percentile over unique accounts."},
    "deal_value":      {"weight": WEIGHTS["deal_value"],
                        "desc": "Percentile of expected $ across open deals."},
    "product_winrate": {"weight": WEIGHTS["product_winrate"],
                        "desc": "Bayesian-smoothed historical close rate per product."},
    "sector_winrate":  {"weight": WEIGHTS["sector_winrate"],
                        "desc": "Bayesian-smoothed historical close rate per sector."},
}


def _smoothed_winrate(closed: pd.DataFrame, key: str, prior_weight: int = 5) -> dict:
    if not len(closed):
        return {}
    grouped = closed.groupby(key)["deal_stage"]
    wins = grouped.apply(lambda s: (s == "Won").sum())
    total = grouped.size()
    prior = (closed["deal_stage"] == "Won").mean()
    rate = (wins + prior_weight * prior) / (total + prior_weight)
    return rate.to_dict()


def _percentile_map(ref_values: np.ndarray, values: pd.Series) -> pd.Series:
    ref = np.sort(ref_values[~np.isnan(ref_values)])
    if len(ref) == 0:
        return pd.Series(50.0, index=values.index)
    ranks = np.searchsorted(ref, values.values, side="right") / len(ref) * 100
    out = pd.Series(ranks, index=values.index)
    out[values.isna()] = 50.0
    return out


def _freshness_vec(days: pd.Series) -> pd.Series:
    """Monotone decay. Fresh = 100. NaN preserved (so caller can renormalize)."""
    bins = [-np.inf, 30, 60, 90, 180, np.inf]
    scores = [100, 80, 55, 30, 10]
    cats = pd.cut(days, bins=bins, labels=scores, right=True, ordered=False)
    return pd.Series(cats, index=days.index).astype(float)


def _typical_discount(df: pd.DataFrame) -> float:
    won = df[(df["deal_stage"] == "Won") & df["close_value"].notna() & df["sales_price"].notna()]
    won = won[(won["sales_price"] > 0) & (won["close_value"] > 0)]
    if not len(won):
        return 0.0
    ratio = (won["close_value"] / won["sales_price"]).median()
    return max(0.0, min(0.5, 1 - float(ratio)))


def _expected_value_vec(df: pd.DataFrame, typical_discount: float) -> pd.Series:
    sales_price = df["sales_price"].astype(float)
    close_value = df["close_value"].astype(float) if "close_value" in df.columns else pd.Series(0.0, index=df.index)
    discounted = sales_price * (1 - typical_discount)
    val = discounted.copy()
    won_mask = (df["deal_stage"] == "Won") & close_value.notna() & (close_value > 0)
    val[won_mask] = close_value[won_mask]
    val[df["deal_stage"] == "Lost"] = 0.0
    return val.fillna(0.0)


def _stage_probabilities(df: pd.DataFrame) -> dict:
    """Cohort-based close rates — see module docstring."""
    closed = df[df["deal_stage"].isin(["Won", "Lost"])]
    if not len(closed):
        return {"Prospecting": 0.2, "Engaging": 0.5, "Won": 1.0, "Lost": 0.0}
    prospecting = float((closed["deal_stage"] == "Won").mean())
    if "engage_date" in closed.columns:
        engaged = closed[closed["engage_date"].notna()]
        engaging = float((engaged["deal_stage"] == "Won").mean()) if len(engaged) else prospecting
    else:
        engaging = prospecting
    return {"Prospecting": prospecting, "Engaging": engaging, "Won": 1.0, "Lost": 0.0}


def _recommend_action(stage: str, days: float, score: float) -> str:
    has_days = pd.notna(days)
    d = days if has_days else 0
    if stage == "Prospecting":
        if has_days and d > PROSPECT_STALE_DAYS and score < 50:
            return f"Stale prospect ({d:.0f}d) — disqualify."
        if has_days and d > PROSPECT_STALE_DAYS:
            return f"Old prospect ({d:.0f}d) — qualify hard or drop."
        if score >= 60:
            return "Push to Engaging — high-quality prospect."
        return "Qualify or disqualify."
    if stage == "Engaging":
        if d > STALE_DAYS and score < 50:
            return "Likely dead — disqualify or escalate."
        if d > STALE_DAYS:
            return f"Stalled {d:.0f}d — re-engage with new angle."
        if score >= 75:
            return "Top focus — close this week."
        return "Stay close, advance to next step."
    return "—"


def score_pipeline(
    df: pd.DataFrame,
    accounts_df: pd.DataFrame,
    ref_date: pd.Timestamp,
):
    out = df.copy()

    if "engage_date" in out.columns:
        out["days_in_pipeline"] = (ref_date - out["engage_date"]).dt.days
        out["days_in_pipeline"] = out["days_in_pipeline"].where(
            out["days_in_pipeline"].isna(), out["days_in_pipeline"].clip(lower=0)
        )
    else:
        out["days_in_pipeline"] = np.nan

    typical_discount = _typical_discount(out)
    out["expected_value"] = _expected_value_vec(out, typical_discount)

    rev_ref = accounts_df["revenue"].astype(float).values if "revenue" in accounts_df.columns else np.array([])
    emp_ref = accounts_df["employees"].astype(float).values if "employees" in accounts_df.columns else np.array([])
    open_mask_all = out["deal_stage"].isin(["Prospecting", "Engaging"])
    val_ref = out.loc[open_mask_all, "expected_value"].astype(float).values

    stage_probs = _stage_probabilities(out)
    closed = out[out["deal_stage"].isin(["Won", "Lost"])]
    product_wr = _smoothed_winrate(closed, "product")
    sector_wr  = _smoothed_winrate(closed, "sector")
    global_wr  = float((closed["deal_stage"] == "Won").mean()) if len(closed) else 0.3

    out["sub_stage"]           = out["deal_stage"].map(stage_probs).fillna(0.3) * 100
    out["sub_freshness"]       = _freshness_vec(out["days_in_pipeline"])  # NaN preserved
    rev_sc = _percentile_map(rev_ref, out["revenue"].astype(float)) if len(rev_ref) else pd.Series(50.0, index=out.index)
    emp_sc = _percentile_map(emp_ref, out["employees"].astype(float)) if len(emp_ref) else pd.Series(50.0, index=out.index)
    out["sub_account_size"]    = (rev_sc + emp_sc) / 2
    out["sub_deal_value"]      = _percentile_map(val_ref, out["expected_value"].astype(float))
    out["sub_product_winrate"] = out["product"].map(product_wr).fillna(global_wr) * 100
    out["sub_sector_winrate"]  = out["sector"].map(sector_wr).fillna(global_wr) * 100

    # Weighted sum with renormalization when freshness is missing.
    w = WEIGHTS
    base = (
        out["sub_stage"]           * w["stage"]
      + out["sub_account_size"]    * w["account_size"]
      + out["sub_deal_value"]      * w["deal_value"]
      + out["sub_product_winrate"] * w["product_winrate"]
      + out["sub_sector_winrate"]  * w["sector_winrate"]
    )
    fresh_part = out["sub_freshness"].fillna(0) * w["freshness"]
    other_w = 1 - w["freshness"]
    has_fresh = out["sub_freshness"].notna()
    out["score"] = np.where(has_fresh, base + fresh_part, base / other_w).round(2)
    out["score"] = out["score"].clip(0, 100)

    out["close_probability"] = out["deal_stage"].map(stage_probs).fillna(global_wr)

    out["action"] = [
        _recommend_action(s, d, sc)
        for s, d, sc in zip(out["deal_stage"], out["days_in_pipeline"], out["score"])
    ]

    return out, stage_probs


def build_breakdown(row: pd.Series) -> pd.DataFrame:
    has_fresh = pd.notna(row["sub_freshness"])
    other_w = 1 - WEIGHTS["freshness"]

    def effective_weight(name: str) -> float:
        if name == "freshness":
            return WEIGHTS["freshness"] if has_fresh else 0.0
        return WEIGHTS[name] if has_fresh else WEIGHTS[name] / other_w

    days_str = f"{row['days_in_pipeline']:.0f} days" if has_fresh else "— (not engaged yet)"
    fresh_sub = float(row["sub_freshness"]) if has_fresh else 0.0

    items = [
        ("Stage", row["deal_stage"], row["sub_stage"], effective_weight("stage"),
         f"Cohort close rate for {row['deal_stage']}."),
        ("Freshness", days_str, fresh_sub, effective_weight("freshness"),
         "Fresh = 100, decays after ~30d. "
         + ("Omitted; remaining weights renormalized." if not has_fresh else "")),
        ("Account size", f"{row['sub_account_size']:.0f} pctile",
         row["sub_account_size"], effective_weight("account_size"),
         "Avg of revenue + employees percentile (vs all accounts)."),
        ("Deal value", f"${row['expected_value']:,.0f}",
         row["sub_deal_value"], effective_weight("deal_value"),
         "Percentile of expected $ across open deals."),
        ("Product win rate", f"{row['sub_product_winrate']:.0f}%",
         row["sub_product_winrate"], effective_weight("product_winrate"),
         f"How often {row['product']} closes (smoothed)."),
        ("Sector win rate", f"{row['sub_sector_winrate']:.0f}%",
         row["sub_sector_winrate"], effective_weight("sector_winrate"),
         f"How often {row.get('sector') or 'n/a'} closes (smoothed)."),
    ]
    rows = []
    for feat, val, sub, w_eff, why in items:
        rows.append({
            "Feature": feat,
            "Raw value": val,
            "Subscore (0–100)": round(float(sub), 1),
            "Weight": f"{w_eff:.0%}",
            "Points": round(float(sub) * w_eff, 1),
            "Why": why,
        })
    return pd.DataFrame(rows)
