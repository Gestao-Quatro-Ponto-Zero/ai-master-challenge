"""Stored AI texts show only on the Monday they were written for.

The index marks that Monday (ai_texts); the page reads the mark. With the texts
file present only its own Monday is marked; with the file absent, none is; and the
contract check refuses an index that marks another Monday.
Run: python3.12 -m unittest discover -s solution/tests
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOLUTION = Path(__file__).resolve().parents[1]


def fresh_copy(tmp):
    copy = Path(tmp) / "solution"
    shutil.copytree(SOLUTION, copy, ignore=shutil.ignore_patterns("out", "__pycache__"))
    return copy


def run(copy, script):
    return subprocess.run([sys.executable, str(copy / script)], capture_output=True, text=True, timeout=300)


def marks(copy):
    index = json.loads((copy / "out" / "index.json").read_text(encoding="utf-8"))
    return {m["monday"]: m["ai_texts"] for m in index["mondays"]}


class TextsByMonday(unittest.TestCase):
    def test_only_the_texts_monday_is_marked(self):
        own = json.loads((SOLUTION / "ai" / "textos.json").read_text(encoding="utf-8"))["meta"]["monday"]
        with tempfile.TemporaryDirectory() as tmp:
            copy = fresh_copy(tmp)
            self.assertEqual(run(copy, "build.py").returncode, 0)
            self.assertEqual([m for m, on in marks(copy).items() if on], [own])
            self.assertEqual(run(copy, "check_contract.py").returncode, 0)
            # an index that lets a past Monday show the texts is refused
            path = copy / "out" / "index.json"
            index = json.loads(path.read_text(encoding="utf-8"))
            next(m for m in index["mondays"] if m["past"])["ai_texts"] = True
            path.write_text(json.dumps(index), encoding="utf-8")
            done = run(copy, "check_contract.py")
            self.assertNotEqual(done.returncode, 0)
            self.assertIn("ai_texts", done.stdout + done.stderr)

    def test_no_monday_is_marked_without_the_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = fresh_copy(tmp)
            (copy / "ai" / "textos.json").unlink()
            self.assertEqual(run(copy, "build.py").returncode, 0)
            self.assertFalse(any(marks(copy).values()))
            self.assertEqual(run(copy, "check_contract.py").returncode, 0)


if __name__ == "__main__":
    unittest.main()
