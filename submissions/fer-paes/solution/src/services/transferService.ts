import { supabase } from '../lib/supabaseClient';
import type { OperatorStatus } from '../types';

export type TransferType = 'operator' | 'queue' | 'agent';

export interface TicketTransfer {
  id:               string;
  ticket_id:        string;
  from_operator_id: string | null;
  to_operator_id:   string | null;
  to_queue_id:      string | null;
  to_agent_id:      string | null;
  transfer_type:    TransferType;
  reason:           string | null;
  created_at:       string;
}

export interface TransferPayload {
  ticket_id:     string;
  transfer_type: TransferType;
  target_id:     string;
  reason?:       string;
  from_user_id:  string;
}

export interface OperatorTarget {
  id:             string;
  user_id:        string;
  full_name:      string;
  email:          string;
  presence_status: OperatorStatus;
  active_tickets: number;
  max_tickets:    number;
}

export interface QueueTarget {
  id:              string;
  name:            string;
  tickets_waiting: number;
  operators_count: number;
}

export interface AgentTarget {
  id:     string;
  name:   string;
  type:   string | null;
  status: string;
}

async function resolveOperatorId(userId: string): Promise<string | null> {
  const { data } = await supabase
    .from('operators')
    .select('id')
    .eq('user_id', userId)
    .maybeSingle();
  return data?.id ?? null;
}

async function logTransfer(params: {
  ticket_id:        string;
  from_operator_id: string | null;
  to_operator_id?:  string;
  to_queue_id?:     string;
  to_agent_id?:     string;
  transfer_type:    TransferType;
  reason?:          string;
}): Promise<TicketTransfer> {
  const { data, error } = await supabase
    .from('ticket_transfers')
    .insert({
      ticket_id:        params.ticket_id,
      from_operator_id: params.from_operator_id,
      to_operator_id:   params.to_operator_id   ?? null,
      to_queue_id:      params.to_queue_id       ?? null,
      to_agent_id:      params.to_agent_id       ?? null,
      transfer_type:    params.transfer_type,
      reason:           params.reason            ?? null,
    })
    .select()
    .single();

  if (error) throw new Error(error.message);
  return data as TicketTransfer;
}

export async function transferToOperator(
  ticketId:      string,
  operatorId:    string,
  fromUserId:    string,
  reason?:       string,
): Promise<void> {
  const now = new Date().toISOString();

  const { data: op, error: opErr } = await supabase
    .from('operators')
    .select('user_id')
    .eq('id', operatorId)
    .maybeSingle();

  if (opErr || !op) throw new Error('Target operator not found');

  await supabase
    .from('tickets')
    .update({ assigned_user_id: op.user_id, updated_at: now })
    .eq('id', ticketId);

  await supabase
    .from('queue_tickets')
    .delete()
    .eq('ticket_id', ticketId);

  const fromOperatorId = await resolveOperatorId(fromUserId);

  await logTransfer({
    ticket_id:        ticketId,
    from_operator_id: fromOperatorId,
    to_operator_id:   operatorId,
    transfer_type:    'operator',
    reason,
  });

  await supabase.from('audit_logs').insert({
    user_id:     fromUserId,
    action:      'ticket.transfer',
    resource:    'tickets',
    resource_id: ticketId,
    meta:        { transfer_type: 'operator', to_operator_id: operatorId, reason },
  });
}

export async function transferToQueue(
  ticketId:   string,
  queueId:    string,
  fromUserId: string,
  reason?:    string,
): Promise<void> {
  const now = new Date().toISOString();

  await supabase
    .from('queue_tickets')
    .delete()
    .eq('ticket_id', ticketId);

  const { data: maxRow } = await supabase
    .from('queue_tickets')
    .select('position')
    .eq('queue_id', queueId)
    .order('position', { ascending: false })
    .limit(1)
    .maybeSingle();

  const position = ((maxRow?.position as number | null) ?? 0) + 1;

  const { data: ticket } = await supabase
    .from('tickets')
    .select('priority')
    .eq('id', ticketId)
    .maybeSingle();

  const priorityMap: Record<string, number> = { urgent: 4, high: 3, medium: 2, low: 1 };
  const pNum = priorityMap[(ticket?.priority as string) ?? 'medium'] ?? 2;

  await supabase.from('queue_tickets').insert({
    queue_id: queueId, ticket_id: ticketId, priority: pNum, position,
  });

  await supabase
    .from('tickets')
    .update({ assigned_user_id: null, updated_at: now })
    .eq('id', ticketId);

  const fromOperatorId = await resolveOperatorId(fromUserId);

  await logTransfer({
    ticket_id:        ticketId,
    from_operator_id: fromOperatorId,
    to_queue_id:      queueId,
    transfer_type:    'queue',
    reason,
  });

  await supabase.from('audit_logs').insert({
    user_id:     fromUserId,
    action:      'ticket.transfer',
    resource:    'tickets',
    resource_id: ticketId,
    meta:        { transfer_type: 'queue', to_queue_id: queueId, reason },
  });
}

