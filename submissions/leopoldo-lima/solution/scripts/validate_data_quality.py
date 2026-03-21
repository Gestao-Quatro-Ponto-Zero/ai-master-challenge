from __future__ import annotations

import csv
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    from src.raw.data_quality import summarize_validation, validate_sales_pipeline_rows

    pipeline_path = ROOT / "data" / "sales_pipeline.csv"
    with pipeline_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    result: dict[str, Any] = summarize_validation(validate_sales_pipeline_rows(rows))
    if not result["passed"]:
        print("Data quality validation failed:")
        for err in result["errors"]:
            print(f"- {err}")
        raise SystemExit(1)

    print("Data quality validation passed.")


if __name__ == "__main__":
    main()
