from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    from src.integrity.referential import evaluate_referential_integrity

    report = evaluate_referential_integrity()
    out_dir = ROOT / "artifacts" / "data-validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "referential-integrity-report.json"
    out_file.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")

    blocking = [r for r in report["relations"] if r["classification"] == "blocking"]
    if blocking:
        print("Referential integrity failed with blocking issues:")
        for row in blocking:
            print(f"- {row['relation']}: {row['matched_rows']}/{row['total_rows_with_value']}")
        raise SystemExit(1)

    print(f"Referential integrity validation passed. Report: {out_file}")


if __name__ == "__main__":
    main()
