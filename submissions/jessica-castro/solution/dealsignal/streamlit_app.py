"""
DealSignal - Streamlit App

Run with:
    streamlit run streamlit_app.py
""" 

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Resolve project root and add to sys.path so all internal imports work
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config.constants import (  # noqa: E402
    RATING_COLORS,
    RATING_ORDER,
    RATING_RANGES,
)
from utils.report import (  # noqa: E402
    generate_csv,
    generate_pdf,
    make_csv_filename,
    make_pdf_filename,
)
from app.ui.data_loaders import ALL, load_metadata, load_results  # noqa: E402
from app.ui.deal_panel import render_deal_insight_panel  # noqa: E402
from app.ui.filters import (  # noqa: E402
    _init_filters,
    _reset_filters,
    _validate_and_apply_cascade,
)
from app.ui.formatters import _rating_badge  # noqa: E402
from app.ui.signals_builder import build_display_dataframe, build_signals_for_deal  # noqa: E402
from app.ui.ui_constants import APP_CSS, _CHART_FONT  # noqa: E402
from app.ui.charts import (  # noqa: E402
    render_top_opportunities,
    render_pipeline_by_rating,
    render_friction_distribution,
    render_velocity_map,
)

# ── Page config (must be the first Streamlit call) ────────────────────────────
st.set_page_config(page_title="DealSignal", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)


# ── Hide sidebar toggle button ────────────────────────────────────────────────
st.markdown(
    "<style>"
    "[data-testid='stSidebarCollapsedControl'] { display:none !important; }"
    "[data-testid='stSidebarNav'] { display:none !important; }"
    "</style>",
    unsafe_allow_html=True,
)


