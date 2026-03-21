from __future__ import annotations

from datetime import date

from src.domain.models import Account, Opportunity, Product, SalesAgent
from src.features.engineering import build_feature_set


def test_feature_engineering_stage_and_dates() -> None:
    opp = Opportunity(
        opportunity_id="OPP-1",
        sales_agent="Ana",
        product="GTX Pro",
        account="Acme",
        deal_stage="Engaging",
        engage_date="2026-01-01",
        close_date="",
        close_value="100",
    )
    feat = build_feature_set(opp, reference_date=date(2026, 1, 21))
    assert feat.days_since_engage == 20
    assert feat.stage_rank == 2
    assert feat.pipeline_age_bucket == "active"
    assert feat.is_open is True
    assert feat.has_close_date is False


def test_feature_engineering_joins_and_nulls() -> None:
    opp = Opportunity(
        opportunity_id="OPP-2",
        sales_agent="Bruno",
        product="GTX Pro",
        account=None,
        deal_stage="Prospecting",
        engage_date="",
        close_date=None,
        close_value="0",
    )
    account = Account("Acme", "Tech", "2000", "12000000", "1500", "SP", "")
    product = Product("GTX Pro", "GTX", "9000")
    agent = SalesAgent("Bruno", "Marcos", "Core")
    feat = build_feature_set(opp, account=account, product=product, sales_agent=agent)
    assert feat.has_account is False
    assert feat.account_revenue_band == "enterprise"
    assert feat.employee_band == "large"
    assert feat.product_series == "GTX"
    assert feat.product_price == 9000.0
    assert feat.manager_name == "Marcos"
