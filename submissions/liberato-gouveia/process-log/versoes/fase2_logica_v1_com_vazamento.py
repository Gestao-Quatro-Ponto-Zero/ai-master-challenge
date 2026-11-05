"""Fase 2: lógica do score. Curva oficial, simulação nos dados reais e teste de volta no tempo.

Uso: python3 fase2_logica.py <pasta_dos_dados> <pasta_resultados> <pasta_graficos>

Regra anti-vazamento: na data de corte, a lógica só usa o que se sabia ATÉ aquela data.
Os desfechos posteriores ao corte servem apenas para avaliar o resultado.
"""
import sys
import numpy as np
import pandas as pd

D, OUT, GRAF = sys.argv[1], sys.argv[2], sys.argv[3]

# ------------------------------------------------------------------ configuração
# Limites PROVISÓRIOS para a simulação; os valores finais são decisão do Liberato.
CONFIG = {
    "limite_ciclo_dias": 138,         # maior ciclo já observado num deal fechado
    "valor_minimo_foco": 100,         # US$; abaixo disso o deal vai para "Automatizar"
    "valor_deal_grande": 1000,        # US$; na lista de requalificação, define "ligar" x "encerrar"
    "inicio_observacao": "2017-03-01",  # primeiro dia com fechamentos registrados na base
}

p = pd.read_csv(f"{D}/sales_pipeline.csv")
a = pd.read_csv(f"{D}/accounts.csv")
pr = pd.read_csv(f"{D}/products.csv")
t = pd.read_csv(f"{D}/sales_teams.csv")
p["product"] = p["product"].replace("GTXPro", "GTX Pro")  # erro de digitação da base oficial
for c in ["engage_date", "close_date"]:
    p[c] = pd.to_datetime(p[c])
p = p.merge(pr, on="product", how="left").merge(t, on="sales_agent", how="left").merge(a, on="account", how="left")
assert p.sales_price.notna().all(), "há deal sem preço depois do join"

LIM = CONFIG["limite_ciclo_dias"]
log = open(f"{OUT}/fase2_resultados.txt", "w", encoding="utf-8")
def out(*x):
    print(*x); print(*x, file=log)
def titulo(x):
    out("\n" + "=" * 72 + f"\n{x}\n" + "=" * 72)


def curva_chance(dados, corte):
    """Chance de ser ganho para um deal ainda aberto com 'a' dias, usando só o que se sabia em 'corte'.
    Safra = deals iniciados entre o início da observação e (corte - limite - 1 dia),
    para que todo desfecho possível já fosse conhecido na data de corte."""
    corte = pd.Timestamp(corte)
    ini = pd.Timestamp(CONFIG["inicio_observacao"])
    fim = corte - pd.Timedelta(days=LIM + 1)
    s = dados[(dados.engage_date >= ini) & (dados.engage_date <= fim)].copy()
    fechou = s.close_date.notna() & (s.close_date <= corte)
    ciclo = (s.close_date - s.engage_date).dt.days.where(fechou)
    ganho = fechou & (s.deal_stage == "Won")
    linhas = []
    for idade in range(0, LIM + 1):
        vivo = ciclo.isna() | (ciclo >= idade)
        linhas.append((idade, int(vivo.sum()), float(ganho[vivo].mean())))
    cur = pd.DataFrame(linhas, columns=["idade_dias", "n_vivos", "chance_ganho"])
    return cur, (ini.date(), fim.date(), len(s))


def classificar(abertos, curva):
    """Aplica as 4 listas a deals abertos. Espera colunas: idade_dias (NaN em prospecção), sales_price."""
    ch = curva.set_index("idade_dias").chance_ganho
    df = abertos.copy()
    df["chance"] = df.idade_dias.map(ch)  # NaN acima do limite e em prospecção
    df["valor_esperado"] = df.chance * df.sales_price
    cond_prosp = df.deal_stage == "Prospecting"
    cond_zumbi = (~cond_prosp) & (df.idade_dias > LIM)
    cond_baixo = (~cond_prosp) & (~cond_zumbi) & (df.sales_price < CONFIG["valor_minimo_foco"])
    df["lista"] = np.select([cond_prosp, cond_zumbi, cond_baixo], ["3. Iniciar contato", "2. Requalificar ou encerrar", "4. Automatizar"], "1. Foco")
    df["acao"] = np.select(
        [df.lista == "1. Foco", cond_zumbi & (df.sales_price >= CONFIG["valor_deal_grande"]), cond_zumbi, cond_prosp, cond_baixo],
        ["Avançar este deal", "Ligar para requalificar", "Encerrar no CRM", "Fazer o primeiro contato", "Incluir na cadência automática"], "")
    df["aviso"] = np.where(df.account.isna(), "Empresa não cadastrada: complete o cadastro", "")
    return df


