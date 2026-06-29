from __future__ import annotations

import html
from pathlib import Path
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
SOLUTION_DIR = APP_DIR.parent
EXPORTS_DIR = SOLUTION_DIR / "exports"

REQUIRED_EXPORTS = {
    "account_health": "account_health.csv",
    "risk_segments": "risk_segments.csv",
    "priority_accounts": "priority_accounts.csv",
    "action_backlog": "action_backlog.csv",
    "executive_findings": "executive_findings.csv",
}

OPTIONAL_EXPORTS = {
    "usage_growth_tests": "usage_growth_tests.csv",
    "root_cause_candidates": "root_cause_candidates.csv",
    "churner_comparison": "churner_comparison.csv",
}

EXPORT_LABELS = {
    "account_health": "Saúde das contas",
    "risk_segments": "Segmentos de risco",
    "priority_accounts": "Contas prioritárias",
    "action_backlog": "Backlog de ações",
    "executive_findings": "Resumo executivo",
    "usage_growth_tests": "Testes de crescimento de uso",
    "root_cause_candidates": "Candidatos de causa raiz",
    "churner_comparison": "Comparação de churners",
}

RISK_ORDER = ["Critical", "High", "Medium", "Low"]
RISK_COLORS = {
    "Critical": "#842E20",
    "High": "#B9915B",
    "Medium": "#706F6F",
    "Low": "#001F35",
}
G4_INK = "#031A26"
G4_GOLD = "#B9915B"
G4_RUST = "#842E20"
G4_BORDER = "#D6D5D5"
G4_MUTED = "#706F6F"

PT_LABELS = {
    "Critical": "Crítico",
    "High": "Alto",
    "Medium": "Médio",
    "Low": "Baixo",
    "All": "Todos",
    "Churn history": "Histórico de churn",
    "Revenue exposure": "Exposição de receita",
    "Support friction": "Fricção de suporte",
    "Subscription/commercial": "Risco comercial",
    "Product usage quality": "Qualidade de uso do produto",
    "Segment save playbook": "Playbook de retenção",
    "Pricing churn review": "Revisão de preço",
    "Usage validity contract": "Contrato de uso válido",
    "Churn label governance": "Governança do label de churn",
    "Value-realization erosion before renewal": "Erosão de valor antes da renovação",
    "Support friction masks satisfaction average": "Fricção de suporte mascarada pela média de satisfação",
    "Commercial renewal and downgrade risk": "Risco comercial de renovação e downgrade",
    "Pricing and budget pressure": "Pressão de preço e orçamento",
    "Product value / feature fit erosion": "Erosão de valor do produto e aderência de features",
    "Data quality and label ambiguity": "Ambiguidade de dados e labels",
    "Top root-cause candidate: Value-realization erosion before renewal": "Principal hipótese: erosão de valor antes da renovação",
    "Retention risk is concentrated enough for a focused save motion": "O risco está concentrado o suficiente para uma operação de retenção",
    "The satisfaction story is incomplete without support friction and response coverage": "Satisfação média é incompleta sem fricção de suporte e cobertura de respostas",
    "Raw usage growth is not enough evidence of healthy adoption": "Crescimento bruto de uso não prova adoção saudável",
    "Priority accounts turn churn diagnosis into a revenue-protection queue": "Contas prioritárias transformam diagnóstico em fila de proteção de receita",
    "Churn labels conflict and should not be collapsed": "Labels de churn conflitam e não devem ser colapsados",
    "The next action is owner-based execution, not another analysis pass": "A próxima ação é execução por dono, não outro ciclo de análise",
    "Leadership": "Liderança",
    "CS": "CS",
    "Support": "Suporte",
    "Product": "Produto",
    "Pricing": "Pricing",
    "Data": "Dados",
    "Proposed": "Proposto",
    "features": "features",
    "pricing": "pricing",
    "budget": "budget",
    "unknown": "não informado",
    "0-7 days": "0-7 dias",
    "8-14 days": "8-14 dias",
    "15-30 days": "15-30 dias",
    "0-14 days": "0-14 dias",
    "account": "Conta",
    "segment": "Segmento",
    "data_quality": "Qualidade de dados",
    "product": "Produto",
    "support": "Suporte",
    "pricing": "Pricing",
}


def as_number(value: Any, default: float = 0.0) -> float:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return default
    return float(numeric)


def as_text(value: Any, fallback: str = "-") -> str:
    if value is None or pd.isna(value):
        return fallback
    rendered = str(value).strip()
    return rendered if rendered else fallback


def safe(value: Any, fallback: str = "-") -> str:
    return html.escape(as_text(value, fallback))


def pt(value: Any) -> str:
    text = as_text(value)
    return PT_LABELS.get(text, text)


def safe_pt(value: Any, fallback: str = "-") -> str:
    return html.escape(PT_LABELS.get(as_text(value, fallback), as_text(value, fallback)))


def money(value: float | int | str, compact: bool = False) -> str:
    numeric = as_number(value, default=float("nan"))
    if pd.isna(numeric):
        return "-"
    if compact:
        abs_value = abs(numeric)
        if abs_value >= 1_000_000:
            return f"US$ {numeric / 1_000_000:.1f}M"
        if abs_value >= 1_000:
            return f"US$ {numeric / 1_000:.0f}k"
    return f"US$ {numeric:,.0f}"


def rate(value: float | int | str) -> str:
    numeric = as_number(value, default=float("nan"))
    if pd.isna(numeric):
        return "-"
    return f"{numeric * 100:.1f}%"


def sorted_values(df: pd.DataFrame, column: str) -> list[str]:
    if column not in df.columns:
        return []
    values = [as_text(value) for value in df[column].dropna().unique().tolist()]
    return sorted(value for value in values if value != "-")


def clean_html(fragment: str) -> str:
    return "\n".join(line.strip() for line in dedent(fragment).strip().splitlines())


def emit_html(fragment: str) -> None:
    cleaned = clean_html(fragment)
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def export_file_name(export_name: str) -> str:
    file_names = {**REQUIRED_EXPORTS, **OPTIONAL_EXPORTS}
    return file_names.get(export_name, f"{export_name}.csv")


def render_download_button(label: str, df: pd.DataFrame, file_name: str, key: str) -> None:
    st.download_button(
        label=label,
        data=csv_bytes(df),
        file_name=file_name,
        mime="text/csv",
        key=key,
        width="stretch",
    )


def load_exports() -> dict[str, pd.DataFrame]:
    missing = [
        file_name for file_name in REQUIRED_EXPORTS.values() if not (EXPORTS_DIR / file_name).exists()
    ]
    if missing:
        missing_list = ", ".join(missing)
        raise FileNotFoundError(
            f"Missing required export files in {EXPORTS_DIR}: {missing_list}. "
            "Run build_exports.py before starting the dashboard."
        )
    exports = {
        name: pd.read_csv(EXPORTS_DIR / file_name)
        for name, file_name in REQUIRED_EXPORTS.items()
    }
    for name, file_name in OPTIONAL_EXPORTS.items():
        path = EXPORTS_DIR / file_name
        if path.exists():
            exports[name] = pd.read_csv(path)
    return exports


