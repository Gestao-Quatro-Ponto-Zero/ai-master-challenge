from __future__ import annotations

from src.domain.models import (
    OpportunityFeatureSet,
    RawOpportunity,
    core_opportunity_to_gold,
    raw_opportunity_to_core,
)


def test_raw_to_core_applies_product_normalization() -> None:
    raw = RawOpportunity(
        opportunity_id="OPP-1",
        sales_agent="Ana",
        product="GTXPro",
        account="Acme",
        deal_stage="Engaging",
        engage_date="2026-01-01",
        close_date="",
        close_value="100",
    )
    core = raw_opportunity_to_core(raw)
    assert core.product == "GTX Pro"


def test_core_to_gold_builds_features() -> None:
    raw = RawOpportunity(
        opportunity_id="OPP-2",
        sales_agent="Bruno",
        product="GTX Pro",
        account="",
        deal_stage="Prospecting",
        engage_date="",
        close_date="",
        close_value="0",
    )
    gold: OpportunityFeatureSet = core_opportunity_to_gold(raw_opportunity_to_core(raw))
    assert gold.opportunity_id == "OPP-2"
    assert gold.has_account is False
    assert gold.close_value == 0.0
