"""Check of the stored texts against the facts (docs/contrato-ia.md).

    python check.py            # checks textos.json beside this file; exit 0 only if all pass

A text fails when: (1) a placeholder is not in its facts; (2) a digit or a number
word is left outside a placeholder; (3) a name of the dataset is typed outside a
placeholder; (4) a judgment that is not in the facts appears; (5) `text` is not
the template filled with `facts`, or the provenance is missing; (6) a fact
differs from the score file for that target.

Limit, stated: the lists below are word lists and a word list does not catch
everything. A paraphrased judgment ("vai dar certo") or the article "um/uma"
used as a number passes. The numbers and the names are the strong part.
"""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import facts as F  # noqa: E402
from render import PLACEHOLDER, render, render_mask  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = F.SOLUTION / "data"
PROMPT = HERE / "prompt.md"
TEXTOS = HERE / "textos.json"

PARTS = {"deal": ("reason", "next_step"), "briefing": ("body",), "manager": ("body",)}
PROVENANCE = ("model", "generated_on", "prompt_sha256", "batch")
META = ("monday", "score_file", "prompt_file", "prompt_sha256", "command")

NUMBER_WORDS = (r"dois|duas|três|tres|quatro|cinco|seis|sete|oito|nove|dez|onze|doze|treze|"
                r"quinze|vinte|trinta|quarenta|cinquenta|cem|cento|mil|metade|dezena|dúzia|duzia")
JUDGMENTS = [
    r"%", r"por cento", r"chances?", r"probabilidade", r"prov[áa]ve(l|is)", r"provavelmente",
    r"garanti\w*", r"promissor\w*", r"quentes?", r"excelente\w*", r"[óo]tim[oa]s?",
    r"certeza", r"certamente", r"sem d[úu]vida", r"vai fechar", r"v[ãa]o fechar",
    r"fecha(m)? mais", r"melhor(es)?", r"pior(es)?", r"urgente\w*", r"grande oportunidade",
    r"boa oportunidade", r"oportunidade de ouro", r"fortes?", r"fraco\w*", r"arriscad\w*",
    r"imperd\w*", r"tende(m)? a", r"alta prioridade", r"vale a pena", r"bom neg[óo]cio",
]
JUDGMENT_RE = re.compile(r"(?<!\w)(" + "|".join(JUDGMENTS) + r")(?!\w)|%", re.IGNORECASE)
NUMBER_WORD_RE = re.compile(r"(?<!\w)(" + NUMBER_WORDS + r")(?!\w)", re.IGNORECASE)
TEM_NENHUM_RE = re.compile(r"(?<!\w)tem nenhum", re.IGNORECASE)
SENTENCE_END = re.compile(r"[.!?]+(?: +|$)")
WORD_RE = re.compile(r"\w+")
COOLING_RE = re.compile(r"esfri\w*", re.IGNORECASE)


