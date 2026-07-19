# -*- coding: utf-8 -*-
"""FASE 5 — Gera embeddings do corpus D2 de forma RESUMÁVEL (rodar até concluir).

Cada execução processa chunks até ~8,5 min e sai; o progresso fica em
models/embed_progress.json e o resultado em models/embeddings_d2.npy (memmap,
ordem natural do d2 pós-filtro = ordem de corpus.parquet/FAISS).
Re-execute até imprimir DONE.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from numpy.lib.format import open_memmap

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_prep import build_dataset2
from src.ticket_ai import MODELS_DIR, embed_texts

CHUNK = 1024
TIME_BUDGET_S = 8.5 * 60
DIM = 384

def main() -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    d2 = build_dataset2()
    texts = d2["Document"].tolist()
    n = len(texts)
    out = MODELS_DIR / "embeddings_d2.npy"
    prog_file = MODELS_DIR / "embed_progress.json"

    if out.exists():
        mm = open_memmap(out, mode="r+")
        assert mm.shape == (n, DIM), "shape do memmap não bate com o corpus"
    else:
        mm = open_memmap(out, mode="w+", dtype=np.float32, shape=(n, DIM))
    done = json.loads(prog_file.read_text())["done"] if prog_file.exists() else 0

    t0 = time.time()
    while done < n and (time.time() - t0) < TIME_BUDGET_S:
        end = min(done + CHUNK, n)
        mm[done:end] = embed_texts(texts[done:end]).astype(np.float32)
        done = end
        mm.flush()
        prog_file.write_text(json.dumps({"done": done, "total": n}))
        print(f"progresso: {done:,}/{n:,} ({done / n:.1%})", flush=True)

    print("DONE" if done >= n else f"PARCIAL ({done:,}/{n:,}) — re-execute")


if __name__ == "__main__":
    main()
