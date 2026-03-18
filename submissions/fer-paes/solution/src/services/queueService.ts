import { supabase } from '../lib/supabaseClient';
import type { OperatorRow } from './operatorService';

export type DistributionStrategy = 'round_robin' | 'least_loaded' | 'skill_based' | 'manual';

export interface Queue {
  id:                    string;
  name:                  string;
  description:           string;
  priority:              number;
  is_active:             boolean;
  distribution_strategy: DistributionStrategy;
  created_at:            string;
  updated_at:            string;
}

export interface QueueWithStats extends Queue {
  operators_count: number;
  tickets_waiting: number;
  operators?:      QueueOperatorEntry[];
}

export interface QueueOperatorEntry {
  id:          string;
  queue_id:    string;
  operator_id: string;
  created_at:  string;
  operator?:   OperatorRow;
}

export interface QueueTicket {
  id:         string;
  ticket_id:  string;
  queue_id:   string;
  position:   number;
  priority:   number;
  created_at: string;
  ticket?: {
    id:         string;
    subject:    string;
    status:     string;
    priority:   string;
    created_at: string;
    customer?:  { name: string; email: string } | null;
  } | null;
}

export interface CreateQueueInput {
  name:                  string;
  description:           string;
  priority:              number;
  distribution_strategy: DistributionStrategy;
}

export async function listQueues(): Promise<QueueWithStats[]> {
  const { data: queues, error } = await supabase
    .from('queues')
    .select('*')
    .order('priority', { ascending: false })
    .order('name', { ascending: true });

  if (error) throw new Error(error.message);

  const ids = (queues ?? []).map((q) => q.id);
  if (ids.length === 0) return [];

  const [{ data: opCounts }, { data: ticketCounts }] = await Promise.all([
    supabase
      .from('queue_operators')
      .select('queue_id')
      .in('queue_id', ids),
    supabase
      .from('queue_tickets')
      .select('queue_id')
      .in('queue_id', ids),
  ]);

  const opMap: Record<string, number>     = {};
  const tickMap: Record<string, number>   = {};
  (opCounts     ?? []).forEach((r) => { opMap[r.queue_id]   = (opMap[r.queue_id]   ?? 0) + 1; });
  (ticketCounts ?? []).forEach((r) => { tickMap[r.queue_id] = (tickMap[r.queue_id] ?? 0) + 1; });

  return (queues ?? []).map((q) => ({
    ...q,
    operators_count: opMap[q.id]   ?? 0,
    tickets_waiting: tickMap[q.id] ?? 0,
  }));
}

export async function getQueue(queueId: string): Promise<QueueWithStats | null> {
  const { data, error } = await supabase
    .from('queues')
    .select('*')
    .eq('id', queueId)
    .maybeSingle();

  if (error) throw new Error(error.message);
  if (!data) return null;

  const [{ count: opCount }, { count: tickCount }] = await Promise.all([
    supabase.from('queue_operators').select('id', { count: 'exact', head: true }).eq('queue_id', queueId),
    supabase.from('queue_tickets').select('id', { count: 'exact', head: true }).eq('queue_id', queueId),
  ]);

  return {
    ...data,
    operators_count: opCount ?? 0,
    tickets_waiting: tickCount ?? 0,
  };
}

export async function createQueue(input: CreateQueueInput): Promise<Queue> {
  const { data, error } = await supabase
    .from('queues')
    .insert({
      name:                  input.name.trim().toLowerCase().replace(/\s+/g, '_'),
      description:           input.description.trim(),
      priority:              input.priority,
      distribution_strategy: input.distribution_strategy,
    })
    .select()
    .single();

  if (error) throw new Error(error.message);
  return data as Queue;
}

