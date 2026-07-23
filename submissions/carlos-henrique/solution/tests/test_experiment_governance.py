import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from experiment_governance import validate_governance

def test_governance_rejects_effective_and_causal_results():
    good=[{"status":"DRAFT","causal_status":"UNTESTED"}]
    assert validate_governance(good,[{"statement":"Design requires more data."}])["interventions_executed"]==0
    with pytest.raises(AssertionError): validate_governance([{"status":"EFFECTIVE","causal_status":"UNTESTED"}],[])
