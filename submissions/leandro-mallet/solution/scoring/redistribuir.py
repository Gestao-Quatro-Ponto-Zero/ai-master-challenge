"""Plano da redistribuição de domingo (cenário B): só leads abertos sem contato registrado, por equilíbrio e FIT.

Uso (a partir da pasta solution/):  python scoring/redistribuir.py      # só leitura: calcula e grava o plano

Método (desenho.md, "Recálculo de domingo"):
- elegíveis: vendedores com fechamentos na janela de 3 meses (os sem destaque entram com FIT 50);
- limite da semana = ativos ÷ elegíveis, arredondado para cima, contando os ativos que cada um já tem;
- pares lead × vendedor do maior FIT para o menor; cada lead vai ao primeiro vendedor abaixo do limite.
Saída: scoring/carga/redistribuicao_<data>.json. Gravar exige função de banco própria (ver validacao.md).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calcular_score as cs  # noqa: E402
import regra  # noqa: E402


def planejar(d: pd.DataFrame, referencia: pd.Timestamp) -> dict:
    res = regra.calcular(d, referencia)
    cel, deals = res["celulas"], res["deals"].set_index("opportunity_id")
    elegiveis = sorted(cel.taxa_vendedor)
    sem_contato = d[(d["estagio"] == "Prospecting") & d["ultimo_contato_em"].isna()]
    alvo = sem_contato["opportunity_id"].tolist()
    ativos = deals[deals["ativo"]]
    fica = ativos.drop(index=alvo, errors="ignore")
    carga = fica.groupby("vendedor_nome").size().reindex(elegiveis, fill_value=0)
    limite = math.ceil(len(ativos[ativos["vendedor_nome"].isin(elegiveis) | ativos.index.isin(alvo)]) / len(elegiveis))
    linhas = d.set_index("opportunity_id")
    fit = {(o, v): regra.fit_do_lead(cel, v, linhas.loc[o])["fit"] for o in alvo for v in elegiveis}
    pares = sorted(((f, o, v) for (o, v), f in fit.items()), key=lambda t: (-t[0], t[1], t[2]))
    vagas = {v: max(0, limite - int(carga[v])) for v in elegiveis}
    dono = {}
    for f, o, v in pares:
        if o in dono or vagas[v] <= 0:
            continue
        dono[o] = v
        vagas[v] -= 1
    trocas = []
    for o in alvo:
        de = linhas.loc[o, "vendedor_nome"]
        para = dono.get(o, de)
        fd = fit.get((o, de), deals.loc[o, "fit"])
        trocas.append({"opportunity_id": o, "de": de, "para": para, "fit_dono": round(float(fd), 2),
                       "fit_novo": round(float(fit[(o, para)]), 2), "muda": para != de})
    return {"limite": limite, "elegiveis": elegiveis, "trocas": trocas, "deals": deals, "carga_fica": carga}


def main():
    deals, contas, produtos = cs.ler_banco()
    d = regra.preparar(deals, contas, produtos)
    p = planejar(d, cs.REFERENCIA)
    t = pd.DataFrame(p["trocas"])
    antes = p["deals"][p["deals"]["ativo"]].groupby("vendedor_nome").size()
    depois_dono = {r.opportunity_id: r.para for r in t.itertuples()}
    dd = p["deals"][p["deals"]["ativo"]].copy()
    dd["dono"] = [depois_dono.get(o, v) for o, v in zip(dd.index, dd["vendedor_nome"])]
    depois = dd.groupby("dono").size()
    m = t[t["muda"]]
    travas = m[(m["fit_novo"] < 75) | (m["fit_novo"] < m["fit_dono"] - 3)]
    resumo = {
        "sem_contato": len(t), "mudam": int(t["muda"].sum()), "limite": p["limite"], "elegiveis": len(p["elegiveis"]),
        "ativos_por_vendedor_antes": [int(antes.min()), int(antes.max())],
        "ativos_por_vendedor_depois_elegiveis": [int(depois.reindex(p["elegiveis"], fill_value=0).min()), int(depois.max())],
        "fit_medio_antes": round(t["fit_dono"].mean(), 1), "fit_medio_depois": round(t["fit_novo"].mean(), 1),
        "fit_75_antes": int((t["fit_dono"] >= 75).sum()), "fit_75_depois": int((t["fit_novo"] >= 75).sum()),
        "trocas_que_as_travas_do_repasse_recusariam": len(travas),
    }
    saida = cs.AQUI / "carga" / f"redistribuicao_{cs.REFERENCIA.date()}.json"
    saida.write_text(json.dumps({"resumo": resumo, "trocas": p["trocas"]}, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8", newline="\n")
    print(json.dumps(resumo, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
