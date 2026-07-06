"""
Lead Scorer — Challenge 003 do AI Master Challenge (G4).

App Streamlit que permite a um vendedor ou Head de RevOps abrir, ver o
pipeline de oportunidades, e saber exatamente onde focar. Cada deal tem
um score 0-100 e a explicação em PT-BR do porquê daquele número.

Design System canônico:
    docs/G4-DESIGN-SYSTEM-PROMPT.md

Como rodar:
    (venv) streamlit run app.py
"""
from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from disc_profile import build_lead_profile
from followup_engine import generate_followup_package
from scoring import score_pipeline

# --- Design tokens G4 (fonte canônica: G4-DESIGN-SYSTEM-PROMPT.md) --------
G4_PRIMARY_HOVER = "#842E20"
G4_PRIMARY = "#AF4332"
G4_TEXT_MUTED = "#64748B"
G4_SURFACE = "#D1D5DB"       # color-7
G4_NAVY = "#001F35"          # color-1
G4_GOLD = "#B9915B"          # color-5
G4_GREEN = "#25D366"         # color-6
G4_BG = "#FFFFFF"            # color-10
G4_LIGHT_TEXT = "#EEEEEE"    # color-8
G4_CREAM = "#F5F4F3"         # color-9


# --- Paths relativos --------------------------------------------------------
BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
PIPELINE_CSV = DATA_DIR / "sales_pipeline.csv"
ACCOUNTS_CSV = DATA_DIR / "accounts.csv"
PRODUCTS_CSV = DATA_DIR / "products.csv"
SALES_TEAMS_CSV = DATA_DIR / "sales_teams.csv"

# "Hoje" — fixado para reprodutibilidade (determinismo, ver AC5)
TODAY = pd.Timestamp("2025-07-01")


