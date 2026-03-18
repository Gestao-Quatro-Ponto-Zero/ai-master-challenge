import { supabase } from '../lib/supabaseClient';
import { createMessage } from './messageService';
import { changeStatus } from './ticketService';
import type { TicketWithRelations, MessageWithAttachments } from '../types';

export type { MessageWithAttachments };

export interface WorkspaceTicket extends TicketWithRelations {
  assigned_at:         string | null;
  last_operator_reply: string | null;
  last_message_preview: string | null;
}

export async function getAssignedTickets(userId: string): Promise<WorkspaceTicket[]> {
  const { data, error } = await supabase
    .from('tickets')
    .select(`
      *,
      customer:customers(*),
      channel:channels(*),
      conversation:conversations(id, last_message_at)
    `)
    .eq('assigned_user_id', userId)
    .not('status', 'in', '("resolved","closed")')
    .order('updated_at', { ascending: false });

  if (error) throw new Error(error.message);
  return normalizeTickets(data ?? []);
}

export async function getQueuedTickets(): Promise<WorkspaceTicket[]> {
  const { data: queueTickets, error: qtErr } = await supabase
    .from('queue_tickets')
    .select('ticket_id')
    .limit(30);

  if (qtErr) throw new Error(qtErr.message);
  if (!queueTickets || queueTickets.length === 0) return [];

  const ids = queueTickets.map((qt) => qt.ticket_id);

  const { data, error } = await supabase
    .from('tickets')
    .select(`
      *,
      customer:customers(*),
      channel:channels(*),
      conversation:conversations(id, last_message_at)
    `)
    .in('id', ids)
    .order('created_at', { ascending: true });

  if (error) throw new Error(error.message);
  return normalizeTickets(data ?? []);
}

export async function getResolvedTickets(userId: string): Promise<WorkspaceTicket[]> {
  const { data, error } = await supabase
    .from('tickets')
    .select(`
      *,
      customer:customers(*),
      channel:channels(*),
      conversation:conversations(id, last_message_at)
    `)
    .eq('assigned_user_id', userId)
    .in('status', ['resolved', 'closed'])
    .order('updated_at', { ascending: false })
    .limit(25);

  if (error) throw new Error(error.message);
  return normalizeTickets(data ?? []);
}

function normalizeTickets(raw: unknown[]): WorkspaceTicket[] {
  return (raw as Record<string, unknown>[]).map((r) => {
    const customer  = Array.isArray(r.customer)  ? (r.customer as unknown[])[0]  ?? null : r.customer;
    const channel   = Array.isArray(r.channel)   ? (r.channel as unknown[])[0]   ?? null : r.channel;
    const convArr   = Array.isArray(r.conversation) ? r.conversation as unknown[] : r.conversation ? [r.conversation] : [];
    const conv      = (convArr[0] ?? null) as Record<string, unknown> | null;
    return {
      ...r,
      customer,
      channel,
      conversation: conv,
      assigned_user: null,
      assigned_at:   (r.assigned_at ?? null) as string | null,
      last_operator_reply: (r.last_operator_reply ?? null) as string | null,
      last_message_preview: null,
    } as WorkspaceTicket;
  });
}

export interface ConversationData {
  id:              string;
  ticket_id:       string;
  started_at:      string;
  last_message_at: string | null;
}

export async function getConversation(ticketId: string): Promise<ConversationData | null> {
  const { data, error } = await supabase
    .from('conversations')
    .select('*')
    .eq('ticket_id', ticketId)
    .maybeSingle();
  if (error) throw new Error(error.message);
  return data as ConversationData | null;
}

export async function getMessages(
  conversationId: string,
  limit = 50,
  offset = 0,
): Promise<MessageWithAttachments[]> {
  const { data, error } = await supabase
    .from('messages')
    .select('*, attachments(*)')
    .eq('conversation_id', conversationId)
    .order('created_at', { ascending: true })
    .range(offset, offset + limit - 1);

  if (error) throw new Error(error.message);
  return ((data ?? []) as (import('../types').Message & { attachments: import('../types').Attachment[] })[]).map((row) => ({
    ...row,
    attachments: row.attachments ?? [],
  }));
}

export async function pollMessages(
  conversationId: string,
  since: string,
): Promise<MessageWithAttachments[]> {
  const { data, error } = await supabase
    .from('messages')
    .select('*, attachments(*)')
    .eq('conversation_id', conversationId)
    .gt('created_at', since)
    .order('created_at', { ascending: true });

  if (error) throw new Error(error.message);
  return ((data ?? []) as (import('../types').Message & { attachments: import('../types').Attachment[] })[]).map((row) => ({
    ...row,
    attachments: row.attachments ?? [],
  }));
}

