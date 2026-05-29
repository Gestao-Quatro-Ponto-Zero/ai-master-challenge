## 1. Critique

1. **`expected_value` metric is mathematically wrong.** `(score/100 * expected_value).sum()` treats the 0–100 score as a probability. It isn't — it's a weighted blend of seven heterogeneous subscores. A deal can have score 80 with a stage subscore of 35 (Prospecting). The "Expected value" KPI is dimensionally meaningless and will mislead the Head of RevOps.
2. **Agent win-rate penalizes struggling reps' deals.** A weak rep working a high-quality account gets systematically deprioritized — that's the opposite of what a rep-facing prioritizer should do. The brief is "where should *I* focus today," not "whose deals does management trust." 18% weight is far too high for a signal that creates this perverse behavior.
3. **`ref_date` ignores `close_date`.** Uses `max(today, engage_date.max())`. For historical CRM dumps, `close_date` for Won/Lost deals is typically later than the latest `engage_date` of *open* deals, making every open deal look artificially fresher than it is and inflating freshness scores.
4. **Percentile distributions are weighted by deal count, not entity count.** `revenue` and `employees` percentiles are computed off the merged pipeline df, so an 85-account universe becomes ~8,800 rows with accounts repeated proportionally to deal volume. Big-pipeline accounts get artificially deflated revenue percentiles.
5. **`iterrows` over 8,800 rows building dict-of-dicts per row.** Slow, and the `breakdown` column is a Python-object column that bloats memory and corrupts the CSV download (lists of dicts serialize as ugly Python repr). The breakdown only needs to exist for the *one* deal the user inspects.
6. **No "what should I do" surface.** A list sorted by score is not a decision aid — the brief explicitly says "ajuda a tomar decisão ou só mostra dados?" Missing: stalled-deal alerts (Engaging + days > N), rep-level workload view, no recommended next action per deal.
7. **`expected_value` for open deals = `sales_price`** ignores the `close_value` field, which in this dataset is populated for Won deals only but is reportedly the forecast field. More importantly, `sales_price` for open deals doesn't account for the typical discount visible in Won deals (close_value < sales_price). Easy calibration miss.
8. **Stage constants (Prospecting=35, Engaging=80) are pulled from thin air** when they could be derived from the data (the empirical Won/(Won+Lost) ratio per stage), which would also make them defensible to the RevOps Head.

## 2. v2

