"""Aplica um arquivo SQL no Supabase (G4-Analysys) usando DATABASE_URL do .env.

Migrations (supabase/migrations/<versão>_<nome>.sql) são registradas em
supabase_migrations.schema_migrations, como faz `supabase db push`.

Uso: uv run python scripts/apply_sql.py supabase/migrations/20261023150000_api_and_app.sql
"""

import sys
from pathlib import Path

import psycopg

from ravenlake.settings import Settings

path = Path(sys.argv[1])
sql_text = path.read_text()
url = Settings().database_url.get_secret_value()  # type: ignore[call-arg]
with psycopg.connect(url, prepare_threshold=None) as conn:
    conn.execute(sql_text)  # type: ignore[arg-type]
    if path.parent.name == "migrations":
        version, name = path.stem.split("_", 1)
        conn.execute(
            """insert into supabase_migrations.schema_migrations (version, name, statements)
               values (%s, %s, %s) on conflict (version) do nothing""",
            (version, name, [sql_text]),
        )
print(f"aplicado: {path}")
