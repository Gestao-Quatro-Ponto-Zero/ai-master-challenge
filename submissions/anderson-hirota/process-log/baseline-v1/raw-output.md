```python app.py
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from scoring import score_pipeline, FEATURE_DESCRIPTIONS

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
    return df, accounts, products, teams, pipeline


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
        "Rule-based scoring to help reps focus on the deals most likely to close "
        "with the biggest impact. Open deals only (Prospecting / Engaging)."
    )

    try:
        df, accounts, products, teams, pipeline = load_data()
    except FileNotFoundError as e:
        st.error(
            f"Missing CSV files in `{DATA_DIR}/`. Expected: accounts.csv, "
            f"products.csv, sales_teams.csv, sales_pipeline.csv. ({e})"
        )
        st.stop()

    today = pd.Timestamp(datetime.today().date())
    # Reference date: if pipeline data is historical, use max engage_date as "today"
    if df["engage_date"].notna().any():
        ref_date = max(today, df["engage_date"].max())
    else:
        ref_date = today

    scored = score_pipeline(df, ref_date=ref_date)
    open_deals = scored[scored["deal_stage"].isin(["Prospecting", "Engaging"])].copy()

    # ---- Sidebar filters
    st.sidebar.header("Filters")

    managers = sorted(open_deals["manager"].dropna().unique().tolist())
    sel_managers = st.sidebar.multiselect("Manager", managers, default=[])

    if sel_managers:
        rep_pool = open_deals[open_deals["manager"].isin(sel_managers)]
    else:
        rep_pool = open_deals
    reps = sorted(rep_pool["sales_agent"].dropna().unique().tolist())
    sel_reps = st.sidebar.multiselect("Sales rep", reps, default=[])

    regions = sorted(open_deals["regional_office"].dropna().unique().tolist())
    sel_regions = st.sidebar.multiselect("Region", regions, default=[])

    stages = ["Prospecting", "Engaging"]
    sel_stages = st.sidebar.multiselect("Stage", stages, default=stages)

    min_score = st.sidebar.slider("Minimum score", 0, 100, 0, 5)

    sectors = sorted(open_deals["sector"].dropna().unique().tolist())
    sel_sectors = st.sidebar.multiselect("Account sector", sectors, default=[])

    # Apply filters
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
    f = f[f["score"] >= min_score]

    f = f.sort_values("score", ascending=False)

    # ---- Top metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open deals", f"{len(f):,}")
    c2.metric("Expected value", fmt_money((f["score"] / 100 * f["expected_value"]).sum()))
    c3.metric("Pipeline value", fmt_money(f["expected_value"].sum()))
    c4.metric("Avg score", f"{f['score'].mean():.1f}" if len(f) else "—")

    st.divider()

    # ---- Layout
    left, right = st.columns([3, 2])

    with left:
        st.subheader("Prioritized pipeline")

        view = f.assign(
            **{
                "": f["score"].apply(score_color),
                "Score": f["score"].round(1),
                "Stage": f["deal_stage"],
                "Account": f["account"],
                "Sector": f["sector"],
                "Product": f["product"],
                "Rep": f["sales_agent"],
                "Manager": f["manager"],
                "Region": f["regional_office"],
                "Days in pipe": f["days_in_pipeline"].round(0).astype("Int64"),
                "Expected $": f["expected_value"].apply(fmt_money),
            }
        )[
            [
                "", "Score", "Stage", "Account", "Sector", "Product",
                "Rep", "Manager", "Region", "Days in pipe", "Expected $",
                "opportunity_id",
            ]
        ]

        st.dataframe(
            view,
            use_container_width=True,
            hide_index=True,
            height=520,
            column_config={
                "opportunity_id": st.column_config.TextColumn("Opp ID"),
            },
        )

        st.download_button(
            "Download filtered list (CSV)",
            f.to_csv(index=False).encode("utf-8"),
            file_name="scored_pipeline.csv",
            mime="text/csv",
        )

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
                f"{row['deal_stage']} · {row['sales_agent']} ({row['regional_office']})"
            )

            meta = pd.DataFrame(
                {
                    "Field": [
                        "Expected close value", "Days in pipeline",
                        "Sector", "Account revenue", "Account employees",
                        "Manager",
                    ],
                    "Value": [
                        fmt_money(row.get("expected_value")),
                        f"{row['days_in_pipeline']:.0f}" if pd.notna(row["days_in_pipeline"]) else "—",
                        row.get("sector", "—"),
                        fmt_money(row.get("revenue")),
                        f"{row['employees']:.0f}" if pd.notna(row.get("employees")) else "—",
                        row.get("manager", "—"),
                    ],
                }
            )
            st.dataframe(meta, hide_index=True, use_container_width=True)

            st.markdown("**Score breakdown**")
            breakdown = pd.DataFrame(row["breakdown"])
            breakdown["contribution"] = breakdown["contribution"].round(1)
            st.dataframe(
                breakdown.rename(
                    columns={
                        "feature": "Feature",
                        "value": "Raw value",
                        "subscore": "Subscore (0–100)",
                        "weight": "Weight",
                        "contribution": "Points",
                        "reason": "Why",
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )

            st.caption(
                "Subscores are 0–100. Final score = weighted average of subscores. "
                "Hover the table or read the README for full methodology."
            )

    st.divider()
    with st.expander("How scoring works"):
        st.markdown(
            "Each open deal gets a 0–100 score built from these weighted features:"
        )
        st.table(
            pd.DataFrame(
                [{"Feature": k, "Weight": v["weight"], "Rationale": v["desc"]}
                 for k, v in FEATURE_DESCRIPTIONS.items()]
            )
        )


if __name__ == "__main__":
    main()
```

