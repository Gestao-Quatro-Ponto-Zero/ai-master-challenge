"""Carrega o playbook-semente (solution/supabase/seed/playbook.json) em validated_resolutions (source = 'playbook').

Cada problem_text recebe embedding text-embedding-3-small com dimensions=512 (mesmo espaço do DS2 e do n8n).
Idempotente: apaga as linhas source='playbook' que não são referenciadas por triage_runs e reinsere.
Custo: ~300 tokens de embedding (frações de centavo).

Pré-requisitos: migration 20261110000003_ops.sql; OPENAI_API_KEY e SUPABASE_DB_URL no .env.
Uso: .venv/bin/python scripts/seed_playbook.py
"""
import json
import os
import urllib.request
from pathlib import Path

import psycopg

import load_raw_datasets as raw

ROOT = Path(__file__).resolve().parents[1]


def embed(texts: list[str], key: str) -> list[list[float]]:
    body = json.dumps({"model": "text-embedding-3-small", "input": texts, "dimensions": 512}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/embeddings", data=body,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    print("tokens:", data["usage"]["total_tokens"])
    return [d["embedding"] for d in sorted(data["data"], key=lambda d: d["index"])]


if __name__ == "__main__":
    raw.load_env()
    entries = json.loads((ROOT / "solution/supabase/seed/playbook.json").read_text())["entries"]
    vecs = embed([e["problem_text"] for e in entries], os.environ["OPENAI_API_KEY"])
    with psycopg.connect(os.environ["SUPABASE_DB_URL"]) as conn:
        conn.execute("""delete from public.validated_resolutions r where r.source = 'playbook'
                        and not exists (select 1 from public.triage_runs t where t.resolution_id = r.id)""")
        for e, v in zip(entries, vecs):
            conn.execute(
                """insert into public.validated_resolutions (category, problem_text, resolution_text, embedding, source)
                   select %s, %s, %s, %s::extensions.halfvec, 'playbook'
                   where not exists (select 1 from public.validated_resolutions
                                     where source = 'playbook' and problem_text = %s)""",
                (e["category"], e["problem_text"], e["resolution_text"], json.dumps(v), e["problem_text"]))
        n = conn.execute("select category, count(*) from public.validated_resolutions where source='playbook' group by 1 order by 1").fetchall()
        conn.commit()
    print(n)
