import type { ScenarioInput } from '../contracts'

export type ScenarioFormValues = {
  eligible_accounts: string
  operational_capacity: string
  budget: string
  cost_per_contact: string
  assumed_uptake_pct: string
  assumed_effectiveness_pct: string
  assumed_monthly_value_per_retained_account: string
  retention_horizon_months: string
}

export function scenarioRequestFromForm(form: ScenarioFormValues): ScenarioInput {
  return {
    eligible_accounts: Number(form.eligible_accounts),
    operational_capacity: Number(form.operational_capacity),
    budget: Number(form.budget),
    cost_per_contact: Number(form.cost_per_contact),
    assumed_uptake_pct: Number(form.assumed_uptake_pct) / 100,
    assumed_effectiveness: Number(form.assumed_effectiveness_pct) / 100,
    assumed_monthly_value_per_retained_account: Number(form.assumed_monthly_value_per_retained_account),
    retention_horizon_months: Number(form.retention_horizon_months),
  }
}

export function formatScenarioUnits(value: number): string {
  return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value)} units`
}
