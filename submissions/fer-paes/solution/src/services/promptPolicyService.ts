import { supabase } from '../lib/supabaseClient';

export const TASK_TYPES = [
  'chat',
  'classification',
  'summarization',
  'reasoning',
  'extraction',
  'translation',
  'embedding',
  'test',
] as const;

export type TaskType = typeof TASK_TYPES[number];

export interface LLMPolicy {
  id: string;
  policy_name: string;
  task_type: string;
  model_id: string;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  model?: { id: string; name: string; provider: string; model_identifier: string } | null;
}

export interface CreatePolicyData {
  policy_name: string;
  task_type: string;
  model_id: string;
  priority: number;
}

export interface UpdatePolicyData {
  policy_name?: string;
  task_type?: string;
  model_id?: string;
  priority?: number;
  is_active?: boolean;
}

export async function getPolicies(): Promise<LLMPolicy[]> {
  const { data, error } = await supabase
    .from('llm_policies')
    .select(`
      id, policy_name, task_type, model_id, priority, is_active, created_at, updated_at,
      model:llm_models!model_id(id, name, provider, model_identifier)
    `)
    .order('task_type', { ascending: true })
    .order('priority',  { ascending: true });
  if (error) throw new Error(error.message);
  return (data ?? []) as LLMPolicy[];
}

export async function getPoliciesByTask(taskType: string): Promise<LLMPolicy[]> {
  const { data, error } = await supabase
    .from('llm_policies')
    .select(`
      id, policy_name, task_type, model_id, priority, is_active, created_at, updated_at,
      model:llm_models!model_id(id, name, provider, model_identifier)
    `)
    .eq('task_type', taskType)
    .eq('is_active', true)
    .order('priority', { ascending: true });
  if (error) throw new Error(error.message);
  return (data ?? []) as LLMPolicy[];
}

export async function createPolicy(data: CreatePolicyData): Promise<LLMPolicy> {
  const { data: row, error } = await supabase
    .from('llm_policies')
    .insert(data)
    .select(`
      id, policy_name, task_type, model_id, priority, is_active, created_at, updated_at,
      model:llm_models!model_id(id, name, provider, model_identifier)
    `)
    .single();
  if (error) throw new Error(error.message);
  return row as LLMPolicy;
}

export async function updatePolicy(id: string, data: UpdatePolicyData): Promise<LLMPolicy> {
  const { data: row, error } = await supabase
    .from('llm_policies')
    .update(data)
    .eq('id', id)
    .select(`
      id, policy_name, task_type, model_id, priority, is_active, created_at, updated_at,
      model:llm_models!model_id(id, name, provider, model_identifier)
    `)
    .single();
  if (error) throw new Error(error.message);
  return row as LLMPolicy;
}

export async function deactivatePolicy(id: string): Promise<void> {
  const { error } = await supabase
    .from('llm_policies')
    .update({ is_active: false })
    .eq('id', id);
  if (error) throw new Error(error.message);
}

export async function deletePolicy(id: string): Promise<void> {
  const { error } = await supabase
    .from('llm_policies')
    .delete()
    .eq('id', id);
  if (error) throw new Error(error.message);
}
