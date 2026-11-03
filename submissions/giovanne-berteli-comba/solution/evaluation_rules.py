"""Frozen-protocol selection arithmetic; accepts validation summaries, fits nothing."""

import math


def wilson_lower(correct, total):
    if not 0 <= correct <= total:
        raise ValueError("Invalid counts")
    if not total:
        return None
    z = 1.959963984540054
    p = correct / total
    return (p + z * z / (2 * total) - z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)) / (1 + z * z / total)


def choose_model(macro_f1, protocol):
    rules = protocol["model_selection"]
    declared = {item["id"] for item in rules["candidates"]}
    if set(macro_f1) != declared or any(not math.isfinite(v) or not 0 <= v <= 1 for v in macro_f1.values()):
        raise ValueError("Expected finite validation macro F1 for exactly the declared candidates")
    eligible = [item["id"] for item in rules["candidates"] if item["role"] == "candidate" and
                macro_f1[item["id"]] + 1e-12 >= rules["validation_min_macro_f1"] and
                macro_f1[item["id"]] - macro_f1["majority"] + 1e-12 >= rules["min_macro_f1_gain_over_majority"] and
                macro_f1["multinomial_nb"] - macro_f1[item["id"]] <= rules["max_macro_f1_loss_against_text_baseline"] + 1e-12]
    return min(eligible, key=lambda name: (-macro_f1[name], name)) if eligible else None


def choose_gate(summaries, protocol):
    rules = protocol["gating"]
    feasible = []
    for item in summaries:
        if item["threshold"] not in rules["score_threshold_grid"] or item["tail"] not in rules["anomaly_tail_grid"]:
            raise ValueError("Gate pair not declared in protocol")
        n, correct, total, alerts = (item[k] for k in ["standard_cases", "standard_correct", "scored_cases", "anomaly_cases"])
        if not 0 <= correct <= n <= total or not 0 <= alerts <= total or not math.isfinite(item["mean_cost"]) or item["mean_cost"] < 0:
            raise ValueError("Invalid gate summary")
        if n < rules["validation_min_standard_cases"] or not total:
            continue
        coverage = n / total
        if (coverage >= rules["validation_min_standard_coverage"] and
                wilson_lower(correct, n) >= rules["validation_min_standard_accuracy_wilson_lower_95"] and
                alerts / total <= rules["validation_max_anomaly_share_of_scored"]):
            feasible.append({**item, "coverage": coverage})
    if not feasible:
        return None
    best_cost = min(item["mean_cost"] for item in feasible)
    tied = [item for item in feasible if item["mean_cost"] <= best_cost + 1e-12]
    return min(tied, key=lambda item: (-item["coverage"], -item["threshold"], item["tail"]))


def assumed_cost(truth, prediction, queues, protocol):
    if not len(truth) == len(prediction) == len(queues):
        raise ValueError("Mismatched evaluation populations")
    if not truth:
        return None
    costs = protocol["assumed_error_costs"]
    special = set(protocol["gating"]["specialist_categories"])
    total = 0
    for actual, predicted, queue in zip(truth, prediction, queues):
        if queue not in {"standard_review", "triage_review", "specialist_review"}:
            raise ValueError("Unknown review queue")
        total += costs[queue]
        if queue == "standard_review" and actual != predicted:
            total += costs["wrong_standard_category_when_true_class_is_specialist"] if actual in special else costs["wrong_standard_category"]
    return total / len(truth)
