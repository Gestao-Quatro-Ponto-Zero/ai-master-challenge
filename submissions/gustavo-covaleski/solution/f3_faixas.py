import json

import numpy as np
import pandas as pd

from comum import OUT_DIR, PROCESS_LOG_DIR, REVISAO_DIR, SEED, ler_csv_excel, salvar_json, wilson

LIMIARES = np.round(np.arange(0.50, 0.995, 0.01), 2)


def curva(p_max, acerto, limiares=LIMIARES):
    p_max, acerto = np.asarray(p_max), np.asarray(acerto)
    linhas = []
    for t in limiares:
        m = p_max >= t
        k, n = int(acerto[m].sum()), int(m.sum())
        li, ls = wilson(k, n)
        linhas.append({"limiar": float(t), "n": n, "cobertura": n / len(p_max),
                       "precisao": k / n if n else float("nan"), "li": li, "ls": ls})
    return pd.DataFrame(linhas)


def faixas(cv: pd.DataFrame, e_inf: float, e_sup: float):
    """Devolve (limiar_decide, limiar_sugere); None quando a meta não é atingida em nenhum limiar."""
    def menor(meta):
        ok = cv[cv["li"] >= meta]
        return float(ok["limiar"].min()) if len(ok) else None
    t_decide, t_sugere = menor(1 - e_inf), menor(1 - e_sup)
    if t_decide is not None and t_sugere is not None and t_sugere > t_decide:
        t_sugere = t_decide
    return t_decide, t_sugere


def e_ponderado(adjud: pd.DataFrame, pesos: pd.Series):
    # taxa de "original errado" por categoria do rótulo original, ponderada pela prevalência no holdout
    taxa = adjud.groupby("rotulo_original")["errado"].mean().reindex(pesos.index).fillna(0.0)
    return float((taxa * pesos / pesos.sum()).sum())


def e_boot(adjud, pesos, n_boot=2000, seed=SEED):
    rng = np.random.default_rng(seed)
    grupos = {c: g["errado"].values for c, g in adjud.groupby("rotulo_original")}
    vals = []
    for _ in range(n_boot):
        amostra = pd.DataFrame([(c, v) for c, arr in grupos.items() for v in rng.choice(arr, len(arr))],
                               columns=["rotulo_original", "errado"])
        vals.append(e_ponderado(amostra, pesos))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def faixa_stats(m, acerto):
    k, n = int(acerto[m].sum()), int(m.sum())
    li, ls = wilson(k, n)
    return {"n": n, "cobertura": round(n / len(acerto), 4),
            "precisao": round(k / n, 4) if n else None, "precisao_ic95": [round(li, 4), round(ls, 4)] if n else None}


