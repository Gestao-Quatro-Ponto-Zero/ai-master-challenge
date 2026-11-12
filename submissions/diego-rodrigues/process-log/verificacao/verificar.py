"""Verificação independente do Lead Scorer (Challenge 003).

Recalcula, a partir SÓ dos quatro CSVs crus e de solution/config.json, os números
citados no README.md e em docs/resumo-executivo.md. Não importa nada de
solution/motor nem de solution/avaliacao: toda regra aqui foi escrita pelo revisor.

Rodar (da raiz da submissão):
    python3 process-log/verificacao/verificar.py > process-log/verificacao/saida.txt

Convenções do revisor (decididas ANTES de ler o código de produção):
- Valor de tabela = sales_price do catálogo, casando produto sem espaços e sem caixa
  ("GTXPro" -> "GTX Pro").
- Recorte numa data de corte c: um negócio é visível se engage_date < c; seu desfecho
  só é conhecido se close_date < c. Se close_date >= c, ele está ABERTO em c (o estágio
  final é ignorado). Prospecting não tem engage_date: aberto, sem idade, fora das filas.
- "Vencido" em c: aberto, com engage_date, e c > prazo, onde prazo = último dia do
  trimestre seguinte ao trimestre de engajamento (regra ativa só se >= 500 fechamentos
  conhecidos em c e < 0,1% deles passou do prazo), OU idade > ciclo máximo observado
  entre os fechamentos conhecidos em c.
- Cortes do backtest: 2017-07-03 e a cada 28 dias (6 cortes, até 2017-11-20).
"""
import json
import os
import numpy as np
import pandas as pd
from statistics import NormalDist

# sem scipy no ambiente: qui-quadrado escrito à mão
def chi2_contingency(ct):
    o = ct.values.astype(float)
    e = o.sum(1, keepdims=True) * o.sum(0, keepdims=True) / o.sum()
    chi2 = float(((o - e) ** 2 / e).sum())
    dof = (o.shape[0] - 1) * (o.shape[1] - 1)
    # p aproximado por Wilson-Hilferty
    zz = ((chi2 / dof) ** (1 / 3) - (1 - 2 / (9 * dof))) / (2 / (9 * dof)) ** 0.5
    return chi2, 1 - NormalDist().cdf(zz), dof, e

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
DADOS = os.path.join(RAIZ, "solution", "data")
CFG = json.load(open(os.path.join(RAIZ, "solution", "config.json")))
H = CFG["horizonte_dias"]          # 28
K = CFG["foco_por_vendedor"]       # 5
REF = pd.Timestamp("2018-01-01")
RNG = np.random.default_rng(12345)  # semente própria do revisor
CORTES = [pd.Timestamp("2017-07-03") + pd.Timedelta(days=28 * i) for i in range(6)]


def titulo(t):
    print("\n" + "=" * 78 + "\n" + t + "\n" + "=" * 78)


def brl(x):
    return f"US$ {x:,.0f}".replace(",", ".")


# --------------------------------------------------------------------------- carga
p = pd.read_csv(os.path.join(DADOS, "sales_pipeline.csv"), parse_dates=["engage_date", "close_date"])
prod = pd.read_csv(os.path.join(DADOS, "products.csv"))
acc = pd.read_csv(os.path.join(DADOS, "accounts.csv"))
team = pd.read_csv(os.path.join(DADOS, "sales_teams.csv"))
norm = lambda s: s.str.replace(" ", "", regex=False).str.lower()

titulo("1. Qualidade do dado")
print("linhas no pipeline:", len(p))
fora = ~p["product"].isin(prod["product"])
print("linhas cujo produto não casa literalmente com o catálogo:", int(fora.sum()),
      p.loc[fora, "product"].value_counts().to_dict())
prod["pk"] = norm(prod["product"])
p["pk"] = norm(p["product"])
p = p.merge(prod[["pk", "sales_price"]], on="pk", how="left")
print("linhas sem preço após normalizar espaço/caixa:", int(p.sales_price.isna().sum()))
aberto_final = p.deal_stage.isin(["Prospecting", "Engaging"])
print("abertos no export:", int(aberto_final.sum()), "| abertos sem conta:", int(p.loc[aberto_final, "account"].isna().sum()),
      "| fechados sem conta:", int(p.loc[~aberto_final, "account"].isna().sum()), "de", int((~aberto_final).sum()))
