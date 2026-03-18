import { supabase } from '../lib/supabaseClient';

export type MetricPeriod = 'today' | '7d' | '30d' | '90d' | 'all';

export interface OperatorMetricRow {
  operator_id:             string;
  user_id:                 string;
  full_name:               string;
  email:                   string;
  tickets_handled:         number;
  tickets_resolved:        number;
  avg_first_response_time: number;
  avg_resolution_time:     number;
  avg_handle_time:         number;
  csat_score:              number | null;
  resolution_rate:         number;
}

export interface MetricsOverview {
  total_tickets_handled:    number;
  total_tickets_resolved:   number;
  avg_response_time_minutes: number;
  avg_resolution_time_minutes: number;
  overall_resolution_rate:  number;
}

export interface StoredMetricSnapshot {
  id:                      string;
  operator_id:             string;
  tickets_handled:         number;
  tickets_resolved:        number;
  avg_first_response_time: number;
  avg_resolution_time:     number;
  avg_handle_time:         number;
  csat_score:              number | null;
  period_start:            string;
  period_end:              string;
  created_at:              string;
}

export function getPeriodRange(period: MetricPeriod): { start: string; end: string } {
  const now = new Date();
  const end = now.toISOString();
  switch (period) {
    case 'today':
      return { start: new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString(), end };
    case '7d':
      return { start: new Date(Date.now() - 7 * 86_400_000).toISOString(), end };
    case '30d':
      return { start: new Date(Date.now() - 30 * 86_400_000).toISOString(), end };
    case '90d':
      return { start: new Date(Date.now() - 90 * 86_400_000).toISOString(), end };
    case 'all':
      return { start: '2000-01-01T00:00:00.000Z', end };
  }
}

export async function getAllOperatorsMetrics(period: MetricPeriod): Promise<OperatorMetricRow[]> {
  const { start, end } = getPeriodRange(period);

  const { data: operators } = await supabase
    .from('operators')
    .select('id, user_id, profile:profiles!operators_user_id_fkey(full_name, email)')
    .order('created_at', { ascending: true });

  if (!operators || operators.length === 0) return [];

  const userIds = operators.map((op) => op.user_id).filter(Boolean);

  const { data: tickets } = await supabase
    .from('tickets')
    .select('id, assigned_user_id, status, created_at, first_response_at, closed_at')
    .in('assigned_user_id', userIds)
    .gte('created_at', start)
    .lte('created_at', end);

  const ticketsByUser: Record<string, {
    id: string;
    assigned_user_id: string;
    status: string;
    created_at: string;
    first_response_at: string | null;
    closed_at: string | null;
  }[]> = {};

  (tickets ?? []).forEach((t) => {
    if (!t.assigned_user_id) return;
    if (!ticketsByUser[t.assigned_user_id]) ticketsByUser[t.assigned_user_id] = [];
    ticketsByUser[t.assigned_user_id].push(t as typeof ticketsByUser[string][number]);
  });

  return ((operators ?? []) as unknown[]).map((raw) => {
    const op      = raw as Record<string, unknown>;
    const profile = (Array.isArray(op.profile) ? op.profile[0] : op.profile) as { full_name?: string; email?: string } | null;
    const userId  = op.user_id as string;
    const ts      = ticketsByUser[userId] ?? [];

    const handled  = ts.length;
    const resolved = ts.filter((t) => ['resolved', 'closed'].includes(t.status)).length;

    const withFirstResp = ts.filter((t) => t.first_response_at);
    const avgFirstResp  = withFirstResp.length > 0
      ? Math.round(
          withFirstResp.reduce(
            (s, t) => s + (new Date(t.first_response_at!).getTime() - new Date(t.created_at).getTime()),
            0,
          ) / withFirstResp.length / 60_000,
        )
      : 0;

    const withClosed = ts.filter((t) => t.closed_at);
    const avgResolution = withClosed.length > 0
      ? Math.round(
          withClosed.reduce(
            (s, t) => s + (new Date(t.closed_at!).getTime() - new Date(t.created_at).getTime()),
            0,
          ) / withClosed.length / 60_000,
        )
      : 0;

    const avgHandleTime  = avgResolution > 0 ? avgResolution : avgFirstResp;
    const resolutionRate = handled > 0 ? Math.round((resolved / handled) * 100) : 0;

    return {
      operator_id:             op.id as string,
      user_id:                 userId,
      full_name:               profile?.full_name ?? '',
      email:                   profile?.email     ?? '',
      tickets_handled:         handled,
      tickets_resolved:        resolved,
      avg_first_response_time: avgFirstResp,
      avg_resolution_time:     avgResolution,
      avg_handle_time:         avgHandleTime,
      csat_score:              null,
      resolution_rate:         resolutionRate,
    } as OperatorMetricRow;
  });
}

export async function getOperatorMetricsSingle(
  operatorId: string,
  period: MetricPeriod,
): Promise<OperatorMetricRow | null> {
  const all = await getAllOperatorsMetrics(period);
  return all.find((r) => r.operator_id === operatorId) ?? null;
}

export function computeOverview(rows: OperatorMetricRow[]): MetricsOverview {
  if (rows.length === 0) {
    return {
      total_tickets_handled:       0,
      total_tickets_resolved:      0,
      avg_response_time_minutes:   0,
      avg_resolution_time_minutes: 0,
      overall_resolution_rate:     0,
    };
  }

  const totalHandled  = rows.reduce((s, r) => s + r.tickets_handled, 0);
  const totalResolved = rows.reduce((s, r) => s + r.tickets_resolved, 0);

  const responding = rows.filter((r) => r.avg_first_response_time > 0);
  const avgResponse = responding.length > 0
    ? Math.round(responding.reduce((s, r) => s + r.avg_first_response_time, 0) / responding.length)
    : 0;

  const resolving = rows.filter((r) => r.avg_resolution_time > 0);
  const avgResolution = resolving.length > 0
    ? Math.round(resolving.reduce((s, r) => s + r.avg_resolution_time, 0) / resolving.length)
    : 0;

  const resolutionRate = totalHandled > 0 ? Math.round((totalResolved / totalHandled) * 100) : 0;

  return {
    total_tickets_handled:       totalHandled,
    total_tickets_resolved:      totalResolved,
    avg_response_time_minutes:   avgResponse,
    avg_resolution_time_minutes: avgResolution,
    overall_resolution_rate:     resolutionRate,
  };
}

export async function saveOperatorMetricsSnapshot(
  rows:   OperatorMetricRow[],
  period: MetricPeriod,
): Promise<void> {
  if (rows.length === 0) return;
  const { start, end } = getPeriodRange(period);

  const records = rows.map((r) => ({
    operator_id:             r.operator_id,
    tickets_handled:         r.tickets_handled,
    tickets_resolved:        r.tickets_resolved,
    avg_first_response_time: r.avg_first_response_time,
    avg_resolution_time:     r.avg_resolution_time,
    avg_handle_time:         r.avg_handle_time,
    csat_score:              r.csat_score,
    period_start:            start,
    period_end:              end,
  }));

  await supabase.from('operator_metrics').insert(records);
}

export function formatDuration(minutes: number): string {
  if (minutes === 0) return '—';
  if (minutes < 60)  return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export function formatPeriodLabel(period: MetricPeriod): string {
  switch (period) {
    case 'today': return 'Today';
    case '7d':    return 'Last 7 days';
    case '30d':   return 'Last 30 days';
    case '90d':   return 'Last 90 days';
    case 'all':   return 'All time';
  }
}
