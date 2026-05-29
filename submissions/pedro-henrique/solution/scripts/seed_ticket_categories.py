"""
Gera embeddings do Dataset 2 e popula a tabela ticket_categories no Supabase.

Estratégia:
- Amostra estratificada: até SAMPLE_PER_CATEGORY tickets por categoria
- Embeddings em lotes de BATCH_SIZE via text-embedding-3-small
- Suporta retomada: pula registros já inseridos (source_ticket_id único)

Uso:
  cd submissions/pedro-henrique-silva/solution
  source .venv312/bin/activate
  python scripts/seed_ticket_categories.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
from openai import OpenAI
from supabase import create_client

# ── Config ────────────────────────────────────────────────────────────────────
DATASET_PATH = Path.home() / ".cache/kagglehub/datasets/adisongoh/it-service-ticket-classification-dataset/versions/1/all_tickets_processed_improved_v3.csv"
SAMPLE_PER_CATEGORY = 400   # ~3.2k total (8 categories)
BATCH_SIZE          = 100   # embeddings per API call
TABLE               = "ticket_categories"
EMBED_MODEL         = "text-embedding-3-small"


def load_sample(path: Path, n_per_cat: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.dropna(subset=["Document", "Topic_group"])
    df["Document"] = df["Document"].astype(str).str.strip()
    df = df[df["Document"].str.len() > 10].copy()

    parts = []
    for cat, group in df.groupby("Topic_group"):
        parts.append(group.sample(min(len(group), n_per_cat), random_state=42))
    sampled = pd.concat(parts, ignore_index=True)
    sampled["source_ticket_id"] = "ds2-" + sampled.index.astype(str)
    return sampled


def embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in resp.data]


def main() -> None:
    url       = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    svc_key   = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    missing = [k for k, v in {"NEXT_PUBLIC_SUPABASE_URL": url,
                               "SUPABASE_SERVICE_ROLE_KEY": svc_key,
                               "OPENAI_API_KEY": openai_key}.items() if not v]
    if missing:
        sys.exit(f"[seed] Variáveis ausentes: {', '.join(missing)}")

    if not DATASET_PATH.exists():
        sys.exit(f"[seed] Dataset não encontrado: {DATASET_PATH}\n       Execute: python scripts/download_datasets.py")

    supabase = create_client(url, svc_key)          # type: ignore[arg-type]
    openai   = OpenAI(api_key=openai_key)

    # ── Check existing records to allow resume ────────────────────────────────
    existing_res = supabase.table(TABLE).select("source_ticket_id").execute()
    existing_ids: set[str] = {r["source_ticket_id"] for r in (existing_res.data or [])}
    print(f"[seed] Registros já existentes: {len(existing_ids)}")

    # ── Load sample ───────────────────────────────────────────────────────────
    df = load_sample(DATASET_PATH, SAMPLE_PER_CATEGORY)
    df = df[~df["source_ticket_id"].isin(existing_ids)]
    print(f"[seed] Novos registros a processar: {len(df)}")

    if df.empty:
        print("[seed] Nada a fazer — tabela já populada.")
        return

    # ── Embed in batches ──────────────────────────────────────────────────────
    rows: list[dict[str, Any]] = []
    total = len(df)
    inserted = 0

    for start in range(0, total, BATCH_SIZE):
        batch = df.iloc[start : start + BATCH_SIZE]
        texts = batch["Document"].tolist()

        try:
            embeddings = embed_batch(openai, texts)
        except Exception as exc:
            print(f"  [warn] Erro ao embedar lote {start}-{start+len(batch)}: {exc} — tentando novamente…")
            time.sleep(5)
            embeddings = embed_batch(openai, texts)

        for (_, row), emb in zip(batch.iterrows(), embeddings):
            rows.append({
                "source_ticket_id": row["source_ticket_id"],
                "description":      str(row["Document"])[:1000],
                "category":         row["Topic_group"],
                "embedding":        emb,
            })

        # Flush every BATCH_SIZE rows
        try:
            supabase.table(TABLE).upsert(rows, on_conflict="source_ticket_id").execute()
            inserted += len(rows)
            rows = []
            pct = min(100, round((start + BATCH_SIZE) / total * 100))
            print(f"  [{pct:3d}%] {inserted}/{total} inseridos")
        except Exception as exc:
            print(f"  [warn] Falha ao inserir lote: {exc}")

        time.sleep(0.25)   # avoid rate-limit on embeddings API

    # Flush remaining
    if rows:
        supabase.table(TABLE).upsert(rows, on_conflict="source_ticket_id").execute()
        inserted += len(rows)

    print(f"\n[seed] Concluído — {inserted} registros inseridos em '{TABLE}'.")
    print("[seed] Distribuição por categoria:")
    for cat, cnt in df["Topic_group"].value_counts().items():
        print(f"  {cat}: {cnt}")


if __name__ == "__main__":
    main()
