import { supabase } from '../lib/supabaseClient';

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  channel_type: string | null;
  rate_limit_per_minute: number;
  is_active: boolean;
  last_used_at: string | null;
  request_count: number;
  expires_at: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiKeyCreated extends ApiKey {
  full_key: string;
}

export interface CreateApiKeyPayload {
  name: string;
  scopes: string[];
  channel_type?: string | null;
  rate_limit_per_minute?: number;
  expires_at?: string | null;
}

export interface IntegrationLog {
  id: string;
  api_key_id: string | null;
  key_prefix: string | null;
  endpoint: string;
  method: string;
  status_code: number;
  ip_address: string | null;
  request_payload: Record<string, unknown> | null;
  response_payload: Record<string, unknown> | null;
  error_message: string | null;
  duration_ms: number | null;
  created_at: string;
}

export const AVAILABLE_SCOPES = [
  { value: 'channel:ingest',  label: 'Channel Ingest',   description: 'Submit messages from external channels' },
  { value: 'events:write',    label: 'Events Write',     description: 'Track customer events' },
  { value: 'customers:read',  label: 'Customers Read',   description: 'Read customer profiles' },
  { value: 'customers:write', label: 'Customers Write',  description: 'Create or update customers' },
  { value: 'tickets:read',    label: 'Tickets Read',     description: 'Read ticket data' },
  { value: 'tickets:write',   label: 'Tickets Write',    description: 'Create or update tickets' },
];

export const CHANNEL_TYPES = [
  { value: 'chat',   label: 'Chat Widget' },
  { value: 'email',  label: 'E-mail' },
  { value: 'api',    label: 'API Genérica' },
  { value: 'bot',    label: 'Bot / Assistente' },
  { value: 'social', label: 'Redes Sociais' },
  { value: 'phone',  label: 'Telefone / Voz' },
];

function generateSecureKey(): string {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return 'sk_live_' + Array.from(bytes).map((b) => b.toString(16).padStart(2, '0')).join('');
}

async function hashKey(key: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(key);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hashBuffer)).map((b) => b.toString(16).padStart(2, '0')).join('');
}

export async function getApiKeys(): Promise<ApiKey[]> {
  const { data, error } = await supabase
    .from('api_keys')
    .select('*')
    .order('created_at', { ascending: false });
  if (error) throw new Error(error.message);
  return (data || []) as ApiKey[];
}

export async function createApiKey(payload: CreateApiKeyPayload): Promise<ApiKeyCreated> {
  const { data: { user } } = await supabase.auth.getUser();
  const fullKey = generateSecureKey();
  const keyHash = await hashKey(fullKey);
  const keyPrefix = fullKey.slice(0, 16);

  const { data, error } = await supabase
    .from('api_keys')
    .insert({
      name: payload.name,
      key_prefix: keyPrefix,
      key_hash: keyHash,
      scopes: payload.scopes,
      channel_type: payload.channel_type ?? null,
      rate_limit_per_minute: payload.rate_limit_per_minute ?? 60,
      expires_at: payload.expires_at ?? null,
      created_by: user?.id ?? null,
    })
    .select()
    .single();

  if (error) throw new Error(error.message);
  return { ...(data as ApiKey), full_key: fullKey };
}

export async function toggleApiKey(id: string, isActive: boolean): Promise<void> {
  const { error } = await supabase
    .from('api_keys')
    .update({ is_active: isActive })
    .eq('id', id);
  if (error) throw new Error(error.message);
}

export async function deleteApiKey(id: string): Promise<void> {
  const { error } = await supabase.from('api_keys').delete().eq('id', id);
  if (error) throw new Error(error.message);
}

export async function getIntegrationLogs(
  apiKeyId?: string,
  limit = 100,
  offset = 0,
): Promise<{ logs: IntegrationLog[]; total: number }> {
  let query = supabase
    .from('integration_logs')
    .select('*', { count: 'exact' })
    .order('created_at', { ascending: false })
    .range(offset, offset + limit - 1);

  if (apiKeyId) {
    query = query.eq('api_key_id', apiKeyId);
  }

  const { data, error, count } = await query;
  if (error) throw new Error(error.message);
  return { logs: (data || []) as IntegrationLog[], total: count ?? 0 };
}