# --- CSS custom para aplicar design tokens não-cobertos pelo config.toml ---
CSS = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=Manrope:wght@200;300;400;600;800&display=swap');

    :root {{
        --primary-hover: {G4_PRIMARY_HOVER};
        --primary-color: {G4_PRIMARY};
        --text-muted: {G4_TEXT_MUTED};
        --color-7: {G4_SURFACE};
        --color-1: {G4_NAVY};
        --color-5: {G4_GOLD};
        --color-6: {G4_GREEN};
        --color-10: {G4_BG};
        --color-8: {G4_LIGHT_TEXT};
        --color-9: {G4_CREAM};
        --radius-sm: 3px;
        --radius-md: 10px;
    }}

    html, body, [class*="css"] {{
        font-family: 'Manrope', 'Segoe UI', sans-serif;
        color: {G4_NAVY};
    }}

    h1, h2, h3, .stMarkdown h1, .stMarkdown h2 {{
        font-family: 'PPMuseum', 'Libre Baskerville', 'Georgia', serif;
        font-weight: 300;
        letter-spacing: -0.01em;
    }}

    /* Editorial subtitling */
    .subtitle-editorial {{
        font-family: 'Libre Baskerville', 'Georgia', serif;
        color: var(--text-muted);
        font-size: 16px;
        line-height: 24px;
    }}

    /* CTA / botões com estado completo */
    .stButton > button, .stDownloadButton > button {{
        border-radius: var(--radius-sm) !important;
        font-weight: 800;
        text-transform: none;
        background-color: var(--color-1);
        color: var(--color-10);
        border: 1px solid var(--color-1);
        padding: 0.5rem 1.2rem;
        transition: background 0.3s, border 0.3s, transform 0.4s;
    }}

    .stButton > button:hover, .stDownloadButton > button:hover {{
        background-color: var(--primary-hover);
        border-color: var(--primary-hover);
        transform: translateY(-1px);
    }}

    .stButton > button:focus-visible, .stDownloadButton > button:focus-visible {{
        outline: 2px solid var(--color-1);
        outline-offset: 2px;
    }}

    .stButton > button:disabled, .stDownloadButton > button:disabled {{
        background-color: var(--color-7);
        border-color: var(--color-7);
        color: var(--text-muted);
    }}

    /* Cards de KPI */
    .kpi-card {{
        background-color: {G4_CREAM};
        border-radius: var(--radius-md);
        padding: 36px;
        border: 1px solid var(--color-7);
        min-height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        gap: 10px;
    }}

    .kpi-label {{
        font-size: 12px;
        color: var(--text-muted);
        letter-spacing: 0;
        font-weight: 400;
        margin-bottom: 10px;
    }}

    .kpi-value {{
        font-size: clamp(30px, 2.1vw, 40px);
        line-height: 1.08;
        font-weight: 600;
        color: {G4_NAVY};
        font-family: 'Manrope', 'Segoe UI', sans-serif;
        letter-spacing: -0.01em;
        font-variant-numeric: tabular-nums;
        overflow-wrap: break-word;
        word-break: normal;
    }}

    .kpi-value-compact {{
        font-size: clamp(24px, 1.8vw, 32px);
    }}

    /* Badge de score: cores wash (10% opacity no fundo) */
    .score-badge {{
        display: inline-block;
        padding: 0.28rem 0.7rem;
        border-radius: var(--radius-sm);
        font-weight: 800;
        font-size: 0.85rem;
        font-family: 'Manrope', sans-serif;
    }}

    .score-high {{ background-color: {G4_GREEN}1A; color: {G4_GREEN}; }}
    .score-mid  {{ background-color: {G4_GOLD}1A; color: {G4_GOLD}; }}
    .score-low  {{ background-color: {G4_PRIMARY}1A; color: {G4_PRIMARY}; }}

    /* Breakdown do score */
    .breakdown-row {{
        display: flex;
        justify-content: space-between;
        padding: 0.3rem 0;
        border-bottom: 1px solid var(--color-7);
        font-size: 0.92rem;
    }}

    .breakdown-row:last-child {{ border-bottom: none; }}
    .breakdown-label {{ color: {G4_NAVY}; opacity: 0.85; }}

    .breakdown-sub {{
        font-weight: 800;
        color: {G4_NAVY};
        font-variant-numeric: tabular-nums;
    }}

    /* Sidebar filters: labels text-sm, campos radius-sm e spacing premium */
    section[data-testid="stSidebar"] label {{
        font-size: 12px !important;
        color: var(--text-muted) !important;
        font-family: 'Manrope', sans-serif !important;
        margin-bottom: 5px !important;
    }}

    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
    section[data-testid="stSidebar"] .stSlider {{
        border-radius: var(--radius-sm) !important;
    }}

    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {{
        margin-bottom: 16px;
    }}

    /* Wrapper container sem padding lateral excessivo */
    .block-container {{
        padding-top: 2rem;
        max-width: 1200px;
    }}

    /* Header */
    .app-header h1 {{
        font-size: 56px;
        line-height: 60px;
        margin: 0;
    }}

    /* Header */
    .app-header {{
        border-bottom: 1px solid var(--color-7);
        padding-bottom: 0.6rem;
        margin-bottom: 1.6rem;
    }}

    /* Zebra da tabela */
    [data-testid="stDataFrame"] tbody tr:nth-child(even) {{
        background-color: var(--color-9) !important;
    }}

    [data-testid="stDataFrame"] tbody tr:nth-child(odd) {{
        background-color: var(--color-10) !important;
    }}

    .followup-profile-card {{
        border: 1px solid var(--color-7);
        border-radius: var(--radius-md);
        background: var(--color-9);
        padding: 20px;
        margin-bottom: 16px;
    }}

    .followup-disc-chip {{
        display: inline-block;
        border-radius: var(--radius-sm);
        font-size: 12px;
        padding: 4px 10px;
        font-weight: 800;
        margin-right: 8px;
        background: {G4_NAVY}1A;
        color: {G4_NAVY};
    }}

    .followup-confidence-chip {{
        display: inline-block;
        border-radius: var(--radius-sm);
        font-size: 12px;
        padding: 4px 10px;
        font-weight: 700;
        background: {G4_GOLD}1A;
        color: {G4_GOLD};
    }}

    .next-action-card {{
        border: 1px solid {G4_PRIMARY};
        border-radius: var(--radius-md);
        background: {G4_PRIMARY}12;
        padding: 16px;
        margin-top: 8px;
    }}

    .hook-item {{
        border: 1px solid var(--color-7);
        border-radius: var(--radius-sm);
        background: var(--color-10);
        padding: 12px;
        margin-bottom: 10px;
    }}
