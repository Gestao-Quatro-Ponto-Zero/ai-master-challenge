"""Carrega os resultados da análise no Supabase para o app ler (PRD v1.1, J2 = dados do Supabase).

- analysis_diagnostic_cuts ← solution/analysis/output/diagnostic_cuts.csv
- analysis_metrics        ← cada solution/analysis/output/*.json (chave = nome do arquivo) + cost_premises.json
- analysis_examples       ← tickets reais do holdout do DS2 para "o que não automatizar": HR Support e
                            Administrative rights, texto legível (12–45 palavras), que o RAG classifica certo
                            e manda para "Somente humano"

O cálculo estatístico continua nos scripts Python (fonte de verdade); este script só publica os resultados.
Idempotente: substitui o conteúdo das três tabelas.

Pré-requisitos: migration 20261110000005_app.sql; SUPABASE_DB_URL no .env.
Uso: .venv/bin/python scripts/load_analysis.py
"""
import json
import os
from pathlib import Path

import pandas as pd
import psycopg

import load_raw_datasets as raw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "solution/analysis/output"
EXAMPLES = {"HR Support": ("sensitive_hr", 3), "Administrative rights": ("sensitive_admin", 2)}

if __name__ == "__main__":
    raw.load_env()
    cuts = pd.read_csv(OUT / "diagnostic_cuts.csv")
    metrics = {p.stem: (json.loads(p.read_text()), f"solution/analysis/output/{p.name}") for p in sorted(OUT.glob("*.json"))}
    metrics["cost_premises"] = (json.loads((ROOT / "solution/analysis/cost_premises.json").read_text()),
                                "solution/analysis/cost_premises.json")
    with psycopg.connect(os.environ["SUPABASE_DB_URL"]) as conn, conn.cursor() as cur:
        cur.execute("truncate public.analysis_diagnostic_cuts")
        cols = list(cuts.columns)
        with cur.copy(f"copy public.analysis_diagnostic_cuts ({', '.join(cols)}) from stdin") as cp:
            for row in cuts.astype(object).where(cuts.notna(), None).itertuples(index=False, name=None):
                cp.write_row(row)
        cur.execute("delete from public.analysis_metrics")
        for key, (payload, src) in metrics.items():
            cur.execute("insert into public.analysis_metrics (key, payload, source_file) values (%s, %s::jsonb, %s)",
                        (key, json.dumps(payload, ensure_ascii=False), src))
        cur.execute("delete from public.analysis_examples")
        for category, (kind, k) in EXAMPLES.items():
            cur.execute(
                """insert into public.analysis_examples (ds2_id, kind, note)
                   select t.id, %s, 'Categoria sensível: ' || c.category || ' (confiança ' || round(c.confidence::numeric, 2) || ')'
                   from (select id, document from public.ds2_tickets
                         where split = 'test' and topic_group = %s
                           and array_length(regexp_split_to_array(document, '\\s+'), 1) between 12 and 45
                         order by id limit 60) t
                   join public.ds2_embeddings e on e.id = t.id
                   cross join lateral public.classify_ticket(e.embedding) c
                   where c.category = %s
                   order by c.confidence desc, t.id
                   limit %s""", (kind, category, category, k))
        conn.commit()
        for table in ("analysis_diagnostic_cuts", "analysis_metrics", "analysis_examples"):
            cur.execute(f"select count(*) from public.{table}")
            print(table, cur.fetchone()[0])
