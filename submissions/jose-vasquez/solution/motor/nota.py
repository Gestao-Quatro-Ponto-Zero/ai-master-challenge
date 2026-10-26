"""Motor do Lead Scorer "Segunda-feira".

Lê os CSVs, aprende com o passado e grava solution/app/dados.js com:
  - a nota de cada venda aberta, o motivo e a próxima ação;
  - as 5 vendas da semana de cada vendedor (nota 20 ou mais);
  - o "pipeline de verdade" para a chefe de vendas.

A chance de uma venda é medida com "fotos do passado": em cada fim de mês,
quais vendas estavam abertas, há quantos dias, e quantas foram ganhas nos
90 dias seguintes. O motor nunca usa informação posterior à data da foto.

Rodar: python3 solution/motor/nota.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
SAIDA = RAIZ / "app" / "dados.js"
HOJE = pd.Timestamp("2017-12-31")  # último dia com dado no dataset

HORIZONTE = 90           # chance de fechar nos próximos 90 dias
FAIXAS = [-1, 7, 14, 30, 45, 60, 75, 90, 100, 110, 120, 130, 138, 100_000]
INICIO_ESFRIAR = 100     # a partir daqui a chance cai mês a mês
POR_SEMANA = 5           # vendas na lista "as 5 da semana"
NOTA_MINIMA = 20         # abaixo disso (os 20% de menor valor) a venda não entra na semana


# ---------------------------------------------------------------- dados

def carregar(data_dir=DATA):
    p = pd.read_csv(data_dir / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
    a = pd.read_csv(data_dir / "accounts.csv")
    pr = pd.read_csv(data_dir / "products.csv")
    t = pd.read_csv(data_dir / "sales_teams.csv")
    p["product"] = p["product"].replace({"GTXPro": "GTX Pro"})
    a["sector"] = a["sector"].replace({"technolgy": "technology"})
    return (p.merge(t, on="sales_agent", how="left")
             .merge(pr, on="product", how="left")
             .merge(a[["account", "sector"]], on="account", how="left"))


def abertas_em(df, t):
    """Vendas em negociação na data t, vistas como se fosse aquele dia."""
    ab = df[(df.engage_date <= t) & ((df.close_date > t) | df.close_date.isna())].copy()
    ab["dias"] = (t - ab.engage_date).dt.days
    return ab


def vitorias_previas(df, vendas, t):
    """Quantas vendas o vendedor já ganhou com aquele cliente até a data t."""
    ganhas = df[(df.deal_stage == "Won") & (df.close_date <= t)]
    n = ganhas.groupby(["sales_agent", "account"]).size()
    return np.array([n.get((s, a), 0) for s, a in zip(vendas.sales_agent, vendas.account)])


# ---------------------------------------------------------------- aprender

def fotos_do_passado(df, ate):
    """Uma foto por fim de mês, só com vendas que têm cliente (registros completos)."""
    fotos = []
    ultima = ate - pd.Timedelta(days=HORIZONTE)  # a foto precisa de 90 dias de futuro conhecido
    for t in pd.date_range(df.engage_date.min(), ultima, freq="ME"):
        ab = abertas_em(df[df.account.notna()], t)
        if ab.empty:
            continue
        ab["ganhou"] = (ab.deal_stage == "Won") & (ab.close_date <= t + pd.Timedelta(days=HORIZONTE))
        ab["ja_ganhou"] = vitorias_previas(df, ab, t) > 0
        ab["foto"] = t
        fotos.append(ab)
    return pd.concat(fotos)


class Modelo:
    def __init__(self, fotos, prazo_maximo, fase_risco):
        fotos = fotos.assign(faixa=pd.cut(fotos.dias, FAIXAS))
        self.tabela = fotos.groupby("faixa", observed=False).ganhou.agg(chance="mean", base="size")
        self.tabela["chance"] = self.tabela["chance"].fillna(0.0)
        geral = fotos[fotos.dias <= prazo_maximo].ganhou.mean()
        rel = fotos[fotos.dias <= prazo_maximo].groupby("ja_ganhou").ganhou.mean()
        self.relacao = {True: rel.get(True, geral) / geral, False: rel.get(False, geral) / geral}
        self.taxa_relacao = {True: float(rel.get(True, geral)), False: float(rel.get(False, geral))}
        self.prazo_maximo = prazo_maximo
        self.fase_risco = fase_risco
        self.fotos = int(fotos.foto.nunique())
        self.ajuste = 1.0  # ajuste pelo último trimestre conhecido (ver calibrar)

    def chance_faixa(self, dias):
        return float(self.tabela.chance.iloc[pd.cut([dias], FAIXAS).codes[0]])

    def chance(self, dias, ja_ganhou):
        if dias > self.prazo_maximo:
            return 0.0
        return min(1.0, self.chance_faixa(dias) * self.relacao[bool(ja_ganhou)] * self.ajuste)

    def faixa_txt(self, dias):
        f = pd.cut([dias], FAIXAS)[0]
        return f"mais de {int(f.left)} dias" if f.right > 10_000 else f"{int(f.left) + 1} a {int(f.right)} dias"


def aprender(df, ate, calibrar=True):
    """Tudo o que o motor sabe vem de vendas encerradas até a data `ate`."""
    fech = df[df.close_date <= ate]
    dias_fech = (fech.close_date - fech.engage_date).dt.days
    prazo_maximo = int(dias_fech.max())
    fase_risco = int(dias_fech[fech.deal_stage == "Lost"].median())
    fotos = fotos_do_passado(ate_a_data(df, ate), ate)
    modelo = Modelo(fotos, prazo_maximo, fase_risco)
    if calibrar:
        modelo.ajuste, modelo.ajuste_base = calibrar_pelo_ultimo_trimestre(df, ate)
    return modelo


def calibrar_pelo_ultimo_trimestre(df, ate):
    """A chance de ganhar caiu ao longo de 2017, e as fotos têm 90 dias de atraso.
    Por isso o motor confere quanto errou no último trimestre já conhecido:
    volta 90 dias, prevê com o que se sabia lá e compara com o que fechou até `ate`.
    A chance de hoje é multiplicada por (ganhas de fato / ganhas previstas)."""
    antes = ate - pd.Timedelta(days=HORIZONTE)
    visto_antes = ate_a_data(df, antes)
    if (visto_antes.close_date.notna()).sum() == 0:
        return 1.0, None  # ainda não há trimestre fechado para conferir
    modelo = aprender(df, antes, calibrar=False)
    ab = abertas_em(visto_antes, antes)
    ab = ab[ab.account.notna() & (ab.dias <= modelo.prazo_maximo)]
    previstas = classificar(ab, modelo, antes, visto_antes).chance.sum()
    agora = ate_a_data(df, ate).loc[ab.index]
    ganhas = ((agora.deal_stage == "Won") & (agora.close_date <= ate)).sum()
    return float(ganhas / previstas), {"previstas": round(float(previstas)), "ganhas": int(ganhas)}


def ate_a_data(df, t):
    """O CRM como estava no dia t: o que fechou depois ainda aparece aberto."""
    visto = df[df.engage_date <= t].copy()
    depois = visto.close_date > t
    visto.loc[depois, "deal_stage"] = "Engaging"
    visto.loc[depois, ["close_date", "close_value"]] = [pd.NaT, np.nan]
    return visto


# ---------------------------------------------------------------- dar nota

def classificar(abertas, modelo, hoje, df, separar_sem_cliente=True):
    """Status, chance e valor esperado de cada venda aberta na data `hoje`."""
    v = abertas.copy()
    v["ja_ganhou"] = vitorias_previas(df, v, hoje) > 0
    v["vitorias"] = vitorias_previas(df, v, hoje)
    sem_data = v.engage_date.isna()
    dias = v.dias.fillna(0)
    v["chance"] = [modelo.chance(d, j) for d, j in zip(dias, v.ja_ganhou)]
    v["status"] = np.select(
        [sem_data, v.dias > modelo.prazo_maximo, v.dias > INICIO_ESFRIAR, v.dias <= modelo.fase_risco],
        ["prospeccao", "revisar", "esfriando", "risco"], default="ativa")
    if separar_sem_cliente:
        # Parada há mais tempo que qualquer venda da história: revisar vem antes de cadastrar.
        sem_cliente = v.account.isna() & (v.status != "revisar")
        v.loc[sem_cliente, "status"] = "cadastro"
        v.loc[sem_cliente, "chance"] = 0.0
    v["valor_esperado"] = v.chance * v.sales_price
    return v


# ---------------------------------------------------------------- explicar

def dinheiro(x):
    return "US$ " + f"{x:,.0f}".replace(",", ".")


def pct(x):
    return f"{x * 100:.0f}%"


ACOES = {
    "risco": "Falar com o cliente esta semana: metade das vendas perdidas morre nos primeiros dias.",
    "ativa": "Avançar para a proposta e combinar a data da decisão.",
    "esfriando": "Pedir uma decisão ao cliente: depois de 138 dias nenhuma venda fechou.",
    "prospeccao": "Fazer o primeiro contato e abrir a negociação.",
    "revisar": "Confirmar com o cliente se a venda ainda existe; se não, encerrar no CRM.",
    "cadastro": "Cadastrar o cliente no CRM.",
}


def motivos(v, modelo):
    m = [f"{v['product']} custa {dinheiro(v['sales_price'])}."]
    if v["status"] == "prospeccao":
        m.append("Ainda em prospecção, sem data de início no CRM. "
                 f"Usamos a chance de uma venda que acabou de começar: {pct(modelo.chance_faixa(0))}.")
    elif v["status"] == "revisar":
        m.append(f"Aberta há {int(v['dias'])} dias. Nenhuma venda da história levou mais de "
                 f"{modelo.prazo_maximo} dias para fechar.")
        return m
    elif v["status"] == "cadastro":
        m.append("Venda sem cliente cadastrado. Nenhuma das vendas encerradas da história estava sem cliente, "
                 "então não dá para calcular a chance dela.")
        return m
    else:
        m.append(f"Aberta há {int(v['dias'])} dias. No passado, vendas com {modelo.faixa_txt(v['dias'])} "
                 f"abertas foram ganhas {pct(modelo.chance_faixa(v['dias']))} das vezes nos 90 dias seguintes.")
    if v["vitorias"] > 0:
        m.append(f"Você já ganhou {int(v['vitorias'])} venda{'s' if v['vitorias'] > 1 else ''} com {v['account']}: "
                 f"isso aumenta a chance ({pct(modelo.taxa_relacao[True])} contra {pct(modelo.taxa_relacao[False])}).")
    elif pd.notna(v["account"]):
        m.append(f"Primeira venda sua com {v['account']}: sem histórico, a chance é um pouco menor "
                 f"({pct(modelo.taxa_relacao[False])} contra {pct(modelo.taxa_relacao[True])}).")
    m.append(f"Chance de fechar em 90 dias: {pct(v['chance'])}, já com o ajuste do último trimestre. "
             f"Valor esperado: {dinheiro(v['valor_esperado'])}.")
    return m


# ---------------------------------------------------------------- gerar a tela

def notas_0_100(valores):
    """Posição do valor esperado entre as vendas da lista (0 a 100)."""
    return (valores.rank(pct=True) * 100).round().astype(int)


def gerar(data_dir=DATA, hoje=HOJE):
    df = carregar(data_dir)
    modelo = aprender(df, hoje)
    ab = df[df.deal_stage.isin(["Engaging", "Prospecting"])].copy()
    ab["dias"] = (hoje - ab.engage_date).dt.days
    v = classificar(ab, modelo, hoje, df)

    prio = v.status.isin(["risco", "ativa", "esfriando", "prospeccao"])
    v["nota"] = 0
    v.loc[prio, "nota"] = notas_0_100(v.loc[prio, "valor_esperado"])
    v["semana"] = False
    candidatas = prio & (v.nota >= NOTA_MINIMA)
    topo = (v[candidatas].sort_values(["valor_esperado", "chance"], ascending=False)
                    .groupby("sales_agent").head(POR_SEMANA).index)
    v.loc[topo, "semana"] = True

    vendas = []
    for _, x in v.iterrows():
        vendas.append({
            "id": x.opportunity_id, "vendedor": x.sales_agent, "gerente": x.manager, "regiao": x.regional_office,
            "produto": x["product"], "cliente": x.account if pd.notna(x.account) else None,
            "setor": x.sector if pd.notna(x.sector) else None,
            "inicio": x.engage_date.strftime("%Y-%m-%d") if pd.notna(x.engage_date) else None,
            "dias": int(x.dias) if pd.notna(x.dias) else None,
            "status": x.status, "nota": int(x.nota), "semana": bool(x.semana),
            "chance": round(float(x.chance), 3), "preco": int(x.sales_price),
            "valor_esperado": round(float(x.valor_esperado), 2),
            "motivos": motivos(x, modelo), "acao": ACOES[x.status],
        })

    meta = {
        "hoje": hoje.strftime("%Y-%m-%d"),
        "prazo_maximo": modelo.prazo_maximo, "fase_risco": modelo.fase_risco,
        "inicio_esfriar": INICIO_ESFRIAR, "por_semana": POR_SEMANA, "nota_minima": NOTA_MINIMA,
        "relacao": {"ja_ganhou": round(modelo.taxa_relacao[True], 3),
                    "sem_historico": round(modelo.taxa_relacao[False], 3)},
        "tabela_chance": [{"de": int(f.left) + 1, "ate": int(f.right), "chance": round(float(c), 3), "base": int(b)}
                          for f, c, b in zip(modelo.tabela.index, modelo.tabela.chance, modelo.tabela.base)],
        "vendas_encerradas": int(df.deal_stage.isin(["Won", "Lost"]).sum()),
        "fotos_do_passado": modelo.fotos,
        "ajuste": round(modelo.ajuste, 3), "ajuste_base": modelo.ajuste_base,
    }
    teste = RAIZ.parent / "docs" / "resultado-teste.json"
    if teste.exists():
        meta["teste"] = json.loads(teste.read_text(encoding="utf-8"))

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("window.DADOS = " + json.dumps({"meta": meta, "vendas": vendas}, ensure_ascii=False) + ";\n",
                     encoding="utf-8")
    return v, modelo


def main():
    v, modelo = gerar()
    print(f"{len(v)} vendas abertas: {v.status.value_counts().to_dict()}")
    print(f"As 5 da semana: {int(v.semana.sum())} vendas para {v[v.semana].sales_agent.nunique()} vendedores")
    print(f"Prazo máximo {modelo.prazo_maximo} dias, fase de risco até {modelo.fase_risco} dias")
    print(f"Arquivo gerado: {SAIDA}")


if __name__ == "__main__":
    main()
