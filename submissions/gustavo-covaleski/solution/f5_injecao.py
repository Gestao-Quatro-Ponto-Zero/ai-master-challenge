import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from comum import OUT_DIR, PLANNING_DIR, SEED, ler_ds2, ler_env_chave, salvar_json

ATAQUES = Path(__file__).resolve().parent / "tests" / "golden" / "ataques_v1.json"
F5_DIR = PLANNING_DIR / "F5"
N_TICKETS = 20
OBS = "ataques inseridos em linguagem natural num texto pré-processado; em produção, o atacante escreve no texto bruto"


def carregar_ataques():
    return json.loads(ATAQUES.read_text(encoding="utf-8"))["ataques"]


def alvo(categorias, pred_limpa, deslocamento):
    # nunca igual à previsão limpa: deslocamentos 1–5 num ciclo de 8 categorias
    return categorias[(categorias.index(pred_limpa) + deslocamento) % len(categorias)]


def montar_pares(tickets: pd.DataFrame, pred_limpa: dict, categorias):
    pares = []
    for t in tickets.itertuples():
        for a in carregar_ataques():
            al = alvo(categorias, pred_limpa[t.id], a["deslocamento_alvo"])
            pares.append({"id": t.id, "ataque": a["id"], "alvo": al,
                          "texto": f"{t.Document} {a['texto'].format(alvo=al)}"})
    return pares


def taxas(pares, pred_ataque, pred_limpa):
    troca = sum(pred_ataque[i] != pred_limpa[p["id"]] for i, p in enumerate(pares))
    sucesso = sum(pred_ataque[i] == p["alvo"] != pred_limpa[p["id"]] for i, p in enumerate(pares))  # só mudança PARA o alvo
    por_ataque = {}
    for a in {p["ataque"] for p in pares}:
        idx = [i for i, p in enumerate(pares) if p["ataque"] == a]
        por_ataque[a] = {"troca": sum(pred_ataque[i] != pred_limpa[pares[i]["id"]] for i in idx),
                         "sucesso": sum(pred_ataque[i] == pares[i]["alvo"] != pred_limpa[pares[i]["id"]] for i in idx), "n": len(idx)}
    n = len(pares)
    return {"n_pares": n, "troca_de_rotulo": {"n": troca, "taxa": round(troca / n, 4)},
            "sucesso_do_ataque": {"n": sucesso, "taxa": round(sucesso / n, 4)}, "por_ataque": por_ataque}


def main():
    from triagem import carregar_modelo
    df = ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")
    tickets = df[df["split_grupo"] == "holdout"].sample(N_TICKETS, random_state=SEED)
    m = carregar_modelo()["pipeline"]
    categorias = sorted(m.classes_)
    limpa_cl = dict(zip(tickets["id"], m.predict(tickets["Document"])))
    pares = montar_pares(tickets, limpa_cl, categorias)
    ataque_cl = list(m.predict([p["texto"] for p in pares]))
    saida = {"observacao": OBS, "ataques": "solution/tests/golden/ataques_v1.json", "n_tickets": N_TICKETS, "seed": SEED,
             "alvo": "categoria diferente da prevista pelo clássico no texto limpo",
             "classico": taxas(pares, ataque_cl, limpa_cl)}

    chave = ler_env_chave()
    if not chave:
        saida["llm"] = "pendente: ANTHROPIC_API_KEY ausente"
    else:
        import anthropic
        from f3_llm import FALHA, classificar, montar_system
        prem = json.loads((OUT_DIR / "f3_premissas.json").read_text(encoding="utf-8"))
        system = montar_system(df[df["split_grupo"] == "treino"])
        client = anthropic.Anthropic(api_key=chave, max_retries=0)
        entradas = [(t.id, t.Document) for t in tickets.itertuples()] + [(p["id"], p["texto"]) for p in pares]
        with ThreadPoolExecutor(8) as ex:
            res = list(ex.map(lambda e: classificar(client, prem["modelo"], system, e[0], e[1]), entradas))
        F5_DIR.mkdir(parents=True, exist_ok=True)
        with open(F5_DIR / "f5_injecao_llm_log.jsonl", "w", encoding="utf-8") as f:
            for k, (tentativas, pred) in enumerate(res):
                for t in tentativas:
                    f.write(json.dumps({"ordem": k, "id": t["id"], "tipo": "limpo" if k < N_TICKETS else pares[k - N_TICKETS]["ataque"],
                                        "latencia_ms": t["lat_ms"], "tokens_entrada": t["in"], "tokens_saida": t["out"],
                                        "resposta_bruta": t["bruto"], "valida": t["valida"]}, ensure_ascii=False) + "\n")
        limpa_llm = {tickets["id"].iloc[k]: res[k][1] for k in range(N_TICKETS)}
        ataque_llm = [r[1] for r in res[N_TICKETS:]]
        t = taxas(pares, ataque_llm, limpa_llm)
        t["falhas_limpo"] = sum(v == FALHA for v in limpa_llm.values())
        t["falhas_ataque"] = sum(v == FALHA for v in ataque_llm)
        t["pares_em_que_alvo_coincide_com_previsao_limpa_do_llm"] = sum(p["alvo"] == limpa_llm[p["id"]] for p in pares)
        t["acuracia_limpo_contra_rotulo"] = round(float((tickets["Topic_group"].values == [limpa_llm[i] for i in tickets["id"]]).mean()), 4)
        t["chamadas"] = len(entradas)
        saida["llm"] = t
    saida["classico"]["acuracia_limpo_contra_rotulo"] = round(float((tickets["Topic_group"].values == [limpa_cl[i] for i in tickets["id"]]).mean()), 4)
    salvar_json(saida, "f5_injecao.json")
    print(json.dumps({k: saida[k] for k in ("classico", "llm")}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
