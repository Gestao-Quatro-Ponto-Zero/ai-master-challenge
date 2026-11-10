"""The commands that read the score files work on a fresh clone, before any build.

The AI check and the generation build solution/out/ themselves when it is missing;
this runs the check in a copy of solution/ with no out/, as a fresh clone has it.
Run: python3.12 -m unittest discover -s solution/tests
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOLUTION = Path(__file__).resolve().parents[1]


class FreshClone(unittest.TestCase):
    def test_ai_check_runs_with_no_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "solution"
            shutil.copytree(SOLUTION, copy, ignore=shutil.ignore_patterns("out", "__pycache__"))
            self.assertFalse((copy / "out").exists())
            done = subprocess.run([sys.executable, str(copy / "ai" / "check.py")],
                                  capture_output=True, text=True, timeout=300)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            self.assertIn("0 failures", done.stdout)
            self.assertTrue((copy / "out" / "index.json").exists())


if __name__ == "__main__":
    unittest.main()
