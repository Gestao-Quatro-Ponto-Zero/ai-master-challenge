"""
DealSignal UI — Deal insight panel renderers.

All functions in this module write directly to the Streamlit layout.
They consume the signal payload produced by signals_builder.build_signals_for_deal().
"""

from typing import Optional

import pandas as pd
import streamlit as st

from app.ui.ai_insight import get_ai_insight
from app.ui.formatters import _engine_label, _rating_badge, format_currency
from app.ui.ui_constants import _ENGINE_LABELS_PT

# ── Shared style constants ─────────────────────────────────────────────────────
_CARD_OPEN = """
<div style='
    background:#f8f9fb;
    border:1px solid #e3e6ed;
    border-radius:12px;
    padding:14px 16px 12px 16px;
    box-shadow:0 1px 4px rgba(0,0,0,0.06);
    font-family:sans-serif;
'>
"""
_CARD_CLOSE = "</div>"

_LABEL_COLOR = {"🟢 Forte": "#2e7d32", "🟡 Moderado": "#f57c00", "🔴 Fraco": "#c62828"}
_LABEL_TEXT  = {"🟢 Forte": "Forte",   "🟡 Moderado": "Moderado", "🔴 Fraco": "Fraco"}
_HEALTH_COLOR = {"Saudável": "#2e7d32", "Atenção": "#f57c00", "Em risco": "#c62828"}
_PRIORITY_COLOR = {"Alta prioridade": "#c62828", "Média prioridade": "#f57c00", "Baixa prioridade": "#555"}


def _pill(text: str, color: str) -> str:
    return (
        f"<span style='font-size:12px;font-weight:600;color:white;"
        f"background:{color};padding:3px 10px;border-radius:10px;"
        f"white-space:nowrap;line-height:20px;'>{text}</span>"
    )


def render_deal_header(row: pd.Series) -> None:
    account        = row.get("account", "—")
    product        = row.get("product", "—")
    rating         = str(row.get("deal_rating", ""))
    priority_tier  = str(row.get("priority_tier", ""))
    priority_pill  = (
        _pill(priority_tier, _PRIORITY_COLOR.get(priority_tier, "#888"))
        if priority_tier and priority_tier != "nan" else ""
    )

    st.markdown(
        f"{_CARD_OPEN}"
        f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>"
        f"  {_rating_badge(rating)}"
        f"  <span style='font-weight:700;font-size:15px;color:#1a1a2e;line-height:1.3;'>{account}<br>"
        f"    <span style='font-weight:400;font-size:13px;color:#666;'>{product}</span>"
        f"  </span>"
        f"  <div style='margin-left:auto;text-align:right;'>"
        f"    {priority_pill}"
        f"  </div>"
        f"</div>"
        f"{_CARD_CLOSE}",
        unsafe_allow_html=True,
    )



