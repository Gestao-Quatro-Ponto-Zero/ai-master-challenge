import { supabase } from '../lib/supabaseClient';

export type DeliveryStatus = 'pending' | 'sending' | 'sent' | 'delivered' | 'failed' | 'skipped';
export type DeliveryChannel = 'email' | 'whatsapp' | 'chat' | 'sms';

export interface CampaignDelivery {
  id:             string;
  campaign_id:    string;
  campaign_name:  string;
  customer_id:    string;
  customer_name:  string;
  customer_email: string;
  channel:        DeliveryChannel;
  status:         DeliveryStatus;
  message_body:   string | null;
  sent_at:        string | null;
  delivered_at:   string | null;
  failed_at:      string | null;
  error_message:  string | null;
  retry_count:    number;
  created_at:     string;
}

export interface DeliveryStats {
  total:         number;
  pending:       number;
  sending:       number;
  sent:          number;
  delivered:     number;
  failed:        number;
  skipped:       number;
  delivery_rate: number;
}

export interface GetDeliveriesFilter {
  campaign_id?: string;
  status?:      DeliveryStatus;
  channel?:     DeliveryChannel;
  limit?:       number;
  offset?:      number;
}

export async function getDeliveries(filter: GetDeliveriesFilter = {}): Promise<CampaignDelivery[]> {
  const { data, error } = await supabase.rpc('get_deliveries', {
    p_campaign_id: filter.campaign_id ?? null,
    p_status:      filter.status      ?? null,
    p_channel:     filter.channel     ?? null,
    p_limit:       filter.limit       ?? 100,
    p_offset:      filter.offset      ?? 0,
  });
  if (error) throw new Error(error.message);
  return ((data ?? []) as CampaignDelivery[]).map((d) => ({
    ...d,
    retry_count: Number(d.retry_count),
  }));
}

export async function getCampaignDeliveries(campaignId: string): Promise<CampaignDelivery[]> {
  return getDeliveries({ campaign_id: campaignId, limit: 500 });
}

export async function getCampaignDeliveryStats(campaignId: string): Promise<DeliveryStats | null> {
  const { data, error } = await supabase.rpc('get_campaign_delivery_stats', { p_campaign_id: campaignId });
  if (error) throw new Error(error.message);
  const rows = data as DeliveryStats[];
  if (!rows || rows.length === 0) return null;
  const r = rows[0];
  return {
    total:         Number(r.total),
    pending:       Number(r.pending),
    sending:       Number(r.sending),
    sent:          Number(r.sent),
    delivered:     Number(r.delivered),
    failed:        Number(r.failed),
    skipped:       Number(r.skipped),
    delivery_rate: Number(r.delivery_rate),
  };
}

export async function executeCampaign(campaignId: string): Promise<number> {
  const { data, error } = await supabase.rpc('execute_campaign', { p_campaign_id: campaignId });
  if (error) throw new Error(error.message);
  return Number(data);
}

export async function updateDeliveryStatus(
  id:     string,
  status: DeliveryStatus,
  error?: string,
): Promise<void> {
  const { error: err } = await supabase.rpc('update_delivery_status', {
    p_id:     id,
    p_status: status,
    p_error:  error ?? null,
  });
  if (err) throw new Error(err.message);
}

export async function retryFailedDeliveries(campaignId: string): Promise<number> {
  const { data, error } = await supabase.rpc('retry_failed_deliveries', { p_campaign_id: campaignId });
  if (error) throw new Error(error.message);
  return Number(data);
}

export const STATUS_META: Record<DeliveryStatus, { label: string; color: string; bg: string; border: string; dot: string }> = {
  pending:   { label: 'Pendente',   color: 'text-gray-500',    bg: 'bg-gray-100',     border: 'border-gray-200',   dot: 'bg-gray-400'   },
  sending:   { label: 'Enviando',   color: 'text-blue-600',    bg: 'bg-blue-50',      border: 'border-blue-100',   dot: 'bg-blue-500'   },
  sent:      { label: 'Enviado',    color: 'text-sky-600',     bg: 'bg-sky-50',       border: 'border-sky-100',    dot: 'bg-sky-500'    },
  delivered: { label: 'Entregue',   color: 'text-emerald-600', bg: 'bg-emerald-50',   border: 'border-emerald-100',dot: 'bg-emerald-500'},
  failed:    { label: 'Falhou',     color: 'text-red-600',     bg: 'bg-red-50',       border: 'border-red-100',    dot: 'bg-red-500'    },
  skipped:   { label: 'Ignorado',   color: 'text-gray-400',    bg: 'bg-gray-50',      border: 'border-gray-100',   dot: 'bg-gray-300'   },
};

export const CHANNEL_META: Record<DeliveryChannel, { label: string; color: string; bg: string }> = {
  email:     { label: 'Email',     color: 'text-blue-600',  bg: 'bg-blue-50'   },
  whatsapp:  { label: 'WhatsApp',  color: 'text-green-600', bg: 'bg-green-50'  },
  chat:      { label: 'Chat',      color: 'text-violet-600',bg: 'bg-violet-50' },
  sms:       { label: 'SMS',       color: 'text-amber-600', bg: 'bg-amber-50'  },
};

export const DELIVERY_STATUSES: DeliveryStatus[] = ['pending','sending','sent','delivered','failed','skipped'];
export const DELIVERY_CHANNELS: DeliveryChannel[] = ['email','whatsapp','chat','sms'];
