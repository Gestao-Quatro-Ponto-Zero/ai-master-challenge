import { supabase } from '../lib/supabaseClient';

export interface SegmentRule {
  last_interaction_days?: number | null;
  min_messages?:          number | null;
  min_tickets?:           number | null;
  min_engagement_score?:  number | null;
  max_engagement_score?:  number | null;
  event_type?:            string | null;
  min_events?:            number | null;
}

export interface CustomerSegment {
  id:                string;
  segment_name:      string;
  description:       string;
  rules:             SegmentRule;
  is_dynamic:        boolean;
  is_active:         boolean;
  member_count:      number;
  last_refreshed_at: string | null;
  created_at:        string;
  updated_at:        string;
}

export interface SegmentMember {
  member_id:        string;
  customer_id:      string;
  customer_name:    string;
  customer_email:   string;
  engagement_score: number;
  total_tickets:    number;
  total_messages:   number;
  added_at:         string;
  total_count?:     number;
}

export interface CreateSegmentInput {
  segment_name: string;
  description?: string;
  rules:        SegmentRule;
  is_dynamic?:  boolean;
}

export interface UpdateSegmentInput {
  segment_name?: string;
  description?:  string;
  rules?:        SegmentRule;
  is_dynamic?:   boolean;
  is_active?:    boolean;
}

export async function getSegments(): Promise<CustomerSegment[]> {
  const { data, error } = await supabase.rpc('get_segments');
  if (error) throw new Error(error.message);
  return ((data ?? []) as CustomerSegment[]).map((s) => ({
    ...s,
    member_count: Number(s.member_count),
  }));
}

export async function createSegment(input: CreateSegmentInput): Promise<string> {
  const { data, error } = await supabase.rpc('create_segment', {
    p_name:        input.segment_name,
    p_description: input.description ?? '',
    p_rules:       input.rules as Record<string, unknown>,
    p_is_dynamic:  input.is_dynamic ?? true,
  });
  if (error) throw new Error(error.message);
  return data as string;
}

export async function updateSegment(id: string, input: UpdateSegmentInput): Promise<void> {
  const { error } = await supabase.rpc('update_segment', {
    p_id:          id,
    p_name:        input.segment_name  ?? null,
    p_description: input.description   ?? null,
    p_rules:       input.rules         ? (input.rules as Record<string, unknown>) : null,
    p_is_dynamic:  input.is_dynamic    ?? null,
    p_is_active:   input.is_active     ?? null,
  });
  if (error) throw new Error(error.message);
}

export async function getSegmentMembers(
  segmentId: string,
  limit  = 100,
  offset = 0,
): Promise<{ members: SegmentMember[]; totalCount: number }> {
  const { data, error } = await supabase.rpc('get_segment_members', {
    p_segment_id: segmentId,
    p_limit:      limit,
    p_offset:     offset,
  });
  if (error) throw new Error(error.message);
  const rows = (data ?? []) as SegmentMember[];
  const totalCount = rows.length > 0 ? Number(rows[0].total_count ?? rows.length) : 0;
  return {
    members: rows.map((m) => ({
      ...m,
      total_tickets:    Number(m.total_tickets),
      total_messages:   Number(m.total_messages),
      engagement_score: Number(m.engagement_score),
    })),
    totalCount,
  };
}

export async function refreshSegmentMembers(segmentId: string): Promise<number> {
  const { data, error } = await supabase.rpc('refresh_segment_members', {
    p_segment_id: segmentId,
  });
  if (error) throw new Error(error.message);
  return Number(data);
}

export async function refreshAllSegments(): Promise<number> {
  const { data, error } = await supabase.rpc('refresh_all_segments');
  if (error) throw new Error(error.message);
  return Number(data);
}

export function ruleLabel(key: keyof SegmentRule, value: unknown): string {
  const MAP: Record<keyof SegmentRule, (v: unknown) => string> = {
    last_interaction_days:  (v) => `Sem interação há ≥ ${v} dias`,
    min_messages:           (v) => `Mínimo de ${v} mensagens`,
    min_tickets:            (v) => `Mínimo de ${v} tickets`,
    min_engagement_score:   (v) => `Engajamento ≥ ${v}`,
    max_engagement_score:   (v) => `Engajamento ≤ ${v}`,
    event_type:             (v) => `Evento: ${v}`,
    min_events:             (v) => `Mínimo de ${v} eventos`,
  };
  return MAP[key]?.(value) ?? `${key}: ${value}`;
}

export const RULE_PRESETS: { label: string; rules: SegmentRule }[] = [
  {
    label: 'Clientes inativos (30 dias)',
    rules: { last_interaction_days: 30 },
  },
  {
    label: 'Clientes inativos (7 dias)',
    rules: { last_interaction_days: 7 },
  },
  {
    label: 'Alto engajamento',
    rules: { min_engagement_score: 70 },
  },
  {
    label: 'Baixo engajamento',
    rules: { max_engagement_score: 30 },
  },
  {
    label: 'Clientes com 5+ tickets',
    rules: { min_tickets: 5 },
  },
  {
    label: 'Clientes com 10+ mensagens',
    rules: { min_messages: 10 },
  },
  {
    label: 'Abriram campanha',
    rules: { event_type: 'campaign_opened' },
  },
  {
    label: 'Criados recentemente',
    rules: { min_messages: 1 },
  },
];