def load_names():
    """Names of the dataset: (phrases matched whole, case-insensitive; tokens matched as typed)."""
    phrases, tokens = set(), set()
    with open(DATA / "sales_teams.csv", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            for n in (r["sales_agent"], r["manager"]):
                phrases.add(n)
                tokens.update(t for t in re.split(r"[\s\-']+", n) if len(t) >= 4)
    with open(DATA / "accounts.csv", encoding="utf-8", newline="") as fh:
        phrases.update(r["account"] for r in csv.DictReader(fh))
    with open(DATA / "products.csv", encoding="utf-8", newline="") as fh:
        phrases.update(r["product"] for r in csv.DictReader(fh))
    return phrases, tokens


def _name_hits(text, names):
    phrases, tokens = names
    hits = [p for p in phrases if re.search(r"(?<!\w)" + re.escape(p) + r"(?!\w)", text, re.I)]
    hits += [t for t in tokens if re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", text)]
    return sorted(set(hits))


def wording_errors(label, template, facts):
    """'tem nenhum', and the same three words twice in one sentence (only a trigram typed
    wholly in the template counts: a list of three deals repeats filled words legitimately)."""
    text, mask = render_mask(template, facts)
    errs = []
    if TEM_NENHUM_RE.search(text):
        errs.append(f"{label}: 'tem nenhum' (a phrase must not follow a verb)")
    start = 0
    for end in [m.end() for m in SENTENCE_END.finditer(text)] + [len(text)]:
        words = [(w.group(0).lower(), any(mask[start + w.start():start + w.end()]))
                 for w in WORD_RE.finditer(text[start:end])]
        seen = set()
        for i in range(len(words) - 2):
            tri = tuple(w for w, _ in words[i:i + 3])
            if tri in seen and all(lit for _, lit in words[i:i + 3]):
                errs.append(f"{label}: repeated sequence '{' '.join(tri)}' in one sentence")
                break
            seen.add(tri)
        start = end
    return errs


def check_part(label, kind, part, facts, names):
    """Rules 1 to 5 (text side) for one part."""
    errs = []
    if not isinstance(part, dict) or not isinstance(part.get("template"), str) \
            or not isinstance(part.get("text"), str):
        return [f"{label}: part without template and text"]
    template = part["template"]
    keys = PLACEHOLDER.findall(template)
    bad = [k for k in keys if k not in facts]
    for k in bad:
        errs.append(f"{label}: placeholder {{{k}}} not in facts")
    outside = PLACEHOLDER.sub(" ", template)
    if "{" in outside or "}" in outside:
        errs.append(f"{label}: unbalanced brace")
    if re.search(r"\d", outside):
        errs.append(f"{label}: digit outside a placeholder")
    for m in NUMBER_WORD_RE.finditer(outside):
        errs.append(f"{label}: number word '{m.group(0)}' outside a placeholder")
    for n in _name_hits(outside, names):
        errs.append(f"{label}: dataset name '{n}' outside a placeholder")
    for m in JUDGMENT_RE.finditer(outside):
        errs.append(f"{label}: judgment '{m.group(0)}' not in the facts")
    cooling_ok = kind != "deal" and facts.get("cooling", 0) > 0
    for m in COOLING_RE.finditer(outside):
        if not cooling_ok:
            errs.append(f"{label}: '{m.group(0)}' outside a placeholder (only {{cooling_label}} may say it)")
    if not bad:
        errs += wording_errors(label, template, facts)
        if part["text"] != render(template, facts):
            errs.append(f"{label}: text is not the template filled with the facts")
    return errs


def check_entry(entry, targets, names, prompt_sha):
    eid = entry.get("id", "<no id>")
    errs = []
    kind = entry.get("kind")
    if kind not in PARTS:
        return [f"{eid}: unknown kind {kind!r}"]
    target = targets.get(eid)
    if target is None:
        return [f"{eid}: target not in the score file"]
    if target["kind"] != kind or entry.get("target") != target["target"]:
        errs.append(f"{eid}: kind or target differ from the score file")
    if entry.get("facts") != target["facts"]:
        diff = sorted(k for k in set(entry.get("facts", {})) | set(target["facts"])
                      if entry.get("facts", {}).get(k) != target["facts"].get(k))
        errs.append(f"{eid}: facts differ from the score file ({', '.join(diff)})")
    prov = entry.get("provenance") or {}
    missing = [k for k in PROVENANCE if prov.get(k) in (None, "")]
    if missing:
        errs.append(f"{eid}: provenance missing {', '.join(missing)}")
    if prov.get("prompt_sha256") and prov["prompt_sha256"] != prompt_sha:
        errs.append(f"{eid}: prompt_sha256 does not match prompt.md")
    parts = entry.get("parts")
    if not isinstance(parts, dict) or set(parts) != set(PARTS[kind]):
        return errs + [f"{eid}: parts must be exactly {', '.join(PARTS[kind])}"]
    for name in PARTS[kind]:
        errs += check_part(f"{eid}.{name}", kind, parts[name], target["facts"], names)
    return errs


def prompt_hash():
    return hashlib.sha256(PROMPT.read_bytes()).hexdigest()


def check_texts(path=TEXTOS, targets=None, names=None):
    """One string per failure; empty when all is well."""
    path = Path(path)
    if not path.exists():
        return [f"{path}: file not found"]
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        return [f"{path}: not valid JSON ({e})"]
    errs = []
    meta = doc.get("meta") or {}
    for k in META:
        if not meta.get(k):
            errs.append(f"meta missing {k}")
    if targets is None:
        targets = F.build_all()
    names = names or load_names()
    sha = prompt_hash() if PROMPT.exists() else None
    if sha is None:
        errs.append("prompt.md not found")
    if sha and meta.get("prompt_sha256") not in (None, "", sha):
        errs.append("meta prompt_sha256 does not match prompt.md")
    seen = set()
    for entry in doc.get("texts", []):
        if entry.get("id") in seen:
            errs.append(f"{entry.get('id')}: duplicated id")
        seen.add(entry.get("id"))
        errs += check_entry(entry, targets, names, sha)
    return errs


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else TEXTOS
    errs = check_texts(path)
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    n = len(doc.get("texts", []))
    for e in errs:
        print("FAIL", e)
    print(f"{n} texts, {len(errs)} failures")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
