"""O relógio do trimestre: quando um deal decide depende da idade E da altura do trimestre.

Base do score do plano v2. Tudo o que é "aprendido" aqui usa só o passado de cada data (as-of).
Rodar de dentro de analise/:  python3 eda-05-relogio-do-trimestre.py > eda-05-relogio-do-trimestre.saida.txt
"""
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 240)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_rows", 200)

D = "../dados/"
p = pd.read_csv(D + "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
pr = pd.read_csv(D + "products.csv")
t = pd.read_csv(D + "sales_teams.csv")
pr["k"] = pr["product"].str.replace(" ", "").str.lower()
p["k"] = p["product"].str.replace(" ", "").str.lower()
p = p.merge(pr[["k", "sales_price"]], on="k", how="left")

REF = pd.Timestamp("2018-01-01")
H = 28                                    # horizonte da lista: quatro semanas
CICLO_MAX = 138
FAIXAS = [-1, 15, 30, 45, 60, 75, 90, 105, 120, 138, 100000]
ROT = ["0-15", "16-30", "31-45", "46-60", "61-75", "76-90", "91-105", "106-120", "121-138", ">138"]

E = p[p.engage_date.notna()].copy()
ini_tri = E.engage_date.dt.to_period("Q").dt.start_time
E["prazo_tri"] = ini_tri + pd.offsets.QuarterBegin(2, startingMonth=1) - pd.Timedelta(days=1)
fech = E[E.close_date.notna()].copy()
fech["ciclo"] = (fech.close_date - fech.engage_date).dt.days
fech["ganho"] = (fech.deal_stage == "Won").astype(int)


def titulo(txt):
    print("\n" + "=" * 100 + "\n" + txt + "\n" + "=" * 100)


def inicio_tri(d):
    return pd.Timestamp(d.year, 3 * ((d.month - 1) // 3) + 1, 1)


def vista(corte, h=H):
    """Deals engajados antes do corte e ainda abertos nele, com o que aconteceu nos h dias seguintes."""
    al = E[(E.engage_date < corte) & ((E.close_date >= corte) | E.close_date.isna())].copy()
    al["idade"] = (corte - al.engage_date).dt.days
    fut = al.close_date.notna() & (al.close_date < corte + pd.Timedelta(days=h))
    al["dec"] = fut.astype(int)
    al["ganhou"] = (fut & (al.deal_stage == "Won")).astype(int)
    al["valor_ganho"] = al.ganhou * al.sales_price
    al["fx"] = pd.cut(al.idade, FAIXAS, labels=ROT)
    return al


def analogas(corte):
    """As mesmas datas dos trimestres anteriores, enquanto houver fechamentos registrados (a partir de mar/2017)."""
    out, a = [], corte
    while True:
        a = a - pd.DateOffset(months=3)
        if a < pd.Timestamp("2017-03-01"):
            return out
        out.append(a)


def tabela_destino(corte):
    an = analogas(corte)
    if not an:
        return None, 0
    hist = pd.concat([vista(a) for a in an])
    g = hist.groupby("fx", observed=False).agg(n=("dec", "size"), decidiram=("dec", "sum"), ganharam=("ganhou", "sum"))
    g["p_decide"] = (g.decidiram / g.n).fillna(0)
    g["p_ganho"] = (g.ganharam / g.decidiram).fillna(hist.ganhou.sum() / max(hist.dec.sum(), 1))
    return g, len(an)


titulo("A. Fechamentos por mês do trimestre e tipo de ciclo (rápido: até 30 dias; lento: mais de 30)")
fech["mes_tri"] = (fech.close_date.dt.month - 1) % 3 + 1
fech["lento"] = fech.ciclo > 30
print(fech.groupby(["lento", "mes_tri"]).agg(n=("ganho", "size"), taxa_ganho=("ganho", "mean"), valor=("close_value", "sum")).round(3).to_string())
print("maior ciclo de um fechamento ocorrido no 1º mês de um trimestre:", int(fech[fech.mes_tri == 1].ciclo.max()), "dias")
print(fech.pivot_table(index=fech.close_date.dt.to_period("M"), columns="lento", values="ganho", aggfunc=["size", "mean"]).round(3).to_string())

titulo("B. Semana do trimestre dos fechamentos lentos (quando a janela abre e quando a taxa de ganho sobe)")
fech["sem_tri"] = ((fech.close_date - fech.close_date.dt.to_period("Q").dt.start_time).dt.days // 7) + 1
print(fech[fech.lento].groupby("sem_tri").agg(n=("ganho", "size"), taxa_ganho=("ganho", "mean")).round(3).T.to_string())

titulo("C. Regra do prazo do trimestre, conferida só com o que se sabia em cada data")
for corte in ("2017-07-01", "2017-10-01", "2018-01-01"):
    k = fech[fech.close_date < pd.Timestamp(corte)]
    print(f"{corte}: fechamentos conhecidos {len(k)} | depois do fim do trimestre seguinte ao engajamento: {int((k.close_date > k.prazo_tri).sum())} | maior ciclo conhecido: {int(k.ciclo.max())}")

titulo(f"D. Tabela de destino para {REF.date()} (datas análogas: 01/10, 01/07 e 01/04 de 2017), horizonte de {H} dias")
T, _ = tabela_destino(REF)
print(T.round(3).to_string())
for a in analogas(REF):
    v = vista(a)
    g = v.groupby("fx", observed=False).agg(n=("dec", "size"), d=("dec", "sum"))
    print(a.date(), "decidem em 28 dias por faixa:", (g.d / g.n).round(2).to_dict())
velhos = T.loc[ROT[1:-1]]
print(f"deals com 16 a 138 dias em início de trimestre: {int(velhos.n.sum())} observações, {int(velhos.decidiram.sum())} decidiram em 28 dias")

titulo("E. Destino até o fim do trimestre para quem está aberto no 1º dia dele (três trimestres somados)")
linhas = []
for a in analogas(REF):
    al = E[(E.engage_date < a) & ((E.close_date >= a) | E.close_date.isna())].copy()
    al["fx"] = pd.cut((a - al.engage_date).dt.days, FAIXAS, labels=ROT)
    no_tri = al.close_date.notna() & (al.close_date < a + pd.DateOffset(months=3))
    al["dec_tri"] = no_tri.astype(int)
    al["ganho_tri"] = (no_tri & (al.deal_stage == "Won")).astype(int)
    linhas.append(al)
Q = pd.concat(linhas).groupby("fx", observed=False).agg(n=("dec_tri", "size"), decide_no_tri=("dec_tri", "mean"), ganha_no_tri=("ganho_tri", "mean"))
print(Q.round(3).to_string())

titulo(f"F. Backtest as-of: segundas a cada 4 semanas (janelas de {H} dias que não se sobrepõem), jul a dez/2017, top 5 por vendedor")


def rodar(cortes, k=5):
    linhas, por_vend = [], []
    for corte in cortes:
        Tc, n_an = tabela_destino(corte)
        if Tc is None:
            continue
        al = vista(corte)
        r = np.random.default_rng(int(corte.strftime("%Y%m%d")))
        vivo138 = al.idade <= CICLO_MAX
        vivo = vivo138 & (al.prazo_tri >= corte)
        dias_rest = np.minimum(CICLO_MAX - al.idade, (al.prazo_tri - corte).dt.days)
        ve = al.fx.map(Tc.p_decide).astype(float) * al.fx.map(Tc.p_ganho).astype(float) * al.sales_price
        al["relogio"] = np.where(vivo, ve + al.sales_price * 1e-7, -1)                          # plano v2
        al["preco_prazo"] = np.where(vivo, al.sales_price * 1e4 + dias_rest, -1)                # melhor regra pública: vivos pelas duas regras, por preço
        al["preco_138"] = np.where(vivo138, al.sales_price * 1e4 + r.random(len(al)), -1)       # preço entre os de até 138 dias
        al["plano_v1"] = np.where(vivo138 & (al.sales_price > 550), al.sales_price * 1e4 + al.idade, -1)
        al["aleatorio"] = np.where(vivo, r.random(len(al)), -1)
        lin = dict(corte=str(corte.date()), sem_tri=int((corte - inicio_tri(corte)).days // 7 + 1), analogas=n_an, vivos=int(vivo.sum()))
        for c in ("relogio", "preco_prazo", "preco_138", "plano_v1", "aleatorio"):
            top = al.sort_values(c, ascending=False).groupby("sales_agent").head(k)
            top = top[top[c] >= 0]
            lin["$" + c] = int(top.valor_ganho.sum())
            lin["acerto_" + c] = round(top.ganhou.sum() / max(len(top), 1), 3)
            x = top.groupby("sales_agent").valor_ganho.sum().rename(c).to_frame()
            x["corte"] = lin["corte"]
            por_vend.append(x.reset_index().melt(id_vars=["sales_agent", "corte"]))
        lin["$oraculo"] = int(al.sort_values("valor_ganho", ascending=False).groupby("sales_agent").head(k).valor_ganho.sum())
        linhas.append(lin)
    R = pd.DataFrame(linhas)
    PV = pd.concat(por_vend).pivot_table(index="sales_agent", columns="variable", values="value", aggfunc="sum").fillna(0)
    return R, PV


def ic(PV, a, b, n=5000):
    rng = np.random.default_rng(7)
    amostras = []
    for _ in range(n):
        i = rng.integers(0, len(PV), len(PV))
        den = PV[b].values[i].sum()
        amostras.append(PV[a].values[i].sum() / den if den else np.nan)
    return PV[a].sum() / PV[b].sum(), np.nanpercentile(amostras, 2.5), np.nanpercentile(amostras, 97.5)


R, PV = rodar(pd.date_range("2017-07-03", "2017-12-03", freq="4W-MON"))
print(R[["corte", "sem_tri", "analogas", "vivos"] + [c for c in R if c.startswith("$")]].to_string(index=False))
print(R[["corte", "sem_tri"] + [c for c in R if c.startswith("acerto_")]].to_string(index=False))
s = R[[c for c in R if c.startswith("$")]].sum()
print("soma:", {k: int(v) for k, v in s.items()})
for a, b in (("relogio", "preco_prazo"), ("relogio", "preco_138"), ("relogio", "plano_v1"), ("preco_prazo", "plano_v1"), ("relogio", "aleatorio")):
    r0, lo, hi = ic(PV, a, b)
    print(f"  {a} / {b} = {r0:.2f}   IC 95% [{lo:.2f}, {hi:.2f}]   (bootstrap por vendedor, 30 vendedores, 5.000 reamostras, semente 7)")
print(f"  fração do teto (oráculo que conhece o futuro): relogio {s['$relogio'] / s['$oraculo']:.2f} | preco_prazo {s['$preco_prazo'] / s['$oraculo']:.2f} | plano_v1 {s['$plano_v1'] / s['$oraculo']:.2f}")

titulo("G. Estabilidade: todas as segundas de jul a dez/2017 (janelas se sobrepõem; serve para ver o padrão, não para o IC)")
R2, _ = rodar(pd.date_range("2017-07-03", "2017-12-03", freq="W-MON"))
R2["grupo"] = pd.cut(R2["sem_tri"], [0, 4, 9, 14], labels=["semanas 1-4", "semanas 5-9", "semanas 10-14"])
g = R2.groupby("grupo", observed=True)[["$relogio", "$preco_prazo", "$plano_v1"]].sum()
g["relogio/preco_prazo"] = g["$relogio"] / g["$preco_prazo"]
g["relogio/plano_v1"] = g["$relogio"] / g["$plano_v1"]
g["segundas"] = R2.groupby("grupo", observed=True).size()
print(g.round(2).to_string())
print("relógio acima de preço+prazo em", int((R2["$relogio"] > R2["$preco_prazo"]).sum()), "de", len(R2), "segundas")
print("taxa de acerto média: relógio", R2.acerto_relogio.mean().round(3), "| preço+prazo", R2.acerto_preco_prazo.mean().round(3), "| plano v1", R2.acerto_plano_v1.mean().round(3), "| aleatório", R2.acerto_aleatorio.mean().round(3))

titulo(f"H. Foto em {REF.date()} pelas regras do v2")
eng = p[p.deal_stage == "Engaging"].copy()
eng["idade"] = (REF - eng.engage_date).dt.days
eng["prazo_tri"] = eng.engage_date.dt.to_period("Q").dt.start_time + pd.offsets.QuarterBegin(2, startingMonth=1) - pd.Timedelta(days=1)
eng["vivo"] = (eng.idade <= CICLO_MAX) & (eng.prazo_tri >= REF)
eng["fx"] = pd.cut(eng.idade, FAIXAS, labels=ROT)
v = eng[eng.vivo].copy()
abertos = p[p.deal_stage.isin(["Engaging", "Prospecting"])]
prosp = p[p.deal_stage == "Prospecting"]
print(f"abertos no CRM: {len(abertos)} deals, US$ {abertos.sales_price.sum():,.0f}")
print(f"Engaging vivos: {len(v)} deals, US$ {v.sales_price.sum():,.0f} ({v.sales_price.sum() / abertos.sales_price.sum():.1%} do aberto)")
print(f"Engaging vencidos: {int((~eng.vivo).sum())} deals, US$ {eng[~eng.vivo].sales_price.sum():,.0f}; dos quais com até 138 dias mas fora do prazo do trimestre: {int(((eng.idade <= CICLO_MAX) & ~eng.vivo).sum())}")
print(f"Prospecting (sem data): {len(prosp)} deals, US$ {prosp.sales_price.sum():,.0f}")
por_v = v.groupby("sales_agent").size().reindex(t.sales_agent).fillna(0)
print("vivos por vendedor do cadastro: mediana", por_v.median(), "| máximo", int(por_v.max()), "| vendedores com zero:", int((por_v == 0).sum()), "de 35")
print("vivos por região:", v.merge(t, on="sales_agent").groupby("regional_office").size().to_dict(), "| vivos por faixa:", v.groupby("fx", observed=True).size().to_dict())
v["p_dec_tri"] = v.fx.map(Q.decide_no_tri).astype(float)
v["p_ganho_tri"] = v.fx.map(Q.ganha_no_tri).astype(float)
print(f"esperado no trimestre a partir dos vivos: {v.p_dec_tri.sum():.0f} decidem, {v.p_ganho_tri.sum():.0f} ganhos, US$ {(v.p_ganho_tri * v.sales_price).sum():,.0f}")
v["ve28"] = v.fx.map(T.p_decide).astype(float) * v.fx.map(T.p_ganho).astype(float) * v.sales_price
print(f"com chance de decidir nos próximos {H} dias: {int((v.ve28 > 0).sum())} deals")

titulo("I. Carteira de abertura: quanto dos ganhos de cada trimestre veio dos deals já abertos no 1º dia")
for qs in ("2017-04-01", "2017-07-01", "2017-10-01"):
    qs = pd.Timestamp(qs)
    w = p[(p.deal_stage == "Won") & (p.close_date >= qs) & (p.close_date < qs + pd.DateOffset(months=3))]
    ab = E[(E.engage_date < qs) & ((E.close_date >= qs) | E.close_date.isna())]
    id_ab = (qs - ab.engage_date).dt.days
    print(f"{qs.date()}: abertos com até 90 dias {int((id_ab <= 90).sum())} | ganhos no trimestre {len(w)}, da carteira de abertura {int((w.engage_date < qs).sum())} ({(w.engage_date < qs).mean():.0%}), US$ {w[w.engage_date < qs].close_value.sum():,.0f} de {w.close_value.sum():,.0f}")

titulo("J. Deals engajados dentro de um 1º mês de trimestre: quantos decidem no próprio mês (hipótese para os 500 de Prospecting)")
E["mes_eng"] = E.engage_date.dt.to_period("M")
E["mesmo_mes"] = E.close_date.notna() & (E.close_date.dt.to_period("M") == E.mes_eng)
E["ganho_mesmo_mes"] = E.mesmo_mes & (E.deal_stage == "Won")
m1 = E[E.mes_eng.isin([pd.Period("2017-04"), pd.Period("2017-07"), pd.Period("2017-10")])]
print(m1.groupby("mes_eng").agg(engajados=("mesmo_mes", "size"), decide_no_mes=("mesmo_mes", "mean"), ganha_no_mes=("ganho_mesmo_mes", "mean")).round(3).to_string())
taxa = m1.ganho_mesmo_mes.mean()
print(f"somados: {m1.mesmo_mes.mean():.1%} decidem no mês, {taxa:.1%} são ganhos no mês")
print(f"se os {len(prosp)} de Prospecting fossem engajados no início de janeiro e se comportassem assim: US$ {taxa * prosp.sales_price.sum():,.0f} (ordem de grandeza; premissa, não medição)")

titulo("K. Carga de referência por vendedor (Lei de Little): deals em andamento que depois fecharam")
meio = pd.date_range("2017-04-15", "2017-11-15", freq="MS") + pd.Timedelta(days=14)
W = pd.concat([fech[(fech.engage_date <= d) & (fech.close_date > d)].groupby("sales_agent").size().rename(str(d.date())) for d in meio], axis=1).fillna(0)
print("mediana por data:", W.median().round(0).to_dict())
print("mediana geral:", float(np.median(W.values)), "| quartis:", np.percentile(W.values, [25, 75]).tolist())
print(f"conferência por Little: {len(fech) / 30 / 43.7:.2f} fechamentos por semana por vendedor x {fech.ciclo.mean():.0f} dias de ciclo médio / 7 = {len(fech) / 30 / 43.7 * fech.ciclo.mean() / 7:.0f} deals em andamento")
print("vivos hoje por vendedor ativo: mediana", v.groupby("sales_agent").size().reindex(W.index).fillna(0).median())

titulo("L. Atributos continuam sem sinal quando se controla o mês do trimestre? (permutação estratificada, 300 rodadas, semente 7)")
rng = np.random.default_rng(7)


def var_taxa(df, chave, n_min=20):
    g = df.groupby(chave).ganho.agg(["mean", "count"])
    return g[g["count"] >= n_min]["mean"].var()


for chave in ("account", "sales_agent", ["sales_agent", "product"], "product"):
    obs = var_taxa(fech, chave)
    sims = []
    for _ in range(300):
        s = fech.copy()
        s["ganho"] = s.groupby("mes_tri").ganho.transform(lambda x: rng.permutation(x.values))
        sims.append(var_taxa(s, chave))
    print(f"  {str(chave):32s} variância observada {obs:.5f} | permutada {np.mean(sims):.5f} | p = {np.mean(np.array(sims) >= obs):.2f}")
