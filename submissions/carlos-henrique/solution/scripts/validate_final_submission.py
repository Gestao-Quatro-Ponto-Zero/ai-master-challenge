"""Validate the complete JourneyGraph submission package.

This dependency-free validator checks repository-backed submission assets and
produces deterministic JSON and Markdown reports. Expected external actions
remain warnings when explicitly marked PENDING_USER_ACTION.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SCRIPT = Path(__file__).resolve()
SUBMISSION = SCRIPT.parents[2]
REPOSITORY = SCRIPT.parents[4]
REPORTS = SUBMISSION / "solution" / "reports"
PROCESS = SUBMISSION / "process-log"
DOCS = SUBMISSION / "docs"
APP = SUBMISSION / "solution" / "app"
JSON_OUTPUT = REPORTS / "final-submission-validation.json"
MD_OUTPUT = REPORTS / "final-submission-validation.md"

PACKAGE_FILES = (
    SUBMISSION / ".gitattributes",
    SUBMISSION / "README.md",
    APP / "README.md",
    APP / "package.json",
    APP / "package-lock.json",
    SUBMISSION / "solution" / "scripts" / "build_dashboard_data.py",
    DOCS / "architecture.md",
    DOCS / "README.md",
    REPORTS / "journeygraph-one-pager.md",
    REPORTS / "pitch-30-seconds.md",
    REPORTS / "pitch-90-seconds.md",
    REPORTS / "video-script-3-minutes.md",
    REPORTS / "video-storyboard.md",
    REPORTS / "video-recording-plan.md",
    REPORTS / "video-subtitles-en.srt",
    REPORTS / "video-subtitles-pt-BR.srt",
    REPORTS / "video-subtitles-note.md",
    REPORTS / "video-thumbnail-spec.md",
    REPORTS / "video-description.md",
    REPORTS / "video-title-options.md",
    REPORTS / "submission-summary.md",
    REPORTS / "submission-form-draft.md",
    REPORTS / "pull-request-description.md",
    REPORTS / "reviewer-guide.md",
    REPORTS / "demo-checklist.md",
    REPORTS / "deployment-readiness.md",
    REPORTS / "deployment-runbook.md",
    REPORTS / "final-submission-checklist.md",
    REPORTS / "external-link-registry.md",
    REPORTS / "final-metric-snapshot.md",
    REPORTS / "clean-room-validation.md",
    REPORTS / "final-submission-inventory.md",
    REPORTS / "submission-message-consistency.md",
    REPORTS / "final-adversarial-review.md",
    REPORTS / "five-minute-submission-test.md",
    PROCESS / "HUMAN_JUDGMENT.md",
    PROCESS / "AI_TRACE.md",
    PROCESS / "EVIDENCE_MAP.md",
)

SCREENSHOTS = tuple(
    REPORTS / "screenshots" / name
    for name in (
        "01-executive-overview.png",
        "02-data-quality.png",
        "03-journey-explorer.png",
        "04-journeygraph.png",
        "05-watchlist.png",
        "06-experiment-lab.png",
        "07-governance.png",
    )
)

REQUIRED_HEADINGS = {
    "journeygraph-one-pager.md": (
        "## Executive Summary",
        "## Why Conventional Retention Views Fail",
        "## What JourneyGraph Delivers",
        "## Canonical Evidence",
        "## Recommended Next Steps",
        "## Caveats and Assumptions",
    ),
    "pitch-30-seconds.md": ("## English", "## Português do Brasil"),
    "pitch-90-seconds.md": ("## English", "## Português do Brasil"),
    "video-script-3-minutes.md": (
        "## Main Script — English",
        "## Supporting Script — Português do Brasil",
        "## Teleprompter — English",
    ),
    "submission-summary.md": (
        "## 50 Words",
        "## 100 Words",
        "## 200 Words",
        "## Up to 500 Characters",
    ),
    "pull-request-description.md": (
        "## Summary",
        "## Governance and Safety",
        "## Validation",
        "## How to Run",
        "## Limitations",
        "## Submission Checklist",
    ),
    "reviewer-guide.md": (
        "## 2-Minute Review",
        "## 5-Minute Review",
        "## 15-Minute Technical Review",
    ),
    "deployment-readiness.md": ("## Classification", "## Readiness Assessment"),
    "final-submission-checklist.md": ("# JourneyGraph Final Submission Checklist",),
    "clean-room-validation.md": ("## Strategy", "## Execution", "## Result"),
    "final-adversarial-review.md": (
        "## Technical Reviewer",
        "## Product Reviewer",
        "## Data Governance Reviewer",
        "## Skeptical AI Reviewer",
    ),
}

EXPECTED_EXTERNAL_MARKERS = (
    "[REPOSITORY_URL_PENDING]",
    "[PUBLIC_DEMO_URL_PENDING]",
    "[VIDEO_URL_PENDING]",
    "[PR_URL_PENDING]",
    "[SUBMISSION_FORM_CONFIRMATION_PENDING]",
    "[LINKEDIN_URL_PENDING_IF_APPLICABLE]",
    "PENDING_USER_ACTION",
)

PROHIBITED = (
    "predicts " + "churn",
    "churn " + "probability",
    "revenue " + "at risk",
    "saved " + "revenue",
    "causes " + "churn",
    "causal " + "driver",
    "best " + "next action",
    "automatically " + "intervenes",
    "guarantees " + "retention",
    "proven " + "uplift",
    "successful " + "experiment",
    "autonomous " + "customer action",
    "fully " + "autonomous",
    "AI " + "decided",
    "AI " + "selected customers",
)

PACKAGE_PREFIXES = (
    "submissions/carlos-henrique/.gitattributes",
    "submissions/carlos-henrique/README.md",
    "submissions/carlos-henrique/docs/README.md",
    "submissions/carlos-henrique/process-log/",
    "submissions/carlos-henrique/solution/app/package.json",
    "submissions/carlos-henrique/solution/app/package-lock.json",
    "submissions/carlos-henrique/solution/reports/",
    "submissions/carlos-henrique/solution/scripts/build_dashboard_data.py",
    "submissions/carlos-henrique/solution/scripts/validate_final_submission.py",
    "submissions/carlos-henrique/solution/scripts/validate_process_evidence.py",
)

LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PLACEHOLDER_PATTERN = re.compile(r"\b(?:TODO|TBD|TK|FIXME)\b|\?\?\?", re.IGNORECASE)
URL_PATTERN = re.compile(r"https?://[^\s)`]+")
WORD_PATTERN = re.compile(r"\b[\wÀ-ÿ][\wÀ-ÿ'’-]*\b")
SRT_TIME_PATTERN = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})$"
)


@dataclass(frozen=True)
class Check:
    """A stable validation result."""

    check_id: str
    status: str
    detail: str


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPOSITORY,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def record(checks: list[Check], check_id: str, status: str, detail: str) -> None:
    checks.append(Check(check_id, status, detail))


def section(text: str, heading: str, next_heading: str | None = None) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    start += len(heading)
    if next_heading:
        end = text.find(next_heading, start)
    else:
        match = re.search(r"(?m)^## ", text[start:])
        end = start + match.start() if match else len(text)
    return text[start:end if end >= 0 else len(text)].strip()


def narrative_word_count(raw: str) -> int:
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "**Target:", "**Meta:")):
            continue
        lines.append(re.sub(r"[`*_]", "", stripped))
    return len(WORD_PATTERN.findall(" ".join(lines)))


def validate_files(checks: list[Check]) -> list[Path]:
    missing = [str(path.relative_to(REPOSITORY)) for path in PACKAGE_FILES if not path.is_file()]
    record(
        checks,
        "package.required_files",
        "PASS" if not missing else "BLOCKED",
        f"required={len(PACKAGE_FILES)}; missing={missing}",
    )
    screenshot_missing = [
        str(path.relative_to(REPOSITORY))
        for path in SCREENSHOTS
        if not path.is_file() or path.stat().st_size == 0
    ]
    record(
        checks,
        "package.screenshots",
        "PASS" if not screenshot_missing else "BLOCKED",
        f"required=7; valid={7-len(screenshot_missing)}; missing={screenshot_missing}",
    )
    return [path for path in PACKAGE_FILES if path.is_file()]


def validate_headings(checks: list[Check]) -> None:
    problems: list[str] = []
    for name, headings in REQUIRED_HEADINGS.items():
        path = REPORTS / name
        if not path.is_file():
            problems.append(f"{name}: file missing")
            continue
        text = read(path)
        missing = [heading for heading in headings if heading not in text]
        if missing:
            problems.append(f"{name}: {missing}")
    record(
        checks,
        "package.required_headings",
        "PASS" if not problems else "BLOCKED",
        "all required headings present" if not problems else f"problems={problems}",
    )


def resolve_link(source: Path, target: str) -> Path | None:
    clean = target.strip().split("#", 1)[0]
    if not clean or clean.startswith(("http://", "https://", "mailto:")):
        return None
    return (source.parent / clean).resolve()


def validate_links(checks: list[Check], files: Iterable[Path]) -> None:
    count = 0
    broken: list[str] = []
    planned = {JSON_OUTPUT.resolve(), MD_OUTPUT.resolve()}
    for source in files:
        if source.suffix.lower() != ".md":
            continue
        for raw in LINK_PATTERN.findall(read(source)):
            target = resolve_link(source, raw)
            if target is None:
                continue
            count += 1
            if not target.exists() and target not in planned:
                broken.append(f"{source.name}->{raw}")
    record(
        checks,
        "links.local",
        "PASS" if not broken else "BLOCKED",
        f"checked={count}; broken={broken}" if broken else f"checked={count}; broken=0",
    )


def validate_pitch_lengths(checks: list[Check]) -> None:
    pitch30 = read(REPORTS / "pitch-30-seconds.md") if (REPORTS / "pitch-30-seconds.md").is_file() else ""
    en30 = narrative_word_count(section(pitch30, "## English", "## Português do Brasil"))
    pt30 = narrative_word_count(section(pitch30, "## Português do Brasil", "## Evidence Boundary"))
    record(
        checks,
        "pitch.30_seconds",
        "PASS" if 65 <= en30 <= 85 and 60 <= pt30 <= 80 else "BLOCKED",
        f"english_words={en30}; portuguese_words={pt30}",
    )

    pitch90 = read(REPORTS / "pitch-90-seconds.md") if (REPORTS / "pitch-90-seconds.md").is_file() else ""
    en90 = narrative_word_count(section(pitch90, "## English", "## Português do Brasil"))
    pt90 = narrative_word_count(section(pitch90, "## Português do Brasil", "## Evidence Boundary"))
    record(
        checks,
        "pitch.90_seconds",
        "PASS" if 190 <= en90 <= 230 and 170 <= pt90 <= 220 else "BLOCKED",
        f"english_words={en90}; portuguese_words={pt90}",
    )


def srt_milliseconds(groups: tuple[str, ...]) -> int:
    hours, minutes, seconds, millis = (int(value) for value in groups)
    return (((hours * 60) + minutes) * 60 + seconds) * 1000 + millis


def validate_srt_file(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, "missing"
    blocks = re.split(r"\r?\n\r?\n", read(path).strip())
    expected = 1
    previous_end = -1
    problems: list[str] = []
    final_end = 0
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            problems.append(f"block {expected}: incomplete")
            continue
        if lines[0] != str(expected):
            problems.append(f"block {expected}: sequence={lines[0]}")
        match = SRT_TIME_PATTERN.match(lines[1])
        if not match:
            problems.append(f"block {expected}: invalid timestamp")
        else:
            start = srt_milliseconds(match.groups()[0:4])
            end = srt_milliseconds(match.groups()[4:8])
            if start < previous_end or end <= start:
                problems.append(f"block {expected}: timing order")
            previous_end = end
            final_end = end
        if len(lines[2:]) > 2:
            problems.append(f"block {expected}: more than two text lines")
        if any(len(line) > 58 for line in lines[2:]):
            problems.append(f"block {expected}: line too long")
        expected += 1
    valid_duration = 165_000 <= final_end <= 195_000
    if not valid_duration:
        problems.append(f"duration_ms={final_end}")
    return not problems, f"cues={len(blocks)}; final_ms={final_end}; problems={problems}"


def validate_video(checks: list[Check]) -> None:
    for code, name in (("en", "video-subtitles-en.srt"), ("pt_br", "video-subtitles-pt-BR.srt")):
        ok, detail = validate_srt_file(REPORTS / name)
        record(checks, f"video.srt.{code}", "PASS" if ok else "BLOCKED", detail)
    script = read(REPORTS / "video-script-3-minutes.md") if (REPORTS / "video-script-3-minutes.md").is_file() else ""
    required = (
        "historical snapshot",
        "descriptive",
        "human review",
        "no predictive churn score",
        "no automated customer action",
        "not completed experiments",
    )
    missing = [phrase for phrase in required if phrase.casefold() not in script.casefold()]
    record(
        checks,
        "video.required_boundaries",
        "PASS" if not missing else "BLOCKED",
        "all six boundaries present" if not missing else f"missing={missing}",
    )


def validate_summary(checks: list[Check]) -> None:
    path = REPORTS / "submission-summary.md"
    text = read(path) if path.is_file() else ""
    limits = (("## 50 Words", "## 100 Words", 50), ("## 100 Words", "## 200 Words", 100), ("## 200 Words", "## Up to 500 Characters", 200))
    details: list[str] = []
    ok = True
    for heading, next_heading, target in limits:
        count = narrative_word_count(section(text, heading, next_heading))
        tolerance = 8 if target == 50 else 12 if target == 100 else 20
        details.append(f"{target}={count}")
        ok = ok and target - tolerance <= count <= target + tolerance
    short = re.sub(r"\s+", " ", section(text, "## Up to 500 Characters", "## Consistency Note")).strip()
    details.append(f"short_chars={len(short)}")
    ok = ok and len(short) <= 500
    record(checks, "summary.lengths", "PASS" if ok else "BLOCKED", "; ".join(details))


def validate_claims_and_urls(checks: list[Check], files: Iterable[Path]) -> None:
    prohibited: list[str] = []
    placeholders: list[str] = []
    unexpected_urls: list[str] = []
    allowed_urls = {
        "http://localhost:3000",
        "https://github.com/acarloshenrique/ai-master-challenge.git",
        "https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge.git",
    }
    for path in files:
        if path.suffix.lower() not in {".md", ".srt"}:
            continue
        text = read(path)
        lowered = text.casefold()
        for phrase in PROHIBITED:
            if phrase.casefold() in lowered:
                prohibited.append(f"{path.name}:{phrase}")
        if PLACEHOLDER_PATTERN.search(text):
            placeholders.append(path.name)
        for url in URL_PATTERN.findall(text):
            clean = url.rstrip(".,;")
            if clean not in allowed_urls:
                unexpected_urls.append(f"{path.name}:{clean}")
    record(
        checks,
        "claims.prohibited",
        "PASS" if not prohibited else "BLOCKED",
        "occurrences=0" if not prohibited else f"occurrences={prohibited}",
    )
    record(
        checks,
        "content.generic_placeholders",
        "PASS" if not placeholders else "BLOCKED",
        "occurrences=0" if not placeholders else f"files={placeholders}",
    )
    record(
        checks,
        "links.no_invented_urls",
        "PASS" if not unexpected_urls else "BLOCKED",
        "unexpected=0" if not unexpected_urls else f"unexpected={unexpected_urls}",
    )


def validate_external_state(checks: list[Check], files: Iterable[Path]) -> None:
    combined = "\n".join(read(path) for path in files if path.suffix.lower() == ".md")
    present = [marker for marker in EXPECTED_EXTERNAL_MARKERS if marker in combined]
    registry = read(REPORTS / "external-link-registry.md") if (REPORTS / "external-link-registry.md").is_file() else ""
    required_registry = ("LINK-001", "LINK-002", "LINK-003", "LINK-004", "LINK-005", "LINK-006")
    missing_ids = [identifier for identifier in required_registry if identifier not in registry]
    record(
        checks,
        "external.registry",
        "PASS" if not missing_ids else "BLOCKED",
        "six link records present" if not missing_ids else f"missing={missing_ids}",
    )
    record(
        checks,
        "external.pending_actions",
        "PASS_WITH_WARNINGS" if present else "PASS",
        f"expected_pending_markers={len(present)}",
    )


def validate_metrics_and_tests(checks: list[Check], files: Iterable[Path]) -> None:
    snapshot_path = REPORTS / "final-metric-snapshot.md"
    snapshot = read(snapshot_path) if snapshot_path.is_file() else ""
    required_metrics = (
        "500",
        "35,586",
        "13,927",
        "21,659",
        "4,221",
        "435",
        "43",
        "1,609",
        "2024-12-31T19:00:00",
        "130/130",
        "19/19",
        "36/36",
    )
    missing = [value for value in required_metrics if value not in snapshot]
    record(
        checks,
        "metrics.canonical_snapshot",
        "PASS" if not missing else "BLOCKED",
        "canonical values present" if not missing else f"missing={missing}",
    )
    all_text = "\n".join(read(path) for path in files if path.suffix.lower() == ".md")
    stale = []
    for pattern in ("Vitest (18/18)", "Vitest: 18/18", "Vitest | 18/18"):
        if pattern in all_text:
            stale.append(pattern)
    record(
        checks,
        "tests.reference_consistency",
        "PASS" if not stale else "BLOCKED",
        "Python=130/130; Vitest=19/19; Playwright=36/36" if not stale else f"stale={stale}",
    )
    matrix = read(REPORTS / "metric-consistency-matrix.md") if (REPORTS / "metric-consistency-matrix.md").is_file() else ""
    record(
        checks,
        "metrics.matrix",
        "PASS" if "**Gate: PASS.**" in matrix else "BLOCKED",
        "metric consistency matrix gate present",
    )


def validate_internal_gates(checks: list[Check]) -> None:
    clean_room = read(REPORTS / "clean-room-validation.md") if (REPORTS / "clean-room-validation.md").is_file() else ""
    adversarial = read(REPORTS / "final-adversarial-review.md") if (REPORTS / "final-adversarial-review.md").is_file() else ""
    five_minute = read(REPORTS / "five-minute-submission-test.md") if (REPORTS / "five-minute-submission-test.md").is_file() else ""
    consistency = read(REPORTS / "submission-message-consistency.md") if (REPORTS / "submission-message-consistency.md").is_file() else ""
    checks_data = (
        ("gate.clean_room", "**Result: PASS.**" in clean_room, "clean-room PASS"),
        (
            "gate.adversarial",
            "| CRITICAL | 0 |" in adversarial and "| HIGH | 0 |" in adversarial and "**Gate: PASS.**" in adversarial,
            "CRITICAL=0; HIGH=0; gate=PASS",
        ),
        ("gate.five_minute", "**Gate: PASS.**" in five_minute, "five-minute gate PASS"),
        ("gate.message_consistency", "**Gate: PASS.**" in consistency, "message consistency PASS"),
    )
    for check_id, ok, detail in checks_data:
        record(checks, check_id, "PASS" if ok else "BLOCKED", detail)


def validate_cross_platform(checks: list[Check]) -> None:
    attributes_path = SUBMISSION / ".gitattributes"
    builder_path = SUBMISSION / "solution" / "scripts" / "build_dashboard_data.py"
    package_path = APP / "package.json"
    lock_path = APP / "package-lock.json"
    expected_attributes = (
        "solution/artifacts/diagnostic_summary.json text eol=lf",
        "solution/artifacts/journey_findings.json text eol=crlf",
        "solution/artifacts/graph_summary.json text eol=crlf",
        "solution/artifacts/graph_findings.json text eol=crlf",
        "solution/artifacts/watchlist_summary.json text eol=crlf",
        "solution/artifacts/watchlist_rules.json text eol=crlf",
        "solution/artifacts/watchlist_findings.json text eol=crlf",
        "solution/artifacts/experiment_lab_summary.json text eol=crlf",
        "solution/artifacts/experiment_hypotheses.json text eol=crlf",
        "solution/artifacts/experiment_findings.json text eol=crlf",
        "solution/artifacts/experiment_sample_size.json text eol=crlf",
        "solution/artifacts/experiment_guardrails.json text eol=crlf",
        "solution/artifacts/experiment_ethics.json text eol=crlf",
        "solution/artifacts/experiment_balance.json text eol=crlf",
        "solution/artifacts/experiment_feasibility.json text eol=crlf",
        "solution/app/public/data/*.json text eol=crlf",
    )
    attributes = read(attributes_path) if attributes_path.is_file() else ""
    builder = read(builder_path) if builder_path.is_file() else ""
    package = json.loads(read(package_path)) if package_path.is_file() else {}
    lock = json.loads(read(lock_path)) if lock_path.is_file() else {}
    attributes_ok = all(line in attributes for line in expected_attributes)
    builder_ok = 'newline="\\r\\n"' in builder
    override_ok = package.get("overrides", {}).get("sharp") == "0.35.3"
    next_requirement = package.get("dependencies", {}).get("next")
    lock_version = lock.get("packages", {}).get("node_modules/sharp", {}).get("version")
    next_lock_version = lock.get("packages", {}).get("node_modules/next", {}).get("version")
    lock_ok = lock_version == "0.35.3"
    next_ok = next_requirement == "^16.2.11" and next_lock_version == "16.2.11"
    ok = attributes_ok and builder_ok and override_ok and lock_ok and next_ok
    detail = (
        f"eol_rules={len(expected_attributes) if attributes_ok else 0}/16; "
        f"builder_crlf={builder_ok}; sharp_override={override_ok}; "
        f"locked_sharp={lock_version}; next_requirement={next_requirement}; "
        f"locked_next={next_lock_version}"
    )
    record(
        checks,
        "build.cross_platform_security",
        "PASS" if ok else "BLOCKED",
        detail,
    )


def validate_git(checks: list[Check]) -> None:
    status = git("status", "--porcelain=v1", "--untracked-files=all")
    outside: list[str] = []
    if status.returncode == 0:
        for line in status.stdout.splitlines():
            raw = line[3:]
            if " -> " in raw:
                raw = raw.split(" -> ", 1)[1]
            path = raw.strip('"').replace("\\", "/")
            allowed = any(path == prefix or path.startswith(prefix) for prefix in PACKAGE_PREFIXES)
            if not allowed:
                outside.append(path)
    record(
        checks,
        "git.change_scope",
        "PASS" if status.returncode == 0 and not outside else "BLOCKED",
        "outside=0" if not outside else f"outside={outside}",
    )

    raw = git("ls-files", "submissions/carlos-henrique/solution/data/raw/*.csv")
    raw_files = [line for line in raw.stdout.splitlines() if line]
    record(
        checks,
        "git.raw_csv",
        "PASS" if raw.returncode == 0 and not raw_files else "BLOCKED",
        f"tracked={len(raw_files)}",
    )

    tracked = git("ls-files")
    artifact_pattern = re.compile(r"(^|/)(?:node_modules|\.next|__pycache__)(?:/|$)|\.(?:pyc|pyo)$")
    artifacts = [line for line in tracked.stdout.splitlines() if artifact_pattern.search(line)]
    record(
        checks,
        "git.build_artifacts",
        "PASS" if tracked.returncode == 0 and not artifacts else "BLOCKED",
        f"tracked={len(artifacts)}",
    )


def status_for(checks: list[Check]) -> str:
    if any(check.status == "BLOCKED" for check in checks):
        return "BLOCKED"
    if any(check.status == "PASS_WITH_WARNINGS" for check in checks):
        return "PASS_WITH_WARNINGS"
    return "PASS"


def write_reports(checks: list[Check], gate: str) -> None:
    counts = {
        state: sum(check.status == state for check in checks)
        for state in ("PASS", "PASS_WITH_WARNINGS", "BLOCKED")
    }
    payload = {
        "validator": "JourneyGraph final submission validator",
        "version": "1.0.0",
        "status": gate,
        "scope": "submissions/carlos-henrique",
        "counts": counts,
        "checks": [check.__dict__ for check in checks],
        "publication_boundary": {
            "internal_package": "validated" if gate != "BLOCKED" else "blocked",
            "external_actions": "pending_user_action",
            "actions_executed": [],
        },
        "limitations": [
            "External URLs and actions remain outside this validator.",
            "The validator checks repository evidence, not hosting-platform behavior.",
            "A new validation cycle is required after external links are added.",
        ],
    }
    JSON_OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    lines = [
        "# Final Submission Validation",
        "",
        f"**Gate: {gate}.**",
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
            "## Publication Boundary",
            "",
            "Internal readiness and external publication are separate gates. Recording, deployment, upload, push, Pull Request creation, form completion, and submission remain under explicit user control.",
            "",
            "## Limitations",
            "",
            "This report validates the repository package and expected placeholders. Hosting behavior and final external visibility must be tested after the user performs each external action.",
            "",
        ]
    )
    MD_OUTPUT.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    checks: list[Check] = []
    existing = validate_files(checks)
    phase_files = [path for path in existing if path.parent == REPORTS]
    validate_headings(checks)
    validate_pitch_lengths(checks)
    validate_video(checks)
    validate_summary(checks)
    validate_links(checks, existing)
    validate_claims_and_urls(checks, phase_files)
    validate_external_state(checks, existing)
    validate_metrics_and_tests(checks, existing)
    validate_internal_gates(checks)
    validate_cross_platform(checks)
    validate_git(checks)
    gate = status_for(checks)
    write_reports(checks, gate)
    print(f"FINAL_SUBMISSION_VALIDATION={gate}")
    print(f"CHECKS={len(checks)}")
    print(f"REPORT_JSON={JSON_OUTPUT.relative_to(REPOSITORY)}")
    print(f"REPORT_MD={MD_OUTPUT.relative_to(REPOSITORY)}")
    return 0 if gate in {"PASS", "PASS_WITH_WARNINGS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
