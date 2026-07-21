import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from watchlist_explanations import build_explanation, validate_explanation_language

def test_deterministic_template_and_unsafe_language_rejected():
    row={"watchlist_rule_id":"W001","queue":"ADOPTION_REVIEW","rule_group_size":20,"matched_pattern_keys":"[]","matched_graph_finding_ids":"[]","reference_date":"2024-12-31T19:00:00","reference_window_days":30,"data_confidence":"MEDIUM","stability_status":"ROBUST","authorized_investigation":"Review evidence"}
    assert build_explanation(row) == build_explanation(row)
    frame=pd.DataFrame([{"what_was_observed":"will churn","why_it_was_flagged":"x","graph_context":"x","authorized_next_step":"x"}])
    with pytest.raises(AssertionError): validate_explanation_language(frame)
