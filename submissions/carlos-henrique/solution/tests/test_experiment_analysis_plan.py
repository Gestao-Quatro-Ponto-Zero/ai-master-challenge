import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from experiment_analysis_plan import build_analysis_plans,build_guardrails,build_stopping_rules,validate_analysis_plans
from experiment_hypotheses import build_hypotheses

def test_sap_uses_itt_guardrails_and_all_stop_types():
    h=build_hypotheses(); plans=build_analysis_plans(h); guards=build_guardrails(h); stops=build_stopping_rules(h)
    assert validate_analysis_plans(plans,guards,stops)["itt_false"]==0
    assert {row["stop_type"] for row in stops}=={"SAFETY_STOP","FUTILITY_STOP","DATA_QUALITY_STOP","OPERATIONAL_STOP","SAMPLE_EXHAUSTION","PLANNED_COMPLETION"}
    assert all(row["specification_only"] for row in guards)
