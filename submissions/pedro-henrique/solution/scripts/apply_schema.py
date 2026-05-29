"""
Aplica o schema do Supabase via Management API.

Requer um Personal Access Token (PAT) do Supabase:
  Dashboard → Account → Access Tokens → Generate new token
  Exporte como: SUPABASE_PAT=sbp_xxxxx

Uso:
  export SUPABASE_PAT=sbp_xxxxx
  python scripts/apply_schema.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

PROJECT_REF = "hrssqkpptrrzgabxxlek"
SCHEMA_FILE = Path(__file__).parent.parent / "supabase" / "schema.sql"

MGMT_URL = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"


def apply_via_management_api(pat: str, sql: str) -> bool:
    resp = requests.post(
        MGMT_URL,
        headers={"Authorization": f"Bearer {pat}", "Content-Type": "application/json"},
        json={"query": sql},
        timeout=30,
    )
    if resp.status_code in (200, 201):
        print("[schema] Aplicado com sucesso via Management API.")
        return True
    print(f"[schema] Falha na API ({resp.status_code}): {resp.text[:300]}")
    return False


def print_manual_instructions(sql: str) -> None:
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  Aplique o schema manualmente no Supabase SQL Editor                    ║
║  1. Acesse: https://supabase.com/dashboard/project/hrssqkpptrrzgabxxlek ║
║  2. Clique em "SQL Editor" no menu lateral                              ║
║  3. Cole e execute o SQL abaixo                                         ║
╚══════════════════════════════════════════════════════════════════════════╝
""")
    print(sql)


def main() -> None:
    if not SCHEMA_FILE.exists():
        sys.exit(f"[schema] Arquivo não encontrado: {SCHEMA_FILE}")

    sql = SCHEMA_FILE.read_text()
    pat = os.getenv("SUPABASE_PAT", "").strip()

    if pat:
        ok = apply_via_management_api(pat, sql)
        if ok:
            return

    print("[schema] SUPABASE_PAT não definido ou API falhou.")
    print_manual_instructions(sql)


if __name__ == "__main__":
    main()