def main():
    pr = pd.read_csv(OUT_DIR / "f3_probs_holdout_grupo.csv")
    acerto = (pr["pred"] == pr["rotulo"]).values
    cv = curva(pr["p_max"], acerto)
    cv.round(6).to_csv(OUT_DIR / "f3_curva.csv", index=False)

    adj = ler_csv_excel(PROCESS_LOG_DIR / "revisao_rotulos_adjudicada.csv")
    adj["errado"] = (adj["adjudicacao"].str.strip() == "original errado").astype(float)
    pesos = ler_csv_excel(REVISAO_DIR / "revisao_pesos.csv").set_index("categoria")["prevalencia_holdout"].astype(float)
    e_adj = e_ponderado(adj, pesos)
    e_adj_ic = e_boot(adj, pesos)
    bruto = int(adj["errado"].sum())

    q = json.loads((OUT_DIR / "f1_ds2_auditoria.json").read_text(encoding="utf-8"))["3.5_quase_duplicados"]
    k_dup, n_dup = q["tickets_fora_da_maioria_do_grupo"], q["tickets_em_grupos_tam_2mais"]
    e_dup, e_dup_ic = k_dup / n_dup, wilson(k_dup, n_dup)

    fonte = "quase_duplicados" if e_dup <= e_adj else "adjudicacao"
    e_q2, (e_inf, e_sup) = (e_dup, e_dup_ic) if fonte == "quase_duplicados" else (e_adj, e_adj_ic)

    t_dec, t_sug = faixas(cv, e_inf, e_sup)
    p = pr["p_max"].values
    m_dec = p >= t_dec if t_dec is not None else np.zeros(len(p), bool)
    m_sug = (p >= t_sug) & ~m_dec if t_sug is not None else np.zeros(len(p), bool)
    m_hum = ~m_dec & ~m_sug
    bandas = {"ia_decide": {"limiar": t_dec, **faixa_stats(m_dec, acerto)},
              "ia_sugere_humano_confirma": {"limiar": t_sug, **faixa_stats(m_sug, acerto)},
              "humano_decide": faixa_stats(m_hum, acerto)}

    custo = pd.read_csv(OUT_DIR / "f2_custo_triagem.csv")
    cob = bandas["ia_decide"]["cobertura"]
    custo["economia_anual_reais"] = (cob * custo["custo_anual_triagem_reais"]).round(2)

    equilibrio = "pendente: depende do custo do LLM (f3_llm.json)"
    llm_path = OUT_DIR / "f3_llm.json"
    if llm_path.exists():
        llm = json.loads(llm_path.read_text(encoding="utf-8"))
        usd_por_ticket = llm.get("custo", {}).get("usd_por_1000") and llm["custo"]["usd_por_1000"] / 1000
        if usd_por_ticket:
            prem = json.loads((OUT_DIR / "f3_premissas.json").read_text(encoding="utf-8"))
            # minutos de triagem por ticket em que o custo humano iguala o custo do LLM por ticket
            equilibrio = {"rotulo": "câmbio é premissa não consultada; R$/h é premissa", "usd_por_ticket_llm": usd_por_ticket,
                          "minutos_por_ticket": [{"cambio": c, "reais_h": r,
                                                  "minutos": round(usd_por_ticket * c / r * 60, 6),
                                                  "segundos": round(usd_por_ticket * c / r * 3600, 4)}
                                                 for c in prem["cambio_brl_por_usd"] for r in [25, 35, 50]]}

    saida = {
        "e_adjudicado": {"original_errado": bruto, "n": int(len(adj)), "taxa_bruta": round(bruto / len(adj), 4),
                         "ponderado": round(e_adj, 4), "ic95_bootstrap_estratificado": [round(v, 4) for v in e_adj_ic],
                         "por_categoria": adj.groupby("rotulo_original")["errado"].agg(["sum", "count"]).astype(int)
                         .rename(columns={"sum": "original_errado", "count": "n"}).to_dict(orient="index")},
        "e_quase_duplicados": {"k": k_dup, "n": n_dup, "taxa": round(e_dup, 4), "ic95_wilson": [round(v, 4) for v in e_dup_ic]},
        "e_q2": {"fonte": fonte, "valor": round(e_q2, 4), "e_inferior": round(e_inf, 4), "e_superior": round(e_sup, 4),
                 "meta_ia_decide_li_ge": round(1 - e_inf, 4), "meta_ia_sugere_li_ge": round(1 - e_sup, 4),
                 "regra": "menor dos dois valores pontuais, com o IC da fonte escolhida (decisão do Gustavo antes da adjudicação)"},
        "faixas": bandas,
        "faixa_ia_decide_vazia": t_dec is None,
        "economia_cenario_A": custo[["min_por_ticket", "reais_por_hora", "custo_anual_triagem_reais", "economia_anual_reais"]]
        .to_dict(orient="records"),
        "economia_cenario_A_rotulo": "premissas (volume, minutos, R$/h) editáveis; cobertura = faixa IA decide no holdout por grupo",
        "economia_cenario_B": "0 (sem etapa separada de triagem); ganho viria do reroteamento evitado, não calculável",
        "ponto_equilibrio": equilibrio,
    }
    salvar_json(saida, "f3_faixas.json")
    print(f"e adjudicado: bruto {bruto}/{len(adj)}; ponderado {e_adj:.4f} IC {e_adj_ic}")
    print(f"e quase-dup: {k_dup}/{n_dup} = {e_dup:.4f} IC {e_dup_ic}; e_Q2 fonte {fonte}")
    print(f"faixas: {json.dumps(bandas, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
