import { supabase } from '../lib/supabaseClient';

export interface AgentMemory {
  id: string;
  memory_type: 'conversation' | 'ticket' | 'customer';
  agent_id: string | null;
  ticket_id: string | null;
  conversation_id: string | null;
  customer_id: string | null;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  agents?: { name: string } | null;
  customers?: { name: string; email: string } | null;
}

export interface ScratchpadStep {
  id: string;
  run_id: string;
  step: number;
  step_type: 'thought' | 'tool_call' | 'tool_result' | 'observation' | 'memory_load';
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface MemoryStats {
  stats: Record<string, number>;
  scratchpad_steps: number;
}

async function memFetch(method: string, body?: unknown, params?: Record<string, string>) {
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData?.session?.access_token;
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
  const anonKey    = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

  let url = `${supabaseUrl}/functions/v1/agent-memory`;
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

export async function getMemoryStats(): Promise<MemoryStats> {
  return memFetch('GET', undefined, { action: 'stats' });
}

export interface ListMemoriesParams {
  agent_id?: string;
  customer_id?: string;
  ticket_id?: string;
  conversation_id?: string;
  memory_type?: string;
  limit?: number;
  offset?: number;
}

export async function listMemories(params: ListMemoriesParams = {}): Promise<{ memories: AgentMemory[]; total: number }> {
  const qs: Record<string, string> = { action: 'list' };
  if (params.agent_id)        qs.agent_id        = params.agent_id;
  if (params.customer_id)     qs.customer_id     = params.customer_id;
  if (params.ticket_id)       qs.ticket_id       = params.ticket_id;
  if (params.conversation_id) qs.conversation_id = params.conversation_id;
  if (params.memory_type)     qs.memory_type     = params.memory_type;
  if (params.limit  != null)  qs.limit           = String(params.limit);
  if (params.offset != null)  qs.offset          = String(params.offset);
  return memFetch('GET', undefined, qs);
}

export async function getScratchpads(runId: string): Promise<{ scratchpads: ScratchpadStep[] }> {
  return memFetch('GET', undefined, { action: 'scratchpads', run_id: runId });
}

export async function createMemory(payload: {
  memory_type: 'conversation' | 'ticket' | 'customer';
  agent_id?: string;
  ticket_id?: string;
  conversation_id?: string;
  customer_id?: string;
  content: string;
  metadata?: Record<string, unknown>;
}): Promise<{ memory: AgentMemory }> {
  return memFetch('POST', { action: 'create', ...payload });
}

export async function deleteMemory(id: string): Promise<void> {
  await memFetch('POST', { action: 'delete', id });
}
