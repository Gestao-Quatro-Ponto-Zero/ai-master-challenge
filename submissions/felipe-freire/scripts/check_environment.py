"""Fail-fast environment check for local runs and CI."""

from __future__ import annotations

import importlib
import platform

REQUIRED = (
    "pandas",
    "numpy",
    "scipy",
    "statsmodels",
    "sklearn",
    "matplotlib",
    "seaborn",
    "plotly",
    "streamlit",
    "pytest",
)


def main() -> None:
    failures: list[str] = []
    print(f"python={platform.python_version()}")
    for package in REQUIRED:
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "unknown")
            print(f"{package}={version}")
        except Exception as exc:  # pragma: no cover - diagnostic boundary
            failures.append(f"{package}: {exc}")
    if failures:
        raise SystemExit("missing/broken dependencies: " + "; ".join(failures))


if __name__ == "__main__":
    main()
