from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Metric(BaseModel):
    value: float | int | None
    status: str
    definition: str
    denominator: str | None = None


class MonthlyPoint(BaseModel):
    month: str
    churn_event_rows: int
    unique_event_accounts: int
    nonreactivation_event_rows: int
    reactivation_event_rows: int
    usage_rows: int
    usage_accounts: int
    usage_count: int
    ticket_count: int
    satisfaction_n: int
    satisfaction_mean: float | None


class SegmentPoint(BaseModel):
    name: str
    accounts: int
    churn_flag_true: int
    churn_flag_rate: float
    event_accounts: int
    event_account_rate: float


class Finding(BaseModel):
    id: str
    title: str
    statement: str
    evidence: list[str]
    interpretation: str
    confidence: str


class SupportComparison(BaseModel):
    group: str
    accounts: int
    ticket_rows: int
    first_response_n: int
    first_response_median_minutes: float | None
    resolution_n: int
    resolution_median_hours: float | None
    satisfaction_n: int
    satisfaction_mean: float | None
    satisfaction_missing: int
    escalation_n: int
    escalated_tickets: int
    escalation_rate: float | None


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset: dict[str, Any]
    record_counts: dict[str, int]
    metrics: dict[str, Metric]
    data_quality: dict[str, Any]
    monthly: list[MonthlyPoint]
    reasons: list[dict[str, Any]]
    support_comparison: list[SupportComparison]
    segments: dict[str, list[SegmentPoint]]
    findings: list[Finding]
    methodology: list[str]


class BusinessInvestigationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metadata: dict[str, Any]
    record_counts: dict[str, int]
    labels: dict[str, Any]
    segments: list[dict[str, Any]]
    subscription_segments: list[dict[str, Any]]
    segment_exploratory_rankings_min_30: list[dict[str, Any]]
    cohorts: dict[str, Any]
    usage: dict[str, Any]
    support: dict[str, Any]
    revenue: dict[str, Any]
    account_investigation_candidates: list[dict[str, Any]]
    hypotheses: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    limitations: list[str]


class HistoricalChurnResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    metadata: dict[str, Any]
    source_counts: dict[str, int]
    snapshots: dict[str, dict[str, int]]
    annual: dict[str, dict[str, Any]]
    monthly: list[dict[str, Any]]
    cohorts: dict[str, Any]
    event_date_conflicts: dict[str, dict[str, int]]
    data_quality: dict[str, Any]


class ContractChurnResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metadata: dict[str, Any]
    revalidation: dict[str, Any]
    ended_subscription_class_counts: dict[str, int]
    ended_subscriptions: list[dict[str, Any]]
    event_end_proximity_counts: dict[str, Any]
    event_reasons: list[dict[str, Any]]
    event_segments: dict[str, list[dict[str, Any]]]
    event_account_investigation_examples: list[dict[str, Any]]
    reactivation_summary: dict[str, Any]
    reactivation_events: list[dict[str, Any]]
    account_reconciliation: dict[str, Any]
    financial_descriptives: dict[str, Any]
    conflicting_events: list[dict[str, Any]]
    limitations: list[str]


class G4CustomerChurnResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metadata: dict[str, Any]
    source_counts: dict[str, int]
    primary_customer_churn: dict[str, Any]
    snapshots: dict[str, dict[str, int]]
    annual: dict[str, dict[str, Any]]
    monthly: list[dict[str, Any]]
    quarterly: list[dict[str, Any]]
    segments: list[dict[str, Any]]
    account_review_candidates: list[dict[str, Any]]
    cohorts: dict[str, Any]
    reconciliation: dict[str, Any]
    methodology: list[str]


class DailyPortfolioChurnResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metadata: dict[str, Any]
    summary: dict[str, int]
    annual_monthly_summary: dict[str, dict[str, Any]]
    periods: dict[str, list[dict[str, Any]]]
    reconciliation: dict[str, Any]
    calendar_boundary_snapshots: dict[str, dict[str, Any]]
    event_reconciliation: dict[str, Any]
    plan_transition_analysis: dict[str, Any]
    plan_proxy_summary: list[dict[str, Any]]
    segment_summary: dict[str, list[dict[str, Any]]]
    account_movement_candidates: list[dict[str, Any]]
    financial_metrics: dict[str, Any]
    daily: list[dict[str, Any]]
    movements: list[dict[str, Any]]
    invalid_intervals: list[dict[str, Any]]
    assumptions: list[str]
    key_moments: "KeyMomentsResponse"


class KeyMoment(BaseModel):
    id: str
    type: str
    month: str
    metric: str
    value: int | float
    numerator: int | None
    denominator: int | None
    comparison: dict[str, Any]
    criterion: str
    segments: list[dict[str, Any]]
    accounts: list[dict[str, Any]]
    account_count: int
    accounts_truncated: bool
    evidence_classification: str
    executive_explanation: str
    investigation_action: str


class KeyMomentsResponse(BaseModel):
    classification: str
    months_analyzed: int
    criteria_note: str
    moments: list[KeyMoment]


class ReconciliationAccount(BaseModel):
    account_id: str
    account_name: str
    industry: str
    country: str
    churn_flag: bool
    churn_event_count: int
    status_comparison: str
    active_subscription_rows: int
    active_record_mrr_sum: float
    interpretation: str


class ReconciliationResponse(BaseModel):
    warning: str
    returned: int
    accounts: list[ReconciliationAccount]


