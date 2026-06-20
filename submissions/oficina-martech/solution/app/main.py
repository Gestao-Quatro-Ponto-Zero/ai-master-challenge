"""Foco — Lead Scorer (app Streamlit). Rodar: streamlit run app/main.py (ou make run).

Orquestração fina: configura página/tema, carrega dados (cacheados), monta a
sidebar (Visão / Regional / contexto por papel) e despacha para a view escolhida.
A lógica de cada tela vive em `app/views.py` (uma função por papel).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # permite rodar de qualquer cwd

import pandas as pd
import streamlit as st

from scoring.model import score_open_deals
from scoring.data import load_pipeline_health, load_outcome
from app.theme import inject_css
from app.views import (
    view_foco, view_time, view_saude,
    ALL_REGIONS, REGION_LABEL, FOCO_DIA_MIN,
)

st.set_page_config(page_title="Foco — O que fechar primeiro", page_icon="🎯", layout="wide")
inject_css(st)


@st.cache_resource(show_spinner="Inicializando banco de dados…")
def _ensure_db() -> None:
    """Auto-init do banco no primeiro boot (Streamlit Cloud / ambiente limpo)."""
    from db.migrate import migrate
    from db.seed import seed
    from scoring.data import DB_PATH
    if not DB_PATH.exists():
        migrate()
        seed()


_ensure_db()


@st.cache_data(show_spinner="Calculando prioridades…")
def get_data() -> tuple[pd.DataFrame, dict, dict]:
    """Score dos deals abertos + KPIs de saúde + outcome histórico (tudo cacheado)."""
    return score_open_deals(), load_pipeline_health(), load_outcome()


df_all, health, outcome = get_data()

# ---------------- Sidebar: marca + recortes ----------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
      <span class="sidebar-brand-icon">🎯</span>
      <span>
        <strong>Foco</strong>
        <small>O que fechar primeiro.</small>
      </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='sidebar-label'>Visão</div>", unsafe_allow_html=True)
    # drill-down do Time: o botão "Ver deals →" sinaliza a intenção via _go_foco;
    # consumimos ANTES de instanciar o widget (setar a key depois é proibido).
    if st.session_state.pop("_go_foco", False):
        st.session_state["view_select"] = "Foco do Dia"
    view = st.selectbox(
        "Visão",
        ["Foco do Dia", "Time", "Saúde"],
        label_visibility="collapsed",
        key="view_select",
        help="Escolha o recorte de decisão para a rotina de hoje.",
    )

    region_options = [ALL_REGIONS] + sorted(df_all["regional_office"].dropna().unique())
    selected_region = st.selectbox(
        "Regional",
        region_options,
        format_func=lambda region: REGION_LABEL.get(region, region),
        help="Filtra todos os números e listas pela regional escolhida.",
    )

df = df_all.copy()
if selected_region != ALL_REGIONS:
    df = df[df["regional_office"] == selected_region]

selected_agent = None
selected_manager = None

# contexto da sidebar por papel (depende do recorte já filtrado)
with st.sidebar:
    st.divider()
    if view == "Foco do Dia":
        agents = sorted(df["sales_agent"].dropna().unique())
        selected_agent = st.selectbox(
            "Vendedor", agents, key="agent_select",
            index=agents.index(st.session_state.get("_drill_agent", agents[0]))
            if st.session_state.get("_drill_agent") in agents else 0)
        scope = df[df["sales_agent"] == selected_agent]
        scope_vivos = scope[~scope["is_stale"]]
        fa = int((scope_vivos["tier"] == "Foco Agora").sum())
        tr = int((scope_vivos["tier"] == "Trabalhar").sum())
        atacar = min(FOCO_DIA_MIN, len(scope_vivos))
        st.markdown(
            f"""
            <div class="sidebar-summary">
              <span>Hoje</span>
              <strong>{atacar} para atacar</strong>
              <small>{fa} no pico · {tr} trabalhar</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif view == "Time":
        managers = sorted(df["manager"].dropna().unique())
        selected_manager = st.selectbox("Manager", managers, index=0)
        scope = df[df["manager"] == selected_manager]
        st.markdown(
            f"""
            <div class="sidebar-summary">
              <span>Time</span>
              <strong>{int((scope["tier"] == "Foco Agora").sum())} foco agora</strong>
              <small>{scope["sales_agent"].nunique()} vendedores no recorte</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # mesmo critério da tela de Saúde: sem conta SOBRE deals abertos (não total)
        pct = health["deals_sem_conta"] / health["open_deals"]
        st.markdown(
            f"""
            <div class="sidebar-summary">
              <span>Saúde</span>
              <strong>{pct:.0%} sem conta</strong>
              <small>{int(health["open_deals"])} deals abertos</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

# rodapé da sidebar: deixa explícito o "hoje" artificial do dataset histórico
with st.sidebar:
    st.caption(
        f"🗓 Pipeline avaliado em **{health['as_of_date']}** "
        "(último evento do dataset — base histórica, não a data de hoje)."
    )


# ---------------- Dispatch ----------------
if view == "Foco do Dia":
    view_foco(df, selected_agent)
elif view == "Time":
    view_time(df, selected_manager)
else:
    view_saude(df, health, outcome, selected_region)
