"""
Deal Detail — painel de detalhe de um deal selecionado.

Funcoes puras (testaveis sem Streamlit):
- build_explanation: gera texto explicativo do score de um deal
- build_next_action_text: gera recomendacao de proxima acao

Funcoes de UI (dependem de Streamlit):
- render_deal_detail: renderiza painel de detalhe em expander
"""

import pandas as pd

from utils.formatters import format_currency, format_days, score_color, score_label

# Labels em PT-BR para os componentes do score
COMPONENT_LABELS = {
    "stage": "Etapa",
    "expected_value": "Valor do Deal",
    "velocity": "Velocidade",
    "seller_fit": "Afinidade do Vendedor",
    "account_health": "Historico da Conta",
}


# ---------------------------------------------------------------------------
# Funcoes puras — preparacao de textos
# ---------------------------------------------------------------------------


def build_explanation(deal: pd.Series, breakdown: dict) -> str:
    """Gera texto explicativo legivel para o score de um deal.

    Args:
        deal: Series com dados do deal (deal_stage, days_in_stage, etc).
        breakdown: Dicionario score_breakdown do scoring engine.

    Returns:
        String com explicacao do score em linguagem natural.
    """
    score = breakdown.get("score_final", 0)
    stage = deal.get("deal_stage", "")
    days = deal.get("days_in_stage")
    velocity = breakdown["components"]["velocity"]
    value = breakdown["components"]["expected_value"]
    seller_fit = breakdown["components"]["seller_fit"]

    parts = [f"Score {score:.0f}"]

    if stage == "Engaging" and days is not None and not (isinstance(days, float) and pd.isna(days)):
        parts.append(f"Deal em Engaging ha {int(days)} dias ({velocity['label']})")
    elif stage == "Prospecting":
        parts.append("Deal em fase inicial de Prospecting")

    parts.append(value["detail"])
    parts.append(seller_fit["detail"])

    return ". ".join(parts) + "."


def build_next_action_text(deal: pd.Series, breakdown: dict) -> str:
    """Gera recomendacao de proxima acao para um deal.

    Prioriza alertas (zumbi > risco > parado) e depois recomendacoes positivas.

    Args:
        deal: Series com dados do deal.
        breakdown: Dicionario score_breakdown do scoring engine.

    Returns:
        String com recomendacao de acao.
    """
    flags = breakdown.get("flags", {})
    velocity = breakdown["components"]["velocity"]
    ratio = velocity.get("ratio")
    score = breakdown.get("score_final", 0)

    if flags.get("is_zombie"):
        days = deal.get("days_in_stage", "?")
        if isinstance(days, float) and pd.isna(days):
            days = "?"
        return f"Deal parado ha {days} dias. Avaliar se vale manter no pipeline ou marcar como perdido."

    if ratio and ratio > 1.5:
        return "Deal em risco. Agendar follow-up urgente ou requalificar."

    if ratio and ratio > 1.0:
        return "Deal parado. Enviar case de sucesso para reengajar."

    if score >= 80:
        return "Deal saudavel e de alto valor. Prioridade maxima para fechar."

    if deal.get("deal_stage") == "Prospecting":
        return "Deal em fase inicial. Qualificar necessidade e agendar primeiro contato."

    return "Deal em andamento saudavel. Manter cadencia de follow-up."


# ---------------------------------------------------------------------------
# Funcoes de UI (Streamlit) — nao testadas em unit tests
# ---------------------------------------------------------------------------


def render_deal_detail(deal: pd.Series, breakdown: dict) -> None:
    """Renderiza painel de detalhe de um deal em expander Streamlit.

    Args:
        deal: Series com dados do deal.
        breakdown: Dicionario score_breakdown do scoring engine.
    """
    import streamlit as st

    from components.pipeline_view import format_zombie_tag

    score = breakdown.get("score_final", 0)
    color = score_color(score)
    label = score_label(score)

    # Cabecalho
    st.markdown(
        f"### <span style='color:{color}'>{score:.0f}</span> — {label}",
        unsafe_allow_html=True,
    )

    # Zombie flag
    flags = breakdown.get("flags", {})
    zombie_tag = format_zombie_tag(
        flags.get("is_zombie", False),
        flags.get("is_critical_zombie", False),
    )
    if zombie_tag:
        st.error(f"**{zombie_tag}** — {flags.get('zombie_detail', '')}")

    # Informacoes basicas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Conta", deal.get("account", "—"))
    with col2:
        st.metric("Produto", deal.get("product", "—"))
    with col3:
        st.metric("Vendedor", deal.get("sales_agent", "—"))

    # Breakdown de componentes
    st.markdown("#### Composicao do Score")
    components = breakdown.get("components", {})
    for name, comp in components.items():
        pct = comp["weight"] * 100
        display_name = COMPONENT_LABELS.get(name, name.replace("_", " ").title())
        st.markdown(
            f"- **{display_name}** "
            f"({pct:.0f}%): {comp['score']:.0f} pts "
            f"= {comp['weighted']:.1f} — {comp['detail']}"
        )

    # Explicacao
    st.markdown("#### Por que este score?")
    explanation = build_explanation(deal, breakdown)
    st.info(explanation)

    # Proxima acao
    st.markdown("#### Proxima acao recomendada")
    action = build_next_action_text(deal, breakdown)
    st.success(action)
