import { supabase } from '../lib/supabaseClient';
import type { Tag, TicketTag } from '../types';

export async function getTags(): Promise<Tag[]> {
  const { data, error } = await supabase
    .from('tags')
    .select('*')
    .order('name');
  if (error) throw new Error(error.message);
  return (data ?? []) as Tag[];
}

export async function createTag(name: string, color: string): Promise<Tag> {
  const { data, error } = await supabase
    .from('tags')
    .insert({ name: name.trim().toLowerCase(), color })
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as Tag;
}

export async function getTicketTags(ticketId: string): Promise<Tag[]> {
  const { data, error } = await supabase
    .from('ticket_tags')
    .select('tag_id, tags(*)')
    .eq('ticket_id', ticketId);
  if (error) throw new Error(error.message);
  return ((data ?? []) as TicketTag[])
    .map((tt) => tt.tag)
    .filter((t): t is Tag => !!t);
}

export async function assignTag(ticketId: string, tagId: string): Promise<void> {
  const { error } = await supabase
    .from('ticket_tags')
    .insert({ ticket_id: ticketId, tag_id: tagId });
  if (error && error.code !== '23505') throw new Error(error.message);
}

export async function removeTag(ticketId: string, tagId: string): Promise<void> {
  const { error } = await supabase
    .from('ticket_tags')
    .delete()
    .eq('ticket_id', ticketId)
    .eq('tag_id', tagId);
  if (error) throw new Error(error.message);
}

export async function getTagsForTickets(ticketIds: string[]): Promise<Record<string, Tag[]>> {
  if (ticketIds.length === 0) return {};
  const { data, error } = await supabase
    .from('ticket_tags')
    .select('ticket_id, tags(*)')
    .in('ticket_id', ticketIds);
  if (error) throw new Error(error.message);

  const map: Record<string, Tag[]> = {};
  for (const row of (data ?? []) as TicketTag[]) {
    if (!row.ticket_id || !row.tag) continue;
    if (!map[row.ticket_id]) map[row.ticket_id] = [];
    map[row.ticket_id].push(row.tag);
  }
  return map;
}
