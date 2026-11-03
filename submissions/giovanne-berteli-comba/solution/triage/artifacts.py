"""Validate owned local artifacts before loading any serialized model."""

import hashlib
from importlib import metadata
import json
import math
from pathlib import Path
import re

from .core import CLASSES, NORMALIZATION

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = Path("data/models/it-triage-v1")
BOUND_INPUTS = ("data/evaluation-protocol.json", "data/evaluation-manifest.json", "requirements.lock",
                "solution/triage/core.py", "solution/triage/artifacts.py", "solution/triage/runtime.py",
                "solution/triage/repository.py", "solution/train_triage.py", "solution/predict_worker.py")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")


def check_environment(root):
    canonical = lambda name: re.sub(r"[-_.]+", "-", name).lower()
    expected = {}
    for line in (root / "requirements.lock").read_text().splitlines():
        if line and not line.startswith("#"):
            name, version = line.split("==")
            expected[canonical(name)] = version
    actual = {canonical(dist.metadata["Name"]): dist.version for dist in metadata.distributions()}
    if expected != actual:
        raise ValueError("Environment differs from lock")


def load_metadata(root=ROOT, environment=True):
    directory = root / BUNDLE
    manifest = json.loads((directory / "bundle.json").read_text())
    if manifest.get("schema_version") != 1 or manifest.get("protocol_id") != "it-triage-v1":
        raise ValueError("Invalid bundle version")
    if set(manifest["input_sha256"]) != set(BOUND_INPUTS):
        raise ValueError("Incomplete bundle dependencies")
    for name, expected in manifest["input_sha256"].items():
        if sha256(root / name) != expected:
            raise ValueError("Stale bundle input")
    allowed = {"majority.pkl", "multinomial_nb.pkl", "logistic_c05.pkl", "logistic_c20.pkl",
               "policy.json", "reference.json", "demo-examples.json"}
    if set(manifest["files"]) != allowed:
        raise ValueError("Unexpected owned artifact paths")
    for name, expected in manifest["files"].items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory.resolve()) or sha256(path) != expected:
            raise ValueError("Invalid artifact path/hash")
    if environment:
        check_environment(root)
    if manifest["selected_model"] is None:
        raise ValueError("No quality-qualified model")
    if manifest["selected_model"] not in {"logistic_c05", "logistic_c20"} or manifest["classes"] != list(CLASSES):
        raise ValueError("Invalid selected model/classes")
    policy = json.loads((directory / "policy.json").read_text())
    reference = json.loads((directory / "reference.json").read_text())
    protocol = json.loads((root / "data/evaluation-protocol.json").read_text())
    split = json.loads((root / "data/evaluation-manifest.json").read_text())
    if (manifest["model_version"] != manifest["files"][manifest["selected_model"] + ".pkl"] or
            manifest["membership_sha256"] != split["membership"]["sha256"]):
        raise ValueError("Inconsistent model/membership version")
    if policy["specialist_categories"] != protocol["gating"]["specialist_categories"]:
        raise ValueError("Invalid specialist policy")
    if policy["mode"] not in {"qualified", "manual_only"}:
        raise ValueError("Missing gate mode")
    if (reference["context"] != "it_service_en" or reference["normalization"] != NORMALIZATION or
            reference["model_version"] != manifest["model_version"] or
            reference["membership_sha256"] != manifest["membership_sha256"] or
            reference["minimum"] != protocol["gating"]["reference_min_records"] or
            reference["method"] != "linear-empirical-quantile-v1"):
        raise ValueError("Incompatible reference")
    if policy["mode"] == "qualified":
        if policy["threshold"] not in protocol["gating"]["score_threshold_grid"] or reference["tail"] not in protocol["gating"]["anomaly_tail_grid"]:
            raise ValueError("Unselected parameters")
        if set(reference["groups"]) != set(CLASSES):
            raise ValueError("Incomplete reference classes")
    elif policy["threshold"] is not None or reference["tail"] is not None or reference["groups"]:
        raise ValueError("Invalid explicit manual fallback")
    for metrics in reference["groups"].values():
        if set(metrics) != {"model_score", "text_chars"}:
            raise ValueError("Incomplete reference metrics")
        for bounds in metrics.values():
            n, lower, upper = (bounds[k] for k in ("n", "lower", "upper"))
            if not isinstance(n, int) or n < 0:
                raise ValueError("Invalid reference support")
            if n >= reference["minimum"]:
                if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in (lower, upper)) or lower > upper:
                    raise ValueError("Invalid reference bounds")
            elif lower is not None or upper is not None:
                raise ValueError("Insufficient reference has bounds")
    return manifest, policy, reference
