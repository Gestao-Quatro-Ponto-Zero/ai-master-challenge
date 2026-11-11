"""Monta o banco do case num projeto Supabase novo, do zero (docs/setup.md, "Subir a stack inteira").

Etapas, em ordem (cada script chamado é idempotente):
  1. banco      aplica solution/supabase/setup.sql (as migrations em ordem, num arquivo só)
  2. dados      scripts/load_raw_datasets.py   → ds1_tickets e ds2_tickets (holdout 80/20, seed 42)
  3. embeddings scripts/embed_ds2.py           → data/embeddings/ds2_te3s_1536.npy (OpenAI, ~US$ 0,04; pula se já existe)
                scripts/load_embeddings.py     → ds2_embeddings (halfvec 512 + índice HNSW)
  4. playbook   scripts/seed_playbook.py       → 14 soluções validadas (OpenAI, frações de centavo)
  5. análises   scripts/load_analysis.py       → tabelas analysis_* lidas pelo app
  6. demo       scripts/reset_demo.py          → só com --demo: repovoa a fila pelo fluxo 1 do n8n (já publicado)

Pré-requisitos: .env com SUPABASE_DB_URL (Session pooler) e OPENAI_API_KEY; para --demo, também
N8N_BASE_URL e N8N_WEBHOOK_SECRET. Os dados brutos vêm de scripts/download_data.sh (rodado aqui se faltarem).

Uso (da pasta submissions/daniel-fonseca, com o .venv do requirements.txt):
  .venv/bin/python scripts/setup_supabase.py              # etapas 1 a 5
  .venv/bin/python scripts/setup_supabase.py --sem-sql    # pula a etapa 1 (setup.sql já colado no SQL Editor)
  .venv/bin/python scripts/setup_supabase.py --demo       # etapas 1 a 6
  .venv/bin/python scripts/setup_supabase.py --gerar-sql  # só regenera solution/supabase/setup.sql das migrations
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "solution/supabase/migrations"
SETUP_SQL = ROOT / "solution/supabase/setup.sql"
RAW = ROOT / "data/raw"
EMBEDDINGS = ROOT / "data/embeddings/ds2_te3s_1536.npy"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import load_raw_datasets as raw  # noqa: E402  (reaproveita o leitor do .env)


def build_sql() -> str:
    """Concatena as migrations na ordem do nome (= ordem de aplicação em produção)."""
    files = sorted(MIGRATIONS.glob("*.sql"))
    parts = [
        "-- setup.sql — banco completo do case num projeto Supabase novo.",
        "-- GERADO por scripts/setup_supabase.py --gerar-sql a partir de solution/supabase/migrations/ (não editar à mão).",
        "-- Uso: cole no SQL Editor do Supabase e rode, ou deixe o scripts/setup_supabase.py aplicar.",
        f"-- {len(files)} migrations, na ordem: " + ", ".join(f.stem for f in files),
        "",
    ]
    for f in files:
        parts += [f"-- ===================== {f.name} =====================", f.read_text().rstrip(), ""]
    return "\n".join(parts) + "\n"


def run(step: str, script: str, *args: str) -> None:
    print(f"\n▶ {step}: {script} {' '.join(args)}".rstrip(), flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=ROOT, check=True)


def require(*names: str) -> None:
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        sys.exit(f"Faltam no .env: {', '.join(missing)} (modelo em .env.example; veja docs/setup.md).")


def main() -> None:
    SETUP_SQL.write_text(build_sql())
    if "--gerar-sql" in sys.argv:
        print(f"{SETUP_SQL.relative_to(ROOT)} regenerado.")
        return

    raw.load_env()
    require("SUPABASE_DB_URL", "OPENAI_API_KEY")
    if "--demo" in sys.argv:
        require("N8N_BASE_URL", "N8N_WEBHOOK_SECRET")

    if not RAW.exists() or not any(RAW.iterdir()):
        print("▶ dados brutos ausentes: scripts/download_data.sh", flush=True)
        subprocess.run(["bash", str(ROOT / "scripts/download_data.sh")], cwd=ROOT, check=True)

    if "--sem-sql" not in sys.argv:
        import psycopg

        print(f"\n▶ banco: {SETUP_SQL.relative_to(ROOT)}", flush=True)
        with psycopg.connect(os.environ["SUPABASE_DB_URL"], autocommit=True) as conn:
            conn.execute(SETUP_SQL.read_text())

    run("dados", "load_raw_datasets.py")
    if EMBEDDINGS.exists():
        print(f"\n▶ embeddings: {EMBEDDINGS.relative_to(ROOT)} já existe, sem nova chamada à OpenAI")
    else:
        run("embeddings", "embed_ds2.py")
    run("embeddings", "load_embeddings.py")
    run("playbook", "seed_playbook.py")
    run("análises", "load_analysis.py")
    if "--demo" in sys.argv:
        run("demo", "reset_demo.py")

    print("\n✔ Banco pronto. Próximos passos: importar os fluxos no n8n e subir o app (docs/setup.md).")


if __name__ == "__main__":
    main()
