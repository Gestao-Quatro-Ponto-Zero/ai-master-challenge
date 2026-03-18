import { supabase } from '../lib/supabaseClient';

export interface LLMBudget {
  id: string;
  name: string;
  organization_id: string | null;
  monthly_budget: number | null;
  token_limit: number | null;
  current_spend: number;
  current_tokens: number;
  period_start: string;
  period_end: string;
  alert_threshold: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateBudgetData {
  name: string;
  organization_id?: string | null;
  monthly_budget?: number | null;
  token_limit?: number | null;
  period_start: string;
  period_end: string;
  alert_threshold?: number;
}

export interface UpdateBudgetData {
  name?: string;
  monthly_budget?: number | null;
  token_limit?: number | null;
  period_start?: string;
  period_end?: string;
  alert_threshold?: number;
  is_active?: boolean;
}

export async function getBudgets(): Promise<LLMBudget[]> {
  const { data, error } = await supabase
    .from('llm_budgets')
    .select('*')
    .order('period_start', { ascending: false });
  if (error) throw new Error(error.message);
  return (data ?? []) as LLMBudget[];
}

export async function getActiveBudget(organizationId?: string | null): Promise<LLMBudget | null> {
  let query = supabase
    .from('llm_budgets')
    .select('*')
    .eq('is_active', true)
    .lte('period_start', new Date().toISOString())
    .gte('period_end',   new Date().toISOString());

  if (organizationId) {
    query = query.eq('organization_id', organizationId);
  } else {
    query = query.is('organization_id', null);
  }

  const { data, error } = await query.maybeSingle();
  if (error) throw new Error(error.message);
  return data as LLMBudget | null;
}

export async function createBudget(payload: CreateBudgetData): Promise<LLMBudget> {
  const { data, error } = await supabase
    .from('llm_budgets')
    .insert(payload)
    .select('*')
    .single();
  if (error) throw new Error(error.message);
  return data as LLMBudget;
}

export async function updateBudget(id: string, payload: UpdateBudgetData): Promise<LLMBudget> {
  const { data, error } = await supabase
    .from('llm_budgets')
    .update(payload)
    .eq('id', id)
    .select('*')
    .single();
  if (error) throw new Error(error.message);
  return data as LLMBudget;
}

export async function deleteBudget(id: string): Promise<void> {
  const { error } = await supabase.from('llm_budgets').delete().eq('id', id);
  if (error) throw new Error(error.message);
}

export async function resetBudgetUsage(id: string): Promise<void> {
  const { error } = await supabase.rpc('reset_budget_usage', { p_budget_id: id });
  if (error) throw new Error(error.message);
}

export function spendPercent(budget: LLMBudget): number {
  if (!budget.monthly_budget || budget.monthly_budget === 0) return 0;
  return Math.min((budget.current_spend / budget.monthly_budget) * 100, 100);
}

export function tokenPercent(budget: LLMBudget): number {
  if (!budget.token_limit || budget.token_limit === 0) return 0;
  return Math.min((budget.current_tokens / budget.token_limit) * 100, 100);
}

export function isOverAlert(budget: LLMBudget): boolean {
  const sp = spendPercent(budget) / 100;
  const tp = tokenPercent(budget) / 100;
  return sp >= budget.alert_threshold || tp >= budget.alert_threshold;
}

export function isExhausted(budget: LLMBudget): boolean {
  const costExhausted  = budget.monthly_budget != null && budget.current_spend  >= budget.monthly_budget;
  const tokenExhausted = budget.token_limit    != null && budget.current_tokens >= budget.token_limit;
  return costExhausted || tokenExhausted;
}

export function formatUSD(value: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 4 }).format(value);
}

export function formatTokens(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000)     return `${(value / 1_000).toFixed(1)}K`;
  return String(value);
}
