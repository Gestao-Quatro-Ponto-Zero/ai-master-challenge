import { supabase } from '../lib/supabaseClient';
import type { SLAPolicy, TicketSLA, TicketPriority } from '../types';

export async function getSLAPolicyByPriority(priority: TicketPriority): Promise<SLAPolicy | null> {
  const { data, error } = await supabase
    .from('sla_policies')
    .select('*')
    .eq('priority', priority)
    .eq('is_active', true)
    .maybeSingle();

  if (error) throw new Error(error.message);
  return data as SLAPolicy | null;
}

export async function applySLA(
  ticketId: string,
  priority: TicketPriority,
  createdAt: string,
): Promise<TicketSLA | null> {
  const policy = await getSLAPolicyByPriority(priority);
  if (!policy) return null;

  const base = new Date(createdAt).getTime();
  const firstResponseDeadline = new Date(base + policy.first_response_minutes * 60_000).toISOString();
  const resolutionDeadline = new Date(base + policy.resolution_minutes * 60_000).toISOString();

  const { data, error } = await supabase
    .from('ticket_sla')
    .insert({
      ticket_id: ticketId,
      sla_policy_id: policy.id,
      first_response_deadline: firstResponseDeadline,
      resolution_deadline: resolutionDeadline,
    })
    .select()
    .single();

  if (error) {
    if (error.code === '23505') return getTicketSLA(ticketId);
    throw new Error(error.message);
  }

  return data as TicketSLA;
}

export async function getTicketSLA(ticketId: string): Promise<TicketSLA | null> {
  const { data, error } = await supabase
    .from('ticket_sla')
    .select('*')
    .eq('ticket_id', ticketId)
    .maybeSingle();

  if (error) throw new Error(error.message);
  return data as TicketSLA | null;
}

export async function markFirstResponse(ticketId: string): Promise<void> {
  const sla = await getTicketSLA(ticketId);
  if (!sla || sla.first_response_at) return;

  const now = new Date().toISOString();
  const isBreached = now > sla.first_response_deadline;

  await supabase
    .from('ticket_sla')
    .update({
      first_response_at: now,
      status: isBreached ? 'breached' : sla.status,
    })
    .eq('ticket_id', ticketId);
}

export async function markResolved(ticketId: string): Promise<void> {
  const sla = await getTicketSLA(ticketId);
  if (!sla || sla.resolved_at) return;

  const now = new Date().toISOString();
  const isBreached = now > sla.resolution_deadline;

  await supabase
    .from('ticket_sla')
    .update({
      resolved_at: now,
      status: isBreached ? 'breached' : sla.status,
    })
    .eq('ticket_id', ticketId);
}

export async function checkAndUpdateSLABreach(ticketId: string): Promise<void> {
  const sla = await getTicketSLA(ticketId);
  if (!sla || sla.status === 'breached') return;

  const now = new Date().toISOString();
  const firstResponseBreached = !sla.first_response_at && now > sla.first_response_deadline;
  const resolutionBreached = !sla.resolved_at && now > sla.resolution_deadline;

  if (firstResponseBreached || resolutionBreached) {
    await supabase
      .from('ticket_sla')
      .update({ status: 'breached' })
      .eq('ticket_id', ticketId);
  }
}

export interface SLACountdown {
  label: string;
  deadline: string;
  isBreached: boolean;
  minutesRemaining: number;
  isFirstResponse: boolean;
}

export function computeSLACountdown(sla: TicketSLA): SLACountdown {
  const now = Date.now();

  if (!sla.first_response_at) {
    const deadline = sla.first_response_deadline;
    const ms = new Date(deadline).getTime() - now;
    return {
      label: 'First response',
      deadline,
      isBreached: ms < 0,
      minutesRemaining: Math.floor(ms / 60_000),
      isFirstResponse: true,
    };
  }

  const deadline = sla.resolution_deadline;
  const ms = new Date(deadline).getTime() - now;
  return {
    label: 'Resolution',
    deadline,
    isBreached: ms < 0,
    minutesRemaining: Math.floor(ms / 60_000),
    isFirstResponse: false,
  };
}

export function formatSLATime(minutesRemaining: number): string {
  if (minutesRemaining <= 0) return 'Breached';
  if (minutesRemaining < 60) return `${minutesRemaining}m`;
  const hrs = Math.floor(minutesRemaining / 60);
  const mins = minutesRemaining % 60;
  if (mins === 0) return `${hrs}h`;
  return `${hrs}h ${mins}m`;
}