</style>
"""


# --- Data loading (cached) --------------------------------------------------
@st.cache_data(ttl=600)
def load_scored_pipeline() -> pd.DataFrame:
    """Carrega CSVs, faz scoring e devolve DataFrame scored.

    Cacheado para evitar recomputar a cada interação de filtro.
    """
    pipeline = pd.read_csv(PIPELINE_CSV)
    accounts = pd.read_csv(ACCOUNTS_CSV)
    products = pd.read_csv(PRODUCTS_CSV)
    sales_teams = pd.read_csv(SALES_TEAMS_CSV)
    scored = score_pipeline(
        pipeline, accounts, products, sales_teams, today=TODAY, only_open=True
    )
    return scored


@st.cache_data(ttl=600)
def load_sales_teams() -> pd.DataFrame:
    return pd.read_csv(SALES_TEAMS_CSV)


# --- Helpers ----------------------------------------------------------------
def score_band(score: float) -> str:
    """Retorna classe CSS para o badge de score (cores wash)."""
    if score >= 80:
        return "score-high"
    if score >= 50:
        return "score-mid"
    return "score-low"


def score_label(score: float) -> str:
    if score >= 80:
        return "Quente"
    if score >= 50:
        return "Morno"
    return "Frio"


def fmt_brl(value: float) -> str:
    return f"R$ {value:,.0f}".replace(",", ".")


def render_kpi(label: str, value: str, compact: bool = False) -> None:
    value_class = "kpi-value kpi-value-compact" if compact else "kpi-value"
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="{value_class}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_breakdown(components: list[dict]) -> str:
    """Renderiza o breakdown de componentes como HTML."""
    rows = []
    for c in components:
        rows.append(
            f"""
            <div class="breakdown-row">
                <span class="breakdown-label">{c.get('label','')}</span>
                <span class="breakdown-sub">{c.get('subscore',0):.1f}
                  <small style="opacity:0.6">×{c.get('weight',0)*100:.0f}%</small>
                  = <strong>{c.get('contribution',0):.1f}</strong>
                </span>
            </div>
            """
        )
    return "".join(rows)


def render_copy_widget(copy_key: str, subject: str, body: str) -> None:
        """Renderiza bloco com botao copiar via JS e fallback selecionar texto."""
        full_text = f"Assunto: {subject}\n\n{body}"
        escaped = html.escape(full_text)
        escaped_id = html.escape(copy_key)
        html_block = f"""
        <div style="border:1px solid {G4_SURFACE};border-radius:3px;padding:10px;background:{G4_BG};">
            <div style="font-family:Manrope,sans-serif;font-size:12px;color:{G4_TEXT_MUTED};margin-bottom:8px;">Mensagem pronta</div>
            <textarea id="txt-{escaped_id}" style="width:100%;height:130px;border:1px solid {G4_SURFACE};border-radius:3px;padding:10px;font-family:Manrope,sans-serif;font-size:14px;">{escaped}</textarea>
            <div style="display:flex;gap:8px;margin-top:8px;align-items:center;">
                <button id="copy-{escaped_id}" style="border-radius:3px;border:1px solid {G4_NAVY};background:{G4_NAVY};color:{G4_BG};padding:6px 10px;font-weight:800;cursor:pointer;">Copiar</button>
                <button id="select-{escaped_id}" style="border-radius:3px;border:1px solid {G4_SURFACE};background:{G4_BG};color:{G4_NAVY};padding:6px 10px;cursor:pointer;">Selecionar texto</button>
                <span id="status-{escaped_id}" style="font-family:Manrope,sans-serif;font-size:12px;color:{G4_TEXT_MUTED};"></span>
            </div>
        </div>
        <script>
            const textArea = document.getElementById('txt-{escaped_id}');
            const copyBtn = document.getElementById('copy-{escaped_id}');
            const selectBtn = document.getElementById('select-{escaped_id}');
            const status = document.getElementById('status-{escaped_id}');

            function selectAll() {{
                textArea.focus();
                textArea.select();
            }}

            copyBtn.addEventListener('click', async () => {{
                try {{
                    await navigator.clipboard.writeText(textArea.value);
                    status.textContent = 'Copiado';
                }} catch (err) {{
                    selectAll();
                    status.textContent = 'Clipboard bloqueado: use Ctrl+C';
                }}
            }});

            selectBtn.addEventListener('click', () => {{
                selectAll();
                status.textContent = 'Texto selecionado';
            }});
        </script>
        """
        components.html(html_block, height=240)


def render_followup_assistant(filtered: pd.DataFrame) -> None:
        """Renderiza bloco DISC + Follow-up + ganchos com foco comercial."""
        st.markdown("---")
        st.markdown("### Assistente de Follow-up")
        st.caption("Selecione um lead para receber perfil DISC, 3 copys e ganchos de venda acionaveis.")

        if filtered.empty:
                st.info("Sem leads disponiveis no filtro atual para gerar follow-up.")
                return

        options = filtered[["opportunity_id", "sales_agent", "account", "score"]].copy()
        options["label"] = options.apply(
                lambda r: f"{r['opportunity_id']} | {r['sales_agent']} | {r['account']} | score {r['score']:.0f}",
                axis=1,
        )
        labels = options["label"].tolist()
        selected_label = st.selectbox("Lead para assistente", labels, index=0)
        selected_idx = options[options["label"] == selected_label].index[0]
        selected = filtered.loc[selected_idx]

        lead_profile = build_lead_profile(selected, today=TODAY)
        followup = generate_followup_package(lead_profile)
        lead_profile["next_best_action"] = followup["next_best_action"]

        st.markdown(
                f"""
                <div class="followup-profile-card">
                    <div style="margin-bottom:8px;"><strong>Perfil do Lead</strong></div>
                    <span class="followup-disc-chip">DISC: {lead_profile['disc_profile']}</span>
                    <span class="followup-confidence-chip">Confianca: {lead_profile['disc_confidence']}/100</span>
                    <div style="margin-top:12px;color:{G4_NAVY};">{lead_profile['disc_rationale']}</div>
                </div>
                """,
                unsafe_allow_html=True,
        )

        st.markdown("#### 3 opcoes de Follow-up")
        for idx, copy_item in enumerate(followup["copies"], start=1):
                tone = copy_item.get("tone", "consultivo")
                subject = copy_item.get("subject", "Sem assunto")
                text = copy_item.get("text", "")

                st.markdown(
                        f"""
                        <div style="border:1px solid {G4_SURFACE};border-radius:10px;padding:14px;margin-bottom:12px;background:{G4_CREAM};">
                            <div style="font-size:12px;color:{G4_TEXT_MUTED};margin-bottom:4px;">Tom {idx}: {tone}</div>
                            <div style="font-weight:700;color:{G4_NAVY};margin-bottom:8px;">Assunto: {subject}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                )
                render_copy_widget(f"{lead_profile['lead_id']}-{idx}", subject, text)

        st.markdown("#### Ganchos para avancar a venda")
        hooks = followup.get("sales_hooks", [])
        for hook in hooks:
                st.markdown(
                        f"""
                        <div class="hook-item">
                            <div><strong>Prioridade {hook.get('priority', '-')}:</strong> {hook.get('hook', '')}</div>
                            <div style="margin-top:4px;"><strong>Por que funciona:</strong> {hook.get('why_it_works', '')}</div>
                            <div style="margin-top:4px;"><strong>Pergunta de abertura:</strong> {hook.get('opening_question', '')}</div>
                            <div style="margin-top:4px;color:{G4_TEXT_MUTED};"><strong>Risco se mal usado:</strong> {hook.get('risk_if_badly_used', '')}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                )

        st.markdown("#### Proxima melhor acao")
        st.markdown(
                f"""
                <div class="next-action-card">{followup.get('next_best_action', 'Sem recomendacao no momento.')}</div>
                """,
                unsafe_allow_html=True,
        )


# --- Sidebar: filtros -------------------------------------------------------
def render_sidebar(scored: pd.DataFrame, teams: pd.DataFrame) -> dict[str, Any]:
    """Sidebar com filtros lendo valores REAIS dos CSVs."""
    st.sidebar.markdown("### Filtros")

    # Merge teams para filtros derived (manager, regional_office por sales_agent)
    agents_with_offices = teams[["sales_agent", "manager", "regional_office"]].drop_duplicates()

    # Filtro por Vendedor (valores reais do dataset)
    agent_options = ["Todos"] + sorted(scored["sales_agent"].dropna().unique().tolist())
    selected_agent = st.sidebar.selectbox("Vendedor", agent_options, index=0)

    # Filtro por Manager (valores reais)
    manager_options = ["Todos"] + sorted(teams["manager"].dropna().unique().tolist())
    selected_manager = st.sidebar.selectbox("Manager", manager_options, index=0)

    # Filtro por Escritório regional (valores reais)
    office_options = ["Todos"] + sorted(teams["regional_office"].dropna().unique().tolist())
    selected_office = st.sidebar.selectbox("Escritório regional", office_options, index=0)

    # Filtro por Stage (valores reais)
    stage_options = ["Todos"] + sorted(scored["deal_stage"].dropna().unique().tolist())
    selected_stage = st.sidebar.selectbox("Stage", stage_options, index=0)

    # Slider: score mínimo
    min_score = st.sidebar.slider("Score mínimo", 0, 100, 0, step=5)

    # Top-N deals para destacar
    top_n = st.sidebar.slider("Mostrar top N deals", 5, 50, 10, step=5)

    return {
        "agent": selected_agent,
        "manager": selected_manager,
        "office": selected_office,
        "stage": selected_stage,
        "min_score": min_score,
        "top_n": top_n,
    }


def apply_filters(
    scored: pd.DataFrame, teams: pd.DataFrame, f: dict[str, Any]
) -> pd.DataFrame:
    """Aplica filtros da sidebar no DataFrame scored."""
    # Join com teams para expor manager/regional_office
    df = scored.merge(
        teams[["sales_agent", "manager", "regional_office"]].drop_duplicates(),
        on="sales_agent",
        how="left",
    )

    if f["agent"] != "Todos":
        df = df[df["sales_agent"] == f["agent"]]
    if f["manager"] != "Todos":
        df = df[df["manager"] == f["manager"]]
    if f["office"] != "Todos":
        df = df[df["regional_office"] == f["office"]]
    if f["stage"] != "Todos":
        df = df[df["deal_stage"] == f["stage"]]
    if f["min_score"] > 0:
        df = df[df["score"] >= f["min_score"]]

    return df.sort_values("score", ascending=False).reset_index(drop=True)


# --- Charts -----------------------------------------------------------------
def render_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Histograma de distribuição de scores no pipeline filtrado."""
    fig = px.histogram(
        df, x="score", nbins=20,
        color_discrete_sequence=[G4_NAVY],
        labels={"score": "Score (0-100)"},
        title="Distribuição de scores no pipeline filtrado",
    )
    # Bandas verticais para as faixas (verde/amarelo/vermelho)
    fig.add_vrect(x0=0, x1=50, fillcolor=G4_PRIMARY, opacity=0.06, line_width=0)
    fig.add_vrect(x0=50, x1=80, fillcolor=G4_GOLD, opacity=0.06, line_width=0)
    fig.add_vrect(x0=80, x1=100, fillcolor=G4_GREEN, opacity=0.06, line_width=0)
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color=G4_NAVY,
        font_family="Manrope, sans-serif",
        height=320,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=True, gridcolor=G4_SURFACE, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=G4_SURFACE, zeroline=False)
    return fig


