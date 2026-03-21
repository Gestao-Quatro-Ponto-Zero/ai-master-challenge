from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAP_PATH = ROOT / "config" / "normalization-map.json"


@dataclass(frozen=True)
class NormalizationResult:
    original: str
    canonical: str
    strategy: str
    risk: str


def load_normalization_map(path: pathlib.Path | None = None) -> dict[str, Any]:
    file_path = path or MAP_PATH
    return json.loads(file_path.read_text(encoding="utf-8"))


def normalize_value(dataset: str, field: str, value: str) -> NormalizationResult:
    mapping = load_normalization_map()
    dataset_map = mapping.get(dataset, {})
    field_map = dataset_map.get(field, {})
    alias = field_map.get(value)
    if not alias:
        return NormalizationResult(
            original=value,
            canonical=value,
            strategy="identity",
            risk="low",
        )
    return NormalizationResult(
        original=value,
        canonical=alias["canonical"],
        strategy=alias.get("strategy", "semantic_alias"),
        risk=alias.get("risk", "medium"),
    )
