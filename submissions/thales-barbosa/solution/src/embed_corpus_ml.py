# -*- coding: utf-8 -*-
"""D-018 — Embeddings MULTILÍNGUES do corpus D2 (portal pt-BR), resumável.

Mesmo desenho de embed_corpus.py, com paraphrase-multilingual-MiniLM-L12-v2:
pergunta em português e ticket em inglês caem no mesmo espaço vetorial.
Saída: models/embeddings_d2_ml.npy · progresso: models/embed_progress_ml.json.
Re-execute até imprimir DONE (ou rode 1x com orçamento longo).
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
from src.ticket_ai import MODELS_DIR, MULTILINGUAL_MODEL_NAME, embed_texts

CHUNK = 512
TIME_BUDGET_S = 150 * 60  # orçamento longo: rodar 1x em background até DONE
DIM = 384


def main() -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    d2 = build_dataset2()
    texts = d2["Document"].tolist()
    n = len(texts)
    out = MODELS_DIR / "embeddings_d2_ml.npy"
    prog_file = MODELS_DIR / "embed_progress_ml.json"

    if out.exists():
        mm = open_memmap(out, mode="r+")
        assert mm.shape == (n, DIM), "shape do memmap não bate com o corpus"
    else:
        mm = open_memmap(out, mode="w+", dtype=np.float32, shape=(n, DIM))
    done = json.loads(prog_file.read_text())["done"] if prog_file.exists() else 0

    t0 = time.time()
    while done < n and (time.time() - t0) < TIME_BUDGET_S:
        end = min(done + CHUNK, n)
        mm[done:end] = embed_texts(
            texts[done:end], model_name=MULTILINGUAL_MODEL_NAME).astype(np.float32)
        done = end
        mm.flush()
        prog_file.write_text(json.dumps({"done": done, "total": n}))
        print(f"progresso: {done:,}/{n:,} ({done / n:.1%})", flush=True)

    print("DONE" if done >= n else f"PARCIAL ({done:,}/{n:,}) — re-execute")


if __name__ == "__main__":
    main()
