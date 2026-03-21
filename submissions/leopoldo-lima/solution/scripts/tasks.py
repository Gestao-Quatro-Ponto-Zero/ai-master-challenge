from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Pacote `submissions/<nome>/`: documentação e process log ficam ao lado de `solution/`.
SUBMISSION_ROOT = ROOT.parent


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def install() -> None:
    print("==> Checking local Python runtime")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version.split()[0]}")
    print("Install dev dependencies with:")
    print("python -m pip install -e .[dev]")


def test() -> None:
    print("==> Running repository smoke checks")
    required_paths = [
        SUBMISSION_ROOT / "process-log" / "crps" / "executed",
        SUBMISSION_ROOT / "docs",
        SUBMISSION_ROOT / "process-log" / "PROCESS_LOG.md",
        ROOT / "README.md",
    ]
    missing = []
    for p in required_paths:
        if not p.exists():
            try:
                missing.append(str(p.relative_to(ROOT)))
            except ValueError:
                missing.append(str(p))
    if missing:
        print("Missing required paths:")
        for item in missing:
            print(f"- {item}")
        raise SystemExit(1)
    print("Repository smoke checks passed.")
    print("==> Running pytest")
    _run([sys.executable, "-m", "pytest", "-q"])


def lint() -> None:
    print("==> Running Markdown whitespace lint")
    text_files = (
        list(ROOT.glob("*.md"))
        + list(SUBMISSION_ROOT.glob("*.md"))
        + list((SUBMISSION_ROOT / "docs").rglob("*.md"))
        + list((SUBMISSION_ROOT / "process-log").rglob("*.md"))
    )
    ignored = {"PROCESS_LOG.md", "legacy/repo_concat_all.md"}
    trailing = []
    for file_path in text_files:
        if file_path.name in ignored:
            continue
        content = file_path.read_text(encoding="utf-8")
        if any(line.endswith(" ") or line.endswith("\t") for line in content.splitlines()):
            trailing.append(str(file_path.relative_to(ROOT)))
    if trailing:
        print("Trailing whitespace detected:")
        for item in trailing:
            print(f"- {item}")
        raise SystemExit(1)
    print("Markdown lint checks passed.")
    print("==> Running ruff check")
    _run([sys.executable, "-m", "ruff", "check", "."])
    print("Ruff lint checks passed.")


def format_check() -> None:
    print("==> Running ruff format check")
    _run([sys.executable, "-m", "ruff", "format", "--check", "."])
    print("Format check passed.")


def typecheck() -> None:
    print("==> Typechecking local Python task runner")
    _run([sys.executable, "-m", "py_compile", str(ROOT / "scripts" / "tasks.py")])
    _run([sys.executable, "-m", "py_compile", str(ROOT / "scripts" / "validate_data_contract.py")])
    _run([sys.executable, "-m", "py_compile", str(ROOT / "scripts" / "validate_data_quality.py")])
    _run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(ROOT / "scripts" / "generate_data_dictionary.py"),
        ]
    )
    _run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(ROOT / "scripts" / "validate_referential_integrity.py"),
        ]
    )
    _run([sys.executable, "-m", "py_compile", str(ROOT / "src" / "domain" / "models.py")])
    _run([sys.executable, "-m", "py_compile", str(ROOT / "src" / "raw" / "data_quality.py")])
    _run([sys.executable, "-m", "py_compile", str(ROOT / "src" / "normalization" / "mapper.py")])
    _run([sys.executable, "-m", "py_compile", str(ROOT / "src" / "integrity" / "referential.py")])
    _run([sys.executable, "-m", "py_compile", str(ROOT / "src" / "features" / "engineering.py")])
    _run([sys.executable, "-m", "py_compile", str(ROOT / "src" / "scoring" / "engine.py")])
    _run([sys.executable, "-m", "py_compile", str(ROOT / "src" / "api" / "app.py")])
    _run([sys.executable, "-m", "mypy", "--explicit-package-bases", "src", "scripts", "tests"])
    print("Typecheck passed.")


def contract() -> None:
    print("==> Validating repository data contract")
    _run([sys.executable, str(ROOT / "scripts" / "validate_data_contract.py")])
    print("Contract validation passed.")


def inspect_data() -> None:
    print("==> Inspecting raw CSV datasets")
    _run([sys.executable, str(ROOT / "scripts" / "inspect_data.py")])
    print("Raw inspection completed.")


