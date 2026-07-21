import json
from pathlib import Path
import pandas as pd

def test_exact_output_inventory_and_privacy():
    root=Path(__file__).parents[1]
    registry=pd.read_parquet(root/"data/processed/experiment_registry.parquet"); assignment=pd.read_parquet(root/"data/processed/experiment_assignment_simulation.parquet")
    assert len(registry)==8 and set(registry.causal_status)=={"UNTESTED"}
    assert assignment.simulation_only.all() and "account_id" not in assignment
    assert len(list((root/"artifacts").glob("experiment_*.json")))==11
    assert len(list((root/"experiments").glob("EXP*.json")))==8
    assert len(list((root/"reports").glob("experiment-*.md")))==6
    assert len(list((root/"reports/figures").glob("experiment-*.png")))==6
    for path in (root/"artifacts").glob("experiment_*.json"): assert '"account_key"' not in path.read_text()
