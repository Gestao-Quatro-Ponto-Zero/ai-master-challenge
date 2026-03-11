"""
DealSignal - Streamlit App

Run with:
    streamlit run app/streamlit_app.py
"""

import json
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

# Resolve project root and ensure utils/ is importable
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from utils.report import (  # noqa: E402
    generate_csv,
    generate_pdf,
    make_csv_filename,
    make_pdf_filename,
)
from utils.signals import (  # noqa: E402
    FEATURE_EXPLANATIONS,
    FEATURE_TO_ENGINE,
    compute_engine_scores,
    get_signals,
    parse_factors,
)

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

RATING_EMOJI = {
    "AAA": "🟢", "AA": "🟢", "A": "🟡",
    "BBB": "🟡", "BB": "🔴", "B": "🔴", "CCC": "🔴",
}


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


ALL = "All"
FILTER_KEYS = ["sel_office", "sel_manager", "sel_agent"]


# ── Formatadores ──────────────────────────────────────────────────────────────

def format_probability_bar(prob: float) -> str:
    pct = round(float(prob) * 100, 1)
    filled = max(0, min(10, round(float(prob) * 10)))
    return f"{pct}%  {'█' * filled}{'░' * (10 - filled)}"


def format_currency(value: float) -> str:
    return f"${value:,.0f}" if pd.notna(value) else "—"


# ── Display dataframe ─────────────────────────────────────────────────────────

def build_display_dataframe(scored_df: pd.DataFrame) -> pd.DataFrame:
    """Return a compact display-ready DataFrame for the pipeline table."""
    out = pd.DataFrame()
    out["opportunity_id"] = scored_df["opportunity_id"].values
    out["Rating"] = scored_df["deal_rating"].apply(
        lambda r: f"{RATING_EMOJI.get(r, '')} {r}"
    ).values
    out["Account"] = scored_df["account"].values
    out["Product"] = scored_df["product"].values
    out["Sales Agent"] = scored_df["sales_agent"].values
    out["Win Prob"] = scored_df["win_probability"].apply(format_probability_bar).values
    out["Exp. Revenue"] = scored_df["expected_revenue"].apply(format_currency).values
    out["Signals"] = scored_df["top_contributing_factors"].apply(
        lambda s: "  ".join(label for label, _ in get_signals(s, max_signals=2))
        if pd.notna(s) else ""
    ).values
    return out


# ── Signal payload ────────────────────────────────────────────────────────────

def build_signals_for_deal(row: pd.Series, df: pd.DataFrame) -> dict:
    """Build structured signal payload for the Deal Insight Panel."""
    factors_raw = row.get("top_contributing_factors", "")
    factors = parse_factors(str(factors_raw) if pd.notna(factors_raw) else "")

    seen_engines: set = set()
    positive_signals = []
    risk_signals = []
    for feat, val in factors:
        engine = FEATURE_TO_ENGINE.get(feat)
        if not engine or engine in seen_engines:
            continue
        seen_engines.add(engine)
        desc = FEATURE_EXPLANATIONS.get(feat, feat)
        entry = {"title": engine, "description": desc}
        if val > 0.05:
            positive_signals.append(entry)
        elif val < -0.05:
            risk_signals.append(entry)

    signals_short = "  ·  ".join(
        label for label, _ in get_signals(str(factors_raw) if pd.notna(factors_raw) else "", max_signals=3)
    )

    return {
        "signals_short": signals_short,
        "positive_signals": positive_signals[:3],
        "risk_signals": risk_signals[:3],
        "rating_engines": compute_engine_scores(row, df),
        "model_factors": factors,
    }


# ── Filter helpers ────────────────────────────────────────────────────────────

def _valid_options(df: pd.DataFrame, col: str, filters: dict) -> list:
    mask = pd.Series(True, index=df.index)
    for filter_col, value in filters.items():
        if filter_col != col and value != ALL:
            mask &= df[filter_col] == value
    return sorted(df.loc[mask, col].dropna().unique().tolist())


def _init_filters():
    for key in FILTER_KEYS:
        if key not in st.session_state:
            st.session_state[key] = ALL


def _reset_filters():
    for key in FILTER_KEYS:
        st.session_state[key] = ALL
    if "sel_ratings" in st.session_state:
        st.session_state["sel_ratings"] = RATING_ORDER
    if "sel_deal" in st.session_state:
        st.session_state["sel_deal"] = None


