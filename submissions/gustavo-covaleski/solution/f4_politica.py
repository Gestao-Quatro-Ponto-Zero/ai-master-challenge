import json

import numpy as np
import pandas as pd

from comum import (OUT_DIR, PLANNING_DIR, PROCESS_LOG_DIR, SEED, ler_csv_excel, ler_ds1, ler_ds2,
                   salvar_csv_excel, salvar_json, wilson)

F4_DIR = PLANNING_DIR / "F4"
ORDEM = ["humano decide", "IA sugere", "IA decide"]
TRECHO = 120


def politica_categoria(li, e_inf, e_sup):
    if li is not None and li >= 1 - e_inf:
        return "IA decide"
    if li is not None and li >= 1 - e_sup:
        return "IA sugere"
    return "humano decide"


def faixa_efetiva(p_max, politica, t_dec, t_sug):
    # a política da categoria é um teto: rebaixa a faixa global, nunca promove
    global_ = "IA decide" if p_max >= t_dec else ("IA sugere" if p_max >= t_sug else "humano decide")
    return ORDEM[min(ORDEM.index(global_), ORDEM.index(politica))]


def main():
    pr = pd.read_csv(OUT_DIR / "f3_probs_holdout_grupo.csv")
    fx = json.loads((OUT_DIR / "f3_faixas.json").read_text(encoding="utf-8"))
    cl = json.loads((OUT_DIR / "f3_classico.json").read_text(encoding="utf-8"))
    t_dec, t_sug = fx["faixas"]["ia_decide"]["limiar"], fx["faixas"]["ia_sugere_humano_confirma"]["limiar"]
    e_inf, e_sup = fx["e_q2"]["e_inferior"], fx["e_q2"]["e_superior"]
    classes = cl["split_grupo"]["matriz_confusao"]["classes"]
    cm = np.array(cl["split_grupo"]["matriz_confusao"]["linhas_verdadeiro"])

    pr["acerto"] = pr["pred"] == pr["rotulo"]
    pr["faixa_global"] = np.where(pr["p_max"] >= t_dec, "IA decide", np.where(pr["p_max"] >= t_sug, "IA sugere", "humano decide"))
    linhas = []
    for c in classes:
        s = pr[pr["pred"] == c]
        d = s[s["faixa_global"] == "IA decide"]
        k, n = int(d["acerto"].sum()), int(len(d))
        li, ls = wilson(k, n) if n else (None, None)
        pol = politica_categoria(li, e_inf, e_sup)
        j = classes.index(c)
        col = [(classes[i], int(cm[i, j])) for i in np.argsort(-cm[:, j]) if i != j][:2]
        motivo = (f"LI {li:.4f} {'≥' if li >= 1 - e_inf else '<'} 1−e_inf {1 - e_inf:.4f}; "
                  f"{'≥' if li >= 1 - e_sup else '<'} 1−e_sup {1 - e_sup:.4f}") if n else "sem tickets na faixa IA decide"
        linhas.append({
            "categoria_prevista": c, "n": int(len(s)),
            "pct_faixa_ia_decide": round(100 * n / len(s), 2),
            "pct_faixa_ia_sugere": round(100 * (s["faixa_global"] == "IA sugere").mean(), 2),
            "pct_faixa_humano": round(100 * (s["faixa_global"] == "humano decide").mean(), 2),
            "n_ia_decide": n, "precisao_ia_decide": round(k / n, 4) if n else None,
            "li_wilson": round(li, 4) if n else None, "ls_wilson": round(ls, 4) if n else None,
            "f1_classe": cl["split_grupo"]["f1_por_classe"][c],
            "confusao_1": f"{col[0][0]} ({col[0][1]})", "confusao_2": f"{col[1][0]} ({col[1][1]})",
            "politica": pol, "motivo": motivo,
        })
    tab = pd.DataFrame(linhas)
    tab.to_csv(OUT_DIR / "f4_politica_por_categoria.csv", index=False)

    pol_map = dict(zip(tab["categoria_prevista"], tab["politica"]))
    pr["faixa_efetiva"] = [faixa_efetiva(p, pol_map[c], t_dec, t_sug) for p, c in zip(pr["p_max"], pr["pred"])]
    cob = {}
    for f in ORDEM[::-1]:
        m = pr["faixa_efetiva"] == f
        k, n = int(pr.loc[m, "acerto"].sum()), int(m.sum())
        li, ls = wilson(k, n)
        cob[f] = {"n": n, "cobertura_pct": round(100 * n / len(pr), 2), "precisao": round(k / n, 4) if n else None,
                  "ic95": [round(li, 4), round(ls, 4)] if n else None}

    # exemplos sorteados (seed 42): ids no repo, texto só fora dele
    textos = ler_ds2().set_index("id")["Document"]
    ex = []
    for c in classes:
        pol = pol_map[c]
        s = pr[(pr["pred"] == c) & (pr["faixa_efetiva"] == pol)]
        if len(s):
            r = s.sample(1, random_state=SEED).iloc[0]
            ex.append({"grupo": f"roteamento {c} → {pol}", "id": int(r["id"]), "rotulo": r["rotulo"], "pred": r["pred"],
                       "p_max": round(float(r["p_max"]), 4)})
    for _, r in pr[pr["faixa_global"] == "humano decide"].sample(3, random_state=SEED).iterrows():
        ex.append({"grupo": "faixa humana", "id": int(r["id"]), "rotulo": r["rotulo"], "pred": r["pred"], "p_max": round(float(r["p_max"]), 4)})
    adj = ler_csv_excel(PROCESS_LOG_DIR / "revisao_rotulos_adjudicada.csv")
    amb = adj[adj["adjudicacao"].str.strip() == "ambíguo"].sample(3, random_state=SEED)
    for _, a in amb.iterrows():
        r = pr[pr["id"] == int(a["id"])].iloc[0]
        ex.append({"grupo": "ambíguo (revisão adjudicada)", "id": int(a["id"]), "rotulo": a["rotulo_original"],
                   "pred": r["pred"], "p_max": round(float(r["p_max"]), 4), "meu_rotulo": a["meu_rotulo"]})
    exdf = pd.DataFrame(ex)
    exdf.to_csv(OUT_DIR / "f4_exemplos_ids.csv", index=False)
    F4_DIR.mkdir(parents=True, exist_ok=True)
    salvar_csv_excel(exdf.assign(trecho=exdf["id"].map(lambda i: str(textos[i])[:TRECHO])), F4_DIR / "f4_exemplos.csv")

    ds1 = ler_ds1()
    ds1_ex = pd.concat([g.sample(1, random_state=SEED) for _, g in ds1.groupby("Ticket Type")])
    ds1_ex = ds1_ex[["Ticket ID", "Ticket Type", "Ticket Subject", "Ticket Channel", "Ticket Priority"]]
    ds1_ex.to_csv(OUT_DIR / "f4_exemplos_ds1.csv", index=False)

    # sensibilidade pós-hoc (portão F4): categorias humanas viram teto "IA sugere"; NÃO usada na decisão
    pol_sens = {c: ("IA sugere" if p == "humano decide" else p) for c, p in pol_map.items()}
    faixa_sens = pd.Series([faixa_efetiva(p, pol_sens[c], t_dec, t_sug) for p, c in zip(pr["p_max"], pr["pred"])])
    sens = []
    for cenario, faixa in [("regra registrada (usada na decisão)", pr["faixa_efetiva"]),
                           ("pós-hoc: abaixo de 1−e_sup vira IA sugere (NÃO usada na decisão)", faixa_sens)]:
        for f in ORDEM[::-1]:
            m = (faixa == f).values
            k, n = int(pr.loc[m, "acerto"].sum()), int(m.sum())
            li, ls = wilson(k, n)
            sens.append({"cenario": cenario, "faixa": f, "n": n, "cobertura_pct": round(100 * n / len(pr), 2),
                         "precisao": round(k / n, 4) if n else None, "li": round(li, 4) if n else None,
                         "ls": round(ls, 4) if n else None})
    pd.DataFrame(sens).to_csv(OUT_DIR / "f4_sensibilidade.csv", index=False)

    custo = pd.read_csv(OUT_DIR / "f2_custo_triagem.csv")
    frac = cob["IA decide"]["n"] / len(pr)
    pd.DataFrame({
        "min_por_ticket": custo["min_por_ticket"], "reais_por_hora": custo["reais_por_hora"],
        "custo_anual_triagem_reais": custo["custo_anual_triagem_reais"],
        "cobertura_ia_decide": round(frac, 4),
        "economia_anual_ia_decide_reais": (frac * custo["custo_anual_triagem_reais"]).round(2),
        "faixa_ia_sugere": "não quantificada; tempo de confirmação a medir no piloto",
        "rotulo": "premissas (volume, minutos, R$/h) editáveis; cenário A; substitui a economia de f3_faixas.json",
    }).to_csv(OUT_DIR / "f4_economia.csv", index=False)

    salvar_json({"limiares": {"ia_decide": t_dec, "ia_sugere": t_sug}, "e_q2": fx["e_q2"],
                 "regra": "política da categoria (LI de Wilson da precisão na faixa IA decide) é teto da faixa global",
                 "cobertura_apos_politica": cob}, "f4_politica.json")
    print(tab[["categoria_prevista", "n", "n_ia_decide", "precisao_ia_decide", "li_wilson", "politica"]].to_string(index=False))
    print("cobertura após política:", {k: v["cobertura_pct"] for k, v in cob.items()})


if __name__ == "__main__":
    main()
