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
