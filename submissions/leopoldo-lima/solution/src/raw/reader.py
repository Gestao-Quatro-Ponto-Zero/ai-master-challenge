from __future__ import annotations

import csv
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
OFFICIAL_RAW_FILES = [
    "accounts.csv",
    "products.csv",
    "sales_teams.csv",
    "sales_pipeline.csv",
    "metadata.csv",
]


def load_raw_rows(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def inspect_raw_file(filename: str) -> dict[str, Any]:
    rows = load_raw_rows(filename)
    columns: dict[str, dict[str, Any]] = {}
    for col in rows[0].keys() if rows else []:
        values = [str(row.get(col, "")).strip() for row in rows]
        non_empty = [v for v in values if v]
        null_count = len(values) - len(non_empty)
        unique_count = len(set(non_empty))

        inferred_type = "string"
        if non_empty:
            numeric = True
            integer_only = True
            for v in non_empty:
                try:
                    n = float(v)
                    if not n.is_integer():
                        integer_only = False
                except ValueError:
                    numeric = False
                    break
            if numeric:
                inferred_type = "int" if integer_only else "float"

        columns[col] = {
            "inferred_type": inferred_type,
            "nullable": null_count > 0,
            "null_count": null_count,
            "cardinality_approx": unique_count,
            "sample": non_empty[:3],
        }

    return {
        "file": filename,
        "source_of_truth": True,
        "rows": len(rows),
        "columns": columns,
        "notes": "Nao renomear colunas na ingestao raw.",
    }
