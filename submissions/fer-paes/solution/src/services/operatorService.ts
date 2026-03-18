import { supabase } from '../lib/supabaseClient';

export type OperatorStatusValue = 'offline' | 'online' | 'busy' | 'away';
export const SKILL_LEVELS = [
  { value: 1, label: 'Basic'        },
  { value: 2, label: 'Intermediate' },
  { value: 3, label: 'Specialist'   },
] as const;

export const PRESET_SKILLS = [
  'billing', 'technical', 'sales', 'vip_support', 'onboarding',
  'returns', 'shipping', 'compliance',
];

export interface OperatorSkill {
  id:          string;
  operator_id: string;
  skill_name:  string;
  skill_level: 1 | 2 | 3;
  created_at:  string;
}

export interface OperatorTicketLoad {
  operator_id:    string;
  active_tickets: number;
  max_tickets:    number;
  updated_at:     string;
}

export interface OperatorRow {
  id:                  string;
  user_id:             string;
  status:              OperatorStatusValue;
  max_active_tickets:  number;
  created_at:          string;
  updated_at:          string;
  profile?:            { full_name: string; email: string; avatar_url: string | null; status: string };
  presence?:           { status: OperatorStatusValue; last_seen: string } | null;
  skills?:             OperatorSkill[];
  load?:               OperatorTicketLoad | null;
}

export interface CreateOperatorInput {
  user_id:            string;
  max_active_tickets: number;
  skills?:            { skill_name: string; skill_level: 1 | 2 | 3 }[];
}

export async function listOperators(): Promise<OperatorRow[]> {
  const { data: ops, error } = await supabase
    .from('operators')
    .select(`
      *,
      profile:profiles!operators_user_id_fkey(full_name, email, avatar_url, status),
      skills:operator_skills(*),
      load:operator_ticket_load(*)
    `)
    .order('created_at', { ascending: true });

  if (error) throw new Error(error.message);

  const rows = (ops ?? []) as OperatorRow[];

  const userIds = rows.map((r) => r.user_id);
  if (userIds.length === 0) return rows;

  const { data: presenceData } = await supabase
    .from('operator_presence')
    .select('user_id, status, last_seen')
    .in('user_id', userIds);

  const presenceMap = Object.fromEntries(
    (presenceData ?? []).map((p) => [p.user_id, p]),
  );

  return rows.map((r) => ({
    ...r,
    presence: presenceMap[r.user_id] ?? null,
  }));
}

export async function getOperator(id: string): Promise<OperatorRow | null> {
  const { data, error } = await supabase
    .from('operators')
    .select(`
      *,
      profile:profiles!operators_user_id_fkey(full_name, email, avatar_url, status),
      skills:operator_skills(*),
      load:operator_ticket_load(*)
    `)
    .eq('id', id)
    .maybeSingle();

  if (error) throw new Error(error.message);
  if (!data) return null;

  const { data: presence } = await supabase
    .from('operator_presence')
    .select('user_id, status, last_seen')
    .eq('user_id', data.user_id)
    .maybeSingle();

  return { ...data, presence } as OperatorRow;
}

export async function createOperator(input: CreateOperatorInput): Promise<OperatorRow> {
  const { data: op, error: opErr } = await supabase
    .from('operators')
    .insert({
      user_id:            input.user_id,
      max_active_tickets: input.max_active_tickets,
      status:             'offline',
    })
    .select()
    .single();

  if (opErr) throw new Error(opErr.message);

  await supabase.from('operator_ticket_load').insert({
    operator_id:    op.id,
    active_tickets: 0,
    max_tickets:    input.max_active_tickets,
  });

  if (input.skills?.length) {
    await supabase.from('operator_skills').insert(
      input.skills.map((s) => ({ operator_id: op.id, ...s })),
    );
  }

  await supabase.from('operator_presence').upsert(
    { user_id: input.user_id, status: 'offline', last_seen: new Date().toISOString() },
    { onConflict: 'user_id' },
  );

  return op as OperatorRow;
}

export async function updateOperatorStatus(
  operatorId: string,
  userId: string,
  status: OperatorStatusValue,
): Promise<void> {
  const now = new Date().toISOString();

  const { error: opErr } = await supabase
    .from('operators')
    .update({ status, updated_at: now })
    .eq('id', operatorId);

  if (opErr) throw new Error(opErr.message);

  await supabase.from('operator_presence').upsert(
    { user_id: userId, status, last_seen: now, updated_at: now },
    { onConflict: 'user_id' },
  );
}

export async function updateOperatorCapacity(
  operatorId: string,
  maxActiveTickets: number,
): Promise<void> {
  const now = new Date().toISOString();

  const { error } = await supabase
    .from('operators')
    .update({ max_active_tickets: maxActiveTickets, updated_at: now })
    .eq('id', operatorId);

  if (error) throw new Error(error.message);

  await supabase
    .from('operator_ticket_load')
    .update({ max_tickets: maxActiveTickets, updated_at: now })
    .eq('operator_id', operatorId);
}

export async function replaceOperatorSkills(
  operatorId: string,
  skills: { skill_name: string; skill_level: 1 | 2 | 3 }[],
): Promise<OperatorSkill[]> {
  const { error: delErr } = await supabase
    .from('operator_skills')
    .delete()
    .eq('operator_id', operatorId);

  if (delErr) throw new Error(delErr.message);

  if (skills.length === 0) return [];

  const { data, error: insErr } = await supabase
    .from('operator_skills')
    .insert(skills.map((s) => ({ operator_id: operatorId, ...s })))
    .select();

  if (insErr) throw new Error(insErr.message);

  return (data ?? []) as OperatorSkill[];
}

export async function deleteOperator(operatorId: string): Promise<void> {
  const { error } = await supabase
    .from('operators')
    .delete()
    .eq('id', operatorId);

  if (error) throw new Error(error.message);
}

export async function getOperatorLoad(operatorId: string): Promise<OperatorTicketLoad | null> {
  const { data, error } = await supabase
    .from('operator_ticket_load')
    .select('*')
    .eq('operator_id', operatorId)
    .maybeSingle();

  if (error) throw new Error(error.message);
  return data as OperatorTicketLoad | null;
}

export async function listUsersWithoutOperator(): Promise<
  { id: string; full_name: string; email: string }[]
> {
  const { data: existingOps } = await supabase
    .from('operators')
    .select('user_id');

  const takenIds = (existingOps ?? []).map((o) => o.user_id);

  let query = supabase
    .from('profiles')
    .select('id, full_name, email')
    .eq('status', 'active')
    .order('full_name');

  if (takenIds.length > 0) {
    query = query.not('id', 'in', `(${takenIds.join(',')})`);
  }

  const { data, error } = await query;
  if (error) throw new Error(error.message);
  return (data ?? []) as { id: string; full_name: string; email: string }[];
}
