"""RAG + LLM: o LLM decide a categoria vendo os K tickets mais parecidos recuperados (com a categoria de cada um).

É o fluxo que vai para o n8n: embedding do ticket → busca no pgvector → prompt com os casos parecidos → LLM.
Mesma amostra do zero-shot (50 por categoria, seed 42) para comparar: zero-shot × voto do RAG × RAG + LLM × TF-IDF.

Confiança usada na política: a fração de votos do RAG (calibrada), não a "confiança" declarada pelo LLM.

Saída: solution/analysis/output/rag_llm_eval.json
Uso: .venv/bin/python solution/analysis/07_rag_llm_eval.py [--model gpt-5.4-mini] [--k 15]
"""
import json
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", category=RuntimeWarning)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "solution/analysis"))
sys.argv += [] if "--n" in sys.argv else ["--n", "50"]
zs = __import__("04_zero_shot_eval")  # reaproveita amostra, chamada à API e baseline

K = int(zs.arg("--k", "15"))
classes, train, sample = zs.classes, zs.train, zs.sample
cidx = {c: i for i, c in enumerate(classes)}

E = np.load(ROOT / "data/embeddings/ds2_te3s_1536.npy").astype(np.float32)[:, :512]
E /= np.linalg.norm(E, axis=1, keepdims=True)
S = E[sample.index.values] @ E[train.index.values].T
top = np.argsort(-S, axis=1)[:, :50]
sims = np.take_along_axis(S, top, axis=1)

# voto do RAG (melhor configuração em 512 dims: k=50, peso sim^16)
votes = np.zeros((len(sample), len(classes)))
ytr = np.array([cidx[c] for c in train.topic_group])
np.add.at(votes, (np.repeat(np.arange(len(sample)), 50), ytr[top].ravel()), (sims.clip(0) ** 16).ravel())
share = votes / votes.sum(1, keepdims=True)
rag_pred, rag_conf = np.array(classes)[share.argmax(1)], share.max(1)

SYSTEM = ("You classify IT service desk tickets of one specific organization. Texts are preprocessed "
          "(lowercase, stopwords and names removed). You receive the new ticket and the most similar past tickets "
          "with the category a human assigned to each. Categories follow this organization's internal taxonomy; "
          "rely on the labeled examples more than on the category names. "
          f"Choose exactly one category from: {', '.join(classes)}. Return JSON with category and confidence (0-1).")


def prompt(i: int) -> str:
    ex = "\n".join(f"- [{train.topic_group.iloc[j]}] (similarity {sims[i, r]:.2f}) {train.document.iloc[j][:400]}"
                   for r, j in enumerate(top[i, :K]))
    return f"Similar past tickets:\n{ex}\n\nNew ticket:\n{sample.document.iloc[i][:3000]}"


def call(i: int) -> dict:
    body = {"model": zs.MODEL, "reasoning_effort": "low",
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt(i)}],
            "response_format": {"type": "json_schema", "json_schema": zs.SCHEMA}}
    import urllib.request, time  # noqa: E401
    for attempt in range(6):
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {zs.KEY}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read())
            o = json.loads(d["choices"][0]["message"]["content"])
            o["usage"] = d["usage"]
            return o
        except Exception as e:  # noqa: BLE001
            if getattr(e, "code", 429) not in (429, 500, 502, 503, 504):
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("falhou")


with ThreadPoolExecutor(8) as ex:
    ans = list(ex.map(call, range(len(sample))))
llm_pred = np.array([a["category"] for a in ans])
y = sample.topic_group.values
tok = {k: sum(a["usage"][k] for a in ans) for k in ("prompt_tokens", "completion_tokens")}

prev = json.loads((ROOT / "solution/analysis/output/zero_shot_eval.json").read_text())
res = {"model": zs.MODEL, "k_in_prompt": K, "n": len(sample), "usage": tok,
       "zero_shot_accuracy": prev["zero_shot"]["accuracy"],
       "tfidf_lr_accuracy": prev["tfidf_lr_same_sample"]["accuracy"],
       "rag_vote_accuracy": round(float((rag_pred == y).mean()), 4),
       "rag_llm_accuracy": round(float((llm_pred == y).mean()), 4)}
agree = llm_pred == rag_pred
for t in (0.0, 0.6, 0.8):
    m = agree & (rag_conf >= t)
    res[f"agree_conf_{t}"] = {"coverage": round(float(m.mean()), 4), "precision": round(float((llm_pred[m] == y[m]).mean()), 4)}
res["disagree"] = {"share": round(float((~agree).mean()), 4),
                   "llm_acc": round(float((llm_pred[~agree] == y[~agree]).mean()), 4),
                   "vote_acc": round(float((rag_pred[~agree] == y[~agree]).mean()), 4)}
(ROOT / "solution/analysis/output/rag_llm_eval.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
print(json.dumps({k: v for k, v in res.items()}, ensure_ascii=False, indent=1))
