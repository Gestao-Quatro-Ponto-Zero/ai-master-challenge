import { supabase } from '../lib/supabaseClient';

export interface ToolDefinition {
  id: string;
  name: string;
  display_name: string;
  description: string;
  input_schema: {
    type: string;
    properties?: Record<string, { type: string; description?: string; enum?: string[] }>;
    required?: string[];
  };
  handler_name: string;
  category: string;
  is_active: boolean;
  created_at: string;
}

export interface ExecuteToolPayload {
  tool_name: string;
  arguments: Record<string, string>;
  context?: {
    ticket_id?: string;
    conversation_id?: string;
    agent_id?: string;
  };
}

export interface ExecuteToolResult {
  result?: unknown;
  error?: string;
  tool_name: string;
  duration_ms: number;
}

export async function getAllTools(): Promise<ToolDefinition[]> {
  const { data, error } = await supabase
    .from('tool_definitions')
    .select('*')
    .eq('is_active', true)
    .order('category')
    .order('name');
  if (error) throw new Error(error.message);
  return (data ?? []) as ToolDefinition[];
}

export async function getToolsForAgent(agentId: string): Promise<ToolDefinition[]> {
  const { data: skills, error: skillsError } = await supabase
    .from('agent_skills')
    .select('skill_name')
    .eq('agent_id', agentId);
  if (skillsError) throw new Error(skillsError.message);

  const skillNames = (skills ?? []).map((s: { skill_name: string }) => s.skill_name);
  if (skillNames.length === 0) return [];

  const { data, error } = await supabase
    .from('tool_definitions')
    .select('*')
    .eq('is_active', true)
    .in('name', skillNames)
    .order('category')
    .order('name');
  if (error) throw new Error(error.message);
  return (data ?? []) as ToolDefinition[];
}

export async function executeTool(payload: ExecuteToolPayload): Promise<ExecuteToolResult> {
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData?.session?.access_token;
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string;
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

  const response = await fetch(`${supabaseUrl}/functions/v1/agent-tools`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token ?? anonKey}`,
      'Apikey': anonKey,
    },
    body: JSON.stringify({ action: 'execute', ...payload }),
  });

  const data = await response.json();
  if (!response.ok && !data.tool_name) {
    throw new Error(data.error ?? `Tool execution returned ${response.status}`);
  }
  return data as ExecuteToolResult;
}

export const CATEGORY_LABELS: Record<string, string> = {
  customer: 'Customer',
  ticket: 'Ticket',
  knowledge: 'Knowledge',
  order: 'Order',
  system: 'System',
  general: 'General',
};

export const CATEGORY_COLORS: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  customer: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20', dot: 'bg-blue-400' },
  ticket: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', dot: 'bg-emerald-400' },
  knowledge: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20', dot: 'bg-amber-400' },
  order: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20', dot: 'bg-orange-400' },
  system: { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/20', dot: 'bg-slate-400' },
  general: { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/20', dot: 'bg-slate-400' },
};
