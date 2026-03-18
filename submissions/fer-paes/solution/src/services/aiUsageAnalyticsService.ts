import { supabase } from '../lib/supabaseClient';
import type { CostByModel, CostByAgent, CostByDay } from './costCalculatorService';
import type { LLMBudget } from './budgetManagerService';

export interface AIUsageOverview {
  total_requests:  number;
  total_tokens:    number;
  total_cost:      number;
  avg_latency_ms:  number;
  error_count:     number;
  fallback_count:  number;
}

export interface AIUsageFilters {
  from: string;
  to:   string;
}

export type { CostByModel, CostByAgent, CostByDay };

export const PERIOD_PRESETS = [
  { label: '7 dias',  days: 7   },
  { label: '30 dias', days: 30  },
  { label: '90 dias', days: 90  },
] as const;

export function defaultFilters(days = 30): AIUsageFilters {
  const to   = new Date();
  const from = new Date(to.getTime() - days * 86_400_000);
  return { from: from.toISOString(), to: to.toISOString() };
}

export async function getAIUsageOverview(filters: AIUsageFilters): Promise<AIUsageOverview> {
  const { data, error } = await supabase.rpc('get_ai_usage_overview', {
    from_ts: filters.from,
    to_ts:   filters.to,
  });
  if (error) throw new Error(error.message);
  const row = Array.isArray(data) ? data[0] : data;
  return {
    total_requests: Number(row?.total_requests ?? 0),
    total_tokens:   Number(row?.total_tokens   ?? 0),
    total_cost:     Number(row?.total_cost      ?? 0),
    avg_latency_ms: Number(row?.avg_latency_ms  ?? 0),
    error_count:    Number(row?.error_count      ?? 0),
    fallback_count: Number(row?.fallback_count   ?? 0),
  };
}

export async function getUsageByModel(filters: AIUsageFilters): Promise<CostByModel[]> {
  const { data, error } = await supabase.rpc('get_cost_by_model', {
    from_ts: filters.from,
    to_ts:   filters.to,
  });
  if (error) throw new Error(error.message);
  return (data ?? []) as CostByModel[];
}

export async function getUsageByAgent(filters: AIUsageFilters): Promise<CostByAgent[]> {
  const { data, error } = await supabase.rpc('get_cost_by_agent', {
    from_ts: filters.from,
    to_ts:   filters.to,
  });
  if (error) throw new Error(error.message);
  return (data ?? []) as CostByAgent[];
}

export async function getUsageTimeseries(filters: AIUsageFilters): Promise<CostByDay[]> {
  const { data, error } = await supabase.rpc('get_cost_by_day', {
    from_ts: filters.from,
    to_ts:   filters.to,
  });
  if (error) throw new Error(error.message);
  return (data ?? []) as CostByDay[];
}

export async function getActiveBudgetForDashboard(): Promise<LLMBudget | null> {
  const now = new Date().toISOString();
  const { data, error } = await supabase
    .from('llm_budgets')
    .select('*')
    .eq('is_active', true)
    .is('organization_id', null)
    .lte('period_start', now)
    .gte('period_end', now)
    .maybeSingle();
  if (error) return null;
  return data as LLMBudget | null;
}

export function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return String(Math.round(n));
}

export function formatUSD(n: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD',
    minimumFractionDigits: n < 0.01 ? 4 : 2,
    maximumFractionDigits: n < 0.01 ? 6 : 2,
  }).format(n);
}

export function formatLatency(ms: number): string {
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms)}ms`;
}