print("Prospecting sem engage_date:", int(p.loc[p.deal_stage == "Prospecting", "engage_date"].isna().sum()),
      "de", int((p.deal_stage == "Prospecting").sum()))
print("Engaging sem engage_date:", int(p.loc[p.deal_stage == "Engaging", "engage_date"].isna().sum()),
      "| abertos com close_date:", int(p.loc[aberto_final, "close_date"].notna().sum()))
print("maior close_date:", p.close_date.max().date(), "| menor close_date:", p.close_date.min().date())
print("vendedores: cadastro", team.sales_agent.nunique(), "| com algum deal", p.sales_agent.nunique(),
      "| com deal aberto", p.loc[aberto_final, "sales_agent"].nunique())

# ------------------------------------------------------------ regras aprendidas
fech = p[~aberto_final].copy()
fech["ciclo"] = (fech.close_date - fech.engage_date).dt.days


def prazo_trimestre(engage):
    return (engage.dt.to_period("Q") + 1).dt.end_time.dt.normalize()


fech["prazo"] = prazo_trimestre(fech.engage_date)

titulo("2. Robustez da regra de 'vencido' (export inteiro)")
print("ciclo (dias) dos 6.711 fechados:", fech.ciclo.describe().round(1).to_dict())
print("fechamentos por ciclo, 120-138 dias:", fech.ciclo.value_counts().sort_index().loc[120:].to_dict())
fora_prazo = fech[fech.close_date > fech.prazo]
print("fechados DEPOIS do fim do trimestre seguinte ao engajamento:", len(fora_prazo), "de", len(fech))
print(fora_prazo[["opportunity_id", "engage_date", "close_date", "deal_stage", "ciclo"]].to_string(index=False))
print("fração que fecha no mesmo trimestre do engajamento:", round((fech.close_date.dt.to_period("Q") == fech.engage_date.dt.to_period("Q")).mean(), 3))
# Ganhos fechados nos últimos dias do prazo: a regra corta onde a massa acaba ou no meio dela?
fech["folga"] = (fech.prazo - fech.close_date).dt.days
print("folga (dias entre close e prazo) dos GANHOS, percentis 0/1/5/50:",
      fech.loc[fech.deal_stage == "Won", "folga"].quantile([0, .01, .05, .5]).to_dict())


def recorte(c):
    """O que existe em c. Devolve (fechados_conhecidos, abertos_em_c) sem nenhum dado futuro."""
    vis = p[(p.engage_date < c) | p.engage_date.isna()].copy()
    conhecido = vis.close_date < c
    fc = vis[conhecido].copy()
    ab = vis[~conhecido].copy()
    # apaga o futuro: estágio, close_date e close_value de quem ainda não fechou em c
    ab["deal_stage"] = np.where(ab.engage_date.isna(), "Prospecting", "Engaging")
    ab["close_date"] = pd.NaT
    ab["close_value"] = np.nan
    return fc, ab


def regras(fc):
    ciclo = (fc.close_date - fc.engage_date).dt.days
    ciclo_max = int(ciclo.max())
    frac = float((fc.close_date > prazo_trimestre(fc.engage_date)).mean())
    ativa = len(fc) >= CFG["min_fechamentos_para_prazo"] and frac < CFG["tolerancia_prazo_trimestre"]
    return ciclo_max, ativa, frac


def classificar(c):
    fc, ab = recorte(c)
    cmax, ativa, frac = regras(fc)
    ab["idade"] = (c - ab.engage_date).dt.days
    ab["prazo"] = prazo_trimestre(ab.engage_date)
    venc = ab.engage_date.notna() & ((ab.idade > cmax) | (ativa & (c > ab.prazo)))
    ab["estado"] = np.where(ab.engage_date.isna(), "sem_data", np.where(venc, "vencido", "vivo"))
    return fc, ab, cmax, ativa, frac


titulo("3. Pipeline em 01/01/2018 (build de referência)")
fc, ab, cmax, ativa, frac = classificar(REF)
tot = ab.sales_price.sum()
print(f"ciclo máximo aprendido = {cmax} | regra do trimestre ativa = {ativa} (fração fora do prazo = {frac:.5f})")
for e in ["vencido", "vivo", "sem_data"]:
    s = ab[ab.estado == e]
    print(f"{e:9s} n={len(s):5d} valor={brl(s.sales_price.sum())} ({s.sales_price.sum() / tot:.1%})")
