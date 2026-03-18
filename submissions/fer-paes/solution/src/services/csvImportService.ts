import Papa from 'papaparse';
import { supabase } from '../lib/supabaseClient';

export interface CsvImportProgress {
  total: number;
  processed: number;
  inserted: number;
  updated: number;
  errors: number;
  errorDetails: string[];
  phase: 'idle' | 'parsing' | 'importing' | 'done' | 'error';
}

export type ProgressCallback = (progress: CsvImportProgress) => void;

export const REQUIRED_COLUMNS = [
  'Ticket ID',
  'Customer Name',
  'Customer Email',
  'Ticket Subject',
  'Ticket Status',
  'Ticket Priority',
  'Ticket Channel',
];

interface CsvRow {
  'Ticket ID': string;
  'Customer Name': string;
  'Customer Email': string;
  'Customer Age'?: string;
  'Customer Gender'?: string;
  'Product Purchased'?: string;
  'Date of Purchase'?: string;
  'Ticket Type'?: string;
  'Ticket Subject': string;
  'Ticket Description'?: string;
  'Ticket Status': string;
  'Resolution'?: string;
  'Ticket Priority': string;
  'Ticket Channel': string;
  'First Response Time'?: string;
  'Time to Resolution'?: string;
  'Customer Satisfaction Rating'?: string;
}

const STATUS_MAP: Record<string, string> = {
  open: 'open',
  closed: 'closed',
  resolved: 'closed',
  pending: 'pending',
  'pending customer': 'pending',
  'in progress': 'open',
  'in-progress': 'open',
};

const PRIORITY_MAP: Record<string, string> = {
  low: 'low',
  medium: 'medium',
  high: 'high',
  critical: 'urgent',
  urgent: 'urgent',
};

function normalizeStatus(raw: string): string {
  return STATUS_MAP[raw?.trim().toLowerCase()] ?? 'open';
}

function normalizePriority(raw: string): string {
  return PRIORITY_MAP[raw?.trim().toLowerCase()] ?? 'medium';
}

function parseDurationToMinutes(raw: string | undefined): number | null {
  if (!raw || raw.trim() === '') return null;
  const s = raw.trim();
  let total = 0;
  const dayMatch = s.match(/(\d+)\s*day/);
  if (dayMatch) total += parseInt(dayMatch[1]) * 1440;
  const timeMatch = s.match(/(\d+):(\d+)(?::(\d+))?/);
  if (timeMatch) {
    total += parseInt(timeMatch[1]) * 60;
    total += parseInt(timeMatch[2]);
  }
  return total > 0 ? total : null;
}

function parseDateSafe(raw: string | undefined): string | null {
  if (!raw || raw.trim() === '') return null;
  try {
    const d = new Date(raw.trim());
    if (isNaN(d.getTime())) return null;
    return d.toISOString();
  } catch {
    return null;
  }
}

function parseSatisfaction(raw: string | undefined): number | null {
  if (!raw || raw.trim() === '') return null;
  const n = parseFloat(raw.trim());
  if (isNaN(n) || n < 1 || n > 5) return null;
  return Math.round(n);
}

function parseAge(raw: string | undefined): number | null {
  if (!raw || raw.trim() === '') return null;
  const n = parseInt(raw.trim());
  return isNaN(n) ? null : n;
}

async function fetchChannelMap(): Promise<Map<string, string>> {
  const { data } = await supabase.from('channels').select('id, name, type');
  const map = new Map<string, string>();
  if (data) {
    for (const ch of data) {
      map.set(ch.name.toLowerCase(), ch.id);
      map.set(ch.type.toLowerCase(), ch.id);
    }
  }
  map.set('email', map.get('email') ?? '');
  map.set('chat', map.get('chat') ?? '');
  map.set('phone', map.get('phone') ?? map.get('api') ?? '');
  map.set('social media', map.get('social media') ?? map.get('api') ?? '');
  map.set('api', map.get('api') ?? '');
  return map;
}

async function upsertCustomerBatch(
  rows: CsvRow[],
): Promise<Map<string, string>> {
  const emailToId = new Map<string, string>();
  const unique = new Map<string, CsvRow>();
  for (const r of rows) {
    const email = r['Customer Email']?.trim().toLowerCase();
    if (email) unique.set(email, r);
  }

  const payload = Array.from(unique.entries()).map(([email, r]) => ({
    email,
    name: r['Customer Name']?.trim() || null,
    age: parseAge(r['Customer Age']),
    gender: r['Customer Gender']?.trim() || null,
    external_source: 'csv_import',
  }));

  if (payload.length === 0) return emailToId;

  const { data, error } = await supabase
    .from('customers')
    .upsert(payload, { onConflict: 'email', ignoreDuplicates: false })
    .select('id, email');

  if (error) throw new Error(`Customer upsert failed: ${error.message}`);
  if (data) {
    for (const c of data) emailToId.set(c.email.toLowerCase(), c.id);
  }
  return emailToId;
}

interface TicketRow {
  external_id: string;
  customer_id: string | null;
  channel_id: string | null;
  subject: string;
  description: string | null;
  status: string;
  priority: string;
  ticket_type: string | null;
  product_purchased: string | null;
  date_of_purchase: string | null;
  resolution_text: string | null;
  first_response_time_minutes: number | null;
  time_to_resolution_minutes: number | null;
  customer_satisfaction_rating: number | null;
  source: string;
}

