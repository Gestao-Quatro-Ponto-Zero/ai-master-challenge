import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sequential_mining import account_subsequences, mine_frequent_sequences


def test_equivalent_prefixspan_respects_gap_and_length():
    dates = list(pd.to_datetime(["2024-01-01", "2024-01-02", "2024-06-01"]))
    patterns = account_subsequences(["A", "B", "C"], dates, max_pattern_length=2, max_gap_events=0, max_gap_days=30)
    assert ("A", "B") in patterns
    assert ("B", "C") not in patterns
    assert all(len(pattern) <= 2 for pattern in patterns)


def test_support_and_closed_pruning():
    dates = list(pd.date_range("2024-01-01", periods=3))
    sequences = {str(i): (["A", "B", "C"], dates) for i in range(3)}
    result = mine_frequent_sequences(sequences, min_support_accounts=2, max_pattern_length=3, max_gap_events=1, closed_patterns_only=True)
    labels = {row["pattern_label"] for row in result["patterns"]}
    assert "A -> B -> C" in labels
    assert result["redundancy_removed"] > 0
    assert result["patterns_before_pruning"] == result["patterns_after_pruning"] + result["redundancy_removed"]


def test_zero_accounts_has_safe_denominator():
    result = mine_frequent_sequences({}, min_support_accounts=1)
    assert result["denominator_accounts"] == 0
    assert result["patterns"] == []
