from __future__ import annotations

import argparse
from pathlib import Path

from .engine import write_outputs


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Reconstruct RavenStack's daily account-plan portfolio from source CSVs.")
    parser.add_argument("--data-dir", type=Path, default=root / "data" / "raw")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "outputs")
    args = parser.parse_args()
    result = write_outputs(args.data_dir, args.output_dir)
    print(f"status={result['metadata']['status']} grain={result['metadata']['grain']} window={result['metadata']['observation_start']}..{result['metadata']['observation_end']}")
    print(result["summary"])


if __name__ == "__main__":
    main()
