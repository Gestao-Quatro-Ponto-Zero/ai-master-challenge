from __future__ import annotations

from src.raw.data_quality import validate_sales_pipeline_rows


def test_quality_rules_pass_for_valid_rows() -> None:
    rows = [
        {
            "opportunity_id": "OPP-1",
            "deal_stage": "Lost",
            "engage_date": "2026-01-01",
            "close_date": "2026-01-10",
            "close_value": "0",
        },
        {
            "opportunity_id": "OPP-2",
            "deal_stage": "Won",
            "engage_date": "2026-01-02",
            "close_date": "2026-01-15",
            "close_value": "100",
        },
        {
            "opportunity_id": "OPP-3",
            "deal_stage": "Engaging",
            "engage_date": "2026-01-03",
            "close_date": "",
            "close_value": "0",
        },
    ]
    assert validate_sales_pipeline_rows(rows) == []


def test_quality_rules_fail_on_invalid_rows() -> None:
    rows = [
        {
            "opportunity_id": "OPP-1",
            "deal_stage": "Lost",
            "engage_date": "2026-01-01",
            "close_date": "2026-01-10",
            "close_value": "10",
        },
        {
            "opportunity_id": "OPP-1",
            "deal_stage": "Won",
            "engage_date": "2026-01-02",
            "close_date": "",
            "close_value": "0",
        },
    ]
    errors = validate_sales_pipeline_rows(rows)
    assert any("duplicado" in e for e in errors)
    assert any("Lost exige close_value = 0" in e for e in errors)
    assert any("Won exige close_value > 0" in e for e in errors)
    assert any("Won exige close_date preenchida" in e for e in errors)
