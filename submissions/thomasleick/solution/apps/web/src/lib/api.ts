import type { Analysis, BusinessInvestigation, ContractChurn, DailyPortfolioChurn, G4CustomerChurn, HistoricalChurn, MonthlyLabScenario, MonthlyLabScenarioInput, Reconciliation, Scenario, ScenarioInput } from '../contracts'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const getAnalysis = () => request<Analysis>('/api/analysis')
export const getBusinessInvestigation = () => request<BusinessInvestigation>('/api/business-investigation')
export const getHistoricalChurn = () => request<HistoricalChurn>('/api/historical-churn')
export const getG4CustomerChurn = () => request<G4CustomerChurn>('/api/g4-customer-churn')
export const getDailyPortfolioChurn = () => request<DailyPortfolioChurn>('/api/daily-portfolio-churn')
export const getTransitionAudit = () => request<Record<string, any>>('/api/transition-audit')
export const getContractChurn = () => request<ContractChurn>('/api/contract-churn')
export const getReconciliation = () => request<Reconciliation>('/api/accounts/reconciliation?limit=12')
export const runScenario = (input: ScenarioInput) =>
  request<Scenario>('/api/scenarios/retention', { method: 'POST', body: JSON.stringify(input) })
export const runMonthlyLabScenario = (input: MonthlyLabScenarioInput) =>
  request<MonthlyLabScenario>('/api/monthly-lab/scenario', { method: 'POST', body: JSON.stringify(input) })
