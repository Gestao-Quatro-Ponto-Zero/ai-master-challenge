const EDGE_URL = `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/channel-ingest/chat`;
const ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

export interface SendMessagePayload {
  session_id: string;
  message: string;
  name?: string;
  email?: string;
  phone?: string;
}

export interface SendMessageResult {
  ticket_id: string;
  customer_id: string;
  conversation_id: string;
  message_id: string;
  is_new_ticket: boolean;
  is_new_customer: boolean;
}

export async function sendChatMessage(payload: SendMessagePayload): Promise<SendMessageResult> {
  const res = await fetch(EDGE_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${ANON_KEY}`,
      Apikey: ANON_KEY,
    },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to send message');
  return data as SendMessageResult;
}
