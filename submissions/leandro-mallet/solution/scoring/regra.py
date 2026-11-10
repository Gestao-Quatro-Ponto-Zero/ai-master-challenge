"""Regra do lead score (decisões 28 a 40; detalhes em desenho.md e regra-lead-score.html).

NOTA = 0,70 × FIT + 0,30 × HEAT + BONUS, de 0 a 120.

Só funções puras sobre DataFrames: nada aqui lê arquivo ou banco.
Entrada: tabelas no formato do banco (core_deals, core_contas, core_produtos).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

VERSAO = "lead-score-1.0"
PESOS = {"fit": 0.70, "heat": 0.30, "bonus_max": 20}

# FIT
ENCOLHIMENTO = 20          # (ganhos + 20 × taxa do vendedor) / (fechados + 20)
MINIMO_CASOS = 10          # característica com menos fechados na janela vale desvio 0
CORTE_DESTAQUE = 0.03      # destaque a menos de 3 pontos da média = vendedor sem destaque (FIT 50)
JANELA_MESES = 3
DIMENSOES = {              # característica -> coluna
    "produto": "produto_nome",
    "serie": "serie",
    "setor": "setor",
    "receita": "faixa_receita",
    "funcionarios": "faixa_funcionarios",
    "empresa": "conta_nome",
    "sede": "sede",
}
ROTULO_DIM = {"produto": "produto", "serie": "série", "setor": "setor", "receita": "receita",
              "funcionarios": "funcionários", "empresa": "empresa", "sede": "sede"}
FAIXAS_PORTE = ["pequena", "media", "grande"]

# HEAT
FAIXAS_HEAT = [  # (até dias, pontos, rótulo)
    (1, 100, "até 1 dia"), (7, 85, "2 a 7 dias"), (15, 70, "8 a 15 dias"), (30, 55, "16 a 30 dias"),
    (60, 40, "31 a 60 dias"), (90, 25, "61 a 90 dias"), (180, 10, "91 a 180 dias"), (None, 0, "181 dias ou mais"),
]
HEAT_SEM_DATA = 50
FATOR_CONTATO = [(7, 1.0), (14, 0.8), (30, 0.5), (None, 0.2)]
RISCO_ESFRIAR = (107, 138)   # marcador "risco_esfriar"; acima de 138 = "esfriou"
DESISTIR_ACIMA = 276         # proposta: o dobro do deal mais longo que já fechou
FIT_FURAR_FILA = 75

# BONUS
BONUS_HISTORICO = (0, 5, 10)   # terços da receita ganha
BONUS_JANELA = 10              # janela de compra por calendário (só com preferência acima do acaso)
JANELA_RECORTE = "semestre"


def _faixa(s: pd.Series) -> pd.Series:
    cortes = s.quantile([1 / 3, 2 / 3]).tolist()
    return pd.cut(s, [-np.inf, cortes[0], cortes[1], np.inf], labels=FAIXAS_PORTE).astype("string")


def preparar(deals: pd.DataFrame, contas: pd.DataFrame, produtos: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por deal com as 7 características, preço e datas."""
    c = contas.copy()
    c["faixa_receita"] = _faixa(c["receita_milhoes"].astype(float))
    c["faixa_funcionarios"] = _faixa(c["funcionarios"].astype(float))
    c["sede"] = np.where(c["pais"] == "United States", "EUA", "fora dos EUA")
    d = deals.merge(produtos[["nome", "serie", "preco"]].rename(columns={"nome": "produto_nome"}),
                    on="produto_nome", how="left", validate="m:1")
    d = d.merge(c[["nome", "setor", "faixa_receita", "faixa_funcionarios", "sede"]].rename(columns={"nome": "conta_nome"}),
                on="conta_nome", how="left", validate="m:1")
    for col in ["data_abertura", "close_date", "ultimo_contato_em"]:
        d[col] = pd.to_datetime(d[col]) if col in d else pd.NaT
    d["criado_em"] = pd.to_datetime(d["criado_em"], utc=True) if "criado_em" in d else pd.NaT
    return d


