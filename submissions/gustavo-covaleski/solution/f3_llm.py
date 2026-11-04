import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

from comum import F3_DIR, OUT_DIR, SEED, boot_ic, ler_ds2, ler_env_chave, salvar_json

CATEGORIAS = ["Access", "Administrative rights", "HR Support", "Hardware", "Internal Project",
              "Miscellaneous", "Purchase", "Storage"]
PROMPT = Path(__file__).resolve().parent / "prompts" / "classificar_v1.txt"
N_AMOSTRA = 400
MAX_TOKENS = 64
FALHA = "falha"


def validar(texto: str):
    """JSON estrito: o texto inteiro (sem espaços nas pontas) tem de ser o objeto, com categoria válida."""
    try:
        obj = json.loads(texto.strip())
    except (json.JSONDecodeError, AttributeError):
        return None
    if not isinstance(obj, dict) or obj.get("categoria") not in CATEGORIAS:
        return None
    c = obj.get("confianca")
    if not isinstance(c, (int, float)) or isinstance(c, bool) or not 0 <= c <= 1:
        return None
    return obj


def montar_system(treino: pd.DataFrame) -> str:
    ex = []
    for c in CATEGORIAS:
        t = treino[treino["Topic_group"] == c].sample(1, random_state=SEED)["Document"].iloc[0]
        ex.append(f"<ticket>{t}</ticket>\n{json.dumps({'categoria': c, 'confianca': 1.0})}")
    return PROMPT.read_text(encoding="utf-8").replace("{exemplos}", "\n\n".join(ex))


def chamar(client, modelo, system, texto):
    import anthropic
    erros = 0
    for tentativa in range(3):
        try:
            t0 = time.perf_counter()
            r = client.messages.create(
                model=modelo, max_tokens=MAX_TOKENS, system=system,
                # Haiku 5.5 recusa temperature != padrão; determinismo aproximado via thinking off + effort low
                thinking={"type": "disabled"}, output_config={"effort": "low"},
                messages=[{"role": "user", "content": f"<ticket>{texto}</ticket>"}])
            lat = (time.perf_counter() - t0) * 1000
            bruto = "".join(b.text for b in r.content if b.type == "text")
            return {"lat_ms": lat, "in": r.usage.input_tokens, "out": r.usage.output_tokens,
                    "bruto": bruto, "erros_api": erros}
        except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError) as e:
            erros += 1
            ultimo = type(e).__name__
            time.sleep(2 ** tentativa)
    return {"lat_ms": None, "in": 0, "out": 0, "bruto": None, "erros_api": erros, "erro": ultimo}


def classificar(client, modelo, system, id_, texto):
    tentativas = []
    for _ in range(2):  # 1 chamada + 1 repetição se a saída for inválida
        r = chamar(client, modelo, system, texto)
        obj = validar(r["bruto"]) if r["bruto"] is not None else None
        r.update(id=int(id_), valida="s" if obj else "n")
        tentativas.append(r)
        if obj or r["bruto"] is None:
            break
    return tentativas, (obj["categoria"] if obj else FALHA)


def macro_f1(y, p):
    return f1_score(y, p, labels=CATEGORIAS, average="macro", zero_division=0)


def metr(y, p):
    return {"acuracia": round(accuracy_score(y, p), 4), "acuracia_ic95": [round(v, 4) for v in boot_ic(y, p, accuracy_score)],
            "macro_f1": round(macro_f1(y, p), 4), "macro_f1_ic95": [round(v, 4) for v in boot_ic(y, p, macro_f1)]}