def porque(r):
    if r.lista == "1. Foco":
        return (f"Valor esperado US$ {r.valor_esperado:,.0f} = US$ {r.sales_price:,.0f} ({r['product']}) × "
                f"{r.chance:.0%} (chance de um deal com {int(r.idade_dias)} dias)").replace(",", ".")
    if r.lista == "2. Requalificar ou encerrar":
        return f"Aberto há {int(r.idade_dias)} dias. Nenhum deal da história fechou depois de {LIM} dias."
    if r.lista == "3. Iniciar contato":
        return f"Em prospecção: não há histórico para estimar a chance. Ordenado pelo valor (US$ {r.sales_price:,.0f}).".replace(",", ".")
    return f"Valor US$ {r.sales_price:,.0f} abaixo do mínimo de US$ {CONFIG['valor_minimo_foco']} para atenção individual.".replace(",", ".")


# ------------------------------------------------------------------ 1) curva oficial (hoje = 31/12/2017)
titulo("1) Curva oficial: chance de ser ganho pela idade atual (hoje = 31/12/2017)")
HOJE = pd.Timestamp("2017-12-31")
curva, info = curva_chance(p, HOJE)
out(f"Safra usada: deals iniciados de {info[0]} a {info[1]} ({info[2]} deals)")
out(f"Configuração provisória: {CONFIG}")
curva.to_csv(f"{OUT}/fase2_curva_chance.csv", index=False)
for idade in [0, 7, 14, 21, 30, 45, 60, 75, 90, 100, 110, 120, 130, 138]:
    r = curva.iloc[idade]
    out(f"  deal com {idade:>3} dias: chance {r.chance_ganho:6.1%}  (base: {r.n_vivos} deals vivos nessa idade)")

# ------------------------------------------------------------------ 2) simulação nos dados reais
titulo("2) Simulação nos dados reais (hoje = 31/12/2017)")
ab = p[p.deal_stage.isin(["Engaging", "Prospecting"])].copy()
ab["idade_dias"] = (HOJE - ab.engage_date).dt.days
res = classificar(ab, curva)
res["porque"] = res.apply(porque, axis=1)
resumo = res.groupby("lista").agg(deals=("opportunity_id", "size"), valor_tabela=("sales_price", "sum"),
                                  sem_empresa=("account", lambda s: int(s.isna().sum())))
out(resumo.to_string())
out("\nAções na lista 2:", res[res.lista.str.startswith("2")].acao.value_counts().to_dict())

out("\nImpacto do 'valor mínimo do foco' (deals vivos até 138 dias):")
vivos = res[(res.deal_stage == "Engaging") & (res.idade_dias <= LIM)]
for v in [100, 600, 1100]:
    out(f"  mínimo US$ {v:>5}: Foco {int((vivos.sales_price >= v).sum()):>3} deals | Automatizar {int((vivos.sales_price < v).sum()):>3} deals")
out("Impacto do 'deal grande' na lista de requalificação:")
zum = res[res.lista.str.startswith("2")]
for v in [1000, 3000, 5000]:
    out(f"  grande >= US$ {v:>5}: ligar {int((zum.sales_price >= v).sum()):>4} | encerrar {int((zum.sales_price < v).sum()):>4}")

foco = res[res.lista == "1. Foco"].copy()
foco["nota_0_100"] = (foco.valor_esperado.rank(pct=True) * 100).round().astype(int)
res = res.merge(foco[["opportunity_id", "nota_0_100"]], on="opportunity_id", how="left")
res.to_csv(f"{OUT}/fase2_deals_classificados.csv", index=False)

out("\nFoco por vendedor (deals):", foco.groupby("sales_agent").size().describe().round(1).to_dict())
exemplo = foco.groupby("sales_agent").size().idxmax()
out(f"\nExemplo: top 5 do Foco de {exemplo}")
for _, r in foco[foco.sales_agent == exemplo].sort_values("valor_esperado", ascending=False).head(5).iterrows():
    out(f"  [{r.opportunity_id}] nota {int(r.nota_0_100)} | {porque(r)}" + (f" | ⚠ {r.aviso}" if r.aviso else ""))
for lista in ["2. Requalificar ou encerrar", "3. Iniciar contato", "4. Automatizar"]:
    sub = res[(res.sales_agent == exemplo) & (res.lista == lista)].sort_values(["valor_esperado", "sales_price"], ascending=False)
    if len(sub):
        r = sub.iloc[0]
        out(f"  {lista}: {len(sub)} deals. 1º: [{r.opportunity_id}] {r.acao} | {r.porque}")

# ------------------------------------------------------------------ 3) teste de volta no tempo
titulo("3) Teste de volta no tempo: 'hoje' = 30/09/2017, resultado conferido até 31/12/2017")
CORTE = pd.Timestamp("2017-09-30")
curva_c, info_c = curva_chance(p, CORTE)
out(f"Curva montada só com dados até {CORTE.date()}: safra {info_c[0]} a {info_c[1]} ({info_c[2]} deals)")
# deals em negociação na data de corte (prospecção não tem data, então não dá para saber quem existia)
pool = p[(p.engage_date <= CORTE) & (p.close_date.isna() | (p.close_date > CORTE))].copy()
pool["idade_dias"] = (CORTE - pool.engage_date).dt.days
pool["ganhou_depois"] = (pool.deal_stage == "Won") & (pool.close_date <= HOJE)
pool["receita_depois"] = np.where(pool.ganhou_depois, pool.close_value, 0.0)
receita_total = pool.receita_depois.sum()
out(f"Deals em negociação em 30/09: {len(pool)} | com mais de {LIM} dias: {(pool.idade_dias > LIM).sum()}")
out(f"Receita ganha por eles até 31/12: US$ {receita_total:,.0f}".replace(",", "."))

