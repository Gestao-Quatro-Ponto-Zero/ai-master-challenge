"""Gera console/data.js (window.DADOS) a partir dos arquivos já existentes. Nenhum número novo é inventado aqui:
tudo vem do modelo atual (triagem.py), dos CSV/JSON de solution/outputs e dos ataques versionados."""
import json
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from comum import OUT_DIR, SEED, SUBMISSAO, ler_ds2, wilson
from f4_politica import ORDEM, faixa_efetiva, politica_categoria
from f5_injecao import carregar_ataques, montar_pares
import triagem

CONSOLE = SUBMISSAO / "console"
N_FILA, N_DIAS = 300, 20
TEXTO_MAX = 400


def politicas():
    f8 = pd.read_csv(OUT_DIR / "f8_politica_por_categoria.csv")
    f4 = pd.read_csv(OUT_DIR / "f4_politica_por_categoria.csv")
    fx8 = json.loads((OUT_DIR / "f8_faixas.json").read_text(encoding="utf-8"))
    fx3 = json.loads((OUT_DIR / "f3_faixas.json").read_text(encoding="utf-8"))
    t8 = (fx8["limiares"]["t_decide"], fx8["limiares"]["t_sugere"])
    t3 = (fx3["faixas"]["ia_decide"]["limiar"], fx3["faixas"]["ia_sugere_humano_confirma"]["limiar"])
    return {
        "F9": {"nome": "F9 implantada", "t_decide": t8[0], "t_sugere": t8[1],
               "por_categoria": dict(zip(f8["categoria_prevista"], f8["politica_implantada"])),
               "origem": "f8_politica_por_categoria.csv (politica_implantada); f8_faixas.json (limiares)"},
        "F8": {"nome": "F8 seleção OOF", "t_decide": t8[0], "t_sugere": t8[1],
               "por_categoria": dict(zip(f8["categoria_prevista"], f8["politica"])),
               "origem": "f8_politica_por_categoria.csv (politica); f8_faixas.json (limiares)"},
        "F4": {"nome": "F4 (escolhida no holdout)", "t_decide": t3[0], "t_sugere": t3[1],
               "por_categoria": dict(zip(f4["categoria_prevista"], f4["politica"])),
               "origem": "f4_politica_por_categoria.csv; f3_faixas.json (limiares)"},
    }


def faixa_e_porque(cat, p, pol):
    """Mesma lógica de triagem.faixa_para: faixa global pelo p_max e teto da política da categoria."""
    td, ts = pol["t_decide"], pol["t_sugere"]
    g = "IA decide" if p >= td else ("IA sugere" if p >= ts else "humano decide")
    teto = pol["por_categoria"].get(cat, "humano decide")
    faixa = ORDEM[min(ORDEM.index(g), ORDEM.index(teto))]
    passos = [{"passo": "confiança × limiar", "p_max": p, "t_decide": td, "t_sugere": ts, "faixa_global": g},
              {"passo": "teto da política da categoria", "categoria": cat, "teto": teto, "rebaixou": faixa != g}]
    return faixa, passos


