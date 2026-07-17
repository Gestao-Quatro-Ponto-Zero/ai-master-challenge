"""Lead scorer — explainable rules engine.

Score 0-100 per open deal, decomposed into named factors. Every rule here
was validated against the closed-deal history first (see docs/PLAYBOOK.md
and docs/DATA_DICTIONARY.md):

  - Win probability: TESTED AND REJECTED. Historical account/agent/product
    win rates have zero out-of-time predictive power (backtest AUC 0.49;
    account rates correlate -0.17 across periods — noise). Outcomes are a
    flat ~63% baseline, so the honest policy is expected value x workflow
    rules. `backtest` reproduces the evidence.
  - Momentum: 14-138d winnable window. No deal in history won after 138d
    -> hard close/recycle. Inside the window age is NOT penalized.
  - Value: list price percentile (won deals close at ~100% of list, and
    win odds are flat across products — same odds, bigger prize).
  - Account attached: every deal that ever closed had an account; deals
    without one are frozen until it's fixed.
  - Account freshness: first deals at an account win at 74% vs ~61% later.

Usage:
  python src/scorer.py score      -> writes data/lake/scored_pipeline.csv
  python src/scorer.py backtest   -> time-split evaluation of the win-prob model
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LAKE = ROOT / "data" / "lake"

BASELINE = None  # set from data at load time
SHRINK_K = 25  # pseudo-observations pulling small samples toward baseline

WINDOW_END = 138  # no deal in history ever won past this age
WINDOW_WARN = 106  # p90 of won cycles — aging, needs a push

W_VALUE, W_MOMENTUM = 0.65, 0.35


def load_deals():
    return pd.read_csv(
        LAKE / "fact_deals.csv", parse_dates=["engage_date", "close_date"]
    )


def shrunk_rates(closed: pd.DataFrame, key: str, base: float) -> pd.Series:
    g = closed.groupby(key)["is_won"].agg(["sum", "size"])
    return (g["sum"] + SHRINK_K * base) / (g["size"] + SHRINK_K)


def reference_stats(closed: pd.DataFrame) -> dict:
    """Historical win rates by account / agent / product, shrunk to baseline."""
    base = closed["is_won"].mean()
    return {
        "base": base,
        "account": shrunk_rates(closed[closed.account_known], "account", base),
        "agent": shrunk_rates(closed, "sales_agent", base),
        "product": shrunk_rates(closed, "product", base),
        # deals already closed per account, to compute freshness of new ones
        "account_depth": closed[closed.account_known].groupby("account").size(),
    }


def win_probability(deals: pd.DataFrame, stats: dict) -> pd.Series:
    base = stats["base"]
    acc = deals["account"].map(stats["account"]).fillna(base)
    agt = deals["sales_agent"].map(stats["agent"]).fillna(base)
    prd = deals["product"].map(stats["product"]).fillna(base)
    p = acc * agt * prd / base**2
    return p.clip(0.15, 0.95)


def score_open_deals(deals: pd.DataFrame, stats: dict) -> pd.DataFrame:
    d = deals[deals.is_open].copy()

    d["f_value"] = d.sales_price.rank(pct=True)
    d["expected_win_value"] = (stats["base"] * d.sales_price).round(0)

    age = d.age_days  # NaN for Prospecting (no dates yet)
    d["f_momentum"] = pd.cut(
        age.fillna(-1),
        bins=[-2, -0.5, 14, WINDOW_WARN, WINDOW_END, 10**6],
        labels=[0.7, 0.6, 1.0, 0.5, 0.0],
        ordered=False,
    ).astype(float)

    d["score"] = (100 * (W_VALUE * d.f_value + W_MOMENTUM * d.f_momentum)).round(0)

    # Hard rules override the weighted blend.
    zombie = age > WINDOW_END
    d.loc[zombie, "score"] = 5
    d.loc[~d.account_known & ~zombie, "score"] = (
        d.loc[~d.account_known & ~zombie, "score"] * 0.85
    ).round(0)

    d["account_depth"] = d["account"].map(stats["account_depth"]).fillna(0)
    d["explanation"] = d.apply(lambda r: explain(r), axis=1)
    d["action"] = d.apply(lambda r: recommend(r), axis=1)

    cols = [
        "opportunity_id", "sales_agent", "manager", "regional_office",
        "deal_stage", "product", "account", "sales_price", "age_days",
        "expected_win_value", "score", "action", "explanation",
    ]
    return d[cols].sort_values("score", ascending=False)


def explain(r) -> str:
    parts = []
    parts.append(
        f"expected value ${r.expected_win_value:,.0f} "
        f"(63% baseline odds x ${r.sales_price:,.0f} list; odds are flat "
        f"across segments — bigger deal, same odds)"
    )
    parts.append(f"value rank: top {100 - r.f_value * 100:.0f}% of open pipeline")
    if pd.isna(r.age_days):
        parts.append("untriaged: not yet engaged")
    elif r.age_days > WINDOW_END:
        parts.append(f"{r.age_days:.0f}d old — no deal in history won past {WINDOW_END}d")
    elif r.age_days > WINDOW_WARN:
        parts.append(f"aging ({r.age_days:.0f}d, p90 of won cycles is {WINDOW_WARN}d)")
    elif r.age_days <= 14:
        parts.append(f"day {r.age_days:.0f} of natural triage window (half of losses die by day 14)")
    else:
        parts.append(f"in the winnable window ({r.age_days:.0f}d; won deals peak ~80d)")
    if not isinstance(r.account, str):
        parts.append("NO ACCOUNT ATTACHED — no deal has ever closed without one")
    elif r.account_depth <= 10:
        parts.append("fresh account (first deals at an account win at 74%)")
    return "; ".join(parts)


def recommend(r) -> str:
    if pd.notna(r.age_days) and r.age_days > WINDOW_END:
        return "CLOSE/RECYCLE — past the 138d line"
    if not isinstance(r.account, str):
        return "ATTACH ACCOUNT in CRM, then qualify"
    if pd.isna(r.age_days):
        return "TRIAGE — qualify and engage"
    if r.age_days > WINDOW_WARN:
        return "PUSH NOW — closing window"
    if r.score >= 60:
        return "FOCUS — work this deal today"
    return "NURTURE"


def backtest():
    """Time-split eval: learn rates from deals closed before 2017-09-01,
    predict outcomes of deals closing after. No leakage."""
    f = load_deals()
    closed = f[~f.is_open]
    train = closed[closed.close_date < "2017-09-01"]
    test = closed[closed.close_date >= "2017-09-01"]
    stats = reference_stats(train)
    p = win_probability(test, stats)
    y = test["is_won"].astype(int)

    # AUC via rank formula (no sklearn dependency)
    r = p.rank()
    n1, n0 = y.sum(), (1 - y).sum()
    auc = (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

    print(f"train: {len(train)} closed deals (< 2017-09-01, win rate {train.is_won.mean():.0%})")
    print(f"test:  {len(test)} closed deals (>= 2017-09-01, win rate {test.is_won.mean():.0%})")
    print(f"AUC of p_win on unseen closings: {auc:.3f}")
    print("\nCalibration by predicted-probability quintile:")
    q = pd.qcut(p, 5, duplicates="drop")
    cal = pd.DataFrame({"predicted": p.groupby(q, observed=True).mean(),
                        "actual": y.groupby(q, observed=True).mean(),
                        "n": y.groupby(q, observed=True).size()})
    print(cal.round(3).to_string())
    print("\n138d rule check on full history:",
          f"{(closed[closed.cycle_days > WINDOW_END].is_won.sum())} wins past 138d",
          f"({(closed.cycle_days > WINDOW_END).sum()} deals)")


def score():
    f = load_deals()
    stats = reference_stats(f[~f.is_open])
    out = score_open_deals(f, stats)
    path = LAKE / "scored_pipeline.csv"
    out.to_csv(path, index=False)
    print(f"scored {len(out)} open deals -> {path}")
    print("\nScore distribution:")
    print(out.score.describe().round(1).to_string())
    print("\nActions:")
    print(out.action.value_counts().to_string())
    print("\nTop 5 deals:")
    print(out.head(5)[["opportunity_id", "sales_agent", "product", "account", "score", "action"]].to_string(index=False))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "score"
    {"score": score, "backtest": backtest}[cmd]()
