import { supabase } from '../lib/supabaseClient';

export interface LLMCostRecord {
  id: string;
  request_id: string;
  model_id: string | null;
  agent_id: string | null;
  provider: string | null;
  model_identifier: string | null;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  input_cost_per_1k: number;
  output_cost_per_1k: number;
  input_cost: number;
  output_cost: number;
  total_cost: number;
  currency: string;
  created_at: string;
}

export interface CostByModel {
  model_id: string | null;
  model_identifier: string | null;
  provider: string | null;
  request_count: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  input_cost: number;
  output_cost: number;
  total_cost: number;
  avg_cost: number;
}

export interface CostByAgent {
  agent_id: string | null;
  agent_name: string | null;
  request_count: number;
  total_tokens: number;
  total_cost: number;
  avg_cost: number;
}

export interface CostByDay {
  day: string;
  request_count: number;
  total_tokens: number;
  input_cost: number;
  output_cost: number;
  total_cost: number;
}

export interface CostFilters {
  from?: string;
  to?: string;
}

export function calculateCost(
  inputTokens: number,
  outputTokens: number,
  inputCostPer1k: number,
  outputCostPer1k: number
): { inputCost: number; outputCost: number; totalCost: number } {
  const inputCost  = (inputTokens  / 1000) * inputCostPer1k;
  const outputCost = (outputTokens / 1000) * outputCostPer1k;
  return { inputCost, outputCost, totalCost: inputCost + outputCost };
}

export async function recordCost(
  requestId: string,
  modelId: string | null,
  agentId: string | null,
  provider: string | null,
  modelIdentifier: string | null,
  inputTokens: number,
  outputTokens: number,
  inputCostPer1k: number,
  outputCostPer1k: number
): Promise<void> {
  const { inputCost, outputCost, totalCost } = calculateCost(
    inputTokens, outputTokens, inputCostPer1k, outputCostPer1k
  );
  const { error } = await supabase.from('llm_costs').insert({
    request_id:         requestId,
    model_id:           modelId,
    agent_id:           agentId,
    provider,
    model_identifier:   modelIdentifier,
    input_tokens:       inputTokens,
    output_tokens:      outputTokens,
    total_tokens:       inputTokens + outputTokens,
    input_cost_per_1k:  inputCostPer1k,
    output_cost_per_1k: outputCostPer1k,
    input_cost:         inputCost,
    output_cost:        outputCost,
    total_cost:         totalCost,
    currency:           'USD',
  });
  if (error) throw new Error(error.message);
}

export async function getCosts(
  filters: CostFilters = {},
  limit = 200,
  offset = 0
): Promise<LLMCostRecord[]> {
  let query = supabase
    .from('llm_costs')
    .select('*')
    .order('created_at', { ascending: false })
    .range(offset, offset + limit - 1);
  if (filters.from) query = query.gte('created_at', filters.from);
  if (filters.to)   query = query.lte('created_at', filters.to);
  const { data, error } = await query;
  if (error) throw new Error(error.message);
  return (data || []) as LLMCostRecord[];
}

export async function getCostsByModel(filters: CostFilters = {}): Promise<CostByModel[]> {
  const from = filters.from ?? new Date(Date.now() - 30 * 86_400_000).toISOString();
  const to   = filters.to   ?? new Date().toISOString();
  const { data, error } = await supabase.rpc('get_cost_by_model', { from_ts: from, to_ts: to });
  if (error) throw new Error(error.message);
  return (data || []) as CostByModel[];
}

export async function getCostsByAgent(filters: CostFilters = {}): Promise<CostByAgent[]> {
  const from = filters.from ?? new Date(Date.now() - 30 * 86_400_000).toISOString();
  const to   = filters.to   ?? new Date().toISOString();
  const { data, error } = await supabase.rpc('get_cost_by_agent', { from_ts: from, to_ts: to });
  if (error) throw new Error(error.message);
  return (data || []) as CostByAgent[];
}

export async function getCostsByDay(filters: CostFilters = {}): Promise<CostByDay[]> {
  const from = filters.from ?? new Date(Date.now() - 30 * 86_400_000).toISOString();
  const to   = filters.to   ?? new Date().toISOString();
  const { data, error } = await supabase.rpc('get_cost_by_day', { from_ts: from, to_ts: to });
  if (error) throw new Error(error.message);
  return (data || []) as CostByDay[];
}
