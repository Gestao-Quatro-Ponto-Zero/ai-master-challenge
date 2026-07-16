from __future__ import annotations

import os
from pathlib import Path

REQUIRED_FILES = (
    "accounts.csv",
    "products.csv",
    "sales_pipeline.csv",
    "sales_teams.csv",
)
OPTIONAL_FILES = ("metadata.csv",)
DATASET_FOLDER = "crm-sales-predictive-analytics"


class DatasetNotFoundError(FileNotFoundError):
    """Raised when the CRM dataset cannot be located or is incomplete."""


def find_repository_root(start: Path | None = None) -> Path:
    """Find the cloned repository root without depending on the current working directory."""
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
        if (candidate / ".gitignore").exists() and (candidate / "submissions").exists():
            return candidate

    # Expected source layout:
    # <repo>/submissions/lucio-castilho/solution/src/data_loader.py
    parents = Path(__file__).resolve().parents
    if len(parents) > 4:
        return parents[4]
    raise DatasetNotFoundError("Could not determine the repository root.")


def _contains_required_files(path: Path) -> bool:
    return path.is_dir() and all((path / filename).is_file() for filename in REQUIRED_FILES)


def get_data_dir() -> Path:
    """Resolve the local dataset directory.

    Resolution order:
    1. CRM_DATA_DIR environment variable.
    2. <repo>/datasets/crm-sales-predictive-analytics/
    3. <repo>/datasets/ (supported for convenience).
    """
    configured = os.getenv("CRM_DATA_DIR")
    if configured:
        path = Path(configured).expanduser().resolve()
        if _contains_required_files(path):
            return path
        raise DatasetNotFoundError(_error_message(path))

    repo_root = find_repository_root()
    candidates = (
        repo_root / "datasets" / DATASET_FOLDER,
        repo_root / "datasets",
    )
    for candidate in candidates:
        if _contains_required_files(candidate):
            return candidate

    raise DatasetNotFoundError(_error_message(candidates[0]))


def validate_data_dir(path: str | Path) -> Path:
    """Validate an explicit data directory and return its resolved path."""
    resolved = Path(path).expanduser().resolve()
    if not _contains_required_files(resolved):
        raise DatasetNotFoundError(_error_message(resolved))
    return resolved


def _error_message(expected_path: Path) -> str:
    required = "\n".join(f"  - {name}" for name in REQUIRED_FILES)
    return (
        "CRM Sales Predictive Analytics dataset not found or incomplete.\n\n"
        "Download the Kaggle dataset and extract the CSV files to:\n"
        f"  {expected_path}\n\n"
        "Required files:\n"
        f"{required}\n\n"
        "Alternative: set CRM_DATA_DIR to the folder containing the CSV files."
    )
