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
