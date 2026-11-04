import json

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from comum import OUT_DIR, SEED, ler_ds2, salvar_json, wilson
from f3_classico import modelo
from f3_faixas import curva, faixas
from f4_politica import ORDEM, faixa_efetiva, politica_categoria

INF = 1.01  # limiar inatingível quando nenhuma faixa passa na meta


def faixa_global(p, t_dec, t_sug):
    return np.where(p >= t_dec, "IA decide", np.where(p >= t_sug, "IA sugere", "humano decide"))


def politica_por_categoria(df, t_dec, e_inf, e_sup, classes):
    linhas = []
    for c in classes:
        s = df[df["pred"] == c]
        d = s[s["p_max"] >= t_dec]
        k, n = int((d["pred"] == d["rotulo"]).sum()), int(len(d))
        li, ls = wilson(k, n) if n else (None, None)
        pol = politica_categoria(li, e_inf, e_sup)
        motivo = (f"OOF treino: LI {li:.4f} vs 1−e_inf {1 - e_inf:.4f} / 1−e_sup {1 - e_sup:.4f}" if n
                  else "OOF treino: sem tickets na faixa IA decide")
        linhas.append({"categoria_prevista": c, "n_oof": int(len(s)), "n_ia_decide_oof": n,
                       "precisao_ia_decide_oof": round(k / n, 4) if n else None,
                       "li_wilson_oof": round(li, 4) if n else None, "ls_wilson_oof": round(ls, 4) if n else None,
                       "politica": pol, "motivo": motivo})
    return pd.DataFrame(linhas)


def stats(acerto, m, total):
    k, n = int(acerto[m].sum()), int(m.sum())
    li, ls = wilson(k, n)
    return {"n": n, "cobertura_pct": round(100 * n / total, 2), "precisao": round(k / n, 4) if n else None,
            "ic95": [round(li, 4), round(ls, 4)] if n else None}


