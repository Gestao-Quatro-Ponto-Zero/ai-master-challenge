#!/usr/bin/env python3
"""Check the foundation's explicit contracts and version its local evidence.

Python 3.12 standard library only. This is not a general Markdown/YAML validator
or a semantic review of arbitrary prose. Historical process logs are not read.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = "docs/review-evidence/foundation-current.json"
DOCUMENTS = (
    "AGENTS.md", "CLAUDE.md", "PROJECT_STATUS.md", "README.md",
    "execution/plan.md", "execution/backlog.md", "docs/architecture-review.md",
    "docs/validation-strategy.md", "docs/foundation-controls.md",
    "knowledge/index.md", "knowledge/challenge-context.md",
    "knowledge/knowledge-workflow.md",
)
CHALLENGE_PATTERNS = {
    "AGENTS.md": r"Challenge (\d{3}) is selected",
    "PROJECT_STATUS.md": r"Selected challenge: \*\*(\d{3})",
    "README.md": r"^# Challenge (\d{3})\b",
    "knowledge/challenge-context.md": r"The user selected Challenge (\d{3})\b",
}


def dependencies(root):
    """Operational inputs only; recruitment archives are not execution context."""
    names = set(DOCUMENTS) | {".gitignore", "docs/review-evidence/foundation-tests.txt"}
    for pattern in ("knowledge/*.md", "scripts/*.py", "tests/*.py"):
        names.update(p.relative_to(root).as_posix() for p in root.glob(pattern))
    return sorted(names)


def local_file(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Input outside submission: {name}")
    return path


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def check_documents(root, pending_paths=()):
    errors = []
    names = [n for n in dependencies(root) if n.endswith(".md")]
    documents = {}
    for name in names:
        try:
            documents[name] = local_file(root, name).read_text(encoding="utf-8")
        except (OSError, ValueError) as error:
            errors.append(f"{name}: {error}")

    context = documents.get("knowledge/challenge-context.md", "")
    owner = re.findall(r'^challenge_id: "(\d{3})"$', context, re.M)
    if len(owner) != 1:
        errors.append("knowledge/challenge-context.md: expected one challenge_id authority")
    else:
        for name, pattern in CHALLENGE_PATTERNS.items():
            found = re.findall(pattern, documents.get(name, ""), re.M)
            if found != owner:
                errors.append(f"{name}: challenge conflict/missing declaration; "
                              f"owner={owner[0]}, found={found}")

    links = 0
    for name, content in documents.items():
        # Check inline links and OKF resource paths; anchors are outside scope.
        targets = re.findall(r"(?<!!)\[[^\]\n]+\]\(([^)\s]+)\)", content)
        targets += re.findall(r"^\s+resource: (\S+)$", content, re.M)
        for target in targets:
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or not parsed.path:
                continue
            links += 1
            path = root / Path(name).parent / unquote(parsed.path)
            if not path.exists() and path.resolve() not in pending_paths:
                errors.append(f"{name}: missing local link {target}")

    for name in names:
        if not name.startswith("knowledge/"):
            continue
        content = documents.get(name, "")
        match = re.match(r"\A---\n(.*?)\n---\n", content, re.S)
        header = match[1] if match else ""
        required = r'^okf_version: "0\.2"$' if name == "knowledge/index.md" else r"^type: \S.*$"
        if not re.search(required, header, re.M):
            errors.append(f"{name}: missing minimum OKF header (not full conformance)")

    review = documents.get("docs/architecture-review.md", "")
    ids = re.findall(r"^\| (F\d{2}) \|", review, re.M)
    if ids != [f"F{i:02}" for i in range(1, 8)]:
        errors.append("docs/architecture-review.md: expected one official F01–F07 table")
    plan = documents.get("execution/plan.md", "")
    tasks = re.findall(r"^- \[[ x]\] (\w\d{2}) —", plan, re.M)
    if "V00" not in tasks or "I01" not in tasks or tasks.index("V00") > tasks.index("I01"):
        errors.append("execution/plan.md: V00 must precede I01")

    return errors, {"markdown_documents": len(documents), "local_file_links": links,
                    "challenge_id": owner[0] if len(owner) == 1 else None}


def capture(root, extra_inputs):
    names = sorted(set(dependencies(root)) | set(extra_inputs))
    return {name: digest(local_file(root, name)) for name in names}


def check_receipt(root, receipt):
    errors = []
    try:
        saved = json.loads(local_file(root, receipt).read_text(encoding="utf-8"))
        if saved.get("schema_version") != 1:
            raise ValueError("unsupported receipt schema")
        extra = saved["extra_inputs"]
        previous = saved["sha256"]
        if not isinstance(extra, list) or not isinstance(previous, dict):
            raise ValueError("invalid dependency manifest")
        names = set(dependencies(root)) | set(extra)
        for name in sorted(names | set(previous)):
            path = local_file(root, name)
            if name not in names or name not in previous:
                errors.append(f"STALE: dependency membership changed: {name}")
            elif not path.is_file():
                errors.append(f"STALE: input missing: {name}")
            elif digest(path) != previous[name]:
                errors.append(f"STALE: input changed: {name}")
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(f"Receipt unavailable/invalid: {error}")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--receipt", default=RECEIPT, help="Path relative to submission")
    parser.add_argument("--record", action="store_true", help="Explicitly record a new checked version")
    parser.add_argument("--input", action="append", default=[], help="Additional data/rule/model file to fingerprint")
    args = parser.parse_args(argv)
    if args.input and not args.record:
        parser.error("--input requires --record; normal checks use the saved manifest")
    root = args.root.resolve()
    try:
        receipt_path = local_file(root, args.receipt)
        if receipt_path.relative_to(root).as_posix() in set(dependencies(root)) | set(args.input):
            raise ValueError("Receipt cannot also be its own input")
        errors, summary = check_documents(root, {receipt_path} if args.record else set())
        if not errors and args.record:
            snapshot = capture(root, args.input)
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(json.dumps({
                "schema_version": 1,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "actor": "automated-local-check; no human verification implied",
                "scope": "Explicit document contracts, file links, minimum OKF fields and input hashes; not model/data quality or arbitrary semantic consistency",
                "checks": summary,
                "extra_inputs": sorted(set(args.input)),
                "sha256": snapshot,
            }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        elif not args.record:
            errors.extend(check_receipt(root, args.receipt))
    except (OSError, ValueError, TypeError) as error:
        errors = [str(error)]
        summary = {}
    print(json.dumps({"passed": not errors, "checks": summary, "errors": errors},
                     indent=2, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
