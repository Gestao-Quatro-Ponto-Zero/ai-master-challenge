import { supabase } from '../lib/supabaseClient';

export interface ModelConfig {
  id: string;
  name: string;
  context_window: number;
  cost_per_input_token: number;
  cost_per_output_token: number;
  supports_tools: boolean;
  supports_vision: boolean;
  provider: string;
}

export interface ProviderConfig {
  id: string;
  name: string;
  models: ModelConfig[];
  env_key: string;
  available: boolean;
}

export interface UsageSummary {
  calls: number;
  input_tokens: number;
  output_tokens: number;
  total_cost: number;
  errors: number;
}

export interface UsageStats {
  summary: Record<string, UsageSummary>;
  totalCost: number;
  totalCalls: number;
  totalTokens: number;
  range: string;
}

export interface UsageLog {
  id: string;
  provider: string;
  model_name: string;
  input_tokens: number;
  output_tokens: number;
  cost_input: number;
  cost_output: number;
  total_cost: number;
  latency_ms: number;
  status: 'success' | 'error' | 'fallback';
  fallback_from: string | null;
  error_message: string | null;
  agent_id: string | null;
  ticket_id: string | null;
  created_at: string;
}

export interface TestResult {
  response: string;
  provider: string;
  model: string;
  usage: { input_tokens: number; output_tokens: number };
  fallback: boolean;
}

async function llmFetch(method: string, body?: unknown, params?: Record<string, string>) {
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData?.session?.access_token;
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

  let url = `${supabaseUrl}/functions/v1/llm-manager`;
  if (params) {
    const qs = new URLSearchParams(params).toString();
    if (qs) url += `?${qs}`;
  }

  const res = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token ?? anonKey}`,
      Apikey: anonKey,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await res.json();
  if (!res.ok && data.error) throw new Error(data.error);
  return data;
}

export async function getProviders(): Promise<ProviderConfig[]> {
  const data = await llmFetch('GET', undefined, { action: 'providers' });
  return data.providers as ProviderConfig[];
}

export async function getModels(): Promise<ModelConfig[]> {
  const data = await llmFetch('GET', undefined, { action: 'models' });
  return data.models as ModelConfig[];
}

export async function getUsageStats(range: '1d' | '7d' | '30d' = '30d'): Promise<UsageStats> {
  return llmFetch('GET', undefined, { action: 'usage', range });
}

export async function getUsageLogs(limit = 50, offset = 0): Promise<{ logs: UsageLog[]; total: number }> {
  return llmFetch('GET', undefined, { action: 'logs', limit: String(limit), offset: String(offset) });
}

export async function testModel(provider: string, model: string, message: string): Promise<TestResult> {
  return llmFetch('POST', { action: 'test', provider, model, message });
}