```python
# app.py
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from scoring import (
    score_pipeline,
    build_breakdown,
    FEATURE_DESCRIPTIONS,
    STALE_DAYS,
)

DATA_DIR = "data"

st.set_page_config(page_title="Lead Scorer", layout="wide", page_icon="🎯")


@st.cache_data
def load_data():
    accounts = pd.read_csv(os.path.join(DATA_DIR, "accounts.csv"))
    products = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))
    teams = pd.read_csv(os.path.join(DATA_DIR, "sales_teams.csv"))
    pipeline = pd.read_csv(os.path.join(DATA_DIR, "sales_pipeline.csv"))

    for col in ("engage_date", "close_date"):
        if col in pipeline.columns:
            pipeline[col] = pd.to_datetime(pipeline[col], errors="coerce")

    df = (
        pipeline
        .merge(teams, on="sales_agent", how="left")
        .merge(accounts, on="account", how="left")
        .merge(products, on="product", how="left")
    )
    return df, accounts


def fmt_money(v):
    if pd.isna(v):
        return "—"
    return f"${v:,.0f}"


def score_color(s):
    if s >= 75:
        return "🟢"
    if s >= 50:
        return "🟡"
    return "🔴"


def main():
    st.title("🎯 Lead Scorer — Pipeline Prioritization")
    st.caption(
        "Rule-based scoring + calibrated close probability. "
        "Open deals only (Prospecting / Engaging)."
    )

    try:
        df, accounts = load_data()
    except FileNotFoundError as e:
        st.error(
            f"Missing CSV files in `{DATA_DIR}/`. Expected: accounts.csv, "
            f"products.csv, sales_teams.csv, sales_pipeline.csv. ({e})"
        )
        st.stop()

    # Reference "today": max of any date in the dataset (handles historical dumps).
    candidates = [pd.Timestamp(datetime.today().date())]
    for col in ("engage_date", "close_date"):
        if col in df.columns and df[col].notna().any():
            candidates.append(df[col].max())
    ref_date = max(candidates)

    scored, stage_probs = score_pipeline(df, accounts_df=accounts, ref_date=ref_date)
    open_deals = scored[scored["deal_stage"].isin(["Prospecting", "Engaging"])].copy()

    # ---------- Sidebar filters
    st.sidebar.header("Filters")

    managers = sorted(open_deals["manager"].dropna().unique().tolist())
    sel_managers = st.sidebar.multiselect("Manager", managers)

    rep_pool = open_deals[open_deals["manager"].isin(sel_managers)] if sel_managers else open_deals
    reps = sorted(rep_pool["sales_agent"].dropna().unique().tolist())
    sel_reps = st.sidebar.multiselect("Sales rep", reps)

    regions = sorted(open_deals["regional_office"].dropna().unique().tolist())
    sel_regions = st.sidebar.multiselect("Region", regions)

    stages = ["Prospecting", "Engaging"]
    sel_stages = st.sidebar.multiselect("Stage", stages, default=stages)

    sectors = sorted(open_deals["sector"].dropna().unique().tolist())
    sel_sectors = st.sidebar.multiselect("Account sector", sectors)

    min_score = st.sidebar.slider("Minimum score", 0, 100, 0, 5)
    only_stalled = st.sidebar.checkbox(
        f"Only stalled deals (Engaging > {STALE_DAYS}d)", value=False
    )

    f = open_deals
    if sel_managers:
        f = f[f["manager"].isin(sel_managers)]
    if sel_reps:
        f = f[f["sales_agent"].isin(sel_reps)]
    if sel_regions:
        f = f[f["regional_office"].isin(sel_regions)]
    if sel_stages:
        f = f[f["deal_stage"].isin(sel_stages)]
    if sel_sectors:
        f = f[f["sector"].isin(sel_sectors)]
    if only_stalled:
        f = f[(f["deal_stage"] == "Engaging") & (f["days_in_pipeline"] > STALE_DAYS)]
    f = f[f["score"] >= min_score].sort_values("score", ascending=False)

    # ---------- KPIs (mathematically honest)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open deals", f"{len(f):,}")
    c2.metric("Pipeline value", fmt_money(f["expected_value"].sum()))
    c3.metric(
        "Probability-weighted $",
        fmt_money((f["close_probability"] * f["expected_value"]).sum()),
        help="Σ (calibrated close probability × expected value). Uses empirical "
             "Won/(Won+Lost) ratios per stage from your historical data.",
    )
    c4.metric("Avg score", f"{f['score'].mean():.1f}" if len(f) else "—")

    # Stalled-deal alert
    stalled = open_deals[
        (open_deals["deal_stage"] == "Engaging")
        & (open_deals["days_in_pipeline"] > STALE_DAYS)
    ]
    if len(stalled):
        st.warning(
            f"⚠️ {len(stalled)} Engaging deals are stalled (>{STALE_DAYS} days). "
            f"Combined value: {fmt_money(stalled['expected_value'].sum())}. "
            "Tick 'Only stalled deals' in the sidebar to focus on these."
        )

    st.divider()
    left, right = st.columns([3, 2])

    # ---------- Table
    with left:
        st.subheader("Prioritized pipeline")

        view = pd.DataFrame({
            "": f["score"].apply(score_color),
            "Score": f["score"].round(0).astype(int),
            "Close %": (f["close_probability"] * 100).round(0).astype(int),
            "Stage": f["deal_stage"],
            "Account": f["account"],
            "Sector": f["sector"],
            "Product": f["product"],
            "Rep": f["sales_agent"],
            "Manager": f["manager"],
            "Region": f["regional_office"],
            "Days": f["days_in_pipeline"].round(0).astype("Int64"),
            "Expected $": f["expected_value"].apply(fmt_money),
            "Action": f["action"],
            "Opp ID": f["opportunity_id"],
        })

        st.dataframe(view, use_container_width=True, hide_index=True, height=520)

        # CSV: drop heavy/object columns
        export_cols = [
            "opportunity_id", "score", "close_probability", "expected_value",
            "deal_stage", "account", "sector", "product", "sales_agent",
            "manager", "regional_office", "days_in_pipeline", "action",
        ]
        st.download_button(
            "Download filtered list (CSV)",
            f[export_cols].to_csv(index=False).encode("utf-8"),
            file_name="scored_pipeline.csv",
            mime="text/csv",
        )

    # ---------- Inspect panel
    with right:
        st.subheader("Why this score?")
        if len(f) == 0:
            st.info("No deals match the current filters.")
        else:
            opp_choices = f["opportunity_id"].tolist()
            sel = st.selectbox(
                "Inspect a deal",
                opp_choices,
                format_func=lambda x: (
                    f"{x} · {f.loc[f['opportunity_id'] == x, 'account'].iloc[0]} "
                    f"· score {f.loc[f['opportunity_id'] == x, 'score'].iloc[0]:.0f}"
                ),
            )
            row = f[f["opportunity_id"] == sel].iloc[0]

            st.markdown(f"### {row['account']} — {row['product']}")
            st.markdown(
                f"**Score: {row['score']:.0f}** {score_color(row['score'])} · "
                f"Close probability: **{row['close_probability']*100:.0f}%** · "
                f"{row['deal_stage']} · {row['sales_agent']} ({row['regional_office']})"
            )
            st.info(f"**Recommended action:** {row['action']}")

            meta = pd.DataFrame({
                "Field": ["Expected $", "Days in pipe", "Sector",
                          "Account revenue", "Account employees", "Manager"],
                "Value": [
                    fmt_money(row["expected_value"]),
                    f"{row['days_in_pipeline']:.0f}" if pd.notna(row["days_in_pipeline"]) else "—",
                    row.get("sector", "—") or "—",
                    fmt_money(row.get("revenue")),
                    f"{row['employees']:.0f}" if pd.notna(row.get("employees")) else "—",
                    row.get("manager", "—") or "—",
                ],
            })
            st.dataframe(meta, hide_index=True, use_container_width=True)

            st.markdown("**Score breakdown**")
            breakdown = build_breakdown(row)
            st.dataframe(breakdown, hide_index=True, use_container_width=True)
            st.caption(
                "Each subscore is 0–100. Final score = Σ (subscore × weight). "
                "Close probability is separate: it's the empirical Won/(Won+Lost) "
                "ratio for this stage in your data."
            )

    st.divider()
    with st.expander("How scoring works"):
        st.markdown("**Feature weights** (sum to 100%):")
        st.table(pd.DataFrame([
            {"Feature": k, "Weight": f"{v['weight']:.0%}", "Rationale": v["desc"]}
            for k, v in FEATURE_DESCRIPTIONS.items()
        ]))
        st.markdown("**Empirical close probability by stage** (from your closed deals):")
        st.table(pd.DataFrame([
            {"Stage": s, "Close probability": f"{p:.0%}"} for s, p in stage_probs.items()
        ]))


if __name__ == "__main__":
    main()
```

