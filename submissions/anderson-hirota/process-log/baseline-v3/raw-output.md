## 1. Critique

1. **Freshness is silently dead for Prospecting deals.** `engage_date` is NaN before a deal enters Engaging, so `days_in_pipeline` is NaN → `_freshness_vec` falls back to 50 (neutral) → 20% of the score collapses to a constant for roughly half the open pipeline. The README sells "Bell shape over days_since engage_date" as if it applies everywhere; it doesn't.

2. **README oversells `close_probability` as "empirical."** For open stages it's literally the hardcoded `STAGE_PROB_FALLBACK` (Prospecting 0.20, Engaging 0.55), because Prospecting/Engaging never appear in closed data. The "Probability-weighted $" KPI is therefore `0.20·sum(prospecting_$) + 0.55·sum(engaging_$)` — a fixed linear combo dressed up as calibration. v1's "score × value" was honest about being a heuristic; v2 hides one behind better vocabulary.

3. **Bell-shaped freshness penalizes fresh leads (<7d → 80, not 100) with no justification.** A rep who just engaged a hot lead today gets a *worse* freshness subscore than the same lead two weeks from now. The brief says scoring should make sense to a non-technical rep — this won't.

4. **No account-level context anywhere.** With 8.8k opportunities across 85 accounts (~100 deals/account avg), the worklist will repeatedly show the same account with different products. There's no "X other open deals at this account" column, no rollup, no dedup hint. A rep prioritizing will call the same buyer six times.

5. **Recommended action ignores time for Prospecting.** A 300-day-old Prospecting deal gets the same "Qualify or disqualify quickly" copy as one created yesterday. The whole stalled-deal philosophy is applied only to Engaging.

6. **The inspect-panel selectbox is unusable at scale.** It's populated with every `opportunity_id` in the filter result — easily thousands — and labeled by ID, which reps don't recognize. No search-by-account, no top-N cap.

7. **The table has no user-controlled sort.** Locked to score-desc. A rep who wants "biggest $ I could close this week" or "most-stalled first" can't get there without re-filtering. Cheap fix, real UX win.

## 2. v3

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
    PROSPECT_STALE_DAYS,
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


SORT_OPTIONS = {
    "Score (high → low)": ("score", False),
    "Expected $ (high → low)": ("expected_value", False),
    "Days in pipeline (most stale)": ("days_in_pipeline", False),
    "Days in pipeline (freshest)": ("days_in_pipeline", True),
    "Close probability (high → low)": ("close_probability", False),
}


