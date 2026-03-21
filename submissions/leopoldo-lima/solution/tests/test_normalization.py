from __future__ import annotations

from src.normalization.mapper import normalize_value


def test_gtxpro_normalizes_to_gtx_pro() -> None:
    result = normalize_value("sales_pipeline.csv", "product", "GTXPro")
    assert result.original == "GTXPro"
    assert result.canonical == "GTX Pro"
    assert result.strategy == "semantic_alias"


def test_unknown_value_keeps_identity() -> None:
    result = normalize_value("sales_pipeline.csv", "product", "ABC")
    assert result.original == "ABC"
    assert result.canonical == "ABC"
    assert result.strategy == "identity"
