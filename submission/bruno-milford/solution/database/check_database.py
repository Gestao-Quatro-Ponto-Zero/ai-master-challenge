from pathlib import Path
import sqlite3

database_path = Path(__file__).resolve().parent / "ravenstack.db"

with sqlite3.connect(database_path) as connection:
    tables = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    ).fetchall()

    print("Tabelas encontradas:")

    for (table_name,) in tables:
        total = connection.execute(
            f'SELECT COUNT(*) FROM "{table_name}"'
        ).fetchone()[0]

        print(f"- {table_name}: {total} registros")
