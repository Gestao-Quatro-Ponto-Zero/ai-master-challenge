import { supabase } from '../lib/supabaseClient';
import type {
  LLMRequest,
  CreateLLMRequestPayload,
  UpdateLLMRequestSuccessPayload,
  LLMRequestFilters,
} from '../types';

export async function createRequest(data: CreateLLMRequestPayload): Promise<LLMRequest> {
  const { data: row, error } = await supabase
    .from('llm_requests')
    .insert({
      agent_id: data.agent_id ?? null,
      model_id: data.model_id ?? null,
      provider: data.provider ?? null,
      model_identifier: data.model_identifier ?? null,
      metadata: data.metadata ?? null,
      status: 'pending',
    })
    .select()
    .single();
  if (error) throw new Error(error.message);
  return row as LLMRequest;
}

export async function updateRequestSuccess(
  requestId: string,
  metrics: UpdateLLMRequestSuccessPayload
): Promise<void> {
  const { error } = await supabase
    .from('llm_requests')
    .update({
      status: 'success',
      prompt_tokens: metrics.prompt_tokens,
      completion_tokens: metrics.completion_tokens,
      total_tokens: metrics.total_tokens,
      latency_ms: metrics.latency_ms,
      updated_at: new Date().toISOString(),
    })
    .eq('id', requestId);
  if (error) throw new Error(error.message);
}

export async function updateRequestError(requestId: string, errorMessage: string): Promise<void> {
  const { error } = await supabase
    .from('llm_requests')
    .update({
      status: 'error',
      error_message: errorMessage,
      updated_at: new Date().toISOString(),
    })
    .eq('id', requestId);
  if (error) throw new Error(error.message);
}

export async function updateRequestTimeout(requestId: string): Promise<void> {
  const { error } = await supabase
    .from('llm_requests')
    .update({
      status: 'timeout',
      updated_at: new Date().toISOString(),
    })
    .eq('id', requestId);
  if (error) throw new Error(error.message);
}

export async function getRequests(
  filters: LLMRequestFilters = {},
  limit = 100,
  offset = 0
): Promise<LLMRequest[]> {
  let query = supabase
    .from('llm_requests')
    .select(`
      *,
      agent:agents(id, name),
      model:llm_models(id, name, provider)
    `)
    .order('created_at', { ascending: false })
    .range(offset, offset + limit - 1);

  if (filters.model_id)  query = query.eq('model_id', filters.model_id);
  if (filters.agent_id)  query = query.eq('agent_id', filters.agent_id);
  if (filters.provider)  query = query.eq('provider', filters.provider);
  if (filters.status)    query = query.eq('status', filters.status);
  if (filters.from)      query = query.gte('created_at', filters.from);
  if (filters.to)        query = query.lte('created_at', filters.to);

  const { data, error } = await query;
  if (error) throw new Error(error.message);
  return (data || []) as unknown as LLMRequest[];
}

export async function getRequestById(id: string): Promise<LLMRequest> {
  const { data, error } = await supabase
    .from('llm_requests')
    .select(`
      *,
      agent:agents(id, name),
      model:llm_models(id, name, provider)
    `)
    .eq('id', id)
    .single();
  if (error) throw new Error(error.message);
  return data as unknown as LLMRequest;
}
