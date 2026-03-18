import { supabase } from '../lib/supabaseClient';
import type {
  Customer,
  CustomerWithStats,
  CustomerFilters,
  IdentifyCustomerPayload,
  UpdateCustomerPayload,
  TicketWithRelations,
  Conversation,
} from '../types';

export async function createCustomer(data: IdentifyCustomerPayload): Promise<Customer> {
  const { data: customer, error } = await supabase
    .from('customers')
    .insert({
      name: data.name ?? null,
      email: data.email ?? null,
      phone: data.phone ?? null,
      external_id: data.external_id ?? null,
      external_source: data.external_source ?? null,
    })
    .select()
    .single();

  if (error) throw new Error(error.message);
  return customer as Customer;
}

export async function getCustomerByEmail(email: string): Promise<Customer | null> {
  const { data, error } = await supabase
    .from('customers')
    .select('*')
    .eq('email', email)
    .maybeSingle();

  if (error) throw new Error(error.message);
  return data as Customer | null;
}

export async function getCustomerByPhone(phone: string): Promise<Customer | null> {
  const { data, error } = await supabase
    .from('customers')
    .select('*')
    .eq('phone', phone)
    .maybeSingle();

  if (error) throw new Error(error.message);
  return data as Customer | null;
}

export async function getCustomerByExternalId(
  externalId: string,
  externalSource?: string,
): Promise<Customer | null> {
  let query = supabase
    .from('customers')
    .select('*')
    .eq('external_id', externalId);

  if (externalSource) {
    query = query.eq('external_source', externalSource);
  }

  const { data, error } = await query.maybeSingle();
  if (error) throw new Error(error.message);
  return data as Customer | null;
}

export async function getCustomer(customerId: string): Promise<Customer | null> {
  const { data, error } = await supabase
    .from('customers')
    .select('*')
    .eq('id', customerId)
    .maybeSingle();

  if (error) throw new Error(error.message);
  return data as Customer | null;
}

export async function getCustomerWithTickets(customerId: string): Promise<{
  customer: Customer;
  tickets: TicketWithRelations[];
  recent_conversations: Conversation[];
} | null> {
  const { data: customer, error: custError } = await supabase
    .from('customers')
    .select('*')
    .eq('id', customerId)
    .maybeSingle();

  if (custError) throw new Error(custError.message);
  if (!customer) return null;

  const { data: ticketsRaw, error: ticketsError } = await supabase
    .from('tickets')
    .select(`
      *,
      customer:customers(*),
      channel:channels(*),
      conversation:conversations(*)
    `)
    .eq('customer_id', customerId)
    .order('updated_at', { ascending: false });

  if (ticketsError) throw new Error(ticketsError.message);

  const tickets: TicketWithRelations[] = ((ticketsRaw || []) as unknown[]).map((row) => {
    const r = row as Record<string, unknown>;
    const conv = Array.isArray(r.conversation)
      ? (r.conversation as Conversation[])[0] ?? null
      : (r.conversation as Conversation | null);
    return {
      ...r,
      customer: Array.isArray(r.customer) ? (r.customer as unknown[])[0] ?? null : r.customer,
      channel: Array.isArray(r.channel) ? (r.channel as unknown[])[0] ?? null : r.channel,
      conversation: conv,
      assigned_user: null,
    } as TicketWithRelations;
  });

  const ticketIds = tickets.map((t) => t.id);
  let recent_conversations: Conversation[] = [];

  if (ticketIds.length > 0) {
    const { data: convData, error: convError } = await supabase
      .from('conversations')
      .select('*')
      .in('ticket_id', ticketIds)
      .order('last_message_at', { ascending: false })
      .limit(5);

    if (convError) throw new Error(convError.message);
    recent_conversations = (convData || []) as Conversation[];
  }

  return {
    customer: customer as Customer,
    tickets,
    recent_conversations,
  };
}

export async function updateCustomer(
  customerId: string,
  data: UpdateCustomerPayload,
): Promise<Customer> {
  const { data: updated, error } = await supabase
    .from('customers')
    .update({
      name: data.name,
      email: data.email,
      phone: data.phone,
      updated_at: new Date().toISOString(),
    })
    .eq('id', customerId)
    .select()
    .single();

  if (error) throw new Error(error.message);
  return updated as Customer;
}

export async function identifyOrCreateCustomer(
  data: IdentifyCustomerPayload,
): Promise<Customer> {
  if (data.external_id) {
    const found = await getCustomerByExternalId(
      data.external_id,
      data.external_source ?? undefined,
    );
    if (found) return found;
  }

  if (data.email) {
    const found = await getCustomerByEmail(data.email);
    if (found) return found;
  }

  if (data.phone) {
    const found = await getCustomerByPhone(data.phone);
    if (found) return found;
  }

  return createCustomer(data);
}

export async function getCustomers(filters: CustomerFilters = {}): Promise<CustomerWithStats[]> {
  let query = supabase
    .from('customers')
    .select('*')
    .order('created_at', { ascending: false });

  if (filters.email) {
    query = query.ilike('email', `%${filters.email}%`);
  }
  if (filters.phone) {
    query = query.ilike('phone', `%${filters.phone}%`);
  }
  if (filters.search) {
    const s = `%${filters.search}%`;
    query = query.or(`name.ilike.${s},email.ilike.${s},phone.ilike.${s}`);
  }

  const { data, error } = await query;
  if (error) throw new Error(error.message);

  const customers = (data || []) as Customer[];
  if (customers.length === 0) return [];

  const ids = customers.map((c) => c.id);
  const { data: ticketsRaw, error: ticketsError } = await supabase
    .from('tickets')
    .select('customer_id, updated_at')
    .in('customer_id', ids);

  if (ticketsError) throw new Error(ticketsError.message);

  const statsMap: Record<string, { count: number; last: string | null }> = {};
  for (const t of (ticketsRaw || []) as { customer_id: string; updated_at: string }[]) {
    if (!statsMap[t.customer_id]) {
      statsMap[t.customer_id] = { count: 0, last: null };
    }
    statsMap[t.customer_id].count += 1;
    if (!statsMap[t.customer_id].last || t.updated_at > statsMap[t.customer_id].last!) {
      statsMap[t.customer_id].last = t.updated_at;
    }
  }

  return customers.map((c) => ({
    ...c,
    tickets_count: statsMap[c.id]?.count ?? 0,
    last_contact: statsMap[c.id]?.last ?? null,
  }));
}