```python scoring.py
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
```

```text requirements.txt
streamlit>=1.32
pandas>=2.0
numpy>=1.24
```

```markdown README.md
# Lead Scorer — Challenge 003

A Streamlit app that scores ~8.800 CRM opportunities so sales reps can focus on the deals most likely to close with the biggest impact, instead of prioritizing by gut feel.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Put the four CSV files inside a `data/` folder next to `app.py`:

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

The app opens in the browser. Use the sidebar to filter by **manager, sales rep, region, stage, sector, and minimum score**. Pick any deal in the right-hand panel to see the full score breakdown.

## Scoring logic

Each **open** opportunity (Prospecting or Engaging) gets a **0–100 score** computed as a weighted average of seven subscores. Closed deals (Won / Lost) are excluded from the priority list but still feed the historical win-rate features.

| Feature | Weight | What it captures |
|---|---|---|
| Stage | 25% | Engaging (80) is much closer to closing than Prospecting (35). |
| Agent win rate | 18% | Closed-deal win rate of the rep, Bayesian-smoothed with a global prior so reps with thin history don't dominate. |
| Product win rate | 12% | Some product lines close more reliably. |
| Sector win rate | 10% | Some industries convert better than others. |
| Freshness | 15% | Step function on days since `engage_date`: ≤14d = 100, ≤30d = 85, ≤60d = 65, ≤90d = 45, ≤180d = 25, else 10. Stale deals decay fast. |
| Account size | 10% | Percentile of `revenue` + percentile of `employees` (averaged). Bigger accounts → more budget. |
| Deal value | 10% | Percentile of expected $ (product price for open deals). Bigger deals get a modest bump — focus matters more there. |

Final score = `Σ (subscore × weight)`, rounded.

### Why these features
- **Stage** and **freshness** dominate close probability in any CRM — they're cheap signals with strong predictive value.
- **Agent / product / sector win rates** add a learned prior from your own historical closed deals, so the score gets smarter as more deals close. Win rates are smoothed (prior weight = 5) to avoid penalizing a rep with only 3 closed deals.
- **Account size + deal value** answer "what's at stake?" — two equally-likely-to-close deals aren't equal if one is worth 5×.
- All subscores are **on the same 0–100 scale**, so the breakdown table is directly readable: a rep sees exactly which feature pushed the score up or down.

### Explainability
The right-hand panel shows the full breakdown per deal: raw value, subscore, weight, points contributed, and a plain-English reason. That's the "why score 85" question answered without staring at code.

## Limitations

- **Rule-based, not learned.** Weights are reasoned, not optimized against held-out labels. A logistic regression on the closed deals could improve calibration — but at the cost of explainability, which the brief explicitly rewards.
- **No external signals.** No email opens, web visits, intent data, or contact-level engagement — the CRM tables don't have it.
- **Stage is binary-ish.** With only Prospecting / Engaging / Won / Lost, there's no early/mid/late distinction inside Engaging.
- **Freshness uses `engage_date`** as the start of the clock. If a deal was created but not engaged, days_in_pipeline is undefined and gets a neutral 50 — could be improved with a `created_date`.
- **Reference "today"** defaults to the max `engage_date` in the dataset (since the data is historical). For a live CRM, swap to actual `datetime.now()`.
- **Win rates are global**, not stratified (e.g., agent × sector). With more data, conditional rates would be more accurate but risk small-cell noise.
- **Expected value** for open deals = list price; doesn't account for typical discounting on Won deals.
- **No write-back.** This is a read-only prioritizer; it doesn't push scores back to the CRM.
```
