import { supabase } from '../lib/supabaseClient';

export type CampaignChannel = 'email' | 'whatsapp' | 'chat' | 'sms';
export type CampaignStatus  = 'draft' | 'scheduled' | 'running' | 'completed' | 'paused';

export interface Campaign {
  id:               string;
  name:             string;
  description:      string;
  segment_id:       string;
  segment_name:     string;
  segment_active:   boolean;
  member_count:     number;
  channel:          CampaignChannel;
  message_template: string;
  status:           CampaignStatus;
  scheduled_at:     string | null;
  started_at:       string | null;
  completed_at:     string | null;
  created_by:       string | null;
  creator_name:     string | null;
  created_at:       string;
  updated_at:       string;
}

export interface CreateCampaignInput {
  name:             string;
  description?:     string;
  segment_id:       string;
  channel:          CampaignChannel;
  message_template: string;
  scheduled_at?:    string | null;
}

export interface UpdateCampaignInput {
  name?:             string;
  description?:      string;
  segment_id?:       string;
  channel?:          CampaignChannel;
  message_template?: string;
  scheduled_at?:     string | null;
}

export async function getCampaigns(): Promise<Campaign[]> {
  const { data, error } = await supabase.rpc('get_campaigns');
  if (error) throw new Error(error.message);
  return ((data ?? []) as Campaign[]).map((c) => ({
    ...c,
    member_count: Number(c.member_count),
  }));
}

export async function getCampaignById(id: string): Promise<Campaign | null> {
  const { data, error } = await supabase.rpc('get_campaign_by_id', { p_id: id });
  if (error) throw new Error(error.message);
  const rows = data as Campaign[];
  if (!rows || rows.length === 0) return null;
  return { ...rows[0], member_count: Number(rows[0].member_count) };
}

export async function createCampaign(
  input: CreateCampaignInput,
  createdBy?: string,
): Promise<string> {
  const { data: userData } = await supabase.auth.getUser();
  const userId = createdBy ?? userData?.user?.id ?? null;

  const { data, error } = await supabase.rpc('create_campaign', {
    p_name:             input.name,
    p_description:      input.description      ?? '',
    p_segment_id:       input.segment_id,
    p_channel:          input.channel,
    p_message_template: input.message_template,
    p_scheduled_at:     input.scheduled_at     ?? null,
    p_created_by:       userId,
  });
  if (error) throw new Error(error.message);
  return data as string;
}

export async function updateCampaign(id: string, input: UpdateCampaignInput): Promise<void> {
  const { error } = await supabase.rpc('update_campaign', {
    p_id:               id,
    p_name:             input.name             ?? null,
    p_description:      input.description      ?? null,
    p_segment_id:       input.segment_id       ?? null,
    p_channel:          input.channel          ?? null,
    p_message_template: input.message_template ?? null,
    p_scheduled_at:     input.scheduled_at     ?? null,
  });
  if (error) throw new Error(error.message);
}

export async function activateCampaign(id: string): Promise<void> {
  const { error } = await supabase.rpc('activate_campaign', { p_id: id });
  if (error) throw new Error(error.message);
}

export async function pauseCampaign(id: string): Promise<void> {
  const { error } = await supabase.rpc('pause_campaign', { p_id: id });
  if (error) throw new Error(error.message);
}

export async function completeCampaign(id: string): Promise<void> {
  const { error } = await supabase.rpc('complete_campaign', { p_id: id });
  if (error) throw new Error(error.message);
}

export async function deleteCampaign(id: string): Promise<void> {
  const { error } = await supabase.rpc('delete_campaign', { p_id: id });
  if (error) throw new Error(error.message);
}

export function renderTemplate(
  template: string,
  vars: Record<string, string>,
): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key: string) => vars[key] ?? `{{${key}}}`);
}

export const CHANNEL_META: Record<
  CampaignChannel,
  { label: string; color: string; bg: string; border: string }
> = {
  email:     { label: 'Email',     color: 'text-blue-600',   bg: 'bg-blue-50',   border: 'border-blue-100' },
  whatsapp:  { label: 'WhatsApp',  color: 'text-emerald-600',bg: 'bg-emerald-50',border: 'border-emerald-100' },
  chat:      { label: 'Chat',      color: 'text-sky-600',    bg: 'bg-sky-50',    border: 'border-sky-100' },
  sms:       { label: 'SMS',       color: 'text-amber-600',  bg: 'bg-amber-50',  border: 'border-amber-100' },
};

export const STATUS_META: Record<
  CampaignStatus,
  { label: string; color: string; bg: string; border: string }
> = {
  draft:     { label: 'Rascunho',  color: 'text-gray-500',   bg: 'bg-gray-100',  border: 'border-gray-200' },
  scheduled: { label: 'Agendada',  color: 'text-blue-600',   bg: 'bg-blue-50',   border: 'border-blue-100' },
  running:   { label: 'Rodando',   color: 'text-emerald-600',bg: 'bg-emerald-50',border: 'border-emerald-100' },
  completed: { label: 'Concluída', color: 'text-teal-600',   bg: 'bg-teal-50',   border: 'border-teal-100' },
  paused:    { label: 'Pausada',   color: 'text-amber-600',  bg: 'bg-amber-50',  border: 'border-amber-100' },
};

export const TEMPLATE_VARS = [
  '{{customer_name}}',
  '{{customer_email}}',
  '{{last_ticket_date}}',
  '{{company_name}}',
  '{{support_link}}',
];
