import { supabase } from '../lib/supabaseClient';
import { logAction } from './auditService';
import type { UserWithProfile, Role, UserStatus } from '../types';

function generateTemporaryPassword(): string {
  const chars = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789!@#$';
  let password = '';
  for (let i = 0; i < 12; i++) {
    password += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return password;
}

export async function getUsers(filters?: {
  email?: string;
  status?: string;
  role?: string;
}): Promise<UserWithProfile[]> {
  let profilesQuery = supabase.from('profiles').select('*');

  if (filters?.email) {
    profilesQuery = profilesQuery.ilike('email', `%${filters.email}%`);
  }
  if (filters?.status) {
    profilesQuery = profilesQuery.eq('status', filters.status);
  }

  const { data: profiles, error } = await profilesQuery;
  if (error) throw new Error(error.message);
  if (!profiles || profiles.length === 0) return [];

  const userIds = profiles.map((p) => p.id);

  const { data: userRoles } = await supabase
    .from('user_roles')
    .select('user_id, role_id')
    .in('user_id', userIds);

  const roleIds = [...new Set((userRoles || []).map((ur) => ur.role_id))];

  let roles: Role[] = [];
  if (roleIds.length > 0) {
    const { data: rolesData } = await supabase.from('roles').select('*').in('id', roleIds);
    roles = (rolesData || []) as Role[];
  }

  const roleMap = new Map(roles.map((r) => [r.id, r]));

  const usersWithRoles: UserWithProfile[] = profiles.map((profile) => {
    const userRoleIds = (userRoles || [])
      .filter((ur) => ur.user_id === profile.id)
      .map((ur) => ur.role_id);
    const assignedRoles = userRoleIds.map((rid) => roleMap.get(rid)).filter(Boolean) as Role[];

    if (filters?.role && !assignedRoles.some((r) => r.name === filters.role)) {
      return null;
    }

    return {
      id: profile.id,
      email: profile.email,
      status: profile.status,
      profile,
      roles: assignedRoles,
    };
  });

  return usersWithRoles.filter(Boolean) as UserWithProfile[];
}

export async function getUserById(userId: string): Promise<UserWithProfile | null> {
  const { data: profile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .maybeSingle();

  if (!profile) return null;

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

  return {
    id: profile.id,
    email: profile.email,
    status: profile.status,
    profile,
    roles,
  };
}

export async function createUser(
  email: string,
  roleIds: string[],
  actorId: string
): Promise<{ user: UserWithProfile; temporaryPassword: string }> {
  const existingProfile = await supabase
    .from('profiles')
    .select('id')
    .eq('email', email)
    .maybeSingle();

  if (existingProfile.data) {
    throw new Error('A user with this email already exists.');
  }

  const temporaryPassword = generateTemporaryPassword();

  const { data: edgeData, error: edgeError } = await supabase.functions.invoke('create-admin-user', {
    body: { email, password: temporaryPassword },
  });

  if (edgeError) throw new Error(edgeError.message);
  if (edgeData?.error) throw new Error(edgeData.error);
  if (!edgeData?.user_id) throw new Error('Failed to create user');

  const newUserId = edgeData.user_id as string;

  const { error: profileError } = await supabase.from('profiles').insert({
    id: newUserId,
    email,
    full_name: '',
    status: 'invited',
    department: '',
    phone: '',
    timezone: 'UTC',
  });

  if (profileError) throw new Error(profileError.message);

  if (roleIds.length > 0) {
    const roleInserts = roleIds.map((role_id) => ({
      user_id: newUserId,
      role_id,
      assigned_by: actorId,
    }));
    const { error: roleError } = await supabase.from('user_roles').insert(roleInserts);
    if (roleError) throw new Error(roleError.message);
  }

  await logAction(actorId, 'user_created', 'users', newUserId, { email, roleIds });

  const created = await getUserById(newUserId);
  if (!created) throw new Error('Failed to fetch created user');

  return { user: created, temporaryPassword };
}

export async function updateUser(
  userId: string,
  data: { email?: string; department?: string; phone?: string; timezone?: string; full_name?: string },
  actorId: string
): Promise<UserWithProfile> {
  const updatePayload: Record<string, unknown> = { ...data, updated_at: new Date().toISOString() };

  const { error } = await supabase.from('profiles').update(updatePayload).eq('id', userId);
  if (error) throw new Error(error.message);

  await logAction(actorId, 'user_updated', 'users', userId, data as Record<string, unknown>);

  const updated = await getUserById(userId);
  if (!updated) throw new Error('Failed to fetch updated user');
  return updated;
}

export async function changeUserStatus(
  userId: string,
  status: UserStatus,
  actorId: string
): Promise<void> {
  const { error } = await supabase
    .from('profiles')
    .update({ status, updated_at: new Date().toISOString() })
    .eq('id', userId);

  if (error) throw new Error(error.message);

  const action = status === 'suspended' ? 'user_suspended' : 'user_updated';
  await logAction(actorId, action, 'users', userId, { status });
}

export async function assignRoles(
  userId: string,
  roleIds: string[],
  actorId: string
): Promise<void> {
  const { error: deleteError } = await supabase
    .from('user_roles')
    .delete()
    .eq('user_id', userId);

  if (deleteError) throw new Error(deleteError.message);

  if (roleIds.length > 0) {
    const roleInserts = roleIds.map((role_id) => ({
      user_id: userId,
      role_id,
      assigned_by: actorId,
    }));
    const { error: insertError } = await supabase.from('user_roles').insert(roleInserts);
    if (insertError) throw new Error(insertError.message);
  }

  await logAction(actorId, 'user_role_changed', 'users', userId, { roleIds });
}
