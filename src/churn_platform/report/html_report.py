"""SPEC-10: Geração de relatório HTML auto-contido."""

from __future__ import annotations

import json
import logging
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://cdn.plot.ly/plotly-3.0.1.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Inter', sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }}
  .header {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 60px 40px; }}
  .header h1 {{ font-size: 2.5rem; font-weight: 800; }}
  .header .meta {{ margin-top: 16px; display: flex; gap: 24px; flex-wrap: wrap; }}
  .header .meta span {{ background: rgba(255,255,255,0.1); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 40px 24px; }}
  section {{ margin-bottom: 48px; }}
  h2 {{ font-size: 1.6rem; font-weight: 700; margin-bottom: 20px; color: #0f172a; border-left: 4px solid #3b82f6; padding-left: 16px; }}
  h3 {{ font-size: 1.15rem; font-weight: 600; margin: 24px 0 12px; color: #334155; }}
  .card {{ background: white; border-radius: 12px; padding: 28px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 20px; }}
  .card table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  .card th {{ text-align: left; padding: 10px 12px; background: #f1f5f9; font-weight: 600; border-bottom: 2px solid #e2e8f0; }}
  .card td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; }}
  .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  .stat {{ text-align: center; padding: 24px; background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  .stat .value {{ font-size: 2.2rem; font-weight: 800; }}
  .stat .label {{ font-size: 0.85rem; color: #64748b; }}
  @media (max-width: 768px) {{ .grid-2, .grid-3 {{ grid-template-columns: 1fr; }} }}
  .footer {{ text-align: center; padding: 32px; color: #94a3b8; font-size: 0.85rem; }}
</style>
</head>
<body>
<div class="header">
  <h1>{title}</h1>
  <div class="meta">{meta_html}</div>
</div>
<div class="container">
{body}
</div>
<script>
const _charts = {charts_json};
for (const [key, fig] of Object.entries(_charts)) {{
  const el = document.getElementById('chart-' + key);
  if (el) Plotly.newPlot(el, fig.data, fig.layout, {{responsive: true}});
}}
</script>
</body>
</html>
"""


def _make_table(df, pct_cols=None, max_rows=20):
    if df is None or (hasattr(df, 'empty') and df.empty):
        return "<p>Sem dados</p>"
    if hasattr(df, 'to_dict'):
        if isinstance(df, pd.Series):
            df = df.to_frame().T
        rows = df.head(max_rows).to_dict("records")
        cols = list(df.columns) if hasattr(df, 'columns') else list(rows[0].keys())
    else:
        return f"<pre>{df}</pre>"

    html = "<table><thead><tr>"
    for c in cols:
        html += f"<th>{c}</th>"
    html += "</tr></thead><tbody>"
    for row in rows:
        html += "<tr>"
        for c in cols:
            val = row.get(c, "")
            if pct_cols and c in pct_cols and isinstance(val, (int, float)):
                val = f"{val:.1%}"
            elif isinstance(val, float):
                val = f"{val:.2f}"
            html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


def _chart_div(key, height=350):
    return f'<div id="chart-{key}" style="width:100%;height:{height}px"></div>'


def build_report(
    account_view: pd.DataFrame,
    stats: dict[str, Any],
    segments: list[dict[str, Any]],
    descriptive: dict[str, Any],
    scored: pd.DataFrame,
    output_path: str = "output/report.html",
) -> str:
    logger.info("=== Gerando relatório HTML ===")
    charts = {}

    # Overview indicators
    fig = make_subplots(rows=1, cols=3, specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]])
    fig.add_trace(go.Indicator(value=round(stats["churn_rate"] * 100, 1), number={"suffix": "%", "font": {"size": 48}}, mode="number"), row=1, col=1)
    fig.add_trace(go.Indicator(value=stats["total_churned"], number={"font": {"size": 48}}, mode="number"), row=1, col=2)
    fig.add_trace(go.Indicator(value=stats["total_mrr_lost"], number={"prefix": "$", "font": {"size": 48}}, mode="number"), row=1, col=3)
    fig.update_layout(height=250, template="plotly_white")
    charts["overview"] = json.loads(fig.to_json())

    # Churn by industry
    if segments:
        for seg_data in segments:
            if seg_data["segment"] == "industry":
                rates = seg_data["churn_rates"]
                if rates:
                    df_seg = pd.DataFrame(rates)
                    fig = px.bar(df_seg, x="industry", y="churn_rate", text_auto=".0%",
                                 color="industry", color_discrete_sequence=px.colors.qualitative.Set2)
                    fig.update_layout(showlegend=False, template="plotly_white")
                    charts["industry"] = json.loads(fig.to_json())

    # Health score distribution
    if "health_score" in scored.columns:
        fig = px.histogram(scored, x="health_score", nbins=20, color="health_tier",
                           color_discrete_map={"Critical": "#ef4444", "At Risk": "#f97316",
                                               "Neutral": "#eab308", "Healthy": "#22c55e", "Champion": "#06b6d4"})
        fig.update_layout(template="plotly_white")
        charts["health_dist"] = json.loads(fig.to_json())

    # Build body
    meta = [
        f"📊 {stats['total_accounts']} contas",
        f"🚩 {stats['total_churned']} churned ({stats['churn_rate']:.1%})",
        f"💰 ${stats['total_mrr_lost']:,} MRR perdido",
    ]

    body = "<section><h2>📋 Sumário Executivo</h2><div class='card'>"
    body += f"<p>Churn rate de <strong>{stats['churn_rate']:.1%}</strong> — {stats['total_churned']} contas perdidas, "
    body += f"<strong>${stats['total_mrr_lost']:,} em MRR perdido</strong> (média de ${stats['avg_mrr_lost']:.0f}/conta).</p>"
    body += "</div></section>"

    body += "<section><h2>📊 Visão Geral</h2>"
    body += f"<div class='grid-3'>"
    body += f"<div class='stat'><div class='value' style='color:#ef4444'>{stats['churn_rate']:.1%}</div><div class='label'>Churn Rate</div></div>"
    body += f"<div class='stat'><div class='value' style='color:#ef4444'>{stats['total_churned']}</div><div class='label'>Contas Perdidas</div></div>"
    body += f"<div class='stat'><div class='value' style='color:#ef4444'>${stats['total_mrr_lost']:,}</div><div class='label'>MRR Perdido</div></div>"
    body += "</div>"
    body += _chart_div("overview", 280)
    body += "</section>"

    if "churn_type_split" in descriptive:
        body += "<section><h2>🔎 Voluntary vs Involuntary Churn</h2><div class='card'>"
        body += _make_table(pd.DataFrame([descriptive["churn_type_split"]]).T.reset_index())
        body += "</div></section>"

    body += "<section><h2>🏭 Churn por Indústria</h2><div class='card'>"
    body += _chart_div("industry", 300)
    if segments:
        for seg_data in segments:
            if seg_data["segment"] == "industry":
                body += _make_table(pd.DataFrame(seg_data["churn_rates"]), pct_cols=["churn_rate", "pct_of_total_churn"])
    body += "</div></section>"

    body += "<section><h2>🏥 Health Score Distribution</h2><div class='card'>"
    body += _chart_div("health_dist", 300)
    body += "</div></section>"

    body += "<section><h2>🎯 Top 10 Contas em Risco (Ativas)</h2><div class='card'>"
    at_risk = scored[(scored["churn_flag"] == False) & (scored["health_score"] <= 60)] if "churn_flag" in scored.columns and "health_score" in scored.columns else scored.head(0)
    if not at_risk.empty:
        cols = [c for c in ["account_id", "account_name", "industry", "plan_tier", "mrr_amount", "health_score", "health_tier"] if c in at_risk.columns]
        body += _make_table(at_risk.sort_values("health_score").head(10)[cols])
    else:
        body += "<p>Nenhuma conta em risco crítico.</p>"
    body += "</div></section>"

    meta_html = "".join(f"<span>{m}</span>" for m in meta)

    html = TEMPLATE.format(
        title="Diagnóstico de Churn — Plataforma SPEC-Driven",
        meta_html=meta_html,
        body=body,
        charts_json=json.dumps(charts),
    )

    with open(output_path, "w") as f:
        f.write(html)
    logger.info("Relatório salvo: %s", output_path)
    return output_path
