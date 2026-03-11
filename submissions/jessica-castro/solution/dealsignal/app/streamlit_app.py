"""
DealSignal - Streamlit App

Run with:
    streamlit run app/streamlit_app.py
"""

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Resolve project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

RESULTS_PATH = ROOT / "data" / "results.csv"
METADATA_PATH = ROOT / "model" / "artifacts" / "metadata.json"

RATING_COLORS = {
    "AAA": "#1a7a1a",
    "AA": "#2ecc71",
    "A": "#82e0aa",
    "BBB": "#f39c12",
    "BB": "#e67e22",
    "B": "#e74c3c",
    "CCC": "#922b21",
}

RATING_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DealSignal",
    page_icon="📈",
    layout="wide",
)

st.markdown(
    """
    <style>
    .metric-card { background: #1e1e2e; border-radius: 8px; padding: 16px; }
    .stDataFrame { font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Data loaders ─────────────────────────────────────────────────────────────
@st.cache_data
def load_results() -> pd.DataFrame:
    if not RESULTS_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(RESULTS_PATH)
    df["win_probability"] = pd.to_numeric(df["win_probability"], errors="coerce")
    df["expected_revenue"] = pd.to_numeric(df["expected_revenue"], errors="coerce")
    df["effective_value"] = pd.to_numeric(df["effective_value"], errors="coerce")
    return df


@st.cache_data
def load_metadata() -> dict:
    if not METADATA_PATH.exists():
        return {}
    with open(METADATA_PATH) as f:
        return json.load(f)


def color_rating(val: str) -> str:
    color = RATING_COLORS.get(val, "#888888")
    return f"background-color: {color}; color: white; font-weight: bold; border-radius: 4px; padding: 2px 6px;"


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    st.title("📈 DealSignal — Deal Rating Engine")
    st.caption("AI-powered opportunity prioritization based on win probability and expected revenue")

    df = load_results()
    metadata = load_metadata()

    if df.empty:
        st.error(
            "No results found. Run the pipeline first:\n\n"
            "```bash\npython run_pipeline.py\n```"
        )
        return

    # ── Sidebar filters ───────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Filters")

        agents = ["All"] + sorted(df["sales_agent"].dropna().unique().tolist())
        selected_agent = st.selectbox("Sales Agent", agents)

        managers = ["All"] + sorted(df["manager"].dropna().unique().tolist())
        selected_manager = st.selectbox("Manager", managers)

        offices = ["All"] + sorted(df["office"].dropna().unique().tolist())
        selected_office = st.selectbox("Regional Office", offices)

        ratings = st.multiselect(
            "Rating",
            options=RATING_ORDER,
            default=RATING_ORDER,
        )

        st.divider()
        st.caption("DealSignal v1.0")
        if metadata:
            st.caption(f"Model AUC: {metadata.get('cv_auc', '—')}")
            st.caption(f"Features: {metadata.get('n_features', '—')}")
            st.caption(f"Trained on: {metadata.get('n_train', '—')} deals")

    # Apply filters
    filtered = df.copy()
    if selected_agent != "All":
        filtered = filtered[filtered["sales_agent"] == selected_agent]
    if selected_manager != "All":
        filtered = filtered[filtered["manager"] == selected_manager]
    if selected_office != "All":
        filtered = filtered[filtered["office"] == selected_office]
    if ratings:
        filtered = filtered[filtered["deal_rating"].isin(ratings)]

    filtered = filtered.sort_values("expected_revenue", ascending=False)

    # ── KPI cards ─────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    total_er = filtered["expected_revenue"].sum()
    top10_er = filtered.head(10)["expected_revenue"].sum()
    n_deals = len(filtered)
    auc = metadata.get("cv_auc", None)

    col1.metric("Total Pipeline (Expected Revenue)", f"${total_er:,.0f}")
    col2.metric("Top 10 Expected Revenue", f"${top10_er:,.0f}")
    col3.metric("Open Deals", str(n_deals))
    col4.metric("Model AUC", f"{auc:.3f}" if auc else "—")

    st.divider()

    # ── Top 10 chart ──────────────────────────────────────────────────────────
    st.subheader("🎯 Top 10 Deals to Prioritize")

    top10 = filtered.head(10).copy()
    top10["label"] = top10["account"] + " · " + top10["product"]
    top10["win_pct"] = (top10["win_probability"] * 100).round(1)

    if not top10.empty:
        fig = px.bar(
            top10,
            x="expected_revenue",
            y="label",
            orientation="h",
            color="deal_rating",
            color_discrete_map=RATING_COLORS,
            category_orders={"deal_rating": RATING_ORDER},
            text=top10["win_pct"].astype(str) + "%",
            labels={"expected_revenue": "Expected Revenue ($)", "label": ""},
            height=420,
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            yaxis={"autorange": "reversed"},
            showlegend=True,
            legend_title="Rating",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No deals match the current filters.")

    st.divider()

    # ── Full pipeline table ───────────────────────────────────────────────────
    st.subheader("📋 Full Pipeline")
    st.caption(f"Showing {len(filtered)} deals — sorted by Expected Revenue (descending)")

    display_cols = [
        "deal_rating", "account", "product", "sales_agent",
        "win_probability", "expected_revenue", "effective_value",
        "top_contributing_factors",
    ]
    available = [c for c in display_cols if c in filtered.columns]
    table = filtered[available].copy()

    # Format columns
    table["win_probability"] = (table["win_probability"] * 100).round(1).astype(str) + "%"
    table["expected_revenue"] = table["expected_revenue"].apply(lambda x: f"${x:,.0f}")
    table["effective_value"] = table["effective_value"].apply(lambda x: f"${x:,.0f}")

    # Rename for display
    table = table.rename(columns={
        "deal_rating": "Rating",
        "account": "Account",
        "product": "Product",
        "sales_agent": "Sales Agent",
        "win_probability": "Win Prob",
        "expected_revenue": "Exp. Revenue",
        "effective_value": "Deal Value",
        "top_contributing_factors": "Key Factors",
    })

    styled = table.style.applymap(color_rating, subset=["Rating"])
    st.dataframe(styled, use_container_width=True, height=500)

    # ── Rating distribution ───────────────────────────────────────────────────
    with st.expander("📊 Rating Distribution"):
        rating_counts = (
            filtered["deal_rating"]
            .value_counts()
            .reindex(RATING_ORDER)
            .dropna()
            .reset_index()
        )
        rating_counts.columns = ["Rating", "Count"]

        fig2 = px.bar(
            rating_counts,
            x="Rating",
            y="Count",
            color="Rating",
            color_discrete_map=RATING_COLORS,
            category_orders={"Rating": RATING_ORDER},
            text="Count",
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)


if __name__ == "__main__":
    main()
