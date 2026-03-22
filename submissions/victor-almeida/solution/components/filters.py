"""
Filtros do Lead Scorer — logica pura + renderizacao Streamlit.

Funcoes puras (testaveis sem Streamlit):
- _get_manager_options: cascade de managers por escritorio
- _get_agent_options: cascade de agentes por escritorio/manager
- apply_filters: aplica filtros combinados com logica AND

Funcoes de UI (dependem de Streamlit):
- render_filters: renderiza widgets na sidebar
- render_filter_summary: exibe resumo dos filtros aplicados
"""

from dataclasses import dataclass

import pandas as pd

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

OPTION_ALL = "Todos"
SCORE_MIN = 0
SCORE_MAX = 100
SCORE_STEP = 5
ZOMBIE_OPTIONS = ["Todos os deals", "Apenas zumbis", "Ocultar zumbis"]


# ---------------------------------------------------------------------------
# Dataclass de estado
# ---------------------------------------------------------------------------


@dataclass
class FilterState:
    """Estado dos filtros aplicados pelo usuario."""

    office: str
    manager: str
    agent: str
    products: list[str]
    sectors: list[str]
    score_min: int
    score_max: int
    zombie_mode: str


# ---------------------------------------------------------------------------
# Funcoes puras — cascade de opcoes
# ---------------------------------------------------------------------------


def _get_manager_options(
    df_teams: pd.DataFrame, selected_office: str
) -> list[str]:
    """Retorna managers disponiveis para o escritorio selecionado.

    Args:
        df_teams: DataFrame de sales_teams com colunas manager e regional_office.
        selected_office: Escritorio selecionado ou OPTION_ALL para todos.

    Returns:
        Lista com OPTION_ALL como primeiro item, seguido de managers ordenados.
    """
    if selected_office == OPTION_ALL:
        managers = sorted(df_teams["manager"].unique().tolist())
    else:
        managers = sorted(
            df_teams[df_teams["regional_office"] == selected_office]["manager"]
            .unique()
            .tolist()
        )
    return [OPTION_ALL] + managers


def _get_agent_options(
    df_teams: pd.DataFrame, selected_office: str, selected_manager: str
) -> list[str]:
    """Retorna vendedores disponiveis para o escritorio e manager selecionados.

    Args:
        df_teams: DataFrame de sales_teams.
        selected_office: Escritorio selecionado ou OPTION_ALL.
        selected_manager: Manager selecionado ou OPTION_ALL.

    Returns:
        Lista com OPTION_ALL como primeiro item, seguido de agentes ordenados.
    """
    mask = pd.Series(True, index=df_teams.index)
    if selected_office != OPTION_ALL:
        mask &= df_teams["regional_office"] == selected_office
    if selected_manager != OPTION_ALL:
        mask &= df_teams["manager"] == selected_manager
    agents = sorted(df_teams[mask]["sales_agent"].unique().tolist())
    return [OPTION_ALL] + agents


# ---------------------------------------------------------------------------
# Funcao pura — aplicacao de filtros
# ---------------------------------------------------------------------------


def apply_filters(df: pd.DataFrame, filters: FilterState) -> pd.DataFrame:
    """Aplica todos os filtros com logica AND. Retorna DataFrame filtrado.

    Args:
        df: DataFrame do pipeline enriquecido.
        filters: Estado dos filtros (FilterState).

    Returns:
        DataFrame filtrado.
    """
    mask = pd.Series(True, index=df.index)

    # Hierarquia organizacional
    if filters.office != OPTION_ALL:
        mask &= df["regional_office"] == filters.office
    if filters.manager != OPTION_ALL:
        mask &= df["manager"] == filters.manager
    if filters.agent != OPTION_ALL:
        mask &= df["sales_agent"] == filters.agent

    # Produtos (multiselect — vazio = todos)
    all_products = df["product"].unique().tolist()
    if filters.products and len(filters.products) < len(all_products):
        mask &= df["product"].isin(filters.products)

    # Setores (multiselect — vazio = todos)
    all_sectors = df["sector"].dropna().unique().tolist()
    if filters.sectors and len(filters.sectors) < len(all_sectors):
        mask &= df["sector"].isin(filters.sectors)

    # Range de score
    mask &= df["score"].between(filters.score_min, filters.score_max)

    # Modo zumbi
    if filters.zombie_mode == "Apenas zumbis":
        mask &= df["is_zombie"] == True  # noqa: E712
    elif filters.zombie_mode == "Ocultar zumbis":
        mask &= df["is_zombie"] == False  # noqa: E712

    return df[mask]


