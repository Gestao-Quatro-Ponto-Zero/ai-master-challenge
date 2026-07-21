import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from journey_patterns import ngram_rows, ngrams, transition_rows


def _records(population="MAIN"):
    return [{"account_id": str(i), "quality_population": population, "journey_scope": "FULL_OBSERVED_JOURNEY", "outcome": "NO_CHURN_OBSERVED", "_tokens": ["ACCOUNT", "FEATURE", "CHURN"], "_dates": list(pd.date_range("2024-01-01", periods=3)), "_raw_tokens": ["ACCOUNT", "FEATURE", "FEATURE", "CHURN"], "_raw_dates": list(pd.date_range("2024-01-01", periods=4))} for i in range(20)]


def test_ngram_content():
    assert ngrams(["A", "B", "C"], 2) == [("A", "B"), ("B", "C")]


def test_transition_support_is_by_account():
    rows = transition_rows(_records() + _records("STRICT"))
    feature_churn = next(r for r in rows if r["source_event"] == "FEATURE" and r["target_event"] == "CHURN")
    assert feature_churn["account_support"] == 20
    assert feature_churn["denominator_accounts"] == 20
    assert feature_churn["strict_denominator_accounts"] == 20
    assert feature_churn["source_conditional_probability"] == 1
    assert feature_churn["stability_status"] == "ROBUST"


def test_raw_bigram_sensitivity_and_group_gate():
    rows = ngram_rows(_records() + _records("STRICT"))
    raw = next(r for r in rows if r["representation"] == "RAW_BIGRAM_SENSITIVITY" and r["pattern_label"] == "FEATURE -> FEATURE")
    assert raw["absolute_occurrences"] == 20
    assert not raw["small_sample"]
