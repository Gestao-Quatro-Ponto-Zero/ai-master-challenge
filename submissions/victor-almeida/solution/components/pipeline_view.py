"""
Pipeline View — tabela principal do Lead Scorer.

Funcoes puras (testaveis sem Streamlit):
- prepare_pipeline_data: filtra deals ativos, ordena por score, formata colunas
- get_velocity_status: converte ratio de velocidade em label textual
- format_zombie_tag: retorna tag visual para deals zumbi

Funcoes de UI (dependem de Streamlit):
- render_pipeline_view: renderiza tabela do pipeline com st.dataframe
"""

import pandas as pd

from scoring.constants import ACTIVE_STAGES
from utils.formatters import format_currency, format_days, score_color, score_label

PAGE_SIZE = 25


# ---------------------------------------------------------------------------
# Funcoes puras — preparacao de dados
# ---------------------------------------------------------------------------


def prepare_pipeline_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara DataFrame para exibicao: filtra ativos, ordena, formata colunas.

    Args:
        df: DataFrame do pipeline enriquecido com scores.

    Returns:
        DataFrame com colunas de exibicao prontas:
        - score_final (original)
        - opportunity_id
        - account (NaN substituido por 'Sem conta')
        - product
        - valor_display (moeda formatada usando sales_price para deals ativos)
        - deal_stage
        - dias_display (dias formatados, '\u2014' para Prospecting)
        - sales_agent
        - is_zombie
    """
    # Filtrar apenas deals ativos (Prospecting + Engaging)
    active = df[df["deal_stage"].isin(ACTIVE_STAGES)].copy()

    # Ordenar por score descendente
    active = active.sort_values("score_final", ascending=False)

    # Formatar colunas de exibicao
    active["account"] = active["account"].fillna("Sem conta")
    active["valor_display"] = active["sales_price"].apply(format_currency)
    active["dias_display"] = active.apply(
        lambda r: "\u2014"
        if r["deal_stage"] == "Prospecting"
        else format_days(None if pd.isna(r.get("days_in_stage")) else r.get("days_in_stage")),
        axis=1,
    )

    return active


def get_velocity_status(ratio: float | None) -> str:
    """Retorna label de status de velocidade a partir do ratio.

    Args:
        ratio: Ratio tempo atual / tempo referencia. None se sem dados.

    Returns:
        Label textual: 'saudavel', 'no limite', 'parado', 'em risco', 'zumbi', 'sem dados'.
    """
    if ratio is None:
        return "sem dados"
    if ratio <= 1.0:
        return "saudavel"
    if ratio <= 1.2:
        return "no limite"
    if ratio <= 1.5:
        return "parado"
    if ratio <= 2.0:
        return "em risco"
    return "zumbi"


def format_zombie_tag(is_zombie: bool, is_critical: bool = False) -> str:
    """Retorna tag visual para deals zumbi ou string vazia.

    Args:
        is_zombie: Se o deal e zumbi.
        is_critical: Se o deal e zumbi critico.

    Returns:
        'ZUMBI CRITICO', 'ZUMBI', ou '' (vazio).
    """
    if is_critical:
        return "ZUMBI CRITICO"
    if is_zombie:
        return "ZUMBI"
    return ""


# ---------------------------------------------------------------------------
# Funcoes de UI (Streamlit) — nao testadas em unit tests
# ---------------------------------------------------------------------------


def render_pipeline_view(df_scored: pd.DataFrame) -> str | None:
    """Renderiza tabela do pipeline com Streamlit.

    Args:
        df_scored: DataFrame preparado por prepare_pipeline_data.

    Returns:
        opportunity_id do deal selecionado, ou None.
    """
    import streamlit as st

    if df_scored.empty:
        st.info("Nenhum deal encontrado com os filtros atuais.")
        return None

    total = len(df_scored)
    st.markdown(f"**{total} deals ativos** no pipeline")

    # Paginacao
    page = st.session_state.get("pipeline_page", 0)
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_df = df_scored.iloc[start:end]

    # Exibir tabela
    for _, row in page_df.iterrows():
        color = score_color(row["score_final"])
        label = score_label(row["score_final"])
        zombie_tag = format_zombie_tag(
            row.get("is_zombie", False),
            row.get("is_critical_zombie", False),
        )

        opp_id = row["opportunity_id"]

        col_score, col_info, col_value, col_days, col_btn = st.columns(
            [1, 3, 1, 1, 0.6]
        )

        with col_score:
            st.markdown(
                f"<span style='color:{color}; font-size:1.4em; font-weight:bold'>"
                f"{row['score_final']:.0f}</span> "
                f"<span style='color:{color}; font-size:0.8em'>{label}</span>",
                unsafe_allow_html=True,
            )

        with col_info:
            agent_text = row.get("sales_agent", "")
            account_text = row.get("account", "")
            product_text = row.get("product", "")
            zombie_html = (
                f" <span style='color:#e74c3c; font-weight:bold'>{zombie_tag}</span>"
                if zombie_tag
                else ""
            )
            st.markdown(
                f"**{account_text}** — {product_text}{zombie_html}<br>"
                f"<span style='font-size:0.85em; color:#888'>{agent_text} | {row.get('deal_stage', '')}</span>",
                unsafe_allow_html=True,
            )

        with col_value:
            st.markdown(f"**{row['valor_display']}**")

        with col_days:
            st.markdown(row["dias_display"])

        with col_btn:
            if st.button("Ver", key=f"ver_{opp_id}"):
                st.session_state["deal_selecionado"] = opp_id
                st.session_state["_open_deal_dialog"] = True
                st.rerun()

    # Navegacao de paginas
    if total > PAGE_SIZE:
        max_page = (total - 1) // PAGE_SIZE
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("\u2190 Anterior", disabled=(page == 0)):
                st.session_state["pipeline_page"] = max(0, page - 1)
                st.rerun()
        with col_info:
            st.markdown(f"Pagina {page + 1} de {max_page + 1}")
        with col_next:
            if st.button("Proximo \u2192", disabled=(page >= max_page)):
                st.session_state["pipeline_page"] = min(max_page, page + 1)
                st.rerun()

    return None
