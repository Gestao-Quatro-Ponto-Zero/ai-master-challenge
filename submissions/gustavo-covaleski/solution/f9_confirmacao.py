import json
from collections import Counter

import numpy as np
import pandas as pd

from comum import OUT_DIR, ler_ds2, salvar_json, wilson
from f4_politica import ORDEM, faixa_efetiva, politica_categoria

# F9 (decisão do Gustavo, conservadora e pós-hoc): a categoria precisa passar na seleção fora da dobra (F8)
# E na confirmação no holdout; a confirmação só rebaixa, nunca promove.


def mais_restritiva(a, b):
    return ORDEM[min(ORDEM.index(a), ORDEM.index(b))]


def confirmar(li_holdout, politica_oof, e_inf, e_sup):
    if li_holdout is None or pd.isna(li_holdout):
        return politica_oof  # sem tickets em IA decide no holdout: mantém a OOF
    return politica_categoria(float(li_holdout), e_inf, e_sup)


def stats(acerto, m, total):
    k, n = int(acerto[m].sum()), int(m.sum())
    li, ls = wilson(k, n)
    return {"n": n, "cobertura_pct": round(100 * n / total, 2), "precisao": round(k / n, 4) if n else None,
            "ic95": [round(li, 4), round(ls, 4)] if n else None}


def dano_por_alvo_oof(pol_oof, t_dec, t_sug):
    """Refaz os pares de ataque com a política OOF da F8 para localizar as trocas silenciosas por categoria-alvo."""
    from f5_injecao import montar_pares
    from triagem import carregar_modelo
    df = ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")
    ho = df[df["split_grupo"] == "holdout"]
    m = carregar_modelo()["pipeline"]
    pr = m.predict_proba(ho["Document"])
    pred = m.classes_[pr.argmax(1)]
    fx = [faixa_efetiva(float(p), pol_oof[c], t_dec, t_sug) for c, p in zip(pred, pr.max(1))]
    uni = ho[[f == "IA decide" for f in fx]]
    limpa = dict(zip(ho["id"], pred))
    pares = montar_pares(uni, limpa, sorted(m.classes_))
    pa = m.predict_proba([p["texto"] for p in pares])
    pa_pred = m.classes_[pa.argmax(1)]
    fa = [faixa_efetiva(float(p), pol_oof[c], t_dec, t_sug) for c, p in zip(pa_pred, pa.max(1))]
    silenciosos = [(p, c) for p, c, f in zip(pares, pa_pred, fa) if f == "IA decide" and c != limpa[p["id"]]]
    return {"n_pares": len(pares), "n_silenciosos": len(silenciosos),
            "por_categoria_alvo": dict(Counter(c for _, c in silenciosos).most_common()),
            "por_ataque": dict(Counter(p["ataque"] for p, _ in silenciosos).most_common())}


def aplicar_confirmacao():
    """Grava politica_confirmada_holdout/politica_implantada, a chave `implantada` e a economia. Chamada pelo f8_oof.py."""
    arq = OUT_DIR / "f8_politica_por_categoria.csv"
    tab = pd.read_csv(arq)
    fx3 = json.loads((OUT_DIR / "f3_faixas.json").read_text(encoding="utf-8"))
    e_inf, e_sup = fx3["e_q2"]["e_inferior"], fx3["e_q2"]["e_superior"]
    tab["politica_confirmada_holdout"] = [confirmar(li, p, e_inf, e_sup) for li, p in zip(tab["li_ia_decide"], tab["politica"])]
    tab["politica_implantada"] = [mais_restritiva(a, b) for a, b in zip(tab["politica"], tab["politica_confirmada_holdout"])]
    tab.to_csv(arq, index=False)

    f8 = json.loads((OUT_DIR / "f8_faixas.json").read_text(encoding="utf-8"))
    t_dec, t_sug = f8["limiares"]["t_decide"], f8["limiares"]["t_sugere"]
    pr = pd.read_csv(OUT_DIR / "f3_probs_holdout_grupo.csv")
    acerto = (pr["pred"] == pr["rotulo"]).values
    pol_imp = dict(zip(tab["categoria_prevista"], tab["politica_implantada"]))
    pol_oof = dict(zip(tab["categoria_prevista"], tab["politica"]))
    fe = np.array([faixa_efetiva(p, pol_imp[c], t_dec, t_sug) for p, c in zip(pr["p_max"], pr["pred"])])
    implantada = {f: stats(acerto, fe == f, len(pr)) for f in ORDEM[::-1]}

    if "holdout_grupo" in f8:
        f8["selecao_oof"] = f8.pop("holdout_grupo")
    f8["implantada"] = {
        "regra": "F9: política implantada = mais restritiva entre a seleção OOF (F8) e a confirmação por categoria no holdout "
                 "(mesma regra da F4 aplicada ao LI do holdout). Decisão conservadora pós-hoc do Gustavo: só rebaixa.",
        "politica_por_categoria": pol_imp, "n": int(len(pr)), "acuracia": round(float(acerto.mean()), 4), "faixas": implantada}
    salvar_json(f8, "f8_faixas.json")

    custo = pd.read_csv(OUT_DIR / "f2_custo_triagem.csv")
    frac = implantada["IA decide"]["n"] / len(pr)
    pd.DataFrame({"min_por_ticket": custo["min_por_ticket"], "reais_por_hora": custo["reais_por_hora"],
                  "custo_anual_triagem_reais": custo["custo_anual_triagem_reais"], "cobertura_ia_decide": round(frac, 4),
                  "economia_anual_ia_decide_reais": (frac * custo["custo_anual_triagem_reais"]).round(2),
                  "faixa_ia_sugere": "não quantificada; tempo de confirmação a medir no piloto",
                  "rotulo": "premissas editáveis; cenário A; política implantada (F9: seleção OOF + confirmação no holdout)"}
                 ).to_csv(OUT_DIR / "f8_economia.csv", index=False)
    return tab, implantada, pol_oof, t_dec, t_sug


def main():
    tab, implantada, pol_oof, t_dec, t_sug = aplicar_confirmacao()
    inj_arq = OUT_DIR / "f5_injecao.json"
    inj = json.loads(inj_arq.read_text(encoding="utf-8"))
    if "dano_ampliado_f8" in inj and "dano_ampliado_f8_oof" not in inj:
        inj["dano_ampliado_f8_oof"] = inj.pop("dano_ampliado_f8")
    inj["dano_ampliado_f8_oof"]["distribuicao_silenciosos"] = dano_por_alvo_oof(pol_oof, t_dec, t_sug)
    salvar_json(inj, "f5_injecao.json")

    print(tab[["categoria_prevista", "politica", "li_ia_decide", "politica_confirmada_holdout", "politica_implantada"]].to_string(index=False))
    print("implantada:", {f: (v["cobertura_pct"], v["precisao"], v["ic95"]) for f, v in implantada.items()})
    print("silenciosos OOF:", inj["dano_ampliado_f8_oof"]["distribuicao_silenciosos"])


if __name__ == "__main__":
    main()