def main():
    pols = politicas()
    df = ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")
    ho = df[df["split_grupo"] == "holdout"]
    modelo = triagem.carregar_modelo()
    m = modelo["pipeline"]
    categorias = sorted(m.classes_)
    fx8 = json.loads((OUT_DIR / "f8_faixas.json").read_text(encoding="utf-8"))
    fx3 = json.loads((OUT_DIR / "f3_faixas.json").read_text(encoding="utf-8"))
    tab8 = pd.read_csv(OUT_DIR / "f8_politica_por_categoria.csv")
    e = fx3["e_q2"]

    # ---- fila: 300 tickets do holdout (seed 42), em 20 dias de 15
    fila_df = ho.sample(N_FILA, random_state=SEED).reset_index(drop=True)
    fila = []
    for i, t in enumerate(fila_df.itertuples()):
        c = triagem.classificar(t.Document)
        texto = str(t.Document)
        item = {"id": int(t.id), "dia": i // (N_FILA // N_DIAS) + 1,
                "texto": texto[:TEXTO_MAX], "truncado": len(texto) > TEXTO_MAX,
                "rotulo_original": t.Topic_group, "pred": c["categoria"], "p_max": c["p_max"], "top2": c["top2"],
                "termos": c["motivo"].replace("termos: ", ""), "faixas": {}}
        for k, pol in pols.items():
            f, passos = faixa_e_porque(c["categoria"], c["p_max"], pol)
            item["faixas"][k] = {"faixa": f, "passos": passos}
        fila.append(item)

    # ---- ataques: 300 × 5, com o clássico (dados reais)
    limpa = {it["id"]: it["pred"] for it in fila}
    pares = montar_pares(fila_df, limpa, categorias)
    pa = m.predict_proba([p["texto"] for p in pares])
    ataques = {}
    for p, pr in zip(pares, pa):
        j = int(pr.argmax())
        cat, pm = str(m.classes_[j]), round(float(pr[j]), 4)
        ataques.setdefault(str(p["id"]), {})[p["ataque"]] = {
            "alvo": p["alvo"], "pred": cat, "p_max": pm,
            "faixas": {k: faixa_e_porque(cat, pm, pol)[0] for k, pol in pols.items()}}

    # ---- governança: holdout inteiro, ordem aleatória (seed 42), 20 dias, acumulado
    gov_df = ho.sample(frac=1, random_state=SEED).reset_index(drop=True)
    proba = m.predict_proba(gov_df["Document"])
    pred = m.classes_[proba.argmax(1)]
    pmax = proba.max(1)
    acerto = pred == gov_df["Topic_group"].values
    dias = np.array_split(np.arange(len(gov_df)), N_DIAS)
    t_dec = pols["F9"]["t_decide"]
    faixas_pol = {k: np.array([faixa_e_porque(c, float(p), pol)[0] for c, p in zip(pred, pmax)]) for k, pol in pols.items()}
    gov = []
    for d in range(N_DIAS):
        ate = np.concatenate(dias[: d + 1])
        dia = {"dia": d + 1, "n_total": int(len(ate)), "categorias": {}, "faixas": {}}
        for c in categorias:
            msk = ate[(pred[ate] == c) & (pmax[ate] >= t_dec)]
            n, k = int(len(msk)), int(acerto[msk].sum())
            li, ls = wilson(k, n) if n else (None, None)
            dia["categorias"][c] = {"n_sombra": n, "acertos": k,
                                    "precisao": round(k / n, 4) if n else None,
                                    "li": round(li, 4) if n else None, "ls": round(ls, 4) if n else None,
                                    "decisao_regra": politica_categoria(li, e["e_inferior"], e["e_superior"]) if n else None}
        for kpol, fx in faixas_pol.items():
            sub = fx[ate]
            dia["faixas"][kpol] = {f: {"n": int((sub == f).sum()), "acertos": int(acerto[ate][sub == f].sum())} for f in ORDEM}
        gov.append(dia)

    # checagem obrigatória (spec F10, passo 1.5)
    ult = gov[-1]
    for r in tab8.itertuples():
        if r.politica_implantada == "IA decide":
            li20 = ult["categorias"][r.categoria_prevista]["li"]
            if abs(li20 - r.li_ia_decide) > 1e-4:
                sys.exit(f"PARAR: LI dia 20 {r.categoria_prevista} = {li20} ≠ li_ia_decide {r.li_ia_decide}")
    cob = round(100 * ult["faixas"]["F9"]["IA decide"]["n"] / ult["n_total"], 2)
    if abs(cob - fx8["implantada"]["faixas"]["IA decide"]["cobertura_pct"]) > 1e-6:
        sys.exit(f"PARAR: cobertura IA decide dia 20 = {cob} ≠ {fx8['implantada']['faixas']['IA decide']['cobertura_pct']}")

    inj = json.loads((OUT_DIR / "f5_injecao.json").read_text(encoding="utf-8"))
    dano = lambda d: {"n_pares": d["n_pares"], "silenciosos": d["dano_silencioso"]["n"],
                      "limite_superior": d["dano_silencioso"]["limite_superior"], "saem_de_ia_decide": d["pares_que_saem_de_ia_decide"]}
    dados = {
        "meta": {"e_q2": e["valor"], "meta_ia_decide": round(1 - e["e_inferior"], 4), "meta_ia_sugere": round(1 - e["e_superior"], 4),
                 "t_decide": t_dec, "t_sugere": pols["F9"]["t_sugere"],
                 "modelo_versao": modelo["versao"], "politica_versao": triagem.carregar_politica()["versao"],
                 "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "categorias": categorias,
                 "origem": {"politicas": {k: v["origem"] for k, v in pols.items()},
                            "fila": "300 tickets do holdout por grupo (f1_splits.csv), seed 42; classificados por triagem.classificar",
                            "ataques": "solution/tests/golden/ataques_v1.json aplicados aos 300 tickets (clássico)",
                            "governanca": "holdout por grupo inteiro (9.567), ordem aleatória seed 42, 20 dias; acumulado",
                            "kpis": "f8_faixas.json (implantada); f5_injecao.json; premissas F0"}},
        "politicas": pols,
        "fila": fila,
        "ataques_modelos": [{"id": a["id"], "texto": a["texto"]} for a in carregar_ataques()],
        "ataques": ataques,
        "governanca": gov,
        "kpis": {"faixas_implantada": fx8["implantada"]["faixas"],
                 "dano_injecao": {"F9": dano(inj["dano_ampliado_f8"]), "F8": dano(inj["dano_ampliado_f8_oof"]),
                                  "F4": dano(inj["dano_ampliado"])},
                 "premissas": {"reais_por_hora": 35, "minutos_triagem": 3, "volume_ano": 30000,
                               "rotulo": "premissas editáveis (F0); cenário B: economia de triagem zero"}},
    }
    CONSOLE.mkdir(parents=True, exist_ok=True)
    (CONSOLE / "data.js").write_text("window.DADOS = " + json.dumps(dados, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"data.js: {len(fila)} tickets na fila, {len(ataques)} × 5 ataques, {len(gov)} dias; cobertura F9 dia 20 = {cob}%")
    print("LI dia 20:", {c: v["li"] for c, v in ult["categorias"].items()})


if __name__ == "__main__":
    main()