def inject_css() -> None:
    emit_html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@1,400&family=Manrope:wght@300;400;500;600;700;800&display=swap');
        :root {
          --g4-navy: #001F35;
          --g4-ink: #031A26;
          --g4-gold: #B9915B;
          --g4-silver: #F5F4F3;
          --g4-rust: #842E20;
          --g4-border: #D6D5D5;
          --g4-muted: #706F6F;
          --g4-white: #FFFFFF;
          --g4-radius-sm: 8px;
          --g4-radius-md: 10px;
          --g4-focus: rgba(185, 145, 91, 0.42);
        }
        * { box-sizing: border-box; }
        .stApp {
          background: var(--g4-silver);
          color: var(--g4-ink);
          font-family: "Manrope", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        h1, h2, h3, h4, h5, h6,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {
          color: var(--g4-ink);
          font-family: "Manrope", system-ui, sans-serif;
          font-weight: 600;
          letter-spacing: 0;
        }
        .block-container { max-width: 1220px; padding-top: 0; padding-bottom: 48px; }
        [data-testid="stVerticalBlock"] { gap: 0.85rem; }
        .g4-executive-header {
          width: 100vw;
          margin-left: calc(50% - 50vw);
          margin-right: calc(50% - 50vw);
          margin-top: 0;
          padding: 28px 24px 30px;
          background:
            radial-gradient(circle at 82% 0%, rgba(185, 145, 91, 0.18), rgba(185, 145, 91, 0) 34%),
            linear-gradient(171deg, #105C88 0%, #02131F 36%, #001F35 100%);
          border-bottom: 1px solid rgba(185, 145, 91, 0.26);
          box-sizing: border-box;
        }
        .g4-header-inner {
          max-width: 900px;
          margin: 0 auto;
        }
        .g4-header-top {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 18px;
          margin-bottom: 20px;
        }
        .g4-header-status {
          display: grid;
          gap: 2px;
          min-width: 180px;
          border: 1px solid rgba(185, 145, 91, 0.42);
          border-radius: 8px;
          padding: 10px 12px;
          background: rgba(255, 255, 255, 0.06);
        }
        .g4-header-status span {
          color: rgba(245, 244, 243, 0.72);
          font-size: 11px;
          font-weight: 800;
          text-transform: uppercase;
        }
        .g4-header-status strong {
          color: #F5F4F3;
          font-size: 13px;
          font-weight: 900;
        }
        .g4-eyebrow {
          margin: 0;
          color: #B9915B;
          font-size: 13px;
          font-weight: 800;
          text-transform: uppercase;
        }
        .g4-executive-header h1 {
          color: #F5F4F3 !important;
          font-size: 34px;
          font-weight: 900;
          line-height: 1.12;
          margin: 0 0 10px 0;
        }
        .g4-governing-thought {
          max-width: 900px;
          color: #F5F4F3;
          font-size: 18px;
          line-height: 1.48;
          margin: 0 0 18px 0;
        }
        .g4-chipline { display: flex; flex-wrap: wrap; gap: 8px; }
        .g4-chip {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-height: 30px;
          border: 1px solid rgba(185, 145, 91, 0.72);
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.06);
          color: #F5F4F3;
          padding: 6px 10px;
          font-size: 12px;
          font-weight: 850;
          line-height: 1.15;
        }
        .g4-chip-risk { background: rgba(132, 46, 32, 0.10); }
        .g4-button-row {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
          margin: 4px 0 18px;
        }
        .stButton > button {
          width: 100%;
          min-height: 44px;
          border: 1px solid #D6D5D5;
          border-radius: 8px;
          background: #FFFFFF;
          color: #031A26;
          font-weight: 850;
          white-space: normal;
          transition: background-color 120ms ease, border-color 120ms ease, color 120ms ease, transform 80ms ease;
        }
        .stButton > button[kind="primary"] {
          border-color: #B9915B;
          background: #001F35;
          color: #F5F4F3;
        }
        .stButton > button:hover {
          border-color: #B9915B;
          background: rgba(185, 145, 91, 0.12);
          color: #031A26;
        }
        .stButton > button[kind="primary"]:hover {
          background: #031A26;
          color: #F5F4F3;
        }
        .stButton > button:active {
          transform: translateY(1px);
          border-color: #001F35;
        }
        .stButton > button:focus-visible,
        [data-testid="stDownloadButton"] > button:focus-visible,
        button[data-baseweb="tab"]:focus-visible {
          outline: 3px solid var(--g4-focus) !important;
          outline-offset: 2px;
        }
        .stButton > button:disabled {
          border-color: #D6D5D5;
          background: #F5F4F3;
          color: #706F6F;
          opacity: 1;
        }
        [data-testid="stDownloadButton"] > button {
          width: 100%;
          min-height: 42px;
          border-radius: 8px;
          border: 1px solid #B9915B;
          background: #001F35;
          color: #F5F4F3;
          font-weight: 800;
          white-space: normal;
          transition: background-color 120ms ease, border-color 120ms ease, transform 80ms ease;
        }
        [data-testid="stDownloadButton"] > button:hover {
          border-color: #B9915B;
          background: #031A26;
          color: #F5F4F3;
        }
        [data-testid="stDownloadButton"] > button:active {
          transform: translateY(1px);
        }
        [data-testid="stDownloadButton"] > button *,
        [data-testid="stDownloadButton"] > button p {
          color: inherit !important;
          opacity: 1 !important;
        }
        .g4-section-kicker { color: #B9915B; font-size: 12px; font-weight: 800; text-transform: uppercase; margin: 20px 0 4px; }
        .g4-section-title { color: #031A26; font-size: 22px; font-weight: 800; line-height: 1.2; margin: 0 0 8px; }
        .g4-section-copy { color: #706F6F; font-size: 14px; line-height: 1.5; margin: 0 0 14px; }
        .g4-status-strip {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 14px;
          margin: -6px 0 18px;
        }
        .g4-status-cell,
        .g4-filter-summary {
          background: #FFFFFF;
          border: 1px solid #D6D5D5;
          border-radius: 8px;
          padding: 12px 14px;
          min-width: 0;
        }
        .g4-status-cell span,
        .g4-filter-summary span {
          display: block;
          color: #706F6F;
          font-size: 11px;
          font-weight: 900;
          line-height: 1.2;
          margin-bottom: 4px;
          text-transform: uppercase;
        }
        .g4-status-cell strong,
        .g4-filter-summary strong {
          display: block;
          color: #031A26;
          font-size: 14px;
          font-weight: 900;
          line-height: 1.25;
          overflow-wrap: anywhere;
        }
        .g4-status-cell p,
        .g4-filter-summary p {
          color: #706F6F;
          font-size: 12px;
          line-height: 1.35;
          margin: 5px 0 0;
        }
        .g4-status-cell--locked {
          border-color: rgba(185, 145, 91, 0.52);
          background: rgba(185, 145, 91, 0.08);
        }
        .g4-filter-summary {
          margin: 4px 0 12px;
          border-left: 4px solid #B9915B;
        }
        .g4-kpi-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 14px;
          margin: 18px 0 24px;
        }
        .g4-kpi {
          background: #FFFFFF;
          border: 1px solid #D6D5D5;
          border-radius: 10px;
          padding: 18px 18px 16px;
          min-height: 148px;
          position: relative;
          overflow: hidden;
        }
        .g4-kpi::before {
          content: "";
          display: block;
          width: 46px;
          height: 3px;
          background: #B9915B;
          border-radius: 999px;
          margin-bottom: 12px;
        }
        .g4-kpi--risk::before { background: #842E20; }
        .g4-kpi-label { color: #706F6F; font-size: 13px; font-weight: 800; margin-bottom: 8px; }
        .g4-kpi-value { color: #031A26; font-size: 29px; font-weight: 900; line-height: 1.08; overflow-wrap: anywhere; }
        .g4-kpi-note { color: #706F6F; font-size: 12px; line-height: 1.4; margin-top: 10px; }
        .g4-chart-card {
          background: #FFFFFF;
          border: 1px solid #D6D5D5;
          border-radius: 10px;
          padding: 16px 18px;
          margin: 8px 0 16px;
        }
        .g4-root-cause-grid {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
          gap: 20px;
          align-items: stretch;
          margin: 8px 0 16px;
        }
        .g4-root-cause-grid .g4-chart-card {
          display: flex;
          flex-direction: column;
          height: 100%;
          margin: 0;
        }
        .g4-root-cause-grid .g4-bar-row {
          flex: 1;
          min-height: 52px;
        }
        .g4-root-cause-grid .g4-action-grid--root {
          height: 100%;
          margin: 0;
          grid-template-rows: repeat(2, minmax(0, 1fr));
        }
        .g4-root-cause-grid .g4-action-card {
          height: 100%;
          min-height: 0;
        }
        .g4-chart-title {
          color: #031A26;
          font-size: 15px;
          font-weight: 900;
          margin: 0 0 14px;
        }
        .g4-bar-row {
          display: grid;
          grid-template-columns: minmax(160px, 260px) 1fr minmax(86px, auto);
          gap: 12px;
          align-items: center;
          padding: 9px 0;
          border-top: 1px solid rgba(214, 213, 213, 0.72);
        }
        .g4-bar-row:first-of-type { border-top: 0; }
        .g4-bar-label { color: #031A26; font-size: 13px; font-weight: 800; line-height: 1.25; }
        .g4-bar-note { display: block; color: #706F6F; font-size: 11px; font-weight: 500; margin-top: 3px; }
        .g4-bar-track {
          height: 18px;
          background: #F5F4F3;
          border: 1px solid #D6D5D5;
          border-radius: 999px;
          overflow: hidden;
        }
        .g4-bar-fill { height: 100%; min-width: 3px; border-radius: 999px; }
        .g4-bar-value { color: #031A26; font-size: 13px; font-weight: 900; text-align: right; white-space: nowrap; }
        .g4-stack-row {
          display: grid;
          grid-template-columns: 140px 1fr 74px;
          gap: 12px;
          align-items: center;
          padding: 10px 0;
          border-top: 1px solid rgba(214, 213, 213, 0.72);
        }
        .g4-stack-row:first-of-type { border-top: 0; }
        .g4-stack-track {
          display: flex;
          height: 20px;
          background: #F5F4F3;
          border: 1px solid #D6D5D5;
          border-radius: 999px;
          overflow: hidden;
        }
        .g4-stack-piece { height: 100%; min-width: 2px; }
        .g4-panel,
        .g4-finding,
        .g4-action-card,
        .g4-note,
        .g4-zero-state {
          background: #FFFFFF;
          border: 1px solid #D6D5D5;
          border-radius: 10px;
          padding: 16px 18px;
        }
        .g4-panel { margin-bottom: 14px; }
        .g4-segment-detail-grid {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
          gap: 14px;
          align-items: stretch;
          margin-top: 10px;
        }
        .g4-segment-detail-grid > * {
          height: 100%;
          min-height: 248px;
        }
        .g4-panel--segment {
          border-left: 4px solid #B9915B;
        }
        .g4-segment-title {
          color: #031A26;
          display: block;
          font-size: 20px;
          font-weight: 900;
          line-height: 1.22;
          margin-bottom: 10px;
          overflow-wrap: anywhere;
        }
        .g4-segment-summary {
          color: #706F6F;
          font-size: 15px;
          line-height: 1.45;
          margin: 0 0 14px;
        }
        .g4-segment-metric-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 8px;
          margin: 12px 0;
        }
        .g4-segment-metric {
          min-height: 76px;
          border: 1px solid rgba(214, 213, 213, 0.86);
          border-radius: 8px;
          background: #F5F4F3;
          padding: 10px;
          min-width: 0;
        }
        .g4-segment-metric span {
          color: #706F6F;
          display: block;
          font-size: 10px;
          font-weight: 900;
          line-height: 1.2;
          margin-bottom: 6px;
          text-transform: uppercase;
        }
        .g4-segment-metric strong {
          color: #031A26;
          display: block;
          font-size: 15px;
          font-weight: 900;
          line-height: 1.18;
          overflow-wrap: anywhere;
        }
        .g4-segment-playbook {
          border-top: 1px solid rgba(214, 213, 213, 0.86);
          color: #031A26;
          font-size: 13px;
          line-height: 1.42;
          margin: 12px 0 0;
          padding-top: 10px;
        }
        .g4-segment-playbook strong {
          display: inline;
          font-weight: 900;
        }
        .g4-finding {
          border-left: 4px solid #B9915B;
          margin-bottom: 12px;
        }
        .g4-finding strong,
        .g4-action-card strong,
        .g4-panel strong {
          color: #031A26;
          display: block;
          overflow-wrap: anywhere;
          word-break: normal;
        }
        .g4-finding p,
        .g4-action-card p,
        .g4-panel p {
          color: #706F6F;
          margin: 6px 0 0;
          line-height: 1.45;
          overflow-wrap: anywhere;
          word-break: normal;
        }
        .g4-meta-row {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 10px;
          align-items: flex-start;
        }
        .g4-pill {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-height: 28px;
          border-radius: 999px;
          padding: 6px 12px;
          font-size: 12px;
          font-weight: 800;
          background: #F5F4F3;
          color: #031A26;
          border: 1px solid #D6D5D5;
          max-width: 100%;
          white-space: normal;
          overflow-wrap: anywhere;
          word-break: normal;
          line-height: 1.2;
          text-align: center;
        }
        .g4-action-card .g4-meta-row {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(112px, 1fr));
          gap: 8px;
        }
        .g4-action-card .g4-pill {
          min-height: 34px;
          width: 100%;
        }
        .g4-pill-critical { color: #842E20; border-color: rgba(132, 46, 32, 0.35); background: rgba(132, 46, 32, 0.08); }
        .g4-pill-high { color: #031A26; border-color: rgba(185, 145, 91, 0.52); background: rgba(185, 145, 91, 0.13); }
        .g4-action-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
          margin-top: 10px;
        }
        .g4-action-grid--root {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .g4-action-card {
          min-height: 150px;
          border-top: 3px solid #B9915B;
          overflow: hidden;
          min-width: 0;
        }
        .g4-action-card--hot { border-top-color: #842E20; }
        .g4-action-grid--root .g4-action-card {
          min-height: 174px;
          padding: 14px;
        }
        .g4-action-grid--root .g4-action-card strong {
          font-size: 14px;
          line-height: 1.25;
        }
        .g4-action-grid--root .g4-action-card p {
          font-size: 13px;
          line-height: 1.35;
        }
        .g4-action-grid--root .g4-meta-row {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .g4-action-grid--root .g4-pill {
          min-height: 30px;
          padding: 5px 8px;
          font-size: 11px;
        }
        .g4-watchlist-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
          margin-top: 12px;
        }
        .g4-account-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          grid-auto-rows: 1fr;
          gap: 12px;
          margin: 12px 0 16px;
          align-items: stretch;
        }
        .g4-account-card {
          background: #FFFFFF;
          border: 1px solid #D6D5D5;
          border-radius: 8px;
          padding: 14px;
          min-height: 284px;
          border-top: 3px solid #B9915B;
          display: flex;
          flex-direction: column;
          gap: 10px;
          height: 100%;
          min-width: 0;
          overflow: hidden;
        }
        .g4-account-card--critical { border-top-color: #842E20; }
        .g4-account-card--high { border-top-color: #B9915B; }
        .g4-account-card-header {
          display: flex;
          justify-content: space-between;
          gap: 10px;
          align-items: flex-start;
          min-height: 58px;
        }
        .g4-account-title { min-width: 0; }
        .g4-account-rank {
          display: block;
          color: #B9915B;
          font-size: 11px;
          font-weight: 900;
          text-transform: uppercase;
          margin-bottom: 5px;
        }
        .g4-account-risk {
          flex: 0 0 auto;
          border: 1px solid rgba(185, 145, 91, 0.48);
          border-radius: 999px;
          background: rgba(185, 145, 91, 0.12);
          color: #031A26;
          font-size: 11px;
          font-weight: 900;
          line-height: 1;
          padding: 7px 9px;
          white-space: nowrap;
        }
        .g4-account-card--critical .g4-account-risk {
          border-color: rgba(132, 46, 32, 0.35);
          background: rgba(132, 46, 32, 0.08);
          color: #842E20;
        }
        .g4-account-name {
          display: block;
          color: #031A26;
          font-size: 16px;
          font-weight: 900;
          line-height: 1.25;
          overflow-wrap: anywhere;
        }
        .g4-account-metrics {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 8px;
        }
        .g4-account-metric {
          min-height: 58px;
          border: 1px solid rgba(214, 213, 213, 0.86);
          border-radius: 8px;
          background: #F5F4F3;
          padding: 8px;
          min-width: 0;
        }
        .g4-account-metric span {
          display: block;
          color: #706F6F;
          font-size: 10px;
          font-weight: 900;
          line-height: 1.15;
          text-transform: uppercase;
          margin-bottom: 5px;
        }
        .g4-account-metric strong {
          display: block;
          color: #031A26;
          font-size: 14px;
          font-weight: 900;
          line-height: 1.15;
          overflow-wrap: anywhere;
        }
        .g4-account-action {
          flex: 1;
          color: #031A26;
          font-size: 13px;
          line-height: 1.42;
          margin: 0;
          padding-top: 10px;
          border-top: 1px solid rgba(214, 213, 213, 0.72);
          overflow-wrap: anywhere;
        }
        .g4-account-action strong {
          display: inline;
          color: #031A26;
        }
        .g4-account-footer {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: auto;
          align-items: flex-start;
        }
        .g4-zero-state {
          border-style: dashed;
          text-align: center;
          padding: 28px;
        }
        .g4-zero-state h3 { margin: 0 0 8px; color: #031A26; }
        .g4-zero-state p { margin: 0; color: #706F6F; }
        .g4-timeline {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 8px;
          margin-top: 12px;
        }
        .g4-timeline div {
          border: 1px solid #D6D5D5;
          border-radius: 8px;
          padding: 10px;
          background: #FFFFFF;
        }
        .g4-timeline span { display: block; color: #706F6F; font-size: 12px; font-weight: 800; margin-bottom: 4px; }
        .g4-timeline strong { color: #031A26; font-size: 13px; line-height: 1.35; }
        div[data-baseweb="tab-list"] {
          gap: 8px;
          align-items: center;
          margin-bottom: 10px;
        }
        button[data-baseweb="tab"] {
          border: 1px solid #D6D5D5 !important;
          border-radius: 8px !important;
          background: #FFFFFF !important;
          box-shadow: none !important;
          color: #031A26 !important;
          min-height: 42px;
          padding: 8px 12px !important;
        }
        button[data-baseweb="tab"] *,
        button[data-baseweb="tab"] p,
        button[data-baseweb="tab"] span,
        button[data-baseweb="tab"] div {
          color: #031A26 !important;
          opacity: 1 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
          background: #001F35 !important;
          border-color: #B9915B !important;
          color: #F5F4F3 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] *,
        button[data-baseweb="tab"][aria-selected="true"] p,
        button[data-baseweb="tab"][aria-selected="true"] span,
        button[data-baseweb="tab"][aria-selected="true"] div {
          color: #F5F4F3 !important;
        }
        button[data-baseweb="tab"]:hover,
        button[data-baseweb="tab"]:focus-visible {
          background: #F5F4F3 !important;
          border-color: #B9915B !important;
          color: #031A26 !important;
        }
        button[data-baseweb="tab"]:hover *,
        button[data-baseweb="tab"]:focus-visible * {
          color: #031A26 !important;
        }
        button[data-baseweb="tab"][disabled],
        button[data-baseweb="tab"][aria-disabled="true"] {
          background: #FFFFFF !important;
          border-color: #D6D5D5 !important;
          color: #706F6F !important;
          opacity: 1 !important;
        }
        button[data-baseweb="tab"][disabled] *,
        button[data-baseweb="tab"][aria-disabled="true"] * {
          color: #706F6F !important;
          opacity: 1 !important;
        }
        [data-testid="stDataFrame"] { font-size: 13px; }
        [data-testid="stSelectbox"] label p,
        [data-testid="stMultiSelect"] label p,
        [data-testid="stNumberInput"] label p,
        [data-testid="stTextInput"] label p {
          color: #031A26;
          font-weight: 850;
        }
        @media (max-width: 900px) {
          .g4-kpi-grid, .g4-action-grid, .g4-watchlist-grid, .g4-account-grid, .g4-button-row, .g4-status-strip, .g4-segment-detail-grid, .g4-root-cause-grid { grid-template-columns: 1fr; }
          .g4-timeline { grid-template-columns: 1fr 1fr; }
          .g4-bar-row, .g4-stack-row { grid-template-columns: 1fr; gap: 6px; }
          .g4-bar-value { text-align: left; }
          .g4-executive-header h1 { font-size: 28px; }
          .g4-header-top { align-items: flex-start; flex-direction: column; }
          .g4-action-grid--root { grid-template-columns: 1fr; }
        }
        @media (max-width: 560px) {
          .block-container { padding-left: 14px; padding-right: 14px; }
          .g4-executive-header { padding: 22px 18px; }
          .g4-kpi-value { font-size: 24px; }
          .g4-timeline { grid-template-columns: 1fr; }
          .block-container { padding-bottom: 112px; }
          div[data-baseweb="tab-list"] {
            position: fixed;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 999;
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 6px;
            padding: 8px 10px calc(8px + env(safe-area-inset-bottom));
            margin: 0;
            background: #001F35;
            border-top: 1px solid rgba(185, 145, 91, 0.42);
            box-shadow: 0 -8px 24px rgba(3, 26, 38, 0.22);
          }
          button[data-baseweb="tab"] {
            min-height: 44px;
            padding: 6px 4px !important;
            border-color: rgba(185, 145, 91, 0.36) !important;
          }
          button[data-baseweb="tab"] p,
          button[data-baseweb="tab"] span {
            font-size: 12px !important;
            line-height: 1.15 !important;
            white-space: normal !important;
          }
        }
        @media (prefers-reduced-motion: reduce) {
          .stButton > button,
          [data-testid="stDownloadButton"] > button {
            transition: none;
          }
        }
        </style>
        """
    )


def critical_high_summary(risk_segments: pd.DataFrame) -> tuple[int, float, float]:
    focused = risk_segments[risk_segments["risk_segment"].isin(["Critical", "High"])]
    accounts = int(focused["account_count"].sum())
    mrr = float(focused["mrr_at_risk"].sum())
    arr = float(focused["current_arr"].sum())
    return accounts, mrr, arr


def share_pct(value: float | int | str, total: float | int | str) -> str:
    numerator = as_number(value, default=float("nan"))
    denominator = as_number(total, default=float("nan"))
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return "-"
    return f"{(numerator / denominator) * 100:.1f}%"


def segment_value_summary(risk_segments: pd.DataFrame) -> dict[str, Any]:
    total_mrr = float(risk_segments["mrr_at_risk"].sum())
    total_arr = float(risk_segments["current_arr"].sum())
    top_segment = risk_segments.loc[risk_segments["mrr_at_risk"].idxmax()]
    critical_rows = risk_segments[risk_segments["risk_segment"].eq("Critical")]
    critical = critical_rows.iloc[0] if not critical_rows.empty else top_segment
    medium_low = risk_segments[risk_segments["risk_segment"].isin(["Medium", "Low"])]
    return {
        "total_mrr": total_mrr,
        "total_arr": total_arr,
        "top_segment": top_segment,
        "critical_segment": critical,
        "medium_low_mrr": float(medium_low["mrr_at_risk"].sum()),
        "medium_low_accounts": int(medium_low["account_count"].sum()),
    }


def churn_label_rates(account_health: pd.DataFrame) -> tuple[float, float]:
    event_rate = account_health["has_churn_event"].astype(bool).mean()
    flag_rate = account_health["account_churn_flag"].astype(bool).mean()
    return float(event_rate), float(flag_rate)


def root_cause_frame(exports: dict[str, pd.DataFrame]) -> pd.DataFrame:
    root_causes = exports.get("root_cause_candidates")
    if root_causes is not None and not root_causes.empty:
        return root_causes.sort_values("rank").copy()
    findings = exports["executive_findings"].copy()
    return findings.rename(
        columns={
            "finding_id": "candidate_id",
            "finding_title": "root_cause_candidate",
            "affected_accounts": "affected_accounts",
            "mrr_at_risk": "mrr_at_risk",
            "confidence_level": "confidence_level",
            "recommended_action": "recommended_action",
            "owner_team": "owner_team",
            "false_causality_risk": "false_causality_risk",
        }
    )


def root_cause_summary_pt(row: pd.Series) -> str:
    summaries = {
        "RC-01": "Contas de risco Médio+ combinam histórico de churn, suporte, qualidade de uso e sinais comerciais antes da renovação.",
        "RC-02": "Tickets urgentes, escalonamentos e baixa cobertura de satisfação podem esconder fricção operacional relevante.",
        "RC-03": "Downgrades, ausência de auto-renew e estágio comercial expõem risco antes da perda formal.",
        "RC-04": "Motivos de preço e orçamento indicam pressão de valor percebido; desconto amplo não deve ser a primeira resposta.",
        "RC-05": "Sinais de features e uso válido baixo pedem revisão de adoção antes de chamar crescimento de uso de sucesso.",
        "RC-06": "Labels conflitantes e uso fora da janela de assinatura explicam parte da ambiguidade da decisão.",
        "F-01": "Contas de risco Médio+ combinam histórico de churn, suporte, qualidade de uso e sinais comerciais antes da renovação.",
        "F-02": "O maior valor exposto não está no rótulo Crítico; severidade e bolso precisam ser lidos separados.",
        "F-03": "Tickets urgentes, escalonamentos e baixa cobertura de satisfação tornam a média de satisfação insuficiente.",
        "F-04": "Uso bruto fora da janela de assinatura impede tratar crescimento agregado como adoção saudável.",
        "F-05": "A watchlist transforma o diagnóstico em fila de proteção de receita por conta e dono.",
        "F-06": "Labels de churn conflitantes precisam de governança antes de forecast, metas ou compensação.",
        "F-07": "A próxima etapa é execução por dono, com validação de intervenção, não outro ciclo de análise.",
    }
    return summaries.get(as_text(row.get("candidate_id")), as_text(row.get("evidence_summary")))


def finding_summary_pt(row: pd.Series) -> tuple[str, str, str]:
    summaries = {
        "F-01": (
            "Risco de churn aparece como erosão de valor antes da renovação, não como uma métrica isolada.",
            "A hipótese cruza histórico de churn, suporte, uso em janela válida e sinais comerciais.",
            "Rodar uma operação de retenção por valor exposto, mantendo SLA acelerado para contas Crítico/Alto.",
        ),
        "F-02": (
            "O valor em risco está concentrado por MRR, não pelo nome do segmento.",
            "Crítico é urgência operacional; a maior parte do bolso aparece em segmentos com maior volume de contas.",
            "Priorizar a fila por MRR e próxima ação, sem ignorar SLA de resposta para contas Crítico/Alto.",
        ),
        "F-03": (
            "Satisfação média não conta a história completa.",
            "Contas com evento de churn têm alta incidência de tickets urgentes e respostas de satisfação incompletas.",
            "Criar fila de fricção de suporte para contas com churn, urgência, escalonamento ou missing satisfaction.",
        ),
    }
    return summaries.get(
        as_text(row.get("finding_id")),
        (
            as_text(row.get("plain_language_finding")),
            as_text(row.get("evidence_summary")),
            as_text(row.get("recommended_action")),
        ),
    )


def backlog_action_pt(row: pd.Series) -> str:
    scope = as_text(row.get("scope_type"))
    theme = as_text(row.get("action_theme"))
    if scope == "account":
        if theme == "Churn history":
            return "Rodar save playbook usando histórico de churn e motivo mais recente como roteiro."
        if theme == "Revenue exposure":
            return "Priorizar revisão executiva da conta pelo MRR em risco."
        if theme == "Support friction":
            return "Abrir frente de suporte antes da próxima renovação."
        if theme == "Subscription/commercial":
            return "Revisar risco comercial, renovação e downgrade."
        return "Confirmar próxima ação da conta com o dono indicado."
    if theme == "Segment save playbook":
        return f"Executar playbook de retenção do segmento {safe_pt(row.get('risk_segment'))}."
    if theme == "Support friction":
        return "Criar fila semanal para contas com tickets urgentes, altos ou escalados."
    if theme == "Product usage quality":
        return "Investigar fluxos com erro alto e uso válido baixo antes de chamar uso de saudável."
    if theme == "Pricing churn review":
        return "Revisar churn por preço/orçamento com prova de valor e ofertas de renovação."
    if theme == "Usage validity contract":
        return "Instrumentar validação de janela de assinatura antes de usar métricas de uso."
    if theme == "Churn label governance":
        return "Definir o label operacional de churn antes de forecast e metas."
    return "Revisar evidência, dono, prazo e impacto esperado antes da próxima reunião."


def backlog_evidence_pt(row: pd.Series) -> str:
    scope = as_text(row.get("scope_type"))
    if scope == "account":
        return f"{money(row.get('mrr_at_risk'), compact=True)} de MRR associado e {safe_pt(row.get('priority'))} prioridade."
    return (
        f"{int(as_number(row.get('account_count_impacted')))} contas impactadas; "
        f"{money(row.get('mrr_at_risk'), compact=True)} de MRR associado."
    )


def segment_playbook_pt(segment: str) -> str:
    playbooks = {
        "Critical": "Plano de retenção patrocinado por liderança em até 7 dias.",
        "High": "Intervenção CS com follow-up de suporte/produto em até 14 dias.",
        "Medium": "Monitorar semanalmente e acionar playbook se surgir novo sinal de suporte ou downgrade.",
        "Low": "Monitoramento padrão de saúde da conta.",
    }
    return playbooks.get(segment, "-")


def render_header(exports: dict[str, pd.DataFrame]) -> None:
    value_summary = segment_value_summary(exports["risk_segments"])
    top_segment = value_summary["top_segment"]
    critical = value_summary["critical_segment"]
    top_cause = root_cause_frame(exports).iloc[0]
    emit_html(
        f"""
        <section class="g4-executive-header">
          <div class="g4-header-inner">
          <div class="g4-header-top">
            <p class="g4-eyebrow">Exports canônicos | Visão CEO + Mesa de Operações CS</p>
          </div>
          <h1>RavenStack Churn Diagnosis</h1>
          <p class="g4-governing-thought">{money(value_summary['total_mrr'], compact=True)} de MRR está exposto no total. O maior bolso está em <strong>{safe_pt(top_segment['risk_segment'])}</strong> ({money(top_segment['mrr_at_risk'], compact=True)}, {share_pct(top_segment['mrr_at_risk'], value_summary['total_mrr'])}); <strong>Crítico soma {money(critical['mrr_at_risk'], compact=True)}</strong>. Priorize valor por conta, não apenas o rótulo de risco. A hipótese de causa raiz é <strong>{safe_pt(top_cause['root_cause_candidate'])}</strong>.</p>
          <div class="g4-chipline">
            <span class="g4-chip">uso em janela válida</span>
            <span class="g4-chip">labels de churn separados</span>
            <span class="g4-chip">watchlist de contas</span>
            <span class="g4-chip">valor exposto antes do label</span>
            <span class="g4-chip g4-chip-risk">evidência observacional, não prova causal</span>
          </div>
          </div>
        </section>
        """
    )


def render_kpis(exports: dict[str, pd.DataFrame]) -> None:
    risk = exports["risk_segments"]
    priority = exports["priority_accounts"]
    account_health = exports["account_health"]
    value_summary = segment_value_summary(risk)
    top_segment = value_summary["top_segment"]
    critical = value_summary["critical_segment"]
    event_rate, flag_rate = churn_label_rates(account_health)
    top10 = priority.head(10)
    top10_mrr = top10["mrr_at_risk"].sum()
    top10_arr = top10["current_arr"].sum()

    emit_html(
        f"""
        <section class="g4-kpi-grid">
          <div class="g4-kpi g4-kpi--risk">
            <div class="g4-kpi-label">MRR total exposto</div>
            <div class="g4-kpi-value">{money(value_summary['total_mrr'])}</div>
            <div class="g4-kpi-note">{money(value_summary['total_arr'], compact=True)} de ARR. Maior bolso: {safe_pt(top_segment['risk_segment'])} com {share_pct(top_segment['mrr_at_risk'], value_summary['total_mrr'])}; Crítico tem {money(critical['mrr_at_risk'], compact=True)}.</div>
          </div>
          <div class="g4-kpi">
            <div class="g4-kpi-label">Churn atual vs. meta</div>
            <div class="g4-kpi-value">{rate(event_rate)} / {rate(flag_rate)}</div>
            <div class="g4-kpi-note">Histórico de eventos vs. flag da conta. Benchmark/meta externa não está no export; isso vira lacuna de governança.</div>
          </div>
          <div class="g4-kpi g4-kpi--risk">
            <div class="g4-kpi-label">Top 10 contas por valor</div>
            <div class="g4-kpi-value">{money(top10_mrr)}</div>
            <div class="g4-kpi-note">{money(top10_arr, compact=True)} de ARR nas dez primeiras contas. Comece aqui antes de campanhas amplas.</div>
          </div>
        </section>
        """
    )


def render_workspace_status(exports: dict[str, pd.DataFrame]) -> None:
    required_loaded = sum(1 for name in REQUIRED_EXPORTS if name in exports)
    optional_loaded = sum(1 for name in OPTIONAL_EXPORTS if name in exports)
    account_rows = len(exports["priority_accounts"])
    backlog_rows = len(exports["action_backlog"])
    emit_html(
        f"""
        <section class="g4-status-strip" aria-label="Status operacional">
          <div class="g4-status-cell">
            <span>Fonte de dados</span>
            <strong>solution/exports/</strong>
            <p>{required_loaded} exports obrigatórios e {optional_loaded} auxiliares carregados.</p>
          </div>
          <div class="g4-status-cell g4-status-cell--locked">
            <span>Contrato</span>
            <strong>Dashboard sem escrita</strong>
            <p>Não faz join, não recalcula score e não altera dados.</p>
          </div>
          <div class="g4-status-cell">
            <span>Fila ativa</span>
            <strong>{account_rows} contas | {backlog_rows} ações</strong>
            <p>Diagnóstico executivo conectado à execução de CS.</p>
          </div>
        </section>
        """
    )


def ensure_cs_filter_state(priority_accounts: pd.DataFrame) -> None:
    available_risks = [risk for risk in ["Critical", "High"] if risk in priority_accounts["risk_segment"].tolist()]
    defaults: dict[str, Any] = {
        "cs_risk_filter": available_risks,
        "cs_plan_filter": [],
        "cs_reason_filter": [],
        "cs_due_filter": ["0-7 days", "8-14 days"],
        "cs_owner_filter": [],
        "cs_churn_reason_filter": [],
        "cs_min_mrr": 0,
        "cs_search": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    valid_options = {
        "cs_risk_filter": [risk for risk in RISK_ORDER if risk in priority_accounts["risk_segment"].tolist()],
        "cs_plan_filter": sorted_values(priority_accounts, "plan_tier"),
        "cs_reason_filter": sorted_values(priority_accounts, "primary_risk_driver"),
        "cs_due_filter": sorted_values(priority_accounts, "due_bucket"),
        "cs_owner_filter": sorted_values(priority_accounts, "action_owner"),
        "cs_churn_reason_filter": sorted_values(priority_accounts, "latest_reason_code"),
    }
    for key, options in valid_options.items():
        st.session_state[key] = [value for value in st.session_state[key] if value in options]


def set_cs_focus(
    *,
    risks: list[str] | None = None,
    reasons: list[str] | None = None,
    churn_reasons: list[str] | None = None,
    due: list[str] | None = None,
    owner: list[str] | None = None,
    min_mrr: int = 0,
) -> None:
    st.session_state["cs_risk_filter"] = risks if risks is not None else []
    st.session_state["cs_reason_filter"] = reasons if reasons is not None else []
    st.session_state["cs_churn_reason_filter"] = churn_reasons if churn_reasons is not None else []
    st.session_state["cs_due_filter"] = due if due is not None else []
    st.session_state["cs_owner_filter"] = owner if owner is not None else []
    st.session_state["cs_min_mrr"] = min_mrr
    st.session_state["cs_search"] = ""


def render_action_buttons(priority_accounts: pd.DataFrame) -> None:
    ensure_cs_filter_state(priority_accounts)
    section_intro(
        "Ações recomendadas",
        "Transforme o diagnóstico em uma fila de trabalho agora.",
        "Cada comando muda apenas a fila visível. Nenhum dado é alterado.",
    )
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Focar Crítico/Alto", type="primary"):
        set_cs_focus(risks=["Critical", "High"], due=["0-7 days", "8-14 days"], owner=["CS"])
        st.toast("Mesa CS focada em SLA Crítico/Alto; priorização financeira continua por MRR.")
    if c2.button("Abrir fila de suporte"):
        set_cs_focus(risks=["Critical", "High", "Medium"], reasons=["Support friction"], owner=["Support"])
        st.toast("Mesa CS focada em fricção de suporte.")
    if c3.button("Revisar preço"):
        set_cs_focus(
            reasons=["Revenue exposure", "Subscription/commercial"],
            churn_reasons=["pricing", "budget"],
            owner=["Leadership", "Pricing"],
        )
        st.toast("Mesa CS focada em exposição de receita e risco comercial.")
    if c4.button("Oferecer treinamento"):
        set_cs_focus(risks=["Critical", "High", "Medium"], churn_reasons=["features"], owner=["CS"])
        st.toast("Mesa CS focada em sinais de uso e adoção.")


def section_intro(kicker: str, title: str, copy: str = "") -> None:
    emit_html(
        f"""
        <p class="g4-section-kicker">{safe(kicker)}</p>
        <h2 class="g4-section-title">{safe(title)}</h2>
        {f'<p class="g4-section-copy">{safe(copy)}</p>' if copy else ''}
        """
    )


def render_findings(findings: pd.DataFrame) -> None:
    section_intro(
        "Resumo executivo",
        "Salvar contas nomeadas tem mais valor agora do que abrir outro diagnóstico.",
        "Cada bloco abaixo segue sinal, evidência, ação e dono para o CEO decidir em menos de 60 segundos.",
    )
    for _, row in findings.head(3).iterrows():
        signal, evidence, action = finding_summary_pt(row)
        emit_html(
            f"""
            <div class="g4-finding">
              <strong>{safe(row['finding_id'])} - {safe_pt(row['finding_title'])}</strong>
              <p><strong>Sinal:</strong> {safe(signal)}</p>
              <p><strong>Evidência:</strong> {safe(evidence)}</p>
              <p><strong>Ação:</strong> {safe(action)}</p>
              <div class="g4-meta-row">
                <span class="g4-pill">{safe_pt(row['owner_team'])}</span>
                <span class="g4-pill">Confiança {safe_pt(row['confidence_level'])}</span>
                <span class="g4-pill">{money(row['mrr_at_risk'], compact=True)} MRR exposto</span>
              </div>
            </div>
            """
        )


def horizontal_bars_html(title: str, rows: list[dict[str, Any]], extra_class: str = "") -> str:
    max_value = max(as_number(row.get("value")) for row in rows) or 1
    classes = f"g4-chart-card {extra_class}".strip()
    html_rows = [f'<div class="{safe(classes)}"><p class="g4-chart-title">{safe(title)}</p>']
    for row in rows:
        value = as_number(row.get("value"))
        width = max(3, min(100, (value / max_value) * 100))
        color = as_text(row.get("color"), G4_GOLD)
        html_rows.append(
            f"""
            <div class="g4-bar-row">
              <div class="g4-bar-label">{safe(row.get('label'))}<span class="g4-bar-note">{safe(row.get('note', ''))}</span></div>
              <div class="g4-bar-track"><div class="g4-bar-fill" style="width:{width:.1f}%; background:{safe(color)};"></div></div>
              <div class="g4-bar-value">{safe(row.get('value_label'))}</div>
            </div>
            """
        )
    html_rows.append("</div>")
    return "".join(html_rows)


def render_horizontal_bars(title: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        render_zero_state("Sem dados para o gráfico", "Ajuste os filtros ou gere novamente os exports.")
        return
    emit_html(horizontal_bars_html(title, rows))


def render_stacked_owner_bars(title: str, action_backlog: pd.DataFrame) -> None:
    if action_backlog.empty:
        render_zero_state("Sem dados para o gráfico", "Ajuste os filtros ou gere novamente os exports.")
        return
    owners = sorted_values(action_backlog, "owner_team")
    summary: dict[tuple[str, str], float] = {}
    owner_totals: dict[str, float] = {}
    for _, row in action_backlog.iterrows():
        owner = as_text(row["owner_team"])
        priority = as_text(row["priority"])
        accounts = as_number(row.get("account_count_impacted"))
        summary[(owner, priority)] = summary.get((owner, priority), 0.0) + accounts
        owner_totals[owner] = owner_totals.get(owner, 0.0) + accounts

    html_rows = [f'<div class="g4-chart-card"><p class="g4-chart-title">{safe(title)}</p>']
    for owner in owners:
        total = owner_totals.get(owner, 0.0) or 1
        html_rows.append(
            f"""
            <div class="g4-stack-row">
              <div class="g4-bar-label">{safe_pt(owner)}</div>
              <div class="g4-stack-track">
            """
        )
        for priority in ["Critical", "High", "Medium", "Low"]:
            value = summary.get((owner, priority), 0.0)
            if value <= 0:
                continue
            width = max(4, (value / total) * 100)
            html_rows.append(
                f'<div class="g4-stack-piece" title="{safe_pt(priority)}: {int(value)}" style="width:{width:.1f}%; background:{RISK_COLORS.get(priority, G4_MUTED)};"></div>'
            )
        html_rows.append(
            f"""
              </div>
              <div class="g4-bar-value">{int(total)} contas</div>
            </div>
            """
        )
    html_rows.append("</div>")
    emit_html("".join(html_rows))


def root_cause_bar_rows(root_causes: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for _, row in root_causes.head(6).iterrows():
        rank = int(as_number(row.get("rank"), 9))
        rows.append(
            {
                "label": pt(row["root_cause_candidate"]),
                "note": f"{int(as_number(row['affected_accounts']))} contas | Confiança {pt(row['confidence_level'])}",
                "value": as_number(row["mrr_at_risk"]),
                "value_label": money(row["mrr_at_risk"], compact=True),
                "color": G4_RUST if rank == 1 else G4_GOLD if rank in (2, 3) else G4_MUTED,
            }
        )
    return rows


def segment_bar_rows(risk_segments: pd.DataFrame) -> list[dict[str, Any]]:
    ordered = risk_segments.set_index("risk_segment").reindex(RISK_ORDER).dropna(how="all").reset_index()
    total_mrr = float(ordered["mrr_at_risk"].sum())
    return [
        {
            "label": pt(row["risk_segment"]),
            "note": (
                f"{int(as_number(row['account_count']))} contas | "
                f"{share_pct(row['mrr_at_risk'], total_mrr)} do MRR | "
                f"Top motivo: {pt(row['top_churn_reason'])}"
            ),
            "value": as_number(row["mrr_at_risk"]),
            "value_label": money(row["mrr_at_risk"], compact=True),
            "color": RISK_COLORS.get(as_text(row["risk_segment"]), G4_MUTED),
        }
        for _, row in ordered.iterrows()
    ]


def segment_so_what_pt(segment_name: str, segment: pd.Series, total_mrr: float) -> str:
    segment_share = share_pct(segment["mrr_at_risk"], total_mrr)
    if segment_name == "Critical":
        return f"Crítico exige SLA imediato, mas representa {segment_share} do MRR exposto. Não use este rótulo como proxy do maior problema financeiro."
    if segment_name == "High":
        return f"Alto combina urgência e valor relevante ({segment_share} do MRR), mas ainda não é o maior bolso do portfólio."
    if segment_name == "Medium":
        return f"Médio é o maior bolso financeiro ({segment_share} do MRR). Aqui a operação deve ser escalável, por cadência e playbook, não apenas atendimento emergencial."
    if segment_name == "Low":
        return f"Baixo não é urgência imediata, mas ainda soma {segment_share} do MRR. Monitore para evitar que volume vire perda silenciosa."
    return "Separe severidade operacional de impacto financeiro antes de decidir a próxima ação."


def priority_account_bar_rows(priority_accounts: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for _, row in priority_accounts.head(12).iterrows():
        rows.append(
            {
                "label": f"#{int(as_number(row['priority_rank']))} {as_text(row['account_name'])}",
                "note": f"{pt(row['risk_segment'])} | {pt(row['primary_risk_driver'])} | {pt(row['due_bucket'])}",
                "value": as_number(row["mrr_at_risk"]),
                "value_label": money(row["mrr_at_risk"], compact=True),
                "color": RISK_COLORS.get(as_text(row["risk_segment"]), G4_MUTED),
            }
        )
    return rows


def render_root_cause(exports: dict[str, pd.DataFrame]) -> None:
    root_causes = root_cause_frame(exports)
    section_intro(
        "Causa raiz e impacto",
        "A hipótese mais cara é erosão de valor antes da renovação; suporte e produto explicam onde investigar primeiro.",
        "As barras usam exports já gerados. Valores de causa podem se sobrepor; a decisão correta é validar em account reviews.",
    )
    chart_html = horizontal_bars_html(
        "Impacto financeiro por hipótese de causa raiz",
        root_cause_bar_rows(root_causes),
        "g4-chart-card--root",
    )
    cards_html = ['<div class="g4-action-grid g4-action-grid--root">']
    for _, row in root_causes.head(4).iterrows():
        hot = "g4-action-card--hot" if as_number(row.get("rank"), 9) <= 2 else ""
        cards_html.append(
            f"""
            <div class="g4-action-card {hot}">
              <strong>{safe_pt(row['root_cause_candidate'])}</strong>
              <p>{safe(root_cause_summary_pt(row))}</p>
              <div class="g4-meta-row">
                <span class="g4-pill">{money(row['mrr_at_risk'], compact=True)} MRR</span>
                <span class="g4-pill">{int(as_number(row['affected_accounts']))} contas</span>
                <span class="g4-pill">{safe_pt(row['owner_team'])}</span>
              </div>
            </div>
            """
        )
    cards_html.append("</div>")
    emit_html(
        f"""
        <div class="g4-root-cause-grid">
          {chart_html}
          {''.join(cards_html)}
        </div>
        """
    )


def render_risk_segments(
    risk_segments: pd.DataFrame, usage_growth: pd.DataFrame | None
) -> None:
    value_summary = segment_value_summary(risk_segments)
    top_segment = value_summary["top_segment"]
    critical = value_summary["critical_segment"]
    section_intro(
        "Segmentos",
        f"O maior problema financeiro está em {safe_pt(top_segment['risk_segment'])}: {money(top_segment['mrr_at_risk'], compact=True)} de MRR ({share_pct(top_segment['mrr_at_risk'], value_summary['total_mrr'])}).",
        f"Crítico soma {money(critical['mrr_at_risk'], compact=True)}; trate como urgência operacional, não como maior bolso.",
    )
    render_horizontal_bars(
        "Impacto financeiro por segmento de risco",
        segment_bar_rows(risk_segments),
    )

    selected_segment = st.selectbox(
        "Segmento",
        [segment for segment in RISK_ORDER if segment in risk_segments["risk_segment"].tolist()],
        index=0,
        key="risk_segment_select",
        format_func=pt,
    )
    segment = risk_segments[risk_segments["risk_segment"].eq(selected_segment)].iloc[0]
    segment_share = share_pct(segment["mrr_at_risk"], value_summary["total_mrr"])
    emit_html(
        f"""
        <div class="g4-segment-detail-grid">
          <div class="g4-panel g4-panel--segment">
            <strong class="g4-segment-title">{safe_pt(selected_segment)}: {money(segment['mrr_at_risk'], compact=True)} de MRR em risco</strong>
            <p class="g4-segment-summary">Este segmento representa {segment_share} do MRR exposto e deve ser lido junto da urgência operacional, não como métrica isolada.</p>
            <div class="g4-segment-metric-grid">
              <div class="g4-segment-metric"><span>Contas</span><strong>{int(segment['account_count'])}</strong></div>
              <div class="g4-segment-metric"><span>ARR atual</span><strong>{money(segment['current_arr'], compact=True)}</strong></div>
              <div class="g4-segment-metric"><span>Churn evento</span><strong>{rate(segment['event_based_churn_rate'])}</strong></div>
              <div class="g4-segment-metric"><span>Churn flag</span><strong>{rate(segment['account_flag_churn_rate'])}</strong></div>
            </div>
            <p class="g4-segment-playbook"><strong>Motivo principal:</strong> {safe_pt(segment['top_churn_reason'])}. <strong>Playbook:</strong> {safe(segment_playbook_pt(selected_segment))}</p>
          </div>
          <div class="g4-note g4-note--segment">
            <strong>So what?</strong>
            <p>{safe(segment_so_what_pt(selected_segment, segment, value_summary['total_mrr']))}</p>
            <p>Use este gráfico para separar severidade operacional de impacto financeiro antes de priorizar account reviews.</p>
          </div>
        </div>
        """
    )

    with st.expander("Detalhe técnico dos segmentos", expanded=False):
        segment_table = risk_segments[
            [
                "risk_segment",
                "account_count",
                "mrr_at_risk",
                "current_arr",
                "event_based_churn_rate",
                "account_flag_churn_rate",
                "top_churn_reason",
                "recommended_playbook",
            ]
        ].rename(
            columns={
                "risk_segment": "Segmento",
                "account_count": "Contas",
                "mrr_at_risk": "MRR em risco",
                "current_arr": "ARR",
                "event_based_churn_rate": "Churn por evento",
                "account_flag_churn_rate": "Churn por flag",
                "top_churn_reason": "Motivo principal",
                "recommended_playbook": "Playbook",
            }
        )
        st.dataframe(
            segment_table,
            column_config={
                "MRR em risco": st.column_config.NumberColumn("MRR em risco", format="US$ %.0f"),
                "ARR": st.column_config.NumberColumn("ARR", format="US$ %.0f"),
                "Churn por evento": st.column_config.NumberColumn("Churn por evento", format="%.2f"),
                "Churn por flag": st.column_config.NumberColumn("Churn por flag", format="%.2f"),
            },
            width="stretch",
            hide_index=True,
        )

    if usage_growth is not None:
        growth = usage_growth[usage_growth["segment_type"].eq("risk_segment")]
        with st.expander("Crescimento bruto vs. uso em janela válida", expanded=False):
            st.caption("Crescimento de uso é mostrado de 2024-H1 para 2024-H2. Uso bruto não é tratado como adoção saudável sem validação de janela de assinatura.")
            usage_table = growth[
                [
                    "segment_value",
                    "raw_usage_direction",
                    "raw_usage_count_growth_pct",
                    "valid_usage_direction",
                    "valid_usage_count_growth_pct",
                    "latest_invalid_usage_event_share",
                    "interpretation",
                ]
            ].rename(
                columns={
                    "segment_value": "Segmento",
                    "raw_usage_direction": "Direção bruta",
                    "raw_usage_count_growth_pct": "Crescimento bruto",
                    "valid_usage_direction": "Direção válida",
                    "valid_usage_count_growth_pct": "Crescimento válido",
                    "latest_invalid_usage_event_share": "Share inválido recente",
                    "interpretation": "Interpretação",
                }
            )
            st.dataframe(
                usage_table,
                column_config={
                    "Crescimento bruto": st.column_config.NumberColumn("Crescimento bruto", format="%.1f%%"),
                    "Crescimento válido": st.column_config.NumberColumn("Crescimento válido", format="%.1f%%"),
                    "Share inválido recente": st.column_config.NumberColumn("Share inválido recente", format="%.2f"),
                },
                width="stretch",
                hide_index=True,
            )
    else:
        st.info("O arquivo opcional usage_growth_tests.csv não está presente. O risco por segmento ainda usa os exports canônicos.")


def operational_action(row: pd.Series) -> str:
    due = as_text(row.get("due_bucket"))
    risk = as_text(row.get("risk_segment"))
    driver = as_text(row.get("primary_risk_driver")).lower()
    reason = as_text(row.get("latest_reason_code")).lower()
    urgent = int(as_number(row.get("high_urgent_ticket_count")))
    churn_events = int(as_number(row.get("churn_event_count")))
    valid_usage = as_number(row.get("valid_usage_share"), default=float("nan"))
    mrr = money(row.get("mrr_at_risk"), compact=True)

    if due == "0-7 days" or risk == "Critical":
        return f"Ligar hoje: {churn_events} eventos de churn, {urgent} tickets urgentes/altos e {mrr} de MRR."
    if "support" in driver:
        return f"Abrir fila de suporte: {urgent} tickets urgentes/altos antes da renovação."
    if "product" in driver or reason == "features":
        usage = rate(valid_usage) if not pd.isna(valid_usage) else "unknown"
        return f"Oferecer treinamento: uso válido em {usage} e sinal de aderência de features."
    if "revenue" in driver or reason in {"pricing", "budget"}:
        return f"Revisar renovação: proteger {mrr} de MRR com prova de valor antes de desconto."
    if "churn history" in driver:
        return "Conduzir save playbook: use histórico de churn e motivo mais recente como roteiro da ligação."
    return "Revisar sinais da conta e confirmar a próxima ação com o dono indicado."


def filtered_priority_accounts(priority_accounts: pd.DataFrame) -> pd.DataFrame:
    ensure_cs_filter_state(priority_accounts)
    section_intro(
        "Mesa de operações CS",
        "A pergunta operacional é: para quem ligar hoje e o que falar.",
        "A fila abre focada no que exige resposta agora; ajustes avançados ficam recolhidos.",
    )
    with st.expander("Ajustar filtros", expanded=False):
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        risk_filter = c1.multiselect(
            "Risco",
            [risk for risk in RISK_ORDER if risk in priority_accounts["risk_segment"].tolist()],
            key="cs_risk_filter",
            format_func=pt,
        )
        plan_filter = c2.multiselect("Tier/Plano", sorted_values(priority_accounts, "plan_tier"), key="cs_plan_filter", format_func=pt)
        reason_filter = c3.multiselect("Sinal", sorted_values(priority_accounts, "primary_risk_driver"), key="cs_reason_filter", format_func=pt)
        due_filter = c4.multiselect("Prazo", sorted_values(priority_accounts, "due_bucket"), key="cs_due_filter", format_func=pt)
        c5, c6, c7, c8 = st.columns([1, 1, 1, 2])
        owner_filter = c5.multiselect("Dono", sorted_values(priority_accounts, "action_owner"), key="cs_owner_filter", format_func=pt)
        churn_reason_filter = c6.multiselect("Churn", sorted_values(priority_accounts, "latest_reason_code"), key="cs_churn_reason_filter", format_func=pt)
        min_mrr = c7.number_input("MRR mínimo", min_value=0, step=5000, key="cs_min_mrr", help="Valor mínimo para aparecer na fila.")
        search = c8.text_input("Buscar", key="cs_search", placeholder="Nome ou account_id")

    filtered = priority_accounts.copy()
    if risk_filter:
        filtered = filtered[filtered["risk_segment"].isin(risk_filter)]
    if plan_filter:
        filtered = filtered[filtered["plan_tier"].isin(plan_filter)]
    if reason_filter:
        filtered = filtered[filtered["primary_risk_driver"].isin(reason_filter)]
    if due_filter:
        filtered = filtered[filtered["due_bucket"].isin(due_filter)]
    if owner_filter:
        filtered = filtered[filtered["action_owner"].isin(owner_filter)]
    if churn_reason_filter:
        filtered = filtered[filtered["latest_reason_code"].isin(churn_reason_filter)]
    filtered = filtered[filtered["mrr_at_risk"].ge(min_mrr)]
    if search.strip():
        needle = search.strip().lower()
        mask = (
            filtered["account_id"].str.lower().str.contains(needle, na=False)
            | filtered["account_name"].str.lower().str.contains(needle, na=False)
        )
        filtered = filtered[mask]
    active_filters = []
    if risk_filter:
        active_filters.append(f"Risco: {', '.join(pt(value) for value in risk_filter)}")
    if due_filter:
        active_filters.append(f"Prazo: {', '.join(pt(value) for value in due_filter)}")
    if owner_filter:
        active_filters.append(f"Dono: {', '.join(pt(value) for value in owner_filter)}")
    if reason_filter:
        active_filters.append(f"Sinal: {', '.join(pt(value) for value in reason_filter)}")
    if churn_reason_filter:
        active_filters.append(f"Churn: {', '.join(pt(value) for value in churn_reason_filter)}")
    if min_mrr:
        active_filters.append(f"MRR mínimo: {money(min_mrr)}")
    if search.strip():
        active_filters.append(f"Busca: {search.strip()}")
    filter_summary = " | ".join(active_filters) if active_filters else "Todos os filtros limpos."
    emit_html(
        f"""
        <div class="g4-filter-summary">
          <span>Fila atual</span>
          <strong>{len(filtered)} contas nos filtros</strong>
          <p>{safe(filter_summary)}</p>
        </div>
        """
    )
    return filtered


def render_zero_state(message: str, detail: str) -> None:
    emit_html(
        f"""
        <div class="g4-zero-state">
          <h3>{safe(message)}</h3>
          <p>{safe(detail)}</p>
        </div>
        """
    )


def render_priority_accounts(priority_accounts: pd.DataFrame, account_health: pd.DataFrame) -> None:
    filtered = filtered_priority_accounts(priority_accounts)
    if filtered.empty:
        render_zero_state(
            "Zero contas em risco crítico hoje",
            "Nenhuma conta atende aos filtros atuais. Remova filtros ou registre que a fila crítica foi resolvida.",
        )
        return

    display = filtered.copy()
    display["next_best_action_today"] = display.apply(operational_action, axis=1)
    render_horizontal_bars(
        "Top contas por MRR em risco",
        priority_account_bar_rows(display),
    )

    summary_col, download_col = st.columns([2.2, 1])
    with summary_col:
        st.caption(
            f"{len(display)} contas nos filtros atuais. Os cards exibem as 9 primeiras por prioridade."
        )
    with download_col:
        render_download_button(
            "Baixar watchlist filtrada",
            display,
            "watchlist_contas_prioritarias_filtrada.csv",
            "download_priority_accounts_filtered",
        )

    st.markdown("#### Contas prioritárias")
    card_rows = display.head(9).reset_index(drop=True)
    cards_html = ['<div class="g4-account-grid">']
    for _, row in card_rows.iterrows():
        risk = as_text(row["risk_segment"])
        risk_class = f"g4-account-card--{risk.lower().replace(' ', '-')}"
        cards_html.append(
            f"""
            <article class="g4-account-card {safe(risk_class)}">
              <div class="g4-account-card-header">
                <div class="g4-account-title">
                  <span class="g4-account-rank">#{int(as_number(row['priority_rank']))} | {safe(row['account_id'])}</span>
                  <strong class="g4-account-name">{safe(row['account_name'])}</strong>
                </div>
                <span class="g4-account-risk">{safe_pt(risk)}</span>
              </div>
              <div class="g4-account-metrics">
                <div class="g4-account-metric"><span>MRR em risco</span><strong>{money(row['mrr_at_risk'], compact=True)}</strong></div>
                <div class="g4-account-metric"><span>Score</span><strong>{as_number(row['account_health_score']):.0f}</strong></div>
                <div class="g4-account-metric"><span>Tickets</span><strong>{int(as_number(row['high_urgent_ticket_count']))} urg.</strong></div>
              </div>
              <p class="g4-account-action"><strong>Próxima ação:</strong> {safe(row['next_best_action_today'])}</p>
              <div class="g4-account-footer">
                <span class="g4-pill">{safe(row['plan_tier'])}</span>
                <span class="g4-pill">{safe_pt(row['primary_risk_driver'])}</span>
                <span class="g4-pill">{safe_pt(row['due_bucket'])}</span>
                <span class="g4-pill">{safe_pt(row['action_owner'])}</span>
              </div>
            </article>
            """
        )
    cards_html.append("</div>")
    emit_html("".join(cards_html))

    with st.expander("Detalhe técnico da watchlist", expanded=False):
        st.dataframe(
            display[
                [
                    "priority_rank",
                    "account_id",
                    "account_name",
                    "plan_tier",
                    "mrr_at_risk",
                    "risk_segment",
                    "account_health_score",
                    "primary_risk_driver",
                    "latest_reason_code",
                    "high_urgent_ticket_count",
                    "next_best_action_today",
                    "action_owner",
                    "due_bucket",
                ]
            ].head(50),
            column_config={
                "priority_rank": st.column_config.NumberColumn("Rank", format="%d"),
                "mrr_at_risk": st.column_config.NumberColumn("MRR", format="US$ %.0f"),
                "account_health_score": st.column_config.ProgressColumn("Score de risco", min_value=0, max_value=100),
                "high_urgent_ticket_count": st.column_config.NumberColumn("Tickets urgentes", format="%d"),
                "next_best_action_today": st.column_config.TextColumn("Próxima ação"),
            },
            width="stretch",
            hide_index=True,
        )
    render_account_drilldown(display, account_health)


def render_account_drilldown(priority_accounts: pd.DataFrame, account_health: pd.DataFrame) -> None:
    labels = [
        f"#{int(row.priority_rank)} {row.account_name} ({row.account_id}) - {money(row.mrr_at_risk, compact=True)} MRR"
        for row in priority_accounts.head(25).itertuples()
    ]
    selected_label = st.selectbox("Drill-down da conta", labels, index=0)
    selected_id = selected_label.split("(")[-1].split(")")[0]
    row = priority_accounts[priority_accounts["account_id"].eq(selected_id)].iloc[0]
    health_match = account_health[account_health["account_id"].eq(selected_id)]
    health = health_match.iloc[0] if not health_match.empty else row

    emit_html(
        f"""
        <div class="g4-panel">
          <strong>{safe(row['account_name'])} | {safe(row['account_id'])}</strong>
          <p>{safe(operational_action(row))}</p>
          <div class="g4-meta-row">
            <span class="g4-pill g4-pill-{safe(row['risk_segment']).lower()}">{safe_pt(row['risk_segment'])}</span>
            <span class="g4-pill">{money(row['mrr_at_risk'])} MRR</span>
            <span class="g4-pill">{safe(row['plan_tier'])}</span>
            <span class="g4-pill">{safe_pt(row['action_owner'])}</span>
          </div>
        </div>
        <div class="g4-timeline">
          <div><span>Signup</span><strong>{safe(health.get('signup_date'))}</strong></div>
          <div><span>Assinatura</span><strong>{safe(health.get('latest_plan_tier', row.get('plan_tier')))} | {money(health.get('current_mrr', row.get('mrr_at_risk')), compact=True)} MRR</strong></div>
          <div><span>Suporte</span><strong>{int(as_number(health.get('high_urgent_ticket_count', row.get('high_urgent_ticket_count'))))} urgentes/altos | {int(as_number(health.get('escalated_ticket_count', row.get('escalated_ticket_count'))))} escalados</strong></div>
          <div><span>Uso</span><strong>{rate(health.get('valid_usage_share', row.get('valid_usage_share')))} em janela válida | {as_number(health.get('error_rate_per_100_valid_events', row.get('error_rate_per_100_valid_events'))):.1f} erros/100</strong></div>
          <div><span>Sinal de churn</span><strong>{safe_pt(row.get('latest_reason_code'))} | {safe(row.get('latest_churn_date'))}</strong></div>
        </div>
        """
    )


def render_action_backlog(action_backlog: pd.DataFrame) -> None:
    section_intro(
        "Backlog de ação",
        "O trabalho já está separado por dono; a UI deve mostrar impacto, urgência e status.",
        "MRR em backlog representa exposição associada ao item, não soma causal garantida.",
    )
    render_stacked_owner_bars("Backlog por dono e prioridade", action_backlog)
    owner_options = ["All"] + sorted(action_backlog["owner_team"].dropna().unique().tolist())
    priority_options = ["All"] + ["Critical", "High", "Medium", "Low"]
    c1, c2 = st.columns([1, 1])
    selected_owner = c1.selectbox("Dono", owner_options, key="owner_filter", format_func=pt)
    selected_priority = c2.selectbox("Prioridade", priority_options, key="priority_filter", format_func=pt)
    filtered = action_backlog.copy()
    if selected_owner != "All":
        filtered = filtered[filtered["owner_team"].eq(selected_owner)]
    if selected_priority != "All":
        filtered = filtered[filtered["priority"].eq(selected_priority)]

    if filtered.empty:
        render_zero_state(
            "Zero ações abertas para este filtro",
            "Use Todos para revisar o backlog completo ou registre que o dono selecionado está limpo.",
        )
        return

    cards = filtered.head(8)
    cards_html = ['<div class="g4-action-grid">']
    for _, row in cards.iterrows():
        hot = "g4-action-card--hot" if as_text(row["priority"]) in {"Critical", "High"} else ""
        cards_html.append(
            f"""
            <div class="g4-action-card {hot}">
              <strong>{safe(backlog_action_pt(row))}</strong>
              <p>{safe(backlog_evidence_pt(row))}</p>
              <div class="g4-meta-row">
                <span class="g4-pill">{safe_pt(row['owner_team'])}</span>
                <span class="g4-pill">{safe_pt(row['priority'])}</span>
                <span class="g4-pill">{safe_pt(row['due_bucket'])}</span>
                <span class="g4-pill">{money(row['mrr_at_risk'], compact=True)} MRR</span>
              </div>
            </div>
            """
        )
    cards_html.append("</div>")
    emit_html("".join(cards_html))

    with st.expander("Detalhe técnico do backlog", expanded=False):
        backlog_table = filtered[
            [
                "action_id",
                "scope_type",
                "action_theme",
                "owner_team",
                "priority",
                "due_bucket",
                "status",
                "recommended_action",
                "trigger_metric",
                "trigger_value",
                "confidence_level",
                "mrr_at_risk",
                "account_count_impacted",
                "effort_size",
                "expected_impact_metric",
            ]
        ].rename(
            columns={
                "action_id": "Ação",
                "scope_type": "Escopo",
                "action_theme": "Tema",
                "owner_team": "Dono",
                "priority": "Prioridade",
                "due_bucket": "Prazo",
                "status": "Status",
                "recommended_action": "Ação recomendada",
                "trigger_metric": "Métrica gatilho",
                "trigger_value": "Valor gatilho",
                "confidence_level": "Confiança",
                "mrr_at_risk": "MRR",
                "account_count_impacted": "Contas",
                "effort_size": "Esforço",
                "expected_impact_metric": "Impacto esperado",
            }
        )
        st.dataframe(
            backlog_table,
            column_config={
                "MRR": st.column_config.NumberColumn("MRR", format="US$ %.0f"),
                "Contas": st.column_config.NumberColumn("Contas", format="%d"),
            },
            width="stretch",
            hide_index=True,
        )


def render_csv_downloads(exports: dict[str, pd.DataFrame]) -> None:
    section_intro(
        "Downloads dos CSVs",
        "Baixe exatamente as tabelas utilizadas pelo dashboard.",
        "Os arquivos vêm de solution/exports/. A UI não acessa dados brutos nem recalcula regras de negócio.",
    )
    ordered_names = [
        name for name in [*REQUIRED_EXPORTS.keys(), *OPTIONAL_EXPORTS.keys()] if name in exports
    ]
    columns = st.columns(3)
    for index, name in enumerate(ordered_names):
        df = exports[name]
        row_count = f"{len(df):,}".replace(",", ".")
        column_count = f"{len(df.columns):,}".replace(",", ".")
        with columns[index % len(columns)]:
            st.caption(f"{EXPORT_LABELS.get(name, name)} | {row_count} linhas | {column_count} colunas")
            render_download_button(
                f"Baixar {export_file_name(name)}",
                df,
                export_file_name(name),
                f"download_export_{name}",
            )


def render_data_quality(exports: dict[str, pd.DataFrame]) -> None:
    section_intro(
        "Confiança",
        "As caveats que impedem conclusões enganosas ficam visíveis na própria entrega.",
        "Isto protege o CEO e o time de CS de tratar correlação e conflito de labels como verdade causal.",
    )
    emit_html(
        """
        <div class="g4-note">
          <ul>
            <li><code>usage_id</code> não é único; a camada analítica gera <code>feature_usage_row_id</code>.</li>
            <li>Uso fora da janela de assinatura é excluído das métricas de uso válido.</li>
            <li><code>account_churn_flag</code> e <code>has_churn_event</code> são labels separados.</li>
            <li>Respostas ausentes de satisfação são tratadas como ausência, não como satisfação zero.</li>
          </ul>
          <p>Relatório completo: <code>solution/analysis/data_quality_report.md</code></p>
        </div>
        """
    )
    render_csv_downloads(exports)


def main() -> None:
    st.set_page_config(
        page_title="RavenStack Churn Diagnosis",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()
    try:
        exports = load_exports()
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()

    render_header(exports)
    render_kpis(exports)
    render_workspace_status(exports)
    render_action_buttons(exports["priority_accounts"])
    render_findings(exports["executive_findings"])
    render_root_cause(exports)

    segments, accounts, backlog, quality = st.tabs(
        ["Segmentos", "Mesa CS", "Backlog", "Confiança"]
    )
    with segments:
        render_risk_segments(exports["risk_segments"], exports.get("usage_growth_tests"))
    with accounts:
        render_priority_accounts(exports["priority_accounts"], exports["account_health"])
    with backlog:
        render_action_backlog(exports["action_backlog"])
    with quality:
        render_data_quality(exports)


if __name__ == "__main__":
    main()