def main():
    st.title("🎯 Lead Scorer — Pipeline Prioritization")
    st.caption(
        "Rule-based scoring with stage-conditional weighting. "
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

    candidates = [pd.Timestamp(datetime.today().date())]
    for col in ("engage_date", "close_date"):
        if col in df.columns and df[col].notna().any():
            candidates.append(df[col].max())
    ref_date = max(candidates)

    scored, stage_probs = score_pipeline(df, accounts_df=accounts, ref_date=ref_date)
    open_deals = scored[scored["deal_stage"].isin(["Prospecting", "Engaging"])].copy()

    # Account-level context: open deals per account.
    open_per_account = open_deals.groupby("account").size().rename("account_open_deals")
    open_deals = open_deals.merge(open_per_account, on="account", how="left")
    open_deals["other_open_at_account"] = (open_deals["account_open_deals"] - 1).clip(lower=0)

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

    accts = sorted(open_deals["account"].dropna().unique().tolist())
    sel_accts = st.sidebar.multiselect("Account", accts)

    min_score = st.sidebar.slider("Minimum score", 0, 100, 0, 5)
    only_stalled = st.sidebar.checkbox(
        f"Only stalled (Engaging >{STALE_DAYS}d or Prospecting >{PROSPECT_STALE_DAYS}d)",
        value=False,
    )
    sort_label = st.sidebar.selectbox("Sort by", list(SORT_OPTIONS.keys()), index=0)
    sort_col, sort_asc = SORT_OPTIONS[sort_label]

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
    if sel_accts:
        f = f[f["account"].isin(sel_accts)]
    if only_stalled:
        f = f[
            ((f["deal_stage"] == "Engaging") & (f["days_in_pipeline"] > STALE_DAYS))
            | ((f["deal_stage"] == "Prospecting") & (f["days_in_pipeline"] > PROSPECT_STALE_DAYS))
        ]
    f = f[f["score"] >= min_score].sort_values(sort_col, ascending=sort_asc, na_position="last")

    # ---------- KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open deals", f"{len(f):,}")
    c2.metric("Pipeline value", fmt_money(f["expected_value"].sum()))
    c3.metric(
        "Probability-weighted $",
        fmt_money((f["close_probability"] * f["expected_value"]).sum()),
        help=(
            "Σ (cohort close-rate × expected value). Engaging rate = "
            "Won/(Won+Lost) among deals that reached Engaging. Prospecting rate "
            "= overall historical win rate, since every deal was once a prospect."
        ),
    )
    c4.metric("Avg score", f"{f['score'].mean():.1f}" if len(f) else "—")

    stalled = open_deals[
        ((open_deals["deal_stage"] == "Engaging") & (open_deals["days_in_pipeline"] > STALE_DAYS))
        | ((open_deals["deal_stage"] == "Prospecting") & (open_deals["days_in_pipeline"] > PROSPECT_STALE_DAYS))
    ]
    if len(stalled):
        st.warning(
            f"⚠️ {len(stalled)} stalled deals "
            f"(Engaging >{STALE_DAYS}d or Prospecting >{PROSPECT_STALE_DAYS}d). "
            f"Combined value: {fmt_money(stalled['expected_value'].sum())}. "
            "Tick 'Only stalled' in the sidebar to focus on these."
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
            "Other open": f["other_open_at_account"].astype("Int64"),
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
        st.caption(
            "**Other open** = additional open opportunities at the same account "
            "(batch the call). **Days** is blank for Prospecting with no engage date."
        )

        export_cols = [
            "opportunity_id", "score", "close_probability", "expected_value",
            "deal_stage", "account", "sector", "product", "sales_agent",
            "manager", "regional_office", "days_in_pipeline",
            "other_open_at_account", "action",
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
            top = f.head(200)
            st.caption(
                f"Inspect any of the top {len(top)} in the current view "
                f"(of {len(f):,} filtered)."
            )
            label_map = {
                row.opportunity_id: f"{row.account} · {row['product']} · "
                                    f"score {row.score:.0f} · {row.sales_agent}"
                for row in top.itertuples()
            }
            sel = st.selectbox(
                "Inspect a deal",
                top["opportunity_id"].tolist(),
                format_func=lambda x: label_map.get(x, x),
            )
            row = f[f["opportunity_id"] == sel].iloc[0]

            st.markdown(f"### {row['account']} — {row['product']}")
            st.markdown(
                f"**Score: {row['score']:.0f}** {score_color(row['score'])} · "
                f"Close prob: **{row['close_probability']*100:.0f}%** · "
                f"{row['deal_stage']} · {row['sales_agent']} ({row['regional_office']})"
            )
            st.info(f"**Recommended action:** {row['action']}")

            other_n = int(row["other_open_at_account"])
            if other_n > 0:
                st.caption(
                    f"📎 {other_n} other open deal(s) at **{row['account']}** — "
                    "consider batching outreach."
                )

            meta = pd.DataFrame({
                "Field": ["Expected $", "Days in pipe", "Sector",
                          "Account revenue", "Account employees", "Manager"],
                "Value": [
                    fmt_money(row["expected_value"]),
                    f"{row['days_in_pipeline']:.0f}" if pd.notna(row["days_in_pipeline"]) else "— (not yet engaged)",
                    row.get("sector") or "—",
                    fmt_money(row.get("revenue")),
                    f"{row['employees']:.0f}" if pd.notna(row.get("employees")) else "—",
                    row.get("manager") or "—",
                ],
            })
            st.dataframe(meta, hide_index=True, use_container_width=True)

            st.markdown("**Score breakdown**")
            breakdown = build_breakdown(row)
            st.dataframe(breakdown, hide_index=True, use_container_width=True)
            st.caption(
                "Each subscore is 0–100. Final score = Σ (subscore × weight). "
                "For Prospecting deals without an engage date, freshness is "
                "omitted and the remaining weights are renormalized — so a "
                "missing time signal doesn't silently penalize the deal."
            )

    st.divider()
    with st.expander("How scoring works"):
        st.markdown("**Feature weights** (sum to 100% when all features apply):")
        st.table(pd.DataFrame([
            {"Feature": k, "Weight": f"{v['weight']:.0%}", "Rationale": v["desc"]}
            for k, v in FEATURE_DESCRIPTIONS.items()
        ]))
        st.markdown("**Stage close-rate (cohort-derived)**:")
        st.table(pd.DataFrame([
            {"Stage": s, "Close rate": f"{p:.0%}"} for s, p in stage_probs.items()
        ]))
        st.markdown(
            "- **Engaging rate**: Won / (Won+Lost) among closed deals that have "
            "an `engage_date` (i.e. ever reached Engaging).\n"
            "- **Prospecting rate**: overall historical win rate — every closed "
            "deal was once a prospect, so this is the natural cohort.\n"
            "- These are real conditional probabilities, not hardcoded fallbacks."
        )


if __name__ == "__main__":
    main()
```

```python
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
```

```txt
# requirements.txt
streamlit>=1.32
pandas>=2.1
numpy>=1.26
```

```markdown
# README.md
# Lead Scorer — Challenge 003 (v3)

Streamlit app that prioritizes ~8.8k CRM opportunities. A rep opens the tool, sees their pipeline ranked, knows where to focus, and can read off *why* any given deal scored what it did.

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

Run:

```bash
streamlit run app.py
```

## Two numbers per deal — kept separate on purpose

- **Score (0–100)** — priority signal. Weighted sum of subscores. Used for ranking the worklist.
- **Close probability (0–1)** — cohort-derived empirical close rate (see below). Used in the "Probability-weighted $" KPI.

Mixing the two (e.g. `score/100 × value`) would be wrong — score is not a probability.

## Scoring features

| Feature | Weight | What it captures |
|---|---:|---|
| Stage | 28% | Cohort close-rate for current stage (see below). |
| Freshness | 18% | Monotone decay over days since `engage_date`. **Omitted, with remaining weights renormalized, when `engage_date` is null** — so Prospecting deals aren't silently penalized for a missing time signal. |
| Account size | 15% | Avg of revenue percentile + employees percentile across the **85 unique accounts** (not 8.8k pipeline rows). |
| Deal value | 16% | Percentile of expected $ across open deals (the universe reps choose from). |
| Product win rate | 15% | Bayesian-smoothed historical close rate per product. |
| Sector win rate | 8% | Bayesian-smoothed historical close rate per sector. |

### Expected $ calibration

Open deals: `sales_price × (1 − typical_discount)`, where `typical_discount` is the median `(close_value / sales_price)` ratio on Won deals.

### Stage close rate — cohort-derived, not hardcoded

The "Probability-weighted $" KPI multiplies value by a **real conditional probability**:

- **Engaging**: `Won / (Won + Lost)` among closed deals with `engage_date` set — i.e. deals that actually reached Engaging.
- **Prospecting**: overall historical `Won / Closed`. Every closed deal was once a prospect, so the full closed cohort is the right denominator.

v2 hardcoded these (20% / 55%) as a fallback. v3 derives them from your data.

### Freshness handling for Prospecting

Prospecting deals typically have no `engage_date` → no time signal. v2 silently neutralized freshness to 50, leaving the score quietly biased. v3 drops freshness from the score for those deals and renormalizes the other weights so they sum to 100%. The breakdown panel shows this explicitly.

### Reference "today"

`max(today, max(engage_date), max(close_date))`. Snaps to the most recent data point so historical dumps don't get freshness measured against a calendar date far past the data.

### Account-level context

The table includes an **Other open** column — how many other open opportunities exist at the same account. The inspect panel surfaces a note when there are siblings. Reps can batch outreach instead of calling the same buyer six times.

### Sort & filters

- Sidebar filters: manager, rep, region, stage, sector, **account**, min score, stalled-only.
- Sort by: score, expected $, days (most stale / freshest), close probability.
- Stalled-only covers both Engaging >60d **and** Prospecting >90d.
- Inspect panel limits its selectbox to the top 200 visible deals, labeled by account/product/score/rep — opportunity IDs are not human-readable.

### Recommended actions

Per-deal one-liner from `(stage, days, score)`. Prospecting now considers age (`Old prospect (Xd) — qualify hard or drop.`, `Stale prospect — disqualify.`), not just stage. Engaging keeps the v2 stalled/top-focus logic.

## Limitations

- **Rule-based, not learned.** Weights are reasoned, not fit. A logistic regression could improve calibration at the cost of explainability — which the brief explicitly rewards.
- **No stage-transition history.** We can identify "ever reached Engaging" via `engage_date`, but can't see *when* it entered Engaging, dwell times, regressions, etc.
- **No external signals.** No email opens, web visits, intent — not in source CSVs.
- **Win rates are global**, not stratified (e.g. agent × sector). Conditional rates risk small-cell noise on this dataset.
- **`typical_discount` is a single median**, not per-product/segment.
- **Read-only.** No write-back to the CRM.
- **No agent-quality feature.** Including rep win-rate would systematically deprioritize struggling reps' deals — the opposite of what a rep-facing prioritizer should do.
```
