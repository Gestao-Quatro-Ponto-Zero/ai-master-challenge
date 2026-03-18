import { supabase } from '../lib/supabaseClient';
import { logAction } from './auditService';
import type { Profile, Role } from '../types';

export interface ProfileWithRoles {
  profile: Profile;
  roles: Role[];
}

export async function getProfile(userId: string): Promise<ProfileWithRoles | null> {
  const { data: profile, error } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .maybeSingle();

  if (error || !profile) return null;

  const { data: userRoles } = await supabase
    .from('user_roles')
    .select('role_id')
    .eq('user_id', userId);

  const roleIds = (userRoles || []).map((ur) => ur.role_id);
  let roles: Role[] = [];

  if (roleIds.length > 0) {
    const { data: rolesData } = await supabase.from('roles').select('*').in('id', roleIds);
    roles = (rolesData || []) as Role[];
  }

  return { profile: profile as Profile, roles };
}

export async function updateProfile(
  userId: string,
  data: {
    full_name?: string;
    phone?: string;
    department?: string;
    timezone?: string;
  }
): Promise<Profile> {
  const { data: updated, error } = await supabase
    .from('profiles')
    .update({ ...data, updated_at: new Date().toISOString() })
    .eq('id', userId)
    .select()
    .single();

  if (error) throw new Error(error.message);

  await logAction(userId, 'profile_updated', 'profiles', userId, data as Record<string, unknown>);

  return updated as Profile;
}

export async function updateAvatar(userId: string, avatarUrl: string): Promise<Profile> {
  const { data: updated, error } = await supabase
    .from('profiles')
    .update({ avatar_url: avatarUrl, updated_at: new Date().toISOString() })
    .eq('id', userId)
    .select()
    .single();

  if (error) throw new Error(error.message);

  await logAction(userId, 'avatar_updated', 'profiles', userId, { avatar_url: avatarUrl });

  return updated as Profile;
}