# estratégia "óbvia": taxa de ganho histórica (só deals fechados até o corte) de produto, setor e vendedor
fech_c = p[p.close_date.notna() & (p.close_date <= CORTE)].assign(w=lambda d: (d.deal_stage == "Won").astype(float))
media_c = fech_c.w.mean()
tx = {col: fech_c.groupby(col).w.mean() for col in ["product", "sector", "sales_agent"]}
pool["chance_obvia"] = pool[["product", "sector", "sales_agent"]].apply(
    lambda r: np.nanmean([tx[c].get(r[c], np.nan) for c in tx]) if any(pd.notna(r[c]) for c in tx) else media_c, axis=1)
pool["chance_idade"] = pool.idade_dias.map(curva_c.set_index("idade_dias").chance_ganho).fillna(0.0)

estrategias = {
    "Nossa lógica (chance pela idade × valor)": pool.chance_idade * pool.sales_price,
    "Só valor (preço de tabela)": pool.sales_price.astype(float),
    "Lógica 'óbvia' (taxa de produto/setor/vendedor × valor)": pool.chance_obvia * pool.sales_price,
    "Lógica 'óbvia' sem valor (só taxa de produto/setor/vendedor)": pool.chance_obvia,
}
rng = np.random.default_rng(42)
N_TOP = int(round(len(pool) * 0.2))
linhas = []
for nome, score in estrategias.items():
    caps, wrs, zs, cap_vend = [], [], [], []
    for _ in range(300):  # desempate aleatório repetido: muitos deals têm a mesma nota
        s = score.values + rng.uniform(0, 1e-6, len(pool))
        top = pool.iloc[np.argsort(-s)[:N_TOP]]
        caps.append(top.receita_depois.sum() / receita_total)
        wrs.append(top.ganhou_depois.mean())
        zs.append((top.idade_dias > LIM).mean())
        tmp = pool.assign(s=s).sort_values("s", ascending=False).groupby("sales_agent").head(10)
        cap_vend.append(tmp.receita_depois.sum() / receita_total)
    linhas.append((nome, np.mean(caps), np.mean(wrs), np.mean(zs), np.mean(cap_vend)))
bt = pd.DataFrame(linhas, columns=["estrategia", "receita_capturada_top20", "taxa_ganho_top20", "zumbis_no_top20", "receita_top10_por_vendedor"])
out(f"\nTop 20% = os {N_TOP} deals com maior nota. Escolher ao acaso capturaria ~20% da receita.")
out(f"Top 10 por vendedor = o que cada vendedor veria primeiro ({pool.sales_agent.nunique()} vendedores).")
out(bt.round(3).to_string(index=False))
bt.to_csv(f"{OUT}/fase2_backtest.csv", index=False)

# gráfico do teste
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
SURF, INK, INK2, GRID, BLUE, GRAY = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6", "#b9b8b3"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": GRID, "text.color": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True})
fig, ax = plt.subplots(figsize=(11, 4.9)); fig.subplots_adjust(top=0.76, left=0.36, right=0.95, bottom=0.12)
nomes = ["Nossa lógica\n(chance pela idade × valor)", "Só valor\n(preço de tabela)", "Lógica 'óbvia' × valor\n(taxa de produto/setor/vendedor)", "Lógica 'óbvia' sem valor"]
vals = bt.receita_capturada_top20.values
cores = [BLUE] + [GRAY] * 3
b = ax.barh(nomes[::-1], vals[::-1], color=cores[::-1], height=0.6)
for r, v in zip(b, vals[::-1]):
    ax.text(v + 0.01, r.get_y() + r.get_height() / 2, f"{v:.0%}", va="center", fontsize=11, weight="bold")
ax.axvline(0.2, color=INK, ls="--", lw=1); ax.text(0.205, 3.42, "ao acaso: 20%", fontsize=9.5, color=INK2)
ax.set_xlim(0, 1); ax.xaxis.set_major_formatter(PercentFormatter(1, 0)); ax.grid(axis="y", visible=False)
ax.set_xlabel("Parte da receita de out–dez que estava nos 20% de deals com maior nota em 30/09")
fig.text(0.01, 0.95, "Gráfico 7 · Teste de volta no tempo: qual lógica aponta onde está o dinheiro?", fontsize=14, weight="bold", va="top")
fig.text(0.01, 0.875, f"Em 30/09/2017, cada lógica escolheu os {N_TOP} deals mais prioritários (de {len(pool)}) usando só dados até aquela data.", fontsize=10.5, color=INK2, va="top")
fig.savefig(f"{GRAF}/grafico7_backtest.png", dpi=150); plt.close(fig)
out("\nGráfico salvo: grafico7_backtest.png")
log.close()
