"""Validate the evaluator-facing JourneyGraph process-evidence package.

The validator is dependency-free, deterministic, and writes its own JSON and
Markdown reports. It checks repository structure and evidence contracts; it
does not execute analytical or dashboard code.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SCRIPT_PATH = Path(__file__).resolve()
SUBMISSION_ROOT = SCRIPT_PATH.parents[2]
REPO_ROOT = SCRIPT_PATH.parents[4]
PROCESS_ROOT = SUBMISSION_ROOT / "process-log"
REPORT_ROOT = SUBMISSION_ROOT / "solution" / "reports"
README_PATH = SUBMISSION_ROOT / "README.md"
DOC_INDEX_PATH = SUBMISSION_ROOT / "docs" / "README.md"
JSON_REPORT_PATH = REPORT_ROOT / "process-evidence-validation.json"
MD_REPORT_PATH = REPORT_ROOT / "process-evidence-validation.md"

PROCESS_DOCUMENTS = {
    "HUMAN_JUDGMENT.md": (
        "# Human Judgment in JourneyGraph",
        "## Purpose",
        "## Decision Framework",
        "## Key Human Decisions",
        "## Limitations",
    ),
    "AI_TRACE.md": (
        "# AI Collaboration Trace",
        "## Scope",
        "## Tools",
        "## Phase-by-Phase Trace",
        "## Prompt Evidence",
        "## Verification Model",
        "## Limitations of the Trace",
    ),
    "AI_ERRORS_AND_CORRECTIONS.md": (
        "# AI and Implementation Errors Corrected During JourneyGraph",
        "## Attribution Policy",
        "## Corrected Errors and Risks",
        "## Limitations",
    ),
    "REJECTED_HYPOTHESES.md": (
        "# Rejected Hypotheses and Approaches",
        "## Purpose",
        "## Rejection Register",
        "## Limitations",
    ),
    "TRADE_OFFS.md": (
        "# Engineering and Product Trade-offs",
        "## Decision Matrix",
        "## Limitations",
    ),
    "HUMAN_INTERVENTION_TIMELINE.md": (
        "# Human Intervention Timeline",
        "## Reading the Timeline",
        "## Timeline",
        "## Coverage and Limitations",
    ),
    "EVIDENCE_MAP.md": (
        "# JourneyGraph Process Evidence Map",
        "## Purpose",
        "## Evidence Register",
        "## Validation Boundary",
    ),
}

REQUIRED_ID_SETS = {
    "HUMAN_JUDGMENT.md": {f"HJ-{number:03d}" for number in range(1, 19)},
    "AI_ERRORS_AND_CORRECTIONS.md": {
        f"AEC-{number:03d}" for number in range(1, 17)
    },
    "REJECTED_HYPOTHESES.md": {f"RH-{number:03d}" for number in range(1, 14)},
    "EVIDENCE_MAP.md": {f"EV-HJ-{number:03d}" for number in range(1, 16)},
}

PROHIBITED_LANGUAGE = (
    "AI decided",
    "AI determined",
    "AI autonomously",
    "AI proved",
    "AI discovered the truth",
    "fully autonomous",
    "without human intervention",
    "guaranteed",
    "caused churn",
    "revenue saved",
    "best action",
    "predicted churn",
)

PLACEHOLDER_PATTERN = re.compile(
    r"\b(?:TODO|TBD|TK|FIXME|PLACEHOLDER)\b|\?\?\?", re.IGNORECASE
)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
COMMIT_PATTERN = re.compile(r"(?<![0-9a-f])([0-9a-f]{40})(?![0-9a-f])")
ID_PATTERN = re.compile(r"\b(?:HJ|AEC|RH)-\d{3}\b|\bEV-HJ-\d{3}\b")

PLANNED_REPORTS = {
    JSON_REPORT_PATH.resolve(),
    MD_REPORT_PATH.resolve(),
}

ALLOWED_CHANGED_PATHS = (
    "submissions/carlos-henrique/.gitattributes",
    "submissions/carlos-henrique/process-log/",
    "submissions/carlos-henrique/README.md",
    "submissions/carlos-henrique/docs/README.md",
    "submissions/carlos-henrique/solution/app/package.json",
    "submissions/carlos-henrique/solution/app/package-lock.json",
    "submissions/carlos-henrique/solution/scripts/build_dashboard_data.py",
    "submissions/carlos-henrique/solution/scripts/validate_final_submission.py",
    "submissions/carlos-henrique/solution/scripts/validate_process_evidence.py",
    "submissions/carlos-henrique/solution/reports/",
    "submissions/carlos-henrique/solution/reports/process-evidence-validation.json",
    "submissions/carlos-henrique/solution/reports/process-evidence-validation.md",
    "submissions/carlos-henrique/solution/reports/process-evidence-adversarial-review.md",
    "submissions/carlos-henrique/solution/reports/evaluator-process-evidence-test.md",
)


@dataclass(frozen=True)
class Check:
    """One deterministic validation result."""

    check_id: str
    status: str
    detail: str


def read_text(path: Path) -> str:
    """Read UTF-8 Markdown with a clear exception for missing files."""

    return path.read_text(encoding="utf-8")


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    """Run a read-only Git command from the repository root."""

    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def add_check(checks: list[Check], check_id: str, ok: bool, detail: str) -> None:
    """Append a PASS or BLOCKED check."""

    checks.append(Check(check_id, "PASS" if ok else "BLOCKED", detail))


def document_existence_and_headings(checks: list[Check]) -> dict[Path, str]:
    """Validate document existence and exact required headings."""

    texts: dict[Path, str] = {}
    for filename, headings in PROCESS_DOCUMENTS.items():
        path = PROCESS_ROOT / filename
        exists = path.is_file()
        add_check(checks, f"document.{filename}.exists", exists, str(path.relative_to(REPO_ROOT)))
        if not exists:
            continue
        text = read_text(path)
        texts[path] = text
        missing = [heading for heading in headings if heading not in text]
        add_check(
            checks,
            f"document.{filename}.headings",
            not missing,
            "all required headings present" if not missing else f"missing: {missing}",
        )
    return texts


def validate_identifiers(checks: list[Check], texts: dict[Path, str]) -> None:
    """Check exact identifier sets and uniqueness in their canonical files."""

    for filename, required in REQUIRED_ID_SETS.items():
        path = PROCESS_ROOT / filename
        text = texts.get(path, "")
        if filename == "EVIDENCE_MAP.md":
            found = re.findall(r"(?m)^\| (EV-HJ-\d{3}) \|", text)
        else:
            found = re.findall(
                r"(?m)^### ((?:HJ|AEC|RH)-\d{3})\b", text
            )
        relevant = [identifier for identifier in found if identifier in required]
        exact = set(relevant) == required
        unique = len(relevant) == len(set(relevant))
        add_check(
            checks,
            f"ids.{filename}.exact",
            exact,
            f"required={len(required)} found={len(set(relevant))}",
        )
        add_check(
            checks,
            f"ids.{filename}.unique",
            unique,
            f"occurrences={len(relevant)} unique={len(set(relevant))}",
        )


def resolve_link(source: Path, raw_target: str) -> Path | None:
    """Resolve one local Markdown link, ignoring URLs and same-page anchors."""

    target = raw_target.strip().split("#", 1)[0]
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return None
    return (source.parent / target).resolve()


def validate_links(checks: list[Check], sources: Iterable[Path]) -> None:
    """Validate all relative Markdown link targets."""

    checked = 0
    broken: list[str] = []
    for source in sources:
        if not source.is_file():
            continue
        for raw_target in MARKDOWN_LINK_PATTERN.findall(read_text(source)):
            target = resolve_link(source, raw_target)
            if target is None:
                continue
            checked += 1
            if not target.exists() and target not in PLANNED_REPORTS:
                broken.append(f"{source.relative_to(REPO_ROOT)} -> {raw_target}")
    add_check(
        checks,
        "links.internal",
        not broken,
        f"checked={checked}; broken={broken}" if broken else f"checked={checked}; broken=0",
    )


def validate_commits(checks: list[Check], texts: dict[Path, str]) -> None:
    """Confirm every full commit hash cited by the process package exists."""

    commits = sorted({match for text in texts.values() for match in COMMIT_PATTERN.findall(text)})
    missing: list[str] = []
    for commit in commits:
        result = run_git("cat-file", "-e", f"{commit}^{{commit}}")
        if result.returncode != 0:
            missing.append(commit)
    add_check(
        checks,
        "commits.references",
        bool(commits) and not missing,
        f"checked={len(commits)}; missing={missing}" if missing else f"checked={len(commits)}; missing=0",
    )


def split_heading_blocks(text: str, prefix: str) -> list[str]:
    """Return level-three heading blocks beginning with an identifier prefix."""

    pattern = re.compile(
        rf"(?ms)^### ({re.escape(prefix)}\d{{3}})\b.*?(?=^### |^## |\Z)"
    )
    return [match.group(0) for match in pattern.finditer(text)]


def validate_required_fields(checks: list[Check], texts: dict[Path, str]) -> None:
    """Check evidence per decision, validation per error, and rejection support."""

    human_text = texts.get(PROCESS_ROOT / "HUMAN_JUDGMENT.md", "")
    human_blocks = split_heading_blocks(human_text, "HJ-")
    human_fields = (
        "Context",
        "AI or implementation suggestion",
        "Human concern",
        "Final decision",
        "Evidence",
        "Impact",
        "Trade-off",
        "What would have happened otherwise",
    )
    missing_human = [
        block.splitlines()[0]
        for block in human_blocks
        if any(f"**{field}:**" not in block for field in human_fields)
    ]
    add_check(
        checks,
        "content.human_decision_fields",
        len(human_blocks) == 18 and not missing_human,
        f"blocks={len(human_blocks)}; incomplete={missing_human}",
    )

    error_text = texts.get(PROCESS_ROOT / "AI_ERRORS_AND_CORRECTIONS.md", "")
    error_blocks = split_heading_blocks(error_text, "AEC-")
    error_fields = (
        "Phase",
        "Initial output or suggestion",
        "Why it was wrong or insufficient",
        "How it was detected",
        "Human decision",
        "Correction",
        "Validation",
        "Residual risk",
    )
    missing_error = [
        block.splitlines()[0]
        for block in error_blocks
        if any(f"**{field}:**" not in block for field in error_fields)
    ]
    add_check(
        checks,
        "content.error_validation_fields",
        len(error_blocks) == 16 and not missing_error,
        f"blocks={len(error_blocks)}; incomplete={missing_error}",
    )

    rejection_text = texts.get(PROCESS_ROOT / "REJECTED_HYPOTHESES.md", "")
    rejection_blocks = split_heading_blocks(rejection_text, "RH-")
    rejection_fields = (
        "Hypothesis or approach",
        "Why it appeared plausible",
        "Evidence reviewed",
        "Reason for rejection",
        "Decision",
        "Residual uncertainty",
    )
    missing_rejection = [
        block.splitlines()[0]
        for block in rejection_blocks
        if any(f"**{field}:**" not in block for field in rejection_fields)
    ]
    add_check(
        checks,
        "content.rejection_fields",
        len(rejection_blocks) == 13 and not missing_rejection,
        f"blocks={len(rejection_blocks)}; incomplete={missing_rejection}",
    )

    unsupported = [
        block.splitlines()[0]
        for block in [*human_blocks, *error_blocks, *rejection_blocks]
        if not MARKDOWN_LINK_PATTERN.search(block)
    ]
    add_check(
        checks,
        "content.claim_support",
        len(human_blocks) == 18
        and len(error_blocks) == 16
        and len(rejection_blocks) == 13
        and not unsupported,
        "47 decision/error/rejection blocks contain linked support"
        if not unsupported
        else f"unsupported={unsupported}",
    )


def validate_language_and_placeholders(checks: list[Check], texts: dict[Path, str]) -> None:
    """Block placeholders and language that assigns inappropriate AI autonomy."""

    placeholders: list[str] = []
    prohibited: list[str] = []
    for path, text in texts.items():
        if PLACEHOLDER_PATTERN.search(text):
            placeholders.append(path.name)
        lower_text = text.casefold()
        for phrase in PROHIBITED_LANGUAGE:
            if phrase.casefold() in lower_text:
                prohibited.append(f"{path.name}: {phrase}")
    add_check(
        checks,
        "language.placeholders",
        not placeholders,
        f"files={placeholders}" if placeholders else "zero placeholders",
    )
    add_check(
        checks,
        "language.ai_autonomy",
        not prohibited,
        f"occurrences={prohibited}" if prohibited else "zero prohibited occurrences",
    )


def validate_trace_and_limitations(checks: list[Check], texts: dict[Path, str]) -> None:
    """Check trace scope, verification cycle, prompt labeling, and limitations."""

    trace = texts.get(PROCESS_ROOT / "AI_TRACE.md", "")
    phases = (
        "Dataset audit",
        "Event log",
        "Churn analysis",
        "Survival analysis",
        "Journey mining",
        "Graph construction",
        "Watchlist",
        "Experiment Lab",
        "Dashboard",
        "Localization",
        "Submission documentation",
        "Cross-platform hardening",
    )
    missing_phases = [phase for phase in phases if phase not in trace]
    add_check(
        checks,
        "trace.phase_coverage",
        not missing_phases,
        "12 required phases present" if not missing_phases else f"missing={missing_phases}",
    )
    add_check(
        checks,
        "trace.reconstructed_prompt_label",
        trace.count("reconstructed instruction summary") >= 3,
        f"label_occurrences={trace.count('reconstructed instruction summary')}",
    )
    add_check(
        checks,
        "trace.verification_cycle",
        all(term in trace for term in ("AI suggestion", "human review", "test", "correction", "revalidation", "local commit")),
        "suggestion-to-commit cycle present",
    )
    missing_limits = [
        path.name for path, text in texts.items() if "limitation" not in text.casefold()
    ]
    add_check(
        checks,
        "content.limitations",
        not missing_limits,
        f"missing={missing_limits}" if missing_limits else "limitations present in all process documents",
    )


def validate_readme_and_index(checks: list[Check]) -> list[Path]:
    """Check evaluator entry points and the 120–180 word README summary."""

    sources: list[Path] = []
    readme_exists = README_PATH.is_file()
    index_exists = DOC_INDEX_PATH.is_file()
    add_check(checks, "integration.readme.exists", readme_exists, str(README_PATH.relative_to(REPO_ROOT)))
    add_check(checks, "integration.index.exists", index_exists, str(DOC_INDEX_PATH.relative_to(REPO_ROOT)))
    if readme_exists:
        sources.append(README_PATH)
        readme = read_text(README_PATH)
        section_match = re.search(
            r"(?ms)^## Human Judgment and AI Collaboration\s+(.*?)(?=^## |\Z)",
            readme,
        )
        section = section_match.group(1) if section_match else ""
        words = re.findall(r"\b[\wÀ-ÿ][\wÀ-ÿ'’-]*\b", re.sub(r"\([^)]*\)", "", section))
        add_check(
            checks,
            "integration.readme.section",
            bool(section_match),
            "section present" if section_match else "section missing",
        )
        add_check(
            checks,
            "integration.readme.word_count",
            120 <= len(words) <= 180,
            f"words={len(words)}; expected=120..180",
        )
        missing_links = [name for name in PROCESS_DOCUMENTS if name not in section]
        add_check(
            checks,
            "integration.readme.links",
            not missing_links,
            "all seven links present" if not missing_links else f"missing={missing_links}",
        )
    if index_exists:
        sources.append(DOC_INDEX_PATH)
        index = read_text(DOC_INDEX_PATH)
        missing_links = [name for name in PROCESS_DOCUMENTS if name not in index]
        has_columns = all(column in index for column in ("Title", "Purpose", "Audience", "Path"))
        add_check(
            checks,
            "integration.index.process_evidence",
            "## Process Evidence" in index and has_columns and not missing_links,
            "category, metadata columns, and seven links present"
            if not missing_links and has_columns
            else f"missing={missing_links}; metadata_columns={has_columns}",
        )
    return sources


def validate_review_reports(checks: list[Check]) -> list[Path]:
    """Check adversarial and five-minute evaluator review gates."""

    adversarial = REPORT_ROOT / "process-evidence-adversarial-review.md"
    evaluator = REPORT_ROOT / "evaluator-process-evidence-test.md"
    sources = [path for path in (adversarial, evaluator) if path.is_file()]
    adversarial_text = read_text(adversarial) if adversarial.is_file() else ""
    evaluator_text = read_text(evaluator) if evaluator.is_file() else ""
    add_check(
        checks,
        "review.adversarial",
        bool(adversarial_text)
        and "| CRITICAL | 0 |" in adversarial_text
        and "| HIGH | 0 |" in adversarial_text
        and "**PASS.**" in adversarial_text,
        "report exists; open CRITICAL=0; open HIGH=0; gate=PASS",
    )
    add_check(
        checks,
        "review.evaluator",
        bool(evaluator_text)
        and evaluator_text.count("| PASS |") == 7
        and "**PASS.**" in evaluator_text,
        f"report exists; question_passes={evaluator_text.count('| PASS |')}; gate=PASS",
    )
    return sources


def validate_evidence_map(checks: list[Check], texts: dict[Path, str]) -> None:
    """Check evidence-map rows for artifacts, commits, and status."""

    text = texts.get(PROCESS_ROOT / "EVIDENCE_MAP.md", "")
    rows = [line for line in text.splitlines() if line.startswith("| EV-HJ-")]
    malformed = [
        line for line in rows if line.count("[") < 2 or "`" not in line or "| PASS |" not in line
    ]
    add_check(
        checks,
        "content.evidence_map_rows",
        len(rows) == 15 and not malformed,
        f"rows={len(rows)}; malformed={len(malformed)}",
    )


def validate_tradeoffs(checks: list[Check], texts: dict[Path, str]) -> None:
    """Check the twelve required trade-off rows and metadata columns."""

    text = texts.get(PROCESS_ROOT / "TRADE_OFFS.md", "")
    rows = [
        line
        for line in text.splitlines()
        if line.startswith("|") and not line.startswith(("| Trade-off", "|---"))
    ]
    columns = (
        "Trade-off",
        "Option A",
        "Option B",
        "Decision",
        "Benefit",
        "Cost",
        "Why acceptable",
        "Revisit condition",
    )
    add_check(
        checks,
        "content.tradeoffs",
        len(rows) == 12 and all(column in text for column in columns),
        f"rows={len(rows)}; required=12",
    )


def validate_change_scope(checks: list[Check]) -> None:
    """Fail if the current worktree contains files outside the documentary scope."""

    result = run_git("status", "--porcelain=v1", "--untracked-files=all")
    changed: list[str] = []
    outside: list[str] = []
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            raw_path = line[3:]
            if " -> " in raw_path:
                raw_path = raw_path.split(" -> ", 1)[1]
            path = raw_path.strip('"').replace("\\", "/")
            changed.append(path)
            if not any(path == allowed or path.startswith(allowed) for allowed in ALLOWED_CHANGED_PATHS):
                outside.append(path)
    add_check(
        checks,
        "scope.changed_files",
        result.returncode == 0 and not outside,
        f"outside={outside}" if outside else "outside=0",
    )


def overall_status(checks: list[Check]) -> str:
    """Calculate the gate status from deterministic check results."""

    if any(check.status == "BLOCKED" for check in checks):
        return "BLOCKED"
    if any(check.status == "PASS_WITH_WARNINGS" for check in checks):
        return "PASS_WITH_WARNINGS"
    return "PASS"


def write_reports(checks: list[Check], status: str) -> None:
    """Write stable JSON and Markdown validation reports."""

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    counts = {
        value: sum(check.status == value for check in checks)
        for value in ("PASS", "PASS_WITH_WARNINGS", "BLOCKED")
    }
    payload = {
        "validator": "JourneyGraph process evidence validator",
        "version": "1.0.0",
        "status": status,
        "scope": "submissions/carlos-henrique",
        "counts": counts,
        "checks": [check.__dict__ for check in checks],
        "limitations": [
            "The validator checks repository evidence structure and traceability, not private reasoning.",
            "Semantic support remains bounded to the linked historical artifacts and commits.",
            "Future operational use requires a separate human review and validation cycle.",
        ],
    }
    JSON_REPORT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines = [
        "# Process Evidence Validation",
        "",
        f"**Gate: {status}.**",
        "",
        "## Summary",
        "",
        f"- PASS: {counts['PASS']}",
        f"- PASS_WITH_WARNINGS: {counts['PASS_WITH_WARNINGS']}",
        f"- BLOCKED: {counts['BLOCKED']}",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for check in checks:
        detail = check.detail.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| `{check.check_id}` | {check.status} | {detail} |")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "This validator checks versioned structure, identifiers, links, commits, attribution fields, language, and evaluator integration. It does not infer private reasoning or extend historical evidence to a live operating context. Future customer action, model use, or experiment execution requires a separate human-approved gate.",
            "",
        ]
    )
    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    """Run all gates, write reports, and return a fail-closed exit code."""

    checks: list[Check] = []
    texts = document_existence_and_headings(checks)
    validate_identifiers(checks, texts)
    validate_required_fields(checks, texts)
    validate_trace_and_limitations(checks, texts)
    validate_evidence_map(checks, texts)
    validate_tradeoffs(checks, texts)
    integration_sources = validate_readme_and_index(checks)
    review_sources = validate_review_reports(checks)
    language_texts = dict(texts)
    for source in [*integration_sources, *review_sources]:
        language_texts[source] = read_text(source)
    validate_language_and_placeholders(checks, language_texts)
    validate_links(
        checks,
        [*texts.keys(), *integration_sources, *review_sources],
    )
    validate_commits(checks, texts)
    validate_change_scope(checks)
    status = overall_status(checks)
    write_reports(checks, status)
    print(f"PROCESS_EVIDENCE_VALIDATION={status}")
    print(f"CHECKS={len(checks)}")
    print(f"REPORT_JSON={JSON_REPORT_PATH.relative_to(REPO_ROOT)}")
    print(f"REPORT_MD={MD_REPORT_PATH.relative_to(REPO_ROOT)}")
    return 0 if status in {"PASS", "PASS_WITH_WARNINGS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
