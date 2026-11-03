"""Pure decision and anomaly rules shared by selection, worker and coordinator."""

import math
import unicodedata

CLASSES = ("Access", "Administrative rights", "HR Support", "Hardware",
           "Internal Project", "Miscellaneous", "Purchase", "Storage")
NORMALIZATION = "nfkc-casefold-space-v1"
METRICS = ("model_score", "text_chars")
MAX_CHARS = 10000


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def quantile(values, q):
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def build_reference(categories, scores, lengths, tail, model_version, membership_hash, minimum=100):
    groups = {}
    for category in CLASSES:
        indices = [i for i, value in enumerate(categories) if value == category]
        groups[category] = {}
        for metric, values in (("model_score", scores), ("text_chars", lengths)):
            sample = [float(values[i]) for i in indices]
            enough = len(sample) >= minimum
            groups[category][metric] = {"n": len(sample),
                                        "lower": quantile(sample, tail) if enough else None,
                                        "upper": quantile(sample, 1 - tail) if enough else None}
    return {"context": "it_service_en", "model_version": model_version,
            "normalization": NORMALIZATION, "membership_sha256": membership_hash,
            "method": "linear-empirical-quantile-v1", "tail": tail, "minimum": minimum, "groups": groups}


def metrics_for(category, score, length, reference=None, reason="no_valid_prediction"):
    result = []
    for metric, value in (("model_score", score), ("text_chars", length)):
        bounds = (reference or {}).get("groups", {}).get(category, {}).get(metric, {})
        record = {"metric": metric, "value": value, "category": category,
                  "reference_id": (reference or {}).get("id"), "n": bounds.get("n", 0),
                  "lower": bounds.get("lower"), "upper": bounds.get("upper"),
                  "method": (reference or {}).get("method"), "tail": (reference or {}).get("tail"),
                  "status": "not_evaluated", "direction": None, "reason": reason,
                  "rule_version": "quantile-comparison-v1"}
        if category is not None and value is not None:
            if record["n"] < (reference or {}).get("minimum", 100) or record["lower"] is None:
                record["reason"] = "insufficient_reference"
            else:
                direction = "low" if value < record["lower"] else "high" if value > record["upper"] else None
                record.update(status="possible_anomaly" if direction else "ordinary", direction=direction,
                              reason="outside_reference" if direction else "within_reference")
        result.append(record)
    return result


def no_prediction(reason, length=None, failed=False):
    return {"outcome": "failed" if failed else "review_needed", "review_queue": "triage_review",
            "reason_codes": [reason], "predicted_category": None, "score": None,
            "metrics": metrics_for(None, None, length, reason=reason)}


def decide(category, score, length, policy, reference):
    """Route a validated prediction; true labels are deliberately absent."""
    assessments = metrics_for(category, score, length, reference)
    reasons = []
    if policy["mode"] == "manual_only":
        reasons.append("no_feasible_gate")
    elif score < policy["threshold"]:
        reasons.append("low_score")
    if any(item["status"] == "possible_anomaly" for item in assessments):
        reasons.append("anomaly_review")
    if any(item["status"] == "not_evaluated" for item in assessments):
        reasons.append("insufficient_reference")
    if category in policy["specialist_categories"]:
        reasons.append("policy_human_category")
    if any(reason in reasons for reason in ("no_feasible_gate", "low_score", "anomaly_review", "insufficient_reference")):
        queue, outcome = "triage_review", "review_needed"
    elif "policy_human_category" in reasons:
        queue, outcome = "specialist_review", "review_needed"
    else:
        queue, outcome = "standard_review", "suggested"
        reasons.append("standard_confirmation")
    return {"outcome": outcome, "review_queue": queue, "reason_codes": reasons,
            "predicted_category": category, "score": score, "metrics": assessments}


def from_scores(classes, scores, known_features, length, policy, reference):
    if (list(classes) != list(CLASSES) or len(scores) != len(CLASSES) or
            any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in scores) or
            not math.isclose(sum(scores), 1, abs_tol=1e-6, rel_tol=0)):
        return no_prediction("invalid_model_output", length, failed=True)
    if not isinstance(known_features, int) or known_features < 0:
        return no_prediction("invalid_model_output", length, failed=True)
    if known_features == 0:
        return no_prediction("no_known_features", length)
    best = max(range(len(scores)), key=scores.__getitem__)
    return decide(classes[best], scores[best], length, policy, reference)
