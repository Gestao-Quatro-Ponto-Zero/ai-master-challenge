import { supabase } from '../lib/supabaseClient';

export type DistributionStrategy = 'round_robin' | 'least_loaded' | 'skill_based' | 'manual';

export interface AssignableOperator {
  id:           string;
  user_id:      string;
  status:       string;
  active_tickets: number;
  max_tickets:  number;
  skills:       string[];
}

export interface DistributionResult {
  processed: number;
  assigned:  number;
  skipped:   number;
  errors:    string[];
}

const BATCH_LIMIT = 10;

export async function triggerDistribution(queueId: string): Promise<DistributionResult> {
  const result: DistributionResult = { processed: 0, assigned: 0, skipped: 0, errors: [] };

  const { data: queue, error: qErr } = await supabase
    .from('queues')
    .select('id, distribution_strategy, is_active')
    .eq('id', queueId)
    .maybeSingle();

  if (qErr || !queue) {
    result.errors.push('Queue not found');
    return result;
  }

  if (!queue.is_active) {
    result.errors.push('Queue is inactive');
    return result;
  }

  const strategy = (queue.distribution_strategy ?? 'least_loaded') as DistributionStrategy;

  if (strategy === 'manual') return result;

  const [queueTickets, operators] = await Promise.all([
    getQueueTickets(queueId),
    getAvailableOperators(queueId),
  ]);

  if (operators.length === 0 || queueTickets.length === 0) return result;

  const batch = queueTickets.slice(0, BATCH_LIMIT);
  const mutableOps = operators.map((o) => ({ ...o }));

  for (const qt of batch) {
    result.processed++;

    let ticketSkills: string[] = [];
    if (strategy === 'skill_based') {
      ticketSkills = await detectTicketSkills(qt.ticket_id);
    }

    const operator = await selectOperator(queueId, mutableOps, strategy, ticketSkills);
    if (!operator) { result.skipped++; continue; }

    try {
      await assignTicketToOperator(qt.ticket_id, qt.id, operator);
      operator.active_tickets++;
      if (operator.active_tickets >= operator.max_tickets) {
        const idx = mutableOps.findIndex((o) => o.id === operator.id);
        if (idx !== -1) mutableOps.splice(idx, 1);
      }
      result.assigned++;
    } catch (err) {
      result.errors.push(err instanceof Error ? err.message : String(err));
      result.skipped++;
    }
  }

  return result;
}

async function getQueueTickets(queueId: string) {
  const { data, error } = await supabase
    .from('queue_tickets')
    .select('id, ticket_id, priority, position')
    .eq('queue_id', queueId)
    .order('priority', { ascending: false })
    .order('position', { ascending: true })
    .limit(BATCH_LIMIT);

  if (error) throw new Error(error.message);
  return (data ?? []) as { id: string; ticket_id: string; priority: number; position: number }[];
}

export async function getAvailableOperators(queueId: string): Promise<AssignableOperator[]> {
  const { data: queueOps, error: qoErr } = await supabase
    .from('queue_operators')
    .select('operator_id')
    .eq('queue_id', queueId);

  if (qoErr) throw new Error(qoErr.message);
  if (!queueOps || queueOps.length === 0) return [];

  const operatorIds = queueOps.map((o) => o.operator_id);

  const { data: operators, error: opErr } = await supabase
    .from('operators')
    .select(`
      id, user_id, status, max_active_tickets,
      load:operator_ticket_load(active_tickets, max_tickets),
      skills:operator_skills(skill_name)
    `)
    .in('id', operatorIds)
    .eq('status', 'online');

  if (opErr) throw new Error(opErr.message);

  return ((operators ?? []) as unknown[])
    .map((raw) => {
      const op = raw as Record<string, unknown>;
      const loadArr = op.load as { active_tickets: number; max_tickets: number }[] | null;
      const load = Array.isArray(loadArr) ? loadArr[0] : loadArr;
      const active = (load?.active_tickets as number) ?? 0;
      const max    = (load?.max_tickets   as number) ?? (op.max_active_tickets as number) ?? 5;
      const skillsArr = op.skills as { skill_name: string }[] | null;
      return {
        id:             op.id as string,
        user_id:        op.user_id as string,
        status:         op.status as string,
        active_tickets: active,
        max_tickets:    max,
        skills:         (skillsArr ?? []).map((s) => s.skill_name),
      } satisfies AssignableOperator;
    })
    .filter((op) => op.active_tickets < op.max_tickets);
}

async function detectTicketSkills(ticketId: string): Promise<string[]> {
  const { data } = await supabase
    .from('tickets')
    .select('subject, priority')
    .eq('id', ticketId)
    .maybeSingle();

  if (!data) return [];

  const text = (data.subject ?? '').toLowerCase();
  const known = ['billing', 'technical', 'sales', 'vip_support', 'onboarding', 'returns', 'shipping', 'compliance'];
  return known.filter((k) => text.includes(k.replace('_', ' ')) || text.includes(k));
}

async function selectOperator(
  queueId:     string,
  operators:   AssignableOperator[],
  strategy:    DistributionStrategy,
  ticketSkills: string[],
): Promise<AssignableOperator | null> {
  if (operators.length === 0) return null;

  if (strategy === 'skill_based' && ticketSkills.length > 0) {
    const skilled = operators.filter((op) =>
      ticketSkills.some((s) => op.skills.includes(s)),
    );
    const pool = skilled.length > 0 ? skilled : operators;
    return pool.sort((a, b) => a.active_tickets - b.active_tickets)[0] ?? null;
  }

  if (strategy === 'round_robin') {
    return selectRoundRobin(queueId, operators);
  }

  return operators.sort((a, b) => a.active_tickets - b.active_tickets)[0] ?? null;
}

