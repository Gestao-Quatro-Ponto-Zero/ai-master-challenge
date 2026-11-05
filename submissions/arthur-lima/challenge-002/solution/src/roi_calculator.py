"""Parametric ROI & TCO Simulator anchored on Out-of-Sample Selective Triage Rates.

Implements H4: separates empirical model metrics (coverage and error rate on
Dataset 2) from external operational assumptions, explicitly distinguishing
pure triage/routing savings (executed by the prototype) from conditional
assisted-handling savings, and allowing negative net outcomes when rework
exceeds gross savings.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class OperationalScenarioResult:
    scenario_name: str
    scope_type: str
    annual_tickets: int
    tier1_coverage_pct: float
    tier1_accuracy_pct: float
    tier2_coverage_pct: float
    tier3_coverage_pct: float
    manual_triage_min: float
    assisted_resolution_saved_min: float
    baseline_annual_hours: float
    baseline_annual_cost_brl: float
    gross_hours_saved: float
    rework_penalty_hours: float
    net_hours_saved: float
    fte_equivalent_freed: float
    gross_financial_savings_brl: float
    annual_ai_tco_brl: float
    net_annual_roi_brl: float
    payback_months: float


# H4 — Cálculo explícito de capacidade e ROI descontando retrabalho por erro de
# auto-roteamento e TCO anual de IA. Distingue o tempo de triagem/roteamento manual
# (executado pelo protótipo) de ganhos condicionais de assistência em resolução, e
# nunca trunca horas líquidas em zero (permitindo saldo negativo se o erro for alto).
def simulate_operational_roi(
    *,
    scenario_name: str = "Cenário Base (Triagem + Copilot N1/N2)",
    scope_type: str = "Triagem + Assistência Runbook",
    annual_tickets: int = 30000,
    tier1_coverage: float = 0.6095,
    tier1_accuracy: float = 0.9739,
    tier2_coverage: float = 0.2631,
    manual_triage_min: float = 4.0,
    assisted_resolution_saved_min: float = 4.0,
    manual_triage_and_handle_min: Optional[float] = None,
    tier1_residual_monitor_min: float = 0.5,
    tier2_copilot_review_min: float = 1.5,
    rework_Select_multiplier: float = 2.0,
    analyst_hourly_cost_brl: float = 65.0,
    monthly_ai_tco_brl: float = 6500.0,
    initial_setup_investment_brl: float = 45000.0,
) -> OperationalScenarioResult:
    """
    Computes net hours and financial impact under transparent operational assumptions:
    - `manual_triage_min`: time spent reading, classifying, checking policy, and routing a ticket.
    - `assisted_resolution_saved_min`: additional handling reduction from runbook checklists/precedents/drafts
      (set to `0.0` in Scenario 1 to isolate pure triage/routing executed directly by the prototype).
    - If `manual_triage_and_handle_min` is explicitly passed, it overrides `manual_triage_min + assisted_resolution_saved_min`.
    - Rework penalty is NOT clamped at zero: if `rework_hours > gross_saved_h`, `net_hours_saved` and
      `fte_equivalent_freed` become negative, exposing net operational degradation.
    """
    if annual_tickets < 0:
        raise ValueError("annual_tickets deve ser não-negativo.")
    t1_cov = max(0.0, min(1.0, float(tier1_coverage)))
    t2_cov = max(0.0, min(1.0 - t1_cov, float(tier2_coverage)))
    t3_cov = max(0.0, 1.0 - t1_cov - t2_cov)
    t1_acc = max(0.0, min(1.0, float(tier1_accuracy)))

    if manual_triage_and_handle_min is not None:
        effective_manual_min = float(manual_triage_and_handle_min)
        triage_min_used = min(float(manual_triage_min), effective_manual_min)
        assisted_min_used = max(0.0, effective_manual_min - triage_min_used)
    else:
        triage_min_used = max(0.0, float(manual_triage_min))
        assisted_min_used = max(0.0, float(assisted_resolution_saved_min))
        effective_manual_min = triage_min_used + assisted_min_used

    baseline_hours = (annual_tickets * effective_manual_min) / 60.0
    baseline_cost = baseline_hours * analyst_hourly_cost_brl

    n_tier1 = annual_tickets * t1_cov
    n_tier1_correct = n_tier1 * t1_acc
    n_tier1_error = n_tier1 * (1.0 - t1_acc)
    n_tier2 = annual_tickets * t2_cov

    tier1_gross_saved_h = (
        n_tier1_correct * max(0.0, effective_manual_min - tier1_residual_monitor_min)
    ) / 60.0
    tier2_gross_saved_h = (
        n_tier2 * max(0.0, effective_manual_min - tier2_copilot_review_min)
    ) / 60.0
    gross_saved_h = tier1_gross_saved_h + tier2_gross_saved_h

    rework_hours = (
        n_tier1_error * effective_manual_min * rework_Select_multiplier
    ) / 60.0
    # Unclamped net hours: negative when error rework exceeds gross savings
    net_saved_h = gross_saved_h - rework_hours

    # 1 FTE = 1,760 productive hours/year (~146.7h/month)
    fte_freed = net_saved_h / 1760.0
    gross_savings_brl = net_saved_h * analyst_hourly_cost_brl
    annual_tco_brl = monthly_ai_tco_brl * 12.0
    net_roi_brl = gross_savings_brl - annual_tco_brl

    monthly_net = net_roi_brl / 12.0
    if monthly_net > 0 and initial_setup_investment_brl > 0:
        payback = initial_setup_investment_brl / monthly_net
    elif initial_setup_investment_brl <= 0 and monthly_net >= 0:
        payback = 0.0
    else:
        payback = float("inf")

    return OperationalScenarioResult(
        scenario_name=scenario_name,
        scope_type=scope_type,
        annual_tickets=int(annual_tickets),
        tier1_coverage_pct=round(t1_cov * 100.0, 2),
        tier1_accuracy_pct=round(t1_acc * 100.0, 2),
        tier2_coverage_pct=round(t2_cov * 100.0, 2),
        tier3_coverage_pct=round(t3_cov * 100.0, 2),
        manual_triage_min=round(triage_min_used, 2),
        assisted_resolution_saved_min=round(assisted_min_used, 2),
        baseline_annual_hours=round(baseline_hours, 1),
        baseline_annual_cost_brl=round(baseline_cost, 2),
        gross_hours_saved=round(gross_saved_h, 1),
        rework_penalty_hours=round(rework_hours, 1),
        net_hours_saved=round(net_saved_h, 1),
        fte_equivalent_freed=round(fte_freed, 2),
        gross_financial_savings_brl=round(gross_savings_brl, 2),
        annual_ai_tco_brl=round(annual_tco_brl, 2),
        net_annual_roi_brl=round(net_roi_brl, 2),
        payback_months=round(payback, 2) if payback != float("inf") else float("inf"),
    )


def build_standard_roi_scenarios(
    tier1_coverage: float, tier1_accuracy: float, tier2_coverage: float
) -> List[Dict[str, object]]:
    """
    Generates 3 transparent scenarios anchored on empirical Dataset 2 rates:
    1. Pure Triage & Routing ONLY (4.0 min triage, 0.0 min resolution savings) — exact scope executed by the prototype.
    2. Operational Base (4.0 min triage + 4.0 min N1/N2 runbook/precedent acceleration = 8.0 min).
    3. Integrated Workflow Expansion (4.0 min triage + 8.0 min automated IAM/Storage provisioning = 12.0 min, conditional on future API integration).
    All 3 scenarios use a uniform rework penalty multiplier of 2.0x.
    """
    configs = [
        {
            "scenario_name": "1. Escopo Estrito do Protótipo (Apenas Triagem & Roteamento: 4,0 min + 0,0 min resolução)",
            "scope_type": "Executado pelo Protótipo (Triagem Pura)",
            "annual_tickets": 30000,
            "tier1_coverage": tier1_coverage,
            "tier1_accuracy": tier1_accuracy,
            "tier2_coverage": tier2_coverage,
            "manual_triage_min": 4.0,
            "assisted_resolution_saved_min": 0.0,
            "tier1_residual_monitor_min": 0.5,
            "tier2_copilot_review_min": 1.5,
            "rework_Select_multiplier": 2.0,
            "analyst_hourly_cost_brl": 65.0,
            "monthly_ai_tco_brl": 4500.0,
            "initial_setup_investment_brl": 35000.0,
        },
        {
            "scenario_name": "2. Base Operacional (Triagem 4,0 min + Aceleração Runbook/Precedente +4,0 min)",
            "scope_type": "Protótipo + Adoção do Runbook N1/N2",
            "annual_tickets": 30000,
            "tier1_coverage": tier1_coverage,
            "tier1_accuracy": tier1_accuracy,
            "tier2_coverage": tier2_coverage,
            "manual_triage_min": 4.0,
            "assisted_resolution_saved_min": 4.0,
            "tier1_residual_monitor_min": 0.5,
            "tier2_copilot_review_min": 2.0,
            "rework_Select_multiplier": 2.0,
            "analyst_hourly_cost_brl": 65.0,
            "monthly_ai_tco_brl": 6500.0,
            "initial_setup_investment_brl": 45000.0,
        },
        {
            "scenario_name": "3. Expansão Futura via API (Triagem 4,0 min + Provisionamento Automático IAM/ITSM +8,0 min)",
            "scope_type": "Hipotético (Requer Integração ITSM/AD)",
            "annual_tickets": 30000,
            "tier1_coverage": tier1_coverage,
            "tier1_accuracy": tier1_accuracy,
            "tier2_coverage": tier2_coverage,
            "manual_triage_min": 4.0,
            "assisted_resolution_saved_min": 8.0,
            "tier1_residual_monitor_min": 0.5,
            "tier2_copilot_review_min": 3.0,
            "rework_Select_multiplier": 2.0,
            "analyst_hourly_cost_brl": 65.0,
            "monthly_ai_tco_brl": 6500.0,
            "initial_setup_investment_brl": 45000.0,
        },
    ]
    rows = []
    for cfg in configs:
        res = simulate_operational_roi(**cfg)
        rows.append(
            {
                "Cenário": res.scenario_name,
                "Escopo Modelado": res.scope_type,
                "Triagem (min)": res.manual_triage_min,
                "Assistência Resolução (min)": res.assisted_resolution_saved_min,
                "Cobertura Tier 1 (%)": res.tier1_coverage_pct,
                "Precisão Tier 1 (%)": res.tier1_accuracy_pct,
                "Horas Base/Ano": res.baseline_annual_hours,
                "Horas Brutas Poupadas": res.gross_hours_saved,
                "(-) Horas Retrabalho Erro": res.rework_penalty_hours,
                "(=) Horas Líquidas/Ano": res.net_hours_saved,
                "FTEs Liberados": res.fte_equivalent_freed,
                "Economia Bruta (R$/ano)": res.gross_financial_savings_brl,
                "(-) TCO Anual IA (R$/ano)": res.annual_ai_tco_brl,
                "(=) Economia Líquida (R$/ano)": res.net_annual_roi_brl,
                "Payback Setup (meses)": res.payback_months,
            }
        )
    return rows
