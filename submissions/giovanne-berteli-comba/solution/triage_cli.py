#!/usr/bin/env python3
"""Run one local assisted analysis and persist it; no external actions."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from triage.artifacts import BUNDLE, ROOT, load_metadata
from triage.repository import Repository
from triage.runtime import TriageService


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text")
    group.add_argument("--example", type=int, choices=range(3))
    parser.add_argument("--context", choices=["it_service_en", "customer_support", "unknown"], default="unknown")
    parser.add_argument("--request-id")
    args = parser.parse_args()
    source, case_id = None, None
    text = args.text if args.text is not None else sys.stdin.read() if args.example is None else None
    if args.example is not None:
        load_metadata()
        row = json.loads((ROOT / BUNDLE / "demo-examples.json").read_text())[args.example]
        text, source, case_id, args.context = row["text"], row["source"], row["case_id"], "it_service_en"
    repository = Repository(ROOT / "data/runtime/triage.sqlite3")
    result = TriageService(repository).submit(text, args.context, args.request_id, case_id, source)
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    sys.exit(0 if result["persisted"] and result["outcome"] != "failed" else 1)
