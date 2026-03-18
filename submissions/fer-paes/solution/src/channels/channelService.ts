import { supabase } from '../lib/supabaseClient';
import type {
  NormalizedPayload,
  ChatAdapterPayload,
  EmailAdapterPayload,
  ApiAdapterPayload,
  ChannelIngestResult,
  Channel,
  TicketWithRelations,
} from '../types';
import { adaptChatMessage } from './adapters/chatAdapter';
import { adaptEmailMessage } from './adapters/emailAdapter';
import { adaptApiMessage } from './adapters/apiAdapter';
import { identifyOrCreateCustomer } from '../services/customerService';
import { getTickets, createTicket } from '../services/ticketService';
import { createMessage } from '../services/messageService';

async function getChannelByType(type: string): Promise<Channel | null> {
  const { data, error } = await supabase
    .from('channels')
    .select('*')
    .eq('type', type)
    .eq('is_active', true)
    .maybeSingle();

  if (error) throw new Error(error.message);
  return data as Channel | null;
}

async function findOpenTicketForCustomer(
  customerId: string,
  channelId: string,
): Promise<TicketWithRelations | null> {
  const tickets = await getTickets({ customer_id: customerId, channel_id: channelId });
  const open = tickets.find(
    (t) => t.status !== 'closed' && t.status !== 'resolved',
  );
  return open ?? null;
}

export async function handleIncomingMessage(
  payload: NormalizedPayload,
): Promise<ChannelIngestResult> {
  const channel = await getChannelByType(payload.channel);
  if (!channel) throw new Error(`No active channel found for type: ${payload.channel}`);

  const existingCustomer = await identifyOrCreateCustomer({
    name: payload.customer.name,
    email: payload.customer.email,
    phone: payload.customer.phone,
    external_id: payload.external_id,
    external_source: payload.channel,
  });
  const isNewCustomer = !existingCustomer.created_at ||
    Date.now() - new Date(existingCustomer.created_at).getTime() < 3000;

  let ticket = await findOpenTicketForCustomer(existingCustomer.id, channel.id);
  let isNewTicket = false;

  if (!ticket) {
    isNewTicket = true;
    ticket = await createTicket({
      customer_id: existingCustomer.id,
      channel_id: channel.id,
      subject: payload.subject ?? undefined,
      initial_message: payload.message.content,
      priority: payload.priority ?? 'medium',
      source: payload.channel,
    });
  }

  const conversation = ticket.conversation;
  if (!conversation) throw new Error('Ticket has no conversation');

  let messageId: string;

  if (isNewTicket) {
    const { data: msgs } = await supabase
      .from('messages')
      .select('id')
      .eq('conversation_id', conversation.id)
      .order('created_at', { ascending: true })
      .limit(1);

    messageId = (msgs && msgs[0]?.id) ? msgs[0].id : '';
  } else {
    const msg = await createMessage({
      conversation_id: conversation.id,
      sender_type: 'customer',
      sender_id: existingCustomer.id,
      message: payload.message.content,
      message_type: payload.message.type,
      attachments: payload.message.attachments,
    });
    messageId = msg.id;
  }

  return {
    ticket_id: ticket.id,
    customer_id: existingCustomer.id,
    conversation_id: conversation.id,
    message_id: messageId,
    is_new_ticket: isNewTicket,
    is_new_customer: isNewCustomer,
  };
}

export async function handleChatMessage(raw: ChatAdapterPayload): Promise<ChannelIngestResult> {
  const normalized = adaptChatMessage(raw);
  return handleIncomingMessage(normalized);
}

export async function handleEmailMessage(raw: EmailAdapterPayload): Promise<ChannelIngestResult> {
  const normalized = adaptEmailMessage(raw);
  return handleIncomingMessage(normalized);
}

export async function handleApiMessage(raw: ApiAdapterPayload): Promise<ChannelIngestResult> {
  const normalized = adaptApiMessage(raw);
  return handleIncomingMessage(normalized);
}
