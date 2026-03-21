from __future__ import annotations

import csv
import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CONTRACT_PATH = ROOT / "contracts" / "repository-data-contract.json"


def _load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _read_rows(dataset: str) -> list[dict[str, str]]:
    path = DATA_DIR / dataset
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def main() -> None:
    if not CONTRACT_PATH.exists():
        raise SystemExit(f"Missing contract file: {CONTRACT_PATH}")

    contract = _load_contract()
    datasets = contract.get("datasets", {})
    errors: list[str] = []
    cached_rows: dict[str, list[dict[str, str]]] = {}

    for dataset_name, spec in datasets.items():
        dataset_path = DATA_DIR / dataset_name
        if not dataset_path.exists():
            errors.append(f"Dataset not found: data/{dataset_name}")
            continue

        rows = _read_rows(dataset_name)
        cached_rows[dataset_name] = rows
        headers = set(rows[0].keys()) if rows else set()
        required_columns = spec.get("required_columns", [])

        for col in required_columns:
            if col not in headers:
                errors.append(f"{dataset_name}: missing required column '{col}'")

        primary_key = spec.get("primary_key")
        if primary_key and rows:
            values = [row.get(primary_key, "").strip() for row in rows]
            if any(not v for v in values):
                errors.append(f"{dataset_name}: empty values in primary key '{primary_key}'")
            if len(set(values)) != len(values):
                errors.append(f"{dataset_name}: duplicated values in primary key '{primary_key}'")

    for dataset_name, spec in datasets.items():
        rows = cached_rows.get(dataset_name, [])
        for fk_col, fk_spec in spec.get("foreign_keys", {}).items():
            ref_dataset = fk_spec["dataset"]
            ref_col = fk_spec["column"]
            aliases = (
                contract.get("normalization_aliases", {}).get(dataset_name, {}).get(fk_col, {})
            )
            ref_rows = cached_rows.get(ref_dataset, [])
            ref_values = {row.get(ref_col, "").strip() for row in ref_rows if row.get(ref_col)}
            for idx, row in enumerate(rows, start=2):
                value = row.get(fk_col, "").strip()
                normalized = aliases.get(value, value)
                if value and normalized not in ref_values:
                    errors.append(
                        (
                            f"{dataset_name}:{idx}: foreign key "
                            f"'{fk_col}'='{value}' not found in {ref_dataset}.{ref_col}"
                        )
                    )

    for rule in contract.get("quality_rules", {}).get("required_not_empty", []):
        dataset_name = rule["dataset"]
        col = rule["column"]
        rows = cached_rows.get(dataset_name, [])
        for idx, row in enumerate(rows, start=2):
            if not row.get(col, "").strip():
                errors.append(f"{dataset_name}:{idx}: required column '{col}' is empty")

    if errors:
        print("Data contract validation failed:")
        for err in errors:
            print(f"- {err}")
        raise SystemExit(1)

    print("Data contract validation passed.")


if __name__ == "__main__":
    main()
