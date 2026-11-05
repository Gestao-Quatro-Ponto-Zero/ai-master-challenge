"""05 — O roteador validado em inglês continua bom quando a mensagem chega em português de chat?

1. Amostra 160 tickets do TESTE do Dataset 2 (20 por fila), nunca vistos no treino.
2. Claude Opus 5.5 reescreve cada um como um funcionário escreveria no chat, em português.
   Ele NÃO recebe a fila (sem vazamento do rótulo).
3. Pipeline do protótipo (máscara de PII -> Haiku 5.5 extrai/traduz -> classificador -> política P5)
   tenta acertar a fila original. Compara com o classificador no texto original em inglês.
4. Em 48 deles (6 por fila), troca o Haiku pelo Opus 5.5 na triagem: a qualidade muda o bastante
   para justificar ~40x o custo?
5. Salva os cenários do teste com colegas (16 = 2 por fila), já com a triagem em cache.

Tudo fica em cache (solution/outputs/llm_cache): rodar de novo sem chave reproduz os números.
Uso (de dentro de solution/): python analysis/05_pt_eval.py
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import config, llm, pii  # noqa: E402
from app.engine import decidir, faltando  # noqa: E402
from app.router import Router  # noqa: E402

OUT = config.SOLUTION / "outputs"
HAIKU, OPUS = "claude-haiku-5-5", "claude-opus-5-5"
SEED = 11


class Gerado(BaseModel):
    mensagem: str


GERADOR = """Abaixo está um ticket real de service desk interno, em inglês e pré-processado (sem pontuação, sem números, sem nomes e sem algumas palavras).
Escreva como o funcionário teria mandado ESSE MESMO pedido no chat do suporte, em português do Brasil, informal, em 1 a 3 frases.
Mantenha o pedido e os detalhes que existem. Não acrescente detalhes novos (nomes, números, sistemas). Se o texto estiver confuso, escreva a interpretação mais provável.
Responda só com a mensagem."""


def gerar_pt(texto_en: str) -> tuple[str, dict]:
    path = config.CACHE_DIR / "geracao_pt" / f"{llm._chave(texto_en, OPUS, 'low')}.json"
    if path.exists():
        d = json.loads(path.read_text())
        return d["mensagem"], d["meta"]
    if config.OFFLINE:
        raise SystemExit("Sem cache da geração e sem ANTHROPIC_API_KEY.")
    import anthropic
    r = anthropic.Anthropic(max_retries=4).messages.parse(
        model=OPUS, max_tokens=4000, system=GERADOR, output_format=Gerado, output_config={"effort": "low"},
        messages=[{"role": "user", "content": f"<ticket>\n{texto_en}\n</ticket>"}])
    meta = {"input_tokens": r.usage.input_tokens, "output_tokens": r.usage.output_tokens,
            "custo_usd": llm.custo_usd(OPUS, r.usage.input_tokens, r.usage.output_tokens), "request_id": r._request_id}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"texto_en": texto_en, "mensagem": r.parsed_output.mensagem, "meta": meta},
                               ensure_ascii=False, indent=1))
    return r.parsed_output.mensagem, meta


pred = pd.read_csv(OUT / "ds2_test_predictions.csv")
amostra = pred.groupby("queue").sample(20, random_state=SEED).reset_index(drop=True)
router = Router()

with ThreadPoolExecutor(8) as ex:
    gen = list(ex.map(gerar_pt, amostra.text))
amostra["texto_pt"] = [g[0] for g in gen]
custo = {"geracao_opus": sum(g[1]["custo_usd"] for g in gen)}


def pipeline(texto_pt: str, model: str):
    tri, meta = llm.triar(pii.mascarar(texto_pt), model=model, effort="low")
    rota = router.prever(tri.texto_ingles)
    d = decidir(tri, rota, ja_perguntou=True)  # sem perguntas: mede só a 1ª mensagem
    return tri, meta, d


def rodar(df: pd.DataFrame, model: str) -> pd.DataFrame:
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda t: pipeline(t, model), df.texto_pt))
    out = df[["queue", "pred", "ok", "texto_pt"]].copy()
    out["fila"] = [d.fila for _, _, d in res]
    out["conf"] = [d.conf for _, _, d in res]
    out["auto"] = [d.destino == "fila" for _, _, d in res]
    out["llm_fila"] = [t.fila_sugerida_llm for t, _, _ in res]
    out["ok_pt"] = out.fila == out.queue
    out["ok_llm"] = out.llm_fila == out.queue
    out["concorda"] = out.fila == out.llm_fila
    # campos obrigatórios da fila VERDADEIRA que o cliente já informou na 1ª mensagem
    out["campos_obrig_ok"] = [not faltando(q, t.campos.model_dump()) for q, (t, _, _) in zip(df.queue, res)]
    out["n_campos"] = [sum(v is not None for v in t.campos.model_dump().values()) for t, _, _ in res]
    out["texto_ingles"] = [t.texto_ingles for t, _, _ in res]
    out["custo_usd"] = [m.get("custo_usd", 0) for _, m, _ in res]
    out["latencia_s"] = [m.get("latencia_s", np.nan) for _, m, _ in res]
    out["campos"] = [json.dumps({k: v for k, v in t.campos.model_dump().items() if v}, ensure_ascii=False)
                     for t, _, _ in res]
    return out


def resumo(r: pd.DataFrame) -> dict:
    a = r[r.auto]
    return {
        "n": len(r),
        "acerto_classificador_texto_original_en": round(r.ok.mean(), 3),
        "acerto_pipeline_pt": round(r.ok_pt.mean(), 3),
        "acerto_so_llm": round(r.ok_llm.mean(), 3),
        "concordancia_llm_classificador": round(r.concorda.mean(), 3),
        "acerto_quando_concordam": round(r[r.concorda].ok_pt.mean(), 3),
        "acerto_quando_discordam_classificador": round(r[~r.concorda].ok_pt.mean(), 3),
        "acerto_quando_discordam_llm": round(r[~r.concorda].ok_llm.mean(), 3),
        "pct_automatico_P5": round(r.auto.mean() * 100, 1),
        "acerto_no_automatico_P5": round(a.ok_pt.mean(), 3) if len(a) else None,
        "auto_e_discordam_n": int((~a.concorda).sum()),
        "acerto_auto_quando_discordam": round(a[~a.concorda].ok_pt.mean(), 3) if (~a.concorda).any() else None,
        "pct_campos_obrigatorios_completos": round(r.campos_obrig_ok.mean() * 100, 1),
        "media_campos_extraidos": round(r.n_campos.mean(), 2),
        "custo_total_usd": round(r.custo_usd.sum(), 4),
        "custo_por_mensagem_usd": round(r.custo_usd.mean(), 6),
        "latencia_mediana_s": round(r.latencia_s.median(), 2) if r.latencia_s.notna().any() else None,
    }


rh = rodar(amostra, HAIKU)
sub_idx = amostra.groupby("queue").head(6).index
ro = rodar(amostra.loc[sub_idx], OPUS)
rh_sub = rh.loc[sub_idx]

R = {"haiku_160": resumo(rh), "haiku_48": resumo(rh_sub), "opus_48": resumo(ro)}
R["por_fila_haiku"] = rh.groupby("queue").agg(acerto_en=("ok", "mean"), acerto_pt=("ok_pt", "mean"),
                                              auto=("auto", "mean")).round(2).to_dict(orient="index")
R["campos_presenca_concordancia_haiku_opus"] = round(float(np.mean([
    set(json.loads(a)) == set(json.loads(b)) for a, b in zip(rh_sub.campos, ro.campos)])), 3)
R["custo_usd"] = {**custo, "triagem_haiku_160": R["haiku_160"]["custo_total_usd"],
                  "triagem_opus_48": R["opus_48"]["custo_total_usd"]}

pd.set_option("display.width", 200)
print(json.dumps(R, indent=1, ensure_ascii=False))
print("\nErros do pipeline PT (Haiku), primeiros 15:")
err = rh[~rh.ok_pt][["queue", "fila", "conf", "llm_fila", "texto_pt"]]
print(err.head(15).to_string(max_colwidth=90))

rh.to_csv(OUT / "pt_eval_haiku.csv", index=False)
ro.to_csv(OUT / "pt_eval_opus.csv", index=False)
(OUT / "pt_eval_results.json").write_text(json.dumps(R, indent=1, ensure_ascii=False))

# Cenários do teste com colegas: 2 por fila, sorteados da amostra. A triagem (Haiku) já está em cache.
cen = amostra.groupby("queue").sample(2, random_state=SEED + 1)
cen = cen.sample(frac=1, random_state=SEED + 2).reset_index(drop=True)
cenarios = [{"id": f"C{i+1:02d}", "fila_verdadeira": r.queue, "texto_pt": r.texto_pt, "texto_original_en": r.text}
            for i, r in cen.iterrows()]
config.SCENARIOS_PATH.parent.mkdir(exist_ok=True)
config.SCENARIOS_PATH.write_text(json.dumps(cenarios, ensure_ascii=False, indent=1))
print(f"\n{len(cenarios)} cenários salvos em {config.SCENARIOS_PATH}")
