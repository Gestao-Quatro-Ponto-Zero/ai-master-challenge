"""Carrega os embeddings do DS2 na tabela ds2_embeddings do Supabase (halfvec 512) via COPY binário.

Origem: data/embeddings/ds2_te3s_1536.npy (gerado por scripts/embed_ds2.py; linha i = ds2_tickets.id i).
Transformação: trunca para 512 dims e renormaliza — equivale ao parâmetro `dimensions=512` da API da OpenAI,
que é o que o n8n usa para embutir tickets novos (ADR-0010).

Pré-requisitos:
  - migration solution/supabase/migrations/20261109000002_rag.sql aplicada;
  - ds2_tickets carregada (scripts/load_raw_datasets.py);
  - SUPABASE_DB_URL no .env (Session pooler).

Idempotente: trunca a tabela, derruba o índice HNSW, copia e recria o índice (mais rápido que indexar linha a linha).
Uso: .venv/bin/python scripts/load_embeddings.py
"""
import time
from pathlib import Path

import numpy as np
import psycopg
from pgvector import HalfVector
from pgvector.psycopg import register_vector

import load_raw_datasets as raw

ROOT = Path(__file__).resolve().parents[1]
DIMS = 512
INDEX_DDL = ("create index if not exists ds2_embeddings_hnsw_idx on public.ds2_embeddings "
             "using hnsw (embedding extensions.halfvec_cosine_ops)")  # igual à migration


def vectors() -> np.ndarray:
    E = np.load(ROOT / "data/embeddings/ds2_te3s_1536.npy").astype(np.float32)[:, :DIMS]
    E /= np.linalg.norm(E, axis=1, keepdims=True)
    return E.astype(np.float16)


if __name__ == "__main__":
    import os
    raw.load_env()
    url = os.environ.get("SUPABASE_DB_URL")
    if not url:
        raise SystemExit("Defina SUPABASE_DB_URL no .env (Supabase → Connect → Session pooler).")
    E = vectors()
    print(f"vetores: {E.shape}, norma média {np.linalg.norm(E.astype(np.float32), axis=1).mean():.4f}")
    with psycopg.connect(url) as conn:
        conn.execute("set search_path = public, extensions")
        register_vector(conn)
        n_tickets = conn.execute("select count(*), min(id), max(id) from public.ds2_tickets").fetchone()
        if n_tickets != (len(E), 0, len(E) - 1):
            raise SystemExit(f"ds2_tickets {n_tickets} não bate com {len(E)} vetores (ids 0..n-1).")
        t0 = time.time()
        with conn.cursor() as cur:
            cur.execute("drop index if exists public.ds2_embeddings_hnsw_idx")
            cur.execute("truncate public.ds2_embeddings")
            with cur.copy("copy public.ds2_embeddings (id, embedding) from stdin with (format binary)") as cp:
                cp.set_types(["int4", "halfvec"])
                for i, v in enumerate(E):
                    cp.write_row((i, HalfVector(v)))
            print(f"COPY: {time.time() - t0:.0f}s")
            t1 = time.time()
            cur.execute("set maintenance_work_mem = '256MB'")
            cur.execute(INDEX_DDL)
            print(f"índice HNSW: {time.time() - t1:.0f}s")
            cur.execute("analyze public.ds2_embeddings")
            cur.execute("select count(*) from public.ds2_embeddings")
            print("ds2_embeddings:", cur.fetchone()[0], "linhas")
        conn.commit()