def janela(referencia: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    return referencia - pd.DateOffset(months=JANELA_MESES) + pd.Timedelta(days=1), referencia


@dataclass
class Celulas:
    """Taxas por vendedor e característica na janela."""
    taxa_vendedor: dict              # vendedor -> taxa
    fechados_vendedor: dict          # vendedor -> fechados na janela
    tabela: pd.DataFrame             # vendedor, dim, valor, n, ganhos, taxa_encolhida, desvio, ok
    destaque: pd.DataFrame           # por vendedor: dim, valor, n, ganhos, taxa_encolhida, desvio
    janela: tuple = field(default_factory=tuple)

    def __post_init__(self):
        self._idx = {(r.vendedor, r.dim, r.valor): r for r in self.tabela.itertuples(index=False)}

    def celula(self, vendedor, dim, valor):
        return self._idx.get((vendedor, dim, str(valor)))

    def tem_destaque(self, vendedor) -> bool:
        return vendedor in self.destaque.index and self.destaque.loc[vendedor, "desvio"] >= CORTE_DESTAQUE


def celulas(d: pd.DataFrame, referencia: pd.Timestamp) -> Celulas:
    ini, fim = janela(referencia)
    f = d[d["estagio"].isin(["Won", "Lost"]) & d["close_date"].between(ini, fim)].copy()
    f["ganhou"] = (f["estagio"] == "Won").astype(int)
    ag = f.groupby("vendedor_nome")["ganhou"].agg(["sum", "count"])
    taxa = (ag["sum"] / ag["count"]).to_dict()
    linhas = []
    for dim, col in DIMENSOES.items():
        g = f.dropna(subset=[col]).groupby(["vendedor_nome", col])["ganhou"].agg(["sum", "count"]).reset_index()
        g.columns = ["vendedor", "valor", "ganhos", "n"]
        g["dim"] = dim
        linhas.append(g)
    t = pd.concat(linhas, ignore_index=True)
    t["valor"] = t["valor"].astype(str)
    t["taxa_vendedor"] = t["vendedor"].map(taxa)
    t["taxa_encolhida"] = (t["ganhos"] + ENCOLHIMENTO * t["taxa_vendedor"]) / (t["n"] + ENCOLHIMENTO)
    t["ok"] = t["n"] >= MINIMO_CASOS
    t["desvio"] = np.where(t["ok"], t["taxa_encolhida"] - t["taxa_vendedor"], 0.0)
    elegiveis = t[t["ok"]].sort_values(["vendedor", "taxa_encolhida", "dim", "valor"], ascending=[True, False, True, True])
    destaque = elegiveis.groupby("vendedor").head(1).set_index("vendedor")
    return Celulas(taxa, ag["count"].to_dict(), t[["vendedor", "dim", "valor", "n", "ganhos", "taxa_encolhida", "desvio", "ok"]],
                   destaque, (ini, fim))


def fit_do_lead(cel: Celulas, vendedor: str, lead: pd.Series) -> dict:
    """FIT = 50 + 50 × média dos desvios das características com 10+ fechados ÷ desvio do destaque."""
    usadas, fora = [], []
    for dim, col in DIMENSOES.items():
        valor = lead.get(col)
        if valor is None or (isinstance(valor, float) and np.isnan(valor)) or pd.isna(valor):
            continue
        c = cel.celula(vendedor, dim, valor)
        item = {"dim": dim, "valor": str(valor), "n": int(c.n) if c else 0, "ganhos": int(c.ganhos) if c else 0,
                "taxa_encolhida": float(c.taxa_encolhida) if c else None, "desvio": float(c.desvio) if c else 0.0}
        (usadas if c is not None and c.ok else fora).append(item)
    if not cel.tem_destaque(vendedor):
        # sem destaque ou sem histórico na janela (decisão 49: os sem histórico entram com FIT 50 em todo lead)
        return {"fit": 50.0, "sem_destaque": True, "sem_historico": vendedor not in cel.taxa_vendedor,
                "usadas": usadas, "fora": fora, "media": 0.0, "destaque": None}
    dest = cel.destaque.loc[vendedor]
    media = float(np.mean([u["desvio"] for u in usadas])) if usadas else 0.0
    fit = float(np.clip(50 + 50 * media / dest["desvio"], 0, 100))
    return {"fit": fit, "sem_destaque": False, "sem_historico": False, "usadas": usadas, "fora": fora, "media": media,
            "destaque": {"dim": dest["dim"], "valor": dest["valor"], "n": int(dest["n"]), "ganhos": int(dest["ganhos"]),
                         "taxa_encolhida": float(dest["taxa_encolhida"]), "desvio": float(dest["desvio"])}}


def faixa_heat(dias) -> tuple[int, str]:
    if dias is None or pd.isna(dias):
        return HEAT_SEM_DATA, "sem data de abertura"
    for limite, pts, rot in FAIXAS_HEAT:
        if limite is None or dias <= limite:
            return pts, rot
    raise AssertionError


def fator_contato(dias_sem_contato) -> float:
    if dias_sem_contato is None or pd.isna(dias_sem_contato):
        return 1.0                      # sem histórico de contato no dataset: não inventa contato
    for limite, f in FATOR_CONTATO:
        if limite is None or dias_sem_contato <= limite:
            return f
    raise AssertionError


def padroes_conta(d: pd.DataFrame, referencia: pd.Timestamp) -> pd.DataFrame:
    """Histórico (terços da receita ganha) e janela de compra por calendário de cada empresa."""
    w = d[(d["estagio"] == "Won") & d["conta_nome"].notna() & (d["close_date"] <= referencia)].copy()
    g = w.groupby("conta_nome").agg(compras_ganhas=("opportunity_id", "size"), receita_ganha=("close_value", "sum"),
                                    ultima_compra=("close_date", "max"))
    cortes = g["receita_ganha"].quantile([1 / 3, 2 / 3]).tolist()
    g["terco"] = np.where(g["receita_ganha"] > cortes[1], 2, np.where(g["receita_ganha"] > cortes[0], 1, 0))
    g["bonus_historico"] = [BONUS_HISTORICO[i] for i in g["terco"]]
    # Janela de compra: semestre preferido acima do calendário geral, além do acaso (permutação + Bonferroni).
    # Nestes dados nenhuma empresa passa (ver validacao.md); a parte fica pronta e vale 0.
    g["periodo_preferido"] = None
    g["na_janela"] = False
    g["bonus_janela"] = 0
    g["bonus"] = g["bonus_historico"] + g["bonus_janela"]
    g.attrs["cortes_receita"] = cortes
    return g


def explicacao_conta(p: pd.Series) -> str:
    terco = {2: "entre as que mais compram (terço de cima da receita ganha): +10",
             1: "no terço do meio da receita ganha: +5",
             0: "no terço de baixo da receita ganha: +0"}[int(p["terco"])]
    return (f"{int(p['compras_ganhas'])} compras ganhas, US$ {int(p['receita_ganha']):,} em receita; empresa {terco}. "
            "Sem época de compra própria: compra no mesmo calendário das outras empresas.").replace(",", ".")


def calcular(d: pd.DataFrame, referencia: pd.Timestamp) -> dict:
    """Nota de todos os deals abertos, com o dono atual."""
    cel = celulas(d, referencia)
    pad = padroes_conta(d, referencia)
    abertos = d[d["estagio"].isin(["Prospecting", "Engaging"])].copy()
    linhas = []
    for _, r in abertos.iterrows():
        dono = r["vendedor_nome"]
        f = fit_do_lead(cel, dono, r)
        dias = (referencia - r["data_abertura"]).days if pd.notna(r["data_abertura"]) else None
        pts, rot = faixa_heat(dias)
        dias_contato = (referencia - r["ultimo_contato_em"]).days if pd.notna(r.get("ultimo_contato_em")) else None
        fator = fator_contato(dias_contato)
        heat = pts * fator
        if pd.notna(r["conta_nome"]) and r["conta_nome"] in pad.index:
            p = pad.loc[r["conta_nome"]]
            b_hist, b_jan = int(p["bonus_historico"]), int(p["bonus_janela"])
        else:
            p, b_hist, b_jan = None, 0, 0
        bonus = b_hist + b_jan
        nota = PESOS["fit"] * f["fit"] + PESOS["heat"] * heat + bonus
        marcadores = []
        if dias is not None and RISCO_ESFRIAR[0] <= dias <= RISCO_ESFRIAR[1]:
            marcadores.append("risco_esfriar")
        if dias is not None and dias > RISCO_ESFRIAR[1]:
            marcadores.append("esfriou")
        criado = r.get("criado_em")
        if pd.notna(criado) and dias_contato is None and f["fit"] >= FIT_FURAR_FILA:
            dias_criado = (referencia - pd.Timestamp(criado).tz_localize(None).normalize()).days
            if dias_criado > 1:
                marcadores.append("atendimento_atrasado")
        acao = "desistir" if dias is not None and dias > DESISTIR_ACIMA else (
            "requalificar" if dias is not None and dias > RISCO_ESFRIAR[1] else "focar")
        linhas.append({
            "opportunity_id": r["opportunity_id"], "vendedor_nome": dono, "produto_nome": r["produto_nome"],
            "conta_nome": None if pd.isna(r["conta_nome"]) else r["conta_nome"], "estagio": r["estagio"],
            "cohort": f"produto={r['produto_nome']}", "fit": f["fit"], "heat": heat, "heat_faixa": rot, "heat_pontos": pts,
            "fator_contato": fator, "bonus": bonus, "bonus_historico": b_hist, "bonus_janela": b_jan,
            "terco": None if p is None else int(p["terco"]), "nota": nota, "acao_sugerida": acao, "dias": dias,
            "valor_esperado": int(r["preco"]), "marcadores": marcadores, "detalhe_fit": f,
            "ativo": r["estagio"] == "Prospecting" or (dias is not None and dias <= RISCO_ESFRIAR[1]),
        })
    deals = pd.DataFrame(linhas)
    for l in linhas:
        l["motivos"] = motivos(l)
    deals["motivos"] = [l["motivos"] for l in linhas]
    return {"deals": deals, "celulas": cel, "padroes": pad}


SETORES = {  # igual à tabela SETORES do app (src/lib/calculos.ts)
    "employment": "recrutamento", "entertainment": "entretenimento", "finance": "finanças", "marketing": "marketing",
    "medical": "saúde", "retail": "varejo", "services": "serviços", "software": "software",
    "technology": "tecnologia", "telecommunications": "telecomunicações",
}
PORTE = {"pequena": "pequena", "media": "média", "grande": "grande"}


def _rot(item) -> str:
    """Característica em português, como a tela mostra."""
    dim, v = item["dim"], item["valor"]
    if dim == "produto":
        return f"produto {v}"
    if dim == "serie":
        return f"série {v}"
    if dim == "setor":
        return f"setor {SETORES.get(v, v)}"
    if dim == "receita":
        return f"empresa de receita {PORTE.get(v, v)}"
    if dim == "funcionarios":
        return f"empresa {PORTE.get(v, v)} em funcionários"
    if dim == "empresa":
        return f"empresa {v}"
    if dim == "sede":
        return "sede nos EUA" if v == "EUA" else "sede fora dos EUA"
    return f"{ROTULO_DIM.get(dim, dim)} {v}"


def motivos(l: dict) -> list[tuple[str, str]]:
    """2 ou 3 frases simples: encaixe, tempo e bônus (ou falta de empresa).

    Em terceira pessoa ("o vendedor"), porque a mesma frase aparece para o vendedor e para o manager.
    """
    f = l["detalhe_fit"]
    saida = []
    if f.get("sem_historico"):
        saida.append(("fit", "Vendedor sem histórico: encaixe neutro (50)."))
    elif f["sem_destaque"]:
        saida.append(("fit", "O vendedor não tem um destaque com casos suficientes nos últimos 3 meses: o encaixe fica neutro (50)."))
    elif not f["usadas"]:
        saida.append(("fit", "Ainda não há casos suficientes para medir o encaixe deste lead com o vendedor: nota neutra (50)."))
    else:
        dest = f["destaque"]
        bate = [u for u in f["usadas"] if u["dim"] == dest["dim"] and u["valor"] == dest["valor"]]
        if bate:
            u = bate[0]
            saida.append(("fit", f"Encaixa no destaque do vendedor: {_rot(u)} ({u['ganhos']} de {u['n']} ganhos nos últimos 3 meses)."))
        elif f["media"] >= 0:
            u = max(f["usadas"], key=lambda x: x["desvio"])
            saida.append(("fit", f"Encaixe acima da média do vendedor: {_rot(u)} ({u['ganhos']} de {u['n']} ganhos nos últimos 3 meses)."))
        else:
            u = min(f["usadas"], key=lambda x: x["desvio"])
            saida.append(("fit", f"Fora do forte do vendedor: {_rot(u)} ({u['ganhos']} de {u['n']} ganhos nos últimos 3 meses, abaixo da média dele)."))
    if l["conta_nome"] is None:
        saida.append(("fit", "Sem empresa cadastrada: o encaixe usa só o produto. Identifique a empresa."))
    dias = l["dias"]
    if dias is None:
        saida.append(("heat", "Ainda não começou: sem data de início. O relógio começa no primeiro contato."))
    elif dias > RISCO_ESFRIAR[1]:
        saida.append(("heat", f"Parado há {dias} dias: nenhum deal fechou depois de 138 dias. Requalifique ou encerre."))
    elif dias >= RISCO_ESFRIAR[0]:
        saida.append(("heat", f"Aberto há {dias} dias: em risco de esfriar."))
    elif dias <= 15:
        saida.append(("heat", f"Aberto há {dias} dias: atenda agora, a nota de tempo cai a cada faixa."))
    else:
        saida.append(("heat", f"Aberto há {dias} dias: a nota de tempo já caiu para {l['heat_pontos']}."))
    if l["conta_nome"] is not None and len(saida) < 3:
        if l["bonus_historico"] == 10:
            saida.append(("bonus", "Empresa entre as que mais compram: +10."))
        elif l["bonus_historico"] == 5:
            saida.append(("bonus", "Empresa no terço do meio em compras: +5."))
    return saida[:3]


def componentes(l: dict) -> list[dict]:
    f = l["detalhe_fit"]
    dest = f["destaque"]
    out = [{"grupo": "fit", "componente": "Encaixe com o vendedor (70%)", "pontos": round(PESOS["fit"] * l["fit"], 2), "maximo": 70},
           {"grupo": "heat", "componente": "Tempo de atendimento (30%)", "pontos": round(PESOS["heat"] * l["heat"], 2), "maximo": 30},
           {"grupo": "heat", "componente": f"Faixa: {l['heat_faixa']}", "pontos": l["heat_pontos"], "maximo": 100},
           {"grupo": "heat", "componente": "Fator de contato", "pontos": l["fator_contato"], "maximo": 1},
           {"grupo": "bonus", "componente": "Histórico da empresa", "pontos": l["bonus_historico"], "maximo": 10},
           {"grupo": "bonus", "componente": "Janela de compra", "pontos": l["bonus_janela"], "maximo": 10}]
    for u in f["usadas"]:
        out.append({"grupo": "fit", "componente": f"Desvio: {_rot(u)}"[:60], "pontos": round(u["desvio"] * 100, 2),
                    "maximo": round(dest["desvio"] * 100, 2) if dest else None})
    return out


def fit_vendedores(cel: Celulas, produtos: pd.DataFrame) -> pd.DataFrame:
    """FIT de cada vendedor para um lead novo de cada produto (sem empresa: produto e série), base do roteamento."""
    linhas = []
    for v in sorted(cel.taxa_vendedor):
        for _, p in produtos.iterrows():
            lead = pd.Series({"produto_nome": p["nome"], "serie": p["serie"]})
            f = fit_do_lead(cel, v, lead)
            cp = cel.celula(v, "produto", p["nome"])
            cs = cel.celula(v, "serie", p["serie"])
            casos = max(int(cp.n) if cp else 0, int(cs.n) if cs else 0)
            taxa = float(cp.taxa_encolhida) if (cp is not None and cp.ok) else cel.taxa_vendedor[v]
            linhas.append({"vendedor_nome": v, "cohort": f"produto={p['nome']}", "produto_nome": p["nome"],
                           "taxa_media_movel": round(taxa, 4), "casos": casos, "fit": int(round(f["fit"]))})
    return pd.DataFrame(linhas)


def top5(deals: pd.DataFrame) -> pd.DataFrame:
    return deals.sort_values(["nota", "heat"], ascending=False).groupby("vendedor_nome").head(5)
