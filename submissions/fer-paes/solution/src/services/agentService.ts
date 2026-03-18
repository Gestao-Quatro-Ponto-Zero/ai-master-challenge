import { supabase } from '../lib/supabaseClient';
import type { Agent, AgentSkill, AgentModel, AgentWithRelations, AgentType, AgentStatus, LLMProvider } from '../types';

export interface CreateAgentPayload {
  name: string;
  description?: string;
  type?: AgentType;
  default_model_provider?: LLMProvider;
  default_model_name?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface SetAgentModelPayload {
  provider: LLMProvider;
  model_name: string;
  temperature?: number;
  max_tokens?: number;
  cost_input?: number;
  cost_output?: number;
}

export async function getAgents(): Promise<AgentWithRelations[]> {
  const { data: agents, error } = await supabase
    .from('agents')
    .select('*')
    .order('created_at', { ascending: false });
  if (error) throw new Error(error.message);

  const result: AgentWithRelations[] = [];
  for (const agent of agents || []) {
    const { data: skills } = await supabase
      .from('agent_skills')
      .select('*')
      .eq('agent_id', agent.id)
      .order('created_at');
    const { data: models } = await supabase
      .from('agent_models')
      .select('*')
      .eq('agent_id', agent.id)
      .order('created_at');
    result.push({ ...(agent as Agent), skills: (skills || []) as AgentSkill[], models: (models || []) as AgentModel[] });
  }
  return result;
}

export async function getAgent(id: string): Promise<AgentWithRelations> {
  const { data: agent, error } = await supabase
    .from('agents')
    .select('*')
    .eq('id', id)
    .single();
  if (error) throw new Error(error.message);

  const { data: skills } = await supabase.from('agent_skills').select('*').eq('agent_id', id).order('created_at');
  const { data: models } = await supabase.from('agent_models').select('*').eq('agent_id', id).order('created_at');
  return { ...(agent as Agent), skills: (skills || []) as AgentSkill[], models: (models || []) as AgentModel[] };
}

export async function createAgent(payload: CreateAgentPayload): Promise<Agent> {
  const { data, error } = await supabase
    .from('agents')
    .insert({
      name: payload.name,
      description: payload.description ?? null,
      type: payload.type ?? null,
      default_model_provider: payload.default_model_provider ?? null,
      default_model_name: payload.default_model_name ?? null,
      temperature: payload.temperature ?? 0.2,
      max_tokens: payload.max_tokens ?? 2000,
    })
    .select()
    .single();
  if (error) throw new Error(error.message);

  if (payload.default_model_provider && payload.default_model_name) {
    await supabase.from('agent_models').insert({
      agent_id: data.id,
      provider: payload.default_model_provider,
      model_name: payload.default_model_name,
      temperature: payload.temperature ?? 0.2,
      max_tokens: payload.max_tokens ?? 2000,
    });
  }

  return data as Agent;
}

export async function updateAgent(
  id: string,
  updates: Partial<Pick<Agent, 'name' | 'description' | 'temperature' | 'max_tokens'>>
): Promise<Agent> {
  const { data, error } = await supabase
    .from('agents')
    .update({ ...updates, updated_at: new Date().toISOString() })
    .eq('id', id)
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as Agent;
}

export async function setAgentStatus(id: string, status: AgentStatus): Promise<void> {
  const { error } = await supabase
    .from('agents')
    .update({ status, updated_at: new Date().toISOString() })
    .eq('id', id);
  if (error) throw new Error(error.message);
}

export async function addAgentSkill(agentId: string, skillName: string): Promise<AgentSkill> {
  const { data, error } = await supabase
    .from('agent_skills')
    .insert({ agent_id: agentId, skill_name: skillName })
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as AgentSkill;
}

export async function removeAgentSkill(agentId: string, skillName: string): Promise<void> {
  const { error } = await supabase
    .from('agent_skills')
    .delete()
    .eq('agent_id', agentId)
    .eq('skill_name', skillName);
  if (error) throw new Error(error.message);
}

export async function setAgentModel(agentId: string, payload: SetAgentModelPayload): Promise<AgentModel> {
  const { data: existing } = await supabase
    .from('agent_models')
    .select('id')
    .eq('agent_id', agentId)
    .eq('provider', payload.provider)
    .maybeSingle();

  if (existing) {
    const { data, error } = await supabase
      .from('agent_models')
      .update({
        model_name: payload.model_name,
        temperature: payload.temperature ?? null,
        max_tokens: payload.max_tokens ?? null,
        cost_input: payload.cost_input ?? null,
        cost_output: payload.cost_output ?? null,
      })
      .eq('id', existing.id)
      .select()
      .single();
    if (error) throw new Error(error.message);
    return data as AgentModel;
  }

  const { data, error } = await supabase
    .from('agent_models')
    .insert({ agent_id: agentId, ...payload })
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as AgentModel;
}
