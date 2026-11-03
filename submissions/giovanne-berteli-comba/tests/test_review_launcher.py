"""External reviewer entry point: resolve cwd/profile and install only if absent."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReviewLauncherTests(unittest.TestCase):
    def run_launcher(self, installed):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            submission = root / "submission with spaces"
            submission.mkdir()
            shutil.copyfile(ROOT / "review.sh", submission / "review.sh")
            (submission / "review.code-workspace").write_text('{}')
            executable = root / "bin"
            executable.mkdir()
            log = root / "calls.jsonl"
            mock = executable / "code"
            mock.write_text('#!/usr/bin/env python3\n' +
                            'import json,os,sys\n' +
                            'with open(os.environ["REVIEW_TEST_LOG"],"a") as f: f.write(json.dumps(sys.argv[1:])+"\\n")\n' +
                            'if sys.argv[1:]==["--list-extensions"] and os.environ["REVIEW_TEST_INSTALLED"]=="yes": print("vsls-contrib.codetour")\n')
            mock.chmod(0o700)
            environment = {**os.environ, "PATH": str(executable) + os.pathsep + os.environ["PATH"],
                           "REVIEW_TEST_LOG": str(log), "REVIEW_TEST_INSTALLED": "yes" if installed else "no"}
            result = subprocess.run(["bash", str(submission / "review.sh")], cwd=root, env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual(calls[0], ["--list-extensions"])
            self.assertEqual(calls[-1], ["--new-window", str(submission / "review.code-workspace")])
            self.assertIn("Start CodeTour", result.stdout)
            return calls

    def test_installed_extension_opens_correct_workspace_from_another_cwd(self):
        self.assertEqual(len(self.run_launcher(True)), 2)

    def test_missing_extension_installs_official_id_before_opening_workspace(self):
        calls = self.run_launcher(False)
        self.assertEqual(calls[1], ["--install-extension", "vsls-contrib.codetour"])
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
