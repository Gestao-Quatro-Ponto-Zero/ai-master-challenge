import { supabase } from '../lib/supabaseClient';

export type AuditAction =
  | 'login'
  | 'logout'
  | 'user_created'
  | 'user_updated'
  | 'user_suspended'
  | 'user_role_changed'
  | 'profile_updated'
  | 'password_changed'
  | 'avatar_updated';

export interface AuditMetadata {
  changes?: Record<string, unknown>;
  [key: string]: unknown;
}

export async function logAction(
  userId: string,
  action: AuditAction | string,
  resource: string,
  resourceId: string,
  metadata?: AuditMetadata
): Promise<void> {
  const { error } = await supabase.from('audit_logs').insert({
    user_id: userId,
    action,
    resource,
    resource_id: resourceId,
    meta: metadata ?? null,
  });

  if (error) {
    console.warn('[AuditService] Failed to write audit log:', error.message);
  }
}
