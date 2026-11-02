"""Partition guarantees versus brute force, plus independent selection examples."""

import importlib.util
from itertools import combinations
import json
from pathlib import Path
import random
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"solution/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


splits, rules = load("prepare_evaluation"), load("evaluation_rules")


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads((ROOT / "data/evaluation-protocol.json").read_text())

    def test_prefix_join_matches_exhaustive_pairs_including_boundary(self):
        rng = random.Random(41)
        sets = [frozenset(rng.sample(range(25), rng.randint(1, 20))) for _ in range(120)]
        sets.extend([frozenset(range(17)), frozenset(range(20)), frozenset(), frozenset(range(17))])
        for numerator, denominator in [(17, 20), (2, 3), (1, 1)]:
            expected = {(a, b) for a, b in combinations(range(len(sets)), 2) if sets[a] and sets[b] and
                        denominator * len(sets[a] & sets[b]) >= numerator * len(sets[a] | sets[b])}
            actual = {tuple(sorted(pair)) for pair in splits.jaccard_pairs(sets, numerator, denominator)}
            self.assertEqual(actual, expected)

    def test_transitive_components_do_not_split_or_relabel(self):
        rows = [{"Document": " ".join(f"w{i}" for i in range(start, start + 20)), "Topic_group": label}
                for start, label in [(0, "A"), (1, "B"), (2, "A")]]
        groups, _, _, _ = splits.group_rows(rows, self.protocol, "source")
        self.assertEqual(len(groups), 1)
        self.assertEqual(dict(groups[0]["labels"]), {"A": 2, "B": 1})
        self.assertFalse(groups[0]["quarantine"])

    def test_exact_conflicts_quarantine_and_preserve_rows(self):
        groups, _, stats, _ = splits.group_rows([
            {"Document": "Ａ test", "Topic_group": "A"},
            {"Document": "a  test", "Topic_group": "B"}], self.protocol, "source")
        self.assertTrue(groups[0]["quarantine"])
        self.assertEqual(stats["exact_conflicting_rows"], 2)
        self.assertEqual(len(groups[0]["rows"]), 2)

    def test_allocation_is_deterministic_and_keeps_groups_whole(self):
        rows = [{"Document": f"unique{i} token{i}", "Topic_group": "A" if i % 2 else "B"} for i in range(60)]
        groups, _, _, _ = splits.group_rows(rows, self.protocol, "source")
        a = splits.allocate(groups, self.protocol["split"]["fractions"], "seed")
        self.assertEqual(a, splits.allocate(list(reversed(groups)), self.protocol["split"]["fractions"], "seed"))
        self.assertEqual(set(a.values()), set(splits.PARTITIONS))
        self.assertEqual(sum(len(group["rows"]) for group in groups), 60)

    def test_wilson_bounds_and_empty_population(self):
        self.assertIsNone(rules.wilson_lower(0, 0))
        self.assertAlmostEqual(rules.wilson_lower(100, 100), .9630065, places=6)
        self.assertLess(rules.wilson_lower(90, 100), .9)
        with self.assertRaises(ValueError):
            rules.wilson_lower(2, 1)

    def test_model_selection_rejects_weak_scores_and_resolves_ties(self):
        scores = {"majority": .05, "multinomial_nb": .75, "logistic_c05": .8, "logistic_c20": .8}
        self.assertEqual(rules.choose_model(scores, self.protocol), "logistic_c05")
        self.assertEqual(rules.choose_model({**scores, "logistic_c05": .74, "logistic_c20": .74}, self.protocol), "logistic_c05")
        scores.update(logistic_c05=.6, logistic_c20=.6)
        self.assertIsNone(rules.choose_model(scores, self.protocol))

    def test_gate_quality_constraints_and_no_permissive_fallback(self):
        weak = {"threshold": .5, "tail": .01, "standard_cases": 200, "standard_correct": 180,
                "scored_cases": 1000, "anomaly_cases": 20, "mean_cost": .3}
        self.assertIsNone(rules.choose_gate([weak], self.protocol))
        good = {**weak, "standard_correct": 198}
        self.assertEqual(rules.choose_gate([good], self.protocol)["threshold"], .5)
        self.assertIsNone(rules.choose_gate([{**good, "anomaly_cases": 200}], self.protocol))

    def test_assumed_error_cost_distinguishes_specialist_misclassification(self):
        result = rules.assumed_cost(["Access", "Hardware"], ["Storage", "Storage"],
                                    ["standard_review", "standard_review"], self.protocol)
        self.assertAlmostEqual(result, 3.2)  # (.2+5 + .2+1)/2.
        self.assertIsNone(rules.assumed_cost([], [], [], self.protocol))


if __name__ == "__main__":
    unittest.main()
