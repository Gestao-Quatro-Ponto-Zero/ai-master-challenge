import { supabase } from '../lib/supabaseClient';
import { logAction } from './auditService';
import type { AuthPayload, LoginCredentials, Profile, Role, Permission } from '../types';

async function getProfileAndRoles(userId: string): Promise<{ profile: Profile | null; roles: Role[]; permissions: Permission[] }> {
  const [profileRes, userRolesRes] = await Promise.all([
    supabase.from('profiles').select('*').eq('id', userId).maybeSingle(),
    supabase.from('user_roles').select('role_id').eq('user_id', userId),
  ]);

  const profile = profileRes.data as Profile | null;
  const roleIds = (userRolesRes.data || []).map((ur: { role_id: string }) => ur.role_id);

  if (roleIds.length === 0) {
    return { profile, roles: [], permissions: [] };
  }

  const rolesRes = await supabase.from('roles').select('*').in('id', roleIds);
  const roles = (rolesRes.data || []) as Role[];

  const rolePermRes = await supabase
    .from('role_permissions')
    .select('permission_id')
    .in('role_id', roleIds);

  const permissionIds = (rolePermRes.data || []).map((rp: { permission_id: string }) => rp.permission_id);
  const uniquePermIds = [...new Set(permissionIds)];

  if (uniquePermIds.length === 0) {
    return { profile, roles, permissions: [] };
  }

  const permsRes = await supabase.from('permissions').select('*').in('id', uniquePermIds);
  const permissions = (permsRes.data || []) as Permission[];

  return { profile, roles, permissions };
}

export async function login(credentials: LoginCredentials): Promise<AuthPayload> {
  const { data, error } = await supabase.auth.signInWithPassword({
    email: credentials.email,
    password: credentials.password,
  });

  if (error || !data.user) {
    throw new Error(error?.message || 'Login failed');
  }

  const { profile, roles, permissions } = await getProfileAndRoles(data.user.id);

  await logAction(data.user.id, 'login', 'auth', data.user.id, {
    email: data.user.email,
  });

  return {
    user: { id: data.user.id, email: data.user.email || '' },
    profile,
    roles,
    permissions,
  };
}

export async function logout(): Promise<void> {
  const { data } = await supabase.auth.getSession();
  const userId = data.session?.user?.id;

  if (userId) {
    await logAction(userId, 'logout', 'auth', userId);
  }

  await supabase.auth.signOut();
}

export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<void> {
  if (newPassword.length < 8) {
    throw new Error('Password must be at least 8 characters.');
  }
  if (!/\d/.test(newPassword)) {
    throw new Error('Password must contain at least one number.');
  }
  if (!/[a-zA-Z]/.test(newPassword)) {
    throw new Error('Password must contain at least one letter.');
  }

  const { data: sessionData } = await supabase.auth.getSession();
  const email = sessionData.session?.user?.email;
  if (!email) throw new Error('Not authenticated.');

  const { error: verifyError } = await supabase.auth.signInWithPassword({
    email,
    password: currentPassword,
  });
  if (verifyError) throw new Error('Current password is incorrect.');

  const { error } = await supabase.auth.updateUser({ password: newPassword });
  if (error) throw new Error(error.message);

  const userId = sessionData.session?.user?.id;
  if (userId) {
    await logAction(userId, 'password_changed', 'auth', userId);
  }
}

export async function getCurrentUser(): Promise<AuthPayload | null> {
  const { data } = await supabase.auth.getSession();
  if (!data.session?.user) return null;

  const user = data.session.user;
  const { profile, roles, permissions } = await getProfileAndRoles(user.id);

  return {
    user: { id: user.id, email: user.email || '' },
    profile,
    roles,
    permissions,
  };
}
