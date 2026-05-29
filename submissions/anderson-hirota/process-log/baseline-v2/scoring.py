# scoring.py
"""Lead scoring logic.

Two outputs per deal:
  * score (0-100): a weighted-average priority signal across 6 subscores.
  * close_probability (0-1): empirical Won/(Won+Lost) ratio for the deal's stage.

These are kept separate so KPIs that need a real probability (e.g. weighted
pipeline $) don't abuse the priority score.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

STALE_DAYS = 60  # Engaging deals older than this are flagged.

WEIGHTS = {
    "stage": 0.30,
    "freshness": 0.20,
    "account_size": 0.15,
    "deal_value": 0.15,
    "product_winrate": 0.12,
    "sector_winrate": 0.08,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

FEATURE_DESCRIPTIONS = {
    "stage": {"weight": WEIGHTS["stage"],
              "desc": "Empirical close probability of the current stage."},
    "freshness": {"weight": WEIGHTS["freshness"],
                  "desc": "Recently-engaged deals are hot; stalled deals decay."},
    "account_size": {"weight": WEIGHTS["account_size"],
                     "desc": "Bigger accounts (revenue + headcount) have budget. "
                             "Percentiles computed over unique accounts, not opportunities."},
    "deal_value": {"weight": WEIGHTS["deal_value"],
                   "desc": "Bigger deals merit more focus."},
    "product_winrate": {"weight": WEIGHTS["product_winrate"],
                        "desc": "Some products close more reliably (Bayesian-smoothed)."},
    "sector_winrate": {"weight": WEIGHTS["sector_winrate"],
                       "desc": "Some sectors convert better (Bayesian-smoothed)."},
}

# Fallbacks if a stage isn't represented in closed data.
STAGE_PROB_FALLBACK = {"Prospecting": 0.20, "Engaging": 0.55, "Won": 1.0, "Lost": 0.0}


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
    """Map each value to its percentile rank (0–100) within ref_values."""
    ref = np.sort(ref_values[~np.isnan(ref_values)])
    if len(ref) == 0:
        return pd.Series(50.0, index=values.index)
    ranks = np.searchsorted(ref, values.values, side="right") / len(ref) * 100
    out = pd.Series(ranks, index=values.index)
    out[values.isna()] = 50.0  # neutral for missing
    return out


def _freshness_vec(days: pd.Series) -> pd.Series:
    # Bell-shaped: penalize both very new (just engaged, no traction) and stale.
    # Peak around 7–30 days; falls off after 60.
    bins = [-np.inf, 7, 30, 60, 90, 180, np.inf]
    scores = [80, 100, 75, 50, 25, 10]
    out = pd.cut(days, bins=bins, labels=scores, right=True).astype(float)
    out = out.fillna(50.0)
    return out


def _expected_value_vec(df: pd.DataFrame, typical_discount: float) -> pd.Series:
    """Realistic $ at stake. For open deals, list price × (1 − typical discount).
    For Won deals, the actual close_value. For Lost, 0."""
    sales_price = df["sales_price"].astype(float)
    close_value = df["close_value"].astype(float) if "close_value" in df.columns else pd.Series(0.0, index=df.index)
    discounted = sales_price * (1 - typical_discount)
    val = discounted.copy()
    won_mask = (df["deal_stage"] == "Won") & close_value.notna() & (close_value > 0)
    val[won_mask] = close_value[won_mask]
    val[df["deal_stage"] == "Lost"] = 0.0
    return val.fillna(0.0)


def _typical_discount(df: pd.DataFrame) -> float:
    """Median (close_value / sales_price) on Won deals, capped to [0, 0.5]."""
    won = df[(df["deal_stage"] == "Won") & df["close_value"].notna() & df["sales_price"].notna()]
    won = won[(won["sales_price"] > 0) & (won["close_value"] > 0)]
    if not len(won):
        return 0.0
    ratio = (won["close_value"] / won["sales_price"]).median()
    discount = max(0.0, min(0.5, 1 - float(ratio)))
    return discount


def _stage_probabilities(df: pd.DataFrame) -> dict:
    """Empirical Won/(Won+Lost) per stage — used for open stages as a heuristic
    via the fallback table, since open deals haven't closed."""
    closed = df[df["deal_stage"].isin(["Won", "Lost"])]
    if not len(closed):
        return dict(STAGE_PROB_FALLBACK)
    by_stage = closed.groupby("deal_stage").apply(
        lambda g: (g["deal_stage"] == "Won").mean()
    ).to_dict()
    probs = dict(STAGE_PROB_FALLBACK)
    probs.update(by_stage)
    return probs


def _recommend_action(stage: str, days: float, score: float) -> str:
    if pd.isna(days):
        days = 0
    if stage == "Prospecting":
        if score >= 60:
            return "Push to Engaging — high-quality prospect."
        return "Qualify or disqualify quickly."
    if stage == "Engaging":
        if days > STALE_DAYS and score < 50:
            return "Likely dead — disqualify or escalate."
        if days > STALE_DAYS:
            return f"Stalled {days:.0f}d — re-engage with new angle."
        if score >= 75:
            return "Top focus — close this week."
        return "Stay close, advance to next step."
    return "—"


