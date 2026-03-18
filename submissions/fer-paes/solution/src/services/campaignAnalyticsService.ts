import { supabase } from '../lib/supabaseClient';
import type { CampaignChannel, CampaignStatus } from './campaignService';

export type CampaignEventType =
  | 'campaign_sent'
  | 'campaign_delivered'
  | 'campaign_opened'
  | 'campaign_clicked'
  | 'campaign_replied'
  | 'campaign_converted';

export interface CampaignMetrics {
  campaign_id:      string;
  sent_count:       number;
  delivered_count:  number;
  open_count:       number;
  click_count:      number;
  reply_count:      number;
  conversion_count: number;
  open_rate:        number;
  click_rate:       number;
  reply_rate:       number;
  conversion_rate:  number;
  updated_at:       string | null;
}

export interface CampaignAnalyticsRow extends CampaignMetrics {
  campaign_name:    string;
  campaign_status:  CampaignStatus;
  campaign_channel: CampaignChannel;
  segment_name:     string | null;
}

export interface AnalyticsOverview {
  total_campaigns:     number;
  total_sent:          number;
  total_delivered:     number;
  total_opens:         number;
  total_clicks:        number;
  total_replies:       number;
  total_conversions:   number;
  avg_open_rate:       number;
  avg_click_rate:      number;
  avg_conversion_rate: number;
}

export interface TimeseriesPoint {
  day:        string;
  event_type: CampaignEventType;
  count:      number;
}

function toNum(v: unknown): number {
  return Number(v ?? 0);
}

function mapMetrics(r: Record<string, unknown>): CampaignMetrics {
  return {
    campaign_id:      String(r.campaign_id ?? ''),
    sent_count:       toNum(r.sent_count),
    delivered_count:  toNum(r.delivered_count),
    open_count:       toNum(r.open_count),
    click_count:      toNum(r.click_count),
    reply_count:      toNum(r.reply_count),
    conversion_count: toNum(r.conversion_count),
    open_rate:        toNum(r.open_rate),
    click_rate:       toNum(r.click_rate),
    reply_rate:       toNum(r.reply_rate),
    conversion_rate:  toNum(r.conversion_rate),
    updated_at:       (r.updated_at as string) ?? null,
  };
}

export async function getAllCampaignAnalytics(): Promise<CampaignAnalyticsRow[]> {
  const { data, error } = await supabase.rpc('get_all_campaign_analytics');
  if (error) throw new Error(error.message);
  return ((data ?? []) as Record<string, unknown>[]).map((r) => ({
    ...mapMetrics(r),
    campaign_name:    String(r.campaign_name    ?? ''),
    campaign_status:  (r.campaign_status  as CampaignStatus)  ?? 'draft',
    campaign_channel: (r.campaign_channel as CampaignChannel) ?? 'email',
    segment_name:     (r.segment_name as string) ?? null,
  }));
}

export async function getCampaignMetrics(campaignId: string): Promise<CampaignMetrics | null> {
  const { data, error } = await supabase.rpc('get_campaign_metrics', { p_campaign_id: campaignId });
  if (error) throw new Error(error.message);
  const rows = (data ?? []) as Record<string, unknown>[];
  if (rows.length === 0) return null;
  return mapMetrics(rows[0]);
}

export async function getAnalyticsOverview(): Promise<AnalyticsOverview | null> {
  const { data, error } = await supabase.rpc('get_campaign_analytics_overview');
  if (error) throw new Error(error.message);
  const rows = (data ?? []) as Record<string, unknown>[];
  if (rows.length === 0) return null;
  const r = rows[0];
  return {
    total_campaigns:     toNum(r.total_campaigns),
    total_sent:          toNum(r.total_sent),
    total_delivered:     toNum(r.total_delivered),
    total_opens:         toNum(r.total_opens),
    total_clicks:        toNum(r.total_clicks),
    total_replies:       toNum(r.total_replies),
    total_conversions:   toNum(r.total_conversions),
    avg_open_rate:       toNum(r.avg_open_rate),
    avg_click_rate:      toNum(r.avg_click_rate),
    avg_conversion_rate: toNum(r.avg_conversion_rate),
  };
}

export async function getEventsTimeseries(
  campaignId?: string,
  days = 30,
): Promise<TimeseriesPoint[]> {
  const { data, error } = await supabase.rpc('get_campaign_events_timeseries', {
    p_campaign_id: campaignId ?? null,
    p_days:        days,
  });
  if (error) throw new Error(error.message);
  return ((data ?? []) as Record<string, unknown>[]).map((r) => ({
    day:        String(r.day ?? ''),
    event_type: r.event_type as CampaignEventType,
    count:      toNum(r.count),
  }));
}

export async function registerCampaignEvent(
  campaignId: string,
  customerId:  string,
  eventType:   CampaignEventType,
  metadata?:   Record<string, unknown>,
): Promise<boolean> {
  const { data, error } = await supabase.rpc('register_campaign_event', {
    p_campaign_id: campaignId,
    p_customer_id: customerId,
    p_event_type:  eventType,
    p_metadata:    metadata ?? null,
  });
  if (error) throw new Error(error.message);
  return Boolean(data);
}

export async function syncCampaignMetrics(campaignId: string): Promise<void> {
  const { error } = await supabase.rpc('sync_campaign_metrics', { p_campaign_id: campaignId });
  if (error) throw new Error(error.message);
}

export async function syncAllCampaignMetrics(): Promise<number> {
  const { data, error } = await supabase.rpc('sync_all_campaign_metrics');
  if (error) throw new Error(error.message);
  return toNum(data);
}

export const EVENT_META: Record<CampaignEventType, { label: string; color: string; bg: string; fill: string }> = {
  campaign_sent:      { label: 'Enviados',   color: 'text-sky-600',    bg: 'bg-sky-50',     fill: '#0ea5e9' },
  campaign_delivered: { label: 'Entregues',  color: 'text-emerald-600',bg: 'bg-emerald-50', fill: '#10b981' },
  campaign_opened:    { label: 'Abertos',    color: 'text-blue-600',   bg: 'bg-blue-50',    fill: '#3b82f6' },
  campaign_clicked:   { label: 'Clicados',   color: 'text-violet-600', bg: 'bg-violet-50',  fill: '#8b5cf6' },
  campaign_replied:   { label: 'Respondidos',color: 'text-amber-600',  bg: 'bg-amber-50',   fill: '#f59e0b' },
  campaign_converted: { label: 'Convertidos',color: 'text-teal-600',   bg: 'bg-teal-50',    fill: '#14b8a6' },
};
