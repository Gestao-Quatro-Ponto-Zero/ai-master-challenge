"""Read-only CSV loading utilities for the RavenStack source tables."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Mapping

import pandas as pd


SOLUTION_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DEFAULT_RAW_DATA_DIR: Final[Path] = SOLUTION_ROOT / "data" / "raw"

OFFICIAL_FILES: Final[Mapping[str, str]] = {
    "accounts": "ravenstack_accounts.csv",
    "subscriptions": "ravenstack_subscriptions.csv",
    "feature_usage": "ravenstack_feature_usage.csv",
    "support_tickets": "ravenstack_support_tickets.csv",
    "churn_events": "ravenstack_churn_events.csv",
}


class DataLoadError(RuntimeError):
    """Raised when a source file cannot be located or read safely."""


@dataclass(frozen=True)
class LoadMetadata:
    """Inspectable metadata about a CSV load operation."""

    table: str
    file_name: str
    relative_path: str
    encoding: str
    delimiter: str
    sampled: bool
    requested_rows: int | None
    records_loaded: int
    columns: tuple[str, ...]
    inferred_dtypes: Mapping[str, str]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""

        payload = asdict(self)
        payload["columns"] = list(self.columns)
        payload["inferred_dtypes"] = dict(self.inferred_dtypes)
        return payload


def resolve_raw_data_dir(raw_data_dir: Path | str | None = None) -> Path:
    """Resolve the raw directory independently from the current directory."""

    candidate = DEFAULT_RAW_DATA_DIR if raw_data_dir is None else Path(raw_data_dir)
    return candidate.expanduser().resolve()


def source_path(table: str, raw_data_dir: Path | str | None = None) -> Path:
    """Resolve an official source path without accepting silent aliases."""

    if table not in OFFICIAL_FILES:
        allowed = ", ".join(sorted(OFFICIAL_FILES))
        raise DataLoadError(f"Unknown table '{table}'. Expected one of: {allowed}.")
    return resolve_raw_data_dir(raw_data_dir) / OFFICIAL_FILES[table]


def validate_all_present(raw_data_dir: Path | str | None = None) -> dict[str, Path]:
    """Validate that the five official files are jointly available."""

    paths = {
        table: source_path(table, raw_data_dir)
        for table in sorted(OFFICIAL_FILES)
    }
    missing = [path.name for path in paths.values() if not path.is_file()]
    if missing:
        raise DataLoadError(
            "Missing official RavenStack source files: " + ", ".join(sorted(missing))
        )
    return paths


def detect_encoding(path: Path) -> str:
    """Try UTF-8 first, then conservative fallback encodings."""

    candidates = ("utf-8", "utf-8-sig", "cp1252", "latin-1")
    for encoding in candidates:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                while handle.read(1024 * 1024):
                    pass
            return encoding
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            raise DataLoadError(f"Could not read '{path.name}': {exc}") from exc
    raise DataLoadError(f"Could not determine a supported encoding for '{path.name}'.")


def detect_delimiter(path: Path, encoding: str) -> str:
    """Detect a delimiter from a bounded sample without modifying the file."""

    try:
        with path.open("r", encoding=encoding, newline="") as handle:
            sample = handle.read(64 * 1024)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except (csv.Error, UnicodeDecodeError):
        return ","
    except OSError as exc:
        raise DataLoadError(f"Could not inspect delimiter for '{path.name}': {exc}") from exc


def load_csv(
    table: str,
    *,
    raw_data_dir: Path | str | None = None,
    sample_rows: int | None = None,
) -> tuple[pd.DataFrame, LoadMetadata]:
    """Load one official CSV without mutating data or silently coercing types."""

    if sample_rows is not None and sample_rows <= 0:
        raise ValueError("sample_rows must be a positive integer or None.")

    path = source_path(table, raw_data_dir)
    if not path.is_file():
        raise DataLoadError(
            f"Required source file is missing for table '{table}': {path}"
        )

    encoding = detect_encoding(path)
    delimiter = detect_delimiter(path, encoding)
    try:
        frame = pd.read_csv(
            path,
            encoding=encoding,
            sep=delimiter,
            nrows=sample_rows,
            low_memory=False,
        )
    except Exception as exc:  # pandas exposes multiple parser exception classes
        raise DataLoadError(f"Failed to load '{path.name}': {exc}") from exc

    metadata = LoadMetadata(
        table=table,
        file_name=path.name,
        relative_path=path.relative_to(SOLUTION_ROOT).as_posix(),
        encoding=encoding,
        delimiter=delimiter,
        sampled=sample_rows is not None,
        requested_rows=sample_rows,
        records_loaded=len(frame),
        columns=tuple(str(column) for column in frame.columns),
        inferred_dtypes={str(column): str(dtype) for column, dtype in frame.dtypes.items()},
    )
    return frame, metadata


def load_all(
    *,
    raw_data_dir: Path | str | None = None,
    sample_rows: int | None = None,
) -> tuple[dict[str, pd.DataFrame], dict[str, LoadMetadata]]:
    """Load all five sources in a deterministic order."""

    validate_all_present(raw_data_dir)
    frames: dict[str, pd.DataFrame] = {}
    metadata: dict[str, LoadMetadata] = {}
    for table in OFFICIAL_FILES:
        frame, load_metadata = load_csv(
            table,
            raw_data_dir=raw_data_dir,
            sample_rows=sample_rows,
        )
        frames[table] = frame
        metadata[table] = load_metadata
    return frames, metadata