def main():
    import anthropic
    chave = ler_env_chave()
    if not chave:
        salvar_json({"status": "pendente: ANTHROPIC_API_KEY ausente"}, "f3_llm.json")
        print("PENDENTE: sem chave")
        return
    prem = json.loads((OUT_DIR / "f3_premissas.json").read_text(encoding="utf-8"))
    fx = json.loads((OUT_DIR / "f3_faixas.json").read_text(encoding="utf-8"))
    t_dec = fx["faixas"]["ia_decide"]["limiar"]

    df = ler_ds2().merge(pd.read_csv(OUT_DIR / "f1_splits.csv"), on="id")
    pr = pd.read_csv(OUT_DIR / "f3_probs_holdout_grupo.csv")
    fora = pr[pr["p_max"] < t_dec] if t_dec is not None else pr
    amostra = fora.sample(N_AMOSTRA, random_state=SEED).merge(df[["id", "Document"]], on="id")
    system = montar_system(df[df["split_grupo"] == "treino"])

    client = anthropic.Anthropic(api_key=chave, max_retries=0)
    tokens_system = client.messages.count_tokens(
        model=prem["modelo"], system=system, messages=[{"role": "user", "content": "<ticket>x</ticket>"}]).input_tokens

    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda row: classificar(client, prem["modelo"], system, row.id, row.Document),
                          amostra.itertuples()))
    F3_DIR.mkdir(parents=True, exist_ok=True)
    with open(F3_DIR / "f3_llm_log.jsonl", "w", encoding="utf-8") as f:
        for tentativas, _ in res:
            for t in tentativas:
                f.write(json.dumps({"id": t["id"], "latencia_ms": t["lat_ms"], "tokens_entrada": t["in"],
                                    "tokens_saida": t["out"], "resposta_bruta": t["bruto"], "valida": t["valida"],
                                    "erros_api": t["erros_api"]}, ensure_ascii=False) + "\n")

    chamadas = [t for tentativas, _ in res for t in tentativas]
    pred_llm = np.array([p for _, p in res])
    y = amostra["rotulo"].values
    pred_cl = amostra["pred"].values
    lat = [t["lat_ms"] for t in chamadas if t["lat_ms"] is not None]
    tin = np.mean([t["in"] for t in chamadas if t["lat_ms"] is not None])
    tout = np.mean([t["out"] for t in chamadas if t["lat_ms"] is not None])
    n_cham_por_ticket = len([t for t in chamadas if t["lat_ms"] is not None]) / N_AMOSTRA
    pin, pout = prem["preco_usd_por_mtok_entrada"], prem["preco_usd_por_mtok_saida"]
    usd_chamada = (tin * pin + tout * pout) / 1e6
    usd_1000 = usd_chamada * n_cham_por_ticket * 1000
    acc_llm, acc_cl = accuracy_score(y, pred_llm), accuracy_score(y, pred_cl)
    ganho = acc_llm - acc_cl

    # estimativa do híbrido no holdout inteiro: clássico na faixa IA decide, LLM no restante (acurácia da amostra)
    cob_dec = fx["faixas"]["ia_decide"]["cobertura"]
    prec_dec = fx["faixas"]["ia_decide"]["precisao"]
    acc_hibrido = cob_dec * prec_dec + (1 - cob_dec) * acc_llm

    saida = {
        "modelo": prem["modelo"], "configuracao": prem["configuracao_usada"], "prompt": "solution/prompts/classificar_v1.txt",
        "amostra": {"n": N_AMOSTRA, "universo": f"holdout por grupo com p_max < {t_dec} (fora da faixa IA decide)",
                    "n_universo": int(len(fora)), "seed": SEED},
        "llm": metr(y, pred_llm), "classico_mesmos_400": metr(y, pred_cl),
        "falhas": {"n": int((pred_llm == FALHA).sum()), "taxa": round(float((pred_llm == FALHA).mean()), 4),
                   "saidas_invalidas_primeira_tentativa": int(sum(1 for tentativas, _ in res if tentativas[0]["valida"] == "n")),
                   "erros_api_total": int(sum(t["erros_api"] for t in chamadas))},
        "latencia_ms": {"p50": round(float(np.percentile(lat, 50)), 1), "p95": round(float(np.percentile(lat, 95)), 1),
                        "n_chamadas": len(lat), "obs": "8 chamadas concorrentes; latência por chamada, medida no cliente"},
        "tokens": {"entrada_media": round(float(tin), 1), "saida_media": round(float(tout), 1),
                   "system_com_exemplos_fixos": int(tokens_system),
                   "chamadas_por_ticket": round(n_cham_por_ticket, 4)},
        "custo": {"usd_por_1000": round(usd_1000, 4),
                  "usd_por_1000_so_exemplos_e_instrucoes": round(tokens_system * pin / 1e6 * n_cham_por_ticket * 1000, 4),
                  "preco": {"entrada_usd_mtok": pin, "saida_usd_mtok": pout, "fonte": prem["fonte_preco"], "data": prem["consulta_em"]}},
        "hibrido": {"acuracia_faixa_abstencao_llm": round(acc_llm, 4), "acuracia_faixa_abstencao_classico": round(acc_cl, 4),
                    "ganho_pp": round(100 * ganho, 2),
                    "acertos_adicionais_por_1000": round(1000 * ganho, 1),
                    "usd_por_acerto_adicional": round(usd_1000 / (1000 * ganho), 6) if ganho > 0 else None,
                    "acuracia_estimada_holdout_inteiro": round(acc_hibrido, 4),
                    "estimativa_rotulo": "cobertura e precisão da faixa IA decide (f3_faixas.json) + acurácia do LLM na amostra de abstenção"},
    }
    salvar_json(saida, "f3_llm.json")
    print(json.dumps({k: saida[k] for k in ["llm", "classico_mesmos_400", "falhas", "latencia_ms", "tokens", "custo", "hibrido"]},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
