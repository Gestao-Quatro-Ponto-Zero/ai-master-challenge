"""Gera docs/dicionario-de-dados.md a partir do catálogo do lake (ops.catalog_*).

O catálogo é montado pelos COMMENT ON das migrations; este script só o publica no repositório.
Uso: uv run python scripts/gen_data_dictionary.py
"""

from pathlib import Path

import psycopg

from ravenlake.settings import Settings

LAYERS = [
    ("bronze", "Bronze — cópia fiel dos CSVs"),
    ("silver", "Silver — dados tipados e validados"),
    ("gold", "Gold — fatos, dimensões, KPIs e score de risco"),
    ("ops", "Ops — operação do lake (ingestão, qualidade, catálogo)"),
    ("app", "App — prompts, perfis, usuários e auditoria da IA"),
]

out = Path(__file__).resolve().parents[1] / "docs" / "dicionario-de-dados.md"
with psycopg.connect(Settings().database_url.get_secret_value(), prepare_threshold=None) as conn:  # type: ignore[call-arg]
    conn.execute("select ops.refresh_catalog()")
    tables = conn.execute(
        "select schema_name, table_name, description, row_count, column_count from ops.catalog_tables order by 1, 2"
    ).fetchall()
    cols = conn.execute(
        """select schema_name, table_name, column_name, data_type, is_key, null_pct, distinct_count, description
             from ops.catalog_columns order by schema_name, table_name, ordinal"""
    ).fetchall()
    as_of = conn.execute("select gold.as_of_date()").fetchone()

lines = [
    "# Dicionário de dados",
    "",
    f"Gerado por `scripts/gen_data_dictionary.py` a partir de `ops.catalog_tables` / `ops.catalog_columns` "
    f"(descrições = `COMMENT ON` das migrations). Dados até {as_of[0] if as_of else '—'}. "
    "Modelo e decisões: [`modelo-de-dados.md`](modelo-de-dados.md).",
    "",
    "## Índice",
    "",
]
for schema, title in LAYERS:
    names = [t for t in tables if t[0] == schema]
    lines.append(
        f"- **{title}:** "
        + ", ".join(f"[`{schema}.{t[1]}`](#{schema}{t[1].replace('_', '')})" for t in names)
    )
for schema, title in LAYERS:
    lines += ["", f"## {title}"]
    for s, t, desc, n, ncols in [x for x in tables if x[0] == schema]:
        lines += [
            "",
            f'<a id="{s}{t.replace("_", "")}"></a>',
            f"### `{s}.{t}`",
            "",
            f"{desc or '—'}  ",
            f"*{n:,} linhas · {ncols} colunas*".replace(",", "."),
            "",
        ]
        lines += [
            "| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |",
            "|---|---|---|---|---|---|",
        ]
        for cs, ct, name, dtype, key, nulls, distinct, cdesc in cols:
            if (cs, ct) != (s, t):
                continue
            lines.append(
                f"| `{name}` | {dtype} | {'🔑' if key else ''} | {'' if nulls is None else nulls} | "
                f"{'' if distinct is None else distinct} | {(cdesc or '').replace('|', '/')} |"
            )
out.write_text("\n".join(lines) + "\n")
print(f"{len(tables)} tabelas/views, {len(cols)} colunas → {out}")