export async function updateQueue(
  queueId: string,
  input: Partial<CreateQueueInput & { is_active: boolean }>,
): Promise<Queue> {
  const patch: Record<string, unknown> = { updated_at: new Date().toISOString() };
  if (input.name                  !== undefined) patch.name                  = input.name.trim().toLowerCase().replace(/\s+/g, '_');
  if (input.description           !== undefined) patch.description           = input.description.trim();
  if (input.priority              !== undefined) patch.priority              = input.priority;
  if (input.is_active             !== undefined) patch.is_active             = input.is_active;
  if (input.distribution_strategy !== undefined) patch.distribution_strategy = input.distribution_strategy;

  const { data, error } = await supabase
    .from('queues')
    .update(patch)
    .eq('id', queueId)
    .select()
    .single();

  if (error) throw new Error(error.message);
  return data as Queue;
}

export async function deleteQueue(queueId: string): Promise<void> {
  const { error } = await supabase.from('queues').delete().eq('id', queueId);
  if (error) throw new Error(error.message);
}

export async function toggleQueueActive(queueId: string, isActive: boolean): Promise<void> {
  const { error } = await supabase
    .from('queues')
    .update({ is_active: isActive, updated_at: new Date().toISOString() })
    .eq('id', queueId);
  if (error) throw new Error(error.message);
}

export async function getQueueOperators(queueId: string): Promise<QueueOperatorEntry[]> {
  const { data, error } = await supabase
    .from('queue_operators')
    .select(`
      *,
      operator:operators(
        *,
        profile:profiles!operators_user_id_fkey(full_name, email, avatar_url)
      )
    `)
    .eq('queue_id', queueId)
    .order('created_at', { ascending: true });

  if (error) throw new Error(error.message);
  return (data ?? []) as QueueOperatorEntry[];
}

export async function replaceQueueOperators(
  queueId: string,
  operatorIds: string[],
): Promise<void> {
  const { error: delErr } = await supabase
    .from('queue_operators')
    .delete()
    .eq('queue_id', queueId);

  if (delErr) throw new Error(delErr.message);

  if (operatorIds.length === 0) return;

  const { error: insErr } = await supabase
    .from('queue_operators')
    .insert(operatorIds.map((id) => ({ queue_id: queueId, operator_id: id })));

  if (insErr) throw new Error(insErr.message);
}

export async function addTicketToQueue(
  queueId: string,
  ticketId: string,
  priority = 1,
): Promise<QueueTicket> {
  const { data: maxRow } = await supabase
    .from('queue_tickets')
    .select('position')
    .eq('queue_id', queueId)
    .order('position', { ascending: false })
    .limit(1)
    .maybeSingle();

  const nextPos = ((maxRow?.position as number | null) ?? 0) + 1;

  const { data, error } = await supabase
    .from('queue_tickets')
    .insert({ queue_id: queueId, ticket_id: ticketId, position: nextPos, priority })
    .select()
    .single();

  if (error) throw new Error(error.message);
  return data as QueueTicket;
}

export async function getQueueTickets(queueId: string): Promise<QueueTicket[]> {
  const { data, error } = await supabase
    .from('queue_tickets')
    .select(`
      *,
      ticket:tickets(
        id, subject, status, priority, created_at,
        customer:customers(name, email)
      )
    `)
    .eq('queue_id', queueId)
    .order('priority', { ascending: false })
    .order('position', { ascending: true });

  if (error) throw new Error(error.message);
  return (data ?? []) as QueueTicket[];
}

export async function removeTicketFromQueue(queueTicketId: string): Promise<void> {
  const { error } = await supabase
    .from('queue_tickets')
    .delete()
    .eq('id', queueTicketId);
  if (error) throw new Error(error.message);
}

export async function listOperatorsForQueue(): Promise<
  { id: string; user_id: string; status: string; profile: { full_name: string; email: string } | null }[]
> {
  const { data, error } = await supabase
    .from('operators')
    .select(`
      id, user_id, status,
      profile:profiles!operators_user_id_fkey(full_name, email)
    `)
    .order('created_at', { ascending: true });

  if (error) throw new Error(error.message);
  return (data ?? []) as { id: string; user_id: string; status: string; profile: { full_name: string; email: string } | null }[];
}
