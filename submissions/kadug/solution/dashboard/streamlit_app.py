from __future__ import annotations

import html
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except ModuleNotFoundError:  # pragma: no cover - dashboard still renders tables.
    go = None


APP_DIR = Path(__file__).resolve().parent
SOLUTION_DIR = APP_DIR.parent
EXPORTS_DIR = SOLUTION_DIR / "exports"
THEME_PATH = SOLUTION_DIR.parent / "docs" / "design-system" / "g4" / "streamlit-theme.css"

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

RISK_ORDER = ["Critical", "High", "Medium", "Low"]
RISK_COLORS = {
    "Critical": "#842E20",
    "High": "#B9915B",
    "Medium": "#706F6F",
    "Low": "#001F35",
}
G4_INK = "#031A26"
G4_RUST = "#842E20"
G4_BORDER = "#D6D5D5"
G4_MUTED = "#706F6F"


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


@st.cache_data(show_spinner=False)
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
    if THEME_PATH.exists():
        css = THEME_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    st.markdown(
        """
        <style>
        .block-container { max-width: 1220px; padding-top: 22px; padding-bottom: 48px; }
        [data-testid="stVerticalBlock"] { gap: 0.85rem; }
        .g4-executive-header { margin-top: -8px; padding: 30px 34px; }
        .g4-eyebrow {
          margin: 0 0 8px 0;
          color: #B9915B;
          font-size: 13px;
          font-weight: 800;
          text-transform: uppercase;
        }
        .g4-executive-header h1 { font-size: 34px; line-height: 1.12; margin: 0 0 10px 0; }
        .g4-governing-thought {
          max-width: 900px;
          color: #F5F4F3;
          font-size: 18px;
          line-height: 1.48;
          margin: 0 0 18px 0;
        }
        .g4-chipline { display: flex; flex-wrap: wrap; gap: 8px; }
        .g4-chip {
          min-height: 30px;
          border-color: rgba(185, 145, 91, 0.72);
          background: rgba(255, 255, 255, 0.06);
        }
        .g4-chip-risk { background: rgba(132, 46, 32, 0.10); }
        .g4-section-kicker { color: #B9915B; font-size: 12px; font-weight: 800; text-transform: uppercase; margin: 20px 0 4px; }
        .g4-section-title { color: #031A26; font-size: 22px; font-weight: 800; line-height: 1.2; margin: 0 0 8px; }
        .g4-section-copy { color: #706F6F; font-size: 14px; line-height: 1.5; margin: 0 0 14px; }
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
        .g4-finding {
          border-left: 4px solid #B9915B;
          margin-bottom: 12px;
        }
        .g4-finding strong,
        .g4-action-card strong,
        .g4-panel strong { color: #031A26; }
        .g4-finding p,
        .g4-action-card p,
        .g4-panel p { color: #706F6F; margin: 6px 0 0; line-height: 1.45; }
        .g4-meta-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
        .g4-pill {
          display: inline-flex;
          align-items: center;
          min-height: 28px;
          border-radius: 999px;
          padding: 3px 9px;
          font-size: 12px;
          font-weight: 800;
          background: #F5F4F3;
          color: #031A26;
          border: 1px solid #D6D5D5;
        }
        .g4-pill-critical { color: #842E20; border-color: rgba(132, 46, 32, 0.35); background: rgba(132, 46, 32, 0.08); }
        .g4-pill-high { color: #031A26; border-color: rgba(185, 145, 91, 0.52); background: rgba(185, 145, 91, 0.13); }
        .g4-action-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
          margin-top: 10px;
        }
        .g4-action-card { min-height: 150px; border-top: 3px solid #B9915B; }
        .g4-action-card--hot { border-top-color: #842E20; }
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
        div[data-baseweb="tab-list"] { gap: 8px; }
        button[data-baseweb="tab"] {
          border: 1px solid #D6D5D5;
          border-radius: 8px;
          background: #FFFFFF;
          min-height: 42px;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
          border-color: #B9915B;
          color: #001F35;
        }
        [data-testid="stDataFrame"] { font-size: 13px; }
        @media (max-width: 900px) {
          .g4-kpi-grid, .g4-action-grid { grid-template-columns: 1fr; }
          .g4-timeline { grid-template-columns: 1fr 1fr; }
          .g4-executive-header h1 { font-size: 28px; }
        }
        @media (max-width: 560px) {
          .block-container { padding-left: 14px; padding-right: 14px; }
          .g4-executive-header { padding: 22px 18px; }
          .g4-kpi-value { font-size: 24px; }
          .g4-timeline { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def critical_high_summary(risk_segments: pd.DataFrame) -> tuple[int, float, float]:
    focused = risk_segments[risk_segments["risk_segment"].isin(["Critical", "High"])]
    accounts = int(focused["account_count"].sum())
    mrr = float(focused["mrr_at_risk"].sum())
    arr = float(focused["current_arr"].sum())
    return accounts, mrr, arr


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


def render_header(exports: dict[str, pd.DataFrame]) -> None:
    accounts, mrr, _arr = critical_high_summary(exports["risk_segments"])
    top_cause = root_cause_frame(exports).iloc[0]
    st.markdown(
        f"""
        <section class="g4-executive-header">
          <p class="g4-eyebrow">Canonical exports only | CEO + CS operating view</p>
          <h1>RavenStack Churn Diagnosis</h1>
          <p class="g4-governing-thought">{money(mrr, compact=True)} MRR is exposed in {accounts} Critical/High accounts. The working root-cause candidate is <strong>{safe(top_cause['root_cause_candidate'])}</strong>, so the first move is a two-week save motion, not another broad analysis pass.</p>
          <div class="g4-chipline">
            <span class="g4-chip">valid-window usage</span>
            <span class="g4-chip">separate churn labels</span>
            <span class="g4-chip">account watchlist</span>
            <span class="g4-chip g4-chip-risk">observational, not causal proof</span>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(exports: dict[str, pd.DataFrame]) -> None:
    risk = exports["risk_segments"]
    priority = exports["priority_accounts"]
    account_health = exports["account_health"]
    focused_accounts, mrr_at_risk, arr_at_risk = critical_high_summary(risk)
    event_rate, flag_rate = churn_label_rates(account_health)
    top10 = priority.head(10)
    top10_mrr = top10["mrr_at_risk"].sum()
    top10_arr = top10["current_arr"].sum()

    st.markdown(
        f"""
        <section class="g4-kpi-grid">
          <div class="g4-kpi g4-kpi--risk">
            <div class="g4-kpi-label">ARR/MRR em risco</div>
            <div class="g4-kpi-value">{money(mrr_at_risk)}</div>
            <div class="g4-kpi-note">{money(arr_at_risk, compact=True)} ARR in Critical/High segments; {focused_accounts} accounts need an owner-backed save motion.</div>
          </div>
          <div class="g4-kpi">
            <div class="g4-kpi-label">Churn atual vs. meta</div>
            <div class="g4-kpi-value">{rate(event_rate)} / {rate(flag_rate)}</div>
            <div class="g4-kpi-note">Event history vs. account flag. External benchmark/meta is not exported, so this is a governance gap to close.</div>
          </div>
          <div class="g4-kpi g4-kpi--risk">
            <div class="g4-kpi-label">Top 10 contas criticas</div>
            <div class="g4-kpi-value">{money(top10_mrr)}</div>
            <div class="g4-kpi-note">{money(top10_arr, compact=True)} ARR in the first ten ranked accounts. Start here before broad portfolio campaigns.</div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def section_intro(kicker: str, title: str, copy: str = "") -> None:
    st.markdown(
        f"""
        <p class="g4-section-kicker">{safe(kicker)}</p>
        <h2 class="g4-section-title">{safe(title)}</h2>
        {f'<p class="g4-section-copy">{safe(copy)}</p>' if copy else ''}
        """,
        unsafe_allow_html=True,
    )


def render_findings(findings: pd.DataFrame) -> None:
    section_intro(
        "Resumo executivo",
        "Salvar contas nomeadas tem mais valor agora do que abrir outro diagnostico.",
        "Cada bloco abaixo segue sinal, evidencia, acao e dono para o CEO decidir em menos de 60 segundos.",
    )
    for _, row in findings.head(3).iterrows():
        st.markdown(
            f"""
            <div class="g4-finding">
              <strong>{safe(row['finding_id'])} - {safe(row['finding_title'])}</strong>
              <p><strong>Sinal:</strong> {safe(row['plain_language_finding'])}</p>
              <p><strong>Evidencia:</strong> {safe(row['evidence_summary'])}</p>
              <p><strong>Acao:</strong> {safe(row['recommended_action'])}</p>
              <div class="g4-meta-row">
                <span class="g4-pill">{safe(row['owner_team'])}</span>
                <span class="g4-pill">{safe(row['confidence_level'])} confidence</span>
                <span class="g4-pill">{money(row['mrr_at_risk'], compact=True)} MRR exposed</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_plotly_or_table(fig: Any, data: pd.DataFrame) -> None:
    if go is None or fig is None:
        st.dataframe(data, use_container_width=True, hide_index=True)
    else:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def cause_chart(root_causes: pd.DataFrame) -> Any:
    if go is None or root_causes.empty:
        return None
    chart_rows = root_causes.head(6).sort_values("mrr_at_risk", ascending=True)
    labels = chart_rows["root_cause_candidate"].map(as_text).tolist()
    colors = [
        G4_RUST if rank == 1 else G4_GOLD if rank in (2, 3) else G4_MUTED
        for rank in chart_rows.get("rank", pd.Series(range(1, len(chart_rows) + 1))).tolist()
    ]
    fig = go.Figure(
        data=[
            go.Bar(
                x=chart_rows["mrr_at_risk"],
                y=labels,
                orientation="h",
                marker_color=colors,
                customdata=chart_rows[["affected_accounts", "confidence_level"]].values,
                hovertemplate=(
                    "<b>%{y}</b><br>MRR exposed: US$ %{x:,.0f}"
                    "<br>Accounts: %{customdata[0]}"
                    "<br>Confidence: %{customdata[1]}<extra></extra>"
                ),
            )
        ]
    )
    fig.update_layout(
        height=360,
        margin={"l": 8, "r": 8, "t": 22, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Manrope, sans-serif", "color": G4_INK},
        xaxis={"title": "MRR exposed", "gridcolor": G4_BORDER},
        yaxis={"title": ""},
    )
    return fig


def segment_chart(risk_segments: pd.DataFrame) -> Any:
    if go is None or risk_segments.empty:
        return None
    ordered = risk_segments.set_index("risk_segment").reindex(RISK_ORDER).dropna(how="all").reset_index()
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=ordered["risk_segment"],
            y=ordered["mrr_at_risk"],
            marker_color=[RISK_COLORS.get(as_text(value), G4_MUTED) for value in ordered["risk_segment"]],
            customdata=ordered[["account_count", "top_churn_reason", "recommended_playbook"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>MRR at risk: US$ %{y:,.0f}"
                "<br>Accounts: %{customdata[0]}"
                "<br>Top reason: %{customdata[1]}"
                "<br>Playbook: %{customdata[2]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        height=320,
        margin={"l": 8, "r": 8, "t": 22, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Manrope, sans-serif", "color": G4_INK},
        yaxis={"title": "MRR at risk", "gridcolor": G4_BORDER},
        xaxis={"title": ""},
    )
    return fig


def render_root_cause(exports: dict[str, pd.DataFrame]) -> None:
    root_causes = root_cause_frame(exports)
    section_intro(
        "Causa raiz e impacto",
        "A hipotese mais cara e erosao de valor antes da renovacao; suporte e produto explicam onde investigar primeiro.",
        "As barras usam exports ja gerados. Valores de causa podem se sobrepor; a decisao correta e validar em account reviews.",
    )
    left, right = st.columns([1.45, 1])
    with left:
        render_plotly_or_table(cause_chart(root_causes), root_causes.head(6))
    with right:
        cards_html = ['<div class="g4-action-grid">']
        for _, row in root_causes.head(4).iterrows():
            hot = "g4-action-card--hot" if as_number(row.get("rank"), 9) <= 2 else ""
            cards_html.append(
                f"""
                <div class="g4-action-card {hot}">
                  <strong>{safe(row['root_cause_candidate'])}</strong>
                  <p>{safe(row['evidence_summary'])}</p>
                  <div class="g4-meta-row">
                    <span class="g4-pill">{money(row['mrr_at_risk'], compact=True)} MRR</span>
                    <span class="g4-pill">{int(as_number(row['affected_accounts']))} accounts</span>
                    <span class="g4-pill">{safe(row['owner_team'])}</span>
                  </div>
                </div>
                """
            )
        cards_html.append("</div>")
        st.markdown("".join(cards_html), unsafe_allow_html=True)


def render_risk_segments(
    risk_segments: pd.DataFrame, usage_growth: pd.DataFrame | None
) -> None:
    accounts, mrr, arr = critical_high_summary(risk_segments)
    section_intro(
        "Segmentos",
        f"Critical+High concentram {money(mrr, compact=True)} MRR em {accounts} contas; Medium vira fila de monitoramento.",
        f"ARR exposto nestes dois segmentos: {money(arr, compact=True)}.",
    )
    render_plotly_or_table(segment_chart(risk_segments), risk_segments)

    selected_segment = st.selectbox(
        "Segment",
        [segment for segment in RISK_ORDER if segment in risk_segments["risk_segment"].tolist()],
        index=0,
        key="risk_segment_select",
    )
    segment = risk_segments[risk_segments["risk_segment"].eq(selected_segment)].iloc[0]
    left, right = st.columns([1.3, 1])
    with left:
        st.dataframe(
            risk_segments[
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
            ],
            column_config={
                "mrr_at_risk": st.column_config.NumberColumn("MRR at risk", format="US$ %.0f"),
                "current_arr": st.column_config.NumberColumn("ARR", format="US$ %.0f"),
                "event_based_churn_rate": st.column_config.NumberColumn("Event churn", format="%.2f"),
                "account_flag_churn_rate": st.column_config.NumberColumn("Flag churn", format="%.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )
    with right:
        st.markdown(
            f"""
            <div class="g4-note">
              <strong>{safe(selected_segment)} segment</strong>
              <p>Accounts: {int(segment['account_count'])}</p>
              <p>MRR at risk: {money(segment['mrr_at_risk'])}</p>
              <p>ARR at risk: {money(segment['current_arr'])}</p>
              <p>Top reason: {safe(segment['top_churn_reason'])}</p>
              <p>Playbook: {safe(segment['recommended_playbook'])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if usage_growth is not None:
        growth = usage_growth[usage_growth["segment_type"].eq("risk_segment")]
        st.caption("Usage growth is shown from 2024-H1 to 2024-H2. Raw growth is not treated as healthy adoption without valid-window checks.")
        st.dataframe(
            growth[
                [
                    "segment_value",
                    "raw_usage_direction",
                    "raw_usage_count_growth_pct",
                    "valid_usage_direction",
                    "valid_usage_count_growth_pct",
                    "latest_invalid_usage_event_share",
                    "interpretation",
                ]
            ],
            column_config={
                "raw_usage_count_growth_pct": st.column_config.NumberColumn("Raw growth", format="%.1f%%"),
                "valid_usage_count_growth_pct": st.column_config.NumberColumn("Valid growth", format="%.1f%%"),
                "latest_invalid_usage_event_share": st.column_config.NumberColumn("Invalid latest share", format="%.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Optional usage_growth_tests.csv is not present. Segment risk still uses canonical exports.")


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
        return f"Ligar hoje - {churn_events} churn events, {urgent} high/urgent tickets, {mrr} MRR."
    if "support" in driver:
        return f"Abrir fila suporte - {urgent} high/urgent tickets antes da renovacao."
    if "product" in driver or reason == "features":
        usage = rate(valid_usage) if not pd.isna(valid_usage) else "unknown"
        return f"Oferecer treinamento - valid usage share {usage} and feature-fit signal."
    if "revenue" in driver or reason in {"pricing", "budget"}:
        return f"Revisar renovacao - protect {mrr} MRR with value proof before discount."
    return as_text(row.get("next_best_action"))


def filtered_priority_accounts(priority_accounts: pd.DataFrame) -> pd.DataFrame:
    section_intro(
        "Mesa de operacoes CS",
        "A pergunta operacional e: para quem ligar hoje e o que falar.",
        "Filtros aparecem somente nesta etapa para manter a primeira tela executiva limpa.",
    )
    with st.expander("Filtros operacionais", expanded=True):
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        risk_filter = c1.multiselect(
            "Risk",
            [risk for risk in RISK_ORDER if risk in priority_accounts["risk_segment"].tolist()],
            default=[risk for risk in ["Critical", "High"] if risk in priority_accounts["risk_segment"].tolist()],
        )
        plan_filter = c2.multiselect("Tier/Plano", sorted_values(priority_accounts, "plan_tier"))
        reason_filter = c3.multiselect("Motivo de risco", sorted_values(priority_accounts, "primary_risk_driver"))
        due_filter = c4.multiselect("Due bucket", sorted_values(priority_accounts, "due_bucket"))
        c5, c6, c7 = st.columns([1, 1, 2])
        owner_filter = c5.multiselect("Owner", sorted_values(priority_accounts, "action_owner"))
        min_mrr = c6.number_input("Minimum MRR", min_value=0, value=0, step=5000)
        search = c7.text_input("Buscar conta ou account_id", value="")

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
    filtered = filtered[filtered["mrr_at_risk"].ge(min_mrr)]
    if search.strip():
        needle = search.strip().lower()
        mask = (
            filtered["account_id"].str.lower().str.contains(needle, na=False)
            | filtered["account_name"].str.lower().str.contains(needle, na=False)
        )
        filtered = filtered[mask]
    return filtered


def render_zero_state(message: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="g4-zero-state">
          <h3>{safe(message)}</h3>
          <p>{safe(detail)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_priority_accounts(priority_accounts: pd.DataFrame, account_health: pd.DataFrame) -> None:
    filtered = filtered_priority_accounts(priority_accounts)
    if filtered.empty:
        render_zero_state(
            "Zero contas em risco critico hoje",
            "Nenhuma conta atende aos filtros atuais. Remova filtros ou registre que a fila critica foi resolvida.",
        )
        return

    display = filtered.copy()
    display["next_best_action_today"] = display.apply(operational_action, axis=1)
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
            "account_health_score": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=100),
            "high_urgent_ticket_count": st.column_config.NumberColumn("Urgent tickets", format="%d"),
            "next_best_action_today": st.column_config.TextColumn("Next Best Action"),
        },
        use_container_width=True,
        hide_index=True,
    )
    render_account_drilldown(display, account_health)


def render_account_drilldown(priority_accounts: pd.DataFrame, account_health: pd.DataFrame) -> None:
    labels = [
        f"#{int(row.priority_rank)} {row.account_name} ({row.account_id}) - {money(row.mrr_at_risk, compact=True)} MRR"
        for row in priority_accounts.head(25).itertuples()
    ]
    selected_label = st.selectbox("Account drill-down", labels, index=0)
    selected_id = selected_label.split("(")[-1].split(")")[0]
    row = priority_accounts[priority_accounts["account_id"].eq(selected_id)].iloc[0]
    health_match = account_health[account_health["account_id"].eq(selected_id)]
    health = health_match.iloc[0] if not health_match.empty else row

    st.markdown(
        f"""
        <div class="g4-panel">
          <strong>{safe(row['account_name'])} | {safe(row['account_id'])}</strong>
          <p>{safe(operational_action(row))}</p>
          <div class="g4-meta-row">
            <span class="g4-pill g4-pill-{safe(row['risk_segment']).lower()}">{safe(row['risk_segment'])}</span>
            <span class="g4-pill">{money(row['mrr_at_risk'])} MRR</span>
            <span class="g4-pill">{safe(row['plan_tier'])}</span>
            <span class="g4-pill">{safe(row['action_owner'])}</span>
          </div>
        </div>
        <div class="g4-timeline">
          <div><span>Signup</span><strong>{safe(health.get('signup_date'))}</strong></div>
          <div><span>Subscription</span><strong>{safe(health.get('latest_plan_tier', row.get('plan_tier')))} | {money(health.get('current_mrr', row.get('mrr_at_risk')), compact=True)} MRR</strong></div>
          <div><span>Support</span><strong>{int(as_number(health.get('high_urgent_ticket_count', row.get('high_urgent_ticket_count'))))} urgent/high | {int(as_number(health.get('escalated_ticket_count', row.get('escalated_ticket_count'))))} escalated</strong></div>
          <div><span>Usage</span><strong>{rate(health.get('valid_usage_share', row.get('valid_usage_share')))} valid window | {as_number(health.get('error_rate_per_100_valid_events', row.get('error_rate_per_100_valid_events'))):.1f} errors/100</strong></div>
          <div><span>Churn signal</span><strong>{safe(row.get('latest_reason_code'))} | {safe(row.get('latest_churn_date'))}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_action_backlog(action_backlog: pd.DataFrame) -> None:
    section_intro(
        "Backlog de acao",
        "O trabalho ja esta separado por dono; a UI deve mostrar impacto, urgencia e status.",
        "MRR em backlog representa exposicao associada ao item, nao soma causal garantida.",
    )
    owner_options = ["All"] + sorted(action_backlog["owner_team"].dropna().unique().tolist())
    priority_options = ["All"] + ["Critical", "High", "Medium", "Low"]
    c1, c2 = st.columns([1, 1])
    selected_owner = c1.selectbox("Owner team", owner_options, key="owner_filter")
    selected_priority = c2.selectbox("Priority", priority_options, key="priority_filter")
    filtered = action_backlog.copy()
    if selected_owner != "All":
        filtered = filtered[filtered["owner_team"].eq(selected_owner)]
    if selected_priority != "All":
        filtered = filtered[filtered["priority"].eq(selected_priority)]

    if filtered.empty:
        render_zero_state(
            "Zero acoes abertas para este filtro",
            "Use All para revisar o backlog completo ou registre que o owner selecionado esta limpo.",
        )
        return

    cards = filtered.head(8)
    cards_html = ['<div class="g4-action-grid">']
    for _, row in cards.iterrows():
        hot = "g4-action-card--hot" if as_text(row["priority"]) in {"Critical", "High"} else ""
        cards_html.append(
            f"""
            <div class="g4-action-card {hot}">
              <strong>{safe(row['recommended_action'])}</strong>
              <p>{safe(row['evidence_summary'])}</p>
              <div class="g4-meta-row">
                <span class="g4-pill">{safe(row['owner_team'])}</span>
                <span class="g4-pill">{safe(row['priority'])}</span>
                <span class="g4-pill">{safe(row['due_bucket'])}</span>
                <span class="g4-pill">{money(row['mrr_at_risk'], compact=True)} MRR</span>
              </div>
            </div>
            """
        )
    cards_html.append("</div>")
    st.markdown("".join(cards_html), unsafe_allow_html=True)

    st.markdown("#### Backlog table")
    st.dataframe(
        filtered[
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
        ],
        column_config={
            "mrr_at_risk": st.column_config.NumberColumn("MRR", format="US$ %.0f"),
            "account_count_impacted": st.column_config.NumberColumn("Accounts", format="%d"),
        },
        use_container_width=True,
        hide_index=True,
    )


def render_data_quality() -> None:
    section_intro(
        "Confianca",
        "As caveats que impedem conclusoes enganosas ficam visiveis na propria entrega.",
        "Isto protege o CEO e o time de CS de tratar correlacao e label conflict como verdade causal.",
    )
    st.markdown(
        """
        <div class="g4-note">
          <ul>
            <li><code>usage_id</code> is not unique; the analytics layer generates <code>feature_usage_row_id</code>.</li>
            <li>Feature usage outside subscription windows is excluded from valid usage metrics.</li>
            <li><code>account_churn_flag</code> and <code>has_churn_event</code> are separate labels.</li>
            <li>Missing satisfaction responses are tracked as missing, not zero satisfaction.</li>
          </ul>
          <p>Full report path: <code>solution/analysis/data_quality_report.md</code></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    render_findings(exports["executive_findings"])
    render_root_cause(exports)

    segments, accounts, backlog, quality = st.tabs(
        ["Segmentos", "Mesa CS", "Backlog", "Data Quality"]
    )
    with segments:
        render_risk_segments(exports["risk_segments"], exports.get("usage_growth_tests"))
    with accounts:
        render_priority_accounts(exports["priority_accounts"], exports["account_health"])
    with backlog:
        render_action_backlog(exports["action_backlog"])
    with quality:
        render_data_quality()


if __name__ == "__main__":
    main()
