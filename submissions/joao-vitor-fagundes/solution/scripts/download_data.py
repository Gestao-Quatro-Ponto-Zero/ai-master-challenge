#!/usr/bin/env python3
"""Download and verify the public CC0 dataset used by Challenge 003."""

from __future__ import annotations

import argparse
import hashlib
import tempfile
import urllib.request
import zipfile
from pathlib import Path


DATASET_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "agungpambudi/crm-sales-predictive-analytics"
)
ARCHIVE_SHA256 = "74d535826330b616758ebb6bb393abf701a5126364a72fbe71003cb6a7a87a9c"
FILE_HASHES = {
    "accounts.csv": "e5242324768a563fc632cddfed49a29acbbf2892b8a3c6453cc9650de9ae0358",
    "metadata.csv": "22b34e498d07e3d7f322afdbf81d70a5dc0a389792944e50ca2af86a3597f0af",
    "products.csv": "7c1c8cbbdb6d4c286902e1985eeb529a36366d6a43f43cd4a93c4b1da2a6eb84",
    "sales_pipeline.csv": "825ce8f6c32d4009548b468df3173d55a46fd73f2531f532c5459371dc52adf2",
    "sales_teams.csv": "aeff1272ebe196f5a27e3fc0578aa27abf48ed9ae461aa344fb95990e5ad8bd1",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_files(output_dir: Path) -> list[str]:
    problems: list[str] = []
    for filename, expected_hash in FILE_HASHES.items():
        path = output_dir / filename
        if not path.exists():
            problems.append(f"missing: {filename}")
        elif sha256(path) != expected_hash:
            problems.append(f"checksum mismatch: {filename}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    current_problems = verify_files(args.output_dir)
    if not current_problems and not args.force:
        print("Dataset already present and verified.")
        return

    with tempfile.TemporaryDirectory(prefix="lead-scorer-data-") as temp_dir:
        archive = Path(temp_dir) / "dataset.zip"
        urllib.request.urlretrieve(DATASET_URL, archive)
        if sha256(archive) != ARCHIVE_SHA256:
            raise RuntimeError("Downloaded archive checksum does not match the audited source.")

        with zipfile.ZipFile(archive) as zipped:
            names = set(zipped.namelist())
            missing = set(FILE_HASHES) - names
            if missing:
                raise RuntimeError(f"Archive is missing expected files: {sorted(missing)}")
            for filename in FILE_HASHES:
                zipped.extract(filename, args.output_dir)

    final_problems = verify_files(args.output_dir)
    if final_problems:
        raise RuntimeError("Dataset verification failed: " + "; ".join(final_problems))
    print("Dataset downloaded and verified successfully.")


if __name__ == "__main__":
    main()
