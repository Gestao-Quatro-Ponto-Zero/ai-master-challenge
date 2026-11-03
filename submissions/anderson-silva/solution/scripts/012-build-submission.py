"""Assemble the submission folder from the project files (challenge 002). Local, no API.

The project stays the only source. This script copies into submissions/anderson-silva/ the documents, scripts,
results and requirements the submission needs, moves the audit trail to process-log/ and rewrites the links to it,
builds the submission index from docs/000-readme.md, and then checks every relative link and scans every text file
(including the compressed CSVs) for e-mail addresses, local paths and the API key. The hand-written files of the
submission (README, process log, screenshots, video, chat export) are never touched.

Usage:
  python 012-build-submission.py
"""
import gzip
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submissions" / "anderson-silva"
SOLUTION = SUBMISSION / "solution"
AUDIT_SOURCE = ROOT / "docs" / "001-audit-trail.md"
AUDIT_TARGET = SUBMISSION / "process-log" / "002-audit-trail.md"
INDEX_SOURCE = ROOT / "docs" / "000-readme.md"
INDEX_TARGET = SUBMISSION / "docs" / "001-indice.md"
ENV_PATH = ROOT / ".env"
DOCS = ["003-arquitetura-fluxo-atendimento.md", "004-proposta-automacao.md", "005-diagnostico-operacional.md",
        "006-prototipo.md"]
SINGLE_FILES = {"requirements.txt": "solution/requirements.txt", ".gitignore": "solution/.gitignore",
                "docs/001-audit-trail.md": "process-log/002-audit-trail.md"}
LINK_REWRITES = {"](001-audit-trail.md": "](../../process-log/002-audit-trail.md"}
SUBMISSION_PREFIX = "submissions/anderson-silva/"
INDEX_ORDER = ["README.md", "docs/", "process-log/0", "process-log/screenshots/", "process-log/video/",
               "process-log/chat-exports/", "solution/docs/", "solution/scripts/", "solution/results/", "solution/"]
TEXT_SUFFIXES = {".md", ".py", ".json", ".csv", ".txt", ""}
SCAN_PATTERNS = {"e-mail": re.compile(r"[\w.+-]+@[\w-]+\.[A-Za-z]{2,}"),
                 "caminho local": re.compile(r"/(?:Users|Volumes|home)/[\w.-]+/"),
                 "chave do OpenRouter": re.compile(r"sk-or-[A-Za-z0-9-]{20,}")}
LINK = re.compile(r"\]\(([^)\s]+)\)")


def read_api_key():
    if not ENV_PATH.exists():
        return None
    for line in ENV_PATH.read_text().splitlines():
        name, _, value = line.partition("=")
        if name.strip() == "OPENROUTER_API_KEY" and value.strip():
            return value.strip()
    return None


def clean_generated():
    # Only the generated parts are removed; everything else in the submission is hand-written.
    if SOLUTION.exists():
        shutil.rmtree(SOLUTION)
    for path in (AUDIT_TARGET, INDEX_TARGET):
        path.unlink(missing_ok=True)


def copy_files():
    (SOLUTION / "docs").mkdir(parents=True)
    for name in DOCS:
        text = (ROOT / "docs" / name).read_text(encoding="utf-8")
        for old, new in LINK_REWRITES.items():
            text = text.replace(old, new)
        (SOLUTION / "docs" / name).write_text(text, encoding="utf-8")
    for folder in ("scripts", "results"):
        (SOLUTION / folder).mkdir()
        for path in sorted((ROOT / folder).iterdir()):
            if path.is_file() and not path.name.startswith("."):
                shutil.copy2(path, SOLUTION / folder / path.name)
    for source, target in SINGLE_FILES.items():
        (SUBMISSION / target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / source, SUBMISSION / target)


def submission_path(project_path):
    if project_path in SINGLE_FILES:
        return SINGLE_FILES[project_path]
    if project_path.startswith(SUBMISSION_PREFIX):
        return project_path[len(SUBMISSION_PREFIX):]
    folder, _, name = project_path.partition("/")
    if folder == "docs" and name in DOCS or folder in ("scripts", "results"):
        return f"solution/{project_path}"
    return None


def order_key(path):
    return next(index for index, prefix in enumerate(INDEX_ORDER + [""]) if path.startswith(prefix)), path


def build_index():
    rows = {}
    for line in INDEX_SOURCE.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\| \[([^\]]+)\]\([^)]*\) \| (.*) \|$", line)
        if not match:
            continue
        target = submission_path(match.group(1))
        if target and target not in rows and (SUBMISSION / target).is_file():
            rows[target] = match.group(2)
    lines = ["# Índice da submissão", "",
             "Todos os arquivos desta pasta. Gerado pelo `solution/scripts/012-build-submission.py` a partir do índice"
             " do projeto; o que ler primeiro está no [README](../README.md).", "",
             "| Arquivo | O que é |", "|---|---|"]
    lines += [f"| [{path}](../{path}) | {rows[path]} |" for path in sorted(rows, key=order_key)]
    INDEX_TARGET.parent.mkdir(exist_ok=True)
    INDEX_TARGET.write_text("\n".join(lines) + "\n", encoding="utf-8")
    missing = sorted(str(path.relative_to(SUBMISSION)) for path in SUBMISSION.rglob("*")
                     if path.is_file() and path.name != ".DS_Store" and str(path.relative_to(SUBMISSION)) not in rows
                     and path != INDEX_TARGET)
    return len(rows), missing


def broken_links():
    broken = []
    for page in SUBMISSION.rglob("*.md"):
        for target in LINK.findall(page.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            if not (page.parent / target.split("#")[0]).exists():
                broken.append(f"{page.relative_to(SUBMISSION)} -> {target}")
    return broken


def read_text(path):
    if path.suffix == ".gz":
        return gzip.decompress(path.read_bytes()).decode("utf-8", errors="replace")
    if path.suffix in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8", errors="replace")
    return None


def scan(api_key):
    hits = []
    for path in sorted(SUBMISSION.rglob("*")):
        text = read_text(path) if path.is_file() else None
        if text is None:
            continue
        for label, pattern in SCAN_PATTERNS.items():
            found = pattern.findall(text)
            if found:
                hits.append(f"{path.relative_to(SUBMISSION)}: {len(found)} {label}")
        if api_key and api_key in text:
            hits.append(f"{path.relative_to(SUBMISSION)}: valor da chave")
    return hits


def main():
    clean_generated()
    copy_files()
    indexed, missing = build_index()
    files = [path for path in SUBMISSION.rglob("*") if path.is_file() and path.name != ".DS_Store"]
    print(f"Arquivos na submissão: {len(files)}, {sum(path.stat().st_size for path in files) / 1e6:.2f} MB")
    for folder in ("README.md", "docs", "process-log", "solution"):
        size = sum(path.stat().st_size for path in files if path.relative_to(SUBMISSION).parts[0] == folder)
        print(f"  {folder}: {size / 1e6:.2f} MB")
    print(f"Índice: {indexed} arquivos; sem descrição no índice do projeto: {missing or 'nenhum'}")
    broken = broken_links()
    print(f"Links relativos quebrados: {broken or 'nenhum'}")
    hits = scan(read_api_key())
    print(f"Varredura de e-mail, caminho local e chave: {hits or 'nada encontrado'}")


if __name__ == "__main__":
    main()
