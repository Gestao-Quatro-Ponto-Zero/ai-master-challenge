from __future__ import annotations

from datetime import date, datetime
from typing import Any

from src.domain.models import Account, Opportunity, OpportunityFeatureSet, Product, SalesAgent

STAGE_RANK = {
    "Prospecting": 1,
    "Engaging": 2,
    "Won": 3,
    "Lost": 0,
}


def _parse_iso_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def _age_bucket(days: int) -> str:
    if days <= 15:
        return "fresh"
    if days <= 45:
        return "active"
    return "stale"


def _revenue_band(raw: str) -> str:
    try:
        val = float((raw or "").strip() or "0")
    except ValueError:
        return "unknown"
    if val >= 10_000_000:
        return "enterprise"
    if val >= 1_000_000:
        return "mid"
    return "small"


def _employee_band(raw: str) -> str:
    try:
        val = int(float((raw or "").strip() or "0"))
    except ValueError:
        return "unknown"
    if val >= 1000:
        return "large"
    if val >= 200:
        return "medium"
    return "small"


def _price(raw: str) -> float:
    try:
        return float((raw or "").strip() or "0")
    except ValueError:
        return 0.0


def feature_set_from_payload(
    payload: dict[str, Any],
    *,
    reference_date: date | None = None,
) -> OpportunityFeatureSet:
    """Constroi `OpportunityFeatureSet` a partir de dict (API row / scoring payload).

    CRP-REAL-04: alinha scoring HTTP ao mesmo vocabulário de features que o pipeline real.
    Chaves aceites (parciais permitidas): id/opportunity_id, deal_stage, engage_date, close_date,
    close_value/amount, account/account_name/title, account_revenue, account_employees,
    product_series, product/product_sales_price/product_price,
    regional_office/team_regional_office/region, manager/manager_name.
    """
    today = reference_date or date.today()
    oid = str(
        payload.get("opportunity_id")
        or payload.get("id")
        or payload.get("opportunityId")
        or "adhoc"
    )
    deal_stage = str(payload.get("deal_stage", "") or "").strip()
    engage_raw = str(payload.get("engage_date", "") or "").strip()
    close_raw = payload.get("close_date")
    close_date_str = str(close_raw).strip() if close_raw not in (None, "") else ""

    engage_date = _parse_iso_date(engage_raw)
    days_since_engage = (today - engage_date).days if engage_date else 0

    cv_raw = payload.get("close_value")
    if cv_raw is None:
        cv_raw = payload.get("amount", 0)
    try:
        close_value = float(str(cv_raw).strip() or "0")
    except ValueError:
        close_value = 0.0

    account_hint = (
        str(payload.get("account_name", "") or "").strip()
        or str(payload.get("account", "") or "").strip()
        or str(payload.get("title", "") or "").strip()
    )
    has_account = bool(account_hint)

    rev_raw = str(payload.get("account_revenue", "") or payload.get("revenue", "") or "")
    emp_raw = str(payload.get("account_employees", "") or payload.get("employees", "") or "")
    series_raw = str(payload.get("product_series", "") or payload.get("series", "") or "").strip()
    series = series_raw or "unknown"
    try:
        pprice = float(
            str(payload.get("product_sales_price", payload.get("product_price", 0)) or "0")
        )
    except ValueError:
        pprice = 0.0

    reg = (
        str(payload.get("team_regional_office", "") or "").strip()
        or str(payload.get("regional_office", "") or "").strip()
        or str(payload.get("region", "") or "").strip()
        or "unknown"
    )
    mgr = (
        str(payload.get("manager_name", "") or payload.get("manager", "") or "").strip()
        or "unknown"
    )
    norm_product = str(payload.get("product", "") or "").strip()

    return OpportunityFeatureSet(
        opportunity_id=oid,
        days_since_engage=max(0, days_since_engage),
        deal_stage=deal_stage,
        stage_rank=STAGE_RANK.get(deal_stage, 0),
        pipeline_age_bucket=_age_bucket(days_since_engage) if engage_date else "unknown",
        has_account=has_account,
        has_close_date=bool(close_date_str),
        is_open=deal_stage in {"Prospecting", "Engaging"},
        is_won=deal_stage == "Won",
        is_lost=deal_stage == "Lost",
        account_revenue_band=_revenue_band(rev_raw),
        employee_band=_employee_band(emp_raw),
        product_series=series if series != "unknown" else "unknown",
        product_price=pprice,
        regional_office=reg if reg != "unknown" else "unknown",
        manager_name=mgr,
        close_value=close_value,
        normalized_product=norm_product,
    )


def build_feature_set(
    opportunity: Opportunity,
    account: Account | None = None,
    product: Product | None = None,
    sales_agent: SalesAgent | None = None,
    reference_date: date | None = None,
) -> OpportunityFeatureSet:
    today = reference_date or date.today()
    engage_date = _parse_iso_date(opportunity.engage_date)
    days_since_engage = (today - engage_date).days if engage_date else 0

    return OpportunityFeatureSet(
        opportunity_id=opportunity.opportunity_id,
        days_since_engage=days_since_engage,
        deal_stage=opportunity.deal_stage,
        stage_rank=STAGE_RANK.get(opportunity.deal_stage, 0),
        pipeline_age_bucket=_age_bucket(days_since_engage),
        has_account=bool((opportunity.account or "").strip()),
        has_close_date=bool((opportunity.close_date or "").strip()),
        is_open=opportunity.deal_stage in {"Prospecting", "Engaging"},
        is_won=opportunity.deal_stage == "Won",
        is_lost=opportunity.deal_stage == "Lost",
        account_revenue_band=_revenue_band(account.revenue if account else ""),
        employee_band=_employee_band(account.employees if account else ""),
        product_series=product.series if product else "unknown",
        product_price=_price(product.sales_price if product else ""),
        regional_office=sales_agent.regional_office if sales_agent else "unknown",
        manager_name=sales_agent.manager if sales_agent else "unknown",
        close_value=_price(opportunity.close_value),
        normalized_product=opportunity.product,
    )
