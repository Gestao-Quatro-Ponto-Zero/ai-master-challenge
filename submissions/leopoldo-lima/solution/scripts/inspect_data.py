from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / "artifacts" / "data-validation"
JSON_PATH = OUT_DIR / "raw-schema-summary.json"
MD_PATH = OUT_DIR / "raw-schema-summary.md"


def _as_markdown(summary: dict[str, dict[str, Any]]) -> str:
    lines = ["# Raw schema summary", ""]
    for filename, info in summary.items():
        lines.append(f"## {filename}")
        lines.append(f"- source_of_truth: {info['source_of_truth']}")
        lines.append(f"- rows: {info['rows']}")
        lines.append("- notes: Nao renomear colunas na ingestao raw.")
        lines.append("")
        lines.append("| coluna | tipo inferido | nulavel | nulos | cardinalidade aprox | sample |")
        lines.append("|---|---|---|---:|---:|---|")
        for col, meta in info["columns"].items():
            sample = ", ".join(meta["sample"]) if meta["sample"] else "-"
            lines.append(
                f"| {col} | {meta['inferred_type']} | {meta['nullable']} | "
                f"{meta['null_count']} | {meta['cardinality_approx']} | {sample} |"
            )
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    from src.raw.reader import OFFICIAL_RAW_FILES, inspect_raw_file

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {name: inspect_raw_file(name) for name in OFFICIAL_RAW_FILES}
    JSON_PATH.write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    MD_PATH.write_text(_as_markdown(summary), encoding="utf-8")
    print(f"Wrote {JSON_PATH}")
    print(f"Wrote {MD_PATH}")


if __name__ == "__main__":
    main()
