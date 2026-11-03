#!/usr/bin/env python3
"""One owned-model prediction. No database access; stdin/stdout JSON only."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from triage.artifacts import BUNDLE, ROOT, load_metadata


def predict(text):
    try:
        manifest, policy, reference = load_metadata()
    except (OSError, ValueError, KeyError, TypeError):
        return {"error": "not_ready"}
    # Only locally produced, hash-checked files in the fixed bundle are deserialized.
    import pickle
    directory = ROOT / BUNDLE
    name = manifest["selected_model"] + ".pkl"
    with (directory / name).open("rb") as handle:
        model = pickle.load(handle)
    features = model.named_steps["tfidf"].transform([text])
    scores = model.named_steps["classifier"].predict_proba(features)[0]
    return {"classes": model.classes_.tolist(), "scores": scores.tolist(), "known_features": int(features.nnz),
            "policy": policy, "reference": reference,
            "model_version": manifest["model_version"], "model_sha256": manifest["files"][name],
            "policy_version": policy["id"], "policy_sha256": manifest["files"]["policy.json"],
            "reference_version": reference["id"], "reference_sha256": manifest["files"]["reference.json"]}


if __name__ == "__main__":
    request = json.load(sys.stdin)
    print(json.dumps(predict(request["text"]), allow_nan=False))
