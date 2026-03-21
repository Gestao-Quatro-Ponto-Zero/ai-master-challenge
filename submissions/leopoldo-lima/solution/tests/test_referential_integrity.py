from __future__ import annotations

from src.integrity.referential import evaluate_referential_integrity


def test_referential_relations_are_not_blocking() -> None:
    report = evaluate_referential_integrity()
    assert report["relations"]
    for relation in report["relations"]:
        assert relation["classification"] == "ok"
        assert relation["matched_rows"] == relation["total_rows_with_value"]


def test_unused_dimension_agents_are_warning() -> None:
    report = evaluate_referential_integrity()
    unused = report["unused_dimension_agents"]
    assert unused["classification"] == "warning"
    assert unused["count"] >= 0
