from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class AccountOut(BaseModel):
    account: str
    sector: str | None
    year_established: int | None
    revenue: float | None
    employees: int | None
    office_location: str | None
    subsidiary_of: str | None


class ProductOut(BaseModel):
    product: str
    series: str | None
    sales_price: float | None


class SalesTeamOut(BaseModel):
    sales_agent: str
    manager: str | None
    regional_office: str | None


class OpportunityOut(BaseModel):
    opportunity_id: str
    sales_agent: str | None
    manager: str | None
    regional_office: str | None
    product: str | None
    series: str | None
    account: str | None
    deal_stage: str | None
    engage_date: str | None
    close_date: str | None
    close_value: float | None
    sales_price: float | None


class PipelineMetricsOut(BaseModel):
    deal_stage: str | None
    opportunities: int
    total_value: float


class AccountScoreOut(BaseModel):
    account: str
    won_deals: int
    lost_deals: int
    closed_deals: int
    win_rate: float
    avg_won_value: float
    account_score: float
