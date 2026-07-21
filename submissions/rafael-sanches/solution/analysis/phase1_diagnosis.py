"""
FASE 1 — Diagnostico operacional do Dataset 1.
Transforma os achados da Fase 0 em 4 graficos executivos + resumo estruturado.
Estrutura da narrativa: 3 perguntas do Diretor -> teste -> resultado (nulo) -> 1 fato solido.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy import stats

D1 = r"D:\Projetos\Case G4\data\challenge-002-support\customer_support_tickets.csv"
FIG = r"D:\Projetos\Case G4\solution-draft\figures"
df = pd.read_csv(D1)

# Paleta: cinza = contexto, azul = neutro, vermelho = alerta/impossivel
INK, GRID, NEUTRAL, ALERT, GOOD = "#1a1a1a", "#e6e6e6", "#4C72B0", "#C44E52", "#55A868"
plt.rcParams.update({
    "figure.dpi": 130, "font.size": 11, "axes.edgecolor": "#888",
    "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
})

def save(fig, name):
    fig.tight_layout()
    fig.savefig(f"{FIG}\\{name}", bbox_inches="tight")
    plt.close(fig)
    print(f"  [salvo] {name}")


# --- GRAFICO 1: Backlog (status) ------------------------------------------
status = df["Ticket Status"].value_counts().reindex(["Open", "Pending Customer Response", "Closed"])
fig, ax = plt.subplots(figsize=(7, 3.2))
colors = [ALERT, ALERT, GOOD]
bars = ax.barh(["Aberto", "Aguardando cliente", "Resolvido"], status.values, color=colors)
for b, v in zip(bars, status.values):
    ax.text(v + 40, b.get_y() + b.get_height()/2, f"{v}  ({v/len(df)*100:.0f}%)", va="center", fontsize=10)
ax.set_title("Apenas 1 em cada 3 tickets chega a 'Resolvido'", fontweight="bold", loc="left")
ax.set_xlabel(f"Tickets (total = {len(df):,})".replace(",", "."))
ax.set_xlim(0, status.max()*1.25)
save(fig, "01_backlog.png")

# --- GRAFICO 2: CSAT por fator (achatado, escala cheia 1-5) ----------------
c = df[df["Customer Satisfaction Rating"].notna()]
gmean = c["Customer Satisfaction Rating"].mean()
fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
for ax, col, titulo in zip(axes, ["Ticket Channel", "Ticket Priority", "Ticket Type"],
                           ["Canal", "Prioridade", "Tipo"]):
    m = c.groupby(col)["Customer Satisfaction Rating"].mean()
    ax.bar(range(len(m)), m.values, color=NEUTRAL)
    ax.axhline(gmean, color=ALERT, ls="--", lw=1.2)
    ax.set_xticks(range(len(m)))
    ax.set_xticklabels([str(x)[:10] for x in m.index], rotation=35, ha="right", fontsize=8)
    ax.set_title(titulo, fontsize=10)
    ax.set_ylim(0, 5)
axes[0].set_ylabel("CSAT medio (1-5)")
sp = c.groupby("Ticket Priority")["Customer Satisfaction Rating"].mean()
fig.suptitle(f"Nada move a satisfacao: toda barra fica em ~{gmean:.1f}  "
             f"(variacao max entre grupos < { (sp.max()-sp.min()):.2f} ponto)",
             fontweight="bold", x=0.02, ha="left")
save(fig, "02_csat_flat.png")

# --- GRAFICO 3: "Duracao" TTR - FRT (49% negativas) ------------------------
closed = df[df["Ticket Status"] == "Closed"].copy()
dur = (pd.to_datetime(closed["Time to Resolution"], errors="coerce")
       - pd.to_datetime(closed["First Response Time"], errors="coerce")).dt.total_seconds()/3600
neg_pct = (dur < 0).mean()*100
fig, ax = plt.subplots(figsize=(7.5, 3.6))
bins = np.linspace(-24, 24, 49)
ax.hist(dur[dur >= 0], bins=bins, color=GOOD, label="Coerente (resolve depois de responder)")
ax.hist(dur[dur < 0], bins=bins, color=ALERT, label=f"IMPOSSIVEL: resolve antes de responder — {neg_pct:.0f}%")
ax.axvline(0, color=INK, lw=1)
ax.set_title("A metrica de tempo esta corrompida", fontweight="bold", loc="left")
ax.set_xlabel("'Tempo de resolucao' calculado (horas)")
ax.set_ylabel("Tickets")
ax.legend(fontsize=8.5, loc="upper left")
save(fig, "03_duracao_corrompida.png")

# --- GRAFICO 4: Uniformidade (volume por fator) ----------------------------
fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
for ax, col, titulo in zip(axes, ["Ticket Type", "Ticket Priority", "Ticket Channel"],
                           ["Tipo", "Prioridade", "Canal"]):
    v = df[col].value_counts()
    obs = v.values; exp = np.full(len(obs), len(df)/len(obs))
    _, p = stats.chisquare(obs, exp)
    ax.bar(range(len(v)), v.values, color=NEUTRAL)
    ax.axhline(len(df)/len(v), color=ALERT, ls="--", lw=1.2)
    ax.set_xticks(range(len(v)))
    ax.set_xticklabels([str(x)[:9] for x in v.index], rotation=35, ha="right", fontsize=8)
    ax.set_title(f"{titulo}  (p={p:.2f})", fontsize=10)
fig.suptitle("Volume identico entre categorias — nao ha gargalo concentrado (linha = uniforme perfeito)",
             fontweight="bold", x=0.02, ha="left")
save(fig, "04_uniformidade.png")

# --- RESUMO NUMERICO -------------------------------------------------------
print("\n" + "="*80)
print("RESUMO NUMERICO — DIAGNOSTICO")
print("="*80)
print(f"Total de tickets: {len(df)}")
print(f"Resolvidos: {(df['Ticket Status']=='Closed').sum()} ({(df['Ticket Status']=='Closed').mean()*100:.1f}%)")
print(f"Backlog (nao resolvido): {(df['Ticket Status']!='Closed').sum()} ({(df['Ticket Status']!='Closed').mean()*100:.1f}%)")
print(f"CSAT medio: {gmean:.2f} | R2 de todos os fatores: 0.003 (Fase 0)")
print(f"Duracao negativa (impossivel): {neg_pct:.1f}% dos tickets resolvidos")
print(f"Janela temporal total dos dados: {pd.to_datetime(df['First Response Time'],errors='coerce').min()} a {pd.to_datetime(df['Time to Resolution'],errors='coerce').max()}")
print("="*80)
