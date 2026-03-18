import { supabase } from '../lib/supabaseClient';

export interface CustomerAnalyticsSummary {
  total_customers:          number;
  active_customers:         number;
  avg_engagement_score:     number;
  avg_tickets_per_customer: number;
}

export interface CustomerAnalyticsRow {
  customer_id:       string;
  customer_name:     string | null;
  customer_email:    string | null;
  total_messages:    number;
  total_tickets:     number;
  resolved_tickets:  number;
  avg_response_time: number | null;
  last_interaction:  string | null;
  engagement_score:  number;
  updated_at:        string;
}

export interface TopCustomerRow {
  customer_id:      string;
  customer_name:    string | null;
  customer_email:   string | null;
  total_messages:   number;
  total_tickets:    number;
  engagement_score: number;
  last_interaction: string | null;
}

export async function getCustomerAnalyticsSummary(): Promise<CustomerAnalyticsSummary> {
  const { data, error } = await supabase.rpc('get_customer_analytics_summary');
  if (error) throw new Error(error.message);
  const row = Array.isArray(data) ? data[0] : data;
  return {
    total_customers:          Number(row?.total_customers          ?? 0),
    active_customers:         Number(row?.active_customers         ?? 0),
    avg_engagement_score:     Number(row?.avg_engagement_score     ?? 0),
    avg_tickets_per_customer: Number(row?.avg_tickets_per_customer ?? 0),
  };
}

export async function getCustomerAnalyticsList(
  search = '',
  limit  = 100,
  offset = 0,
): Promise<CustomerAnalyticsRow[]> {
  const { data, error } = await supabase.rpc('get_customer_analytics_list', {
    p_search: search,
    p_limit:  limit,
    p_offset: offset,
  });
  if (error) throw new Error(error.message);
  return ((data ?? []) as CustomerAnalyticsRow[]).map((r) => ({
    ...r,
    total_messages:   Number(r.total_messages   ?? 0),
    total_tickets:    Number(r.total_tickets    ?? 0),
    resolved_tickets: Number(r.resolved_tickets ?? 0),
    engagement_score: Number(r.engagement_score ?? 0),
  }));
}

export async function getTopCustomersByEngagement(limit = 10): Promise<TopCustomerRow[]> {
  const { data, error } = await supabase.rpc('get_top_customers_by_engagement', { p_limit: limit });
  if (error) throw new Error(error.message);
  return ((data ?? []) as TopCustomerRow[]).map((r) => ({
    ...r,
    total_messages:   Number(r.total_messages   ?? 0),
    total_tickets:    Number(r.total_tickets    ?? 0),
    engagement_score: Number(r.engagement_score ?? 0),
  }));
}

export async function refreshCustomerAnalytics(customerId: string): Promise<void> {
  const { error } = await supabase.rpc('refresh_customer_analytics', { p_customer_id: customerId });
  if (error) throw new Error(error.message);
}

export async function refreshAllCustomerAnalytics(): Promise<number> {
  const { data, error } = await supabase.rpc('refresh_all_customer_analytics');
  if (error) throw new Error(error.message);
  return Number(data ?? 0);
}

export function formatResponseTime(seconds: number | null): string {
  if (seconds == null || seconds <= 0) return '—';
  if (seconds < 60)  return `${seconds}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}min`;
  return `${(seconds / 3600).toFixed(1)}h`;
}

export function formatLastInteraction(iso: string | null): string {
  if (!iso) return '—';
  const d    = new Date(iso);
  const now  = new Date();
  const diff = now.getTime() - d.getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1)    return 'Agora mesmo';
  if (mins < 60)   return `${mins}min atrás`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)    return `${hrs}h atrás`;
  const days = Math.floor(hrs / 24);
  if (days < 30)   return `${days}d atrás`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months} ${months === 1 ? 'mês' : 'meses'} atrás`;
  return `${Math.floor(months / 12)} anos atrás`;
}

export function engagementLabel(score: number): { label: string; color: string } {
  if (score >= 70) return { label: 'Alto',    color: 'text-emerald-600 bg-emerald-50 border-emerald-100' };
  if (score >= 40) return { label: 'Médio',   color: 'text-amber-600  bg-amber-50  border-amber-100'  };
  if (score >= 10) return { label: 'Baixo',   color: 'text-orange-600 bg-orange-50 border-orange-100' };
  return               { label: 'Inativo', color: 'text-gray-500   bg-gray-50   border-gray-100'   };
}
