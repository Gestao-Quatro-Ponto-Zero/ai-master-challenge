import { supabase } from '../lib/supabaseClient';

export interface AgentMetricsSummary {
  agent_id: string;
  agent_name: string;
  agent_type: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  success_rate: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_tool_calls: number;
  last_run_at: string | null;
}

export interface ExecutionOverview {
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  success_rate: number;
  avg_latency_ms: number;
  total_tokens: number;
  input_tokens: number;
  output_tokens: number;
  total_tool_calls: number;
}

export interface TimelinePoint {
  day: string;
  total_runs: number;
  success_runs: number;
  error_runs: number;
  avg_latency: number;
  total_tokens: number;
}

export interface ToolUsageStat {
  tool_name: string;
  call_count: number;
  success_rate: number;
  avg_latency: number;
}

export interface ExecutionLog {
  id: string;
  agent_id: string | null;
  run_id: string | null;
  ticket_id: string | null;
  conversation_id: string | null;
  model_provider: string;
  model_name: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  tool_calls_count: number;
  iterations: number;
  status: 'success' | 'error' | 'timeout' | 'cancelled';
  error_message: string;
  created_at: string;
  agents?: { name: string; type: string } | null;
}

export interface ToolCall {
  id: string;
  run_id: string;
  agent_id: string | null;
  tool_name: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown>;
  latency_ms: number;
  success: boolean;
  created_at: string;
}

async function obsFetch(params: Record<string, string>): Promise<Record<string, unknown>> {
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData?.session?.access_token;
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
  const anonKey    = import.meta.env.VITE_SUPABASE_ANON_KEY as string;
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${supabaseUrl}/functions/v1/agent-observability?${qs}`, {
    headers: {
      Authorization: `Bearer ${token ?? anonKey}`,
      Apikey: anonKey,
    },
  });
  const data = await res.json();
  if (!res.ok && data.error) throw new Error(data.error);
  return data as Record<string, unknown>;
}

export async function getAgentMetrics(): Promise<AgentMetricsSummary[]> {
  const data = await obsFetch({ action: 'metrics' });
  return (data.metrics as AgentMetricsSummary[]) ?? [];
}

export async function getOverview(days = 7): Promise<{
  overview: ExecutionOverview;
  timeline: TimelinePoint[];
  tool_usage: ToolUsageStat[];
}> {
  const data = await obsFetch({ action: 'overview', days: String(days) });
  return data as unknown as { overview: ExecutionOverview; timeline: TimelinePoint[]; tool_usage: ToolUsageStat[] };
}

export async function getExecutionLogs(params: {
  agent_id?: string;
  ticket_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<{ executions: ExecutionLog[]; total: number }> {
  const qs: Record<string, string> = { action: 'executions' };
  if (params.agent_id) qs.agent_id = params.agent_id;
  if (params.ticket_id) qs.ticket_id = params.ticket_id;
  if (params.status)   qs.status   = params.status;
  if (params.limit  != null) qs.limit  = String(params.limit);
  if (params.offset != null) qs.offset = String(params.offset);
  const data = await obsFetch(qs);
  return data as unknown as { executions: ExecutionLog[]; total: number };
}

export async function getToolCalls(params: {
  run_id?: string;
  agent_id?: string;
  limit?: number;
}): Promise<{ tool_calls: ToolCall[]; total: number }> {
  const qs: Record<string, string> = { action: 'tool-calls' };
  if (params.run_id)   qs.run_id   = params.run_id;
  if (params.agent_id) qs.agent_id = params.agent_id;
  if (params.limit != null) qs.limit = String(params.limit);
  const data = await obsFetch(qs);
  return data as unknown as { tool_calls: ToolCall[]; total: number };
}