export async function transferToAgent(
  ticketId:   string,
  agentId:    string,
  fromUserId: string,
  reason?:    string,
): Promise<void> {
  const now = new Date().toISOString();

  await supabase
    .from('tickets')
    .update({ assigned_user_id: null, agent_id: agentId, updated_at: now })
    .eq('id', ticketId);

  const fromOperatorId = await resolveOperatorId(fromUserId);

  await logTransfer({
    ticket_id:        ticketId,
    from_operator_id: fromOperatorId,
    to_agent_id:      agentId,
    transfer_type:    'agent',
    reason,
  });

  await supabase.from('audit_logs').insert({
    user_id:     fromUserId,
    action:      'ticket.transfer',
    resource:    'tickets',
    resource_id: ticketId,
    meta:        { transfer_type: 'agent', to_agent_id: agentId, reason },
  });
}

export async function transferTicket(payload: TransferPayload): Promise<void> {
  const { ticket_id, transfer_type, target_id, reason, from_user_id } = payload;

  switch (transfer_type) {
    case 'operator':
      return transferToOperator(ticket_id, target_id, from_user_id, reason);
    case 'queue':
      return transferToQueue(ticket_id, target_id, from_user_id, reason);
    case 'agent':
      return transferToAgent(ticket_id, target_id, from_user_id, reason);
    default:
      throw new Error(`Unknown transfer type: ${transfer_type}`);
  }
}

export async function getTransferHistory(ticketId: string): Promise<TicketTransfer[]> {
  const { data, error } = await supabase
    .from('ticket_transfers')
    .select('*')
    .eq('ticket_id', ticketId)
    .order('created_at', { ascending: false });

  if (error) throw new Error(error.message);
  return (data ?? []) as TicketTransfer[];
}

export async function getOperatorTransferTargets(): Promise<OperatorTarget[]> {
  const { data: ops, error } = await supabase
    .from('operators')
    .select(`
      id, user_id, max_active_tickets,
      profile:profiles!operators_user_id_fkey(full_name, email),
      load:operator_ticket_load(active_tickets)
    `)
    .order('created_at', { ascending: true });

  if (error) throw new Error(error.message);

  const rows = (ops ?? []) as unknown[];

  const userIds = (rows as Record<string, unknown>[]).map((r) => r.user_id as string);
  const { data: presenceData } = await supabase
    .from('operator_presence')
    .select('user_id, status')
    .in('user_id', userIds);

  const presenceMap: Record<string, string> = {};
  (presenceData ?? []).forEach((p) => { presenceMap[p.user_id] = p.status; });

  return (rows as Record<string, unknown>[]).map((r) => {
    const profileArr = r.profile as { full_name?: string; email?: string }[] | null;
    const profile = Array.isArray(profileArr) ? profileArr[0] : profileArr;
    const loadArr  = r.load as { active_tickets?: number }[] | null;
    const load     = Array.isArray(loadArr) ? loadArr[0] : loadArr;
    return {
      id:              r.id as string,
      user_id:         r.user_id as string,
      full_name:       profile?.full_name ?? '',
      email:           profile?.email     ?? '',
      presence_status: (presenceMap[r.user_id as string] ?? 'offline') as OperatorStatus,
      active_tickets:  load?.active_tickets ?? 0,
      max_tickets:     r.max_active_tickets as number,
    };
  });
}

export async function getQueueTransferTargets(): Promise<QueueTarget[]> {
  const { data: queues, error } = await supabase
    .from('queues')
    .select('id, name')
    .eq('is_active', true)
    .order('name', { ascending: true });

  if (error) throw new Error(error.message);

  const ids = (queues ?? []).map((q) => q.id);
  if (ids.length === 0) return [];

  const [{ data: opCounts }, { data: ticketCounts }] = await Promise.all([
    supabase.from('queue_operators').select('queue_id').in('queue_id', ids),
    supabase.from('queue_tickets').select('queue_id').in('queue_id', ids),
  ]);

  const opMap: Record<string, number>   = {};
  const tkMap: Record<string, number>   = {};
  (opCounts     ?? []).forEach((r) => { opMap[r.queue_id] = (opMap[r.queue_id] ?? 0) + 1; });
  (ticketCounts ?? []).forEach((r) => { tkMap[r.queue_id] = (tkMap[r.queue_id] ?? 0) + 1; });

  return (queues ?? []).map((q) => ({
    id:              q.id,
    name:            q.name,
    tickets_waiting: tkMap[q.id] ?? 0,
    operators_count: opMap[q.id] ?? 0,
  }));
}

export async function getAgentTransferTargets(): Promise<AgentTarget[]> {
  const { data, error } = await supabase
    .from('agents')
    .select('id, name, type, status')
    .eq('status', 'active')
    .order('name', { ascending: true });

  if (error) throw new Error(error.message);
  return (data ?? []) as AgentTarget[];
}
