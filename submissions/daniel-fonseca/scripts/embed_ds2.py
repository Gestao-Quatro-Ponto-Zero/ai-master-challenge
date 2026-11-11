"""Gera embeddings (text-embedding-3-small, 1536 dims) dos 47.837 documentos do DS2.

Saída local (gitignored): data/embeddings/ds2_te3s_1536.npy (float16, na ordem de ds2_tickets.id).
Retomável: cada lote é salvo em data/embeddings/shards/ e não é refeito.
Custo estimado: ~3M tokens → centavos de dólar.

Uso: .venv/bin/python scripts/embed_ds2.py
"""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

import load_raw_datasets as raw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/embeddings"
SHARDS = OUT / "shards"
MODEL, DIMS, BATCH = "text-embedding-3-small", 1536, 1000


def embed(texts: list[str], key: str) -> tuple[np.ndarray, int]:
    body = json.dumps({"model": MODEL, "input": texts, "dimensions": DIMS}).encode()
    for attempt in range(6):
        req = urllib.request.Request("https://api.openai.com/v1/embeddings", data=body,
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
            vecs = np.array([d["embedding"] for d in sorted(data["data"], key=lambda d: d["index"])], dtype=np.float32)
            return vecs, data["usage"]["total_tokens"]
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            code = getattr(e, "code", None)
            if code and code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("falhou após 6 tentativas")


if __name__ == "__main__":
    raw.load_env()
    key = os.environ["OPENAI_API_KEY"]
    docs = raw.ds2()["document"].tolist()
    SHARDS.mkdir(parents=True, exist_ok=True)
    tokens, t0 = 0, time.time()
    for start in range(0, len(docs), BATCH):
        shard = SHARDS / f"{start:06d}.npy"
        if shard.exists():
            continue
        vecs, used = embed(docs[start:start + BATCH], key)
        np.save(shard, vecs.astype(np.float16))
        tokens += used
        print(f"{start + len(vecs):>6}/{len(docs)} | tokens nesta execução: {tokens:,} | {time.time() - t0:.0f}s", flush=True)
    full = np.concatenate([np.load(SHARDS / f"{s:06d}.npy") for s in range(0, len(docs), BATCH)])
    assert full.shape == (len(docs), DIMS), full.shape
    np.save(OUT / "ds2_te3s_1536.npy", full)
    print("ok:", full.shape, f"| tokens nesta execução: {tokens:,} | custo ≈ US$ {tokens / 1e6 * 0.02:.3f} (US$ 0,02/1M — confirmar preço vigente)")
