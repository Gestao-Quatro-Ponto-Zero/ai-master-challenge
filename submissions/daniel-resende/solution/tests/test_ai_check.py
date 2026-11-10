"""The AI check refuses what the contract forbids and accepts a correct text.

Inputs are built in a temporary directory from the real score file; textos.json
does not need to exist.  Run: python3.12 -m unittest solution/tests/test_ai_check.py
"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
SOLUTION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOLUTION))
sys.path.insert(0, str(SOLUTION / "ai"))
import check  # noqa: E402
import facts  # noqa: E402
from render import render  # noqa: E402

TARGETS = facts.build_all()
NAMES = check.load_names()
DEAL = next(t for t in TARGETS.values() if t["kind"] == "deal" and "account" in t["facts"]
            and "cooling_label" not in t["facts"])
GOOD = {
    "reason": "O negócio de {product} está aberto há {days_open} dias e vai até {window_end}.",
    "next_step": "Próximo passo: {play_label}.",
}


def doc_with(reason, next_step=GOOD["next_step"], deal=DEAL):
    parts = {n: {"template": t, "text": render(t, {**deal["facts"], "color": "x"})}
             for n, t in (("reason", reason), ("next_step", next_step))}
    sha = check.prompt_hash()
    entry = {**{k: deal[k] for k in ("id", "kind", "target", "facts")}, "parts": parts,
             "provenance": {"model": "m", "generated_on": "2026-11-10", "prompt_sha256": sha, "batch": 1}}
    meta = {"monday": "2018-01-01", "score_file": "s", "prompt_file": "p",
            "prompt_sha256": sha, "command": "c"}
    return {"meta": meta, "texts": [entry]}


def run_check(doc):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "textos.json"
        p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        return check.check_texts(p, targets=TARGETS, names=NAMES)


class AiCheck(unittest.TestCase):
    def test_correct_text_passes(self):
        self.assertEqual(run_check(doc_with(GOOD["reason"])), [])

    def test_digit_outside_placeholder(self):
        errs = run_check(doc_with("Está aberto há 21 dias."))
        self.assertTrue(any("digit" in e for e in errs), errs)

    def test_unknown_placeholder(self):
        errs = run_check(doc_with("O negócio de {color} está parado."))
        self.assertTrue(any("not in facts" in e for e in errs), errs)

    def test_judgment_not_in_facts(self):
        errs = run_check(doc_with("Este negócio tem ótima chance de fechar."))
        self.assertTrue(any("judgment" in e for e in errs), errs)

    def test_dataset_name_outside_placeholder(self):
        name = DEAL["facts"]["product"]
        errs = run_check(doc_with(f"Fale do {name} com a conta."))
        self.assertTrue(any("dataset name" in e for e in errs), errs)
        errs = run_check(doc_with(f"Fale com {DEAL['facts']['account']} hoje."))
        self.assertTrue(any("dataset name" in e for e in errs), errs)

    def test_text_that_is_not_the_filled_template(self):
        doc = doc_with(GOOD["reason"])
        doc["texts"][0]["parts"]["reason"]["text"] += " Com 99 dias."
        errs = run_check(doc)
        self.assertTrue(any("not the template filled" in e for e in errs), errs)

    def test_fact_that_differs_from_the_score(self):
        doc = doc_with(GOOD["reason"])
        doc["texts"][0]["facts"] = copy.deepcopy(doc["texts"][0]["facts"])
        doc["texts"][0]["facts"]["days_open"] += 1
        errs = run_check(doc)
        self.assertTrue(any("facts differ" in e for e in errs), errs)

    def test_missing_provenance(self):
        doc = doc_with(GOOD["reason"])
        del doc["texts"][0]["provenance"]["model"]
        errs = run_check(doc)
        self.assertTrue(any("provenance" in e for e in errs), errs)

    def test_tem_nenhum(self):
        errs = run_check(doc_with("O vendedor tem nenhum {product} parado."))
        self.assertTrue(any("tem nenhum" in e for e in errs), errs)

    def test_repeated_three_words_in_one_sentence(self):
        errs = run_check(doc_with("Fale com o cliente hoje e volte a falar com o cliente amanhã."))
        self.assertTrue(any("repeated sequence" in e for e in errs), errs)

    def test_same_words_from_placeholders_are_fine(self):
        doc = doc_with("{days_left_phrase} e {days_left_phrase}.")
        self.assertEqual(run_check(doc), [])

    def test_phrase_starting_a_sentence_is_capitalised(self):
        doc = doc_with("{days_open_phrase}. {days_left_phrase}.")
        self.assertRegex(doc["texts"][0]["parts"]["reason"]["text"], r"^Aberto .*\. (Faltam|Falta|É) ")
        self.assertEqual(run_check(doc), [])


if __name__ == "__main__":
    unittest.main()
