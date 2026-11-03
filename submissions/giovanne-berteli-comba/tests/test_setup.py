"""Idempotent setup and actionable diagnostics without fitting a classifier."""

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "solution"))
from triage.artifacts import BUNDLE
from triage.setup_state import reuse_completed


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / BUNDLE
        self.directory.mkdir(parents=True)
        (self.root / "data/evaluation-protocol.json").write_bytes((ROOT / "data/evaluation-protocol.json").read_bytes())

    def attempt(self, **overrides):
        value = {"state": "completed", "fits_started": ["majority", "multinomial_nb", "logistic_c05", "logistic_c20"], "final_test_predictions": 0, **overrides}
        (self.directory / "training-attempt.json").write_text(json.dumps(value))

    def test_empty_directory_allows_first_training(self):
        self.assertFalse(reuse_completed(self.root))

    def test_completed_training_is_verified_and_reused_without_mutation(self):
        self.attempt()
        before = (self.directory / "training-attempt.json").read_bytes()
        with patch("triage.setup_state.load_metadata") as check, redirect_stdout(io.StringIO()) as output:
            self.assertTrue(reuse_completed(self.root))
        check.assert_called_once_with(self.root)
        self.assertIn("sem novo ajuste", output.getvalue())
        self.assertEqual(before, (self.directory / "training-attempt.json").read_bytes())

    def test_interrupted_unknown_or_modified_artifacts_never_restart_fitting(self):
        for state in ["started", "failed", "unknown"]:
            self.attempt(state=state)
            with patch("triage.setup_state.load_metadata") as check:
                with self.assertRaisesRegex(ValueError, "incompleto"):
                    reuse_completed(self.root)
                check.assert_not_called()
        self.attempt()
        with patch("triage.setup_state.load_metadata", side_effect=ValueError("Stale bundle input")):
            with self.assertRaisesRegex(ValueError, "incompatíveis"):
                reuse_completed(self.root)

    def test_orphaned_and_corrupt_state_are_preserved(self):
        orphan = self.directory / "logistic_c20.pkl"
        orphan.write_bytes(b"fixture")
        with self.assertRaisesRegex(ValueError, "sem registro"):
            reuse_completed(self.root)
        self.assertEqual(orphan.read_bytes(), b"fixture")
        (self.directory / "training-attempt.json").write_text("{")
        with self.assertRaisesRegex(ValueError, "inválido"):
            reuse_completed(self.root)

    def test_no_eligible_model_keeps_explicit_manual_fallback(self):
        self.attempt()
        with patch("triage.setup_state.load_metadata", side_effect=ValueError("No quality-qualified model")), redirect_stdout(io.StringIO()) as output:
            self.assertTrue(reuse_completed(self.root))
        self.assertIn("revisão humana", output.getvalue())

    def test_training_entrypoint_returns_before_imports_or_population_loading(self):
        spec = importlib.util.spec_from_file_location("setup_training_fixture", ROOT / "solution/train_triage.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.object(module, "reuse_completed", return_value=True), patch.object(module, "populations", side_effect=AssertionError("Must not fit")):
            self.assertIsNone(module.main())

    def test_launcher_help_works_from_unrelated_directory_without_setup(self):
        result = subprocess.run(["bash", str(ROOT / "run.sh"), "--help"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--prepare-only", result.stdout)
        self.assertFalse((self.root / ".venv").exists())


if __name__ == "__main__":
    unittest.main()
