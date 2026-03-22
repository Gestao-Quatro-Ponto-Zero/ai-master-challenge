"""
Lead Scorer — Pipeline Inteligente.

Aplicacao Streamlit que orquestra todos os componentes do Lead Scorer:
carregamento de dados, scoring, NBA, filtros, metricas, pipeline view
e detalhe de deal.

Ponto de entrada: streamlit run app.py
"""

import pandas as pd
import streamlit as st

from utils.data_loader import load_data, get_reference_date
from scoring.engine import ScoringEngine
from scoring.nba import calcular_nba_batch
from components.filters import render_filters, apply_filters, render_filter_summary
from components.metrics import render_metrics
from components.pipeline_view import render_pipeline_view, prepare_pipeline_data
from components.deal_detail import render_deal_detail

# ============================================================================
# 9.1 — Page Config & CSS
# ============================================================================

st.set_page_config(
    page_title="Lead Scorer — Pipeline Inteligente",
    page_icon="\U0001f3af",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
    }
    [data-testid="stSidebar"] {
        min-width: 280px;
        max-width: 320px;
    }
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    [data-testid="stSidebarNav"] button,
    [data-testid="stSidebar"] button[kind="header"] {
        display: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    [data-testid="stSidebar"][aria-expanded="false"] {
        display: block !important;
        min-width: 280px !important;
        max-width: 320px !important;
        transform: none !important;
        margin-left: 0 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px;
    }
    .zombie-tag {
        background-color: #e74c3c;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75em;
        font-weight: bold;
    }
    .zombie-critical-tag {
        background-color: #c0392b;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75em;
        font-weight: bold;
    }
    .nba-risco {
        border-left: 4px solid #e74c3c;
        padding-left: 12px;
    }
    .nba-alerta {
        border-left: 4px solid #f1c40f;
        padding-left: 12px;
    }
    .nba-oportunidade {
        border-left: 4px solid #2ecc71;
        padding-left: 12px;
    }
    .nba-orientacao {
        border-left: 4px solid #3498db;
        padding-left: 12px;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================================
# 9.4 — Performance: cached data loading & scoring
# ============================================================================


@st.cache_data(show_spinner="Carregando dados...")
def _load_data() -> dict:
    """Carrega e retorna os 4 DataFrames do dataset."""
    return load_data("data")


@st.cache_data(show_spinner="Calculando scores...")
def _score_pipeline(
    _pipeline_df: pd.DataFrame,
    _accounts_df: pd.DataFrame,
    _products_df: pd.DataFrame,
    _sales_teams_df: pd.DataFrame,
) -> pd.DataFrame:
    """Executa o scoring engine e retorna o DataFrame scored."""
    engine = ScoringEngine(
        _pipeline_df, _accounts_df, _products_df, _sales_teams_df
    )
    return engine.score_pipeline()


@st.cache_data(show_spinner="Calculando acoes recomendadas...")
def _calculate_nba(
    _scored_df: pd.DataFrame,
    _pipeline_df: pd.DataFrame,
    _products_df: pd.DataFrame,
) -> dict:
    """Calcula NBA batch e retorna dict[opportunity_id, NBAResult]."""
    return calcular_nba_batch(_scored_df, _pipeline_df, _products_df)


# ============================================================================
# 9.2 — Component Integration
# ============================================================================


def _add_column_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas alias para compatibilidade entre componentes.

    O scoring engine gera 'score_final' e 'effective_value', mas os
    componentes de filtros e metricas esperam 'score' e 'estimated_value'.
    """
    result = df.copy()
    if "score_final" in result.columns and "score" not in result.columns:
        result["score"] = result["score_final"]
    if "effective_value" in result.columns and "estimated_value" not in result.columns:
        result["estimated_value"] = result["effective_value"]
    return result


def main():
    """Fluxo principal da aplicacao."""

    # --- 1. Carregar dados ---
    data = _load_data()
    pipeline_df = data["pipeline"]
    accounts_df = data["accounts"]
    products_df = data["products"]
    sales_teams_df = data["sales_teams"]

    # --- 2. Scoring ---
    scored_df = _score_pipeline(pipeline_df, accounts_df, products_df, sales_teams_df)

    # --- 3. NBA ---
    nba_results = _calculate_nba(scored_df, pipeline_df, products_df)

    # --- 4. Adicionar aliases de colunas ---
    scored_df = _add_column_aliases(scored_df)

    # --- 5. Sidebar: filtros ---
    filter_state = render_filters(sales_teams_df, products_df, accounts_df)

    # --- 6. Aplicar filtros ---
    df_filtered = apply_filters(scored_df, filter_state)

    # --- 7. Resumo de filtros na sidebar ---
    render_filter_summary(df_filtered, scored_df)

    # --- 8. Titulo e cabecalho ---
    st.title("Lead Scorer")
    st.caption("Priorizacao inteligente de pipeline")
    ref_date = get_reference_date()
    st.caption(f"Data de referencia: {ref_date.strftime('%d/%m/%Y')}")

    if filter_state.agent == "Todos":
        st.info(
            "Selecione um vendedor na barra lateral para ver o pipeline personalizado."
        )

    # --- 9. Metricas ---
    active_filters = {
        "office": filter_state.office,
        "manager": filter_state.manager,
        "agent": filter_state.agent,
    }
    render_metrics(df_filtered, scored_df, active_filters, pipeline_df)

    # --- 10. Separador ---
    st.markdown("---")

    # --- 11. Pipeline view ---
    st.subheader("Pipeline")
    df_display = prepare_pipeline_data(df_filtered)
    render_pipeline_view(df_display)

    # --- 12. Abrir modal de detalhe se deal foi selecionado ---
    if st.session_state.get("_open_deal_dialog"):
        st.session_state["_open_deal_dialog"] = False
        selected_opp_id = st.session_state.get("deal_selecionado")
        if selected_opp_id:
            deal_rows = scored_df[scored_df["opportunity_id"] == selected_opp_id]
            if not deal_rows.empty:
                deal = deal_rows.iloc[0]
                breakdown = deal.get("score_breakdown", {})
                nba = nba_results.get(selected_opp_id)
                _show_deal_dialog(deal, breakdown, nba)


# ============================================================================
# 9.3 — Deal Detail Dialog
# ============================================================================


@st.dialog("Detalhe do Deal", width="large")
def _show_deal_dialog(deal, breakdown, nba):
    """Modal com detalhe completo do deal: score, breakdown e acoes."""
    render_deal_detail(deal, breakdown)

    st.markdown("---")

    if nba and nba.tem_acao:
        _render_nba_result(nba)


def _render_nba_result(nba) -> None:
    """Renderiza o resultado do NBA para o deal selecionado."""
    st.markdown("#### Acoes Recomendadas")

    # Acao principal
    acao = nba.acao_principal
    tipo_css = f"nba-{acao.tipo}"
    st.markdown(
        f'<div class="{tipo_css}">'
        f"<strong>{acao.nome}</strong><br>"
        f"{acao.mensagem}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Acoes secundarias
    if nba.acoes_secundarias:
        st.markdown("**Outras acoes:**")
        for sec in nba.acoes_secundarias:
            tipo_css_sec = f"nba-{sec.tipo}"
            st.markdown(
                f'<div class="{tipo_css_sec}" style="margin-top:8px">'
                f"<strong>{sec.nome}</strong><br>"
                f"{sec.mensagem}"
                f"</div>",
                unsafe_allow_html=True,
            )


# ============================================================================
# Ponto de entrada
# ============================================================================

if __name__ == "__main__":
    main()
else:
    # Streamlit executa o modulo diretamente, nao via __main__
    main()