# ---------------------------------------------------------------------------
# Funcoes de UI (Streamlit) — nao testadas em unit tests
# ---------------------------------------------------------------------------


def render_filters(df_teams, df_products, df_accounts):
    """Renderiza filtros na sidebar do Streamlit. Retorna FilterState.

    Args:
        df_teams: DataFrame de sales_teams.
        df_products: DataFrame de products.
        df_accounts: DataFrame de accounts.

    Returns:
        FilterState com os valores selecionados pelo usuario.
    """
    import streamlit as st

    st.sidebar.header("Filtros")

    # Counter para forcar reset dos widgets (muda as keys)
    rc = st.session_state.get("_filter_reset", 0)

    # --- Escritorio ---
    offices = [OPTION_ALL] + sorted(df_teams["regional_office"].unique().tolist())
    office = st.sidebar.selectbox("Escritorio", offices, key=f"f_office_{rc}")

    # --- Manager (cascade) ---
    manager_options = _get_manager_options(df_teams, office)
    manager = st.sidebar.selectbox("Manager", manager_options, key=f"f_manager_{rc}")

    # --- Vendedor (cascade) ---
    agent_options = _get_agent_options(df_teams, office, manager)
    agent = st.sidebar.selectbox("Vendedor", agent_options, key=f"f_agent_{rc}")

    # --- Produtos ---
    all_products = sorted(df_products["product"].unique().tolist())
    products = st.sidebar.multiselect("Produtos", all_products, key=f"f_products_{rc}")

    # --- Setores ---
    all_sectors = sorted(df_accounts["sector"].dropna().unique().tolist())
    sectors = st.sidebar.multiselect("Setores", all_sectors, key=f"f_sectors_{rc}")

    # --- Score ---
    score_range = st.sidebar.slider(
        "Score",
        min_value=SCORE_MIN,
        max_value=SCORE_MAX,
        value=(SCORE_MIN, SCORE_MAX),
        step=SCORE_STEP,
        key=f"f_score_{rc}",
    )

    # --- Zumbi ---
    zombie_mode = st.sidebar.radio("Deals zumbi", ZOMBIE_OPTIONS, key=f"f_zombie_{rc}")

    return FilterState(
        office=office,
        manager=manager,
        agent=agent,
        products=products,
        sectors=sectors,
        score_min=score_range[0],
        score_max=score_range[1],
        zombie_mode=zombie_mode,
    )


def render_filter_summary(df_filtered: pd.DataFrame, df_total: pd.DataFrame):
    """Renderiza resumo dos filtros aplicados na sidebar.

    Args:
        df_filtered: DataFrame apos aplicacao dos filtros.
        df_total: DataFrame original (sem filtros).
    """
    import streamlit as st

    total = len(df_total)
    filtered = len(df_filtered)
    pct = (filtered / total * 100) if total > 0 else 0

    st.sidebar.markdown("---")
    st.sidebar.metric(
        "Deals exibidos",
        f"{filtered:,}",
        delta=f"{pct:.0f}% do total",
        delta_color="off",
    )

    rc = st.session_state.get("_filter_reset", 0)
    if st.sidebar.button("Limpar filtros", use_container_width=True):
        st.session_state["_filter_reset"] = rc + 1
        st.session_state.pop("deal_selecionado", None)
        st.session_state.pop("pipeline_page", None)
        st.rerun()
