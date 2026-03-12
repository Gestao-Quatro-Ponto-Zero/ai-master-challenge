"""
DealSignal - Streamlit App

Run with:
    streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

# Resolve project root and add to sys.path so all internal imports work
ROOT = Path(__file__).parent.parent
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
from app.ui.formatters import _rating_badge, format_currency  # noqa: E402
from app.ui.signals_builder import build_display_dataframe, build_signals_for_deal  # noqa: E402
from app.ui.ui_constants import APP_CSS, _CHART_FONT, _CHART_MARGIN  # noqa: E402

# ── Page config (must be the first Streamlit call) ────────────────────────────
st.set_page_config(page_title="DealSignal", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    logo_path = ROOT / "assets" / "dealsignal_logo.png"
    if logo_path.exists():
        st.image(str(logo_path), width=260)
    st.caption(
        "Priorização inteligente de oportunidades com base em "
        "probabilidade de fechamento e receita esperada"
    )

    df       = load_results()
    metadata = load_metadata()

    if df.empty:
        st.error(
            "Nenhum resultado encontrado. Execute o pipeline primeiro:\n\n"
            "```bash\npython run_pipeline.py\n```"
        )
        return

    _init_filters()
    valid = _validate_and_apply_cascade(df)

    # Aplicar filtros
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
    filtered = filtered.sort_values("expected_revenue", ascending=False).reset_index(drop=True)

    auc = metadata.get("cv_auc", None)
    kpis = {
        "Pipeline Total":  format_currency(filtered["expected_revenue"].sum()),
        "Top 10 Pipeline": format_currency(filtered.head(10)["expected_revenue"].sum()),
        "Deals Ativos":    str(len(filtered)),
        "AUC do Modelo":   f"{auc:.3f}" if auc else "—",
    }
    active_filters = {
        "Escritório": selected_office,
        "Gerente":    selected_manager,
        "Vendedor":   selected_agent,
    }

    # ── Sidebar — filtros + legenda de rating + downloads ─────────────────────
    with st.sidebar:
        st.header("Filtros")
        st.selectbox("Escritório", options=[ALL] + valid["office"],      key="sel_office")
        st.selectbox("Gerente",    options=[ALL] + valid["manager"],     key="sel_manager")
        st.selectbox("Vendedor",   options=[ALL] + valid["sales_agent"], key="sel_agent")

        st.multiselect(
            "Rating",
            options=RATING_ORDER,
            default=RATING_ORDER,
            key="sel_ratings",
        )
        st.button("Limpar Filtros", on_click=_reset_filters, use_container_width=True)

        st.markdown("**Escala de Rating**")
        rating_rows = "".join(
            f"<tr>"
            f"<td style='padding:3px 6px;'>{_rating_badge(r)}</td>"
            f"<td style='padding:3px 6px; font-size:12px; color:#555;'>{RATING_RANGES[r]}</td>"
            f"</tr>"
            for r in RATING_ORDER
        )
        st.markdown(
            f"<table style='border-collapse:collapse; width:100%;'>{rating_rows}</table>",
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown("**Exportar Relatório**")
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

    # ── KPIs ──────────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pipeline Total",  kpis["Pipeline Total"])
    col2.metric("Top 10 Pipeline", kpis["Top 10 Pipeline"])
    col3.metric("Deals Ativos",    kpis["Deals Ativos"])
    col4.metric("AUC do Modelo",   kpis["AUC do Modelo"])

    st.divider()

    # ── Top 10 + Distribuição por Rating lado a lado ───────────────────────────
    col_top10, col_dist = st.columns([2, 1])

    with col_top10:
        st.subheader("Top 10 Deals para Priorizar")
        top10 = filtered.head(10).copy()
        top10["label"]   = top10["account"] + " · " + top10["product"]
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
                labels={"expected_revenue": "", "label": ""},
                height=420,
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                yaxis={"autorange": "reversed"},
                showlegend=True,
                legend_title="Rating",
                legend=dict(orientation="v", x=1.01, y=1),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=_CHART_FONT,
                margin=_CHART_MARGIN,
                xaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum deal corresponde aos filtros selecionados.")

    with col_dist:
        st.subheader("Distribuição por Rating")
        rating_counts = (
            filtered["deal_rating"]
            .value_counts()
            .reindex(RATING_ORDER)
            .dropna()
            .reset_index()
        )
        rating_counts.columns = ["Rating", "Quantidade"]
        fig2 = px.bar(
            rating_counts,
            x="Rating",
            y="Quantidade",
            color="Rating",
            color_discrete_map=RATING_COLORS,
            category_orders={"Rating": RATING_ORDER},
            text="Quantidade",
            height=420,
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=_CHART_FONT,
            margin=_CHART_MARGIN,
            xaxis_title="",
            yaxis_title="Qtd",
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Master-detail: tabela (esquerda) | Análise do Deal (direita) ──────────
    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.markdown(
            f"#### Pipeline Completo "
            f"<span style='font-size:12px; font-weight:400; color:#888;'>"
            f"{len(filtered)} deals</span>",
            unsafe_allow_html=True,
        )

        display_df = build_display_dataframe(filtered)

        event = st.dataframe(
            display_df,
            column_config={
                "opportunity_id": None,
                "_win_prob": st.column_config.ProgressColumn(
                    "% Fechamento",
                    min_value=0,
                    max_value=100,
                    format="%.1f%%",
                    width="medium",
                ),
                "Rating":        st.column_config.TextColumn("Rating",        width="small"),
                "Conta":         st.column_config.TextColumn("Conta",         width="medium"),
                "Produto":       st.column_config.TextColumn("Produto",       width="medium"),
                "Vendedor":      st.column_config.TextColumn("Vendedor",      width="medium"),
                "Estágio":       st.column_config.TextColumn("Estágio",       width="medium"),
                "Engajamento":   st.column_config.TextColumn("Engajamento",   width="small"),
                "Rec. Esperada": st.column_config.TextColumn("Rec. Esperada", width="small"),
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
            render_deal_insight_panel(row, payload)
        else:
            st.info("← Clique em uma linha da tabela para ver a análise do deal.")


if __name__ == "__main__":
    main()
