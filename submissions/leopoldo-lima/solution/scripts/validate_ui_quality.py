from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> None:
    app_js = _read(ROOT / "public" / "app.js")
    index_html = _read(ROOT / "public" / "index.html")
    factory_js = _read(
        ROOT / "public" / "infrastructure" / "repositories" / "repository-factory.js"
    )

    errors: list[str] = []

    if 'type="module"' not in index_html:
        errors.append("index.html must load app.js as module.")
    if "createOpportunityRepository" not in app_js:
        errors.append("app.js must use createOpportunityRepository factory.")
    if "fetch(" in app_js:
        errors.append("app.js must not call fetch directly.")
    if "mocks/fixtures" in app_js:
        errors.append("app.js must not import mock fixtures.")
    if "window.LEAD_SCORER_REPOSITORY_MODE" not in factory_js:
        errors.append("repository-factory must centralize runtime mode switch.")

    if errors:
        print("UI quality gate failed:")
        for item in errors:
            print(f"- {item}")
        raise SystemExit(1)

    print("UI quality gate passed.")


if __name__ == "__main__":
    main()
