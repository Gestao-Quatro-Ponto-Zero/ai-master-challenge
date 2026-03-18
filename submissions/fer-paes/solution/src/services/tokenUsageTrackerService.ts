import { supabase } from '../lib/supabaseClient';

export interface TokenUsageRecord {
  id: string;
  request_id: string;
  model_id: string | null;
  agent_id: string | null;
  provider: string | null;
  model_identifier: string | null;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  created_at: string;
}

export interface TokenUsageByModel {
  model_id: string | null;
  model_identifier: string | null;
  provider: string | null;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  request_count: number;
}

export interface TokenUsageByAgent {
  agent_id: string | null;
  agent_name: string | null;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  request_count: number;
}

export interface TokenUsageByDay {
  day: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  request_count: number;
}

export interface TokenUsageFilters {
  from?: string;
  to?: string;
}

export async function recordUsage(
  requestId: string,
  modelId: string | null,
  agentId: string | null,
  provider: string | null,
  modelIdentifier: string | null,
  inputTokens: number,
  outputTokens: number
): Promise<void> {
  const total = inputTokens + outputTokens;
  const { error } = await supabase.from('llm_token_usage').insert({
    request_id:       requestId,
    model_id:         modelId,
    agent_id:         agentId,
    provider,
    model_identifier: modelIdentifier,
    input_tokens:     inputTokens,
    output_tokens:    outputTokens,
    total_tokens:     total,
  });
  if (error) throw new Error(error.message);
}

export async function getTokenUsage(
  filters: TokenUsageFilters = {},
  limit = 200,
  offset = 0
): Promise<TokenUsageRecord[]> {
  let query = supabase
    .from('llm_token_usage')
    .select('*')
    .order('created_at', { ascending: false })
    .range(offset, offset + limit - 1);
  if (filters.from) query = query.gte('created_at', filters.from);
  if (filters.to)   query = query.lte('created_at', filters.to);
  const { data, error } = await query;
  if (error) throw new Error(error.message);
  return (data || []) as TokenUsageRecord[];
}

export async function getTokenUsageByModel(
  filters: TokenUsageFilters = {}
): Promise<TokenUsageByModel[]> {
  const from = filters.from ?? new Date(Date.now() - 30 * 86_400_000).toISOString();
  const to   = filters.to   ?? new Date().toISOString();
  const { data, error } = await supabase.rpc('get_token_usage_by_model', {
    from_ts: from,
    to_ts:   to,
  });
  if (error) throw new Error(error.message);
  return (data || []) as TokenUsageByModel[];
}

export async function getTokenUsageByAgent(
  filters: TokenUsageFilters = {}
): Promise<TokenUsageByAgent[]> {
  const from = filters.from ?? new Date(Date.now() - 30 * 86_400_000).toISOString();
  const to   = filters.to   ?? new Date().toISOString();
  const { data, error } = await supabase.rpc('get_token_usage_by_agent', {
    from_ts: from,
    to_ts:   to,
  });
  if (error) throw new Error(error.message);
  return (data || []) as TokenUsageByAgent[];
}

export async function getTokenUsageByDay(
  filters: TokenUsageFilters = {}
): Promise<TokenUsageByDay[]> {
  const from = filters.from ?? new Date(Date.now() - 30 * 86_400_000).toISOString();
  const to   = filters.to   ?? new Date().toISOString();
  const { data, error } = await supabase.rpc('get_token_usage_by_day', {
    from_ts: from,
    to_ts:   to,
  });
  if (error) throw new Error(error.message);
  return (data || []) as TokenUsageByDay[];
}
