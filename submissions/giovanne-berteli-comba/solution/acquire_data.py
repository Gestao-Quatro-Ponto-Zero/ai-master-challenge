#!/usr/bin/env python3
"""Download the two public Kaggle version-1 archives and verify frozen hashes."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifest.json"
SOURCES = {
    "customer_support": "suraj520/customer-support-ticket-dataset",
    "it_service": "adisongoh/it-service-ticket-classification-dataset",
}
MAX_BYTES = 60 * 1024 * 1024


def sha256(path):
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def download(url, target):
    request = urllib.request.Request(url, headers={"User-Agent": "support-challenge-data-audit/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response, target.open("wb") as output:
        size = 0
        for block in iter(lambda: response.read(1024 * 1024), b""):
            size += len(block)
            if size > MAX_BYTES:
                raise ValueError("Download exceeds 60 MiB limit")
            output.write(block)


def acquire(initialize=False):
    if initialize and MANIFEST.exists():
        raise ValueError("Manifest already exists; do not overwrite the frozen acquisition")
    if not initialize and not MANIFEST.exists():
        raise ValueError("Missing manifest; use --initialize for the first acquisition")
    manifest = {"schema_version": 1, "acquired_at": datetime.now(timezone.utc).isoformat(),
                "method": "Anonymous HTTPS GET; pinned Kaggle datasetVersionNumber=1; ZIP member bytes preserved",
                "datasets": {}} if initialize else json.loads(MANIFEST.read_text())
    if not initialize and (manifest.get("schema_version") != 1 or
                           set(manifest.get("datasets", {})) != set(SOURCES) or
                           any(entry.get("version") != 1 for entry in manifest["datasets"].values())):
        raise ValueError("Manifest must lock both expected datasets at version 1")
    raw = ROOT / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    for key, slug in SOURCES.items():
        url = f"https://www.kaggle.com/api/v1/datasets/download/{slug}?datasetVersionNumber=1"
        locked = manifest["datasets"].get(key)
        archive = raw / f"{key}-v1.zip"
        with tempfile.TemporaryDirectory(dir=raw) as temporary:
            staged = Path(temporary) / "download.zip"
            if archive.exists():
                shutil.copyfile(archive, staged)
            else:
                download(url, staged)
            if locked and sha256(staged) != locked["archive"]["sha256"]:
                raise ValueError(f"{key}: archive hash differs from manifest")
            with zipfile.ZipFile(staged) as package:
                members = [m for m in package.infolist() if not m.is_dir()]
                if len(members) != 1 or not members[0].filename.lower().endswith(".csv"):
                    raise ValueError(f"{key}: expected exactly one CSV ZIP member")
                member = members[0]
                if member.file_size > MAX_BYTES:
                    raise ValueError(f"{key}: expanded member exceeds size limit")
                csv_path = raw / f"{key}-v1.csv"
                staged_csv = Path(temporary) / "data.csv"
                with package.open(member) as source, staged_csv.open("wb") as output:
                    shutil.copyfileobj(source, output)
            if locked and (member.filename != locked["file"]["zip_member"] or
                           sha256(staged_csv) != locked["file"]["sha256"]):
                raise ValueError(f"{key}: CSV member/hash differs from manifest")
            if csv_path.exists() and sha256(csv_path) != sha256(staged_csv):
                raise ValueError(f"{key}: existing raw CSV changed; refusing to overwrite")
            if not archive.exists():
                shutil.copyfile(staged, archive)
            if not csv_path.exists():
                shutil.copyfile(staged_csv, csv_path)
        if initialize:
            metadata_url = f"https://www.kaggle.com/api/v1/datasets/view/{slug}"
            with urllib.request.urlopen(metadata_url, timeout=30) as response:
                metadata = json.load(response)
            if metadata["ref"] != slug or not any(v["versionNumber"] == 1 for v in metadata["versions"]):
                raise ValueError(f"{key}: source/version identity mismatch")
            manifest["datasets"][key] = {
                "source": f"https://www.kaggle.com/datasets/{slug}",
                "metadata_url": metadata_url, "download_url": url,
                "version": 1, "source_last_updated": metadata["lastUpdated"],
                "license_declared_by_publisher": metadata["licenseName"],
                "archive": {"path": archive.relative_to(ROOT).as_posix(),
                            "bytes": archive.stat().st_size, "sha256": sha256(archive)},
                "file": {"path": csv_path.relative_to(ROOT).as_posix(),
                         "zip_member": member.filename, "bytes": csv_path.stat().st_size,
                         "sha256": sha256(csv_path)},
            }
        print(f"{key}: version 1 verified, CSV {csv_path.stat().st_size} bytes, sha256={sha256(csv_path)}")
    if initialize:
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--initialize", action="store_true", help="Create the initial frozen manifest once")
    args = parser.parse_args()
    acquire(args.initialize)