def score_pipeline(
    df: pd.DataFrame,
    accounts_df: pd.DataFrame,
    ref_date: pd.Timestamp,
):
    """Vectorized scorer. Returns (scored_df, stage_probability_dict)."""
    out = df.copy()

    out["days_in_pipeline"] = (ref_date - out["engage_date"]).dt.days
    out["days_in_pipeline"] = out["days_in_pipeline"].clip(lower=0)

    typical_discount = _typical_discount(out)
    out["expected_value"] = _expected_value_vec(out, typical_discount)

    # ---- Reference distributions: use UNIQUE accounts, not deal-weighted.
    rev_ref = accounts_df["revenue"].astype(float).values if "revenue" in accounts_df.columns else np.array([])
    emp_ref = accounts_df["employees"].astype(float).values if "employees" in accounts_df.columns else np.array([])
    # Deal value reference: open deals only (what reps will be ranked against).
    open_mask_all = out["deal_stage"].isin(["Prospecting", "Engaging"])
    val_ref = out.loc[open_mask_all, "expected_value"].astype(float).values

    # ---- Empirical priors
    stage_probs = _stage_probabilities(out)
    closed = out[out["deal_stage"].isin(["Won", "Lost"])]
    product_wr = _smoothed_winrate(closed, "product")
    sector_wr = _smoothed_winrate(closed, "sector")
    global_wr = (closed["deal_stage"] == "Won").mean() if len(closed) else 0.3

    # ---- Subscores (all 0–100, vectorized)
    out["sub_stage"] = out["deal_stage"].map(stage_probs).fillna(0.3) * 100
    out["sub_freshness"] = _freshness_vec(out["days_in_pipeline"])
    rev_sc = _percentile_map(rev_ref, out["revenue"].astype(float))
    emp_sc = _percentile_map(emp_ref, out["employees"].astype(float)) if len(emp_ref) else pd.Series(50.0, index=out.index)
    out["sub_account_size"] = (rev_sc + emp_sc) / 2
    out["sub_deal_value"] = _percentile_map(val_ref, out["expected_value"].astype(float))
    out["sub_product_winrate"] = out["product"].map(product_wr).fillna(global_wr) * 100
    out["sub_sector_winrate"] = out["sector"].map(sector_wr).fillna(global_wr) * 100

    out["score"] = (
        out["sub_stage"] * WEIGHTS["stage"]
        + out["sub_freshness"] * WEIGHTS["freshness"]
        + out["sub_account_size"] * WEIGHTS["account_size"]
        + out["sub_deal_value"] * WEIGHTS["deal_value"]
        + out["sub_product_winrate"] * WEIGHTS["product_winrate"]
        + out["sub_sector_winrate"] * WEIGHTS["sector_winrate"]
    )

    out["close_probability"] = out["deal_stage"].map(stage_probs).fillna(0.3)

    # Recommended action per deal
    out["action"] = [
        _recommend_action(s, d, sc)
        for s, d, sc in zip(out["deal_stage"], out["days_in_pipeline"], out["score"])
    ]

    return out, stage_probs


def build_breakdown(row: pd.Series) -> pd.DataFrame:
    """Build the per-deal breakdown table lazily (only for the inspected deal)."""
    items = [
        ("Stage", row["deal_stage"], row["sub_stage"], WEIGHTS["stage"],
         f"Empirical close probability for {row['deal_stage']}."),
        ("Freshness", f"{row['days_in_pipeline']:.0f} days",
         row["sub_freshness"], WEIGHTS["freshness"],
         "Peaks at 7–30 days, decays after 60."),
        ("Account size", f"{row['sub_account_size']:.0f} pctile",
         row["sub_account_size"], WEIGHTS["account_size"],
         "Avg of revenue + employees percentile (vs all accounts)."),
        ("Deal value", f"${row['expected_value']:,.0f}",
         row["sub_deal_value"], WEIGHTS["deal_value"],
         "Percentile of expected $ across open deals."),
        ("Product win rate", f"{row['sub_product_winrate']:.0f}%",
         row["sub_product_winrate"], WEIGHTS["product_winrate"],
         f"How often {row['product']} closes (smoothed)."),
        ("Sector win rate", f"{row['sub_sector_winrate']:.0f}%",
         row["sub_sector_winrate"], WEIGHTS["sector_winrate"],
         f"How often {row.get('sector', 'n/a')} closes (smoothed)."),
    ]
    rows = []
    for feat, val, sub, w, why in items:
        rows.append({
            "Feature": feat,
            "Raw value": val,
            "Subscore (0–100)": round(float(sub), 1),
            "Weight": f"{w:.0%}",
            "Points": round(float(sub) * w, 1),
            "Why": why,
        })
    return pd.DataFrame(rows)
