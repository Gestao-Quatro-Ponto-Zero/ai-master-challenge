import { supabase } from '../lib/supabaseClient';
import type { Macro, MacroContext } from '../types';

export async function getMacros(): Promise<Macro[]> {
  const { data, error } = await supabase
    .from('macros')
    .select('*')
    .order('category')
    .order('name');
  if (error) throw new Error(error.message);
  return (data ?? []) as Macro[];
}

export async function getMacroById(id: string): Promise<Macro | null> {
  const { data, error } = await supabase
    .from('macros')
    .select('*')
    .eq('id', id)
    .maybeSingle();
  if (error) throw new Error(error.message);
  return data as Macro | null;
}

export async function createMacro(
  macro: Pick<Macro, 'name' | 'content' | 'category'>,
): Promise<Macro> {
  const { data, error } = await supabase
    .from('macros')
    .insert(macro)
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as Macro;
}

export async function updateMacro(
  id: string,
  updates: Partial<Pick<Macro, 'name' | 'content' | 'category'>>,
): Promise<Macro> {
  const { data, error } = await supabase
    .from('macros')
    .update({ ...updates, updated_at: new Date().toISOString() })
    .eq('id', id)
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as Macro;
}

export async function deleteMacro(id: string): Promise<void> {
  const { error } = await supabase.from('macros').delete().eq('id', id);
  if (error) throw new Error(error.message);
}

export function applyMacro(content: string, ctx: MacroContext): string {
  return content
    .replace(/\{\{customer_name\}\}/gi, ctx.customer_name || 'Customer')
    .replace(/\{\{ticket_id\}\}/gi, ctx.ticket_id || '')
    .replace(/\{\{agent_name\}\}/gi, ctx.agent_name || 'Agent');
}