print("total aberto:", brl(tot), "n=", len(ab))
print("vencidos só pela idade (> ciclo máx):", int((ab.idade > cmax).sum()), "| só pelo prazo:",
      int(((ab.idade <= cmax) & (REF > ab.prazo)).sum()))
print("vendedores com deal vivo:", ab.loc[ab.estado == "vivo", "sales_agent"].nunique(),
      "| com > 5 vivos:", int((ab.loc[ab.estado == "vivo"].groupby("sales_agent").size() > 5).sum()))
print("checagem: os mesmos abertos do export?", sorted(ab.opportunity_id) == sorted(p.loc[aberto_final, "opportunity_id"]))

titulo("4. Achado central: algum 'vencido' foi ganho depois?")
venc_ids = {}
for c in CORTES:
    fc, ab, cmax, ativa, frac = classificar(c)
    v = ab[ab.estado == "vencido"]
    print(f"{c.date()}  fechados conhecidos={len(fc):5d}  ciclo_max={cmax:3d}  trimestre_ativa={ativa}  "
          f"abertos={len(ab):5d}  vivos={(ab.estado == 'vivo').sum():5d}  vencidos={len(v):5d}")
    for oid in v.opportunity_id:
        venc_ids.setdefault(oid, c)
ids = pd.Series(venc_ids, name="primeiro_corte")
real = p.set_index("opportunity_id").loc[ids.index]
print("negócios distintos classificados como vencidos em algum corte:", len(ids))
print("desfecho real no export:", real.deal_stage.value_counts().to_dict())
ganhos_depois = real[(real.deal_stage == "Won") & (real.close_date >= ids)]
print("vencidos ganhos com close_date >= corte da classificação:", len(ganhos_depois))
# Ataque: e se o ciclo máximo fosse o único critério (sem regra do trimestre)?
alt = {}
for c in CORTES:
    fc, ab = recorte(c)
    cm = int(((fc.close_date - fc.engage_date).dt.days).max())
    idade = (c - ab.engage_date).dt.days
    for oid in ab.loc[idade > cm, "opportunity_id"]:
        alt.setdefault(oid, c)
alt = pd.Series(alt)
ra = p.set_index("opportunity_id").loc[alt.index]
print("variante só-ciclo-máximo: distintos", len(alt), "| ganhos depois:",
      int(((ra.deal_stage == "Won") & (ra.close_date >= alt)).sum()))
# Ataque: regra do trimestre usando a convenção engage <= c, close <= c
alt2 = set()
for c in CORTES:
    vis = p[(p.engage_date <= c)]
    ab2 = vis[~(vis.close_date <= c)]
    alt2 |= set(ab2.loc[c > prazo_trimestre(ab2.engage_date), "opportunity_id"])
r2 = p.set_index("opportunity_id").loc[sorted(alt2)]
print("variante convenção <= c (só trimestre): distintos", len(alt2), "| ganhos (qualquer data):", int((r2.deal_stage == "Won").sum()))

titulo("5. Vazamento temporal: amostra de cortes")
for c in [pd.Timestamp("2017-05-15"), pd.Timestamp("2017-08-28"), pd.Timestamp("2017-10-23")]:
    fc, ab = recorte(c)
    print(f"{c.date()}: fechados visíveis com close_date >= c: {(fc.close_date >= c).sum()} | "
          f"abertos com estágio Won/Lost: {ab.deal_stage.isin(['Won', 'Lost']).sum()} | "
          f"abertos com close_date preenchido: {ab.close_date.notna().sum()} | "
          f"visíveis com engage_date >= c: {(fc.engage_date >= c).sum() + (ab.engage_date >= c).sum()} | "
          f"ciclo_max aprendido: {regras(fc)[0]} (export inteiro: {int(fech.ciclo.max())})")

