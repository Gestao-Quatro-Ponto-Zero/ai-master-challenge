from __future__ import annotations

import os
import json
import sys
import csv
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from analytics.engine import build_analysis
from schemas.contracts import AnalysisResponse, BusinessInvestigationResponse, ContractChurnResponse, DailyPortfolioChurnResponse, G4CustomerChurnResponse, HistoricalChurnResponse, MonthlyLabScenarioRequest, MonthlyLabScenarioResponse, ReconciliationResponse, ScenarioRequest, ScenarioResponse

APP_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.getenv("RAVENSTACK_DATA_DIR", APP_ROOT / "data" / "raw"))
BUSINESS_DATA_PATH = APP_ROOT / "analysis" / "business_drivers" / "outputs" / "g4-alignment" / "business-investigation.json"
HISTORICAL_MODULE = APP_ROOT / "analysis" / "historical_churn"
CONTRACT_CHURN_MODULE = APP_ROOT / "analysis" / "contract_churn"
G4_CUSTOMER_CHURN_MODULE = APP_ROOT / "analysis" / "g4_customer_churn"
DAILY_PORTFOLIO_MODULE = APP_ROOT / "analysis" / "daily_portfolio_churn"
TRANSITION_AUDIT_PATH = APP_ROOT / "analysis" / "transition_audit" / "outputs" / "transition-audit.json"
sys.path.insert(0, str(HISTORICAL_MODULE))
from reconstruct import reconstruct as reconstruct_historical_churn  # noqa: E402
sys.path.insert(0, str(CONTRACT_CHURN_MODULE))
from investigate import investigate as investigate_contract_churn  # noqa: E402
sys.path.insert(0, str(G4_CUSTOMER_CHURN_MODULE))
from analyze import analyze as analyze_g4_customer_churn  # noqa: E402
sys.path.insert(0, str(DAILY_PORTFOLIO_MODULE))
from engine import analyze as analyze_daily_portfolio_churn  # noqa: E402
from key_moments import build_key_moments  # noqa: E402

app = FastAPI(
    title="RavenStack — The Churn Paradox",
    description="Evidence-first churn investigation and transparent retention scenarios.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

try:
    ANALYSIS = build_analysis(DATA_DIR)
except Exception as exc:
    # Fail startup visibly rather than returning invented placeholder metrics.
    raise RuntimeError(f"Could not initialize source-data analysis from {DATA_DIR}: {exc}") from exc

try:
    BUSINESS_INVESTIGATION = json.loads(BUSINESS_DATA_PATH.read_text(encoding="utf-8"))
except Exception as exc:
    raise RuntimeError(f"Could not load generated business investigation artifact at {BUSINESS_DATA_PATH}: {exc}") from exc

try:
    HISTORICAL_CHURN = reconstruct_historical_churn(DATA_DIR)
except Exception as exc:
    raise RuntimeError(f"Could not reconstruct historical churn from source data at {DATA_DIR}: {exc}") from exc

try:
    CONTRACT_CHURN = investigate_contract_churn(DATA_DIR)
except Exception as exc:
    raise RuntimeError(f"Could not reconcile account and subscription records from {DATA_DIR}: {exc}") from exc

try:
    G4_CUSTOMER_CHURN = analyze_g4_customer_churn(DATA_DIR)
except Exception as exc:
    raise RuntimeError(f"Could not reconstruct G4 customer churn evidence from {DATA_DIR}: {exc}") from exc

try:
    DAILY_PORTFOLIO_CHURN = analyze_daily_portfolio_churn(DATA_DIR)
except Exception as exc:
    raise RuntimeError(f"Could not reconstruct daily customer-plan portfolio from {DATA_DIR}: {exc}") from exc

def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


try:
    KEY_MOMENTS = build_key_moments(
        DAILY_PORTFOLIO_CHURN,
        _read_csv_rows(DATA_DIR / "ravenstack_churn_events.csv"),
        _read_csv_rows(DATA_DIR / "ravenstack_accounts.csv"),
    )
except Exception as exc:
    raise RuntimeError(f"Could not derive deterministic monthly key moments from {DATA_DIR}: {exc}") from exc

try:
    TRANSITION_AUDIT = json.loads(TRANSITION_AUDIT_PATH.read_text(encoding="utf-8"))
except Exception as exc:
    raise RuntimeError(f"Could not load subscription transition flag audit at {TRANSITION_AUDIT_PATH}: {exc}") from exc


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "analysis": "loaded", "data": "source-csv"}


