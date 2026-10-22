import { describe, expect, it } from 'vitest'
import { formatScenarioUnits, scenarioRequestFromForm, type ScenarioFormValues } from './features/scenario'

const form: ScenarioFormValues = {
  eligible_accounts: '100',
  operational_capacity: '50',
  budget: '2500',
  cost_per_contact: '100',
  assumed_uptake_pct: '60',
  assumed_effectiveness_pct: '10',
  assumed_monthly_value_per_retained_account: '500',
  retention_horizon_months: '3',
}

describe('production scenario helpers', () => {
  it('converts percentage points to an incremental proportion and preserves user units', () => {
    expect(scenarioRequestFromForm(form)).toEqual({
      eligible_accounts: 100,
      operational_capacity: 50,
      budget: 2500,
      cost_per_contact: 100,
      assumed_uptake_pct: 0.6,
      assumed_effectiveness: 0.1,
      assumed_monthly_value_per_retained_account: 500,
      retention_horizon_months: 3,
    })
  })

  it('formats scenario amounts without asserting a currency', () => {
    expect(formatScenarioUnits(1250)).toBe('1,250 units')
    expect(formatScenarioUnits(2.5)).toBe('2.5 units')
  })
})