def _validate_and_apply_cascade(df: pd.DataFrame):
    current = {
        "office": st.session_state.get("sel_office", ALL),
        "manager": st.session_state.get("sel_manager", ALL),
        "sales_agent": st.session_state.get("sel_agent", ALL),
    }
    valid = {col: _valid_options(df, col, current) for col in current}
    if current["office"] != ALL and current["office"] not in valid["office"]:
        st.session_state["sel_office"] = ALL
    if current["manager"] != ALL and current["manager"] not in valid["manager"]:
        st.session_state["sel_manager"] = ALL
    if current["sales_agent"] != ALL and current["sales_agent"] not in valid["sales_agent"]:
        st.session_state["sel_agent"] = ALL
    return valid


# ── Pipeline table ────────────────────────────────────────────────────────────

def render_pipeline_table(display_df: pd.DataFrame) -> Optional[str]:
    """Render the compact pipeline table and return the selected opportunity_id."""
    st.dataframe(
        display_df,
        column_config={"opportunity_id": None},  # hide id column
        use_container_width=True,
        height=460,
    )

    # Deal selector — reliability-first approach using selectbox
    options = [None] + display_df["opportunity_id"].tolist()
    label_map = {None: "— Select a deal to inspect —"}
    label_map.update({
        oid: f"{row['Account']} · {row['Product']}"
        for oid, row in zip(display_df["opportunity_id"], display_df.to_dict("records"))
    })

    selected_id = st.selectbox(
        "Select deal to inspect:",
        options=options,
        format_func=lambda x: label_map.get(x, str(x)),
        key="sel_deal",
    )
    return selected_id


# ── Deal Insight Panel renderers ──────────────────────────────────────────────

def render_deal_header(row: pd.Series) -> None:
    rating = str(row.get("deal_rating", ""))
    rating_color = RATING_COLORS.get(rating, "#888888")

    st.markdown(
        f'<span style="background:{rating_color}; color:white; padding:5px 14px; '
        f'border-radius:6px; font-size:18px; font-weight:bold;">{rating}</span>',
        unsafe_allow_html=True,
    )
    st.write("")

    col_info, col_metrics = st.columns([1, 1])
    with col_info:
        st.markdown(f"**Account** &nbsp;&nbsp; {row.get('account', '—')}")
        st.markdown(f"**Product** &nbsp;&nbsp; {row.get('product', '—')}")
        st.markdown(f"**Sales Agent** &nbsp;&nbsp; {row.get('sales_agent', '—')}")
        st.markdown(f"**Office** &nbsp;&nbsp; {row.get('office', '—')}")

    with col_metrics:
        st.metric("Win Probability", format_probability_bar(row.get("win_probability", 0.0)))
        st.metric("Expected Revenue", format_currency(row.get("expected_revenue", 0.0)))
        st.metric("Deal Value", format_currency(row.get("effective_value", 0.0)))


def render_positive_signals(signal_payload: dict) -> None:
    st.markdown("#### ✅ Positive Signals")
    if signal_payload["positive_signals"]:
        for s in signal_payload["positive_signals"]:
            st.success(f"**{s['title']}** — {s['description']}")
    else:
        st.info("No strong positive signals identified.")


def render_risk_signals(signal_payload: dict) -> None:
    st.markdown("#### ⚠️ Risk Signals")
    if signal_payload["risk_signals"]:
        for s in signal_payload["risk_signals"]:
            st.error(f"**{s['title']}** — {s['description']}")
    else:
        st.info("No risk signals identified.")


def render_rating_engines(signal_payload: dict) -> None:
    st.markdown("#### ⚡ Rating Engines")
    for engine, score in signal_payload["rating_engines"].items():
        col1, col2 = st.columns([4, 1])
        col1.progress(score / 100, text=engine)
        col2.markdown(f"**{score}**")


def render_model_factors(signal_payload: dict) -> None:
    with st.expander("🔬 Model Factors"):
        factors = signal_payload["model_factors"]
        if factors:
            factors_df = pd.DataFrame(factors, columns=["Feature", "Contribution"])
            factors_df["Contribution"] = factors_df["Contribution"].map(lambda x: f"{x:+.3f}")
            st.dataframe(factors_df, hide_index=True, use_container_width=True)
        else:
            st.caption("No factor data available.")


