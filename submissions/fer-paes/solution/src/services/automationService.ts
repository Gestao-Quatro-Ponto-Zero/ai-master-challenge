import { supabase } from '../lib/supabaseClient';
import type {
  AutomationRule,
  AutomationCondition,
  AutomationAction,
  AutomationContext,
  TriggerEvent,
} from '../types';

export async function getRules(): Promise<AutomationRule[]> {
  const { data, error } = await supabase
    .from('automation_rules')
    .select('*')
    .order('created_at', { ascending: false });
  if (error) throw new Error(error.message);
  return (data ?? []) as AutomationRule[];
}

export async function createRule(
  rule: Omit<AutomationRule, 'id' | 'created_at' | 'updated_at' | 'created_by'>,
): Promise<AutomationRule> {
  const { data, error } = await supabase
    .from('automation_rules')
    .insert(rule)
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as AutomationRule;
}

export async function updateRule(
  id: string,
  updates: Partial<Omit<AutomationRule, 'id' | 'created_at' | 'created_by'>>,
): Promise<AutomationRule> {
  const { data, error } = await supabase
    .from('automation_rules')
    .update({ ...updates, updated_at: new Date().toISOString() })
    .eq('id', id)
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as AutomationRule;
}

export async function deleteRule(id: string): Promise<void> {
  const { error } = await supabase.from('automation_rules').delete().eq('id', id);
  if (error) throw new Error(error.message);
}

export async function toggleRule(id: string, is_active: boolean): Promise<void> {
  const { error } = await supabase
    .from('automation_rules')
    .update({ is_active, updated_at: new Date().toISOString() })
    .eq('id', id);
  if (error) throw new Error(error.message);
}

function evaluateCondition(condition: AutomationCondition, ctx: AutomationContext): boolean {
  const { field, operator, value } = condition;

  let fieldValue: string | null = null;
  if (field === 'priority') fieldValue = ctx.priority;
  else if (field === 'status') fieldValue = ctx.status;
  else if (field === 'channel') fieldValue = ctx.channel_name ?? ctx.channel_id ?? null;
  else if (field === 'assigned') fieldValue = ctx.assigned_user_id ?? null;
  else if (field === 'tag') {
    if (operator === 'is_empty') return (ctx.tag_ids ?? []).length === 0;
    if (operator === 'contains') return (ctx.tag_ids ?? []).includes(value);
    if (operator === 'not_equals') return !(ctx.tag_ids ?? []).includes(value);
    if (operator === 'equals') return (ctx.tag_ids ?? []).includes(value);
    return false;
  }

  if (operator === 'is_empty') return !fieldValue;
  if (!fieldValue) return false;
  if (operator === 'equals') return fieldValue === value;
  if (operator === 'not_equals') return fieldValue !== value;
  if (operator === 'contains') return fieldValue.toLowerCase().includes(value.toLowerCase());
  return false;
}

async function executeAction(action: AutomationAction, ctx: AutomationContext): Promise<void> {
  const { type, value } = action;

  if (type === 'assign_user') {
    await supabase
      .from('tickets')
      .update({ assigned_user_id: value, updated_at: new Date().toISOString() })
      .eq('id', ctx.ticket_id);
  } else if (type === 'add_tag') {
    await supabase
      .from('ticket_tags')
      .insert({ ticket_id: ctx.ticket_id, tag_id: value })
      .select();
  } else if (type === 'change_priority') {
    await supabase
      .from('tickets')
      .update({ priority: value, updated_at: new Date().toISOString() })
      .eq('id', ctx.ticket_id);
  } else if (type === 'change_status') {
    await supabase
      .from('tickets')
      .update({ status: value, updated_at: new Date().toISOString() })
      .eq('id', ctx.ticket_id);
  }
}

export async function evaluateRules(
  event: TriggerEvent,
  ctx: AutomationContext,
): Promise<void> {
  let rules: AutomationRule[];
  try {
    const { data, error } = await supabase
      .from('automation_rules')
      .select('*')
      .eq('trigger_event', event)
      .eq('is_active', true);
    if (error || !data) return;
    rules = data as AutomationRule[];
  } catch {
    return;
  }

  for (const rule of rules) {
    const conditions = rule.conditions ?? [];
    const allPass = conditions.every((c) => evaluateCondition(c, ctx));
    if (allPass) {
      for (const action of rule.actions ?? []) {
        try {
          await executeAction(action, ctx);
        } catch {
          // continue with next action
        }
      }
    }
  }
}
