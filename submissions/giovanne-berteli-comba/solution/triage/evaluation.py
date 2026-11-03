"""Evaluation denominators and frozen acceptance rules; no training or selection."""

from collections import Counter
import hashlib

from evaluation_rules import wilson_lower
from .core import CLASSES, quantile


def runtime_sample(case_ids, size, seed):
    if len(case_ids) != len(set(case_ids)) or not 0 < size <= len(case_ids):
        raise ValueError("Expected unique cases and a supported sample size")
    return sorted(case_ids, key=lambda case: (hashlib.sha256((seed + case).encode()).hexdigest(), case))[:size]


def summarize_assisted(truth, results):
    if len(truth) != len(results) or not results:
        raise ValueError("Expected aligned nonempty evaluation populations")
    standard = [i for i, item in enumerate(results) if item["review_queue"] == "standard_review"]
    correct = sum(results[i]["predicted_category"] == truth[i] for i in standard)
    metrics = [record for item in results for record in item["metrics"]]
    return {"attempted": len(results), "stored": sum(item["persisted"] for item in results),
            "failed_outcomes": sum(item["outcome"] == "failed" for item in results),
            "standard_cases": len(standard), "standard_correct": correct, "standard_errors": len(standard) - correct,
            "standard_accuracy": correct / len(standard) if standard else None,
            "standard_accuracy_wilson_lower_95": wilson_lower(correct, len(standard)),
            "standard_coverage": len(standard) / len(results),
            "queue_counts": dict(Counter(item["review_queue"] for item in results)),
            "outcome_counts": dict(Counter(item["outcome"] for item in results)),
            "reason_case_counts_overlapping": dict(Counter(reason for item in results for reason in set(item["reason_codes"]))),
            "anomaly_cases": sum(any(record["status"] == "possible_anomaly" for record in item["metrics"]) for item in results),
            "not_evaluated_cases": sum(any(record["status"] == "not_evaluated" for record in item["metrics"]) for item in results),
            "metric_record_counts": dict(Counter(f"{record['metric']}:{record['status']}:{record['direction'] or 'none'}" for record in metrics)),
            "standard_by_true_class": {label: {"all_test_cases": sum(t == label for t in truth),
                                                "standard_cases": sum(truth[i] == label for i in standard),
                                                "standard_correct": sum(truth[i] == label and results[i]["predicted_category"] == label for i in standard)} for label in CLASSES}}


def acceptance(models, selected, assisted, protocol):
    rules = protocol["final_test"]
    score = models[selected]["macro_f1"]
    lower = assisted["standard_accuracy_wilson_lower_95"]
    checks = {"min_macro_f1": score + 1e-12 >= rules["min_macro_f1"],
              "min_gain_over_majority": score - models["majority"]["macro_f1"] + 1e-12 >= rules["min_macro_f1_gain_over_majority"],
              "max_loss_against_text_baseline": models["multinomial_nb"]["macro_f1"] - score <= rules["max_macro_f1_loss_against_text_baseline"] + 1e-12,
              "min_standard_cases": assisted["standard_cases"] >= rules["min_standard_cases"],
              "min_standard_coverage": assisted["standard_coverage"] >= rules["min_standard_coverage"],
              "min_standard_accuracy_wilson_lower_95": lower is not None and lower >= rules["min_standard_accuracy_wilson_lower_95"]}
    return {"checks": checks, "all_quality_targets_passed": all(checks.values()),
            "meaning": "Predeclared offline benchmark targets only; not business approval, autonomous resolution or production readiness"}


def latency_summary(milliseconds):
    if not milliseconds:
        raise ValueError("Latency population must include every attempted request")
    return {"attempted": len(milliseconds), "p50_ms": quantile(milliseconds, .5),
            "p95_ms": quantile(milliseconds, .95), "max_ms": max(milliseconds)}