def render_deal_insight_panel(row: pd.Series, signal_payload: dict) -> None:
    st.divider()
    st.subheader("🔍 Deal Insights")
    render_deal_header(row)
    st.divider()
    col_pos, col_risk = st.columns(2)
    with col_pos:
        render_positive_signals(signal_payload)
    with col_risk:
        render_risk_signals(signal_payload)
    st.divider()
    render_rating_engines(signal_payload)
    render_model_factors(signal_payload)


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

    _init_filters()
    valid = _validate_and_apply_cascade(df)

    # Apply filters (before sidebar so download buttons see filtered data)
    selected_office = st.session_state["sel_office"]
    selected_manager = st.session_state["sel_manager"]
    selected_agent = st.session_state["sel_agent"]
    ratings = st.session_state.get("sel_ratings", RATING_ORDER)

    filtered = df.copy()
    if selected_office != ALL:
        filtered = filtered[filtered["office"] == selected_office]
    if selected_manager != ALL:
        filtered = filtered[filtered["manager"] == selected_manager]
    if selected_agent != ALL:
        filtered = filtered[filtered["sales_agent"] == selected_agent]
    if ratings:
        filtered = filtered[filtered["deal_rating"].isin(ratings)]
    filtered = filtered.sort_values("expected_revenue", ascending=False).reset_index(drop=True)

    auc = metadata.get("cv_auc", None)
    kpis = {
        "Total Exp. Revenue": format_currency(filtered["expected_revenue"].sum()),
        "Top 10 Exp. Revenue": format_currency(filtered.head(10)["expected_revenue"].sum()),
        "Open Deals": str(len(filtered)),
        "Model AUC": f"{auc:.3f}" if auc else "—",
    }
    active_filters = {
        "Office": selected_office,
        "Manager": selected_manager,
        "Agent": selected_agent,
    }

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Filters")
        st.selectbox("Regional Office", options=[ALL] + valid["office"], key="sel_office")
        st.selectbox("Manager", options=[ALL] + valid["manager"], key="sel_manager")
        st.selectbox("Sales Agent", options=[ALL] + valid["sales_agent"], key="sel_agent")
        st.multiselect("Rating", options=RATING_ORDER, default=RATING_ORDER, key="sel_ratings")
        st.button("Clear Filters", on_click=_reset_filters, use_container_width=True)

        st.divider()
        st.markdown("**Download Report**")
        dl_col1, dl_col2 = st.columns(2)
        dl_col1.download_button(
            label="CSV",
            data=generate_csv(filtered),
            file_name=make_csv_filename(active_filters),
            mime="text/csv",
            use_container_width=True,
        )
        dl_col2.download_button(
            label="PDF",
            data=generate_pdf(filtered, kpis, active_filters, metadata),
            file_name=make_pdf_filename(active_filters),
            mime="application/pdf",
            use_container_width=True,
        )

        st.divider()
        st.caption("DealSignal v1.0")
        if metadata:
            st.caption(f"Model AUC: {metadata.get('cv_auc', '—')}")
            st.caption(f"Features: {metadata.get('n_features', '—')}")
            st.caption(f"Trained on: {metadata.get('n_train', '—')} deals")

    # ── KPI cards ─────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Pipeline (Exp. Revenue)", kpis["Total Exp. Revenue"])
    col2.metric("Top 10 Expected Revenue", kpis["Top 10 Exp. Revenue"])
    col3.metric("Open Deals", kpis["Open Deals"])
    col4.metric("Model AUC", kpis["Model AUC"])

    st.divider()

    # ── Top 10 chart + Rating Distribution (side by side) ────────────────────
    col_top10, col_dist = st.columns([2, 1])

    with col_top10:
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

    with col_dist:
        st.subheader("📊 Rating Distribution")
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
            height=420,
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Full pipeline table ───────────────────────────────────────────────────
    st.subheader("📋 Full Pipeline")
    st.caption(f"Showing {len(filtered)} deals — sorted by Expected Revenue (descending).")

    display_df = build_display_dataframe(filtered)
    selected_id = render_pipeline_table(display_df)

    # ── Deal Insight Panel ────────────────────────────────────────────────────
    if selected_id:
        row = filtered[filtered["opportunity_id"] == selected_id].iloc[0]
        payload = build_signals_for_deal(row, filtered)
        render_deal_insight_panel(row, payload)


if __name__ == "__main__":
    main()