def render_scatter_chart(df: pd.DataFrame) -> go.Figure:
    """Scatter score x close_value."""
    plot_df = df.copy()
    plot_df["score_band_label"] = pd.cut(
        plot_df["score"],
        bins=[-0.001, 49.999, 79.999, 100.0],
        labels=["Frio", "Morno", "Quente"],
    )
    fig = px.scatter(
        plot_df, x="score", y="close_value",
        color="score_band_label",
        color_discrete_map={
            "Quente": G4_GREEN,
            "Morno": G4_GOLD,
            "Frio": G4_PRIMARY,
        },
        hover_data=["opportunity_id", "sales_agent", "account", "deal_stage"],
        labels={"score": "Score", "close_value": "Valor esperado (R$)"},
        title="Score × Valor esperado",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color=G4_NAVY,
        font_family="Manrope, sans-serif",
        height=320,
        margin=dict(l=20, r=20, t=50, b=20),
        legend_title_text="Faixa de score",
    )
    fig.update_xaxes(showgrid=True, gridcolor=G4_SURFACE, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=G4_SURFACE, zeroline=False)
    return fig


# --- Main -------------------------------------------------------------------
def main() -> None:
    """Entry point do app Streamlit Lead Scorer.

    Renderiza filtros, KPIs, top-N deals com breakdown explicável,
    tabela completa e charts (histograma + scatter).
    """
    st.set_page_config(
        page_title="Lead Scorer — G4",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CSS, unsafe_allow_html=True)

    # Header
    st.markdown(
        f"""
        <div class="app-header">
            <h1>Lead Scorer</h1>
            <p class="subtitle-editorial" style="margin:8px 0 0 0;">
                Onde focar nesta segunda-feira — pipeline priorizado com IA explicável
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load data
    try:
        scored = load_scored_pipeline()
        teams = load_sales_teams()
    except FileNotFoundError as e:
        st.error(
            f"Dataset não encontrado em {DATA_DIR}. "
            f"Coloque accounts.csv, products.csv, sales_teams.csv e sales_pipeline.csv "
            f"em solution/data/. Erro: {e}"
        )
        st.stop()

    # Sidebar
    filters = render_sidebar(scored, teams)
    filtered = apply_filters(scored, teams, filters)

    # --- KPIs no topo ---
    n_deals = len(filtered)
    mean_score = filtered["score"].mean() if n_deals else 0
    total_value = filtered["close_value"].sum() if n_deals else 0
    top_deal = filtered.iloc[0] if n_deals else None
    top_deal_label = (
        f"{top_deal['score']:.0f} · {top_deal['opportunity_id']}" if top_deal is not None else "—"
    )

    cols = st.columns(4)
    with cols[0]:
        render_kpi("Deals ativos", f"{n_deals}")
    with cols[1]:
        render_kpi("Score médio", f"{mean_score:.1f}")
    with cols[2]:
        render_kpi("Valor em jogo", fmt_brl(total_value), compact=True)
    with cols[3]:
        render_kpi("Top deal", top_deal_label, compact=True)

    st.markdown("")  # spacer

    # --- Top N deals prioritários ---
    st.markdown(f"### Top {filters['top_n']} deals para focar agora")
    top_df = filtered.head(filters["top_n"])

    if top_df.empty:
        st.info("Nenhum deal no filtro atual. Afrouxe os filtros na sidebar.")
        st.stop()

    # Renderizar cada deal como card
    for _, row in top_df.iterrows():
        score = row["score"]
        band = score_band(score)
        label = score_label(score)

        with st.container():
            col_main, col_score = st.columns([5, 1])
            with col_main:
                st.markdown(
                    f"""
                    **{row['opportunity_id']}** · {row['sales_agent']} ·
                    {row['product']} · {row['account']} ·
                    {row['deal_stage']} · {fmt_brl(row['close_value'])}
                    """,
                    unsafe_allow_html=True,
                )
            with col_score:
                st.markdown(
                    f"""
                    <div style="text-align:right">
                      <span class="score-badge {band}">{score:.0f} · {label}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Expansor com breakdown
            with st.expander("Por que este score?"):
                components = row["components_json"]
                st.markdown(
                    f"""
                    <div style="margin: 0.4rem 0;">
                      <em style="color:{G4_NAVY}; opacity:0.8;">{row['summary']}</em>
                    </div>
                    {render_breakdown(components)}
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("")  # spacer entre cards

    render_followup_assistant(filtered)

    # --- Tabela completa expandida ---
    st.markdown("---")
    st.markdown("### Pipeline completo (filtrado)")
    table_cols = [
        "opportunity_id", "sales_agent", "manager", "regional_office",
        "product", "account", "deal_stage", "close_value", "score", "summary",
    ]
    available_cols = [c for c in table_cols if c in filtered.columns]
    st.dataframe(
        filtered[available_cols],
        width="stretch",
        height=400,
        column_config={
            "score": st.column_config.ProgressColumn(
                "Score",
                help="Score 0-100 de priorização",
                format="%d",
                min_value=0,
                max_value=100,
            ),
            "close_value": st.column_config.NumberColumn(
                "Valor (R$)", format="R$ %d"
            ),
        },
    )

    # --- Charts ---
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(render_distribution_chart(filtered), width="stretch")
    with c2:
        st.plotly_chart(render_scatter_chart(filtered), width="stretch")

    # --- Footer com explicações ---
    st.markdown("---")
    with st.expander("ℹ️ Como o score é calculado"):
        st.markdown(
            f"""
            Cada deal recebe um score 0-100 que combina **6 componentes explicáveis**:

            | Componente | Peso | Por quê |
            |-----------|------|---------|
            | **Stage** | 25% | Engaging > Prospecting — já passou por descoberta |
            | **Velocidade** | 20% | Janela ótima 15-60 dias no pipeline |
            | **Tamanho da conta** | 20% | Contas maiores = deals estratégicos |
            | **Valor do produto** | 15% | Ticket alto = payoff maior |
            | **Histórico do vendedor** | 15% | Quem vende importa (win rate 42%–67%) |
            | **Valor do deal** | 5% | Peso baixo de propósito (não é só ordenar por valor) |

            Score **≥ 80** = Quente · **50-80** = Morno · **< 50** = Frio

            Esta é a versão heurística (sem ML black-box) — ver
            `process-log/PROMPT_03_spec_scoring.md` para a SPEC completa.
            """
        )


if __name__ == "__main__":
    main()
