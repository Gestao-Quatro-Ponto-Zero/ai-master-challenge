"""Valida a função SQL classify_ticket (Supabase, pgvector HNSW) contra o cálculo local exato (ADR-0010).

Amostra: 500 tickets do split de teste (sorteio com seed 42). Para cada um, a consulta usa o embedding
já gravado em ds2_embeddings como se fosse um ticket novo — a função só busca vizinhos do split de treino.
Compara: acurácia no banco × acurácia local exata (busca exaustiva em float32) nos mesmos tickets,
concordância entre os dois, distribuição dos 3 níveis e latência por chamada.

Saída: solution/analysis/output/db_rag_validation.json
Uso: .venv/bin/python solution/analysis/09_db_rag_validation.py
"""
import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import psycopg

warnings.filterwarnings("ignore", category=RuntimeWarning)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import load_raw_datasets as raw  # noqa: E402

N, K, P = 500, 50, 16
SENS = ("HR Support", "Administrative rights")


def tier(cat: str, conf: float, sens_share: float) -> int:
    if cat in SENS or sens_share >= 0.3 or conf < 0.5:
        return 3
    return 1 if conf >= 0.9 else 2


raw.load_env()
df = raw.ds2()
train, test = df[df.split == "train"], df[df.split == "test"]
ids = np.sort(np.random.default_rng(42).choice(test.index.values, size=N, replace=False))

# --- referência local exata (mesmo cálculo de 08_rag_only_policy.py) ---
E = np.load(ROOT / "data/embeddings/ds2_te3s_1536.npy").astype(np.float32)[:, :512]
E /= np.linalg.norm(E, axis=1, keepdims=True)
S = E[ids] @ E[train.index.values].T
top = np.argpartition(-S, K, axis=1)[:, :K]
w = np.take_along_axis(S, top, 1).clip(0) ** P
ytr = train.topic_group.values
local = []
for r in range(N):
    votes = {}
    for j, wt in zip(top[r], w[r]):
        votes[ytr[j]] = votes.get(ytr[j], 0.0) + float(wt)
    tot = sum(votes.values())
    cat = max(votes, key=votes.get)
    local.append((cat, votes[cat] / tot, sum(v for c, v in votes.items() if c in SENS) / tot))

# --- banco: uma chamada por ticket, como o n8n fará ---
rows, lat = [], []
with psycopg.connect(os.environ["SUPABASE_DB_URL"]) as conn:
    for i in ids:
        t0 = time.perf_counter()
        r = conn.execute(
            "select c.category, c.confidence, c.sensitive_share, jsonb_array_length(c.similar_cases) "
            "from public.ds2_embeddings e cross join lateral public.classify_ticket(e.embedding) c "
            "where e.id = %s", (int(i),)).fetchone()
        lat.append(time.perf_counter() - t0)
        rows.append(r)
    plan = conn.execute(
        "explain select e.id from public.ds2_embeddings e join public.ds2_tickets t on t.id = e.id "
        "where t.split = 'train' order by e.embedding <=> (select embedding from public.ds2_embeddings where id = 0) "
        "limit 50").fetchall()

y = df.loc[ids, "topic_group"].values
db_pred = np.array([r[0] for r in rows])
loc_pred = np.array([c for c, _, _ in local])
db_tiers = np.array([tier(r[0], r[1], r[2]) for r in rows])
loc_tiers = np.array([tier(*x) for x in local])
out = {
    "sample": {"n": N, "split": "test", "seed": 42},
    "accuracy_db": round(float((db_pred == y).mean()), 4),
    "accuracy_local_exact": round(float((loc_pred == y).mean()), 4),
    "agreement_category": round(float((db_pred == loc_pred).mean()), 4),
    "agreement_tier": round(float((db_tiers == loc_tiers).mean()), 4),
    "max_abs_confidence_diff": round(float(np.max(np.abs([r[1] - l[1] for r, l in zip(rows, local)]))), 4),
    "tiers_db": {f"nivel_{t}": {"share": round(float((db_tiers == t).mean()), 4),
                                "precision": round(float((db_pred[db_tiers == t] == y[db_tiers == t]).mean()), 4)}
                 for t in (1, 2, 3)},
    "similar_cases_always_5": bool(all(r[3] == 5 for r in rows)),
    "latency_ms": {"p50": round(float(np.median(lat)) * 1000, 1), "p95": round(float(np.percentile(lat, 95)) * 1000, 1)},
    "uses_hnsw_index": any("ds2_embeddings_hnsw_idx" in p[0] for p in plan),
    "reference_full_holdout": "output/rag_only_policy.json (82,8% em 9.567 tickets)",
}
print(json.dumps(out, ensure_ascii=False, indent=1))
(ROOT / "solution/analysis/output/db_rag_validation.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
