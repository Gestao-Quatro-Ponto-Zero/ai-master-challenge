import { supabase } from '../lib/supabaseClient';
import { applySLA, markResolved } from './slaService';
import { evaluateRules } from './automationService';
import type {
  Ticket,
  TicketWithRelations,
  TicketStatus,
  TicketPriority,
  CreateTicketPayload,
  TicketFilters,
  Conversation,
} from '../types';

export async function createTicket(data: CreateTicketPayload): Promise<TicketWithRelations> {
  const { data: ticket, error: ticketError } = await supabase
    .from('tickets')
    .insert({
      customer_id: data.customer_id,
      channel_id: data.channel_id,
      subject: data.subject ?? null,
      status: 'open',
      priority: data.priority ?? 'medium',
      source: data.source ?? null,
    })
    .select()
    .single();

  if (ticketError) throw new Error(ticketError.message);

  const now = new Date().toISOString();

  const { data: conversation, error: convError } = await supabase
    .from('conversations')
    .insert({
      ticket_id: ticket.id,
      started_at: now,
      last_message_at: now,
    })
    .select()
    .single();

  if (convError) throw new Error(convError.message);

  const { error: msgError } = await supabase.from('messages').insert({
    conversation_id: conversation.id,
    sender_type: 'customer',
    sender_id: data.customer_id,
    message: data.initial_message,
    message_type: 'text',
  });

  if (msgError) throw new Error(msgError.message);

  applySLA(ticket.id, ticket.priority, ticket.created_at).catch(() => {});

  evaluateRules('ticket_created', {
    ticket_id: ticket.id,
    priority: ticket.priority,
    status: ticket.status,
    channel_id: ticket.channel_id ?? undefined,
  }).catch(() => {});

  return getTicketById(ticket.id) as Promise<TicketWithRelations>;
}

export async function getTicketById(ticketId: string): Promise<TicketWithRelations | null> {
  const { data, error } = await supabase
    .from('tickets')
    .select(`
      *,
      customer:customers(*),
      channel:channels(*),
      conversation:conversations(*)
    `)
    .eq('id', ticketId)
    .maybeSingle();

  if (error) throw new Error(error.message);
  if (!data) return null;

  let assigned_user = null;
  if (data.assigned_user_id) {
    const { data: profile } = await supabase
      .from('profiles')
      .select('id, full_name, email')
      .eq('id', data.assigned_user_id)
      .maybeSingle();
    if (profile) {
      assigned_user = { id: profile.id, email: profile.email, full_name: profile.full_name };
    }
  }

  const conv = Array.isArray(data.conversation) ? data.conversation[0] ?? null : data.conversation;

  return {
    ...data,
    customer: Array.isArray(data.customer) ? data.customer[0] ?? null : data.customer,
    channel: Array.isArray(data.channel) ? data.channel[0] ?? null : data.channel,
    conversation: conv,
    assigned_user,
  } as TicketWithRelations;
}

export async function getTickets(filters: TicketFilters = {}): Promise<TicketWithRelations[]> {
  let query = supabase
    .from('tickets')
    .select(`
      *,
      customer:customers(*),
      channel:channels(*),
      conversation:conversations(*)
    `)
    .order('updated_at', { ascending: false });

  if (filters.status) query = query.eq('status', filters.status);
  if (filters.priority) query = query.eq('priority', filters.priority);
  if (filters.channel_id) query = query.eq('channel_id', filters.channel_id);
  if (filters.assigned_user_id) query = query.eq('assigned_user_id', filters.assigned_user_id);
  if (filters.customer_id) query = query.eq('customer_id', filters.customer_id);

  const { data, error } = await query;
  if (error) throw new Error(error.message);

  return ((data as unknown[]) || []).map((row: unknown) => {
    const r = row as Record<string, unknown>;
    const conv = Array.isArray(r.conversation) ? (r.conversation as Conversation[])[0] ?? null : r.conversation as Conversation | null;
    return {
      ...r,
      customer: Array.isArray(r.customer) ? (r.customer as unknown[])[0] ?? null : r.customer,
      channel: Array.isArray(r.channel) ? (r.channel as unknown[])[0] ?? null : r.channel,
      conversation: conv,
      assigned_user: null,
    } as TicketWithRelations;
  });
}

