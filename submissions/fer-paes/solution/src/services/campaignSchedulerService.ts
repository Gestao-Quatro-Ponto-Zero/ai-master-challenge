import { supabase } from '../lib/supabaseClient';

export type ScheduleType = 'once' | 'recurring' | 'event_triggered';

export interface CampaignSchedule {
  id:               string;
  campaign_id:      string;
  campaign_name:    string;
  campaign_status:  string;
  campaign_channel: string;
  schedule_type:    ScheduleType;
  run_at:           string | null;
  cron_expression:  string | null;
  event_type:       string | null;
  next_run_at:      string | null;
  last_run_at:      string | null;
  is_active:        boolean;
  execution_count:  number;
  created_at:       string;
  updated_at:       string;
}

export interface CreateScheduleInput {
  campaign_id:      string;
  schedule_type:    ScheduleType;
  run_at?:          string | null;
  cron_expression?: string | null;
  event_type?:      string | null;
  next_run_at?:     string | null;
}

export async function getSchedules(): Promise<CampaignSchedule[]> {
  const { data, error } = await supabase.rpc('get_schedules');
  if (error) throw new Error(error.message);
  return ((data ?? []) as CampaignSchedule[]).map((s) => ({
    ...s,
    execution_count: Number(s.execution_count),
  }));
}

export async function getScheduleById(id: string): Promise<CampaignSchedule | null> {
  const { data, error } = await supabase.rpc('get_schedule_by_id', { p_id: id });
  if (error) throw new Error(error.message);
  const rows = data as CampaignSchedule[];
  if (!rows || rows.length === 0) return null;
  return { ...rows[0], execution_count: Number(rows[0].execution_count) };
}

export async function createSchedule(input: CreateScheduleInput): Promise<string> {
  const { data, error } = await supabase.rpc('create_schedule', {
    p_campaign_id:     input.campaign_id,
    p_schedule_type:   input.schedule_type,
    p_run_at:          input.run_at          ?? null,
    p_cron_expression: input.cron_expression ?? null,
    p_event_type:      input.event_type      ?? null,
    p_next_run_at:     input.next_run_at     ?? null,
  });
  if (error) throw new Error(error.message);
  return data as string;
}

export async function updateSchedule(
  id: string,
  input: {
    run_at?:          string | null;
    cron_expression?: string | null;
    event_type?:      string | null;
    next_run_at?:     string | null;
  },
): Promise<void> {
  const { error } = await supabase.rpc('update_schedule', {
    p_id:              id,
    p_run_at:          input.run_at          ?? null,
    p_cron_expression: input.cron_expression ?? null,
    p_event_type:      input.event_type      ?? null,
    p_next_run_at:     input.next_run_at     ?? null,
  });
  if (error) throw new Error(error.message);
}

export async function disableSchedule(id: string): Promise<void> {
  const { error } = await supabase.rpc('disable_schedule', { p_id: id });
  if (error) throw new Error(error.message);
}

export async function enableSchedule(id: string): Promise<void> {
  const { error } = await supabase.rpc('enable_schedule', { p_id: id });
  if (error) throw new Error(error.message);
}

export async function deleteSchedule(id: string): Promise<void> {
  const { error } = await supabase.rpc('delete_schedule', { p_id: id });
  if (error) throw new Error(error.message);
}

export async function getDueSchedules(): Promise<CampaignSchedule[]> {
  const { data, error } = await supabase.rpc('get_due_schedules');
  if (error) throw new Error(error.message);
  return ((data ?? []) as CampaignSchedule[]).map((s) => ({
    ...s,
    execution_count: Number(s.execution_count),
  }));
}

export async function markScheduleExecuted(id: string, nextRunAt?: string | null): Promise<void> {
  const { error } = await supabase.rpc('mark_schedule_executed', {
    p_id:          id,
    p_next_run_at: nextRunAt ?? null,
  });
  if (error) throw new Error(error.message);
}

export const SCHEDULE_TYPE_META: Record<ScheduleType, { label: string; description: string; color: string; bg: string; border: string }> = {
  once:            { label: 'Envio Único',    description: 'Executa uma vez na data/hora definida', color: 'text-blue-600',   bg: 'bg-blue-50',   border: 'border-blue-100' },
  recurring:       { label: 'Recorrente',     description: 'Executa repetidamente via expressão cron', color: 'text-violet-600', bg: 'bg-violet-50', border: 'border-violet-100' },
  event_triggered: { label: 'Por Evento',     description: 'Executa quando um evento específico ocorre', color: 'text-amber-600',  bg: 'bg-amber-50',  border: 'border-amber-100' },
};

export const EVENT_TYPES = [
  { value: 'ticket_resolved',    label: 'Ticket resolvido' },
  { value: 'ticket_created',     label: 'Ticket criado' },
  { value: 'message_sent',       label: 'Mensagem enviada' },
  { value: 'customer_created',   label: 'Cliente criado' },
  { value: 'customer_inactive',  label: 'Cliente inativo (30 dias)' },
];

export const CRON_PRESETS = [
  { label: 'Todo dia às 09:00',       value: '0 9 * * *' },
  { label: 'Toda segunda às 09:00',   value: '0 9 * * 1' },
  { label: 'Toda sexta às 17:00',     value: '0 17 * * 5' },
  { label: 'Todo dia 1 do mês',       value: '0 9 1 * *' },
  { label: 'A cada hora',             value: '0 * * * *' },
];

export function parseCronHuman(cron: string): string {
  const preset = CRON_PRESETS.find((p) => p.value === cron);
  if (preset) return preset.label;
  return cron;
}
