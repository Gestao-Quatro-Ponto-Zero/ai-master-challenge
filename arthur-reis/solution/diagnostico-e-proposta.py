"""
diagnostico.py — Gera diagnostico.html
Lê os CSVs reais, mas comunica os achados já validados no BRIEFING.
Não recalcula conclusões analíticas.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent
CSV1 = BASE / "datasets" / "customer_support_tickets.csv"
OUTPUT = BASE / "diagnostico-e-proposta.html"

# ---------------------------------------------------------------------------
# Leitura e preparo dos dados
# ---------------------------------------------------------------------------
df = pd.read_csv(CSV1)

# TTR em horas: (Time to Resolution) - (First Response Time)
df["First Response Time"] = pd.to_datetime(df["First Response Time"], errors="coerce")
df["Time to Resolution"]  = pd.to_datetime(df["Time to Resolution"],  errors="coerce")
df["TTR_hours"] = (df["Time to Resolution"] - df["First Response Time"]).dt.total_seconds() / 3600

# Subsets
df_closed  = df[df["Ticket Status"] == "Closed"].copy()
df_open    = df[df["Ticket Status"] == "Open"].copy()
df_pending = df[df["Ticket Status"] == "Pending Customer Response"].copy()

# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------
RED    = "#E84040"
YELLOW = "#F5A623"
GREEN  = "#27AE60"
GREY   = "#95A5A6"
DARK   = "#1A1A2E"
CARD_BG = "#F8F9FA"

# ---------------------------------------------------------------------------
# Helper: retorna string HTML do plotly figure
# ---------------------------------------------------------------------------
def fig_html(fig) -> str:
    return pio.to_html(fig, full_html=False, include_plotlyjs=False)


# ===========================================================================
# BLOCO 1 — Onde o fluxo trava?
# ===========================================================================

# --- 1A: Distribuição de status ---
status_labels  = ["Closed", "Open", "Pending Customer Response"]
status_values  = [2769, 2819, 2881]
status_colors  = [GREEN, RED, YELLOW]

fig_status = go.Figure(go.Pie(
    labels=status_labels,
    values=status_values,
    marker_colors=status_colors,
    hole=0.55,
    textinfo="label+percent",
    textfont_size=13,
    hovertemplate="%{label}: %{value:,} tickets (%{percent})<extra></extra>",
))
fig_status.update_layout(
    title=dict(text="Distribuição de Status dos Tickets", font_size=16, x=0.5),
    annotations=[dict(text="8.469<br>tickets", x=0.5, y=0.5, font_size=14,
                      showarrow=False)],
    showlegend=True,
    margin=dict(t=60, b=20, l=20, r=20),
    height=380,
    paper_bgcolor="white",
)

# --- 1B: Distribuição uniforme por canal ---
canais = ["Email", "Phone", "Chat", "Social media"]
totais = [2143, 2132, 2073, 2121]
fechados_pct = [33.6, 32.4, 32.5, 32.2]
nunca_tocados = [701, 736, 685, 697]
ttr_canal = [7.6, 7.3, 7.5, 7.9]

fig_canal = go.Figure()
fig_canal.add_trace(go.Bar(
    name="% Fechados", x=canais, y=fechados_pct,
    marker_color=GREEN, text=[f"{v}%" for v in fechados_pct],
    textposition="outside",
))
fig_canal.add_trace(go.Bar(
    name="% Nunca tocados", x=canais,
    y=[round(v/t*100, 1) for v, t in zip(nunca_tocados, totais)],
    marker_color=RED, text=[f"{round(v/t*100,1)}%" for v, t in zip(nunca_tocados, totais)],
    textposition="outside",
))
fig_canal.update_layout(
    title=dict(text="Taxa de Fechamento e Tickets Nunca Tocados por Canal",
               font_size=16, x=0.5),
    barmode="group",
    yaxis=dict(title="% dos tickets", range=[0, 50]),
    xaxis_title="Canal",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=80, b=40),
    height=380,
    paper_bgcolor="white",
)

# --- 1C: TTR por faixa (go.Bar com dados fixos do BRIEFING) ---
ttr_faixas  = ["< 1h", "1–4h", "4–8h", "8–24h"]
ttr_qtd     = [103, 378, 357, 566]
ttr_pct     = [7.3, 26.9, 25.4, 40.3]
# Gradiente verde → amarelo → laranja → vermelho (mais tempo = mais quente)
ttr_cores   = ["#27AE60", "#F1C40F", "#E67E22", "#E84040"]

fig_ttr = go.Figure(go.Bar(
    x=ttr_faixas,
    y=ttr_qtd,
    marker_color=ttr_cores,
    text=[f"{q} tickets<br>({p}%)" for q, p in zip(ttr_qtd, ttr_pct)],
    textposition="outside",
    hovertemplate="%{x}: %{y} tickets (%{customdata}%)<extra></extra>",
    customdata=ttr_pct,
))
fig_ttr.update_layout(
    title=dict(text="Distribuição de TTR — Tickets Resolvidos por Faixa", font_size=16, x=0.5),
    xaxis_title="Faixa de tempo até resolução",
    yaxis=dict(title="Quantidade de tickets", range=[0, 700]),
    bargap=0.25,
    margin=dict(t=60, b=40),
    height=360,
    paper_bgcolor="white",
)

# --- 1D: Combinações críticas ---
combos = [
    "Social media × Cancellation",
    "Phone × Cancellation",
    "Email × Product inquiry",
    "Média geral",
]
fechados_combo = [26.2, 27.7, 29.5, 32.7]
colors_combo = [RED, RED, RED, GREEN]

fig_combo = go.Figure(go.Bar(
    x=fechados_combo,
    y=combos,
    orientation="h",
    marker_color=colors_combo,
    text=[f"{v}%" for v in fechados_combo],
    textposition="outside",
    hovertemplate="%{y}: %{x}% fechados<extra></extra>",
))
fig_combo.update_layout(
    title=dict(text="Combinações Mais Críticas — % de Tickets Fechados", font_size=16, x=0.5),
    xaxis=dict(title="% fechados", range=[0, 50]),
    margin=dict(t=60, b=40, l=220),
    height=300,
    paper_bgcolor="white",
)


# ===========================================================================
# BLOCO 2 — O que impacta satisfação?
# ===========================================================================

ratings = [1, 2, 3, 4, 5]
rating_counts = [553, 549, 580, 543, 544]
rating_pct    = [20.0, 19.8, 20.9, 19.6, 19.6]

fig_rating = go.Figure(go.Bar(
    x=[f"★{r}" for r in ratings],
    y=rating_counts,
    marker_color=["#E74C3C","#E67E22","#F1C40F","#2ECC71","#27AE60"],
    text=[f"{p}%" for p in rating_pct],
    textposition="outside",
    hovertemplate="%{x}: %{y} tickets (%{text})<extra></extra>",
))
fig_rating.add_hline(y=553, line_dash="dot", line_color=GREY,
                     annotation_text="Distribuição esperada se aleatória (≈ 553)",
                     annotation_font_color=GREY)
fig_rating.update_layout(
    title=dict(text="Distribuição de CSAT — Tickets Fechados (n=2.769)", font_size=16, x=0.5),
    yaxis=dict(title="Quantidade de tickets", range=[0, 700]),
    xaxis_title="Rating",
    margin=dict(t=60, b=40),
    height=360,
    paper_bgcolor="white",
)


# ===========================================================================
# BLOCO 3 — Quanto desperdiçamos?
# ===========================================================================

# --- 3A: Horas por categoria ---
categorias_horas = [
    "TTR — Tickets resolvidos",
    "Toque estimado — Tickets não fechados",
]
horas = [10639, 1881]
colors_horas = ["#3498DB", RED]

fig_horas = go.Figure(go.Bar(
    x=horas,
    y=categorias_horas,
    orientation="h",
    marker_color=colors_horas,
    text=[f"{h:,}h" for h in horas],
    textposition="outside",
    hovertemplate="%{y}: %{x:,}h<extra></extra>",
))
fig_horas.update_layout(
    title=dict(text="Distribuição de Horas de Agente na Operação", font_size=16, x=0.5),
    xaxis=dict(title="Horas", range=[0, 13500]),
    margin=dict(t=60, b=40, l=280),
    height=260,
    paper_bgcolor="white",
)

# --- 3B: Potencial de automação por tipo ---
tipos = ["Billing inquiry", "Product inquiry", "Technical issue", "Cancellation request", "Refund request"]
potencial = [85, 80, 60, 0, 50]  # % estimado de automação — baseado na lógica do briefing
colors_pot = [GREEN, GREEN, YELLOW, RED, YELLOW]
notas = ["Alta", "Alta", "Média", "Nunca automatizar", "Média"]

fig_auto = go.Figure(go.Bar(
    x=potencial,
    y=tipos,
    orientation="h",
    marker_color=colors_pot,
    text=[f"{p}% — {n}" for p, n in zip(potencial, notas)],
    textposition="outside",
    hovertemplate="%{y}: %{x}% automação<extra></extra>",
))
fig_auto.update_layout(
    title=dict(text="Potencial de Automação por Tipo de Ticket", font_size=16, x=0.5),
    xaxis=dict(title="% estimado de cobertura por IA", range=[0, 120]),
    margin=dict(t=60, b=40, l=190),
    height=320,
    paper_bgcolor="white",
)


# ===========================================================================
# BLOCO 4 — Proposta de Automação
# ===========================================================================

# --- 4A: Projeção de cobertura antes × depois ---
etapas = ["Hoje (sem IA)", "Fase 1: Follow-up automático", "Fase 2: Triagem IA (SIM/TALVEZ/NÃO)", "Fase 3: Resposta automática (SIM)"]
resolvidos_proj = [32.7, 52.0, 65.0, 78.0]
colors_proj = [RED, YELLOW, "#3498DB", GREEN]

fig_proj = go.Figure(go.Bar(
    x=etapas,
    y=resolvidos_proj,
    marker_color=colors_proj,
    text=[f"{v}%" for v in resolvidos_proj],
    textposition="outside",
    hovertemplate="%{x}: %{y}% de tickets resolvidos/cobertos<extra></extra>",
))
fig_proj.add_hline(y=32.7, line_dash="dash", line_color=GREY,
                   annotation_text="Baseline atual: 32.7%",
                   annotation_font_color=GREY)
fig_proj.update_layout(
    title=dict(text="Projeção de Cobertura por Fase de Automação", font_size=16, x=0.5),
    yaxis=dict(title="% tickets resolvidos/cobertos por IA", range=[0, 100]),
    xaxis_title="Fase",
    margin=dict(t=60, b=80),
    height=380,
    paper_bgcolor="white",
)

# --- 4B: Gráfico de decisão SIM / TALVEZ / NÃO por tipo ---
tipos_decisao = ["Billing inquiry", "Product inquiry", "Refund request", "Technical issue", "Cancellation request"]
sim_pct    = [60, 55, 35, 40, 0]
talvez_pct = [25, 25, 15, 20, 0]
nao_pct    = [15, 20, 50, 40, 100]

fig_decisao = go.Figure()
fig_decisao.add_trace(go.Bar(name="SIM ✅",    x=tipos_decisao, y=sim_pct,    marker_color=GREEN))
fig_decisao.add_trace(go.Bar(name="TALVEZ 🟡", x=tipos_decisao, y=talvez_pct, marker_color=YELLOW))
fig_decisao.add_trace(go.Bar(name="NÃO 🔴",    x=tipos_decisao, y=nao_pct,    marker_color=RED))
fig_decisao.update_layout(
    title=dict(text="Distribuição Estimada SIM / TALVEZ / NÃO por Tipo de Ticket", font_size=16, x=0.5),
    barmode="stack",
    yaxis=dict(title="% dos tickets do tipo", range=[0, 105]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=80, b=40),
    height=380,
    paper_bgcolor="white",
)


# ===========================================================================
# HTML FINAL
# ===========================================================================

def card(title: str, value: str, subtitle: str, color: str) -> str:
    return f"""
    <div style="background:{CARD_BG};border-left:5px solid {color};
                border-radius:6px;padding:16px 20px;flex:1;min-width:180px;">
      <div style="font-size:13px;color:#666;margin-bottom:4px;">{title}</div>
      <div style="font-size:28px;font-weight:700;color:{color};">{value}</div>
      <div style="font-size:12px;color:#888;margin-top:4px;">{subtitle}</div>
    </div>"""


def table_html(headers: list, rows: list, highlight_col=None) -> str:
    ths = "".join(f"<th>{h}</th>" for h in headers)
    trs = ""
    for row in rows:
        tds = ""
        for i, cell in enumerate(row):
            style = ' style="font-weight:600;"' if i == highlight_col else ""
            tds += f"<td{style}>{cell}</td>"
        trs += f"<tr>{tds}</tr>"
    return f"""
    <div style="overflow-x:auto;">
    <table>
      <thead><tr>{ths}</tr></thead>
      <tbody>{trs}</tbody>
    </table>
    </div>"""


# Tabelas do bloco 1
table_canal = table_html(
    ["Canal", "Total", "% Fechados", "TTR médio", "Nunca tocados"],
    [
        ["Email",        "2.143", "33.6%", "7.6h", "701 (32.7%)"],
        ["Phone",        "2.132", "32.4%", "7.3h", "736 (34.5%)"],
        ["Chat",         "2.073", "32.5%", "7.5h", "685 (33.0%)"],
        ["Social media", "2.121", "32.2%", "7.9h", "697 (32.9%)"],
    ],
)

table_tipo = table_html(
    ["Tipo", "Total", "% Fechados", "TTR médio", "Pending"],
    [
        ["Technical issue",      "1.747", "33.2%", "7.4h", "565 (32.3%)"],
        ["Billing inquiry",      "1.634", "33.3%", "7.0h", "551 (33.7%)"],
        ["Refund request",       "1.752", "34.0%", "8.1h", "592 (33.8%)"],
        ["Product inquiry",      "1.641", "32.5%", "7.7h", "576 (35.1%)"],
        ["Cancellation request", "1.695", "30.4%", "7.7h", "597 (35.2%)"],
    ],
)

table_ttr_faixas = table_html(
    ["Faixa de TTR", "Tickets", "%"],
    [
        ["< 1h",  "103",  "7.3%"],
        ["1–4h",  "378",  "26.9%"],
        ["4–8h",  "357",  "25.4%"],
        ["8–24h", "566",  "40.3%"],
    ],
    highlight_col=2,
)

PLOTLYJS = '<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>'

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Diagnóstico Operacional — G4 Tech</title>
  {PLOTLYJS}
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #F0F2F5;
      color: #1A1A2E;
      margin: 0;
      padding: 0 0 60px;
    }}
    header {{
      background: {DARK};
      color: white;
      padding: 36px 48px 28px;
    }}
    header h1 {{ margin: 0 0 6px; font-size: 26px; }}
    header p  {{ margin: 0; opacity: .7; font-size: 14px; }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 0 24px; }}
    .section {{
      background: white;
      border-radius: 10px;
      padding: 32px;
      margin: 32px 0;
      box-shadow: 0 2px 8px rgba(0,0,0,.06);
    }}
    .section h2 {{
      margin: 0 0 6px;
      font-size: 20px;
      border-left: 5px solid {DARK};
      padding-left: 12px;
    }}
    .section .lead {{
      color: #555;
      font-size: 14px;
      margin: 0 0 24px 17px;
    }}
    .cards {{
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 28px;
    }}
    .insight {{
      background: #FFF8E1;
      border-left: 5px solid {YELLOW};
      border-radius: 6px;
      padding: 14px 18px;
      font-size: 14px;
      margin: 20px 0;
      line-height: 1.6;
    }}
    .insight.critical {{
      background: #FFEBEE;
      border-color: {RED};
    }}
    .insight.positive {{
      background: #E8F5E9;
      border-color: {GREEN};
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      margin: 16px 0;
    }}
    thead tr {{ background: {DARK}; color: white; }}
    th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #EEE; }}
    tbody tr:hover {{ background: #F5F5F5; }}
    .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
    .cost-box {{
      background: #E8EAF6;
      border-radius: 8px;
      padding: 20px 24px;
      font-family: monospace;
      font-size: 14px;
      line-height: 2;
    }}
    .cost-box strong {{ color: {DARK}; }}
    .tag {{
      display: inline-block;
      padding: 2px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
    }}
    .tag.sim {{ background: #E8F5E9; color: {GREEN}; }}
    .tag.talvez {{ background: #FFF8E1; color: #E67E00; }}
    .tag.nao {{ background: #FFEBEE; color: {RED}; }}
    @media (max-width: 700px) {{
      .grid2 {{ grid-template-columns: 1fr; }}
      header {{ padding: 24px 20px 20px; }}
      .section {{ padding: 20px; }}
    }}
  </style>
</head>
<body>

<header>
  <div class="container">
    <h1>Diagnóstico Operacional + Proposta de Automação — G4 Tech</h1>
    <p>Challenge 002 · Entregáveis 1 e 2 · Dados: 8.469 tickets de suporte · Arthur Reis</p>
    <p style="margin-top:8px;opacity:.85;font-size:13px;">
      Este documento reúne o <strong>Entregável 1 — Diagnóstico Operacional</strong> (Blocos 1, 2 e 3)
      e o <strong>Entregável 2 — Proposta de Automação com IA</strong> (Bloco 4).
      O Entregável 3 — Protótipo Funcional — está no arquivo <code>app.py</code>.
    </p>
  </div>
</header>

<div class="container">

  <!-- ===== BLOCO 1 ===== -->
  <div class="section">
    <h2>Bloco 1 — Onde o fluxo trava?</h2>
    <p class="lead">67.3% dos tickets não foram resolvidos. O problema não é pontual — é sistêmico.</p>

    <div class="cards">
      {card("Tickets Resolvidos",    "2.769", "32.7% do total · únicos com CSAT", GREEN)}
      {card("Tickets Open",          "2.819", "33.3% · nunca receberam first response", RED)}
      {card("Pending Customer Resp.","2.881", "34.0% · sem follow-up automático", YELLOW)}
      {card("Total NÃO resolvidos",  "5.700", "67.3% da operação presa", RED)}
    </div>

    <div class="insight critical">
      <strong>Dois tipos distintos de falha:</strong><br>
      <b>Open = falha de capacidade</b> — 100% dos tickets Open nunca receberam first response. A fila não tem capacidade de atendimento.<br>
      <b>Pending = falha de processo</b> — o agente tocou, devolveu ao cliente e parou. Sem follow-up automático, o ticket fica suspenso indefinidamente.
    </div>

    {fig_html(fig_status)}

    <h3 style="margin:28px 0 8px;">Distribuição uniforme — achado estrutural</h3>
    <div class="insight">
      Canais, tipos e prioridades têm taxas de fechamento quase idênticas (~32–34%).
      <strong>Isso não é ausência de achado — é o achado:</strong> o problema é sistêmico, não localizado em nenhum canal ou tipo específico.
    </div>

    <div class="grid2">
      <div>
        <h4>Por Canal</h4>
        {table_canal}
      </div>
      <div>
        <h4>Por Tipo</h4>
        {table_tipo}
      </div>
    </div>

    {fig_html(fig_canal)}
    {fig_html(fig_combo)}

    <h3 style="margin:28px 0 8px;">TTR dos tickets resolvidos</h3>
    <div class="grid2">
      <div>{fig_html(fig_ttr)}</div>
      <div style="padding-top:24px;">
        <h4>Distribuição por faixa</h4>
        {table_ttr_faixas}
        <div class="insight positive" style="margin-top:16px;">
          Nenhum ticket levou mais de 24h para ser resolvido após iniciado.
          A mediana de 6.4h é razoável — o problema não é a velocidade de resolução,
          é a <strong>incapacidade de iniciar o atendimento</strong> em 67% dos casos.
        </div>
      </div>
    </div>
  </div>

  <!-- ===== BLOCO 2 ===== -->
  <div class="section">
    <h2>Bloco 2 — O que impacta satisfação?</h2>
    <p class="lead">A G4 Tech não possui sistema de coleta de CSAT funcionando.</p>

    {fig_html(fig_rating)}

    <div class="insight critical" style="margin-top:24px;">
      <strong>Achado crítico: ratings estatisticamente aleatórios.</strong><br>
      A distribuição perfeitamente uniforme (20% em cada nota de 1 a 5) indica que os ratings
      foram atribuídos aleatoriamente — não refletem a experiência real do cliente.<br><br>
      Testes realizados:<br>
      • Pearson r(TTR × Satisfação) = <b>-0.0035</b> | NÃO significativo<br>
      • F-statistic Canal = <b>1.28</b> (limiar de sinal &gt; 2.5) → ruído<br>
      • F-statistic Tipo = <b>0.55</b> → ruído<br>
      • F-statistic Prioridade = <b>0.57</b> → ruído<br><br>
      <strong>Consequência:</strong> Sem CSAT válido, é impossível medir o impacto de qualquer melhoria futura.
      Implementar coleta de satisfação real é pré-requisito para qualquer programa de melhoria contínua.
    </div>
  </div>

  <!-- ===== BLOCO 3 ===== -->
  <div class="section">
    <h2>Bloco 3 — Quanto desperdiçamos?</h2>
    <p class="lead">~12.520 horas de agente na operação. Mais da metade tocando tickets que nunca fecham.</p>

    <div class="cards">
      {card("Horas em tickets resolvidos", "10.639h", "TTR acumulado · 2.769 tickets fechados", "#3498DB")}
      {card("Horas estimadas em abertos",  "1.881h",  "0.33h toque médio × 5.700 não fechados", YELLOW)}
      {card("Total horas na operação",     "~12.520h", "Base para cálculo de custo", DARK)}
    </div>

    {fig_html(fig_horas)}

    <h3 style="margin:28px 0 8px;">Custo financeiro — fórmula (use o custo/hora real da empresa)</h3>
    <div class="cost-box">
      <strong>Custo por ticket fechado</strong> = (custo/hora do agente) × 10.639h ÷ 2.769 tickets<br>
      <strong>Custo do desperdício recuperável</strong> = (custo/hora) × 1.881h<br><br>
      Exemplo com benchmark de mercado R$ 45/h:<br>
      → Custo por ticket fechado ≈ <b>R$ 172,70</b><br>
      → Custo estimado do desperdício ≈ <b>R$ 84.645</b><br><br>
      <em>* Substitua pelo custo/hora real para obter o número correto.</em>
    </div>

    <h3 style="margin:28px 0 8px;">Onde está o maior desperdício recuperável</h3>
    <div class="insight">
      • <b>2.881 tickets "Pending"</b> — uma automação de follow-up resolve boa parte sem IA complexa<br>
      • <b>2.819 tickets "Open/nunca tocados"</b> — atendimento imediato por IA cobre a fila 24/7<br>
      • Tipos mais determinísticos para automação: <b>Billing inquiry</b> e <b>Product inquiry</b>
    </div>

    {fig_html(fig_auto)}

    <h4 style="margin-top:24px;">Thresholds de automação por tipo</h4>
    <table>
      <thead><tr><th>Tipo</th><th>Decisão</th><th>Justificativa</th></tr></thead>
      <tbody>
        <tr><td>Billing inquiry</td>
            <td><span class="tag sim">SIM / TALVEZ</span></td>
            <td>Perguntas com respostas padronizáveis</td></tr>
        <tr><td>Product inquiry</td>
            <td><span class="tag sim">SIM / TALVEZ</span></td>
            <td>Perguntas com respostas padronizáveis</td></tr>
        <tr><td>Technical issue (baixa/média)</td>
            <td><span class="tag talvez">TALVEZ</span></td>
            <td>Depende da complexidade; triagem necessária</td></tr>
        <tr><td>Cancellation request</td>
            <td><span class="tag nao">NÃO</span></td>
            <td>Requer retenção humana — nunca automatizar</td></tr>
        <tr><td>Qualquer ticket Critical</td>
            <td><span class="tag nao">NÃO</span></td>
            <td>Sempre escala para agente humano</td></tr>
      </tbody>
    </table>
  </div>

  <!-- ===== BLOCO 4 — Entregável 2 ===== -->
  <div class="section">
    <h2>Bloco 4 — Proposta de Automação com IA <span style="font-size:13px;font-weight:400;color:#888;margin-left:8px;">(Entregável 2)</span></h2>
    <p class="lead">67.3% dos tickets não são resolvidos. O problema não é falta de capacidade humana — é falta de inteligência no processo. A proposta é uma plataforma interna de suporte com IA que resolve o que é determinístico e entrega contexto pronto para o que exige julgamento humano.</p>

    <div class="insight positive">
      <strong>Princípio de design:</strong> IA não substitui o agente. IA faz o que é repetível e padronizável —
      classificar, perguntar, buscar no histórico, gerar resposta. O agente humano assume o que exige julgamento:
      retenção, negociação, complexidade técnica. A divisão é clara: cada um no que faz melhor.
    </div>

    <h3 style="margin:32px 0 12px;">1. O que a plataforma faz na primeira mensagem</h3>
    <p style="color:#555;font-size:14px;margin-bottom:16px;">
      O pipeline tem duas fases distintas e sequenciais: <b>roteamento</b> (sempre acontece, independente de qualquer análise de confiança)
      e <b>decisão de resposta</b> (baseada na confiança do classificador). O roteamento determina <i>onde</i> o ticket pertence.
      A decisão determina <i>como</i> ele será tratado.
    </p>

    <div style="background:#F8F9FA;border-radius:8px;padding:22px 26px;font-size:13px;line-height:2.3;overflow-x:auto;border:1px solid #E0E0E0;">

      <b style="font-size:14px;color:#1565C0;">— FASE 1: ROTEAMENTO (sempre, em milissegundos) —</b><br><br>

      &nbsp;&nbsp;<b style="color:{RED};">① Regras fixas</b> — verificadas primeiro, sem modelo<br>
      &nbsp;&nbsp;&nbsp;&nbsp;→ Contém "cancelar" / "urgente" / "emergência"? → flag de bloqueio ativado → segue para NÃO direto após roteamento<br><br>

      &nbsp;&nbsp;<b style="color:#1565C0;">② Nível 1 — Tipo de ticket e setor</b><br>
      &nbsp;&nbsp;&nbsp;&nbsp;→ 5 categorias: Billing inquiry · Technical issue · Refund request · Product inquiry · Cancellation request<br>
      &nbsp;&nbsp;&nbsp;&nbsp;→ Determina o <b>setor responsável</b> (Faturamento · Técnico · Reembolsos · Produto · Retenção)<br>
      &nbsp;&nbsp;&nbsp;&nbsp;→ Acontece sempre — independente da decisão SIM / TALVEZ / NÃO<br><br>

      &nbsp;&nbsp;<b style="color:#7B1FA2;">③ Nível 2 — Sub-área técnica</b> — <i>somente se Nível 1 = Technical issue</i><br>
      &nbsp;&nbsp;&nbsp;&nbsp;→ Sub-área: Hardware · Access &amp; Login · Software &amp; App · Network · Storage<br>
      &nbsp;&nbsp;&nbsp;&nbsp;→ Determina o <b>time técnico específico</b> dentro da Equipe Técnica<br>
      &nbsp;&nbsp;&nbsp;&nbsp;→ Acontece sempre para Technical issue — independente da decisão SIM / TALVEZ / NÃO<br><br>

      <b style="font-size:14px;color:#27AE60;">— FASE 2: DECISÃO DE RESPOSTA (baseada em confiança) —</b><br><br>

      &nbsp;&nbsp;<b style="color:#27AE60;">④ Busca RAG no histórico</b> — tickets similares já resolvidos<br>
      &nbsp;&nbsp;&nbsp;&nbsp;→ Recupera padrões de resolução e contexto relevante do setor já determinado no roteamento<br>
      &nbsp;&nbsp;&nbsp;&nbsp;→ Alimenta tanto a resposta automática (SIM) quanto o resumo para o agente (NÃO)<br><br>

      <b style="font-size:14px;">Com os resultados do roteamento + confiança do classificador → decisão:</b><br><br>
      &nbsp;&nbsp;<span style="color:{GREEN};font-weight:700;">✅ SIM (confiança ≥ 70%)</span> — resposta gerada via Claude API com contexto do RAG → <b>2 outputs simultâneos:</b><br>
      &nbsp;&nbsp;&nbsp;&nbsp;<b>① Resposta automática enviada ao cliente</b> → ticket fechado → CSAT solicitado em 24h<br>
      &nbsp;&nbsp;&nbsp;&nbsp;<b>② Tarefa interna gerada para o operador responsável</b> — quando a resposta contém promessa de ação com prazo<br>
      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(ex.: "estorno em 3–5 dias", "equipe entrará em contato em 4h") — a tarefa registra: operador, ação, sistema, prazo alinhado com o prometido<br>
      &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ <em>A IA responde. O humano entrega. Se o prazo da tarefa vencer sem execução, o ticket reabre automaticamente.</em><br><br>
      &nbsp;&nbsp;<span style="color:#E67E00;font-weight:700;">🟡 TALVEZ (45–69%)</span> — 2–3 perguntas de triagem enviadas ao cliente → aguarda resposta → reclassifica → SIM ou NÃO<br>
      &nbsp;&nbsp;<span style="color:{RED};font-weight:700;">🔴 NÃO (&lt; 45% ou regra fixa)</span> — resumo estruturado gerado → fila do setor correto (já determinado no roteamento) com categoria, sub-área e histórico

    </div>

    <h3 style="margin:32px 0 12px;">2. Stack Tecnológica — Plataforma Interna</h3>
    <p style="color:#555;font-size:14px;margin-bottom:16px;">
      A plataforma é construída com Claude Code sobre infraestrutura própria. Sem dependência de ferramentas
      de automação externas. Arquitetura desenhada para escala.
    </p>
    <table>
      <thead><tr><th>Camada</th><th>Tecnologia</th><th>Função</th></tr></thead>
      <tbody>
        <tr>
          <td><b>API de IA</b></td>
          <td>Claude API (Anthropic)</td>
          <td>Geração de respostas para casos SIM, síntese de resumos para casos NÃO, processamento de linguagem natural</td>
        </tr>
        <tr>
          <td><b>Classificação rápida</b></td>
          <td>Keywords + ML leve (TF-IDF) — sem latência de API</td>
          <td>Nível 1: Ticket Type. Nível 2: sub-área técnica. Executado localmente em milissegundos</td>
        </tr>
        <tr>
          <td><b>Base de conhecimento + RAG</b></td>
          <td>Embeddings vetoriais (ex: pgvector no PostgreSQL)</td>
          <td>Busca semântica no histórico de tickets resolvidos. Recupera contexto relevante para respostas e resumos</td>
        </tr>
        <tr>
          <td><b>Plataforma interna</b></td>
          <td>Backend próprio (Python/FastAPI) + fila de tickets</td>
          <td>Recebe tickets de qualquer canal, executa o pipeline de decisão, entrega resultado ao agente ou ao cliente</td>
        </tr>
        <tr>
          <td><b>Interface do agente</b></td>
          <td>Dashboard interno</td>
          <td>Fila priorizada para casos NÃO, com contexto estruturado pronto. Agente vê: tipo, sub-área, histórico, TTR esperado</td>
        </tr>
        <tr>
          <td><b>CSAT e monitoramento</b></td>
          <td>Coleta automática pós-fechamento + dashboard de métricas</td>
          <td>Taxa de automação, TTR real, CSAT por tipo, volume por canal — retroalimenta o modelo de classificação</td>
        </tr>
      </tbody>
    </table>

    <h3 style="margin:32px 0 12px;">3. Base de Conhecimento — Curadoria pelos Agentes</h3>
    <p style="color:#555;font-size:14px;margin-bottom:16px;">
      A qualidade das respostas automáticas é diretamente proporcional à qualidade do que está na base de conhecimento.
      A IA não inventa respostas — ela recupera, sintetiza e adapta o que os agentes já sabem. A base é construída e mantida pela equipe operacional.
    </p>

    <div style="background:#F8F9FA;border-radius:8px;padding:22px 26px;font-size:13px;line-height:2.3;overflow-x:auto;border:1px solid #E0E0E0;">
      <b style="font-size:14px;">O que os agentes e líderes inserem na base:</b><br><br>
      &nbsp;&nbsp;<b style="color:#1565C0;">① SOPs e procedimentos internos</b> — passo a passo de como resolver cada tipo de ticket, regras de negócio, exceções e escalonamentos<br>
      &nbsp;&nbsp;<b style="color:#1565C0;">② FAQs estruturadas por categoria</b> — perguntas frequentes com resposta padrão aprovada pelo líder de equipe<br>
      &nbsp;&nbsp;<b style="color:#1565C0;">③ Templates de resposta validados</b> — respostas de tickets já resolvidos com CSAT ≥ 4, revisadas antes de indexação<br>
      &nbsp;&nbsp;<b style="color:#1565C0;">④ Documentação de produto</b> — manuais técnicos, notas de versão, políticas de cobrança, políticas de reembolso<br>
      &nbsp;&nbsp;<b style="color:#1565C0;">⑤ Pares ticket × resolução validados</b> — gerados automaticamente após fechamento + CSAT ≥ 4, com revisão para CSAT = 3
    </div>

    <table style="margin-top:20px;">
      <thead><tr><th>Responsável</th><th>O que sobe na base</th><th>Frequência</th><th>Validação</th></tr></thead>
      <tbody>
        <tr><td>Agente operacional</td><td>Tickets resolvidos com CSAT ≥ 4, anotações de resolução</td><td>A cada fechamento</td><td>Automático + quarentena 24h</td></tr>
        <tr><td>Líder de equipe</td><td>SOPs revisados, templates aprovados, FAQ atualizada</td><td>Quinzenal</td><td>Manual — líder aprova antes de indexar</td></tr>
        <tr><td>Time de produto</td><td>Documentação técnica, políticas de cobrança/reembolso</td><td>A cada release</td><td>Pull request revisado pelo líder técnico</td></tr>
        <tr><td>Processo automático</td><td>Novos pares (ticket, resolução) após fechamento bem-sucedido</td><td>Diário</td><td>CSAT e flag de revisão humana</td></tr>
      </tbody>
    </table>

    <div class="insight">
      <strong>Base sem curadoria ativa deteriora.</strong> Os agentes são o mecanismo de atualização contínua —
      cada resolução bem-sucedida é uma nova entrada em potencial. Cada política alterada precisa de atualização manual.
      Cada release de produto gera documentação nova. A plataforma é tão boa quanto o que está na base.<br><br>
      <strong>Responsabilidade por seção:</strong> cada time de especialidade (billing, técnico, produto) é owner da sua seção.
      Revisão quinzenal obrigatória para remover conteúdo desatualizado. Entradas novas ficam em quarentena de 24h
      para revisão antes de ficarem ativas para o RAG.
    </div>

    {fig_html(fig_decisao)}
    {fig_html(fig_proj)}

    <h3 style="margin:32px 0 12px;">4. Roadmap — 3 Fases de Implementação</h3>
    <table>
      <thead><tr><th>Fase</th><th>O que implementar</th><th>Impacto esperado</th><th>Complexidade</th></tr></thead>
      <tbody>
        <tr>
          <td><b>Fase 1</b><br><small>Semanas 1–4</small><br><small style="color:{GREEN};">Quick win</small></td>
          <td>
            <b>Follow-up automático nos 2.881 tickets Pending:</b> após 24h sem resposta do cliente,
            mensagem automática de lembrete. Após 72h, fecha como "sem retorno".<br>
            <b>CSAT real:</b> pesquisa de 1 pergunta (1–5 estrelas) enviada automaticamente ao fechar qualquer ticket.
          </td>
          <td>+19pp de resolução estimado<br>~547 tickets reativados<br>CSAT funcional desde o dia 1</td>
          <td><span class="tag sim">Baixa</span> — automação de processo, sem ML</td>
        </tr>
        <tr>
          <td><b>Fase 2</b><br><small>Meses 1–2</small></td>
          <td>
            <b>Pipeline de decisão SIM/TALVEZ/NÃO em produção:</b> classificação Nível 1 + Nível 2 automática
            na primeira mensagem. Casos TALVEZ recebem perguntas de triagem. Casos NÃO chegam ao agente
            com resumo estruturado pronto (categoria, sub-área, histórico, TTR de referência).
          </td>
          <td>+13pp adicionais<br>Fila Open atendida 24/7<br>Agente humano já sabe o que é antes de abrir</td>
          <td><span class="tag talvez">Média</span> — integração da classificação + Claude API</td>
        </tr>
        <tr>
          <td><b>Fase 3</b><br><small>Meses 2–4</small></td>
          <td>
            <b>Respostas automáticas para casos SIM (piloto):</b> Billing inquiry e Product inquiry primeiro.
            Claude API gera resposta personalizada com base no histórico RAG e envia diretamente ao cliente.
            Nível 2 roteia Technical issues para o time técnico correto automaticamente.
          </td>
          <td>+13pp adicionais<br>Cobertura total estimada: ~78%<br>Custo por ticket reduzido ~60%</td>
          <td><span class="tag talvez">Média-Alta</span> — RAG + geração de resposta via Claude API</td>
        </tr>
      </tbody>
    </table>

    <h3 style="margin:28px 0 12px;">5. Melhoria Contínua — Ciclo de Retroalimentação</h3>
    <p style="color:#555;font-size:14px;margin-bottom:16px;">
      A plataforma não é estática. Cada ticket resolvido é uma nova amostra de treinamento — o sistema aprende com o
      que funcionou e com o que falhou. O loop fecha quando CSAT real está disponível.
    </p>

    <div style="background:#F8F9FA;border-radius:8px;padding:22px 26px;font-size:13px;line-height:2.3;overflow-x:auto;border:1px solid #E0E0E0;">
      <b style="font-size:14px;">O ciclo depois de cada ticket fechado:</b><br><br>
      &nbsp;&nbsp;<b style="color:{GREEN};">① Ticket resolvido</b> → CSAT coletado automaticamente (1–5 estrelas)<br>
      &nbsp;&nbsp;<b style="color:{GREEN};">② CSAT ≥ 4 em casos SIM</b> → resposta marcada como positiva → entra na base de conhecimento ativa após revisão<br>
      &nbsp;&nbsp;<b style="color:{RED};">③ CSAT ≤ 2 em casos SIM</b> → flagged para revisão humana → classificação e resposta revisadas → threshold de confiança dessa categoria revisado<br>
      &nbsp;&nbsp;<b style="color:#1565C0;">④ Casos NÃO resolvidos por agente</b> → par (ticket, resolução) entra no pool de retreinamento com label validado<br>
      &nbsp;&nbsp;<b style="color:#7B1FA2;">⑤ Ciclo semanal de retreinamento</b> → novos pares adicionados → modelos de classificação retreinados → acurácia validada antes de ir para produção
    </div>

    <table style="margin-top:20px;">
      <thead><tr><th>Métrica monitorada</th><th>Frequência</th><th>Ação se degradar</th></tr></thead>
      <tbody>
        <tr><td>Acurácia do classificador Nível 1 (Ticket Type)</td><td>Semanal</td><td>Retreinamento com novos dados + revisão dos thresholds de confiança</td></tr>
        <tr><td>Taxa de SIM com CSAT ≥ 4</td><td>Diária</td><td>Abaixo de 75%: eleva threshold mínimo para 75%; revisão de templates ativos</td></tr>
        <tr><td>Taxa de automação geral</td><td>Semanal</td><td>Abaixo da meta: revisão das regras fixas + verificação de novos padrões de ticket</td></tr>
        <tr><td>TTR médio nos casos NÃO (resolvidos por agente)</td><td>Semanal</td><td>Aumento indica contexto insuficiente → revisar qualidade dos resumos gerados</td></tr>
        <tr><td>Volume de entradas novas na base de conhecimento</td><td>Quinzenal</td><td>Volume baixo = curadoria paralisada → revisão do processo com líderes de equipe</td></tr>
      </tbody>
    </table>

    <div class="insight positive">
      <strong>O efeito composto:</strong> na semana 1, o sistema comete mais erros e tem menos contexto. Na semana 12,
      com dados reais de CSAT e resoluções validadas, a acurácia cresce de forma mensurável. O modelo não é
      um ativo fixo — é um ativo que <em>aprecia com uso</em>.<br><br>
      <strong>O que fecha o loop:</strong> CSAT real (Fase 1) + tickets resolvidos com label de qualidade +
      ciclo semanal de revisão. Sem CSAT real, a retroalimentação não é possível — reforça a prioridade da Fase 1.
    </div>

    <h3 style="margin:28px 0 12px;">6. Pré-requisitos inegociáveis</h3>
    <div class="insight critical">
      <strong>CSAT real é pré-requisito para medir qualquer resultado.</strong><br>
      O dataset atual tem ratings estatisticamente aleatórios (Pearson r = -0.0035, F-stats todos &lt; 1.5) —
      impossível medir o impacto de qualquer melhoria sem coleta real de satisfação.
      A Fase 1 precisa incluir CSAT antes de qualquer investimento em IA.
    </div>
    <div class="insight">
      <strong>Cancellation request: nunca automatizar — sempre retenção humana.</strong><br>
      35.2% dos tickets de cancelamento estão pendentes. São o maior risco de churn da operação.
      Devem ir diretamente para agentes especializados em retenção com SLA máximo de 2h, com contexto completo do histórico do cliente.
    </div>

    <h3 style="margin:28px 0 12px;">7. Sobre o Protótipo Funcional (Entregável 3)</h3>
    <div class="insight">
      O protótipo é o arquivo <code><b>app.html</b></code> — abre diretamente no browser, sem instalação.<br><br>
      <b>O que demonstra:</b> os 3 caminhos completos do pipeline de decisão, passo a passo:<br>
      &nbsp;&nbsp;• <b>✅ SIM</b> — ticket classificado com alta confiança → <b>2 outputs simultâneos:</b>
        resposta automática enviada ao cliente + tarefa interna gerada para o operador executar o que foi prometido
        (para Billing, Refund e Technical — qualquer resposta com prazo de ação); CSAT → base de conhecimento<br>
      &nbsp;&nbsp;• <b>🟡 TALVEZ</b> — confiança moderada → perguntas de triagem enviadas → cliente responde → reclassificação → SIM ou NÃO<br>
      &nbsp;&nbsp;• <b>🔴 NÃO</b> — bloqueio por regra (cancelamento/crítico) → agente humano recebe resumo estruturado completo → atendimento → CSAT → ciclo de melhoria<br><br>
      <b>Para cada caminho, o protótipo mostra:</b> as etapas do pipeline em sequência, a decisão final, os outputs gerados (resposta ao cliente / perguntas de triagem / dashboard do agente / tarefa interna de execução) e o ciclo completo de fechamento — incluindo como cada ticket retroalimenta o sistema.<br><br>
      <b>Nota técnica:</b> a classificação usa regras semânticas PT/EN — explícitas e auditáveis — em vez de ML treinado em dado sintético.
      Os datasets do challenge foram gerados para análise de métricas operacionais, não para NLP
      (Ticket Subject com média de 15.7 chars; Ticket Description com templates não preenchidos).
      Em produção real, o classificador seria treinado nos tickets históricos da própria empresa.
      Esta decisão e sua justificativa estão documentadas no DEVLOG.
    </div>
  </div>

</div><!-- /container -->
</body>
</html>
"""

OUTPUT.write_text(html, encoding="utf-8")
print(f"[OK] diagnostico.html gerado em: {OUTPUT}")