# ── Escala dialog ─────────────────────────────────────────────────────────────
@st.dialog("Escala de Rating")
def _show_escala_dialog():
    rating_rows = "".join(
        f"<tr>"
        f"<td style='padding:4px 8px;'>{_rating_badge(r)}</td>"
        f"<td style='padding:4px 8px; font-size:13px; color:#555;'>{RATING_RANGES[r]}</td>"
        f"</tr>"
        for r in RATING_ORDER
    )
    st.markdown(
        f"<table style='border-collapse:collapse; width:100%;'>{rating_rows}</table>",
        unsafe_allow_html=True,
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    logo_path = ROOT / "assets" / "dealsignal_logo.png"

    df       = load_results()
    metadata = load_metadata()

    if df.empty:
        st.error(
            "Nenhum resultado encontrado. Execute o pipeline primeiro:\n\n"
            "```bash\npython run_pipeline.py\n```"
        )
        return

    _init_filters()
    st.session_state.setdefault("chart_days_filter", None)
    st.session_state.setdefault("chart_rating_filter", None)
    valid = _validate_and_apply_cascade(df)

    # ── Lê estado atual → aplica filtros → calcula KPIs (antes de renderizar) ─
    selected_office  = st.session_state["sel_office"]
    selected_manager = st.session_state["sel_manager"]
    selected_agent   = st.session_state["sel_agent"]
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
    # Apply chart-driven filters
    _DAYS_BINS = {
        "0–30 dias":  (0,   30),
        "30–60 dias": (30,  60),
        "60–90 dias": (60,  90),
        "90+ dias":   (90,  99999),
    }
    if st.session_state.get("chart_days_filter"):
        lo, hi = _DAYS_BINS[st.session_state["chart_days_filter"]]
        filtered = filtered[
            (filtered["days_since_engage"] >= lo) &
            (filtered["days_since_engage"] < hi)
        ]
    if st.session_state.get("chart_rating_filter"):
        filtered = filtered[filtered["deal_rating"] == st.session_state["chart_rating_filter"]]

    filtered = filtered.sort_values("expected_revenue", ascending=False).reset_index(drop=True)

    avg_prob = filtered["win_probability"].mean() if not filtered.empty else 0
    priority_count = int(filtered["deal_rating"].isin(["AAA", "AA"]).sum()) if not filtered.empty else 0

    def _fmt_millions(v: float) -> str:
        return f"{v / 1_000_000:.1f} M".replace(".", ",")

    # Weekly sparklines from engage_date
    def _weekly_series(df: pd.DataFrame, col: str, agg: str = "sum") -> list:
        if df.empty or "engage_date" not in df.columns:
            return []
        tmp = df.copy()
        tmp["_week"] = pd.to_datetime(tmp["engage_date"], errors="coerce").dt.to_period("W")
        tmp = tmp.dropna(subset=["_week"])
        if tmp.empty:
            return []
        grouped = tmp.groupby("_week")[col].agg(agg).sort_index()
        return grouped.tolist()

    def _weekly_count_series(df: pd.DataFrame, condition=None) -> list:
        if df.empty or "engage_date" not in df.columns:
            return []
        tmp = df.copy() if condition is None else df[condition].copy()
        tmp["_week"] = pd.to_datetime(tmp["engage_date"], errors="coerce").dt.to_period("W")
        tmp = tmp.dropna(subset=["_week"])
        if tmp.empty:
            return []
        return tmp.groupby("_week").size().sort_index().tolist()

    spark_pipeline  = _weekly_series(filtered, "effective_value", "sum")
    spark_receita   = _weekly_series(filtered, "expected_revenue", "sum")
    spark_prob      = _weekly_series(filtered, "win_probability", "mean")
    spark_total     = _weekly_count_series(filtered)
    spark_priority  = _weekly_count_series(filtered, filtered["deal_rating"].isin(["AAA", "AA"]))

    kpis = {
        "Pipeline Total":      _fmt_millions(filtered["effective_value"].sum()),
        "Receita Esperada":    _fmt_millions(filtered["expected_revenue"].sum()),
        "Probabilidade Média": f"{avg_prob * 100:.0f}%",
        "Deals Totais":        str(len(filtered)),
        "Deals Prioritários":  str(priority_count),
    }
    active_filters = {
        "Escritório": selected_office,
        "Gerente":    selected_manager,
        "Vendedor":   selected_agent,
    }

    # ── Header: logo + caption ────────────────────────────────────────────────
    hdr_logo, hdr_text = st.columns([1.6, 5])
    with hdr_logo:
        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)
    with hdr_text:
        st.markdown(
            "<div style='padding-top:18px; font-size:13px; color:#888;'>"
            "Score de oportunidades: priorize os deals certos no momento certo"
            "</div>",
            unsafe_allow_html=True,
        )

    # ── 1. KPIs ───────────────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Pipeline Total",      kpis["Pipeline Total"],     chart_data=spark_pipeline, chart_type="line")
    col2.metric("Receita Esperada",    kpis["Receita Esperada"],   chart_data=spark_receita,  chart_type="line")
    col3.metric("Probabilidade Média", kpis["Probabilidade Média"],chart_data=spark_prob,     chart_type="line")
    col4.metric("Deals Totais",        kpis["Deals Totais"],       chart_data=spark_total,    chart_type="line")
    col5.metric("Deals Prioritários",  kpis["Deals Prioritários"], chart_data=spark_priority, chart_type="line")

    # ── 2. Barra de filtros horizontais ──────────────────────────────────────
    st.divider()
    flabel, f1, f2, f3, f4, f5 = st.columns([0.5, 1, 1, 1, 1, 0.7])
    with flabel:
        st.markdown("<div style='padding-top:8px; font-size:18px; color:#000;'>Filtros</div>", unsafe_allow_html=True)
    with f1:
        st.selectbox("Escritório", options=[ALL] + valid["office"],      key="sel_office",  label_visibility="collapsed",
                     format_func=lambda x: "Escritório" if x == ALL else x)
    with f2:
        st.selectbox("Gerente",    options=[ALL] + valid["manager"],     key="sel_manager", label_visibility="collapsed",
                     format_func=lambda x: "Gerente" if x == ALL else x)
    with f3:
        st.selectbox("Vendedor",   options=[ALL] + valid["sales_agent"], key="sel_agent",   label_visibility="collapsed",
                     format_func=lambda x: "Vendedor" if x == ALL else x)
    with f4:
        rating_label = f"Rating ({len(ratings)})" if ratings else "Rating (0)"
        with st.popover(rating_label, use_container_width=True):
            st.multiselect(
                "Ratings",
                options=RATING_ORDER,
                default=RATING_ORDER,
                key="sel_ratings",
                label_visibility="collapsed",
            )
    with f5:
        st.button("Limpar", on_click=_reset_filters, use_container_width=True)

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns([4, 1.5])

    # Compute table_df first so title shows accurate count
    search_text = st.session_state.get("_pipeline_search", "")
    table_df = filtered.copy()
    if search_text:
        q = search_text.strip().lower()
        mask = (
            table_df["account"].str.lower().str.contains(q, na=False)
            | table_df["product"].str.lower().str.contains(q, na=False)
            | table_df["opportunity_id"].astype(str).str.lower().str.contains(q, na=False)
        )
        table_df = table_df[mask].reset_index(drop=True)
    with col_left:
        tbl_title, tbl_search, tbl_csv, tbl_pdf, tbl_info = st.columns([3, 3, 1, 1, 1])
        with tbl_title:
            st.markdown(
                f"#### Ranking de Oportunidades "
                f"<span style='font-size:12px; font-weight:400; color:#888;'>",

                unsafe_allow_html=True,
            )
        with tbl_search:
            new_search = st.text_input(
                "Buscar",
                value=search_text,
                placeholder="Buscar por conta, produto ou ID…",
                label_visibility="collapsed",
                key="_pipeline_search",
            )
            if new_search != search_text:
                st.rerun()
        with tbl_csv:
            st.download_button(
                label="↓ CSV",
                data=generate_csv(filtered),
                file_name=make_csv_filename(active_filters),
                mime="text/csv",
                use_container_width=True,
            )
        with tbl_pdf:
            st.download_button(
                label="↓ PDF",
                data=generate_pdf(filtered, kpis, active_filters, metadata),
                file_name=make_pdf_filename(active_filters),
                mime="application/pdf",
                use_container_width=True,
            )
        with tbl_info:
            if st.button("ⓘ", use_container_width=True):
                _show_escala_dialog()

    with col_left:

        display_df = build_display_dataframe(table_df)
        display_df["Conta"] = [
            f"Top 10 🔥 {v}" if i < 10 else v
            for i, v in enumerate(display_df["Conta"])
        ]
        display_df = display_df[
            ["opportunity_id", "Rating", "Etapa", "Conta", "Produto", "Valor", "Rec. Esperada", "_win_prob"]
        ]

        event = st.dataframe(
            display_df,
            column_config={
                "Rating":        st.column_config.TextColumn("Rating"),
                "Etapa":         st.column_config.TextColumn("Etapa"),
                "Conta":         st.column_config.TextColumn("Conta"),
                "Produto":       st.column_config.TextColumn("Produto"),
                "_win_prob":     None,
                "Valor":         st.column_config.TextColumn("Preço Prod."),
                "Rec. Esperada": st.column_config.TextColumn("Receita Estim."),
                "opportunity_id": st.column_config.TextColumn("Id"),
            },
            use_container_width=True,
            height=760,
            selection_mode="single-row",
            on_select="rerun",
            hide_index=True,
            key="pipeline_table",
        )
        rows = event.selection.rows
        if rows:
            st.session_state["selected_deal_id"] = display_df.iloc[rows[0]]["opportunity_id"]

    # Validate that the selected deal is still in the filtered dataset
    selected_id = st.session_state.get("selected_deal_id")
    if selected_id and selected_id not in filtered["opportunity_id"].values:
        st.session_state["selected_deal_id"] = None
        selected_id = None

    with col_right:
        if selected_id:
            row     = filtered[filtered["opportunity_id"] == selected_id].iloc[0]
            payload = build_signals_for_deal(row, filtered)
            render_deal_insight_panel(row, payload, df, auc=metadata.get("cv_auc"))
        else:
            st.info("← Clique em uma linha da tabela para ver a análise do deal.")

    st.divider()

    # ── Badge de filtros de gráfico ativos ────────────────────────────────────
    active_chart_filters = [v for v in [
        st.session_state.get("chart_days_filter"),
        st.session_state.get("chart_rating_filter"),
    ] if v]
    if active_chart_filters:
        badge_col, clear_col = st.columns([8, 1])
        with badge_col:
            st.caption(f"Filtro ativo: {' · '.join(active_chart_filters)}")
        with clear_col:
            if st.button("✕ Limpar", key="clear_chart_filters"):
                st.session_state["chart_days_filter"] = None
                st.session_state["chart_rating_filter"] = None
                st.rerun()

    # ── Gráficos operacionais: esquerda empilhada | direita quadrante ─────────
    col_left, col_right = st.columns(2)
    with col_left:
        sub_a, sub_b = st.columns(2)
        with sub_a:
            days_click = render_top_opportunities(filtered)
        with sub_b:
            render_friction_distribution(filtered)
        rating_click = render_pipeline_by_rating(filtered)
    with col_right:
        deal_click = render_velocity_map(filtered)

    # Processar cliques (toggle: clicar no mesmo valor limpa o filtro)
    if days_click is not None:
        current = st.session_state.get("chart_days_filter")
        st.session_state["chart_days_filter"] = None if current == days_click else days_click
        st.rerun()

    if rating_click is not None:
        current = st.session_state.get("chart_rating_filter")
        st.session_state["chart_rating_filter"] = None if current == rating_click else rating_click
        st.rerun()

    if deal_click is not None:
        st.session_state["selected_deal_id"] = deal_click
        st.rerun()


if __name__ == "__main__":
    main()