@app.get("/api/analysis", response_model=AnalysisResponse)
def analysis() -> dict[str, Any]:
    return {key: value for key, value in ANALYSIS.items() if key != "_internal"}


@app.get("/api/business-investigation", response_model=BusinessInvestigationResponse)
def business_investigation() -> dict[str, Any]:
    return BUSINESS_INVESTIGATION


@app.get("/api/historical-churn", response_model=HistoricalChurnResponse)
def historical_churn() -> dict[str, Any]:
    return HISTORICAL_CHURN


@app.get("/api/contract-churn", response_model=ContractChurnResponse)
def contract_churn() -> dict[str, Any]:
    return CONTRACT_CHURN


@app.get("/api/g4-customer-churn", response_model=G4CustomerChurnResponse)
def g4_customer_churn() -> dict[str, Any]:
    return G4_CUSTOMER_CHURN


@app.get("/api/daily-portfolio-churn", response_model=DailyPortfolioChurnResponse)
def daily_portfolio_churn() -> dict[str, Any]:
    # Runtime API omits interval internals and already-generated snapshots; daily and period results remain reproducible.
    response = {key: value for key, value in DAILY_PORTFOLIO_CHURN.items() if key not in {"intervals", "active_snapshots", "customer_snapshots"}}
    response["key_moments"] = KEY_MOMENTS
    return response


@app.get("/api/transition-audit")
def transition_audit() -> dict[str, Any]:
    return TRANSITION_AUDIT


@app.get("/api/accounts/reconciliation", response_model=ReconciliationResponse)
def reconciliation(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, Any]:
    frame = ANALYSIS["_internal"]["account_view"].copy()
    frame = frame.loc[frame["status_comparison"] != "neither"]
    frame = frame.sort_values(["active_record_mrr_sum", "account_id"], ascending=[False, True]).head(limit)
    records = []
    for row in frame.to_dict(orient="records"):
        records.append({
            "account_id": str(row["account_id"]), "account_name": str(row["account_name"]),
            "industry": str(row["industry"]), "country": str(row["country"]),
            "churn_flag": bool(row["_flag"]), "churn_event_count": int(row["churn_event_count"]),
            "status_comparison": str(row["status_comparison"]),
            "active_subscription_rows": int(row["active_subscription_rows"]),
            "active_record_mrr_sum": float(row["active_record_mrr_sum"]),
            "interpretation": "Record-reconciliation example only. Not an account risk score or verified revenue exposure.",
        })
    return {
        "warning": "Accounts are shown because churn_flag and event history disagree. Active MRR sums are raw subscription-row values, not a revenue exposure measure; currency and snapshot semantics are unconfirmed.",
        "returned": len(records), "accounts": records,
    }


