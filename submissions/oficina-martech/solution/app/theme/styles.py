"""CSS global do tema Foco + injeção. O CSS é derivado dos tokens de cor."""
from app.theme.tokens import COLORS

CSS = f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  :root {{
    --ink: {COLORS['ink']}; --ink-soft: {COLORS['ink_soft']};
    --slate: {COLORS['slate']}; --slate-2: {COLORS['slate_2']};
    --surface: {COLORS['surface']}; --canvas: {COLORS['canvas']};
    --canvas-2: {COLORS['canvas_2']}; --border: {COLORS['border']};
    --brand: {COLORS['brand']}; --brand-700: {COLORS['brand_700']};
    --brand-soft: {COLORS['brand_soft']};
  }}

  html, body, [data-testid="stAppViewContainer"], .stApp {{
    background: {COLORS['canvas']} !important;
    color: {COLORS['ink']};
    font-family: "Inter", system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .block-container {{
    padding: 1.8rem 1.15rem 4rem;
    max-width: none;
    width: 100%;
  }}

  * {{
    scrollbar-color: {COLORS['slate_2']} {COLORS['canvas_2']};
  }}

  /* ---------- Topo — header usa Emotion inline-style; forçar nossa cor canvas ---------- */
  /* stDecoration foi removido no Streamlit 1.28+; o header (class stAppHeader) usa  */
  /* background=t.colors.bgColor via Emotion quando sidebar está presente.            */
  header.stAppHeader,
  header[data-testid="stHeader"] {{
    background-color: {COLORS['canvas']} !important;
    background: {COLORS['canvas']} !important;
    box-shadow: none !important;
    border-bottom: 1px solid {COLORS['border']};
  }}
  [data-testid="stToolbar"],
  [data-testid="stSidebarCollapseButton"] {{
    background: transparent !important;
    background-color: transparent !important;
    color: {COLORS['ink']} !important;
  }}
  [data-testid="stToolbar"] svg,
  [data-testid="stHeader"] svg,
  [data-testid="stSidebarCollapseButton"] svg {{ color: {COLORS['slate']}; }}

  h1, h2, h3,
  [data-testid="stMarkdownContainer"] h1,
  [data-testid="stMarkdownContainer"] h2,
  [data-testid="stMarkdownContainer"] h3 {{
    color: {COLORS['ink']};
    font-family: "Inter", system-ui, sans-serif;
    font-weight: 700; letter-spacing: -0.01em;
  }}
  [data-testid="stMarkdownContainer"] p,
  [data-testid="stMarkdownContainer"] li,
  [data-testid="stMarkdownContainer"] span {{ font-family: "Inter", system-ui, sans-serif; }}

  /* ---------- Sidebar (clara) ---------- */
  section[data-testid="stSidebar"] {{
    width: 248px !important; min-width: 248px !important;
    background: {COLORS['surface']};
    border-right: 1px solid {COLORS['border']};
  }}
  section[data-testid="stSidebar"] > div {{ padding: 26px 16px; }}
  section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
  section[data-testid="stSidebar"] label {{
    color: {COLORS['ink']}; font-size: 13px; font-weight: 500;
  }}
  section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
    min-height: 44px; background: {COLORS['surface']};
    border: 1px solid {COLORS['border']}; border-radius: 10px; box-shadow: none;
  }}
  section[data-testid="stSidebar"] div[data-baseweb="select"] > div:hover {{
    border-color: {COLORS['slate_2']};
  }}
  section[data-testid="stSidebar"] div[data-baseweb="select"] > div:focus-within {{
    border-color: {COLORS['brand']};
    box-shadow: 0 0 0 3px {COLORS['brand_soft']};
  }}
  section[data-testid="stSidebar"] div[data-baseweb="select"] > div * {{
    color: {COLORS['ink']} !important; font-family: "Inter", sans-serif;
  }}
  section[data-testid="stSidebar"] hr {{ margin: 18px 0; border-color: {COLORS['border']}; }}

  .sidebar-brand {{ display: flex; align-items: center; gap: 11px; margin: 0 0 26px; }}
  .sidebar-brand-icon {{
    display: grid; place-items: center; width: 38px; height: 38px;
    border-radius: 11px; background: {COLORS['brand_soft']};
    font-size: 19px; line-height: 1;
  }}
  .sidebar-brand strong {{
    display: block; color: {COLORS['ink']};
    font-size: 19px; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1;
  }}
  .sidebar-brand small {{
    display: block; color: {COLORS['slate']}; font-size: 12px; margin-top: 2px;
  }}
  .sidebar-label {{
    color: {COLORS['slate_2']}; font-size: 11px; font-weight: 700;
    letter-spacing: .1em; margin: 0 0 7px; text-transform: uppercase;
  }}
  .sidebar-summary {{
    border: 1px solid {COLORS['border']}; border-radius: 14px;
    background: {COLORS['canvas']}; padding: 15px 16px; margin-top: 16px;
  }}
  .sidebar-summary span {{
    display: block; color: {COLORS['slate']}; font-size: 11px; font-weight: 700;
    letter-spacing: .08em; margin-bottom: 8px; text-transform: uppercase;
  }}
  .sidebar-summary strong {{
    display: block; color: {COLORS['ink']}; font-size: 26px; font-weight: 800;
    line-height: 1.1; font-variant-numeric: tabular-nums;
  }}
  .sidebar-summary small {{ display: block; color: {COLORS['slate']}; font-size: 12px; margin-top: 5px; }}

  /* ---------- Métricas / KPIs ---------- */
  [data-testid="stMetric"] {{
    background: {COLORS['surface']}; border: 1px solid {COLORS['border']};
    border-radius: 14px; padding: 10px 12px;
    min-height: 84px;
  }}
  [data-testid="stMetricLabel"] {{
    color: {COLORS['slate']} !important; font-size: 10.5px; font-weight: 600;
    letter-spacing: .01em;
  }}
  [data-testid="stMetricLabel"] > div {{
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  [data-testid="stMetricValue"] {{
    color: {COLORS['ink']} !important; font-size: 23px; font-weight: 800;
    font-variant-numeric: tabular-nums;
    line-height: 1.08;
    overflow: visible;
  }}
  [data-testid="stMetricDelta"] {{
    font-size: 11px !important;
  }}

  /* ---------- Botões ---------- */
  .stButton > button, .stDownloadButton > button {{
    border-radius: 10px; border: 1px solid {COLORS['border']};
    background: {COLORS['surface']}; color: {COLORS['ink']};
    font-family: "Inter", sans-serif; font-size: 13px; font-weight: 600;
    padding: 7px 14px; transition: all .12s ease;
    white-space: nowrap !important; overflow: hidden; text-overflow: ellipsis;
  }}
  .stButton > button:hover, .stDownloadButton > button:hover {{
    border-color: {COLORS['slate_2']}; background: {COLORS['canvas']};
    color: {COLORS['ink']};
  }}
  /* CTA primário (kind="primary"): Contatado hoje */
  .stButton > button[kind="primary"] {{
    border-color: {COLORS['brand']}; background: {COLORS['brand']}; color: #fff;
  }}
  .stButton > button[kind="primary"]:hover {{
    border-color: {COLORS['brand_700']}; background: {COLORS['brand_700']}; color: #fff;
  }}

  /* ---------- Alertas / banners ---------- */
  [data-testid="stAlert"] {{
    border-radius: 12px; border: 1px solid {COLORS['border']};
    background: {COLORS['surface']}; color: {COLORS['ink']};
  }}
  [data-testid="stAlert"] * {{
    color: {COLORS['ink']} !important;
  }}
  [data-testid="stAlert"][kind="warning"],
  [data-testid="stAlert"]:has(svg[data-testid="stAlertIcon-warning"]) {{
    background: {COLORS['warning_soft']} !important;
    border-color: #E5C98E !important;
  }}
  [data-testid="stAlert"][kind="warning"] *,
  [data-testid="stAlert"]:has(svg[data-testid="stAlertIcon-warning"]) * {{
    color: #6D4612 !important;
  }}

  /* ---------- Expander (o "porquê") ---------- */
  [data-testid="stExpander"] {{
    border: 1px solid {COLORS['border']}; border-radius: 12px;
    background: {COLORS['surface']}; overflow: hidden;
  }}
  [data-testid="stExpander"] details,
  [data-testid="stExpander"] summary,
  [data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    background: {COLORS['surface']} !important;
    color: {COLORS['ink']} !important;
  }}
  [data-testid="stExpander"] summary {{ font-size: 13px; font-weight: 600; color: {COLORS['brand']} !important; }}
  [data-testid="stExpander"] summary:hover {{ color: {COLORS['brand_700']}; }}

  /* Streamlit code blocks are too dark for this product. Keep any accidental code readable. */
  pre, code, [data-testid="stCodeBlock"], [data-testid="stCodeBlock"] * {{
    background: {COLORS['canvas_2']} !important;
    color: {COLORS['ink']} !important;
    border-color: {COLORS['border']} !important;
  }}

  /* Segmented control / tabs: no dark selected state. */
  [data-testid="stSegmentedControl"] button,
  [role="tablist"] button,
  [data-testid="stButtonGroup"] button,
  [data-testid^="stBaseButton-segmented_control"] {{
    background: {COLORS['surface']} !important;
    color: {COLORS['ink']} !important;
    border-color: {COLORS['border']} !important;
  }}
  [data-testid="stSegmentedControl"] button[aria-pressed="true"],
  [role="tablist"] button[aria-selected="true"],
  [data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"],
  [data-testid="stBaseButton-segmented_controlActive"] {{
    background: {COLORS['brand_soft']} !important;
    color: {COLORS['brand_700']} !important;
    border-color: {COLORS['brand']} !important;
  }}
  [data-testid="stButtonGroup"] button:hover,
  [data-testid^="stBaseButton-segmented_control"]:hover {{
    background: {COLORS['canvas_2']} !important;
    color: {COLORS['brand_700']} !important;
    border-color: {COLORS['brand']} !important;
  }}

  /* ---------- Brief do dia ---------- */
  .brief-panel {{
    border: 1px solid {COLORS['border']};
    border-radius: 16px;
    background: {COLORS['surface']};
    margin: 4px 0 10px;
    overflow: hidden;
  }}
  .brief-panel.is-compact {{
    border: 0;
    border-radius: 0;
    margin: 0;
    background: transparent;
  }}
  .brief-panel.is-compact .brief-list {{
    padding: 2px 0 0;
  }}
  .brief-head {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 16px 18px;
    background: linear-gradient(180deg, {COLORS['brand_soft']} 0%, {COLORS['surface']} 100%);
    border-bottom: 1px solid {COLORS['border']};
  }}
  .brief-icon {{
    display: grid;
    place-items: center;
    width: 36px;
    height: 36px;
    border-radius: 12px;
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
  }}
  .brief-title {{
    color: {COLORS['ink']};
    font-size: 16px;
    font-weight: 800;
    line-height: 1.2;
  }}
  .brief-sub {{
    color: {COLORS['slate']};
    font-size: 13px;
    margin-top: 3px;
  }}
  .brief-list {{
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 14px;
  }}
  .brief-item {{
    display: grid;
    grid-template-columns: 42px minmax(0, 1fr) auto;
    gap: 13px;
    align-items: center;
    border: 1px solid {COLORS['border_soft']};
    border-radius: 13px;
    background: {COLORS['canvas']};
    padding: 12px 14px;
  }}
  .brief-rank {{
    display: grid;
    place-items: center;
    width: 36px;
    height: 36px;
    border-radius: 12px;
    background: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['brand_700']};
    font-size: 13px;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
  }}
  .brief-main {{
    min-width: 0;
  }}
  .brief-deal {{
    color: {COLORS['ink']};
    font-size: 14px;
    font-weight: 800;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  .brief-action {{
    color: {COLORS['brand_700']};
    font-size: 12.5px;
    font-weight: 700;
    margin-top: 8px;
  }}
  .brief-motivo {{
    color: {COLORS['ink_soft']};
    font-size: 13px;
    line-height: 1.45;
    margin-top: 5px;
  }}
  .brief-aside {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
  }}
  .brief-tier {{
    display: inline-grid;
    place-items: center;
    width: 28px;
    height: 28px;
    border-radius: 9px;
    font-size: 14px;
    line-height: 1;
  }}
  .brief-greeting {{
    color: {COLORS['ink']};
    font-size: 13.5px;
    font-weight: 600;
    line-height: 1.4;
    padding: 12px 14px 2px;
  }}
  .brief-score {{
    display: inline-flex;
    flex-direction: column;
    align-items: flex-end;
    min-width: 58px;
    color: {COLORS['focus']};
    font-size: 26px;
    font-weight: 800;
    line-height: 1;
    font-variant-numeric: tabular-nums;
  }}
  .brief-score small {{
    display: block;
    color: {COLORS['slate']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .07em;
    margin-top: 4px;
    text-transform: uppercase;
  }}
  .brief-empty {{
    padding: 18px;
    color: {COLORS['slate']};
    font-size: 13px;
  }}
  .hygiene-alert {{
    display: flex;
    gap: 10px;
    align-items: flex-start;
    margin: 18px 0;
    border: 1px solid #E5C98E;
    border-radius: 12px;
    background: {COLORS['warning_soft']};
    color: #5C3B10;
    padding: 14px 16px;
    font-size: 14px;
    line-height: 1.5;
  }}
  .hygiene-alert strong {{
    color: #6D4612;
    font-weight: 800;
  }}
  .hygiene-alert span {{
    flex: 1;
  }}

  /* ---------- Funil (scoreboard) ---------- */
  .funnel {{ display:flex; flex-direction:column; gap:11px; margin:18px 0 6px; }}
  .funnel-row {{
    display:grid; grid-template-columns: 118px 1fr 132px;
    align-items:center; gap:14px;
  }}
  .funnel-label {{ font-size:13px; font-weight:700; color:{COLORS['ink']}; }}
  .funnel-bar-bg {{
    height:30px; background:{COLORS['canvas_2']}; border-radius:8px; overflow:hidden;
    border:1px solid {COLORS['border_soft']};
  }}
  .funnel-bar {{ height:100%; border-radius:7px; transition:width .4s ease; }}
  .funnel-val {{
    font-size:13px; font-weight:800; color:{COLORS['ink']};
    font-variant-numeric:tabular-nums; text-align:right;
  }}

  /* ---------- Deal card ---------- */
  /* margin-bottom negativo fecha o gap entre o card HTML e os botões nativos abaixo */
  [data-testid="stElementContainer"]:has(.foco-card) {{ margin-bottom: -0.5rem !important; }}

  .foco-card {{
    border: 1px solid {COLORS['border']}; border-radius: 14px;
    padding: 16px 18px; background: {COLORS['surface']};
    display: flex; align-items: center; gap: 18px;
    transition: box-shadow .14s ease, border-color .14s ease;
  }}
  .foco-card:hover {{
    border-color: {COLORS['brand']};
    box-shadow: 0 4px 16px -6px rgba(79,70,229,.18);
  }}
  .foco-card.is-done {{ opacity: .62; }}
  .foco-scorewrap {{ min-width: 72px; text-align: center; }}
  .foco-score {{
    font-size: 38px; font-weight: 800; font-variant-numeric: tabular-nums; line-height: 1;
  }}
  .foco-bar {{
    height: 4px; border-radius: 999px; background: {COLORS['canvas_2']};
    margin-top: 8px; overflow: hidden;
  }}
  .foco-bar > i {{ display: block; height: 100%; border-radius: 999px; }}
  .foco-body {{ flex: 1; min-width: 0; }}
  .foco-title {{
    font-size: 16px; font-weight: 700; color: {COLORS['ink']}; letter-spacing: -0.01em;
  }}
  .foco-reason {{ font-size: 13px; color: {COLORS['slate']}; margin-top: 3px; }}
  .foco-reason b {{ color: {COLORS['ink-soft'] if False else COLORS['ink_soft']}; font-weight: 600; }}
  .foco-action {{
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 12.5px; color: {COLORS['brand']}; font-weight: 600; margin-top: 7px;
  }}
  .foco-done-tag {{
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 12.5px; color: {COLORS['positive']}; font-weight: 600; margin-top: 7px;
  }}

  /* ---------- Chips / pills ---------- */
  .tier-pill {{
    display: inline-flex; align-items: center; gap: 5px; white-space: nowrap;
    padding: 5px 11px; border-radius: 999px;
    font-size: 12px; font-weight: 700; letter-spacing: .005em;
  }}

  /* ---------- Cabeçalho de seção ---------- */
  .sectionhdr {{
    display: flex; align-items: center; gap: 9px;
    font-size: 13px; font-weight: 700; letter-spacing: .005em;
    color: {COLORS['ink']}; margin: 26px 0 12px;
  }}
  .sectionhdr .count {{
    color: {COLORS['slate']}; font-weight: 600;
    background: {COLORS['canvas_2']}; border-radius: 999px; padding: 2px 9px; font-size: 12px;
  }}
  .table-title {{
    color: {COLORS['ink']};
    font-size: 16px;
    font-weight: 800;
    margin: 8px 0 8px;
  }}
  [data-testid="stDataFrame"] {{
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    overflow: hidden;
    background: {COLORS['surface']};
  }}
  [data-testid="stDataFrame"] * {{
    font-size: 12px !important;
  }}

  /* ---------- Hero (saudação) ---------- */
  .foco-hero {{ margin-bottom: 4px; }}
  .foco-hero h2 {{ font-size: 26px; font-weight: 800; letter-spacing: -0.02em; margin: 0; }}
  .foco-hero p {{ color: {COLORS['slate']}; font-size: 15px; margin: 4px 0 0; }}
  .foco-hero p b {{ color: {COLORS['focus']}; font-weight: 700; }}

  /* ---------- Breakdown (factor rows no expander) ---------- */
  .bd-wrap {{ display: flex; flex-direction: column; gap: 8px; }}
  .bd-row {{
    display: grid; grid-template-columns: 22px 1fr auto auto;
    align-items: center; gap: 12px;
    padding: 10px 12px; border-radius: 10px; background: {COLORS['canvas']};
    border: 1px solid {COLORS['border_soft']};
  }}
  .bd-ico {{ font-size: 13px; line-height: 1; }}
  .bd-main {{ min-width: 0; }}
  .bd-feature {{ font-size: 13px; font-weight: 600; color: {COLORS['ink']}; }}
  .bd-value {{ font-size: 12.5px; color: {COLORS['slate']}; margin-top: 1px; }}
  .bd-weight {{ font-size: 11px; color: {COLORS['slate_2']}; font-variant-numeric: tabular-nums; }}
  .bd-points {{
    font-size: 15px; font-weight: 800; font-variant-numeric: tabular-nums;
    min-width: 42px; text-align: right;
  }}
  .bd-foot {{
    margin-top: 10px; padding: 12px 14px; border-radius: 10px;
    background: {COLORS['brand_soft']}; border: 1px solid {COLORS['border']};
    font-size: 13px; color: {COLORS['ink']};
  }}
  .bd-foot b {{ color: {COLORS['brand_700']}; }}

  /* ---------- Kanban ---------- */
  .kanban-head {{
    display: flex; align-items: center; gap: 8px;
    padding: 10px 13px; border-radius: 12px; margin-bottom: 10px;
    font-size: 13px; font-weight: 700;
  }}
  .kanban-head .count {{
    margin-left: auto; font-weight: 700; font-variant-numeric: tabular-nums;
    background: rgba(255,255,255,.6); border-radius: 999px; padding: 1px 9px; font-size: 12px;
  }}
  .kanban-body {{
    border: 1px solid {COLORS['border']}; border-radius: 0 0 12px 12px;
    background: {COLORS['canvas_2']}; padding: 12px; min-height: 80px;
  }}
  .kanban-empty {{
    text-align: center; color: {COLORS['slate_2']}; font-size: 12.5px;
    padding: 18px 8px;
  }}

  /* ---------- Card compacto (kanban) ---------- */
  .foco-card.compact {{
    flex-direction: column; align-items: stretch; gap: 0;
    padding: 13px 14px; margin-bottom: 0;
  }}
  .foco-card.compact .kc-top {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
  .foco-card.compact .foco-score {{ font-size: 28px; }}
  .foco-card.compact .foco-bar {{ margin: 8px 0 0; }}
  .foco-card.compact .kc-title {{
    font-size: 14px; font-weight: 700; color: {COLORS['ink']};
    letter-spacing: -0.01em; margin-top: 11px;
  }}
  .foco-card.compact .foco-reason {{ font-size: 12px; margin-top: 3px; }}
  .foco-card.compact .foco-action,
  .foco-card.compact .foco-done-tag {{ font-size: 12px; margin-top: 8px; }}

  /* ---------- Rep card (Visão Time) ---------- */
  .rep-card {{
    border: 1px solid {COLORS['border']}; border-radius: 14px;
    padding: 14px 18px; background: {COLORS['surface']}; margin-bottom: 10px;
    display: flex; align-items: center; gap: 18px;
    transition: box-shadow .14s ease, border-color .14s ease;
  }}
  .rep-card:hover {{
    border-color: {COLORS['brand']};
    box-shadow: 0 4px 16px -6px rgba(79,70,229,.18);
  }}
  .rep-foco {{ min-width: 66px; text-align: center; }}
  .rep-foco .n {{
    font-size: 30px; font-weight: 800; line-height: 1; font-variant-numeric: tabular-nums;
  }}
  .rep-foco .l {{
    font-size: 10.5px; color: {COLORS['slate_2']}; text-transform: uppercase;
    letter-spacing: .07em; margin-top: 4px;
  }}
  .rep-body {{ flex: 1; min-width: 0; }}
  .rep-name {{ font-size: 16px; font-weight: 700; color: {COLORS['ink']}; letter-spacing: -0.01em; }}
  .rep-sub {{ font-size: 12.5px; color: {COLORS['slate']}; margin-top: 3px; }}
  .rep-metrics {{ display: flex; gap: 26px; }}
  .rep-metric {{ text-align: right; }}
  .rep-metric .v {{
    font-size: 18px; font-weight: 800; color: {COLORS['ink']}; font-variant-numeric: tabular-nums;
  }}
  .rep-metric .v.risk {{ color: {COLORS['danger']}; }}
  .rep-metric .k {{
    font-size: 10.5px; color: {COLORS['slate_2']}; text-transform: uppercase;
    letter-spacing: .06em; margin-top: 3px;
  }}
</style>
"""


def inject_css(st) -> None:
    """Injeta o CSS global do tema na app Streamlit."""
    st.markdown(CSS, unsafe_allow_html=True)
