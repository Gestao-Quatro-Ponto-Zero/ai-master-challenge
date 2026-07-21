import json
from pathlib import Path

def test_validation_gate_and_privacy_contract():
    root=Path(__file__).parents[1]; artifact=root/"artifacts/watchlist_validation.json"
    value=json.loads(artifact.read_text())
    assert value["difference_unexplained"] == 0
    assert value["priority"]["behavioral_low_confidence_p1"] == 0
    for path in root.joinpath("artifacts").glob("watchlist_*.json"):
        assert '"account_key"' not in path.read_text()
