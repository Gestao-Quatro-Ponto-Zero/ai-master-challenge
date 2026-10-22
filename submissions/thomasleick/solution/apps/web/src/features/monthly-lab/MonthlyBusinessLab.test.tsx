import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { MonthlyLabScenario, PortfolioPeriod } from '../../contracts'

const runMonthlyLabScenario = vi.fn()
vi.mock('../../lib/api', () => ({ runMonthlyLabScenario: (...args: unknown[]) => runMonthlyLabScenario(...args) }))
import { MonthlyBusinessLab } from './MonthlyBusinessLab'

const plans = ['Basic', 'Enterprise', 'Pro'].map((plan_tier, index) => ({
  plan_tier, opening_relations: 10 + index, new_relations: 2, reactivations: 0,
  gross_loss_events: index === 0 ? 1 : 0, opening_relations_lost_any_time: index === 0 ? 1 : 0,
  opening_relations_lost_at_close: index === 0 ? 1 : 0, closing_relations: 11 + index,
  opening_cohort_loss_rate_pct: index === 0 ? 10 : 0,
}))
const row = {
  period: '2024-01', period_type: 'MONTHLY', start_date: '2024-01-01', end_date: '2024-01-31',
  opening_plan_relations: 33, new_plan_relationships: 6, reactivated_plan_relationships: 0,
  gross_plan_relation_loss_events: 1, opening_relations_lost_any_time: 1, opening_relations_lost_at_close: 1,
  unique_plan_relations_with_loss_events: 1, closing_plan_relations: 38, net_change: 5,
  plan_relation_bridge_residual: 0, opening_cohort_churn_any_pct: 3.03, opening_cohort_churn_at_close_pct: 3.03,
  opening_relations_lost_then_active_at_close: 0, opening_customers: 20, closing_customers: 21,
  opening_customers_lost_any_time: 1, opening_customers_lost_at_close: 1,
  opening_cohort_customer_churn_any_pct: 5, opening_cohort_customer_churn_at_close_pct: 5,
  gross_customer_churn_events: 1, new_customers: 3, customer_reactivations: 0, customer_bridge_residual: 0,
  plan_reactivations: 0, possible_upgrade_candidates: 1, possible_downgrade_candidates: 0,
  portfolio_expansion_events: 2, portfolio_contraction_events: 1, methodology: 'Conditional date reconstruction',
  plan_segments: plans, account_segments: { industry: [], country: [], referral_source: [] },
} as PortfolioPeriod

const result = {
  status: 'SCENARIO_ONLY', evidence_classification: 'HYPOTHETICAL_USER_ASSUMPTIONS', month: '2024-01',
  observed_baseline: { closing_customers: 21, closing_plan_relations: 38 },
  scenario: {
    closing_customers: 21, closing_plan_relations: 38, customer_cohort_gross_loss_rate_pct: 5,
    customer_cohort_closing_loss_rate_pct: 5, plan_cohort_gross_loss_rate_pct: 3.03,
    plan_cohort_closing_loss_rate_pct: 3.03, monthly_modeled_opening_run_rate: null,
    monthly_modeled_closing_run_rate: null, modeled_protected_customer_value: null,
    modeled_net_contribution: null,
    scenario_cases: Object.fromEntries(['conservative', 'base', 'optimistic'].map((key) => [key, {
      assumed_uptake_pct: 25, assumed_incremental_lift_pct_points: 5,
      incremental_customers_retained_equivalent: 0.1, modeled_protected_customer_value: null,
      modeled_retention_cost: 0, modeled_acquisition_cost: 0, modeled_net_contribution: null,
    }])),
  },
  comparison: { customer_closing_base_delta: 0, plan_closing_base_delta: 0 },
  assumptions: {}, limitations: ['Scenario assumptions only.'],
} as unknown as MonthlyLabScenario

describe('MonthlyBusinessLab', () => {
  let container: HTMLDivElement
  let root: Root
  beforeEach(() => {
    Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true })
    container = document.createElement('div'); document.body.append(container); root = createRoot(container)
    runMonthlyLabScenario.mockReset().mockResolvedValue(result)
  })
  afterEach(async () => { await act(async () => root.unmount()); container.remove() })

  it('keeps the real selected-month baseline separate and submits assumptions to the API', async () => {
    await act(async () => root.render(<MonthlyBusinessLab rows={[row]} />))
    expect(container.querySelector('[data-testid="observed-mode"]')?.textContent).toContain('CONDITIONAL DATE RECONSTRUCTION')
    expect(container.textContent).toContain('Opening customers20')
    const scenarioTab = [...container.querySelectorAll('[role="tab"]')].find((item) => item.textContent?.includes('SCENARIO MODE')) as HTMLButtonElement
    await act(async () => scenarioTab.click())
    const form = container.querySelector('form')!
    await act(async () => form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
    expect(runMonthlyLabScenario).toHaveBeenCalledOnce()
    expect(runMonthlyLabScenario.mock.calls[0][0]).toMatchObject({ month: '2024-01', opening_customers: 20, plans: expect.arrayContaining([expect.objectContaining({ plan_tier: 'Basic', opening_relations: 10 })]) })
    expect(container.querySelector('[data-testid="scenario-results"]')?.textContent).toContain('SCENARIO ONLY')
    expect(container.querySelector('[data-testid="scenario-results"]')?.textContent).toContain('Not causal benefit or observed revenue')
  })

  it('shows API validation failures instead of presenting an uncomputed scenario', async () => {
    runMonthlyLabScenario.mockRejectedValueOnce(new Error('Impossible scenario flow'))
    await act(async () => root.render(<MonthlyBusinessLab rows={[row]} />))
    const tab = [...container.querySelectorAll('[role="tab"]')].find((item) => item.textContent?.includes('SCENARIO MODE')) as HTMLButtonElement
    await act(async () => tab.click())
    const form = container.querySelector('form')!
    await act(async () => form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
    expect(container.querySelector('[role="alert"]')?.textContent).toContain('Impossible scenario flow')
    expect(container.querySelector('[data-testid="scenario-results"]')).toBeNull()
  })
})
