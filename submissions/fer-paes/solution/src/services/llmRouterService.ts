import { supabase } from '../lib/supabaseClient';

const ROUTER_URL = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/llm-router`;

async function authHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${data.session?.access_token ?? import.meta.env.VITE_SUPABASE_ANON_KEY}`,
    Apikey: import.meta.env.VITE_SUPABASE_ANON_KEY,
  };
}

export interface RouterModel {
  id: string;
  name: string;
  provider: string;
  model_identifier: string;
  max_tokens: number | null;
  input_cost_per_1k_tokens: number | null;
  output_cost_per_1k_tokens: number | null;
  is_active: boolean;
}

export interface RouterLogEntry {
  id: string;
  agent_id: string | null;
  model_id: string | null;
  provider: string | null;
  model_identifier: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  latency_ms: number | null;
  status: string;
  error_message: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
  agent?: { id: string; name: string } | null;
  model?: { id: string; name: string } | null;
}

export interface ExecuteRequest {
  prompt?: string;
  messages?: Array<{ role: 'user' | 'assistant'; content: string }>;
  system?: string;
  agent_id?: string;
  model_id?: string;
  provider?: string;
  task_type?: string;
  max_tokens?: number;
  temperature?: number;
}

export interface ExecuteResponse {
  request_id: string;
  response: string;
  model: string;
  model_id: string;
  provider: string;
  stop_reason: string;
  usage: { input_tokens: number; output_tokens: number; total_tokens: number };
  cost: { input_cost: number; output_cost: number; total_cost: number; currency: string };
  latency_ms: number;
  fallback: boolean;
}

export interface RouterStatus {
  status: string;
  providers: Record<string, boolean>;
}

export async function getRouterStatus(): Promise<RouterStatus> {
  const headers = await authHeaders();
  const res = await fetch(`${ROUTER_URL}?action=status`, { headers });
  if (!res.ok) throw new Error(`Router status error: ${res.status}`);
  return res.json();
}

export async function getActiveModels(): Promise<RouterModel[]> {
  const headers = await authHeaders();
  const res = await fetch(`${ROUTER_URL}?action=models`, { headers });
  if (!res.ok) throw new Error(`Models fetch error: ${res.status}`);
  const data = await res.json();
  return data.models ?? [];
}

export async function getRouterLogs(limit = 50, offset = 0): Promise<{ logs: RouterLogEntry[]; total: number }> {
  const headers = await authHeaders();
  const res = await fetch(`${ROUTER_URL}?action=logs&limit=${limit}&offset=${offset}`, { headers });
  if (!res.ok) throw new Error(`Logs fetch error: ${res.status}`);
  return res.json();
}

export async function executePrompt(request: ExecuteRequest): Promise<ExecuteResponse> {
  const headers = await authHeaders();
  const res = await fetch(ROUTER_URL, {
    method: 'POST',
    headers,
    body: JSON.stringify({ action: 'execute', ...request }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error ?? `Execute error: ${res.status}`);
  return data as ExecuteResponse;
}

export async function testRouter(prompt: string, modelId?: string, provider?: string): Promise<ExecuteResponse> {
  const headers = await authHeaders();
  const res = await fetch(ROUTER_URL, {
    method: 'POST',
    headers,
    body: JSON.stringify({ action: 'test', prompt, model_id: modelId, provider }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error ?? `Test error: ${res.status}`);
  return data as ExecuteResponse;
}
