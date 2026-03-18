import { supabase } from '../lib/supabaseClient';
import { evaluateRules } from './automationService';
import type { Message, Attachment, SenderType, MessageType } from '../types';

export interface CreateMessageData {
  conversation_id: string;
  sender_type: SenderType;
  sender_id: string | null;
  message: string;
  message_type?: MessageType;
  metadata?: Record<string, unknown>;
  attachments?: CreateAttachmentData[];
}

export interface CreateAttachmentData {
  file_url: string;
  file_type: string;
  file_size: number;
}

export interface MessageWithAttachments extends Message {
  attachments: Attachment[];
}

export async function createMessage(data: CreateMessageData): Promise<MessageWithAttachments> {
  const { data: conv, error: convError } = await supabase
    .from('conversations')
    .select('id, ticket_id')
    .eq('id', data.conversation_id)
    .maybeSingle();

  if (convError) throw new Error(convError.message);
  if (!conv) throw new Error('Conversation not found');

  const { data: msg, error: msgError } = await supabase
    .from('messages')
    .insert({
      conversation_id: data.conversation_id,
      sender_type: data.sender_type,
      sender_id: data.sender_id,
      message: data.message,
      message_type: data.message_type ?? 'text',
      metadata: data.metadata ?? null,
    })
    .select()
    .single();

  if (msgError) throw new Error(msgError.message);

  let savedAttachments: Attachment[] = [];

  if (data.attachments && data.attachments.length > 0) {
    const rows = data.attachments.map((a) => ({
      message_id: msg.id,
      file_url: a.file_url,
      file_type: a.file_type,
      file_size: a.file_size,
    }));

    const { data: attData, error: attError } = await supabase
      .from('attachments')
      .insert(rows)
      .select();

    if (attError) throw new Error(attError.message);
    savedAttachments = (attData || []) as Attachment[];
  }

  const now = new Date().toISOString();

  await supabase
    .from('conversations')
    .update({ last_message_at: now })
    .eq('id', data.conversation_id);

  const { data: ticketCtx } = await supabase
    .from('tickets')
    .select('priority, status, channel_id')
    .eq('id', conv.ticket_id)
    .maybeSingle();

  await supabase
    .from('tickets')
    .update({ updated_at: now })
    .eq('id', conv.ticket_id);

  if (ticketCtx && data.sender_type === 'customer') {
    evaluateRules('message_received', {
      ticket_id: conv.ticket_id,
      priority: ticketCtx.priority,
      status: ticketCtx.status,
      channel_id: ticketCtx.channel_id ?? undefined,
    }).catch(() => {});
  }

  return { ...(msg as Message), attachments: savedAttachments };
}

export async function getMessages(
  conversationId: string,
  limit = 20,
  offset = 0,
): Promise<MessageWithAttachments[]> {
  const { data, error } = await supabase
    .from('messages')
    .select('*, attachments(*)')
    .eq('conversation_id', conversationId)
    .order('created_at', { ascending: true })
    .range(offset, offset + limit - 1);

  if (error) throw new Error(error.message);

  return ((data || []) as (Message & { attachments: Attachment[] })[]).map((row) => ({
    ...row,
    attachments: row.attachments || [],
  }));
}

export async function countMessages(conversationId: string): Promise<number> {
  const { count, error } = await supabase
    .from('messages')
    .select('id', { count: 'exact', head: true })
    .eq('conversation_id', conversationId);

  if (error) throw new Error(error.message);
  return count ?? 0;
}

export async function getMessageById(messageId: string): Promise<MessageWithAttachments | null> {
  const { data, error } = await supabase
    .from('messages')
    .select('*, attachments(*)')
    .eq('id', messageId)
    .maybeSingle();

  if (error) throw new Error(error.message);
  if (!data) return null;

  const row = data as Message & { attachments: Attachment[] };
  return { ...row, attachments: row.attachments || [] };
}

export async function addAttachment(
  messageId: string,
  attachment: CreateAttachmentData,
): Promise<Attachment> {
  const { data, error } = await supabase
    .from('attachments')
    .insert({
      message_id: messageId,
      file_url: attachment.file_url,
      file_type: attachment.file_type,
      file_size: attachment.file_size,
    })
    .select()
    .single();

  if (error) throw new Error(error.message);
  return data as Attachment;
}

export async function getMessageAttachments(messageId: string): Promise<Attachment[]> {
  const { data, error } = await supabase
    .from('attachments')
    .select('*')
    .eq('message_id', messageId)
    .order('created_at', { ascending: true });

  if (error) throw new Error(error.message);
  return (data || []) as Attachment[];
}

export async function deleteMessage(messageId: string): Promise<void> {
  const { data: existing, error: fetchError } = await supabase
    .from('messages')
    .select('metadata')
    .eq('id', messageId)
    .maybeSingle();

  if (fetchError) throw new Error(fetchError.message);
  if (!existing) throw new Error('Message not found');

  const currentMeta = (existing.metadata as Record<string, unknown>) || {};
  const updatedMeta = { ...currentMeta, deleted: true, deleted_at: new Date().toISOString() };

  const { error } = await supabase
    .from('messages')
    .update({ metadata: updatedMeta })
    .eq('id', messageId);

  if (error) throw new Error(error.message);
}
