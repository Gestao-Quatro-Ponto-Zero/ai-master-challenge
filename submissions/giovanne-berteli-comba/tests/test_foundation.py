"""Regression probes for F01, isolated from the real working tree."""

from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("foundation", ROOT / "scripts/check_foundation.py")
foundation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(foundation)


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "submission"
        # Preserve paths for link existence without loading recruitment archives.
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(
            "__pycache__", ".venv", ".runtime", "raw", "processed", "models", "runtime", "chat-exports"))
        archive_dir = self.root / "process-log/chat-exports"
        archive_dir.mkdir(exist_ok=True)
        for archive in (ROOT / "process-log/chat-exports").glob("*.md"):
            (archive_dir / archive.name).touch()
        # A receipt link may precede the first real capture; never reuse it as proof.
        (self.root / foundation.RECEIPT).touch(exist_ok=True)

    def record(self, inputs=()):
        with redirect_stdout(io.StringIO()):
            result = foundation.main(["--root", str(self.root), "--record",
                                      *[arg for name in inputs for arg in ("--input", name)]])
        self.assertEqual(result, 0)

    def mutate(self, name, old, new):
        path = self.root / name
        content = path.read_text()
        self.assertIn(old, content)
        path.write_text(content.replace(old, new, 1))

    def test_current_documents_and_receipt_pass(self):
        errors, _ = foundation.check_documents(self.root)
        self.assertEqual(errors, [])
        self.record()
        self.assertEqual(foundation.check_receipt(self.root, foundation.RECEIPT), [])

    def test_original_challenge_mutation_is_rejected_even_when_recording(self):
        self.mutate("PROJECT_STATUS.md", "**002", "**004")
        errors, _ = foundation.check_documents(self.root)
        self.assertTrue(any("challenge conflict" in error for error in errors))
        with redirect_stdout(io.StringIO()):
            result = foundation.main(["--root", str(self.root), "--record"])
        self.assertEqual(result, 1)

    def test_missing_challenge_declaration_is_rejected(self):
        self.mutate("AGENTS.md", "Challenge 002 is selected", "Challenge choice removed")
        errors, _ = foundation.check_documents(self.root)
        self.assertTrue(any("AGENTS.md: challenge" in error for error in errors))

    def test_changed_rule_requires_revalidation(self):
        self.record()
        with (self.root / "AGENTS.md").open("a") as target:
            target.write("\nChanged operational rule.\n")
        self.assertIn("STALE: input changed: AGENTS.md",
                      foundation.check_receipt(self.root, foundation.RECEIPT))

    def test_data_and_model_content_changes_and_deletion_are_detected(self):
        for name in ("sample.csv", "model.json"):
            (self.root / name).write_text("original\n")
        self.record(["sample.csv", "model.json"])
        (self.root / "sample.csv").write_text("changed\n")
        (self.root / "model.json").write_text("new model configuration\n")
        self.assertIn("STALE: input changed: model.json",
                      foundation.check_receipt(self.root, foundation.RECEIPT))
        (self.root / "model.json").unlink()
        errors = foundation.check_receipt(self.root, foundation.RECEIPT)
        self.assertIn("STALE: input changed: sample.csv", errors)
        self.assertIn("STALE: input missing: model.json", errors)

    def test_new_knowledge_input_invalidates_receipt(self):
        self.record()
        (self.root / "knowledge/new.md").write_text("---\ntype: Note\n---\n")
        self.assertIn("STALE: dependency membership changed: knowledge/new.md",
                      foundation.check_receipt(self.root, foundation.RECEIPT))

    def test_broken_link_is_reported(self):
        (self.root / "execution/backlog.md").unlink()
        errors, _ = foundation.check_documents(self.root)
        self.assertTrue(any("missing local link" in error for error in errors))

    def test_missing_and_malformed_receipt_fail_closed(self):
        receipt = self.root / foundation.RECEIPT
        receipt.unlink(missing_ok=True)
        self.assertTrue(foundation.check_receipt(self.root, foundation.RECEIPT))
        receipt.write_text("{broken json")
        self.assertTrue(foundation.check_receipt(self.root, foundation.RECEIPT))

    def test_recruitment_archive_content_is_not_a_dependency(self):
        self.record()
        archive = self.root / "process-log/chat-exports/01-preparation-chatgpt.md"
        archive.write_text("Historical Challenge 004; not operational authority.\n")
        self.assertEqual(foundation.check_receipt(self.root, foundation.RECEIPT), [])

    def test_inputs_cannot_escape_submission(self):
        with self.assertRaises(ValueError):
            foundation.capture(self.root, ["../outside"])

    def test_cli_works_from_unrelated_directory_without_site_packages(self):
        self.record()
        result = subprocess.run([
            sys.executable, "-I", str(self.root / "scripts/check_foundation.py")
        ], cwd=self.temp.name, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
