"""Lead scoring logic.

Score = weighted average of subscores (each 0–100), then rounded.
Subscores are designed so that a non-technical rep can read the breakdown
and immediately understand *why* a deal ranks where it does.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Feature weights — must sum to 1.0
WEIGHTS = {
    "stage": 0.25,
    "agent_winrate": 0.18,
    "product_winrate": 0.12,
    "sector_winrate": 0.10,
    "freshness": 0.15,
    "account_size": 0.10,
    "deal_value": 0.10,
}

FEATURE_DESCRIPTIONS = {
    "stage": {
        "weight": WEIGHTS["stage"],
        "desc": "Engaging deals are far closer to closing than Prospecting.",
    },
    "agent_winrate": {
        "weight": WEIGHTS["agent_winrate"],
        "desc": "Historical win rate of the rep on closed deals.",
    },
    "product_winrate": {
        "weight": WEIGHTS["product_winrate"],
        "desc": "Some products close more reliably than others.",
    },
    "sector_winrate": {
        "weight": WEIGHTS["sector_winrate"],
        "desc": "Sectors where we historically win more.",
    },
    "freshness": {
        "weight": WEIGHTS["freshness"],
        "desc": "Recently-engaged deals are hot; stale deals (>90d) cool fast.",
    },
    "account_size": {
        "weight": WEIGHTS["account_size"],
        "desc": "Larger accounts (revenue + headcount) tend to have budget.",
    },
    "deal_value": {
        "weight": WEIGHTS["deal_value"],
        "desc": "Bigger deals get a small boost — focus matters more there.",
    },
}

STAGE_SCORE = {"Prospecting": 35, "Engaging": 80, "Won": 100, "Lost": 0}


def _winrate(df: pd.DataFrame, key: str) -> pd.Series:
    """Win rate per `key`, smoothed so small samples don't dominate."""
    closed = df[df["deal_stage"].isin(["Won", "Lost"])]
    grouped = closed.groupby(key)["deal_stage"]
    wins = grouped.apply(lambda s: (s == "Won").sum())
    total = grouped.size()
    # Bayesian smoothing toward global mean with prior weight = 5
    prior = (closed["deal_stage"] == "Won").mean() if len(closed) else 0.3
    rate = (wins + 5 * prior) / (total + 5)
    return rate


def _percentile_score(series: pd.Series, value) -> float:
    """Map a value to its percentile in the series (0–100)."""
    if pd.isna(value):
        return 50.0  # neutral for missing
    s = series.dropna()
    if len(s) == 0:
        return 50.0
    return float((s <= value).mean() * 100)


def _freshness_score(days: float) -> float:
    if pd.isna(days):
        return 50.0
    if days <= 14:
        return 100.0
    if days <= 30:
        return 85.0
    if days <= 60:
        return 65.0
    if days <= 90:
        return 45.0
    if days <= 180:
        return 25.0
    return 10.0


def _expected_value(row) -> float:
    """Best estimate of $ at stake. For open deals, use product price."""
    if row["deal_stage"] in ("Won",) and pd.notna(row.get("close_value")) and row["close_value"] > 0:
        return float(row["close_value"])
    if pd.notna(row.get("sales_price")):
        return float(row["sales_price"])
    return float(row.get("close_value") or 0.0)


