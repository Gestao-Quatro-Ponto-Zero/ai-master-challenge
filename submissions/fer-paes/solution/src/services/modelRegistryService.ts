import { supabase } from '../lib/supabaseClient';
import type { LLMModel, CreateLLMModelPayload, UpdateLLMModelPayload } from '../types';

export async function getModels(): Promise<LLMModel[]> {
  const { data, error } = await supabase
    .from('llm_models')
    .select('*')
    .order('provider')
    .order('name');
  if (error) throw new Error(error.message);
  return (data || []) as LLMModel[];
}

export async function getActiveModels(): Promise<LLMModel[]> {
  const { data, error } = await supabase
    .from('llm_models')
    .select('*')
    .eq('is_active', true)
    .order('provider')
    .order('name');
  if (error) throw new Error(error.message);
  return (data || []) as LLMModel[];
}

export async function getModelById(id: string): Promise<LLMModel> {
  const { data, error } = await supabase
    .from('llm_models')
    .select('*')
    .eq('id', id)
    .single();
  if (error) throw new Error(error.message);
  return data as LLMModel;
}

export async function createModel(payload: CreateLLMModelPayload): Promise<LLMModel> {
  const { data, error } = await supabase
    .from('llm_models')
    .insert({
      name: payload.name,
      provider: payload.provider,
      model_identifier: payload.model_identifier,
      description: payload.description ?? null,
      input_cost_per_1k_tokens: payload.input_cost_per_1k_tokens ?? null,
      output_cost_per_1k_tokens: payload.output_cost_per_1k_tokens ?? null,
      max_tokens: payload.max_tokens ?? null,
    })
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as LLMModel;
}

export async function updateModel(id: string, payload: UpdateLLMModelPayload): Promise<LLMModel> {
  const { data, error } = await supabase
    .from('llm_models')
    .update({ ...payload, updated_at: new Date().toISOString() })
    .eq('id', id)
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as LLMModel;
}

export async function deactivateModel(id: string): Promise<LLMModel> {
  return updateModel(id, { is_active: false });
}

export async function activateModel(id: string): Promise<LLMModel> {
  return updateModel(id, { is_active: true });
}
