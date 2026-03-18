import { supabase } from '../lib/supabaseClient';
import type { Conversation } from '../types';
import {
  createMessage,
  getMessages,
  countMessages,
  type CreateMessageData,
  type MessageWithAttachments,
} from './messageService';

export type { MessageWithAttachments };

export async function createConversation(ticketId: string): Promise<Conversation> {
  const now = new Date().toISOString();
  const { data, error } = await supabase
    .from('conversations')
    .insert({ ticket_id: ticketId, started_at: now, last_message_at: now })
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as Conversation;
}

export async function getConversationById(conversationId: string): Promise<Conversation | null> {
  const { data, error } = await supabase
    .from('conversations')
    .select('*')
    .eq('id', conversationId)
    .maybeSingle();
  if (error) throw new Error(error.message);
  return data as Conversation | null;
}

export interface ConversationWithMessages {
  conversation: Conversation;
  messages: MessageWithAttachments[];
}

export async function getConversationByTicket(ticketId: string): Promise<ConversationWithMessages | null> {
  const { data: conv, error: convError } = await supabase
    .from('conversations')
    .select('*')
    .eq('ticket_id', ticketId)
    .maybeSingle();

  if (convError) throw new Error(convError.message);
  if (!conv) return null;

  const messages = await getMessages(conv.id, 20, 0);
  return { conversation: conv as Conversation, messages };
}

export async function getConversationMessages(
  conversationId: string,
  limit = 20,
  offset = 0,
): Promise<MessageWithAttachments[]> {
  return getMessages(conversationId, limit, offset);
}

export async function countConversationMessages(conversationId: string): Promise<number> {
  return countMessages(conversationId);
}

export async function addMessage(
  conversationId: string,
  senderId: string,
  senderType: string,
  message: string,
): Promise<MessageWithAttachments> {
  const data: CreateMessageData = {
    conversation_id: conversationId,
    sender_type: senderType as CreateMessageData['sender_type'],
    sender_id: senderId,
    message,
    message_type: 'text',
  };
  return createMessage(data);
}

export async function updateLastMessage(conversationId: string): Promise<void> {
  const now = new Date().toISOString();
  const { error } = await supabase
    .from('conversations')
    .update({ last_message_at: now })
    .eq('id', conversationId);
  if (error) throw new Error(error.message);
}