async function upsertTicketBatch(
  rows: CsvRow[],
  emailToId: Map<string, string>,
  channelMap: Map<string, string>,
): Promise<{ inserted: number; updated: number; errors: string[] }> {
  const errors: string[] = [];
  const payload: TicketRow[] = [];
  const externalIds: string[] = [];
  const descriptionMap = new Map<string, { description: string | null; resolution: string | null; customerId: string | null }>();

  for (const r of rows) {
    const externalId = r['Ticket ID']?.trim();
    if (!externalId) { errors.push(`Row skipped: missing Ticket ID`); continue; }

    const email = r['Customer Email']?.trim().toLowerCase();
    const customerId = emailToId.get(email ?? '') ?? null;

    const channelRaw = r['Ticket Channel']?.trim().toLowerCase();
    const channelId = channelMap.get(channelRaw) || null;

    const description = r['Ticket Description']?.trim() || null;
    const resolution = r['Resolution']?.trim() || null;

    externalIds.push(externalId);
    descriptionMap.set(externalId, { description, resolution, customerId });

    payload.push({
      external_id: externalId,
      customer_id: customerId,
      channel_id: channelId,
      subject: r['Ticket Subject']?.trim() || '(sem assunto)',
      description,
      status: normalizeStatus(r['Ticket Status']),
      priority: normalizePriority(r['Ticket Priority']),
      ticket_type: r['Ticket Type']?.trim() || null,
      product_purchased: r['Product Purchased']?.trim() || null,
      date_of_purchase: parseDateSafe(r['Date of Purchase']),
      resolution_text: resolution,
      first_response_time_minutes: parseDurationToMinutes(r['First Response Time']),
      time_to_resolution_minutes: parseDurationToMinutes(r['Time to Resolution']),
      customer_satisfaction_rating: parseSatisfaction(r['Customer Satisfaction Rating']),
      source: 'csv_import',
    });
  }

  if (payload.length === 0) return { inserted: 0, updated: 0, errors };

  const existingResult = await supabase
    .from('tickets')
    .select('id, external_id')
    .in('external_id', externalIds);

  const existingSet = new Set((existingResult.data ?? []).map((t) => t.external_id));

  const { error } = await supabase
    .from('tickets')
    .upsert(payload, { onConflict: 'external_id', ignoreDuplicates: false });

  if (error) throw new Error(`Ticket upsert failed: ${error.message}`);

  const newRows = payload.filter((p) => !existingSet.has(p.external_id));
  const inserted = newRows.length;
  const updated = payload.length - inserted;

  if (newRows.length > 0) {
    const newExternalIds = newRows.map((p) => p.external_id);
    const { data: ticketData } = await supabase
      .from('tickets')
      .select('id, external_id, customer_id')
      .in('external_id', newExternalIds);

    if (ticketData && ticketData.length > 0) {
      const conversationPayload = ticketData.map((t) => ({
        ticket_id: t.id,
        started_at: new Date().toISOString(),
      }));

      const { data: convData } = await supabase
        .from('conversations')
        .insert(conversationPayload)
        .select('id, ticket_id');

      if (convData && convData.length > 0) {
        const ticketIdToExt = new Map(ticketData.map((t) => [t.id, t.external_id]));
        const ticketIdToCustomer = new Map(ticketData.map((t) => [t.id, t.customer_id]));
        const messages: object[] = [];

        for (const conv of convData) {
          const extId = ticketIdToExt.get(conv.ticket_id);
          if (!extId) continue;
          const meta = descriptionMap.get(extId);
          if (!meta) continue;

          if (meta.description) {
            messages.push({
              conversation_id: conv.id,
              sender_type: 'customer',
              sender_id: ticketIdToCustomer.get(conv.ticket_id) ?? null,
              message: meta.description,
              message_type: 'text',
            });
          }

          if (meta.resolution) {
            messages.push({
              conversation_id: conv.id,
              sender_type: 'operator',
              sender_id: null,
              message: meta.resolution,
              message_type: 'text',
            });
          }
        }

        if (messages.length > 0) {
          await supabase.from('messages').insert(messages);
        }
      }
    }
  }

  return { inserted, updated, errors };
}

export async function importCsv(
  file: File,
  onProgress: ProgressCallback,
): Promise<CsvImportProgress> {
  const progress: CsvImportProgress = {
    total: 0,
    processed: 0,
    inserted: 0,
    updated: 0,
    errors: 0,
    errorDetails: [],
    phase: 'parsing',
  };

  onProgress({ ...progress });

  const channelMap = await fetchChannelMap();

  return new Promise((resolve) => {
    const allRows: CsvRow[] = [];

    Papa.parse<CsvRow>(file, {
      header: true,
      skipEmptyLines: true,
      complete: async (results) => {
        allRows.push(...(results.data as CsvRow[]));
        progress.total = allRows.length;
        progress.phase = 'importing';
        onProgress({ ...progress });

        const BATCH = 300;
        for (let i = 0; i < allRows.length; i += BATCH) {
          const batch = allRows.slice(i, i + BATCH);
          try {
            const emailToId = await upsertCustomerBatch(batch);
            const { inserted, updated, errors } = await upsertTicketBatch(batch, emailToId, channelMap);
            progress.inserted += inserted;
            progress.updated += updated;
            progress.errors += errors.length;
            progress.errorDetails.push(...errors);
          } catch (err) {
            const msg = err instanceof Error ? err.message : String(err);
            progress.errors += batch.length;
            progress.errorDetails.push(msg);
          }
          progress.processed = Math.min(i + BATCH, allRows.length);
          onProgress({ ...progress });
        }

        progress.phase = 'done';
        onProgress({ ...progress });
        resolve({ ...progress });
      },
      error: (err) => {
        progress.phase = 'error';
        progress.errorDetails.push(err.message);
        onProgress({ ...progress });
        resolve({ ...progress });
      },
    });
  });
}