titulo("6. Viés de sobrevivência: chance de decidir em 28 dias por faixa de idade")
bordas = CFG["bordas_faixa"]
rot = lambda a: next((f"{(bordas[i - 1] + 1) if i else 0}-{b}" for i, b in enumerate(bordas) if a <= b), f"{bordas[-1] + 1}+")
# Ingênua: só fechados. Para cada fechado e cada idade a que ele atingiu, decidiu em 28 dias se ciclo - a <= 28.
ing = []
for a in range(0, 139):
    s = fech[fech.ciclo >= a]
    ing.append((rot(a), len(s), int((s.ciclo - a <= H).sum())))
ing = pd.DataFrame(ing, columns=["faixa", "n", "decide"]).groupby("faixa", sort=False).sum()
# Correta (censurada): cortes diários entre 2017-03-01 e 2017-12-03 (desfecho em c+28 conhecido),
# todos os abertos em c com aquela idade, incluindo os que nunca fecharam.
cor = []
for c in pd.date_range("2017-03-01", REF - pd.Timedelta(days=H), freq="7D"):
    vis = p[(p.engage_date < c) & ~(p.close_date < c)]
    idade = (c - vis.engage_date).dt.days
    dec = vis.close_date.notna() & (vis.close_date < c + pd.Timedelta(days=H))
    cor.append(pd.DataFrame({"faixa": idade.map(rot), "n": 1, "decide": dec.astype(int)}))
cor = pd.concat(cor).groupby("faixa", sort=False).sum()
t = ing.join(cor, lsuffix="_ingenua", rsuffix="_correta", how="outer")
t["p_ingenua"] = (t.decide_ingenua / t.n_ingenua).round(3)
t["p_correta"] = (t.decide_correta / t.n_correta).round(3)
ordem = [rot(a) for a in [0] + [b + 1 for b in bordas]]
print(t.loc[[o for o in ordem if o in t.index]].to_string())

titulo("7. Backtest simplificado (versão do revisor, NÃO é o motor)")
# Política 'relógio' do revisor: chance de decidir em 28d por faixa de idade aprendida SÓ de origens
# o <= c - 28 (desfecho conhecido em c), com denominador censurado; ordena por chance e desempata
# pela menor folga até o prazo do trimestre. Política 'preço': maior sales_price, desempate menor folga.
def tabela_aprendida(c):
    linhas = []
    for o in pd.date_range("2017-03-01", c - pd.Timedelta(days=H), freq="7D"):
        vis = p[(p.engage_date < o) & ~(p.close_date < o)]
        idade = (o - vis.engage_date).dt.days
        dec = vis.close_date.notna() & (vis.close_date < o + pd.Timedelta(days=H))  # o+28 <= c: já conhecido em c
        linhas.append(pd.DataFrame({"faixa": idade.map(rot), "d": dec.astype(int)}))
    if not linhas:
        return {}
    return pd.concat(linhas).groupby("faixa").d.mean().to_dict()


res = []
for c in CORTES:
    fc, ab, cmax, ativa, frac = classificar(c)
    viv = ab[ab.estado == "vivo"].copy()
    tab = tabela_aprendida(c)
    viv["chance"] = viv.idade.map(rot).map(tab).fillna(0.0)
    viv["folga"] = (viv.prazo - c).dt.days
    real = p.set_index("opportunity_id")
    fim = c + pd.Timedelta(days=H)
    viv["ganhou"] = viv.opportunity_id.map(lambda i: real.at[i, "deal_stage"] == "Won" and c <= real.at[i, "close_date"] < fim)
    viv["valor_real"] = viv.opportunity_id.map(real.close_value).where(viv.ganhou, 0.0)
    viv["decidiu"] = viv.opportunity_id.map(lambda i: pd.notna(real.at[i, "close_date"]) and real.at[i, "close_date"] < fim)
    def top(df, chaves, asc):
        return df.sort_values(chaves, ascending=asc).groupby("sales_agent").head(K)
    pol = {
        "relogio_rev": top(viv, ["chance", "folga", "sales_price"], [False, True, False]),
        "preco_prazo": top(viv, ["sales_price", "folga"], [False, True]),
        "folga": top(viv, ["folga", "sales_price"], [True, False]),
    }
    for nome, sel in pol.items():
        for ag, g in sel.groupby("sales_agent"):
            res.append((c, nome, ag, g.valor_real.sum(), g.ganhou.sum(), len(g)))
    res.append((c, "_vivos", "-", viv.valor_real.sum(), viv.ganhou.sum(), len(viv)))
    print(f"{c.date()} vivos={len(viv)} " + " ".join(f"{n}={pol[n].valor_real.sum():,.0f}" for n in pol))