def render_ai_insight_card(
    row: pd.Series,
    signal_payload: dict,
    df: Optional[pd.DataFrame] = None,
) -> dict:
    """Renders the AI insight card and returns the full result dict for downstream use."""
    prob      = float(row.get("win_probability", 0.0))
    pct       = round(prob * 100)
    pct_color = "#6ee7b7" if prob >= 0.65 else ("#fbbf24" if prob >= 0.40 else "#f87171")

    with st.spinner("Gerando análise..."):
        result = get_ai_insight(row, df if df is not None else pd.DataFrame(), signal_payload)

    insight_text   = result["insight_text"]
    friction_label = result["friction_label"]
    confidence     = result["confidence"]
    is_ai          = result["is_ai"]

    header_label = (
        "<span style='font-size:11px;font-weight:700;color:#a78bfa;text-transform:uppercase;"
        "letter-spacing:1px;'>✦ Análise por IA</span>"
        if is_ai else
        "<span style='font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;"
        "letter-spacing:1px;'>Análise por Regras</span>"
    )

    narrative_text = result.get("narrative_text", "")
    action_text    = result.get("action_text", "")

    # Extract only the "Leitura" section from the AI text (skip Observação)
    leitura = ""
    in_leitura = False
    for line in insight_text.splitlines():
        stripped = line.strip()
        if stripped == "Leitura":
            in_leitura = True
            continue
        if in_leitura and stripped in ("Observação", "Próximo passo"):
            break
        if in_leitura and stripped:
            leitura += stripped + "\n"

    # Build display: Leitura → narrative → Próximo passo (bold, at the end)
    parts = []
    if leitura.strip():
        parts.append(leitura.strip())
    if narrative_text:
        parts.append(narrative_text)
    combined = "\n".join(parts)

    st.markdown(
        f"<div style='"
        f"background:linear-gradient(135deg,#1a1a2e 0%,#16213e 60%,#0f3460 100%);"
        f"border-radius:14px;padding:14px 16px;box-shadow:0 4px 16px rgba(15,52,96,0.25);"
        f"font-family:sans-serif;'>"
        # Header: label (esq) | probabilidade + label (dir)
        f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;'>"
        f"  {header_label}"
        f"  <div style='display:flex;flex-direction:column;align-items:flex-end;flex-shrink:0;'>"
        f"    <div style='display:flex;align-items:baseline;gap:1px;'>"
        f"      <span style='font-size:40px;font-weight:800;color:{pct_color};line-height:1;'>{pct}</span>"
        f"      <span style='font-size:18px;font-weight:700;color:{pct_color};'>%</span>"
        f"    </div>"
        f"    <span style='font-size:10px;color:#94a3b8;margin-top:1px;'>prob. de fechamento</span>"
        f"  </div>"
        f"</div>"
        # Leitura + narrative
        f"<div style='font-size:12px;color:#cbd5e1;line-height:1.5;white-space:pre-line;margin-bottom:8px;'>{combined}</div>"
        # Próximo passo — bold, at the end
        + (
            f"<div style='font-size:12px;color:#cbd5e1;line-height:1.5;'>"
            f"<b>Próximo passo:</b> {action_text}"
            f"</div>"
            if action_text else ""
        )
        # Footer
        + f"<div style='margin-top:10px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.07);"
        f"display:flex;align-items:center;gap:5px;flex-wrap:wrap;'>"
        f"  <span style='font-size:10px;color:#64748b;'>◈ Fricção:</span>"
        f"  <span style='font-size:10px;font-weight:600;color:#94a3b8;'>{friction_label}</span>"
        f"  <span style='font-size:10px;color:#4a5568;'>·</span>"
        f"  <span style='font-size:10px;color:#64748b;'>Confiança: {confidence}</span>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    return result


def render_deal_narrative_card(narrative_text: str) -> None:
    """Renders the deterministic Deal Narrative card."""
    st.markdown(
        f"<div style='"
        f"background:#f0f4ff;"
        f"border:1px solid #d0d9f0;"
        f"border-radius:12px;"
        f"padding:12px 16px;"
        f"font-family:sans-serif;'>"
        f"<div style='font-size:11px;font-weight:700;color:#7986a8;text-transform:uppercase;"
        f"letter-spacing:.5px;margin-bottom:6px;'>Narrativa do Deal</div>"
        f"<div style='font-size:13px;color:#334155;font-style:italic;line-height:1.6;'>"
        f"&ldquo;{narrative_text}&rdquo;"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_seller_benchmark(current: dict, top: dict) -> None:
    def _fmt_wr(v):
        return f"{v:.0%}" if v is not None and pd.notna(v) else "—"
    def _fmt_cur(v):
        return format_currency(v) if v is not None and pd.notna(v) else "—"
    def _fmt_wp(v):
        return f"{v:.0%}" if v is not None and pd.notna(v) else "—"

    is_top    = current["name"] == top["name"]
    cur_badge = " 🏆" if is_top else ""

    rows = [
        ("Vendedor",               current["name"] + cur_badge,       top["name"] + " 🏆"),
        ("Deals no pipeline",      str(current["deals"]),              str(top["deals"])),
        ("Taxa de conversão",      _fmt_wr(current["win_rate"]),       _fmt_wr(top["win_rate"])),
        ("Expected Revenue médio", _fmt_cur(current["exp_revenue"]),   _fmt_cur(top["exp_revenue"])),
        ("Valor efetivo médio",    _fmt_cur(current["eff_value"]),     _fmt_cur(top["eff_value"])),
        ("Win Probability média",  _fmt_wp(current["win_prob"]),       _fmt_wp(top["win_prob"])),
    ]

    html = (
        "<table style='width:100%;border-collapse:collapse;font-size:12px;margin-bottom:6px;'>"
        "<thead><tr>"
        "<th style='text-align:left;padding:3px 5px;border-bottom:1px solid #ddd;color:#666;'>Métrica</th>"
        "<th style='text-align:center;padding:3px 5px;border-bottom:1px solid #ddd;color:#1976D2;'>Atual</th>"
        "<th style='text-align:center;padding:3px 5px;border-bottom:1px solid #ddd;color:#388E3C;'>🏆 Top</th>"
        "</tr></thead><tbody>"
    )
    for metric, cur_val, top_val in rows:
        html += (
            f"<tr>"
            f"<td style='padding:3px 5px;border-bottom:1px solid #f0f0f0;color:#444;'>{metric}</td>"
            f"<td style='padding:3px 5px;border-bottom:1px solid #f0f0f0;text-align:center;font-weight:600;color:#1976D2;'>{cur_val}</td>"
            f"<td style='padding:3px 5px;border-bottom:1px solid #f0f0f0;text-align:center;font-weight:600;color:#388E3C;'>{top_val}</td>"
            f"</tr>"
        )
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)


@st.dialog("Detalhes do Motor")
def _engine_details_dialog(name_pt: str, engine: str, details: dict) -> None:
    st.markdown(f"**{name_pt}**", unsafe_allow_html=False)
    if engine == "Seller Power":
        benchmark   = details.get("benchmark", {})
        agent_stats = details.get("agent_stats", {})
        if benchmark and agent_stats:
            _render_seller_benchmark(agent_stats, benchmark)
    for k, v in details.get("metrics", []):
        st.markdown(
            f"<span style='font-size:13px;'><b>{k}:</b> {v}</span>",
            unsafe_allow_html=True,
        )
    if details.get("interpretation"):
        st.markdown(
            f"<div style='font-size:13px;color:#555;background:#f5f5f5;"
            f"border-radius:4px;padding:8px 10px;margin-top:6px;'>"
            f"{details['interpretation']}</div>",
            unsafe_allow_html=True,
        )


def render_rating_engines(signal_payload: dict) -> None:
    engine_details = signal_payload.get("engine_details", {})

    with st.container(border=True):
        st.markdown(
            "<div style='font-size:14px;font-weight:700;color:#888;text-transform:uppercase;"
            "letter-spacing:.5px;margin-bottom:8px;'>Motores de Rating</div>",
            unsafe_allow_html=True,
        )

        for i, (engine, score) in enumerate(signal_payload["rating_engines"].items()):
            label   = _engine_label(score)
            name_pt = _ENGINE_LABELS_PT.get(engine, engine)
            color   = _LABEL_COLOR.get(label, "#888")
            text    = _LABEL_TEXT.get(label, label)
            details = engine_details.get(engine, {})

            if i > 0:
                st.markdown(
                    "<div style='border-top:1px solid #f0f0f0;margin:6px 0;'></div>",
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;'>"
                f"  <span style='font-size:13px;font-weight:600;color:#333;'>{name_pt}</span>"
                f"  {_pill(text, color)}"
                f"</div>"
                f"<div style='display:flex;align-items:center;gap:6px;margin-bottom:4px;'>"
                f"  <div style='flex:1;background:#e8eaed;border-radius:3px;height:5px;'>"
                f"    <div style='width:{score}%;background:{color};height:5px;border-radius:3px;'></div>"
                f"  </div>"
                f"  <span style='font-size:13px;font-weight:700;color:{color};min-width:24px;text-align:right;'>{score}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if details:
                if st.button("ver detalhes", key=f"engine_dlg_{engine}", use_container_width=True):
                    _engine_details_dialog(name_pt, engine, details)


def render_deal_health_card(row: pd.Series) -> None:
    health_score  = row.get("deal_health_score", None)
    health_status = str(row.get("deal_health_status", "—"))
    days          = row.get("days_since_engage", None)
    stale         = int(row.get("is_stale_flag", 0))
    velocity      = row.get("pipeline_velocity", None)
    maturity      = row.get("digital_maturity_index", None)

    score_val  = float(health_score) if health_score is not None and pd.notna(health_score) else 0.0
    bar_color  = _HEALTH_COLOR.get(health_status, "#888")
    score_str  = f"{score_val:.0f}" if score_val else "—"
    days_str   = f"{int(days)}d" if days is not None and pd.notna(days) else "—"
    vel_str    = f"{float(velocity):.0f}" if velocity is not None and pd.notna(velocity) else "—"
    mat_str    = f"{float(maturity) * 100:.0f}%" if maturity is not None and pd.notna(maturity) else "—"
    stale_badge = "<span style='background:#fef3c7;color:#b45309;font-size:11px;font-weight:600;" \
                  "padding:1px 7px;border-radius:8px;margin-left:6px;'>⚠ parado</span>" if stale else ""

    def _row(label: str, value: str, extra: str = "") -> str:
        return (
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"padding:5px 0;border-bottom:1px solid #f0f0f0;'>"
            f"  <span style='font-size:12px;color:#888;'>{label}</span>"
            f"  <span style='font-size:13px;font-weight:600;color:#333;'>{value}{extra}</span>"
            f"</div>"
        )

    st.markdown(
        f"{_CARD_OPEN}"
        # Seção Saúde — título esq, badge dir
        f"<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;'>"
        f"  <span style='font-size:14px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:.5px;'>Saúde</span>"
        f"  {_pill(health_status, bar_color)}"
        f"</div>"
        f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:12px;'>"
        f"  <div style='flex:1;background:#e8eaed;border-radius:4px;height:8px;'>"
        f"    <div style='width:{score_val}%;background:{bar_color};height:8px;border-radius:4px;'></div>"
        f"  </div>"
        f"  <span style='font-size:20px;font-weight:700;color:{bar_color};min-width:48px;text-align:right;white-space:nowrap;'>"
        f"    {score_str}<span style='font-size:12px;font-weight:400;color:#bbb;'>/100</span>"
        f"  </span>"
        f"</div>"
        + _row("Dias no pipeline", days_str, stale_badge)
        + _row("Velocidade", f"{vel_str} <span style='font-size:11px;color:#aaa;font-weight:400;'>dias/etapa</span>")
        + _row("Maturidade digital", mat_str)
        + f"{_CARD_CLOSE}",
        unsafe_allow_html=True,
    )


def render_deal_insight_panel(
    row: pd.Series,
    signal_payload: dict,
    df: Optional[pd.DataFrame] = None,
    auc: Optional[float] = None,
) -> None:
    """Renders the full deal analysis panel as a compact card."""
    auc_badge = (
        f"<span style='font-size:12px;font-weight:500;color:#888;margin-left:8px;'>"
        f"AUC {auc:.4f}</span>"
        if auc is not None else ""
    )
    st.markdown(
        f"<div style='display:flex;align-items:center;justify-content:space-between;'>"
        f"  <h4 style='margin:0;'>Análise do Deal</h4>"
        f"  {auc_badge}"
        f"</div>",
        unsafe_allow_html=True,
    )
    render_deal_header(row)
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    render_ai_insight_card(row, signal_payload, df)
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    render_deal_health_card(row)
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    render_rating_engines(signal_payload)
