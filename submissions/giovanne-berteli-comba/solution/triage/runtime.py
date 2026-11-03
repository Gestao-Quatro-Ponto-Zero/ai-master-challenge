"""Coordinator: bounded worker execution, validated decisions and sole DB writer."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from .artifacts import ROOT
from .core import MAX_CHARS, NORMALIZATION, from_scores, no_prediction, normalize
from .repository import RequestConflict, now


def run_worker(text, root=ROOT, timeout=5):
    environment = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    process = subprocess.run([sys.executable, "-I", str(root / "solution/predict_worker.py")],
                             input=json.dumps({"text": text}), capture_output=True, text=True,
                             timeout=timeout, env=environment, cwd=root)
    if process.returncode != 0:
        raise RuntimeError("Inference worker failed")
    return json.loads(process.stdout)


class TriageService:
    def __init__(self, repository, worker=run_worker):
        self.repository, self.worker = repository, worker

    def submit(self, text, context, request_id=None, case_id=None, source=None):
        started = time.perf_counter()
        request_id = request_id or str(uuid.uuid4())
        if not isinstance(request_id, str) or not request_id or len(request_id) > 160:
            raise ValueError("Invalid request ID")
        if case_id is not None and (not isinstance(case_id, str) or not case_id or len(case_id) > 160):
            raise ValueError("Invalid case ID")
        if not isinstance(context, str) or len(context) > 80:
            context = "unknown"
        raw_chars = len(text) if isinstance(text, str) else None
        payload = text if isinstance(text, str) else json.dumps(text, sort_keys=True, default=str)
        text_hash = hashlib.sha256(payload.encode()).hexdigest()
        fingerprint = hashlib.sha256(json.dumps([text_hash, context, source, case_id], sort_keys=True).encode()).hexdigest()
        result = {"schema_version": 1, "case_id": case_id or str(uuid.uuid4()), "request_id": request_id,
                  "run_id": str(uuid.uuid4()), "created_at": now(), "context": context, "source": source,
                  "text_sha256": text_hash, "model_version": None, "model_sha256": None,
                  "policy_version": None, "policy_sha256": None, "reference_version": None,
                  "reference_sha256": None, "normalization": NORMALIZATION,
                  "normalization_sha256": hashlib.sha256(NORMALIZATION.encode()).hexdigest(),
                  "persisted": False, "confirmation_required": True}
        normalized = normalize(text) if isinstance(text, str) and raw_chars <= MAX_CHARS else None
        length = len(normalized) if normalized is not None else None
        original = text if normalized and length <= MAX_CHARS else None
        try:
            previous = self.repository.lookup(request_id, fingerprint)
            if previous:
                return previous
            if not normalized or length > MAX_CHARS:
                decision = no_prediction("invalid_input", length)
            elif context != "it_service_en":
                decision = no_prediction("unsupported_context", length)
            else:
                try:
                    reply = self.worker(normalized)
                    if reply.get("error") == "not_ready":
                        decision = no_prediction("not_ready", length, failed=True)
                    else:
                        decision = from_scores(reply["classes"], reply["scores"], reply["known_features"], length,
                                               reply["policy"], reply["reference"])
                        for key in ("model_version", "model_sha256", "policy_version", "policy_sha256", "reference_version", "reference_sha256"):
                            result[key] = reply[key]
                except subprocess.TimeoutExpired:
                    decision = no_prediction("timeout", length, failed=True)
                except (KeyError, TypeError, ValueError):
                    decision = no_prediction("invalid_model_output", length, failed=True)
                except Exception:
                    decision = no_prediction("inference_error", length, failed=True)
            result.update(decision, elapsed_ms=(time.perf_counter() - started) * 1000)
            return self.repository.save(result, original, raw_chars, length, fingerprint)
        except RequestConflict:
            result.update(no_prediction("request_conflict", length, failed=True))
        except Exception:
            result.update(no_prediction("persistence_error", length, failed=True))
        result["elapsed_ms"] = (time.perf_counter() - started) * 1000
        return result