@app.post("/api/scenarios/retention", response_model=ScenarioResponse)
def retention_scenario(request: ScenarioRequest) -> dict[str, Any]:
    affordable = request.operational_capacity
    if request.cost_per_contact > 0:
        affordable = min(affordable, int(request.budget // request.cost_per_contact))
    selected = min(request.eligible_accounts, affordable)
    participants = selected * request.assumed_uptake_pct
    expected_retained = participants * request.assumed_effectiveness
    cost = selected * request.cost_per_contact
    value = None
    net = None
    sensitivity: dict[str, float | None] = {"low_net_value": None, "base_net_value": None, "high_net_value": None}
    scenario_cases: dict[str, dict[str, float | None]] = {}
    cases = {
        "conservative": (min(1.0, request.assumed_uptake_pct * 0.5), min(1.0, request.assumed_effectiveness * 0.5)),
        "base": (request.assumed_uptake_pct, request.assumed_effectiveness),
        "optimistic": (min(1.0, request.assumed_uptake_pct * 1.5), min(1.0, request.assumed_effectiveness * 1.5)),
    }
    for name, (uptake, lift) in cases.items():
        case_participants = selected * uptake
        case_retained = case_participants * lift
        case_value = case_retained * request.assumed_monthly_value_per_retained_account * request.retention_horizon_months if request.assumed_monthly_value_per_retained_account > 0 else None
        case_net = case_value - cost if case_value is not None else None
        break_even_value = cost / (case_retained * request.retention_horizon_months) if case_retained and request.retention_horizon_months else None
        scenario_cases[name] = {
            "assumed_uptake_pct": round(uptake * 100, 4),
            "assumed_incremental_lift_pct_points": round(lift * 100, 4),
            "expected_participants": round(case_participants, 4),
            "hypothetical_incremental_retained_accounts": round(case_retained, 4),
            "gross_hypothetical_value": round(case_value, 2) if case_value is not None else None,
            "intervention_cost": round(cost, 2),
            "hypothetical_net_value": round(case_net, 2) if case_net is not None else None,
            "break_even_monthly_value_per_retained_account": round(break_even_value, 2) if break_even_value is not None else None,
        }
    if request.assumed_monthly_value_per_retained_account > 0:
        value = expected_retained * request.assumed_monthly_value_per_retained_account * request.retention_horizon_months
        net = value - cost
        sensitivity = {
            "low_net_value": scenario_cases["conservative"]["hypothetical_net_value"],
            "base_net_value": net,
            "high_net_value": scenario_cases["optimistic"]["hypothetical_net_value"],
        }
    limitations = [
        "Effectiveness is interpreted as a user-supplied incremental percentage-point retention lift versus an untreated baseline; it is not observed or causal uplift.",
        "Uptake, contact cost, eligible-account count, currency unit, retained value and horizon are user-supplied assumptions.",
        "Conservative/base/optimistic cases multiply the base uptake and lift by 0.5×/1.0×/1.5× (capped at 100%); these are sensitivity scenarios, not confidence intervals.",
        "Value arithmetic assumes each incremental retained account contributes the assumed monthly value for the full selected horizon.",
        "The source tables do not establish reliable account-level recurring revenue exposure.",
    ]
    if request.assumed_monthly_value_per_retained_account == 0:
        limitations.append("Retained-account monthly value is unset; hypothetical value and net benefit are therefore UNKNOWN.")
    return {
        "status": "HYPOTHETICAL", "currency_unit": "user-supplied units", "assumptions": request,
        "selected_accounts": selected,
        "expected_participants": round(participants, 2),
        "hypothetical_incremental_retained_accounts": round(expected_retained, 2), "intervention_cost": round(cost, 2),
        "hypothetical_retained_value": round(value, 2) if value is not None else None,
        "hypothetical_net_value": round(net, 2) if net is not None else None,
        "sensitivity": {key: round(val, 2) if val is not None else None for key, val in sensitivity.items()},
        "scenario_cases": scenario_cases,
        "limitations": limitations,
    }


@app.post("/api/monthly-lab/scenario", response_model=MonthlyLabScenarioResponse)
def monthly_lab_scenario(request: MonthlyLabScenarioRequest) -> dict[str, Any]:
    observed = next((row for row in DAILY_PORTFOLIO_CHURN["periods"]["MONTHLY"] if row["period"] == request.month), None)
    if observed is None:
        raise HTTPException(status_code=404, detail="Selected month is outside the observed monthly ledger.")
    observed_tiers = {row["plan_tier"]: row for row in observed["plan_segments"]}
    requested_tiers = {row.plan_tier: row for row in request.plans}
    if set(requested_tiers) != set(observed_tiers):
        raise HTTPException(status_code=422, detail="Scenario must include every observed plan tier exactly once.")

    # Opening bases remain immutable and must match the source ledger exactly.
    for tier, plan in requested_tiers.items():
        if plan.opening_relations != observed_tiers[tier]["opening_relations"]:
            raise HTTPException(status_code=422, detail=f"Opening base for {tier} is observed and cannot be edited.")
        if plan.opening_cohort_loss_any > plan.loss_events:
            raise HTTPException(status_code=422, detail=f"Opening cohort losses for {tier} exceed monthly loss events.")
    if sum(plan.opening_relations for plan in request.plans) != observed["opening_plan_relations"]:
        raise HTTPException(status_code=422, detail="Plan-tier opening bases do not reconcile to the observed monthly total.")
    if request.opening_customers != observed["opening_customers"]:
        raise HTTPException(status_code=422, detail="Opening customer base is observed and cannot be edited.")

    plans_out = []
    opening_value = closing_value = modeled_loss_value = acquisition_value = 0.0
    plan_values_set = any(p.assumed_monthly_value > 0 for p in request.plans)
    financial_inputs_set = request.assumed_customer_monthly_value > 0 or plan_values_set
    for tier, plan in requested_tiers.items():
        source = observed_tiers[tier]
        closing = plan.opening_relations + plan.new_relations + plan.reactivations - plan.loss_events
        opening_value += plan.opening_relations * plan.assumed_monthly_value
        closing_value += closing * plan.assumed_monthly_value
        modeled_loss_value += plan.loss_events * plan.assumed_monthly_value
        acquisition_value += plan.new_relations * plan.assumed_monthly_value
        plans_out.append({
            "plan_tier": tier,
            "opening_relations": plan.opening_relations,
            "new_relations": plan.new_relations,
            "loss_events": plan.loss_events,
            "reactivations": plan.reactivations,
            "opening_cohort_loss_any": plan.opening_cohort_loss_any,
            "opening_cohort_loss_at_close": plan.opening_cohort_loss_at_close,
            "closing_relations": closing,
            "opening_cohort_gross_loss_rate_pct": round(plan.opening_cohort_loss_any / plan.opening_relations * 100, 4) if plan.opening_relations else None,
            "opening_cohort_closing_loss_rate_pct": round(plan.opening_cohort_loss_at_close / plan.opening_relations * 100, 4) if plan.opening_relations else None,
            "assumed_monthly_value": plan.assumed_monthly_value,
            "observed_monthly_baseline": source,
        })

    closing_customers = request.opening_customers + request.new_customers + request.customer_reactivations - request.customer_loss_events
    opening_plan_relations = sum(row.opening_relations for row in request.plans)
    new_plan_relations = sum(row.new_relations for row in request.plans)
    reactivated_plan_relations = sum(row.reactivations for row in request.plans)
    plan_loss_events = sum(row.loss_events for row in request.plans)
    opening_cohort_plan_losses = sum(row.opening_cohort_loss_any for row in request.plans)
    opening_cohort_plan_losses_close = sum(row.opening_cohort_loss_at_close for row in request.plans)
    modeled_acquisition_cost = request.new_customers * request.assumed_acquisition_cost_per_customer
    modeled_retention_eligible = request.opening_customer_loss_any
    modeled_retention_cost = modeled_retention_eligible * request.assumed_uptake_pct * request.assumed_retention_cost_per_account
    acquired_customer_value = request.new_customers * request.assumed_customer_monthly_value * request.horizon_months
    scenario_cases = {}
    for name, multiplier in (("conservative", 0.5), ("base", 1.0), ("optimistic", 1.5)):
        uptake = min(1.0, request.assumed_uptake_pct * multiplier)
        lift = min(1.0, request.assumed_incremental_retention_lift_pct * multiplier)
        retained_customers = modeled_retention_eligible * uptake * lift
        protected_customer_value = retained_customers * request.assumed_customer_monthly_value * request.horizon_months
        protected_plan_relations = sum(
            plan.opening_cohort_loss_any * uptake * lift * plan.assumed_monthly_value * request.horizon_months
            for plan in request.plans
        )
        retention_cost = modeled_retention_eligible * uptake * request.assumed_retention_cost_per_account
        net_modeled_contribution = protected_customer_value + acquired_customer_value - retention_cost - modeled_acquisition_cost
        break_even_monthly_value = (
            max(0.0, retention_cost + modeled_acquisition_cost - acquired_customer_value)
            / (retained_customers * request.horizon_months)
            if retained_customers > 0 else None
        )
        scenario_cases[name] = {
            "assumed_uptake_pct": round(uptake * 100, 4),
            "assumed_incremental_lift_pct_points": round(lift * 100, 4),
            "incremental_customers_retained_equivalent": round(retained_customers, 4),
            "modeled_protected_plan_value_over_horizon": round(protected_plan_relations, 2) if any(p.assumed_monthly_value > 0 for p in request.plans) else None,
            "modeled_protected_customer_value": round(protected_customer_value, 2) if request.assumed_customer_monthly_value > 0 else None,
            "modeled_acquired_customer_value": round(acquired_customer_value, 2) if request.assumed_customer_monthly_value > 0 else None,
            "modeled_retention_cost": round(retention_cost, 2),
            "modeled_acquisition_cost": round(modeled_acquisition_cost, 2),
            "modeled_net_contribution": round(net_modeled_contribution, 2) if request.assumed_customer_monthly_value > 0 else None,
            "break_even_monthly_value_per_retained_customer": round(break_even_monthly_value, 2) if break_even_monthly_value is not None else None,
        }
    base = scenario_cases["base"]
    assumptions = request.model_dump()
    observed_baseline = {
        "month": request.month,
        "evidence_classification": observed["methodology"],
        "opening_customers": observed["opening_customers"],
        "new_customers": observed["new_customers"],
        "customer_loss_events": observed["gross_customer_churn_events"],
        "customer_reactivations": observed["customer_reactivations"],
        "opening_customer_loss_any": observed["opening_customers_lost_any_time"],
        "opening_customer_loss_at_close": observed["opening_customers_lost_at_close"],
        "closing_customers": observed["closing_customers"],
        "opening_plan_relations": observed["opening_plan_relations"],
        "new_plan_relationships": observed["new_plan_relationships"],
        "plan_loss_events": observed["gross_plan_relation_loss_events"],
        "plan_reactivations": observed["plan_reactivations"],
        "opening_cohort_plan_losses_any": observed["opening_relations_lost_any_time"],
        "opening_cohort_plan_losses_at_close": observed["opening_relations_lost_at_close"],
        "closing_plan_relations": observed["closing_plan_relations"],
        "plan_bridge_residual": observed["plan_relation_bridge_residual"],
        "customer_bridge_residual": observed["customer_bridge_residual"],
    }
    scenario = {
        "opening_customers": request.opening_customers,
        "new_customers": request.new_customers,
        "customer_loss_events": request.customer_loss_events,
        "customer_reactivations": request.customer_reactivations,
        "opening_customer_loss_any": request.opening_customer_loss_any,
        "opening_customer_loss_at_close": request.opening_customer_loss_at_close,
        "closing_customers": closing_customers,
        "customer_cohort_gross_loss_rate_pct": round(request.opening_customer_loss_any / request.opening_customers * 100, 4) if request.opening_customers else None,
        "customer_cohort_closing_loss_rate_pct": round(request.opening_customer_loss_at_close / request.opening_customers * 100, 4) if request.opening_customers else None,
        "opening_plan_relations": opening_plan_relations,
        "new_plan_relationships": new_plan_relations,
        "plan_loss_events": plan_loss_events,
        "plan_reactivations": reactivated_plan_relations,
        "opening_cohort_plan_losses_any": opening_cohort_plan_losses,
        "opening_cohort_plan_losses_at_close": opening_cohort_plan_losses_close,
        "closing_plan_relations": opening_plan_relations + new_plan_relations + reactivated_plan_relations - plan_loss_events,
        "plan_cohort_gross_loss_rate_pct": round(opening_cohort_plan_losses / opening_plan_relations * 100, 4) if opening_plan_relations else None,
        "plan_cohort_closing_loss_rate_pct": round(opening_cohort_plan_losses_close / opening_plan_relations * 100, 4) if opening_plan_relations else None,
        "portfolio_expansions": request.portfolio_expansions,
        "portfolio_contractions": request.portfolio_contractions,
        "possible_upgrades": request.possible_upgrades,
        "possible_downgrades": request.possible_downgrades,
        "plans": plans_out,
        "monthly_modeled_opening_run_rate": round(opening_value, 2) if plan_values_set else None,
        "monthly_modeled_closing_run_rate": round(closing_value, 2) if plan_values_set else None,
        "monthly_modeled_gross_loss_value": round(modeled_loss_value, 2) if plan_values_set else None,
        "monthly_modeled_acquisition_value": round(acquisition_value, 2) if plan_values_set else None,
        "modeled_acquisition_cost": round(modeled_acquisition_cost, 2),
        "modeled_retention_cost": round(modeled_retention_cost, 2),
        "modeled_protected_customer_value": base["modeled_protected_customer_value"],
        "modeled_protected_plan_value_over_horizon": base["modeled_protected_plan_value_over_horizon"],
        "modeled_net_contribution": base["modeled_net_contribution"],
        "financial_model_status": "USER_ASSUMPTIONS_ONLY" if financial_inputs_set else "UNSET",
        "scenario_cases": scenario_cases,
    }
    return {
        "status": "SCENARIO_ONLY",
        "evidence_classification": "HYPOTHETICAL_USER_ASSUMPTIONS; OBSERVED_BASELINE_IMMUTABLE",
        "month": request.month,
        "observed_baseline": observed_baseline,
        "scenario": scenario,
        "comparison": {
            "customer_closing_base_delta": closing_customers - observed["closing_customers"],
            "customer_closing_base_delta_pct": round((closing_customers - observed["closing_customers"]) / observed["closing_customers"] * 100, 4) if observed["closing_customers"] else None,
            "plan_closing_base_delta": scenario["closing_plan_relations"] - observed["closing_plan_relations"],
            "plan_closing_base_delta_pct": round((scenario["closing_plan_relations"] - observed["closing_plan_relations"]) / observed["closing_plan_relations"] * 100, 4) if observed["closing_plan_relations"] else None,
            "customer_loss_events_delta": request.customer_loss_events - observed["gross_customer_churn_events"],
            "customer_loss_events_delta_pct": round((request.customer_loss_events - observed["gross_customer_churn_events"]) / observed["gross_customer_churn_events"] * 100, 4) if observed["gross_customer_churn_events"] else None,
            "plan_loss_events_delta": plan_loss_events - observed["gross_plan_relation_loss_events"],
            "plan_loss_events_delta_pct": round((plan_loss_events - observed["gross_plan_relation_loss_events"]) / observed["gross_plan_relation_loss_events"] * 100, 4) if observed["gross_plan_relation_loss_events"] else None,
            "monthly_modeled_run_rate_vs_observed": "NOT_COMPARABLE; observed recurring revenue is unreconciled",
        },
        "assumptions": assumptions,
        "limitations": [
            "Observed baseline is loaded from the date-reconstructed monthly ledger and is never overwritten by scenario inputs.",
            "Scenario flows are hypothetical plan-level proxies; possible upgrades and downgrades are separate annotations and are not added again to acquisition or loss counts.",
            "Plan values, customer values, acquisition cost, retention cost, uptake, lift and horizon are user assumptions; no causal uplift, actual revenue, profit, or ROI is measured.",
            "Modeled value assumes constant monthly value for the full horizon, with no discounting, margin, taxes, refunds, or partial-period adjustment.",
        ],
    }
