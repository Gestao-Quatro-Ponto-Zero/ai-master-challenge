from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.normalization.mapper import normalize_value


# Raw layer
@dataclass(frozen=True)
class RawAccount:
    account: str
    sector: str
    year_established: str
    revenue: str
    employees: str
    office_location: str
    subsidiary_of: str


@dataclass(frozen=True)
class RawProduct:
    product: str
    series: str
    sales_price: str


@dataclass(frozen=True)
class RawSalesTeam:
    sales_agent: str
    manager: str
    regional_office: str


@dataclass(frozen=True)
class RawOpportunity:
    opportunity_id: str
    sales_agent: str
    product: str
    account: Optional[str]
    deal_stage: str
    engage_date: str
    close_date: Optional[str]
    close_value: str


@dataclass(frozen=True)
class RawMetadataRow:
    table: str
    field: str
    description: str


# Core layer
@dataclass(frozen=True)
class Account:
    account: str
    sector: str
    year_established: str
    revenue: str
    employees: str
    office_location: str
    subsidiary_of: str


@dataclass(frozen=True)
class Product:
    product: str
    series: str
    sales_price: str


@dataclass(frozen=True)
class SalesAgent:
    sales_agent: str
    manager: str
    regional_office: str


@dataclass(frozen=True)
class Opportunity:
    opportunity_id: str
    sales_agent: str
    product: str
    account: Optional[str]
    deal_stage: str
    engage_date: str
    close_date: Optional[str]
    close_value: str


@dataclass(frozen=True)
class MetadataField:
    table: str
    field: str
    description: str


# Gold layer
@dataclass(frozen=True)
class OpportunityFeatureSet:
    opportunity_id: str
    days_since_engage: int
    deal_stage: str
    stage_rank: int
    pipeline_age_bucket: str
    has_account: bool
    has_close_date: bool
    is_open: bool
    is_won: bool
    is_lost: bool
    account_revenue_band: str
    employee_band: str
    product_series: str
    product_price: float
    regional_office: str
    manager_name: str
    close_value: float
    normalized_product: str


@dataclass(frozen=True)
class OpportunityScore:
    opportunity_id: str
    score: int
    reason: str


@dataclass(frozen=True)
class OpportunityDetailView:
    opportunity_id: str
    account: Optional[str]
    product: str
    normalized_product: str
    sales_agent: str
    deal_stage: str
    close_value: float


def raw_opportunity_to_core(raw: RawOpportunity) -> Opportunity:
    normalized = normalize_value("sales_pipeline.csv", "product", raw.product).canonical
    return Opportunity(
        opportunity_id=raw.opportunity_id,
        sales_agent=raw.sales_agent,
        product=normalized,
        account=raw.account,
        deal_stage=raw.deal_stage,
        engage_date=raw.engage_date,
        close_date=raw.close_date,
        close_value=raw.close_value,
    )


def core_opportunity_to_gold(core: Opportunity) -> OpportunityFeatureSet:
    try:
        close_value = float((core.close_value or "").strip() or "0")
    except ValueError:
        close_value = 0.0
    return OpportunityFeatureSet(
        opportunity_id=core.opportunity_id,
        days_since_engage=0,
        deal_stage=core.deal_stage,
        stage_rank=0,
        pipeline_age_bucket="unknown",
        has_account=bool((core.account or "").strip()),
        has_close_date=bool((core.close_date or "").strip()),
        is_open=core.deal_stage in {"Prospecting", "Engaging"},
        is_won=core.deal_stage == "Won",
        is_lost=core.deal_stage == "Lost",
        account_revenue_band="unknown",
        employee_band="unknown",
        product_series="unknown",
        product_price=0.0,
        regional_office="unknown",
        manager_name="unknown",
        close_value=close_value,
        normalized_product=core.product,
    )
