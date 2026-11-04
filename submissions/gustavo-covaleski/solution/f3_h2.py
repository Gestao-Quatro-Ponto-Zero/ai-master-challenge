import json

import numpy as np
import pandas as pd

from comum import F3_DIR, OUT_DIR, PROCESS_LOG_DIR, SEED, ler_csv_excel, ler_ds2, salvar_csv_excel, salvar_json

DESTAQUES = ["Administrative rights", "Hardware", "Storage"]


def main():
    pr = pd.read_csv(OUT_DIR / "f3_probs_holdout_grupo.csv")
    cl = json.loads((OUT_DIR / "f3_classico.json").read_text(encoding="utf-8"))
    fx = json.loads((OUT_DIR / "f3_faixas.json").read_text(encoding="utf-8"))
    adj = ler_csv_excel(PROCESS_LOG_DIR / "revisao_rotulos_adjudicada.csv")
    adj["id"] = adj["id"].astype(int)
    adj["adjudicacao"] = adj["adjudicacao"].str.strip()
    adj["meu_rotulo"] = adj["meu_rotulo"].str.strip()
    r = adj.merge(pr[["id", "pred", "p_max"]], on="id", how="left")
    assert r["pred"].notna().all(), "ticket revisado fora do holdout por grupo"

    def conc(a, b):
        return {"n_concorda": int((r[a] == r[b]).sum()), "n": int(len(r)), "taxa": round(float((r[a] == r[b]).mean()), 4)}

    concord = {"modelo_x_original": conc("pred", "rotulo_original"),
               "modelo_x_gustavo": conc("pred", "meu_rotulo"),
               "gustavo_x_original": conc("meu_rotulo", "rotulo_original")}

    def desfecho(nome):
        s = r[r["adjudicacao"] == nome]
        return {"n": int(len(s)),
                "modelo_preve_original": int((s["pred"] == s["rotulo_original"]).sum()),
                "modelo_preve_gustavo": int((s["pred"] == s["meu_rotulo"]).sum()),
                "modelo_preve_outro": int(((s["pred"] != s["rotulo_original"]) & (s["pred"] != s["meu_rotulo"])).sum())}

    oe, amb = desfecho("original errado"), desfecho("ambíguo")

    acc = cl["split_grupo"]["acuracia"]
    e = fx["e_adjudicado"]
    teto, teto_inf = 1 - e["ponderado"], 1 - e["ic95_bootstrap_estratificado"][1]
    frase = ("a discordância do revisor reflete uma convenção da taxonomia que o modelo aprende, "
             "não erro aleatório do rótulo")
    consist = {
        "e_adjudicado_ponderado": e["ponderado"], "e_superior": e["ic95_bootstrap_estratificado"][1],
        "teto_esperado_1_menos_e": round(teto, 4), "1_menos_e_superior": round(teto_inf, 4),
        "acuracia_medida_holdout_grupo": acc,
        "acuracia_acima_de_1_menos_e_superior": acc > teto_inf,
        "modelo_concorda_com_original_na_maioria_dos_original_errado": oe["modelo_preve_original"] > oe["n"] / 2,
    }
    consist["conclusao"] = frase if (consist["acuracia_acima_de_1_menos_e_superior"]
                                     or consist["modelo_concorda_com_original_na_maioria_dos_original_errado"]) else \
        "nenhuma das duas condições pré-registradas foi atendida"

    classes = cl["split_grupo"]["matriz_confusao"]["classes"]
    cm = np.array(cl["split_grupo"]["matriz_confusao"]["linhas_verdadeiro"])
    tab = {}
    for i, c in enumerate(classes):
        s = adj[adj["rotulo_original"] == c]
        fora = [(classes[j], int(cm[i, j])) for j in np.argsort(-cm[i]) if j != i][:3]
        tab[c] = {"n_revisado": int(len(s)),
                  "taxa_original_errado": round(float((s["adjudicacao"] == "original errado").mean()), 4) if len(s) else None,
                  "taxa_ambiguo": round(float((s["adjudicacao"] == "ambíguo").mean()), 4) if len(s) else None,
                  "f1_modelo": cl["split_grupo"]["f1_por_classe"][c],
                  "top3_confusoes_holdout": [{"previsto": p, "n": n} for p, n in fora],
                  "destaque": c in DESTAQUES}
    ih, ist = classes.index("Hardware"), classes.index("Storage")
    par_hs = {"hardware_previsto_storage": int(cm[ih, ist]), "storage_previsto_hardware": int(cm[ist, ih]),
              "suporte_hardware": int(cm[ih].sum()), "suporte_storage": int(cm[ist].sum())}

    errados_conf = pr[(pr["pred"] != pr["rotulo"]) & (pr["p_max"] >= 0.90)]
    ex = errados_conf.sample(min(20, len(errados_conf)), random_state=SEED)
    textos = ler_ds2().set_index("id")["Document"]
    F3_DIR.mkdir(parents=True, exist_ok=True)
    salvar_csv_excel(pd.DataFrame({"id": ex["id"], "texto": textos.loc[ex["id"]].values, "rotulo": ex["rotulo"],
                                   "pred": ex["pred"], "p_max": ex["p_max"]}), F3_DIR / "f3_suspeitos.csv")

    salvar_json({"concordancia_60": concord, "original_errado": oe, "ambiguo": amb,
                 "teste_consistencia": consist, "por_categoria": tab, "par_hardware_storage": par_hs,
                 "suspeitos": {"erros_com_p_max_ge_0_90": int(len(errados_conf)), "n_holdout": int(len(pr)),
                               "pct_holdout": round(100 * len(errados_conf) / len(pr), 2),
                               "exemplos": "planning/F3/f3_suspeitos.csv (fora do repo)"}}, "f3_h2.json")
    print("concordância:", {k: v["taxa"] for k, v in concord.items()})
    print("original errado:", oe, "| ambíguo:", amb)
    print("consistência:", consist)
    print("Admin rights:", tab["Administrative rights"], "| H×S:", par_hs, "| suspeitos:", len(errados_conf))


if __name__ == "__main__":
    main()
