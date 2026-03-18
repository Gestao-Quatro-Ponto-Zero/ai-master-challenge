import { supabase } from '../lib/supabaseClient';
import type { AgentRun, AgentMessage, AgentRunWithMessages, ExecuteAgentPayload, ExecuteAgentResult } from '../types';

export async function executeAgent(payload: ExecuteAgentPayload): Promise<ExecuteAgentResult> {
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData?.session?.access_token;

  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

  const response = await fetch(`${supabaseUrl}/functions/v1/agent-executor`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token ?? anonKey}`,
      'Apikey': anonKey,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(err.error ?? `Executor returned ${response.status}`);
  }

  return response.json() as Promise<ExecuteAgentResult>;
}

export async function getAgentRuns(limit = 20): Promise<AgentRun[]> {
  const { data, error } = await supabase
    .from('agent_runs')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as AgentRun[];
}

export async function getAgentRunWithMessages(runId: string): Promise<AgentRunWithMessages> {
  const { data: run, error: runError } = await supabase
    .from('agent_runs')
    .select('*')
    .eq('id', runId)
    .single();
  if (runError) throw new Error(runError.message);

  const { data: messages, error: msgError } = await supabase
    .from('agent_messages')
    .select('*')
    .eq('run_id', runId)
    .order('created_at', { ascending: true });
  if (msgError) throw new Error(msgError.message);

  return { ...(run as AgentRun), messages: (messages ?? []) as AgentMessage[] };
}

export async function getRecentRunsForAgent(agentId: string, limit = 10): Promise<AgentRun[]> {
  const { data, error } = await supabase
    .from('agent_runs')
    .select('*')
    .eq('agent_id', agentId)
    .order('created_at', { ascending: false })
    .limit(limit);
  if (error) throw new Error(error.message);
  return (data ?? []) as AgentRun[];
}
