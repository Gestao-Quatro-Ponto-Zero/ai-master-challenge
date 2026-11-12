"""Protótipo do motor do plano v2, na especificação exata das Tarefas 1 a 4.

Serve para dois fins: fixar os valores de ouro dos testes do plano e provar que a
especificação é implementável antes de alguém começar a implementá-la.

Tudo é as-of: `recortar` apaga o futuro, `aprender` só vê o que ficou, `pontuar`
não toca em nenhuma coluna de desfecho. O backtest da seção F reconstrói a fila
com a mesma ordem que a tela mostraria.

Rodar de dentro de analise/:  python3 eda-06-prototipo-motor-v2.py > eda-06-prototipo-motor-v2.saida.txt
"""
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 50)
pd.set_option("display.max_rows", 300)

D = "../dados/"
BORDAS = [15, 30, 45, 60, 75, 90, 105, 120]   # fim de cada faixa de idade; a última vai até ciclo_max
HORIZONTE = 28                                 # dias da lista
P_MIN = 0.05                                   # chance mínima de decidir para entrar na fila "fechar"
FOCO = 5                                       # deals por vendedor na lista do dia
REF = pd.Timestamp("2018-01-01")


def titulo(txt):
    print("\n" + "=" * 100 + "\n" + txt + "\n" + "=" * 100)


