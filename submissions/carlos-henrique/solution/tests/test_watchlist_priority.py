import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from watchlist_priority import assign_priority, priority_matrix

def test_discrete_matrix_and_low_confidence_block():
    assert priority_matrix("HIGH","HIGH","HIGH","MEDIUM","RECENT_CHURN_REVIEW")[0] == "P1"
    row={"watchlist_rule_id":"W004","queue":"RECENT_CHURN_REVIEW","stability_status":"SENSITIVE","quality_coverage_ratio":.1,"rule_group_size":40,"strict_supported":False,"days_since_last_churn":3,"mrr_band":"VERY_HIGH","main_strict_divergence":.9,"same_day_order_dependency":"HIGH"}
    result=assign_priority(row)
    assert result["data_confidence"] == "LOW" and result["priority"] != "P1"
