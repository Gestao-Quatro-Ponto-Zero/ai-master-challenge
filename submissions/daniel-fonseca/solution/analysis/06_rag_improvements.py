"""RAG como classificador principal (decisão do Daniel): como aumentar o acerto sem sair do RAG?

A. Ajuste da votação: k vizinhos e "nitidez" do peso (similaridade^p), em 512 e 1536 dims.
B. Busca híbrida: vizinhos semânticos (embeddings) + vizinhos por palavras-chave (similaridade lexical,
   proxy do full-text search do Postgres), fundidos por Reciprocal Rank Fusion (RRF). Continua sendo
   recuperação por similaridade, sem modelo treinado.

Saída: solution/analysis/output/rag_improvements.json
Uso: .venv/bin/python solution/analysis/06_rag_improvements.py
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

warnings.filterwarnings("ignore", category=RuntimeWarning)  # avisos espúrios do matmul no macOS
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import load_raw_datasets as raw  # noqa: E402

df = raw.ds2()
train, test = df[df.split == "train"], df[df.split == "test"]
classes = sorted(df.topic_group.unique())
cidx = {c: i for i, c in enumerate(classes)}
ytr = np.array([cidx[c] for c in train.topic_group])
yte = np.array([cidx[c] for c in test.topic_group])
E = np.load(ROOT / "data/embeddings/ds2_te3s_1536.npy").astype(np.float32)
KMAX = 50


def neighbors(Q, D, kmax=KMAX):
    """top-kmax vizinhos por similaridade (cosseno; vetores já normalizados)."""
    idx, sim = np.zeros((Q.shape[0], kmax), int), np.zeros((Q.shape[0], kmax), np.float32)
    for s in range(0, Q.shape[0], 1000):
        S = Q[s:s + 1000] @ D.T
        S = S.toarray() if hasattr(S, "toarray") else S
        top = np.argpartition(-S, kmax, axis=1)[:, :kmax]
        ts = np.take_along_axis(S, top, axis=1)
        order = np.argsort(-ts, axis=1)
        idx[s:s + 1000], sim[s:s + 1000] = np.take_along_axis(top, order, 1), np.take_along_axis(ts, order, 1)
    return idx, sim


def vote(idx, w, k):
    v = np.zeros((len(idx), len(classes)))
    np.add.at(v, (np.repeat(np.arange(len(idx)), k), ytr[idx[:, :k]].ravel()), w[:, :k].ravel())
    share = v / np.maximum(v.sum(1, keepdims=True), 1e-12)
    return share.argmax(1), share.max(1)


def summarize(pred, conf):
    acc = float((pred == yte).mean())
    m = conf >= 0.8
    return {"accuracy": round(acc, 4), "coverage_at_0_8": round(float(m.mean()), 4),
            "precision_at_0_8": round(float((pred[m] == yte[m]).mean()), 4)}


out = {"grid": [], "hybrid": []}
print("## A. Ajuste da votação (acurácia)")
nb = {}
for dims in (512, 1536):
    V = E[:, :dims] / np.linalg.norm(E[:, :dims], axis=1, keepdims=True)
    nb[dims] = neighbors(V[test.index.values], V[train.index.values])
    idx, sim = nb[dims]
    for k in (1, 5, 10, 15, 25, 50):
        row = []
        for p in (1, 4, 16):
            pred, conf = vote(idx, np.clip(sim, 0, None) ** p, k)
            r = {"dims": dims, "k": k, "power": p, **summarize(pred, conf)}
            out["grid"].append(r)
            row.append(f"p={p}: {r['accuracy']:.3f}")
        print(f"dims {dims:4d} k={k:2d} | " + " | ".join(row))
best = max(out["grid"], key=lambda r: r["accuracy"])
print("melhor:", best)

print("\n## B. Busca híbrida (semântica + palavras-chave, RRF)")
vec = TfidfVectorizer(sublinear_tf=True, min_df=2)  # só recuperação lexical, sem classificador treinado
Ltr, Lte = vec.fit_transform(train.document), vec.transform(test.document)
lidx, lsim = neighbors(Lte, Ltr)
print(f"só palavras-chave (kNN lexical, k=15, p=4): {summarize(*vote(lidx, lsim ** 4, 15))['accuracy']:.3f}")
for dims in (512, 1536):
    sidx, _ = nb[dims]
    for k in (10, 15, 25):
        for rrf_k in (10, 60):
            # RRF: cada documento recebe 1/(rrf_k + posição) em cada lista; soma as duas listas
            scores = [{} for _ in range(len(sidx))]
            for lst in (sidx, lidx):
                for i in range(len(lst)):
                    for rank, d in enumerate(lst[i, :KMAX]):
                        scores[i][d] = scores[i].get(d, 0) + 1 / (rrf_k + rank + 1)
            fused = np.array([sorted(s, key=s.get, reverse=True)[:k] for s in scores])
            fw = np.array([[scores[i][d] for d in fused[i]] for i in range(len(fused))])
            pred, conf = vote(fused, fw, k)
            r = {"dims": dims, "k": k, "rrf_k": rrf_k, **summarize(pred, conf)}
            out["hybrid"].append(r)
            print(f"híbrido dims {dims:4d} k={k:2d} rrf_k={rrf_k:2d}: acurácia {r['accuracy']:.3f} | "
                  f"conf ≥ 0,8: {r['coverage_at_0_8']:.0%} → {r['precision_at_0_8']:.1%}")
out["best_vector_only"] = best
out["best_hybrid"] = max(out["hybrid"], key=lambda r: r["accuracy"])
(ROOT / "solution/analysis/output/rag_improvements.json").write_text(json.dumps(out, indent=1))
print("\nmelhor híbrido:", out["best_hybrid"])
