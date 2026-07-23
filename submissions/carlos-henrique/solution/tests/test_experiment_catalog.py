import json,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from experiment_catalog import validate_catalog

def test_catalog_is_complete_and_design_only():
    payload=json.loads((Path(__file__).parents[1]/"config/intervention_catalog.json").read_text())
    assert validate_catalog(payload)["intervention_count"]==10
    broken=json.loads(json.dumps(payload)); broken["interventions"][0]["treatment_result"]="x"
    with pytest.raises(ValueError): validate_catalog(broken)
