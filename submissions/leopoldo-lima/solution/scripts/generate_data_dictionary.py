from __future__ import annotations

import csv
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
SUBMISSION_ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data"
OUT_MD = SUBMISSION_ROOT / "docs" / "DATA_DICTIONARY.md"
OUT_JSON = ROOT / "artifacts" / "data-validation" / "metadata-coverage-report.json"


def _read_metadata() -> list[dict[str, str]]:
    with (DATA_DIR / "metadata.csv").open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _build_coverage(
    metadata_rows: list[dict[str, str]], schema_by_file: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    metadata_by_table: dict[str, dict[str, str]] = {}
    for row in metadata_rows:
        table = (row.get("Table") or "").strip()
        field = (row.get("Field") or "").strip()
        desc = (row.get("Description") or "").strip()
        if not table or not field:
            continue
        metadata_by_table.setdefault(table, {})[field] = desc

    tables: dict[str, Any] = {}
    for file_name, info in schema_by_file.items():
        table_name = file_name.replace(".csv", "")
        schema_columns = set(info["columns"].keys())
        metadata_columns = set(metadata_by_table.get(table_name, {}).keys())

        tables[table_name] = {
            "file": file_name,
            "schema_columns": sorted(schema_columns),
            "metadata_columns": sorted(metadata_columns),
            "missing_in_metadata": sorted(schema_columns - metadata_columns),
            "extra_in_metadata": sorted(metadata_columns - schema_columns),
        }

    return {"tables": tables}


def _as_markdown(
    metadata_rows: list[dict[str, str]],
    schema_by_file: dict[str, dict[str, Any]],
    coverage: dict[str, Any],
) -> str:
    metadata_lookup: dict[tuple[str, str], str] = {}
    for row in metadata_rows:
        table = (row.get("Table") or "").strip()
        field = (row.get("Field") or "").strip()
        desc = (row.get("Description") or "").strip()
        metadata_lookup[(table, field)] = desc

    lines = ["# Data dictionary", ""]
    lines.append(
        "Gerado automaticamente de `metadata.csv` + schema real dos CSVs. "
        "Divergências ficam explícitas na seção de cobertura."
    )
    lines.append("")

    for file_name, info in schema_by_file.items():
        table_name = file_name.replace(".csv", "")
        lines.append(f"## {table_name}")
        lines.append("")
        lines.append("| Campo | Descrição (metadata) | Tipo inferido | Nulável |")
        lines.append("|---|---|---|---|")
        for field, meta in info["columns"].items():
            desc = metadata_lookup.get((table_name, field), "MISSING_IN_METADATA")
            lines.append(f"| {field} | {desc} | {meta['inferred_type']} | {meta['nullable']} |")
        lines.append("")

    lines.append("## Cobertura metadata vs schema")
    lines.append("")
    for table_name, info in coverage["tables"].items():
        lines.append(f"### {table_name}")
        lines.append(f"- missing_in_metadata: {info['missing_in_metadata']}")
        lines.append(f"- extra_in_metadata: {info['extra_in_metadata']}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def main() -> None:
    from src.raw.reader import OFFICIAL_RAW_FILES, inspect_raw_file

    schema_by_file = {name: inspect_raw_file(name) for name in OFFICIAL_RAW_FILES}
    metadata_rows = _read_metadata()
    coverage = _build_coverage(metadata_rows, schema_by_file)

    OUT_MD.write_text(_as_markdown(metadata_rows, schema_by_file, coverage), encoding="utf-8")
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(coverage, ensure_ascii=True, indent=2), encoding="utf-8")

    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
