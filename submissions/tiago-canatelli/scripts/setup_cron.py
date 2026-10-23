"""Grava o CRON_TOKEN do .env no Supabase Vault (segredo 'ravenstack_cron_token').

Uso (depois da migration cloud_ingest_schedule): uv run python scripts/setup_cron.py
"""

import sys
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).parent))
from render_deploy import read_env  # noqa: E402

env = read_env()
with psycopg.connect(env["DATABASE_URL"], prepare_threshold=None) as conn:
    row = conn.execute("select id from vault.secrets where name = 'ravenstack_cron_token'").fetchone()
    if row:
        conn.execute("select vault.update_secret(%s, %s)", (row[0], env["CRON_TOKEN"]))
    else:
        conn.execute("select vault.create_secret(%s, 'ravenstack_cron_token')", (env["CRON_TOKEN"],))
print("token do agendador gravado no Vault")