def main():
    df = ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")
    tr = df[df["split_grupo"] == "treino"].reset_index(drop=True)
    ho = df[df["split_grupo"] == "holdout"].reset_index(drop=True)
    classes = sorted(df["Topic_group"].unique())

    # 1. predições fora da dobra no treino
    oof = np.zeros((len(tr), len(classes)))
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    for k, (a, b) in enumerate(sgkf.split(tr, tr["Topic_group"], groups=tr["group_id"])):
        m = modelo().fit(tr.loc[a, "Document"], tr.loc[a, "Topic_group"])
        assert list(m.classes_) == classes
        oof[b] = m.predict_proba(tr.loc[b, "Document"])
        print(f"dobra {k} ok")
    po = pd.DataFrame(oof, columns=[f"p_{c}" for c in classes]).round(6)
    po.insert(0, "p_max", oof.max(1).round(6))
    po.insert(0, "pred", np.array(classes)[oof.argmax(1)])
    po.insert(0, "rotulo", tr["Topic_group"].values)
    po.insert(0, "id", tr["id"].values)
    po.to_csv(OUT_DIR / "f8_probs_oof_treino.csv", index=False)

    # 2. mesmas regras registradas (F3: curva/faixas com e_Q2; F4: regra por categoria), só sobre o OOF
    fx3 = json.loads((OUT_DIR / "f3_faixas.json").read_text(encoding="utf-8"))
    e_inf, e_sup = fx3["e_q2"]["e_inferior"], fx3["e_q2"]["e_superior"]
    acerto_oof = (po["pred"] == po["rotulo"]).values
    cv = curva(po["p_max"], acerto_oof)
    cv.round(6).to_csv(OUT_DIR / "f8_curva_oof.csv", index=False)
    t_dec, t_sug = faixas(cv, e_inf, e_sup)
    t_dec_ef = t_dec if t_dec is not None else INF
    t_sug_ef = t_sug if t_sug is not None else INF
    pol = politica_por_categoria(po, t_dec_ef, e_inf, e_sup, classes)

    # 3. congelado; aplicado uma única vez no holdout por grupo
    pr = pd.read_csv(OUT_DIR / "f3_probs_holdout_grupo.csv")  # mesmo modelo da F3, treinado no treino inteiro
    acerto = (pr["pred"] == pr["rotulo"]).values
    pol_map = dict(zip(pol["categoria_prevista"], pol["politica"]))
    fe = np.array([faixa_efetiva(p, pol_map[c], t_dec_ef, t_sug_ef) for p, c in zip(pr["p_max"], pr["pred"])])
    geral = {f: stats(acerto, fe == f, len(pr)) for f in ORDEM[::-1]}
    por_cat = []
    for c in classes:
        mc = (pr["pred"] == c).values
        linha = {"categoria_prevista": c, "politica": pol_map[c], "n_holdout": int(mc.sum())}
        for f in ORDEM[::-1]:
            s = stats(acerto, mc & (fe == f), int(mc.sum()))
            chave = f.replace(" ", "_").lower()
            linha |= {f"n_{chave}": s["n"], f"cobertura_pct_{chave}": s["cobertura_pct"], f"precisao_{chave}": s["precisao"],
                      f"li_{chave}": s["ic95"][0] if s["ic95"] else None, f"ls_{chave}": s["ic95"][1] if s["ic95"] else None}
        por_cat.append(linha)
    tab = pol.merge(pd.DataFrame(por_cat).drop(columns="politica"), on="categoria_prevista")
    tab.to_csv(OUT_DIR / "f8_politica_por_categoria.csv", index=False)

    # 4. economia, cenário A
    custo = pd.read_csv(OUT_DIR / "f2_custo_triagem.csv")
    frac = geral["IA decide"]["n"] / len(pr)
    pd.DataFrame({"min_por_ticket": custo["min_por_ticket"], "reais_por_hora": custo["reais_por_hora"],
                  "custo_anual_triagem_reais": custo["custo_anual_triagem_reais"], "cobertura_ia_decide": round(frac, 4),
                  "economia_anual_ia_decide_reais": (frac * custo["custo_anual_triagem_reais"]).round(2),
                  "faixa_ia_sugere": "não quantificada; tempo de confirmação a medir no piloto",
                  "rotulo": "premissas editáveis; cenário A; limiar e política escolhidos fora do holdout (F8)"}
                 ).to_csv(OUT_DIR / "f8_economia.csv", index=False)

    salvar_json({
        "metodo": "StratifiedGroupKFold(5, shuffle, seed 42) no treino por grupo; curva/faixas de f3_faixas.py e regra por categoria "
                  "de f4_politica.py aplicadas às predições fora da dobra; limiares e política congelados e aplicados uma única vez no holdout",
        "e_q2": fx3["e_q2"],
        "limiares": {"t_decide": t_dec, "t_sugere": t_sug},
        "faixa_ia_decide_vazia_no_oof": t_dec is None,
        "oof_treino": {"n": int(len(po)), "acuracia": round(float(acerto_oof.mean()), 4),
                       "politica_por_categoria": pol_map},
        "holdout_grupo": {"n": int(len(pr)), "acuracia": round(float(acerto.mean()), 4), "faixas": geral},
        "comparacao_f3_f4": {"limiares_f3_holdout": {"t_decide": fx3["faixas"]["ia_decide"]["limiar"],
                                                     "t_sugere": fx3["faixas"]["ia_sugere_humano_confirma"]["limiar"]},
                             "politica_f4": dict(pd.read_csv(OUT_DIR / "f4_politica_por_categoria.csv")[["categoria_prevista", "politica"]].values)},
    }, "f8_faixas.json")
    # F9: o CSV de política nunca fica sem politica_implantada (confirmação por categoria no holdout; só rebaixa)
    from f9_confirmacao import aplicar_confirmacao
    aplicar_confirmacao()
    print("limiares OOF:", t_dec, t_sug)
    print("política OOF:", pol_map)
    print("holdout:", {f: (v["cobertura_pct"], v["precisao"], v["ic95"]) for f, v in geral.items()})


if __name__ == "__main__":
    main()