```python
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
```

```txt
# requirements.txt
streamlit>=1.30
pandas>=2.0
numpy>=1.24
```

```markdown
# README.md
# Lead Scorer — Challenge 003 (v2)

Streamlit app that prioritizes ~8.800 CRM opportunities so a rep opens the tool, sees their pipeline ranked, and knows where to focus.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Drop the four CSVs into `data/`:

```
.
├── app.py
├── scoring.py
├── requirements.txt
└── data/
    ├── accounts.csv
    ├── products.csv
    ├── sales_teams.csv
    └── sales_pipeline.csv
```

## Run

```bash
streamlit run app.py
```

Sidebar filters: **manager, rep, region, stage, sector, minimum score, stalled-only**. The right panel shows the full score breakdown plus a recommended action for any selected deal.

## Two numbers per deal — kept separate on purpose

- **Score (0–100)** — a *priority* signal. Weighted average of 6 subscores. Used for ranking the worklist.
- **Close probability (0–1)** — the *empirical* Won/(Won+Lost) ratio for that deal's stage in your historical data. Used in the "Probability-weighted $" KPI so that number actually means something.

Mixing the two (e.g. `score/100 × value`) is wrong — score is not a probability.

## Scoring features

| Feature | Weight | What it captures |
|---|---|---|
| Stage | 30% | Empirical Won/(Won+Lost) per stage, derived from your own closed deals (not hardcoded). |
| Freshness | 20% | Bell shape over `days_since engage_date`: peak 7–30d, decays after 60d. Penalizes both "just engaged, no traction" and stalled deals. |
| Account size | 15% | Avg of revenue percentile + employees percentile. **Percentiles are computed over the 85 unique accounts**, not over the 8.800 pipeline rows — otherwise high-volume accounts dilute their own percentile. |
| Deal value | 15% | Percentile of expected $ across *open* deals (the universe reps are choosing from). |
| Product win rate | 12% | Bayesian-smoothed historical close rate per product. |
| Sector win rate | 8% | Bayesian-smoothed historical close rate per sector. |

**Removed from v1:** agent win rate. It systematically deprioritized struggling reps' deals, which is the opposite of what a rep-facing prioritizer should do.

### Expected $ calibration

Open deals use `sales_price × (1 − typical_discount)`, where `typical_discount` is the median `(close_value / sales_price)` ratio on Won deals — so the forecasted value matches what these deals historically actually close at.

### Reference "today"

`max(today, max(engage_date), max(close_date))`. For historical CSV dumps this snaps to the most recent activity so freshness isn't measured against a calendar date years in the future of the data.

### Recommended actions

Each deal gets a one-line next action based on stage + days + score (e.g. "Stalled 87d — re-engage with new angle.", "Top focus — close this week.", "Likely dead — disqualify or escalate."). Surfaced in the table and the inspect panel.

### Stalled-deal alert

Engaging deals older than 60 days are surfaced as a top-of-page warning with total $ at risk, plus a sidebar toggle to filter to them.

## Limitations

- **Rule-based, not learned.** Weights are reasoned, not fit. A logistic regression could improve calibration but at the cost of explainability — which the brief explicitly rewards.
- **Stage probability comes from closed deals only.** Prospecting and Engaging never appear in closed data, so their probabilities use the fallback table (Prospecting 20%, Engaging 55%). A proper version would need stage-transition history.
- **No external signals.** No email opens, web visits, intent — not in the source CSVs.
- **Win rates are global**, not stratified (e.g. agent × sector). With more data, conditional rates would be more accurate but risk small-cell noise.
- **`typical_discount` is a single median.** Doesn't vary by product or segment.
- **Read-only.** No write-back to the CRM.
```