export async function sendOperatorMessage(
  conversationId: string,
  ticketId:        string,
  senderId:        string,
  text:            string,
): Promise<MessageWithAttachments> {
  const msg = await createMessage({
    conversation_id: conversationId,
    sender_type:     'operator',
    sender_id:       senderId,
    message:         text,
    message_type:    'text',
  });

  const now = new Date().toISOString();

  await supabase
    .from('tickets')
    .update({ last_operator_reply: now, status: 'in_progress', updated_at: now })
    .eq('id', ticketId)
    .eq('status', 'open');

  return msg;
}

export async function sendAttachmentMessage(
  conversationId: string,
  ticketId:        string,
  senderId:        string,
  file:            File,
): Promise<MessageWithAttachments> {
  const ext       = file.name.split('.').pop() ?? 'bin';
  const path      = `workspace/${ticketId}/${Date.now()}_${Math.random().toString(36).slice(2)}.${ext}`;
  const bucket    = 'attachments';

  const { error: uploadErr } = await supabase.storage
    .from(bucket)
    .upload(path, file, { contentType: file.type, upsert: false });

  if (uploadErr) throw new Error(`Upload failed: ${uploadErr.message}`);

  const { data: publicData } = supabase.storage.from(bucket).getPublicUrl(path);
  const fileUrl = publicData.publicUrl;

  return createMessage({
    conversation_id: conversationId,
    sender_type:     'operator',
    sender_id:       senderId,
    message:         file.name,
    message_type:    file.type.startsWith('image/') ? 'image' : 'file',
    attachments: [{
      file_url:  fileUrl,
      file_type: file.type,
      file_size: file.size,
    }],
  });
}

export async function resolveTicket(ticketId: string, userId: string): Promise<void> {
  await changeStatus(ticketId, 'resolved', userId);
}

export async function reopenTicket(ticketId: string, userId: string): Promise<void> {
  await changeStatus(ticketId, 'in_progress', userId);
}

export async function transferToOperator(
  ticketId:   string,
  toUserId:   string,
  fromUserId: string,
): Promise<void> {
  const now = new Date().toISOString();

  await supabase
    .from('tickets')
    .update({ assigned_user_id: toUserId, assigned_at: now, updated_at: now })
    .eq('id', ticketId);

  await supabase.from('audit_logs').insert({
    user_id:     fromUserId,
    action:      'ticket.transfer',
    resource:    'tickets',
    resource_id: ticketId,
    meta:        { transferred_to_user: toUserId, type: 'operator' },
  });
}

export async function transferToQueue(
  ticketId:   string,
  queueId:    string,
  fromUserId: string,
): Promise<void> {
  const { data: lastPos } = await supabase
    .from('queue_tickets')
    .select('position')
    .eq('queue_id', queueId)
    .order('position', { ascending: false })
    .limit(1)
    .maybeSingle();

  const position = ((lastPos?.position as number) ?? 0) + 1;

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
    .update({ assigned_user_id: null, updated_at: new Date().toISOString() })
    .eq('id', ticketId);

  await supabase.from('audit_logs').insert({
    user_id:     fromUserId,
    action:      'ticket.transfer',
    resource:    'tickets',
    resource_id: ticketId,
    meta:        { transferred_to_queue: queueId, type: 'queue' },
  });
}

export async function getCustomerHistory(
  customerId:      string,
  excludeTicketId: string,
): Promise<WorkspaceTicket[]> {
  const { data, error } = await supabase
    .from('tickets')
    .select('*, customer:customers(id,name,email), channel:channels(id,name,type), conversation:conversations(id,last_message_at)')
    .eq('customer_id', customerId)
    .neq('id', excludeTicketId)
    .order('created_at', { ascending: false })
    .limit(6);

  if (error) throw new Error(error.message);
  return normalizeTickets(data ?? []);
}

export interface OperatorUser {
  id:        string;
  user_id:   string;
  full_name: string;
  email:     string;
  status:    string;
}

export async function getOperatorsList(): Promise<OperatorUser[]> {
  const { data, error } = await supabase
    .from('operators')
    .select('id, user_id, status, profile:profiles!operators_user_id_fkey(full_name, email)')
    .eq('status', 'online')
    .order('created_at');

  if (error) throw new Error(error.message);

  return ((data ?? []) as unknown[]).map((raw) => {
    const op = raw as Record<string, unknown>;
    const profileArr = op.profile as { full_name: string; email: string }[] | null;
    const profile = Array.isArray(profileArr) ? profileArr[0] : profileArr;
    return {
      id:        op.id as string,
      user_id:   op.user_id as string,
      full_name: profile?.full_name ?? '',
      email:     profile?.email     ?? '',
      status:    op.status as string,
    };
  });
}

export interface QueueOption {
  id:   string;
  name: string;
}

export async function getQueuesList(): Promise<QueueOption[]> {
  const { data, error } = await supabase
    .from('queues')
    .select('id, name')
    .eq('is_active', true)
    .order('name');
  if (error) throw new Error(error.message);
  return (data ?? []) as QueueOption[];
}
