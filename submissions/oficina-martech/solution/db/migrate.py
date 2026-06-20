"""Runner de migrations — aplica os .sql de migrations/ em ordem, uma única vez cada.

Uso:  python -m db.migrate            (cria/atualiza foco.db)
      python -m db.migrate --reset    (recria do zero)

Portável: SQLite puro (stdlib), sem dependências. Idempotente — rodar 2x não duplica.
"""
import sqlite3, sys
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "foco.db"
MIGRATIONS = DB_DIR / "migrations"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def applied_set(conn):
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " version TEXT PRIMARY KEY, applied_at TEXT DEFAULT (datetime('now')));"
    )
    return {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}


def migrate(reset=False):
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[reset] {DB_PATH.name} removido")

    conn = connect()
    done = applied_set(conn)
    files = sorted(MIGRATIONS.glob("*.sql"))
    if not files:
        print("Nenhuma migration encontrada."); return

    n = 0
    for f in files:
        version = f.stem  # ex: 0001_init
        if version in done:
            print(f"  · {version} (já aplicada)")
            continue
        sql = f.read_text(encoding="utf-8")
        try:
            conn.executescript("BEGIN;\n" + sql + "\nCOMMIT;")
            conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", (version,))
            conn.commit()
            print(f"  ✓ {version} aplicada")
            n += 1
        except Exception as e:
            conn.rollback()
            print(f"  ✗ {version} FALHOU: {e}")
            sys.exit(1)
    conn.close()
    print(f"Migrations OK ({n} nova(s)). Banco: {DB_PATH}")


if __name__ == "__main__":
    migrate(reset="--reset" in sys.argv)
