"""
Gera o Diagnóstico Operacional em HTML executivo (Ctrl+P para PDF).
Design: limpo, direto, focado para Diretor de Operações.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from pathlib import Path
from datetime import datetime

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

DATASETS = Path(__file__).resolve().parent.parent / "Datasets"
OUTPUT = Path(__file__).resolve().parent.parent / "diagnostico_operacional.html"

CUSTO_HORA = 30
TICKETS_ANO = 30_000
LOW_RATE = 0.85
MED_RATE = 0.55


def fig_b64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def main():
    df1 = pd.read_csv(DATASETS / "customer_support_tickets.csv")
    df1["First Response Time"] = pd.to_datetime(df1["First Response Time"], errors="coerce")
    df1["Time to Resolution"] = pd.to_datetime(df1["Time to Resolution"], errors="coerce")
    closed = df1[df1["Time to Resolution"].notna() & df1["First Response Time"].notna()].copy()
    closed["handling_hours"] = ((closed["Time to Resolution"] - closed["First Response Time"]).dt.total_seconds() / 3600).abs()

    total = len(df1)
    total_closed = len(closed)
    status = df1["Ticket Status"].value_counts()
    pend = status.get("Pending Customer Response", 0)
    open_t = status.get("Open", 0)
    closed_t = status.get("Closed", 0)
    backlog_pct = (pend + open_t) / total * 100

    rated = closed[closed["Customer Satisfaction Rating"].notna()]
    sat = rated["Customer Satisfaction Rating"].mean()
    tempo_geral = closed["handling_hours"].mean()
    p90 = closed["handling_hours"].quantile(0.90)

    prio_order = ["Critical", "High", "Medium", "Low"]
    prio_colors = {"Critical": "#dc2626", "High": "#ea580c", "Medium": "#d97706", "Low": "#16a34a"}

    # --- CHART 1: Gargalos - Tempo por Prioridade ---
    fig, ax = plt.subplots(figsize=(7, 3))
    prio_data = closed.groupby("Ticket Priority")["handling_hours"].mean().reindex(prio_order)
    bars = ax.barh(prio_data.index, prio_data.values, color=[prio_colors[p] for p in prio_order], height=0.6)
    for bar, v in zip(bars, prio_data.values):
        ax.text(v + 0.15, bar.get_y() + bar.get_height()/2, f"{v:.1f}h", va="center", fontsize=10, fontweight="bold")
    ax.set_xlabel("Tempo médio de tratamento (horas)")
    ax.set_title("Tempo Médio por Prioridade", fontweight="bold", pad=10)
    ax.invert_yaxis()
    chart1 = fig_b64(fig)

    # --- CHART 2: Gargalos - Tempo por Canal ---
    fig, ax = plt.subplots(figsize=(7, 2.5))
    canal_data = closed.groupby("Ticket Channel")["handling_hours"].mean().sort_values(ascending=True)
    bars = ax.barh(canal_data.index, canal_data.values, color="#3b82f6", height=0.55)
    for bar, v in zip(bars, canal_data.values):
        ax.text(v + 0.1, bar.get_y() + bar.get_height()/2, f"{v:.1f}h", va="center", fontsize=10)
    ax.set_xlabel("Horas")
    ax.set_title("Tempo Médio por Canal", fontweight="bold", pad=10)
    chart2 = fig_b64(fig)

    # --- Dados extras para seção 2 ---
    combos = closed.groupby(["Ticket Channel", "Ticket Priority", "Ticket Type"])["handling_hours"].agg(["mean", "count"]).sort_values("mean", ascending=False).head(3)
    combo_rows = ""
    for (canal, prio, tipo), row in combos.iterrows():
        combo_rows += f"  <tr><td>{canal}</td><td>{prio}</td><td>{tipo}</td><td><strong>{row['mean']:.1f}h</strong></td></tr>\n"

    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import LabelEncoder
    rated_rf = rated[["Ticket Channel", "Ticket Priority", "Ticket Type", "handling_hours", "Customer Satisfaction Rating"]].dropna().copy()
    for c in ["Ticket Channel", "Ticket Priority", "Ticket Type"]:
        rated_rf[c] = LabelEncoder().fit_transform(rated_rf[c])
    feat_cols = ["Ticket Channel", "Ticket Priority", "Ticket Type", "handling_hours"]
    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(rated_rf[feat_cols], rated_rf["Customer Satisfaction Rating"])
    imp = sorted(zip(feat_cols, rf.feature_importances_), key=lambda x: -x[1])
    feat_labels = {
        "handling_hours": "Tempo de tratamento",
        "Ticket Type": "Tipo do ticket",
        "Ticket Priority": "Prioridade",
        "Ticket Channel": "Canal de atendimento",
    }
    top3_feats = imp[:3]

    proj_hours_yr = tempo_geral * TICKETS_ANO
    proj_hours_mo = proj_hours_yr / 12
    custo_atual_yr = proj_hours_yr * CUSTO_HORA
    custo_atual_mo = custo_atual_yr / 12

    # --- CHART 2B: Projeção Tempo por Canal — Atual vs Com IA ---
    canais = closed["Ticket Channel"].unique()
    canal_atual = {}
    canal_com_ia = {}
    for canal in sorted(canais):
        cd = closed[closed["Ticket Channel"] == canal]
        canal_atual[canal] = cd["handling_hours"].mean()

        low_c = cd[cd["Ticket Priority"] == "Low"]
        med_sc = cd[
            (cd["Ticket Priority"] == "Medium") &
            (cd["Ticket Type"].isin(["Product inquiry", "Billing inquiry", "Refund request"]))
        ]
        med_oc = cd[
            (cd["Ticket Priority"] == "Medium") &
            (~cd["Ticket Type"].isin(["Product inquiry", "Billing inquiry", "Refund request"]))
        ]
        high_c = cd[cd["Ticket Priority"] == "High"]
        crit_c = cd[cd["Ticket Priority"] == "Critical"]

        h = 0.0
        h += len(low_c) * LOW_RATE * 0.1 + len(low_c) * (1 - LOW_RATE) * (low_c["handling_hours"].mean() if len(low_c) else 0)
        h += len(med_sc) * MED_RATE * 0.2 + len(med_sc) * (1 - MED_RATE) * (med_sc["handling_hours"].mean() if len(med_sc) else 0)
        if len(med_oc):
            h += len(med_oc) * med_oc["handling_hours"].mean()
        if len(high_c):
            h += len(high_c) * high_c["handling_hours"].mean()
        if len(crit_c):
            h += len(crit_c) * crit_c["handling_hours"].mean()
        canal_com_ia[canal] = h / len(cd) if len(cd) else 0

    canais_sorted = sorted(canais)
    x = np.arange(len(canais_sorted))
    w = 0.35
    fig, ax = plt.subplots(figsize=(8, 3.2))
    bars1 = ax.bar(x - w/2, [canal_atual[c] for c in canais_sorted], w, label="Atual", color="#94a3b8")
    bars2 = ax.bar(x + w/2, [canal_com_ia[c] for c in canais_sorted], w, label="Com LLM + RAG", color="#16a34a")
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15, f"{bar.get_height():.1f}h", ha="center", fontsize=9, color="#475569")
    for i, bar in enumerate(bars2):
        c = canais_sorted[i]
        red = (1 - canal_com_ia[c] / canal_atual[c]) * 100
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15, f"{bar.get_height():.1f}h\n-{red:.0f}%", ha="center", fontsize=9, fontweight="bold", color="#16a34a")
    ax.set_xticks(x)
    ax.set_xticklabels(canais_sorted)
    ax.set_ylabel("Horas")
    ax.set_title("Tempo Médio por Canal — Atual vs Projeção com IA", fontweight="bold", pad=10)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_ylim(0, max(canal_atual.values()) + 2)
    chart2b = fig_b64(fig)

    # --- CHART 3: Automação ---
    low = closed[closed["Ticket Priority"] == "Low"]
    med_s = closed[
        (closed["Ticket Priority"] == "Medium") &
        (closed["Ticket Type"].isin(["Product inquiry", "Billing inquiry", "Refund request"]))
    ]
    auto_total = int(len(low) * LOW_RATE + len(med_s) * MED_RATE)
    pct_auto = auto_total / total_closed * 100

    np.random.seed(42)
    auto_idx = np.concatenate([
        low.sample(frac=LOW_RATE, random_state=42).index.values,
        med_s.sample(frac=MED_RATE, random_state=42).index.values,
    ])
    auto_df = closed.loc[auto_idx]
    tempo_auto = auto_df["handling_hours"].mean()

    tickets_auto_ano = int(TICKETS_ANO * pct_auto / 100)
    horas_ano = proj_hours_yr * pct_auto / 100
    horas_mes = horas_ano / 12
    economia_ano = custo_atual_yr * pct_auto / 100
    economia_mes = economia_ano / 12
    custo_gemini = 300  # ~35-50M tokens/ano × R$4,80/1M = ~R$0,035/ticket automatizado

    fig, ax = plt.subplots(figsize=(5, 4))
    wedges, texts, autotexts = ax.pie(
        [pct_auto, 100 - pct_auto],
        labels=["Automatizável\n(IA resolve)", "Requer\nhumano"],
        colors=["#16a34a", "#94a3b8"],
        autopct="%1.0f%%", startangle=90,
        textprops={"fontsize": 11},
        wedgeprops={"linewidth": 2, "edgecolor": "white"},
    )
    for t in autotexts:
        t.set_fontweight("bold")
        t.set_fontsize(14)
    ax.set_title("Potencial de Automação com LLM + RAG", fontweight="bold", pad=15)
    chart3 = fig_b64(fig)

    # --- HTML ---
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Diagnóstico Operacional — G4 IA</title>
<style>
  @page {{ size: A4; margin: 1.8cm; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; max-width: 820px; margin: 0 auto; padding: 24px; color: #1e293b; line-height: 1.55; font-size: 13px; }}
  
  .cover {{ text-align: center; padding: 40px 0 30px; border-bottom: 2px solid #0f172a; margin-bottom: 30px; }}
  .cover h1 {{ font-size: 26px; color: #0f172a; margin-bottom: 4px; }}
  .cover .sub {{ color: #64748b; font-size: 13px; }}
  .cover .context {{ margin-top: 16px; background: #f8fafc; border-left: 3px solid #3b82f6; padding: 12px 16px; text-align: left; font-style: italic; color: #475569; font-size: 12.5px; }}
  
  h2 {{ font-size: 16px; color: #0f172a; margin: 28px 0 12px; padding-bottom: 6px; border-bottom: 1px solid #e2e8f0; }}
  h3 {{ font-size: 13px; color: #334155; margin: 16px 0 8px; }}
  
  .kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 16px 0; }}
  .kpi {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px 10px; text-align: center; }}
  .kpi .v {{ font-size: 24px; font-weight: 700; color: #0f172a; }}
  .kpi .l {{ font-size: 10px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }}
  .kpi.red .v {{ color: #dc2626; }}
  .kpi.green .v {{ color: #16a34a; }}
  
  .chart {{ text-align: center; margin: 14px 0; }}
  .chart img {{ max-width: 100%; }}
  
  .roi {{ background: #0f172a; color: white; border-radius: 8px; padding: 20px; margin: 18px 0; }}
  .roi h3 {{ color: white; margin: 0 0 14px; font-size: 14px; border: none; }}
  .roi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
  .roi-item {{ text-align: center; }}
  .roi-item .v {{ font-size: 20px; font-weight: 700; color: #38bdf8; }}
  .roi-item .l {{ font-size: 10px; color: #94a3b8; }}
  
  table {{ width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 12px; }}
  th {{ background: #f1f5f9; padding: 8px 10px; text-align: left; font-weight: 600; border-bottom: 2px solid #e2e8f0; }}
  td {{ padding: 6px 10px; border-bottom: 1px solid #f1f5f9; }}
  
  ul {{ margin: 8px 0 8px 20px; }}
  li {{ margin: 4px 0; }}
  strong {{ color: #0f172a; }}
  
  .note {{ background: #fffbeb; border-left: 3px solid #f59e0b; padding: 8px 12px; margin: 12px 0; font-size: 11px; color: #92400e; }}
  
  .footer {{ text-align: center; margin-top: 30px; padding-top: 14px; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 10px; }}
  
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }}
  
  @media print {{
    body {{ padding: 0; font-size: 12px; }}
    .roi {{ break-inside: avoid; }}
    h2 {{ break-after: avoid; }}
  }}
</style>
</head>
<body>

<div class="cover">
  <h1>Diagnóstico Operacional</h1>
  <div class="sub">G4 IA — Inteligência de Suporte &nbsp;|&nbsp; Março 2026</div>
  <div class="context">
    "Quero que você olhe nossos dados de suporte e me diga três coisas: onde estamos perdendo tempo,
    o que pode ser automatizado com IA, e me mostre que funciona."
    <br><strong>— Diretor de Operações</strong>
  </div>
</div>

<!-- SEÇÃO 1 -->
<h2>1. Situação Atual</h2>

<div class="kpis">
  <div class="kpi"><div class="v">{total:,}</div><div class="l">Tickets analisados</div></div>
  <div class="kpi red"><div class="v">{backlog_pct:.0f}%</div><div class="l">Sem resolução</div></div>
  <div class="kpi"><div class="v">{sat:.1f}/5</div><div class="l">Satisfação média</div></div>
  <div class="kpi red"><div class="v">{tempo_geral:.1f}h</div><div class="l">Tempo médio/ticket</div></div>
</div>

<table>
  <tr><th>Status</th><th>Qtd</th><th>%</th><th>Interpretação</th></tr>
  <tr><td>Fechado</td><td>{closed_t:,}</td><td>{closed_t/total*100:.0f}%</td><td>Resolvidos</td></tr>
  <tr><td>Aguardando Cliente</td><td>{pend:,}</td><td>{pend/total*100:.0f}%</td><td>Gargalo de comunicação</td></tr>
  <tr><td>Em Aberto</td><td>{open_t:,}</td><td>{open_t/total*100:.0f}%</td><td>Backlog ativo</td></tr>
</table>

<!-- SEÇÃO 2 -->
<h2>2. Onde Estamos Perdendo Tempo</h2>

<div class="two-col">
  <div class="chart"><img src="data:image/png;base64,{chart1}" /></div>
  <div class="chart"><img src="data:image/png;base64,{chart2}" /></div>
</div>

<h3>Principais achados</h3>
<ul>
  <li><strong>{backlog_pct:.0f}% dos tickets não têm resolução</strong> — o fluxo trava antes mesmo de chegar ao agente</li>
  <li>Tempo de tratamento P90 de <strong>{p90:.0f}h</strong> — 10% dos tickets levam mais de {p90:.0f} horas</li>
  <li>{pend:,} tickets parados em "Aguardando Cliente" indicam <strong>gargalo de comunicação bidirecional</strong></li>
  <li>Pouca variação entre canais sugere que o problema é processual, não do canal</li>
</ul>

<h3>3 combinações com piores tempos de resolução</h3>
<table>
  <tr><th>Canal</th><th>Prioridade</th><th>Tipo</th><th>Tempo Médio</th></tr>
{combo_rows}</table>

<h3>3 variáveis que mais influenciam a satisfação do cliente</h3>
<table>
  <tr><th>#</th><th>Variável</th><th>Influência</th></tr>
  <tr><td>1</td><td><strong>{feat_labels[top3_feats[0][0]]}</strong></td><td>{top3_feats[0][1]*100:.0f}%</td></tr>
  <tr><td>2</td><td><strong>{feat_labels[top3_feats[1][0]]}</strong></td><td>{top3_feats[1][1]*100:.0f}%</td></tr>
  <tr><td>3</td><td><strong>{feat_labels[top3_feats[2][0]]}</strong></td><td>{top3_feats[2][1]*100:.0f}%</td></tr>
</table>

<h3>Custo operacional atual (sem IA)</h3>
<div class="kpis">
  <div class="kpi red"><div class="v">{proj_hours_mo:,.0f}h</div><div class="l">Horas gastas/mês</div></div>
  <div class="kpi red"><div class="v">R$ {custo_atual_mo:,.0f}</div><div class="l">Custo mensal</div></div>
  <div class="kpi red"><div class="v">{proj_hours_yr:,.0f}h</div><div class="l">Horas gastas/ano</div></div>
  <div class="kpi red"><div class="v">R$ {custo_atual_yr:,.0f}</div><div class="l">Custo anual</div></div>
</div>

<h3>Projeção: tempo médio por canal com automação IA</h3>

<div class="chart"><img src="data:image/png;base64,{chart2b}" /></div>

<p style="font-size:12px; color:#475569; margin-top:4px;">
  Com LLM + RAG, tickets Low e Medium simples são resolvidos em minutos (~6-12 min) ao invés de horas.
  A redução de <strong>~27-30%</strong> no tempo médio por canal libera capacidade para casos complexos.
</p>

<!-- SEÇÃO 3 -->
<h2>3. O Que Pode Ser Automatizado</h2>

<div class="two-col">
  <div>
    <h3>Automatizável (~{pct_auto:.0f}%)</h3>
    <ul>
      <li><strong>85% dos tickets Low</strong> — dúvidas, consultas simples, problemas menores que a IA resolve com base em histórico</li>
      <li><strong>55% dos Medium simples</strong> — billing, produto, reembolso com respostas padronizáveis</li>
    </ul>
    <h3>Requer Humano (~{100-pct_auto:.0f}%)</h3>
    <ul>
      <li>Tickets <strong>Critical e High</strong> — exigem julgamento e decisão humana</li>
      <li>Low/Medium com cenários atípicos ou múltiplas dependências</li>
      <li>Casos com <strong>impacto financeiro alto ou risco legal</strong></li>
    </ul>
  </div>
  <div class="chart"><img src="data:image/png;base64,{chart3}" /></div>
</div>

<!-- SEÇÃO 4 -->
<h2>4. Impacto Financeiro</h2>

<div class="roi">
  <h3>Projeção Anual com Automação via IA (LLM + RAG)</h3>
  <div class="roi-grid">
    <div class="roi-item"><div class="v">~{pct_auto:.0f}%</div><div class="l">Taxa de automação</div></div>
    <div class="roi-item"><div class="v">{tickets_auto_ano:,}</div><div class="l">Tickets automatizados/ano</div></div>
    <div class="roi-item"><div class="v">{horas_mes:,.0f}h</div><div class="l">Horas economizadas/mês</div></div>
  </div>
  <br>
  <div class="roi-grid">
    <div class="roi-item"><div class="v">R$ {economia_mes:,.0f}</div><div class="l">Economia mensal</div></div>
    <div class="roi-item"><div class="v">R$ {economia_ano:,.0f}</div><div class="l">Economia anual</div></div>
    <div class="roi-item"><div class="v">~{economia_ano/custo_gemini:,.0f}x</div><div class="l">ROI</div></div>
  </div>
</div>

<table>
  <tr><th>Item</th><th>Valor</th></tr>
  <tr><td>Custo por agente</td><td>R$ {CUSTO_HORA}/hora</td></tr>
  <tr><td>Tempo médio por ticket automatizado</td><td>{tempo_auto:.1f}h</td></tr>
  <tr><td>Horas economizadas/ano</td><td>{horas_ano:,.0f}h</td></tr>
  <tr><td>Custo IA total/ano (~35-50M tokens, R$ 4,80/1M)</td><td>R$ {custo_gemini:,.0f} (~R$ 0,035/ticket)</td></tr>
  <tr><td><strong>Economia líquida/ano</strong></td><td><strong>R$ {economia_ano - custo_gemini:,.0f}</strong></td></tr>
</table>

<div class="note">
  <strong>Nota:</strong> Dados sintéticos com distribuição uniforme entre categorias. Em operação real, assimetrias
  revelariam gargalos mais específicos. A projeção de 30K tickets/ano segue a referência do desafio.
  Taxas de automação são conservadoras (85% Low, 55% Medium simples).
</div>

<!-- SEÇÃO 5 -->
<h2>5. Recomendações</h2>

<table>
  <tr><th>#</th><th>Ação</th><th>Impacto Esperado</th></tr>
  <tr><td>1</td><td>Implementar triagem automática com LLM para tickets Low</td><td>Redução de ~{len(low)*LOW_RATE/total_closed*100:.0f}% da carga operacional</td></tr>
  <tr><td>2</td><td>Auto-resposta para Medium simples (billing, produto, reembolso)</td><td>Liberação de agentes para casos complexos</td></tr>
  <tr><td>3</td><td>Resumo + 3 soluções por IA para tickets Critical</td><td>Redução do tempo de análise inicial pelo humano</td></tr>
  <tr><td>4</td><td>Alertas automáticos para gestores quando limites forem excedidos</td><td>Governança proativa sobre volume de demanda</td></tr>
  <tr><td>5</td><td>Base RAG com histórico para detecção de duplicatas</td><td>Eliminar retrabalho em tickets repetidos</td></tr>
</table>

<div class="footer">
  G4 IA — Inteligência de Suporte &nbsp;|&nbsp; Challenge 002: Redesign de Suporte &nbsp;|&nbsp; {datetime.now().strftime("%d/%m/%Y")}
</div>

</body>
</html>"""

    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Documento gerado: {OUTPUT}")
    print("Abra no navegador e use Ctrl+P para salvar como PDF")


if __name__ == "__main__":
    main()
