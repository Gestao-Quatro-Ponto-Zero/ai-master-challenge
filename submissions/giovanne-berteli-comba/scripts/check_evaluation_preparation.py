#!/usr/bin/env python3
"""Reproduce V00 preparation in a clean directory and check membership integrity."""

import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    manifest = json.loads((ROOT / "data/evaluation-manifest.json").read_text())
    source = json.loads((ROOT / "data/manifest.json").read_text())["datasets"]["it_service"]["file"]["path"]
    copied = ["solution/prepare_evaluation.py", "solution/audit_data.py", "data/manifest.json",
              "data/evaluation-protocol.json", source]
    outputs = ["data/evaluation-manifest.json", "data/processed/evaluation-membership.csv"]
    with tempfile.TemporaryDirectory(prefix="triage-v00-") as folder:
        clean = Path(folder)
        for name in copied:
            (clean / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, clean / name)
        subprocess.run([sys.executable, "-I", str(clean / "solution/prepare_evaluation.py")],
                       cwd=clean, check=True, capture_output=True, text=True)
        identical = {name: digest(ROOT / name) == digest(clean / name) for name in outputs}
        if not all(identical.values()):
            raise AssertionError("Clean preparation differs")
    with (ROOT / outputs[1]).open(newline="") as handle:
        membership = list(csv.DictReader(handle))
    assert [int(row["row_index"]) for row in membership] == list(range(1, manifest["raw_rows"] + 1))
    for field in ("group_id", "normalized_text_sha256"):
        partitions = {}
        for row in membership:
            previous = partitions.setdefault(row[field], row["partition"])
            assert previous == row["partition"], f"Cross-partition {field}"
    assert digest(ROOT / outputs[1]) == manifest["membership"]["sha256"]
    train = {int(row["row_index"]) for row in membership if row["partition"] == "train"}
    markers = ["resolved", "fixed", "solved", "closed", "solution", "resolution"]
    counts = dict.fromkeys(markers, 0)
    with (ROOT / source).open(newline="", encoding="utf-8-sig") as handle:
        for i, row in enumerate(csv.DictReader(handle), 1):
            if i in train:
                words = set(re.findall(r"\w+", row["Document"].casefold()))
                for word in markers:
                    counts[word] += word in words
    inputs = copied + outputs + ["scripts/check_evaluation_preparation.py"]
    return {"clean_reproduction_byte_identical": identical,
            "ordered_rows_assigned_once": True, "whole_groups_and_normalized_duplicates": True,
            "preparation_model_fits": 0,
            "training_text_risk_probe": {"partition": "train", "rows": len(train),
                                         "rows_containing_literal_markers": counts,
                                         "interpretation": "Heuristic inspection only: these words can describe requests or outcomes. Processed Document has no proven entry timestamp; do not claim prospective validity or remove markers as a validated leakage repair."},
            "limits": "Source copied with matching bytes, not downloaded again. Exact declared token similarity only, not semantic/entity independence. No model performance evaluated.",
            "input_sha256": {name: digest(ROOT / name) for name in inputs}}


if __name__ == "__main__":
    result = check()
    path = ROOT / "docs/review-evidence/evaluation-checks.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "input_sha256"}, indent=2))