async function selectRoundRobin(
  queueId:   string,
  operators: AssignableOperator[],
): Promise<AssignableOperator | null> {
  if (operators.length === 0) return null;

  const { data: state } = await supabase
    .from('queue_distribution_state')
    .select('last_operator_id')
    .eq('queue_id', queueId)
    .maybeSingle();

  const lastId = state?.last_operator_id ?? null;
  let idx = 0;
  if (lastId) {
    const lastIdx = operators.findIndex((o) => o.id === lastId);
    if (lastIdx !== -1) idx = (lastIdx + 1) % operators.length;
  }

  const selected = operators[idx];
  if (!selected) return null;

  await supabase
    .from('queue_distribution_state')
    .upsert({ queue_id: queueId, last_operator_id: selected.id, updated_at: new Date().toISOString() },
      { onConflict: 'queue_id' });

  return selected;
}

async function assignTicketToOperator(
  ticketId:     string,
  queueTicketId: string,
  operator:     AssignableOperator,
): Promise<void> {
  const { error: ticketErr } = await supabase
    .from('tickets')
    .update({ assigned_user_id: operator.user_id, updated_at: new Date().toISOString() })
    .eq('id', ticketId);

  if (ticketErr) throw new Error(ticketErr.message);

  const { error: queueErr } = await supabase
    .from('queue_tickets')
    .delete()
    .eq('id', queueTicketId);

  if (queueErr) throw new Error(queueErr.message);

  await incrementOperatorLoad(operator.id);
}

async function incrementOperatorLoad(operatorId: string): Promise<void> {
  const { data: load } = await supabase
    .from('operator_ticket_load')
    .select('active_tickets')
    .eq('operator_id', operatorId)
    .maybeSingle();

  const current = (load?.active_tickets as number) ?? 0;

  await supabase
    .from('operator_ticket_load')
    .upsert(
      { operator_id: operatorId, active_tickets: current + 1, updated_at: new Date().toISOString() },
      { onConflict: 'operator_id' },
    );
}

export async function decrementOperatorLoad(operatorId: string): Promise<void> {
  const { data: load } = await supabase
    .from('operator_ticket_load')
    .select('active_tickets')
    .eq('operator_id', operatorId)
    .maybeSingle();

  const current = (load?.active_tickets as number) ?? 0;

  await supabase
    .from('operator_ticket_load')
    .upsert(
      { operator_id: operatorId, active_tickets: Math.max(0, current - 1), updated_at: new Date().toISOString() },
      { onConflict: 'operator_id' },
    );
}

export async function manualAssign(
  ticketId:   string,
  operatorId: string,
  assignedBy: string,
): Promise<void> {
  const { data: operator, error: opErr } = await supabase
    .from('operators')
    .select('id, user_id')
    .eq('id', operatorId)
    .maybeSingle();

  if (opErr || !operator) throw new Error('Operator not found');

  const { error: ticketErr } = await supabase
    .from('tickets')
    .update({ assigned_user_id: operator.user_id, updated_at: new Date().toISOString() })
    .eq('id', ticketId);

  if (ticketErr) throw new Error(ticketErr.message);

  const { data: qt } = await supabase
    .from('queue_tickets')
    .select('id')
    .eq('ticket_id', ticketId)
    .maybeSingle();

  if (qt) {
    await supabase.from('queue_tickets').delete().eq('id', qt.id);
  }

  await incrementOperatorLoad(operatorId);

  await supabase.from('audit_logs').insert({
    user_id:     assignedBy,
    action:      'ticket.assign',
    resource:    'tickets',
    resource_id: ticketId,
    meta:        { assigned_to_operator: operatorId, method: 'manual' },
  });
}

export async function getSupervisorSnapshot() {
  const [
    { data: queues },
    { data: operators },
    { data: queueTickets },
  ] = await Promise.all([
    supabase.from('queues').select('id, name, is_active, distribution_strategy, priority').eq('is_active', true).order('priority', { ascending: false }),
    supabase.from('operators').select(`
      id, user_id, status, max_active_tickets,
      load:operator_ticket_load(active_tickets),
      profile:profiles!operators_user_id_fkey(full_name, email)
    `).order('created_at'),
    supabase.from('queue_tickets').select('queue_id').order('queue_id'),
  ]);

  const waitingByQueue: Record<string, number> = {};
  (queueTickets ?? []).forEach((qt) => {
    waitingByQueue[qt.queue_id] = (waitingByQueue[qt.queue_id] ?? 0) + 1;
  });

  const onlineCount  = (operators ?? []).filter((o) => o.status === 'online').length;
  const totalWaiting = Object.values(waitingByQueue).reduce((s, v) => s + v, 0);

  return {
    queues: (queues ?? []).map((q) => ({
      ...q,
      tickets_waiting: waitingByQueue[q.id] ?? 0,
    })),
    operators: (operators ?? []).map((op) => {
      const loadArr = op.load as { active_tickets: number }[] | null;
      const load = Array.isArray(loadArr) ? loadArr[0] : loadArr;
      const profileArr = op.profile as { full_name: string; email: string }[] | null;
      const profile = Array.isArray(profileArr) ? profileArr[0] : profileArr;
      return {
        id:             op.id,
        user_id:        op.user_id,
        status:         op.status as string,
        max_active_tickets: op.max_active_tickets as number,
        active_tickets: (load?.active_tickets ?? 0) as number,
        full_name:      profile?.full_name ?? '',
        email:          profile?.email     ?? '',
      };
    }),
    stats: {
      total_queues:   (queues ?? []).length,
      online_operators: onlineCount,
      tickets_waiting: totalWaiting,
    },
  };
}
