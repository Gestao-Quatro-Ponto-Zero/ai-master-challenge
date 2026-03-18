import { supabase } from '../lib/supabaseClient';

export interface TicketStats {
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  closed_tickets: number;
  avg_response_time_seconds: number | null;
}

export async function getTicketStats(): Promise<TicketStats> {
  const [totalResult, openResult, resolvedResult, closedResult, avgResult] = await Promise.all([
    supabase.from('tickets').select('id', { count: 'exact', head: true }),
    supabase
      .from('tickets')
      .select('id', { count: 'exact', head: true })
      .in('status', ['open', 'in_progress', 'waiting_customer']),
    supabase
      .from('tickets')
      .select('id', { count: 'exact', head: true })
      .eq('status', 'resolved'),
    supabase
      .from('tickets')
      .select('id', { count: 'exact', head: true })
      .eq('status', 'closed'),
    supabase.rpc('get_avg_first_response_seconds'),
  ]);

  return {
    total_tickets: totalResult.count ?? 0,
    open_tickets: openResult.count ?? 0,
    resolved_tickets: resolvedResult.count ?? 0,
    closed_tickets: closedResult.count ?? 0,
    avg_response_time_seconds:
      avgResult.data != null ? Number(avgResult.data) : null,
  };
}

export function formatResponseTime(seconds: number | null): string {
  if (seconds === null || seconds <= 0) return '—';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  const remMins = mins % 60;
  return remMins > 0 ? `${hrs}h ${remMins}m` : `${hrs}h`;
}
