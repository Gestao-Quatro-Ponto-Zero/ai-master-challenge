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
            # NOTE: baseline bug — original used row['product'] on a namedtuple
            # (raw-output.md preserved). Fixed to row.product so the app runs.
            label_map = {
                row.opportunity_id: f"{row.account} · {row.product} · "
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
