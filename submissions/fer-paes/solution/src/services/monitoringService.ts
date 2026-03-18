import { supabase } from '../lib/supabaseClient';

export interface OverviewMetrics {
  active_tickets:            number;
  queued_tickets:            number;
  online_operators:          number;
  busy_operators:            number;
  avg_response_time_minutes: number;
  resolved_today:            number;
}

export interface QueueMetric {
  id:                 string;
  name:               string;
  strategy:           string;
  is_active:          boolean;
  waiting_tickets:    number;
  assigned_operators: number;
}

export interface OperatorMetric {
  id:             string;
  user_id:        string;
  full_name:      string;
  email:          string;
  status:         string;
  active_tickets: number;
  max_tickets:    number;
  last_seen:      string | null;
}

export interface ActiveTicketRow {
  id:             string;
  subject:        string;
  status:         string;
  priority:       string;
  created_at:     string;
  customer_name:  string;
  customer_email: string;
  operator_id:    string | null;
  operator_name:  string | null;
  queue_name:     string | null;
}

export async function getOverviewMetrics(): Promise<OverviewMetrics> {
  const since24h = new Date(Date.now() - 86_400_000).toISOString();

  const [
    activeRes,
    queuedRes,
    onlineRes,
    busyRes,
    resolvedRes,
    avgRaw,
  ] = await Promise.all([
    supabase.from('tickets').select('id', { count: 'exact', head: true }).in('status', ['open', 'in_progress']),
    supabase.from('queue_tickets').select('id', { count: 'exact', head: true }).eq('status', 'pending'),
    supabase.from('operator_presence').select('id', { count: 'exact', head: true }).eq('status', 'online'),
    supabase.from('operator_presence').select('id', { count: 'exact', head: true }).eq('status', 'busy'),
    supabase.from('tickets').select('id', { count: 'exact', head: true }).in('status', ['resolved', 'closed']).gte('updated_at', since24h),
    supabase.from('tickets').select('created_at, first_response_at').not('first_response_at', 'is', null).gte('first_response_at', since24h).limit(200),
  ]);

  let avg_response_time_minutes = 0;
  const rows = (avgRaw.data ?? []) as { created_at: string; first_response_at: string }[];
  if (rows.length > 0) {
    const totalMs = rows.reduce(
      (s, r) => s + (new Date(r.first_response_at).getTime() - new Date(r.created_at).getTime()),
      0,
    );
    avg_response_time_minutes = Math.round(totalMs / rows.length / 60_000);
  }

  return {
    active_tickets:            activeRes.count   ?? 0,
    queued_tickets:            queuedRes.count   ?? 0,
    online_operators:          onlineRes.count   ?? 0,
    busy_operators:            busyRes.count     ?? 0,
    resolved_today:            resolvedRes.count ?? 0,
    avg_response_time_minutes,
  };
}

export async function getQueueMetrics(): Promise<QueueMetric[]> {
  const { data: queues } = await supabase
    .from('queues')
    .select('id, name, distribution_strategy, is_active')
    .order('priority', { ascending: true });

  if (!queues || queues.length === 0) return [];

  const queueIds = queues.map((q) => q.id);

  const [waitingRes, opsRes] = await Promise.all([
    supabase.from('queue_tickets').select('queue_id').eq('status', 'pending').in('queue_id', queueIds),
    supabase.from('queue_operators').select('queue_id').in('queue_id', queueIds),
  ]);

  const waitingByQueue: Record<string, number> = {};
  (waitingRes.data ?? []).forEach((r) => {
    waitingByQueue[r.queue_id] = (waitingByQueue[r.queue_id] ?? 0) + 1;
  });

  const opsByQueue: Record<string, number> = {};
  (opsRes.data ?? []).forEach((r) => {
    opsByQueue[r.queue_id] = (opsByQueue[r.queue_id] ?? 0) + 1;
  });

  return queues.map((q) => ({
    id:                 q.id,
    name:               q.name,
    strategy:           q.distribution_strategy,
    is_active:          q.is_active,
    waiting_tickets:    waitingByQueue[q.id] ?? 0,
    assigned_operators: opsByQueue[q.id]     ?? 0,
  }));
}

export async function getOperatorMetrics(): Promise<OperatorMetric[]> {
  const { data: ops } = await supabase
    .from('operators')
    .select(`
      id, user_id, max_active_tickets,
      profile:profiles!operators_user_id_fkey(full_name, email),
      presence:operator_presence(status, last_seen),
      load:operator_ticket_load(active_tickets)
    `)
    .order('created_at', { ascending: true });

  return ((ops ?? []) as unknown[]).map((raw) => {
    const op      = raw as Record<string, unknown>;
    const profile = (Array.isArray(op.profile) ? op.profile[0] : op.profile) as { full_name?: string; email?: string } | null;
    const pres    = (Array.isArray(op.presence) ? op.presence[0] : op.presence) as { status?: string; last_seen?: string } | null;
    const load    = (Array.isArray(op.load)    ? op.load[0]    : op.load)    as { active_tickets?: number } | null;

    return {
      id:             op.id        as string,
      user_id:        op.user_id   as string,
      full_name:      profile?.full_name ?? '',
      email:          profile?.email     ?? '',
      status:         pres?.status       ?? 'offline',
      active_tickets: load?.active_tickets ?? 0,
      max_tickets:    (op.max_active_tickets as number) ?? 5,
      last_seen:      pres?.last_seen     ?? null,
    } as OperatorMetric;
  });
}

export async function getActiveTickets(): Promise<ActiveTicketRow[]> {
  const { data } = await supabase
    .from('tickets')
    .select(`
      id, subject, status, priority, created_at,
      customer:customers(name, email),
      assignee:operators(
        id, user_id,
        profile:profiles!operators_user_id_fkey(full_name, email)
      ),
      queue:queues(name)
    `)
    .in('status', ['open', 'in_progress'])
    .order('created_at', { ascending: false })
    .limit(100);

  return ((data ?? []) as unknown[]).map((raw) => {
    const t        = raw as Record<string, unknown>;
    const cust     = (Array.isArray(t.customer) ? t.customer[0] : t.customer) as { name?: string; email?: string } | null;
    const assignee = (Array.isArray(t.assignee) ? t.assignee[0] : t.assignee) as Record<string, unknown> | null;
    const aProfile = assignee
      ? (Array.isArray(assignee.profile) ? assignee.profile[0] : assignee.profile) as { full_name?: string; email?: string } | null
      : null;
    const queue    = (Array.isArray(t.queue) ? t.queue[0] : t.queue) as { name?: string } | null;

    return {
      id:             t.id          as string,
      subject:        (t.subject as string) ?? '',
      status:         t.status      as string,
      priority:       t.priority    as string,
      created_at:     t.created_at  as string,
      customer_name:  cust?.name    ?? '',
      customer_email: cust?.email   ?? '',
      operator_id:    assignee ? (assignee.id as string) : null,
      operator_name:  aProfile?.full_name ?? aProfile?.email ?? null,
      queue_name:     queue?.name   ?? null,
    } as ActiveTicketRow;
  });
}

export async function saveOperationSnapshot(metrics: OverviewMetrics): Promise<void> {
  await supabase.from('operation_metrics').insert({
    active_tickets:    metrics.active_tickets,
    queued_tickets:    metrics.queued_tickets,
    online_operators:  metrics.online_operators,
    busy_operators:    metrics.busy_operators,
    avg_response_time: metrics.avg_response_time_minutes,
  });
}
