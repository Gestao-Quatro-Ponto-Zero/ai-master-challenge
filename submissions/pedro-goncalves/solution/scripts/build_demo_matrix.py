from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts/demo/case_test_matrix.csv"
sys.path.insert(0, str(ROOT))

from src.support_copilot.demo_matrix import matrix_frame


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame = matrix_frame()
    frame.to_csv(OUTPUT, index=False)
    print(
        {
            "rows": len(frame),
            "output": str(OUTPUT.relative_to(ROOT)),
        }
    )


if __name__ == "__main__":
    main()