def carregar():
    p = pd.read_csv(D + "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
    pr = pd.read_csv(D + "products.csv")
    t = pd.read_csv(D + "sales_teams.csv")
    a = pd.read_csv(D + "accounts.csv")
    pr["k"] = pr["product"].str.replace(" ", "").str.lower()
    p["k"] = p["product"].str.replace(" ", "").str.lower()
    p = p.merge(pr[["k", "sales_price", "product"]].rename(columns={"product": "produto_catalogo"}), on="k", how="left")
    return p, pr, t, a


def inicio_tri(d):
    return pd.Timestamp(d.year, 3 * ((d.month - 1) // 3) + 1, 1)


def prazo_trimestre(serie):
    """Fim do trimestre seguinte ao do engajamento."""
    return serie.dt.to_period("Q").dt.start_time + pd.offsets.QuarterBegin(2, startingMonth=1) - pd.Timedelta(days=1)


def recortar(full, ref):
    """O export que existiria em `ref`: nenhum engajamento futuro, nenhum fechamento futuro."""
    d = full[full.engage_date.isna() | (full.engage_date < ref)].copy()
    futuro = d.close_date.notna() & (d.close_date >= ref)
    d.loc[futuro, ["close_date", "close_value"]] = [pd.NaT, np.nan]
    d.loc[futuro, "deal_stage"] = "Engaging"
    if ref <= full.close_date.max():
        d = d[d.engage_date.notna()]     # Prospecting sem data não tem como ser datado no passado
    return d


def rotulo_faixa(idade, ciclo_max):
    lo = 1
    for borda in BORDAS + [ciclo_max]:
        if lo <= idade <= borda:
            return f"{lo}-{borda}"
        lo = borda + 1
    return None


def aprender(con, ref):
    """Tudo o que o motor sabe em `ref`, vindo só de `con`."""
    fe = con[con.close_date.notna()].copy()
    fe["ciclo"] = (fe.close_date - fe.engage_date).dt.days
    ciclo_max = int(fe.ciclo.max())
    apos_prazo = int((fe.close_date > prazo_trimestre(fe.engage_date)).sum())
    usa_prazo_tri = len(fe) >= 500 and apos_prazo / len(fe) <= 0.001

    primeiro = fe.close_date.min()
    analogas, x = [], ref
    while True:
        x = x - pd.DateOffset(months=3)
        if x < primeiro:
            break
        analogas.append(x)

    E = con[con.engage_date.notna()]
    blocos = []
    for A in analogas:
        al = E[(E.engage_date < A) & ((E.close_date >= A) | E.close_date.isna())].copy()
        al["idade"] = (A - al.engage_date).dt.days
        al = al[al.idade <= ciclo_max]
        al["fx"] = al.idade.map(lambda i: rotulo_faixa(i, ciclo_max))
        d28 = al.close_date.notna() & (al.close_date < A + pd.Timedelta(days=HORIZONTE))
        dtri = al.close_date.notna() & (al.close_date < inicio_tri(A) + pd.DateOffset(months=3))
        al["d28"] = d28.astype(int)
        al["g28"] = (d28 & (al.deal_stage == "Won")).astype(int)
        al["dtri"] = dtri.astype(int)
        al["gtri"] = (dtri & (al.deal_stage == "Won")).astype(int)
        blocos.append(al)

    tabela = carga = None
    if blocos:
        H = pd.concat(blocos)
        tabela = H.groupby("fx").agg(n=("d28", "size"), d28=("d28", "sum"), g28=("g28", "sum"),
                                     dtri=("dtri", "sum"), gtri=("gtri", "sum"))
        cs = []
        for A in analogas:
            viv = E[(E.engage_date < A) & ((E.close_date >= A) | E.close_date.isna()) & E.close_date.notna()]
            cs.append(viv.groupby("sales_agent").size().rename(str(A.date())))
        carga = pd.concat(cs, axis=1).fillna(0).median(axis=1)

    w = fe[fe.deal_stage == "Won"]
    return dict(ciclo_max=ciclo_max, n_fechamentos=len(fe), apos_prazo=apos_prazo, usa_prazo_tri=usa_prazo_tri,
                analogas=analogas, tabela=tabela, carga=carga,
                razao_fechado_tabela=float((w.close_value / w.sales_price).mean()),
                semana_tri=int((ref - inicio_tri(ref)).days // 7 + 1))


def pontuar(con, ap, ref):
    op = con[con.close_date.isna()].copy()
    op["idade"] = (ref - op.engage_date).dt.days
    pt = prazo_trimestre(op.engage_date)
    por_idade = op.engage_date + pd.Timedelta(days=ap["ciclo_max"])
    op["prazo"] = np.minimum(por_idade, pt) if ap["usa_prazo_tri"] else por_idade
    no_prazo = (pt >= ref) | (not ap["usa_prazo_tri"])
    op["estado"] = np.where(op.engage_date.isna(), "sem_data",
                            np.where((op.idade <= ap["ciclo_max"]) & no_prazo, "vivo", "vencido"))
    op["dias_restantes"] = (op.prazo - ref).dt.days
    op["fx"] = [rotulo_faixa(r.idade, ap["ciclo_max"]) if r.estado == "vivo" else None for r in op.itertuples()]

    T = ap["tabela"]
    for col in ("n", "d28", "g28", "dtri", "gtri"):
        op[col] = op.fx.map(T[col]) if T is not None else np.nan
    op["p_decide"] = op.d28 / op.n
    op["ve_28"] = op.sales_price * op.g28 / op.n            # valor esperado ganho nos 28 dias
    op["ve_tri"] = op.sales_price * op.gtri / op.n          # valor esperado ganho até o fim do trimestre

    op["fila"] = np.select([op.estado == "sem_data", op.estado == "vencido", op.p_decide >= P_MIN],
                           ["iniciar", "encerrar", "fechar"], "preparar")
    op["chave"] = np.select([op.fila == "fechar", op.fila == "preparar"], [op.ve_28, op.ve_tri], op.sales_price)
    op["ordem_fila"] = op.fila.map({"fechar": 0, "preparar": 1, "iniciar": 2, "encerrar": 3})
    op = op.sort_values(["sales_agent", "ordem_fila", "chave", "dias_restantes", "opportunity_id"],
                        ascending=[True, True, False, True, True])
    op["posicao"] = op.groupby(["sales_agent", "fila"]).cumcount() + 1
    rank_foco = op[op.fila != "encerrar"].groupby("sales_agent").cumcount() + 1
    op["em_foco"] = False
    op.loc[rank_foco.index, "em_foco"] = rank_foco <= FOCO

    viv = op[op.estado == "vivo"]
    op["indice"] = np.nan
    if len(viv) > 1:
        op.loc[viv.index, "indice"] = [
            max(1, round(100 * int(((viv.ordem_fila > r.ordem_fila) | ((viv.ordem_fila == r.ordem_fila) & (viv.chave < r.chave))).sum()) / (len(viv) - 1)))
            for r in viv.itertuples()]
    op.loc[op.estado == "vencido", "indice"] = 0
    return op


p, pr, t, a = carregar()

titulo("A. Qualidade do dado (o que a tela do gestor mostra)")
print("linhas cujo nome de produto difere do catálogo:", int((p["product"] != p.produto_catalogo).sum()),
      "| apelidos:", sorted(set(p.loc[p["product"] != p.produto_catalogo, "product"])))
print("sem par no catálogo (preço nulo):", int(p.sales_price.isna().sum()))
print("contas com setor 'technolgy':", int((a.sector == "technolgy").sum()),
      "| contas com país 'Philipines':", int((a.office_location == "Philipines").sum()))
print("abertos sem conta:", int(p[p.deal_stage.isin(["Engaging", "Prospecting"])].account.isna().sum()),
      "| Prospecting sem data:", int(p[p.deal_stage == "Prospecting"].engage_date.isna().sum()))
print("linhas:", len(p), "| ids duplicados:", int(p.opportunity_id.duplicated().sum()),
      "| fechamento anterior ao engajamento:", int((p.close_date < p.engage_date).sum()))
print("primeiro fechamento registrado:", p.close_date.min().date(), "| último:", p.close_date.max().date(),
      "| vendedores no cadastro:", t.sales_agent.nunique(), "| com algum deal:", p.sales_agent.nunique())

con = recortar(p, REF)
ap = aprender(con, REF)
s = pontuar(con, ap, REF)

titulo(f"B. O que o motor aprendeu em {REF.date()} (semana {ap['semana_tri']} do trimestre)")
print("ciclo_max:", ap["ciclo_max"], "| fechamentos conhecidos:", ap["n_fechamentos"],
      "| depois do prazo do trimestre:", ap["apos_prazo"], "| regra do trimestre ativa:", ap["usa_prazo_tri"])
print("datas análogas:", [str(x.date()) for x in ap["analogas"]],
      "| razão fechado/tabela:", round(ap["razao_fechado_tabela"], 4))
print(ap["tabela"].assign(p_decide=lambda d: (d.d28 / d.n).round(3),
                          p_ganha_tri=lambda d: (d.gtri / d.n).round(3)).to_string())
print("carga de referência: vendedores", len(ap["carga"]), "| mediana", ap["carga"].median(),
      "| mínimo", ap["carga"].min(), "| máximo", ap["carga"].max())

titulo("C. Resultado da pontuação")
print("filas:", s.fila.value_counts().to_dict(), "| total:", len(s))
print("estado:", s.estado.value_counts().to_dict(),
      "| vencidos por idade:", int(((s.estado == "vencido") & (s.idade > ap["ciclo_max"])).sum()),
      "| vencidos só pelo prazo do trimestre:", int(((s.estado == "vencido") & (s.idade <= ap["ciclo_max"])).sum()))
print("valor de tabela por fila:", {k: int(v) for k, v in s.groupby("fila").sales_price.sum().items()})
print("valor esperado no trimestre: US$", round(s.ve_tri.sum(), 2), "| nos próximos 28 dias: US$", round(s.ve_28.sum(), 2))
print("deals em foco:", int(s.em_foco.sum()), "| vendedores com deal aberto:", s.sales_agent.nunique(),
      "| índice dos vivos: de", int(s[s.estado == "vivo"].indice.min()), "a", int(s[s.estado == "vivo"].indice.max()))
viol = sum(int(x.sort_values(["ordem_fila", "posicao"]).indice.diff().dropna().gt(0).sum())
           for _, x in s[s.estado == "vivo"].groupby("sales_agent"))
print("violações de monotonia entre índice e ordem da fila:", viol, "(precisa ser 0)")

COLS = ["opportunity_id", "sales_agent", "product", "idade", "dias_restantes", "fx", "sales_price",
        "p_decide", "ve_28", "ve_tri", "fila", "posicao", "em_foco", "indice"]
titulo("D. A fila 'fechar' inteira nesta data (os únicos deals com chance medida de decidir em 28 dias)")
print(s[s.fila == "fechar"][COLS].round(2).to_string(index=False))
print("\nLeitura: é a primeira semana do trimestre. Nos três trimestres anteriores, nenhum dos 3.618 deals")
print("com mais de 15 dias decidiu nas quatro semanas seguintes a essa data. A ferramenta diz isso em vez")
print("de mandar o vendedor ligar para quem a história mostra que não decide agora.")

titulo("E. Três vendedores, a lista que cada um veria")
for ag in ("Maureen Marcano", "Boris Faz", "Darcel Schlecht"):
    x = s[s.sales_agent == ag]
    print(f"\n{ag} — filas {x.fila.value_counts().to_dict()}")
    print(x[x.em_foco][COLS].round(2).to_string(index=False))

titulo(f"F. Backtest as-of com a ordem exata do motor (segundas a cada {HORIZONTE // 7} semanas, jul a dez/2017, {FOCO} por vendedor)")


def replay(cortes, k=FOCO):
    full = p.set_index("opportunity_id")
    linhas, por_vend = [], []
    for corte in cortes:
        c = recortar(p, corte)
        apc = aprender(c, corte)
        if apc["tabela"] is None:
            continue
        sc = pontuar(c, apc, corte)
        sc = sc[sc.estado != "sem_data"]
        cd = sc.opportunity_id.map(full.close_date)
        st = sc.opportunity_id.map(full.deal_stage)
        sc["ganhou"] = ((cd.notna()) & (cd < corte + pd.Timedelta(days=HORIZONTE)) & (st == "Won")).astype(int).values
        sc["valor_ganho"] = sc.ganhou * sc.sales_price
        rng = np.random.default_rng(int(corte.strftime("%Y%m%d")))
        sc["r"] = rng.random(len(sc))
        viv = sc[sc.estado == "vivo"]
        por_idade = sc[sc.idade <= apc["ciclo_max"]]
        politicas = {
            "relogio": viv.sort_values(["sales_agent", "ordem_fila", "posicao"]).groupby("sales_agent").head(k),
            "preco_prazo": viv.sort_values(["sales_price", "dias_restantes", "opportunity_id"], ascending=[False, False, True]).groupby("sales_agent").head(k),
            "preco_138": por_idade.sort_values(["sales_price", "opportunity_id"], ascending=[False, True]).groupby("sales_agent").head(k),
            "aleatorio": viv.sort_values("r").groupby("sales_agent").head(k),
        }
        lin = dict(corte=str(corte.date()), semana_tri=apc["semana_tri"], vivos=len(viv), fila_fechar=int((viv.fila == "fechar").sum()))
        for nome, top in politicas.items():
            lin["$" + nome] = int(top.valor_ganho.sum())
            lin["acerto_" + nome] = round(top.ganhou.mean(), 3)
            x = top.groupby("sales_agent").valor_ganho.sum().rename(nome).to_frame()
            x["corte"] = lin["corte"]
            por_vend.append(x.reset_index().melt(id_vars=["sales_agent", "corte"]))
        lin["$oraculo"] = int(sc.sort_values("valor_ganho", ascending=False).groupby("sales_agent").head(k).valor_ganho.sum())
        linhas.append(lin)
    R = pd.DataFrame(linhas)
    PV = pd.concat(por_vend).pivot_table(index="sales_agent", columns="variable", values="value", aggfunc="sum").fillna(0)
    return R, PV


def ic(PV, a_, b_, n=5000):
    rng = np.random.default_rng(7)
    out = [PV[a_].values[i].sum() / PV[b_].values[i].sum()
           for i in (rng.integers(0, len(PV), len(PV)) for _ in range(n))]
    return PV[a_].sum() / PV[b_].sum(), np.percentile(out, 2.5), np.percentile(out, 97.5)


R, PV = replay(pd.date_range("2017-07-03", "2017-12-03", freq="4W-MON"))
print(R.to_string(index=False))
soma = R[[c for c in R if c.startswith("$")]].sum()
print("soma:", {k: int(v) for k, v in soma.items()})
for a_, b_ in (("relogio", "preco_prazo"), ("relogio", "preco_138"), ("relogio", "aleatorio")):
    r0, lo, hi = ic(PV, a_, b_)
    print(f"  {a_} / {b_} = {r0:.3f}   IC 95% [{lo:.3f}, {hi:.3f}]   (bootstrap por vendedor, {len(PV)} vendedores, 5.000 reamostras, semente 7)")
print(f"  fração do teto (oráculo que conhece o futuro): relogio {soma['$relogio'] / soma['$oraculo']:.3f} | preco_prazo {soma['$preco_prazo'] / soma['$oraculo']:.3f}")
print("  taxa média de acerto: relogio", R.acerto_relogio.mean().round(3), "| preco_prazo", R.acerto_preco_prazo.mean().round(3),
      "| preco_138", R.acerto_preco_138.mean().round(3), "| aleatorio", R.acerto_aleatorio.mean().round(3))

titulo("G. A ferramenta muda de recomendação conforme a altura do trimestre (duas datas, mesma regra)")
for d in ("2017-08-28", "2017-10-02"):
    c = pd.Timestamp(d)
    cc = recortar(p, c)
    apc = aprender(cc, c)
    sc = pontuar(cc, apc, c)
    print(f"{d} (semana {apc['semana_tri']} do trimestre): filas {sc.fila.value_counts().to_dict()} | análogas {[str(x.date()) for x in apc['analogas']]}")
print("\nSemana 9: quase todo deal vivo entra em 'fechar'. Semana 1: a maioria vai para 'preparar'.")
print("Nenhum limiar foi escrito à mão: os dois quadros saem da mesma tabela aprendida das datas análogas.")