def data_dictionary() -> None:
    print("==> Generating data dictionary from metadata.csv")
    _run([sys.executable, str(ROOT / "scripts" / "generate_data_dictionary.py")])
    print("Data dictionary generated.")


def data_quality() -> None:
    print("==> Validating dataset quality rules")
    _run([sys.executable, str(ROOT / "scripts" / "validate_data_quality.py")])
    print("Data quality validation passed.")


def normalization() -> None:
    print("==> Running normalization checks")
    _run([sys.executable, "-m", "pytest", "-q", "tests/test_normalization.py"])
    print("Normalization checks passed.")


def referential_integrity() -> None:
    print("==> Validating referential integrity")
    _run([sys.executable, str(ROOT / "scripts" / "validate_referential_integrity.py")])
    _run([sys.executable, "-m", "pytest", "-q", "tests/test_referential_integrity.py"])
    print("Referential integrity validation passed.")


def features() -> None:
    print("==> Running feature engineering checks")
    _run([sys.executable, "-m", "pytest", "-q", "tests/test_features.py"])
    print("Feature engineering checks passed.")


def runbook_data() -> None:
    print("==> Generating data runbook evidence")
    _run([sys.executable, str(ROOT / "scripts" / "run_data_runbook.py")])
    print("Data runbook evidence generated.")


def ui_quality() -> None:
    print("==> Running UI quality checks")
    _run([sys.executable, str(ROOT / "scripts" / "validate_ui_quality.py")])
    ui_tests()
    print("UI quality checks passed.")


def ui_tests() -> None:
    print("==> Running UI test coverage")
    _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_ui_smoke.py",
            "tests/test_ui_front_coverage.py",
        ]
    )
    print("UI test coverage passed.")


def ui_ci_check() -> None:
    print("==> Running UI CI-equivalent checks")
    ui_quality()
    print("UI CI-equivalent checks passed.")


def security() -> None:
    print("==> Running dependency vulnerability scan (pip-audit)")
    _run([sys.executable, "-m", "pip_audit", "-r", str(ROOT / "requirements-audit.txt")])
    print("Dependency scan passed.")


def sbom() -> None:
    output = ROOT / "artifacts" / "security" / "sbom.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    print(f"==> Generating SBOM at {output}")
    _run([sys.executable, "-m", "cyclonedx_py", "environment", "--output-file", str(output)])
    print("SBOM generated.")


def build() -> None:
    print("==> Running composite build")
    test()
    lint()
    format_check()
    typecheck()
    contract()
    inspect_data()
    data_dictionary()
    data_quality()
    normalization()
    referential_integrity()
    features()
    ui_quality()
    runbook_data()
    security()
    sbom()
    print("Build completed.")


def export_real_flow_evidence() -> None:
    print("==> Exporting HTTP snapshots (real_dataset) to artifacts/process-log/test-runs/")
    _run([sys.executable, str(ROOT / "scripts" / "export_real_flow_evidence.py")])


def dev() -> None:
    port = os.environ.get("LEAD_SCORER_PORT", "8787")
    print(f"==> Starting Lead Scorer API on http://127.0.0.1:{port}")
    _run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Challenge pack task runner")
    parser.add_argument(
        "task",
        choices=[
            "install",
            "dev",
            "test",
            "lint",
            "format",
            "typecheck",
            "contract",
            "inspect-data",
            "data-dictionary",
            "data-quality",
            "normalization",
            "referential-integrity",
            "features",
            "runbook-data",
            "ui-quality",
            "ui-tests",
            "ui-ci-check",
            "security",
            "sbom",
            "export-real-flow-evidence",
            "build",
        ],
    )
    args = parser.parse_args()

    dispatch = {
        "install": install,
        "dev": dev,
        "test": test,
        "lint": lint,
        "format": format_check,
        "typecheck": typecheck,
        "contract": contract,
        "inspect-data": inspect_data,
        "data-dictionary": data_dictionary,
        "data-quality": data_quality,
        "normalization": normalization,
        "referential-integrity": referential_integrity,
        "features": features,
        "runbook-data": runbook_data,
        "ui-quality": ui_quality,
        "ui-tests": ui_tests,
        "ui-ci-check": ui_ci_check,
        "security": security,
        "sbom": sbom,
        "export-real-flow-evidence": export_real_flow_evidence,
        "build": build,
    }
    dispatch[args.task]()


if __name__ == "__main__":
    main()
