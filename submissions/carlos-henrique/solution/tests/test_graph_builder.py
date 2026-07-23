"""Tests for governed graph construction and promotion."""

import json
import sys
from pathlib import Path

import pandas as pd

SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(SRC))

from graph_builder import build_analytical_graph, pattern_matches, promoted_patterns  # noqa: E402


def _pattern() -> dict:
    return {
        "pattern": ["FEATURE", "CHURN"], "pattern_label": "FEATURE -> CHURN",
        "pattern_type": "SEQUENTIAL_CLOSED", "journey_scope": "FULL_OBSERVED_JOURNEY",
        "outcome_context": "SINGLE_CHURN", "quality_population": "MAIN",
        "account_support": 20, "denominator_accounts": 40, "relative_support": .5,
        "confidence": .5, "lift": 1.2, "coverage": .5, "leverage": .1,
        "discriminative_ratio": 1.2, "principal_support": 20, "strict_support": 18,
        "stability_status": "ROBUST", "same_day_dependency": "NONE",
        "small_sample": False, "exposure_control": "ACCOUNT_SUPPORT",
        "associated_mrr": 1000.0, "median_mrr": 50.0, "mean_mrr": 50.0,
        "mrr_account_count": 20,
    }


def _transition(stability: str = "ROBUST", order: str = "NONE") -> dict:
    return {
        "source_event": "FEATURE", "target_event": "CHURN",
        "journey_scope": "FULL_OBSERVED_JOURNEY", "outcome": "SINGLE_CHURN",
        "account_support": 20, "transition_count": 22, "denominator_accounts": 40,
        "relative_support": .5, "source_conditional_probability": .6,
        "lift_vs_population": 1.2, "principal_support": 20, "strict_support": 18,
        "stability_status": stability, "same_day_dependency": order,
        "small_sample": False,
    }


def test_pattern_matching_respects_sequence_semantics() -> None:
    tokens = ["ACCOUNT", "FEATURE", "SUPPORT_OPEN", "CHURN"]
    assert pattern_matches(tokens, ["FEATURE", "CHURN"], "SEQUENTIAL_CLOSED")
    assert not pattern_matches(tokens, ["FEATURE", "CHURN"], "NGRAM_2_COLLAPSED")
    assert pattern_matches(tokens, ["SUPPORT_OPEN", "CHURN"], "PRE_CHURN_SUFFIX_30D_L2")


def test_promotion_excludes_unstable_high_and_small_candidates() -> None:
    base = {
        "pattern": ["FEATURE", "CHURN"], "pattern_label": "FEATURE -> CHURN",
        "denominator_accounts": 40, "account_support": 20, "relative_support": .5,
        "stability_status": "ROBUST", "same_day_dependency": "NONE",
        "principal_support": 20, "strict_support": 18, "is_generic": False,
    }
    sequential = {"patterns": [base, {**base, "pattern_label": "UNSTABLE", "stability_status": "UNSTABLE"}, {**base, "pattern_label": "HIGH", "same_day_dependency": "HIGH"}]}
    promoted, rejected = promoted_patterns(sequential, {"patterns": []}, {"patterns": []})
    assert len(promoted) == 1
    assert rejected == {"HIGH_ORDER_DEPENDENCY": 1, "UNSTABLE": 1}


def test_analytical_graph_contains_governed_nodes_and_only_promotable_edges() -> None:
    journeys = pd.DataFrame([{"account_id": "a1", "quality_population": "MAIN", "outcome": "SINGLE_CHURN", "journey_scope": "FULL_OBSERVED_JOURNEY", "collapsed_sequence": json.dumps(["FEATURE", "CHURN"])}])
    features = pd.DataFrame([{"account_id": "a1", "primary_outcome": "SINGLE_CHURN", "max_mrr": 100.0}])
    built = build_analytical_graph([_pattern()], [_transition(), _transition("UNSTABLE", "NONE")], [], [{"taxonomy_id": "T1", "name": "TEST", "definition": "Fixture"}], journeys, features)
    labels = {data["label"] for _, data in built.graph.nodes(data=True)}
    assert {"EventType", "Pattern", "Outcome", "Taxonomy", "QualityProfile", "Investigation"} <= labels
    transitions = [data for *_, data in built.graph.edges(data=True, keys=True) if data["relationship"] == "TRANSITIONS_TO"]
    assert len(transitions) == 1 and transitions[0]["is_promotable"]
    assert built.accounting["rejected_transitions"] == {"UNSTABLE": 1}
