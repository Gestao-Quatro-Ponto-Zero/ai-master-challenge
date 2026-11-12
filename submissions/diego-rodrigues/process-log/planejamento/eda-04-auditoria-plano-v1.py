"""Auditoria do plano v1 contra o dataset (revisão de 11/11/2026).

Cada bloco confere uma afirmação ou um número pinado em 02-plano-implementacao (v1).
Rodar de dentro de analise/:  python3 eda-04-auditoria-plano-v1.py > eda-04-auditoria-plano-v1.saida.txt
"""
import math
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_rows", 200)

D = "../dados/"
p = pd.read_csv(D + "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
pr = pd.read_csv(D + "products.csv")
t = pd.read_csv(D + "sales_teams.csv")
pr["k"] = pr["product"].str.replace(" ", "").str.lower()
p["k"] = p["product"].str.replace(" ", "").str.lower()
p = p.merge(pr[["k", "sales_price"]], on="k", how="left")

EXPORT = p.close_date.max()                 # 2017-12-31, último dia do export
REF = EXPORT + pd.Timedelta(days=1)         # 2018-01-01, a segunda-feira em que o vendedor abre
fech = p[p.deal_stage.isin(["Won", "Lost"])].copy()
fech["ciclo"] = (fech.close_date - fech.engage_date).dt.days
fech["ganho"] = (fech.deal_stage == "Won").astype(int)
abertos = p[p.deal_stage.isin(["Engaging", "Prospecting"])].copy()
eng = p[p.deal_stage == "Engaging"].copy()
COM_DATA = p[p.engage_date.notna()].copy()


def titulo(txt):
    print("\n" + "=" * 100 + "\n" + txt + "\n" + "=" * 100)


titulo("A. Vendedores: cadastro x pipeline x abertos (o v1 pina 35 em três testes)")
print("no cadastro (sales_teams):", t.sales_agent.nunique())
print("com algum deal no pipeline:", p.sales_agent.nunique())
print("com deal aberto:", abertos.sales_agent.nunique())
print("no cadastro sem nenhum deal:", sorted(set(t.sales_agent) - set(p.sales_agent)))
print("com histórico mas sem deal aberto:", sorted(set(p.sales_agent) - set(abertos.sales_agent)))
print("Prospecting por região:", abertos[abertos.deal_stage == "Prospecting"].merge(t, on="sales_agent").groupby("regional_office").size().to_dict())

titulo("B. Data de referência: o EDA usou 31/12, o produto usa 01/01 (o v1 pina 1.291 com hoje = 01/01)")
for nome, ref in [("31/12/2017 (EDA)", EXPORT), ("01/01/2018 (produto)", REF)]:
    idade = (ref - eng.engage_date).dt.days
    print(f"{nome}: idade>138 = {(idade > 138).sum()} | 0-30 = {idade.between(0, 30).sum()} | 31-90 = {idade.between(31, 90).sum()} | 91-138 = {idade.between(91, 138).sum()}")
print("dia da semana de 01/01/2018:", REF.day_name())
print("deals fechados com ciclo exatamente 138:", int((fech.ciclo == 138).sum()), "(por isso o corte é > 138, não >= 138)")

titulo("C. 'Chance de decidir em 30 dias': fórmula do v1 (só fechados) x tábua de vida com os abertos em risco")
obs_fim = COM_DATA.close_date.fillna(EXPORT)
COM_DATA["dur"] = (obs_fim - COM_DATA.engage_date).dt.days
COM_DATA["evento"] = COM_DATA.close_date.notna()
linhas = []
for a0 in (0, 15, 30, 60, 90, 120, 138):
    risco = COM_DATA[COM_DATA.dur >= a0]
    obs = risco[risco.evento | (risco.dur >= a0 + 30)]          # janela de 30 dias inteira observada
    dec = obs[obs.evento & (obs.dur < a0 + 30)]
    so_fech = fech[fech.ciclo >= a0]
    linhas.append(dict(idade=a0, em_risco=len(obs), real_decide_30d=round(len(dec) / len(obs), 3),
                       v1_decide_30d=round((so_fech.ciclo <= a0 + 30).mean(), 3)))
print(pd.DataFrame(linhas).to_string(index=False))
print("Leitura: aos 120 dias o v1 mostraria 100 em 100; o real é ~16 em 100. É viés de sobrevivência dentro da própria tabela.")

titulo("D. Capacidade do v1: fechamentos em 90 dias / (90/7) x 1,5, piso 5, teto 25")
f90 = fech[fech.close_date > EXPORT - pd.Timedelta(days=90)].groupby("sales_agent").size().reindex(t.sales_agent).fillna(0)
cap_sem = (f90 / (90 / 7) * 1.5).round().clip(5, 25)
cap_dia = np.ceil(cap_sem / 5)
print("cap_dia (quantos vendedores em cada valor):", cap_dia.astype(int).value_counts().sort_index().to_dict())
print("cap_semana mediana:", cap_sem.median(), "| o guia e a tela-rascunho falam em 5 por dia e 20 a 25 por semana")
ab = abertos.copy()
ab["idade"] = (REF - ab.engage_date).dt.days
ab["vivo_v1"] = (ab.deal_stage == "Engaging") & (ab.idade <= 138) & (ab.sales_price > 550)
viv = ab[ab.vivo_v1].groupby("sales_agent").size().reindex(t.sales_agent).fillna(0)
print("fila 'vivo' do v1 por vendedor: mediana", viv.median(), "| com zero:", int((viv == 0).sum()), "de 35 | total:", int(viv.sum()))

titulo("E. O '3x o aleatório' é poder de previsão ou mistura de preço?")
rng = np.random.default_rng(7)
tot = {"preco": [0, 0, 0], "aleat": [0, 0, 0]}
razoes = []
for corte in pd.date_range("2017-05-01", "2017-10-01", freq="MS"):
    al = COM_DATA[(COM_DATA.engage_date <= corte) & ((COM_DATA.close_date > corte) | COM_DATA.close_date.isna())].copy()
    al["g90"] = ((al.deal_stage == "Won") & (al.close_date <= corte + pd.Timedelta(days=90))).astype(int)
    al["r"] = rng.random(len(al))
    for nome, col in (("preco", "sales_price"), ("aleat", "r")):
        top = al.sort_values(col, ascending=False).groupby("sales_agent").head(5)
        tot[nome][0] += (top.g90 * top.sales_price).sum(); tot[nome][1] += top.g90.sum(); tot[nome][2] += len(top)
    top = al.sort_values("sales_price", ascending=False).groupby("sales_agent").head(5)
    razoes.append(top.sales_price.mean() / al.sales_price.mean())
print(f"valor ganho: top 5 por preço / aleatório = {tot['preco'][0] / tot['aleat'][0]:.2f}x")
print(f"taxa de acerto (ganhou em 90 dias): por preço {tot['preco'][1] / tot['preco'][2]:.3f} | aleatório {tot['aleat'][1] / tot['aleat'][2]:.3f}")
print(f"preço médio do top 5 por preço / preço médio de todos os vivos = {np.mean(razoes):.2f}x")
print("Leitura: o múltiplo de valor é a razão de preços. A taxa de acerto é a mesma. Não é previsão.")

titulo("F. Poder do piloto 'metade dos vendedores de uma região, +10% de valor ganho'")
w = p[p.deal_stage == "Won"].copy()
w["tri"] = w.close_date.dt.to_period("Q")
M = w.pivot_table(index="sales_agent", columns="tri", values="close_value", aggfunc="sum").fillna(0)[["2017Q2", "2017Q3", "2017Q4"]]
cv = (M.std() / M.mean()).mean()
rho = np.corrcoef(M["2017Q3"], M["2017Q4"])[0, 1]
z = 1.96 + 0.84
print(f"valor ganho por vendedor por trimestre: CV médio {cv:.2f} | correlação entre trimestres {rho:.2f}")
for n in (5, 15):
    bruto = z * cv * math.sqrt(2 / n)
    print(f"{n} vendedores por braço: menor efeito detectável {bruto:.0%}; ajustando pelo trimestre anterior {bruto * math.sqrt(1 - rho ** 2):.0%}")
print(f"para detectar +10% com ajuste: {2 * (z * cv * math.sqrt(1 - rho ** 2) / 0.10) ** 2:.0f} vendedores por braço (a empresa tem 30 ativos)")
p0, d = 0.22, 0.05
n_deal = ((1.96 * math.sqrt(2 * p0 * (1 - p0)) + 0.84 * math.sqrt(p0 * (1 - p0) + (p0 + d) * (1 - p0 - d))) / d) ** 2
print(f"alternativa, sorteio por deal dentro do vendedor: {n_deal:.0f} deals por braço detectam +5 pontos na taxa de decisão em 28 dias")

titulo("G. De onde vêm 'US$ 3,66 mi / 74%' e 'US$ 236 mil' do guia")
eng2 = eng.copy()
eng2["idade"] = (REF - eng2.engage_date).dt.days
ini_tri = eng2.engage_date.dt.to_period("Q").dt.start_time
eng2["prazo_tri"] = ini_tri + pd.offsets.QuarterBegin(2, startingMonth=1) - pd.Timedelta(days=1)   # fim do trimestre seguinte
total = abertos.sales_price.sum()
v138 = eng2[eng2.idade > 138].sales_price.sum()
vivo2 = eng2[(eng2.idade <= 138) & (eng2.prazo_tri >= REF)]
morto2 = eng2[~eng2.index.isin(vivo2.index)].sales_price.sum()
print(f"pipeline aberto a preço de tabela: US$ {total:,.0f}")
print(f"regra só de 138 dias: vencido US$ {v138:,.0f} ({v138 / total:.1%} do aberto) em {(eng2.idade > 138).sum()} deals; vivos {(eng2.idade <= 138).sum()} deals")
print(f"regra de 138 dias + prazo do trimestre: vencido US$ {morto2:,.0f} ({morto2 / total:.1%}) | vivos {len(vivo2)} deals, US$ {vivo2.sales_price.sum():,.0f}")
print("Leitura: os valores do guia são os da segunda regra, rotulados como se fossem da primeira.")
