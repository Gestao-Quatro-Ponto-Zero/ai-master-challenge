import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from journey_reporting import write_json


class _Parent:
    def mkdir(self, **kwargs):
        return None


class _MemoryPath:
    def __init__(self):
        self.parent = _Parent()
        self.content = ""

    def write_text(self, value, **kwargs):
        self.content = value


def test_json_is_deterministic_and_aggregate():
    path = _MemoryPath()
    payload = {"denominator_accounts": 20, "patterns": [{"pattern": ["A", "B"], "support": 10}]}
    write_json(path, payload)
    first = path.content
    write_json(path, payload)
    assert path.content == first
    assert json.loads(first)["denominator_accounts"] == 20


def test_artifact_payload_has_no_pii():
    path = _MemoryPath()
    write_json(path, {"patterns": [], "limitations": ["DESCRIPTIVE_NOT_CAUSAL"]})
    text = path.content.lower()
    assert "account_name" not in text
    assert "feedback_text" not in text
