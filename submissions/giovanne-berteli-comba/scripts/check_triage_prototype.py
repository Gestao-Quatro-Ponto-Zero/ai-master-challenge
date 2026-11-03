#!/usr/bin/env python3
"""Exercise the owned model and persistence using TRAIN examples only, in a temp DB."""

import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solution"))
from triage.artifacts import BUNDLE, load_metadata, sha256, write_json
from triage.core import quantile
from triage.repository import Repository
from triage.runtime import TriageService


def check():
    manifest, policy, _ = load_metadata()
    examples = json.loads((ROOT / BUNDLE / "demo-examples.json").read_text())
    cases = [{"text": row["text"], "context": "it_service_en", "case_id": row["case_id"], "source": row["source"]} for row in examples]
    assert all(case["source"]["partition"] == "train" for case in cases)
    cases += [{"text": "support request", "context": "unknown"},
              {"text": "", "context": "it_service_en"},
              {"text": "zzqxvptrnzzzz", "context": "it_service_en"},
              {"text": "x" * 10001, "context": "it_service_en"}]
    latencies, results = [], []
    with tempfile.TemporaryDirectory(prefix="triage-i01-") as folder:
        repo = Repository(Path(folder) / "triage.sqlite3")
        service = TriageService(repo)
        for i, case in enumerate(cases):
            started = time.perf_counter()
            result = service.submit(**case, request_id=f"prototype-{i}")
            latencies.append((time.perf_counter() - started) * 1000)
            assert result["persisted"] and result["outcome"] != "failed", result["reason_codes"]
            results.append(result)
        first = service.submit(**cases[0], request_id="prototype-0")
        assert first == results[0]
        rows = Repository(repo.path).filter_metrics()
        assert len(rows) == 2 * len(cases)
        assert len(repo.list_runs()) == len(cases)
        with repo.connect() as connection:
            connection.execute("CREATE TRIGGER fixture_write_failure BEFORE INSERT ON metrics BEGIN SELECT RAISE(ABORT,'fixture'); END;")
        failed = service.submit("fixture failure", "unknown", request_id="fault-fixture")
        assert not failed["persisted"] and failed["reason_codes"] == ["persistence_error"]
        assert len(repo.list_runs()) == len(cases)
    return {"scope": "Functional smoke with train examples and synthetic invalid/unknown inputs; no final-test prediction, accuracy estimate or human adjudication",
            "model": manifest["selected_model"], "gate_mode": policy["mode"], "final_test_predictions": 0,
            "requests": {"attempted": len(cases) + 1, "unique": len(cases), "duplicate_deliveries": 1,
                         "unique_stored": len(cases), "saved_acknowledgments": len(cases) + 1, "stored_metric_rows": len(rows)},
            "write_failure_fixture": {"attempted": 1, "stored": 0, "visible_reason": failed["reason_codes"]},
            "end_to_end_smoke_latency_ms": {"n": len(latencies), "p50": quantile(latencies, .5), "p95": quantile(latencies, .95), "max": max(latencies),
                                             "population": "7 unique functional submissions including DB commit; tiny smoke only, not production latency or V01 benchmark"},
            "results": [{key: result[key] for key in ("source", "predicted_category", "score", "outcome", "review_queue", "reason_codes", "persisted")} for result in results],
            "input_sha256": {name: sha256(ROOT / name) for name in ["scripts/check_triage_prototype.py", "data/triage-development.json", "data/models/it-triage-v1/bundle.json"]}}


if __name__ == "__main__":
    result = check()
    write_json(ROOT / "docs/review-evidence/triage-smoke.json", result)
    print(json.dumps({key: result[key] for key in ("model", "gate_mode", "requests", "write_failure_fixture", "final_test_predictions")}, indent=2))