class ScenarioRequest(BaseModel):
    eligible_accounts: int = Field(ge=0, le=500)
    operational_capacity: int = Field(ge=0, le=500)
    budget: float = Field(ge=0, le=10_000_000, allow_inf_nan=False)
    cost_per_contact: float = Field(ge=0, le=1_000_000, allow_inf_nan=False)
    assumed_uptake_pct: float = Field(default=1.0, ge=0, le=1, allow_inf_nan=False,
        description="Assumed share of selected outreach accounts that participate; user-supplied scenario input, not an observed response rate.")
    assumed_effectiveness: float = Field(
        ge=0,
        le=1,
        allow_inf_nan=False,
        description=(
            "User-supplied hypothetical incremental retention lift versus an untreated baseline; "
            "not an observed or causal effect."
        ),
    )
    assumed_monthly_value_per_retained_account: float = Field(ge=0, le=10_000_000, allow_inf_nan=False)
    retention_horizon_months: int = Field(ge=1, le=36)


class ScenarioResponse(BaseModel):
    status: str
    currency_unit: str
    assumptions: ScenarioRequest
    selected_accounts: int
    expected_participants: float
    hypothetical_incremental_retained_accounts: float
    intervention_cost: float
    hypothetical_retained_value: float | None
    hypothetical_net_value: float | None
    sensitivity: dict[str, float | None]
    scenario_cases: dict[str, dict[str, float | None]]
    limitations: list[str]


class MonthlyLabPlanInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_tier: str = Field(min_length=1, max_length=40)
    opening_relations: int = Field(ge=0, le=100_000)
    new_relations: int = Field(ge=0, le=100_000)
    loss_events: int = Field(ge=0, le=100_000)
    reactivations: int = Field(ge=0, le=100_000)
    opening_cohort_loss_any: int = Field(ge=0, le=100_000)
    opening_cohort_loss_at_close: int = Field(ge=0, le=100_000)
    assumed_monthly_value: float = Field(default=0, ge=0, le=10_000_000, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_plan_bridge(self):
        if self.loss_events > self.opening_relations + self.new_relations + self.reactivations:
            raise ValueError("Plan losses cannot exceed available opening, new, and reactivated relations.")
        if self.opening_cohort_loss_any > self.opening_relations:
            raise ValueError("Opening-cohort losses cannot exceed the opening plan base.")
        if self.opening_cohort_loss_at_close > self.opening_cohort_loss_any:
            raise ValueError("Opening-cohort relations lost at close cannot exceed those lost at any time.")
        return self


class MonthlyLabScenarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    plans: list[MonthlyLabPlanInput] = Field(min_length=1, max_length=20)
    opening_customers: int = Field(ge=0, le=100_000)
    new_customers: int = Field(ge=0, le=100_000)
    customer_loss_events: int = Field(ge=0, le=100_000)
    customer_reactivations: int = Field(ge=0, le=100_000)
    opening_customer_loss_any: int = Field(ge=0, le=100_000)
    opening_customer_loss_at_close: int = Field(ge=0, le=100_000)
    portfolio_expansions: int = Field(ge=0, le=100_000)
    portfolio_contractions: int = Field(ge=0, le=100_000)
    possible_upgrades: int = Field(ge=0, le=100_000)
    possible_downgrades: int = Field(ge=0, le=100_000)
    assumed_customer_monthly_value: float = Field(default=0, ge=0, le=10_000_000, allow_inf_nan=False)
    assumed_acquisition_cost_per_customer: float = Field(default=0, ge=0, le=10_000_000, allow_inf_nan=False)
    assumed_retention_cost_per_account: float = Field(default=0, ge=0, le=10_000_000, allow_inf_nan=False)
    assumed_uptake_pct: float = Field(default=0, ge=0, le=1, allow_inf_nan=False)
    assumed_incremental_retention_lift_pct: float = Field(default=0, ge=0, le=1, allow_inf_nan=False)
    horizon_months: int = Field(default=1, ge=1, le=36)

    @field_validator("plans")
    @classmethod
    def unique_plan_tiers(cls, plans):
        tiers = [item.plan_tier for item in plans]
        if len(tiers) != len(set(tiers)):
            raise ValueError("Each plan tier must appear once in the scenario.")
        return plans

    @model_validator(mode="after")
    def validate_customer_bridge(self):
        plan_open = sum(item.opening_relations for item in self.plans)
        plan_new = sum(item.new_relations for item in self.plans)
        plan_losses = sum(item.loss_events for item in self.plans)
        plan_returns = sum(item.reactivations for item in self.plans)
        if self.customer_loss_events > plan_losses:
            raise ValueError("Complete customer losses cannot exceed plan relation losses.")
        if self.new_customers > plan_new:
            raise ValueError("New customers cannot exceed newly acquired plan relations.")
        if self.customer_loss_events > plan_open + self.new_customers + self.customer_reactivations:
            raise ValueError("Customer losses exceed the available opening, new, and reactivated customer base.")
        if self.opening_customer_loss_any > self.opening_customers:
            raise ValueError("Opening-cohort customer losses cannot exceed the opening customer base.")
        if self.opening_customer_loss_at_close > self.opening_customer_loss_any:
            raise ValueError("Opening-cohort customers lost at close cannot exceed those lost at any time.")
        if self.opening_customer_loss_any > self.customer_loss_events:
            raise ValueError("Opening-cohort customer losses cannot exceed total customer loss events.")
        if self.customer_reactivations > plan_returns + plan_new:
            raise ValueError("Customer reactivations must be supported by plan reactivations or new relations.")
        if self.portfolio_expansions > plan_new + plan_returns:
            raise ValueError("Portfolio expansions cannot exceed new or reactivated plan relations.")
        if self.portfolio_contractions > plan_losses:
            raise ValueError("Portfolio contractions cannot exceed plan losses.")
        return self


class MonthlyLabScenarioResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    evidence_classification: str
    month: str
    observed_baseline: dict[str, Any]
    scenario: dict[str, Any]
    comparison: dict[str, Any]
    assumptions: MonthlyLabScenarioRequest
    limitations: list[str]
