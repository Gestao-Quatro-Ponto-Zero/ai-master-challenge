import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from experiment_hypotheses import build_hypotheses

def test_hypotheses_are_untested_with_one_primary_metric():
    rows=build_hypotheses()
    assert len(rows)==8 and all(row["causal_status"]=="UNTESTED" for row in rows)
    assert all(isinstance(row["primary_metric"],str) and row["primary_metric"] not in row["secondary_metrics"] for row in rows)