R = pd.DataFrame(res, columns=["corte", "pol", "ag", "valor", "ganhos", "n"])
S = R[R.pol != "_vivos"].groupby("pol")[["valor", "ganhos", "n"]].sum()
S["acerto"] = (S.ganhos / S.n).round(3)
print(S.to_string())
pv = R[R.pol != "_vivos"].pivot_table(index="ag", columns="pol", values="valor", aggfunc="sum").fillna(0)
for alt_ in ["preco_prazo", "folga"]:
    obs = pv.relogio_rev.sum() / pv[alt_].sum()
    bs = []
    ags = pv.index.values
    for _ in range(5000):
        s = pv.loc[RNG.choice(ags, len(ags))]
        bs.append(s.relogio_rev.sum() / s[alt_].sum())
    print(f"razão relogio_rev / {alt_} = {obs:.3f}  IC95% bootstrap por vendedor [{np.quantile(bs, .025):.3f}, {np.quantile(bs, .975):.3f}]")

titulo("7b. Backtest com a regra DOCUMENTADA do relógio, reimplementada pelo revisor")
# Escrito depois de ler docs/logica.md e motor/aprender.py só para entender a regra (sem importar nada):
# - tabela por faixa de idade aprendida nas 'datas análogas' (c - 3, 6, 9... meses, >= 1º fechamento),
#   denominador = todos os abertos em A com idade <= ciclo máx; p_decide = decidiu em 28d; p_ganha = ganhou em 28d.
# - fila 'fechar' se p_decide >= p_decide_min; ordem: fechar antes de preparar; dentro de fechar,
#   valor de tabela x p_ganha_28d (desc), desempate pelo menor prazo restante.
#   (em 'preparar' o motor usa p_ganha até o fim do trimestre; o revisor usa o mesmo.)
# - 'valor ganho' = preço de tabela dos escolhidos que ganharam em [c, c+28). O motor também usa preço de
#   tabela, não close_value (verificado em avaliacao/backtest.py).
def tabela_analogas(c, cmax):
    bordas_ = [b for b in bordas if b < cmax] + [cmax]
    analogas, x = [], c
    while True:
        x = x - pd.DateOffset(months=3)
        if x < p.close_date.min():
            break
        analogas.append(x)
    obs = []
    for A in analogas:
        al = p[(p.engage_date < A) & ~(p.close_date < A)].copy()
        al["idade"] = (A - al.engage_date).dt.days
        al = al[al.idade <= cmax]
        d28 = al.close_date.notna() & (al.close_date < A + pd.Timedelta(days=H))
        fim_tri = pd.Timestamp(A.year, 3 * ((A.month - 1) // 3) + 1, 1) + pd.DateOffset(months=3)
        dtri = al.close_date.notna() & (al.close_date < fim_tri)
        won = al.deal_stage == "Won"
        al["faixa"] = pd.cut(al.idade, [0] + bordas_, labels=False)
        obs.append(pd.DataFrame({"faixa": al.faixa, "d28": d28, "g28": d28 & won, "gtri": dtri & won}))
    o = pd.concat(obs)
    g = o.groupby("faixa").agg(n=("d28", "size"), d28=("d28", "sum"), g28=("g28", "sum"), gtri=("gtri", "sum"))
    # junta faixa rala (< n_min) à vizinha mais velha
    linhas, acc, membros = [], None, []
    for f, r in g.iterrows():
        acc = r.copy() if acc is None else acc + r
        membros.append(f)
        if acc.n >= CFG["n_min_faixa"]:
            linhas.append((list(membros), acc)); acc, membros = None, []
    if acc is not None and linhas:
        linhas[-1] = (linhas[-1][0] + membros, linhas[-1][1] + acc)
    m = {}
    for fs, r in linhas:
        for f in fs:
            m[f] = (r.d28 / r.n, r.g28 / r.n, r.gtri / r.n)
    return bordas_, m


res2 = []
for c in CORTES:
    fc, ab, cmax, ativa, frac = classificar(c)
    viv = ab[ab.estado == "vivo"].copy()
    b_, m = tabela_analogas(c, cmax)
    fx = pd.cut(viv.idade, [0] + b_, labels=False)
    viv["pdec"] = fx.map(lambda f: m.get(f, (0, 0, 0))[0])
    viv["pg28"] = fx.map(lambda f: m.get(f, (0, 0, 0))[1])
    viv["pgtri"] = fx.map(lambda f: m.get(f, (0, 0, 0))[2])
    viv["fila"] = np.where(viv.pdec >= CFG["p_decide_min"], 0, 1)
    viv["chave"] = np.where(viv.fila == 0, viv.sales_price * viv.pg28, viv.sales_price * viv.pgtri)
    viv["restante"] = (np.minimum(viv.engage_date + pd.Timedelta(days=cmax), viv.prazo) - c).dt.days
    real = p.set_index("opportunity_id")
    fim = c + pd.Timedelta(days=H)
    cd = viv.opportunity_id.map(real.close_date); st = viv.opportunity_id.map(real.deal_stage)
    viv["ganhou"] = (cd.notna() & (cd < fim) & (st == "Won")).astype(int)
    viv["vg"] = viv.ganhou * viv.sales_price
    top = lambda ch, asc: viv.sort_values(ch, ascending=asc).groupby("sales_agent").head(K)
    pol = {
        "relogio": top(["fila", "chave", "restante", "opportunity_id"], [True, False, True, True]),
        "preco_prazo_desc": top(["sales_price", "restante", "opportunity_id"], [False, False, True]),  # desempate: MAIS dias restantes
        "preco_prazo_asc": top(["sales_price", "restante", "opportunity_id"], [False, True, True]),    # desempate: MENOS dias restantes
    }
    for nome, sel in pol.items():
        for ag, g in sel.groupby("sales_agent"):
            res2.append((c, nome, ag, g.vg.sum(), g.ganhou.sum(), len(g)))
    print(f"{c.date()} vivos={len(viv)} fechar={(viv.fila == 0).sum()} " + " ".join(f"{n}={pol[n].vg.sum():,.0f}" for n in pol))
R2 = pd.DataFrame(res2, columns=["corte", "pol", "ag", "valor", "ganhos", "n"])
S2 = R2.groupby("pol")[["valor", "ganhos", "n"]].sum()
# taxa de acerto como média dos cortes (como o documento descreve "taxa média")
S2["acerto_media_cortes"] = R2.groupby(["pol", "corte"]).apply(lambda d: d.ganhos.sum() / d.n.sum()).groupby("pol").mean().round(3)
print(S2.to_string())
pv2 = R2.pivot_table(index="ag", columns="pol", values="valor", aggfunc="sum").fillna(0)
for alt_ in ["preco_prazo_desc", "preco_prazo_asc"]:
    obs = pv2.relogio.sum() / pv2[alt_].sum()
    bs = [(lambda s: s.relogio.sum() / s[alt_].sum())(pv2.iloc[RNG.integers(0, len(pv2), len(pv2))]) for _ in range(5000)]
    print(f"razão relogio / {alt_} = {obs:.3f}  IC95% bootstrap por vendedor [{np.quantile(bs, .025):.3f}, {np.quantile(bs, .975):.3f}]")
print("diferença relogio - preco_prazo_desc:", int(pv2.relogio.sum() - pv2.preco_prazo_desc.sum()))

titulo("8b. Atributos x 'ganhou em 28d' (1 registro por deal vivo com conta, 1º corte) — desenho do documento")
hist = []
for c in CORTES:
    fc, ab, *_ = classificar(c)
    v = ab[(ab.estado == "vivo") & ab.account.notna()].copy()
    real = p.set_index("opportunity_id")
    cd = v.opportunity_id.map(real.close_date); st = v.opportunity_id.map(real.deal_stage)
    v["ganhou"] = (cd.notna() & (cd < c + pd.Timedelta(days=H)) & (st == "Won")).astype(int)
    v["mes_tri"] = (c.month - 1) % 3
    hist.append(v)
hd = pd.concat(hist).drop_duplicates("opportunity_id").merge(team, on="sales_agent", how="left").merge(acc, on="account", how="left")
hd["porte"] = pd.qcut(hd.employees, 4, labels=False, duplicates="drop")
print("registros:", len(hd), "| taxa de ganho em 28d:", round(hd.ganhou.mean(), 3))
for col in ["account", "sales_agent", "manager", "regional_office", "sector", "porte", "pk"]:
    obs = hd.groupby(col).ganhou.mean().var()
    cnt = 0
    for _ in range(500):
        perm = hd.groupby("mes_tri").ganhou.transform(lambda s: RNG.permutation(s.values))
        cnt += hd.assign(g=perm).groupby(col).g.mean().var() >= obs
    print(f"{col:16s} permutação(500, estratificada por mês do trimestre) p={(cnt + 1) / 501:.3f}")

titulo("8. Atributos x ganhar (só fechados; teste do revisor)")
f = fech.merge(team, on="sales_agent", how="left").merge(acc, on="account", how="left")
f["ganhou"] = (f.deal_stage == "Won").astype(int)
f["porte"] = pd.qcut(f.employees, 4, labels=False)
f["produto"] = f.pk
f["mes_tri"] = (f.close_date.dt.month - 1) % 3
print("taxa de ganho geral entre fechados:", round(f.ganhou.mean(), 3), "n =", len(f))
for col in ["account", "sales_agent", "manager", "regional_office", "sector", "porte", "produto"]:
    ct = pd.crosstab(f[col], f.ganhou)
    chi2, pv_, dof, _ = chi2_contingency(ct)
    # permutação simples estratificada por mês do trimestre (estatística = qui-quadrado)
    obs = chi2
    g = f[[col, "ganhou", "mes_tri"]].dropna()
    cnt = 0
    for _ in range(300):
        perm = g.groupby("mes_tri").ganhou.transform(lambda s: RNG.permutation(s.values))
        cnt += chi2_contingency(pd.crosstab(g[col], perm))[0] >= obs
    print(f"{col:16s} grupos={ct.shape[0]:3d}  min/max taxa={ (ct[1] / ct.sum(axis=1)).min():.3f}/{(ct[1] / ct.sum(axis=1)).max():.3f}  "
          f"qui2 p={pv_:.3f}  permutação(300) p={(cnt + 1) / 301:.3f}")

titulo("9. Taxa-base de decisão em 28 dias, um registro por negócio")
for nome, cortes in [("6 cortes de 28d", CORTES)]:
    primeiro = {}
    for c in cortes:
        fc, ab, *_ = classificar(c)
        for oid in ab.loc[ab.estado == "vivo", "opportunity_id"]:
            primeiro.setdefault(oid, c)
    s = pd.Series(primeiro)
    r = p.set_index("opportunity_id").loc[s.index]
    dec = r.close_date.notna() & (r.close_date < s + pd.Timedelta(days=H))
    print(f"{nome}: negócios vivos distintos = {len(s)}; decidiram em 28d do 1º corte vivo = {dec.mean():.3f}")
# todas as aparições (deal x corte), para comparação
tot_n = tot_d = 0
for c in CORTES:
    fc, ab, *_ = classificar(c)
    v = ab[ab.estado == "vivo"]
    r = p.set_index("opportunity_id").loc[v.opportunity_id]
    tot_n += len(v)
    tot_d += int((r.close_date.notna() & (r.close_date < c + pd.Timedelta(days=H))).sum())
print(f"todas as aparições deal x corte: n={tot_n}, decidiram={tot_d / tot_n:.3f}")

titulo("10. Aritmética derivada do resumo executivo")
print("1.097.324 - 842.462 =", 1097324 - 842462, "| por vendedor por corte (30 x 6):", round((1097324 - 842462) / 180, 1))
for h in [25, 50, 100]:
    print(f"horas de equilíbrio a US$ {h}/h: {1416 / h:.1f}")
print("razão de acertos 0,227/0,147 =", round(.227 / .147, 3), "| fração do teto:", round(1097324 / 2666327, 3), round(842462 / 2666327, 3))
from math import sqrt
z = NormalDist().inv_cdf(.975) + NormalDist().inv_cdf(.8)
p1, p2 = .173, .223
print("n por braço (2 proporções, 17,3% -> 22,3%, alfa 5%, poder 80%):",
      round(z ** 2 * (p1 * (1 - p1) + p2 * (1 - p2)) / (p2 - p1) ** 2))
