import { supabase } from '../lib/supabaseClient';

export const EVENT_TYPES = [
  'customer_created',
  'message_sent',
  'ticket_created',
  'ticket_assigned',
  'ticket_resolved',
  'ticket_escalated',
  'conversation_started',
  'campaign_sent',
  'campaign_opened',
  'campaign_clicked',
] as const;

export type EventType = (typeof EVENT_TYPES)[number] | string;

export const EVENT_SOURCES = ['system', 'agent', 'campaign_engine', 'integration', 'manual'] as const;
export type EventSource = (typeof EVENT_SOURCES)[number] | string;

export interface CustomerEvent {
  id:             string;
  customer_id:    string | null;
  customer_name:  string | null;
  customer_email: string | null;
  event_type:     string;
  event_data:     Record<string, unknown>;
  source:         string;
  created_at:     string;
  total_count?:   number;
}

export interface EventFilters {
  search?:      string;
  customerId?:  string | null;
  eventType?:   string | null;
  source?:      string | null;
  dateFrom?:    string | null;
  dateTo?:      string | null;
  limit?:       number;
  offset?:      number;
}

export interface EventTypeSummary {
  event_type: string;
  count:      number;
  last_seen:  string;
}

export async function getEventsPaginated(filters: EventFilters = {}): Promise<{
  events:      CustomerEvent[];
  totalCount:  number;
}> {
  const { data, error } = await supabase.rpc('get_events_paginated', {
    p_search:      filters.search      ?? '',
    p_customer_id: filters.customerId  ?? null,
    p_event_type:  filters.eventType   ?? null,
    p_source:      filters.source      ?? null,
    p_date_from:   filters.dateFrom    ?? null,
    p_date_to:     filters.dateTo      ?? null,
    p_limit:       filters.limit       ?? 50,
    p_offset:      filters.offset      ?? 0,
  });
  if (error) throw new Error(error.message);
  const rows = (data ?? []) as CustomerEvent[];
  const totalCount = rows.length > 0 ? Number(rows[0].total_count ?? rows.length) : 0;
  return { events: rows, totalCount };
}

export async function getCustomerEvents(
  customerId: string,
  limit  = 100,
  offset = 0,
): Promise<CustomerEvent[]> {
  const { data, error } = await supabase.rpc('get_customer_events', {
    p_customer_id: customerId,
    p_limit:       limit,
    p_offset:      offset,
  });
  if (error) throw new Error(error.message);
  return (data ?? []) as CustomerEvent[];
}

export async function getEventsByType(
  eventType: string,
  limit  = 100,
  offset = 0,
): Promise<CustomerEvent[]> {
  const { data, error } = await supabase.rpc('get_events_by_type', {
    p_event_type: eventType,
    p_limit:      limit,
    p_offset:     offset,
  });
  if (error) throw new Error(error.message);
  return (data ?? []) as CustomerEvent[];
}

export async function getEventTypeSummary(): Promise<EventTypeSummary[]> {
  const { data, error } = await supabase.rpc('get_event_type_summary');
  if (error) throw new Error(error.message);
  return ((data ?? []) as EventTypeSummary[]).map((r) => ({
    ...r,
    count: Number(r.count),
  }));
}

export async function trackEvent(
  customerId: string | null,
  eventType:  string,
  eventData:  Record<string, unknown> = {},
  source:     string = 'system',
): Promise<string> {
  const { data, error } = await supabase.rpc('track_event', {
    p_customer_id: customerId,
    p_event_type:  eventType,
    p_event_data:  eventData,
    p_source:      source,
  });
  if (error) throw new Error(error.message);
  return data as string;
}

export function eventTypeLabel(type: string): string {
  const MAP: Record<string, string> = {
    customer_created:   'Cliente Criado',
    message_sent:       'Mensagem Enviada',
    ticket_created:     'Ticket Criado',
    ticket_assigned:    'Ticket Atribuído',
    ticket_resolved:    'Ticket Resolvido',
    ticket_escalated:   'Ticket Escalado',
    conversation_started: 'Conversa Iniciada',
    campaign_sent:      'Campanha Enviada',
    campaign_opened:    'Campanha Aberta',
    campaign_clicked:   'Campanha Clicada',
  };
  return MAP[type] ?? type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function eventTypeColor(type: string): { bg: string; text: string; border: string } {
  if (type.startsWith('ticket'))      return { bg: 'bg-blue-50',    text: 'text-blue-700',    border: 'border-blue-100'    };
  if (type.startsWith('message'))     return { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-100' };
  if (type.startsWith('campaign'))    return { bg: 'bg-amber-50',   text: 'text-amber-700',   border: 'border-amber-100'   };
  if (type.startsWith('customer'))    return { bg: 'bg-sky-50',     text: 'text-sky-700',     border: 'border-sky-100'     };
  if (type.startsWith('conversation'))return { bg: 'bg-violet-50',  text: 'text-violet-700',  border: 'border-violet-100'  };
  return                                     { bg: 'bg-gray-50',    text: 'text-gray-600',    border: 'border-gray-100'    };
}

export function sourceLabel(source: string): string {
  const MAP: Record<string, string> = {
    system:          'Sistema',
    agent:           'Agente',
    campaign_engine: 'Campanha',
    integration:     'Integração',
    manual:          'Manual',
  };
  return MAP[source] ?? source;
}

export function formatEventDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString('pt-BR', {
    day:    '2-digit',
    month:  '2-digit',
    year:   'numeric',
    hour:   '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}
