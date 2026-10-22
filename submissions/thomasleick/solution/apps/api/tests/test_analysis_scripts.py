import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


APP_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("RAVENSTACK_DATA_DIR", APP_ROOT / "data" / "raw"))
SCRIPTS = APP_ROOT / "scripts"


@pytest.mark.parametrize("script_name", ["audit_data.py", "analyze.py"])
def test_cli_help_is_available(script_name):
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / script_name), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--data-dir" in result.stdout
    assert "--output" in result.stdout


@pytest.mark.parametrize("script_name", ["audit_data.py", "analyze.py"])
def test_cli_uses_packaged_defaults_and_writes_only_to_explicit_output(script_name, tmp_path):
    output = tmp_path / "nested" / f"{script_name}.json"
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / script_name), "--output", str(output)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert output.is_file()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert "Wrote" in result.stdout
    if script_name == "analyze.py":
        assert payload["counts"]["accounts"] == 500
        assert payload["counts"]["usage_duplicate_ids"] == 21
        assert payload["counts"]["usage_rows_in_duplicate_id_groups"] == 42
        assert payload["counts"]["usage_duplicate_excess_rows"] == 21
        assert payload["support_satisfaction_by_event_membership"]["event_accounts"]["satisfaction_n"] == 815
    else:
        assert payload["ravenstack_accounts.csv"]["rows"] == 500
        assert payload["relationships"]["feature_usage.subscription_id"]["orphan_rows"] == 0


def test_cli_rejects_a_missing_dataset_directory():
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "analyze.py"), "--data-dir", str(DATA_DIR / "missing")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "missing required CSV files" in result.stderr