export async function assignTicket(ticketId: string, userId: string, changedBy: string): Promise<Ticket> {
  const { data, error } = await supabase
    .from('tickets')
    .update({ assigned_user_id: userId, updated_at: new Date().toISOString() })
    .eq('id', ticketId)
    .select()
    .single();

  if (error) throw new Error(error.message);

  await supabase.from('audit_logs').insert({
    user_id: changedBy,
    action: 'ticket.assign',
    resource: 'tickets',
    resource_id: ticketId,
    meta: { assigned_to: userId },
  });

  return data as Ticket;
}

export async function changeStatus(
  ticketId: string,
  newStatus: TicketStatus,
  changedBy: string,
): Promise<Ticket> {
  const { data: current, error: fetchError } = await supabase
    .from('tickets')
    .select('status')
    .eq('id', ticketId)
    .single();

  if (fetchError) throw new Error(fetchError.message);

  const oldStatus = current.status as TicketStatus;

  const { data, error } = await supabase
    .from('tickets')
    .update({ status: newStatus, updated_at: new Date().toISOString() })
    .eq('id', ticketId)
    .select()
    .single();

  if (error) throw new Error(error.message);

  await supabase.from('ticket_status_history').insert({
    ticket_id: ticketId,
    old_status: oldStatus,
    new_status: newStatus,
    changed_by: changedBy,
  });

  if (newStatus === 'resolved' || newStatus === 'closed') {
    markResolved(ticketId).catch(() => {});
  }

  return data as Ticket;
}

export async function closeTicket(ticketId: string, changedBy: string): Promise<Ticket> {
  const now = new Date().toISOString();

  const { data: current, error: fetchError } = await supabase
    .from('tickets')
    .select('status')
    .eq('id', ticketId)
    .single();

  if (fetchError) throw new Error(fetchError.message);

  const { data, error } = await supabase
    .from('tickets')
    .update({ status: 'closed', closed_at: now, updated_at: now })
    .eq('id', ticketId)
    .select()
    .single();

  if (error) throw new Error(error.message);

  await supabase.from('ticket_status_history').insert({
    ticket_id: ticketId,
    old_status: current.status,
    new_status: 'closed',
    changed_by: changedBy,
  });

  markResolved(ticketId).catch(() => {});

  return data as Ticket;
}

export async function updateResolutionNotes(ticketId: string, notes: string): Promise<void> {
  const { error } = await supabase
    .from('tickets')
    .update({ resolution_notes: notes, updated_at: new Date().toISOString() })
    .eq('id', ticketId);
  if (error) throw new Error(error.message);
}

export async function updateTicketActivity(ticketId: string): Promise<void> {
  const now = new Date().toISOString();

  await supabase
    .from('tickets')
    .update({ updated_at: now })
    .eq('id', ticketId);

  const { data: conv } = await supabase
    .from('conversations')
    .select('id')
    .eq('ticket_id', ticketId)
    .maybeSingle();

  if (conv) {
    await supabase
      .from('conversations')
      .update({ last_message_at: now })
      .eq('id', conv.id);
  }
}

export async function getChannels(): Promise<import('../types').Channel[]> {
  const { data, error } = await supabase
    .from('channels')
    .select('*')
    .eq('is_active', true)
    .order('name');
  if (error) throw new Error(error.message);
  return (data || []) as import('../types').Channel[];
}

export async function getStatusHistory(ticketId: string) {
  const { data, error } = await supabase
    .from('ticket_status_history')
    .select('*')
    .eq('ticket_id', ticketId)
    .order('created_at', { ascending: false });
  if (error) throw new Error(error.message);
  return data || [];
}

export function getPriorityOrder(priority: TicketPriority): number {
  const order: Record<TicketPriority, number> = { urgent: 0, high: 1, medium: 2, low: 3 };
  return order[priority] ?? 2;
}