def score_pipeline(df: pd.DataFrame, ref_date: pd.Timestamp) -> pd.DataFrame:
    """Return df with `score`, `breakdown`, `expected_value`, `days_in_pipeline`."""
    out = df.copy()

    # Engagement age
    out["days_in_pipeline"] = (ref_date - out["engage_date"]).dt.days
    out.loc[out["days_in_pipeline"] < 0, "days_in_pipeline"] = 0

    out["expected_value"] = out.apply(_expected_value, axis=1)

    # Win rates from closed deals
    agent_wr = _winrate(out, "sales_agent")
    product_wr = _winrate(out, "product")
    sector_wr = _winrate(out, "sector")

    # Reference distributions for percentile scoring
    rev_series = out["revenue"]
    emp_series = out["employees"] if "employees" in out.columns else pd.Series(dtype=float)
    val_series = out["expected_value"]

    records = []
    breakdowns = []

    for _, row in out.iterrows():
        # --- Stage
        stage_sc = STAGE_SCORE.get(row["deal_stage"], 30)

        # --- Agent win rate
        a_wr = agent_wr.get(row["sales_agent"], np.nan)
        agent_sc = float(a_wr * 100) if pd.notna(a_wr) else 50.0

        # --- Product win rate
        p_wr = product_wr.get(row["product"], np.nan)
        product_sc = float(p_wr * 100) if pd.notna(p_wr) else 50.0

        # --- Sector win rate
        s_wr = sector_wr.get(row.get("sector"), np.nan)
        sector_sc = float(s_wr * 100) if pd.notna(s_wr) else 50.0

        # --- Freshness
        fresh_sc = _freshness_score(row["days_in_pipeline"])

        # --- Account size (avg of revenue percentile + employees percentile)
        rev_sc = _percentile_score(rev_series, row.get("revenue"))
        emp_sc = _percentile_score(emp_series, row.get("employees")) if len(emp_series) else 50.0
        acct_sc = (rev_sc + emp_sc) / 2

        # --- Deal value percentile
        val_sc = _percentile_score(val_series, row["expected_value"])

        subs = {
            "stage": stage_sc,
            "agent_winrate": agent_sc,
            "product_winrate": product_sc,
            "sector_winrate": sector_sc,
            "freshness": fresh_sc,
            "account_size": acct_sc,
            "deal_value": val_sc,
        }

        total = sum(subs[k] * WEIGHTS[k] for k in WEIGHTS)
        records.append(total)

        breakdowns.append([
            {
                "feature": "Stage",
                "value": row["deal_stage"],
                "subscore": round(stage_sc, 1),
                "weight": WEIGHTS["stage"],
                "contribution": stage_sc * WEIGHTS["stage"],
                "reason": "Engaging > Prospecting in close probability.",
            },
            {
                "feature": "Agent win rate",
                "value": f"{a_wr:.0%}" if pd.notna(a_wr) else "n/a",
                "subscore": round(agent_sc, 1),
                "weight": WEIGHTS["agent_winrate"],
                "contribution": agent_sc * WEIGHTS["agent_winrate"],
                "reason": f"{row['sales_agent']}'s historical close rate.",
            },
            {
                "feature": "Product win rate",
                "value": f"{p_wr:.0%}" if pd.notna(p_wr) else "n/a",
                "subscore": round(product_sc, 1),
                "weight": WEIGHTS["product_winrate"],
                "contribution": product_sc * WEIGHTS["product_winrate"],
                "reason": f"How often {row['product']} closes.",
            },
            {
                "feature": "Sector win rate",
                "value": f"{s_wr:.0%}" if pd.notna(s_wr) else "n/a",
                "subscore": round(sector_sc, 1),
                "weight": WEIGHTS["sector_winrate"],
                "contribution": sector_sc * WEIGHTS["sector_winrate"],
                "reason": f"Historical win rate in {row.get('sector', 'n/a')}.",
            },
            {
                "feature": "Freshness",
                "value": f"{row['days_in_pipeline']:.0f} days in pipe"
                if pd.notna(row["days_in_pipeline"]) else "n/a",
                "subscore": round(fresh_sc, 1),
                "weight": WEIGHTS["freshness"],
                "contribution": fresh_sc * WEIGHTS["freshness"],
                "reason": "Recently-engaged deals close faster; stale deals decay.",
            },
            {
                "feature": "Account size",
                "value": f"rev pct {rev_sc:.0f} / emp pct {emp_sc:.0f}",
                "subscore": round(acct_sc, 1),
                "weight": WEIGHTS["account_size"],
                "contribution": acct_sc * WEIGHTS["account_size"],
                "reason": "Bigger accounts → bigger budget capacity.",
            },
            {
                "feature": "Deal value",
                "value": f"${row['expected_value']:,.0f}",
                "subscore": round(val_sc, 1),
                "weight": WEIGHTS["deal_value"],
                "contribution": val_sc * WEIGHTS["deal_value"],
                "reason": "Bigger deals get a modest priority bump.",
            },
        ])

    out["score"] = records
    out["breakdown"] = breakdowns
    return out
