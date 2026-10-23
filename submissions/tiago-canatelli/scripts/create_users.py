"""Cria os usuários do painel (admin + uma pessoa por área) com códigos pessoais gerados.

Os códigos ficam só em .users.local.md (no .gitignore); o banco guarda o hash PBKDF2.
Uso: uv run python scripts/create_users.py
"""

import secrets
from pathlib import Path

import psycopg
from api.auth import hash_code

from ravenlake.settings import Settings

USERS = [
    ("admin@ravenstack.demo", "Admin", "admin"),
    ("ceo@ravenstack.demo", "CEO", "executivo"),
    ("financeiro@ravenstack.demo", "Financeiro", "financeiro"),
    ("cs@ravenstack.demo", "Customer Success", "cs"),
    ("suporte@ravenstack.demo", "Suporte", "suporte"),
    ("produto@ravenstack.demo", "Produto", "produto"),
    ("marketing@ravenstack.demo", "Marketing", "marketing"),
    ("vendas@ravenstack.demo", "Vendas", "vendas"),
    ("dados@ravenstack.demo", "Dados", "dados"),
]

out = Path(__file__).resolve().parents[1] / ".users.local.md"
lines = ["# Usuários do painel (NÃO commitar)\n", "| E-mail | Papel | Código |", "|---|---|---|"]
with psycopg.connect(Settings().database_url.get_secret_value(), prepare_threshold=None) as conn:  # type: ignore[call-arg]
    for email, name, role in USERS:
        code = secrets.token_urlsafe(9)
        conn.execute(
            """insert into app.users (email, name, role, code_hash) values (%s, %s, %s, %s)
               on conflict (email) do update set code_hash = excluded.code_hash, role = excluded.role""",
            (email, name, role, hash_code(code)),
        )
        lines.append(f"| {email} | {role} | `{code}` |")
out.write_text("\n".join(lines) + "\n")
print(f"{len(USERS)} usuários criados; códigos em {out.name}")
