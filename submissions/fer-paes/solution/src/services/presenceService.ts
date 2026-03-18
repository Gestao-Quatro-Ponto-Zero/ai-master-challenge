import { supabase } from '../lib/supabaseClient';
import type { OperatorPresence, OperatorStatus } from '../types';

const STALE_THRESHOLD_MS = 2 * 60 * 1000;

export async function setPresence(userId: string, status: OperatorStatus): Promise<OperatorPresence> {
  const now = new Date().toISOString();
  const { data, error } = await supabase
    .from('operator_presence')
    .upsert(
      { user_id: userId, status, last_seen: now, updated_at: now },
      { onConflict: 'user_id' },
    )
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as OperatorPresence;
}

export async function heartbeat(userId: string): Promise<void> {
  const now = new Date().toISOString();
  const { error } = await supabase
    .from('operator_presence')
    .upsert(
      { user_id: userId, last_seen: now, updated_at: now },
      { onConflict: 'user_id' },
    );
  if (error) throw new Error(error.message);
}

export async function getPresence(userId: string): Promise<OperatorPresence | null> {
  const { data, error } = await supabase
    .from('operator_presence')
    .select('*')
    .eq('user_id', userId)
    .maybeSingle();
  if (error) throw new Error(error.message);
  return data as OperatorPresence | null;
}

export async function getOnlineOperators(): Promise<OperatorPresence[]> {
  const staleThreshold = new Date(Date.now() - STALE_THRESHOLD_MS).toISOString();
  const { data, error } = await supabase
    .from('operator_presence')
    .select('*')
    .neq('status', 'offline')
    .gte('last_seen', staleThreshold);
  if (error) throw new Error(error.message);
  return (data ?? []) as OperatorPresence[];
}

export async function getAllPresence(): Promise<OperatorPresence[]> {
  const { data, error } = await supabase
    .from('operator_presence')
    .select('*');
  if (error) throw new Error(error.message);
  return (data ?? []) as OperatorPresence[];
}

export function isStale(lastSeen: string): boolean {
  return Date.now() - new Date(lastSeen).getTime() > STALE_THRESHOLD_MS;
}

export function resolveStatus(presence: OperatorPresence | null | undefined): OperatorStatus {
  if (!presence) return 'offline';
  if (presence.status === 'offline') return 'offline';
  if (isStale(presence.last_seen)) return 'offline';
  return presence.status;
}

export interface PresenceWithProfile {
  id:        string;
  user_id:   string;
  status:    OperatorStatus;
  last_seen: string;
  updated_at: string;
  full_name: string;
  email:     string;
}

export async function getAllPresenceWithProfiles(): Promise<PresenceWithProfile[]> {
  const { data, error } = await supabase
    .from('operator_presence')
    .select('*, profile:profiles!operator_presence_user_id_fkey(full_name, email)')
    .order('last_seen', { ascending: false });

  if (error) throw new Error(error.message);

  return ((data ?? []) as unknown[]).map((raw) => {
    const row = raw as Record<string, unknown>;
    const profileArr = row.profile as { full_name?: string; email?: string }[] | null;
    const profile = Array.isArray(profileArr) ? profileArr[0] : profileArr;
    const resolved = resolveStatus({ status: row.status as OperatorStatus, last_seen: row.last_seen as string } as OperatorPresence);
    return {
      id:         row.id as string,
      user_id:    row.user_id as string,
      status:     resolved,
      last_seen:  row.last_seen as string,
      updated_at: row.updated_at as string,
      full_name:  profile?.full_name ?? '',
      email:      profile?.email     ?? '',
    };
  });
}

export async function markStaleOperatorsOffline(): Promise<number> {
  const threshold = new Date(Date.now() - STALE_THRESHOLD_MS).toISOString();
  const now       = new Date().toISOString();

  const { data, error } = await supabase
    .from('operator_presence')
    .update({ status: 'offline', updated_at: now })
    .lt('last_seen', threshold)
    .neq('status', 'offline')
    .select('id');

  if (error) throw new Error(error.message);
  return (data ?? []).length;
}
