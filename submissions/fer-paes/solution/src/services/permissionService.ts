import { supabase } from '../lib/supabaseClient';
import type { Permission } from '../types';

export async function getPermissionsByRole(roleId: string): Promise<Permission[]> {
  const { data: rolePerms } = await supabase
    .from('role_permissions')
    .select('permission_id')
    .eq('role_id', roleId);

  if (!rolePerms || rolePerms.length === 0) return [];

  const permIds = rolePerms.map((rp: { permission_id: string }) => rp.permission_id);
  const { data } = await supabase.from('permissions').select('*').in('id', permIds);
  return (data || []) as Permission[];
}

export async function getPermissionsByUser(userId: string): Promise<Permission[]> {
  const { data: userRoles } = await supabase
    .from('user_roles')
    .select('role_id')
    .eq('user_id', userId);

  if (!userRoles || userRoles.length === 0) return [];

  const roleIds = userRoles.map((ur: { role_id: string }) => ur.role_id);

  const { data: rolePerms } = await supabase
    .from('role_permissions')
    .select('permission_id')
    .in('role_id', roleIds);

  if (!rolePerms || rolePerms.length === 0) return [];

  const permIds = [...new Set(rolePerms.map((rp: { permission_id: string }) => rp.permission_id))];
  const { data } = await supabase.from('permissions').select('*').in('id', permIds);
  return (data || []) as Permission[];
}

export function userHasPermission(permissions: Permission[], permissionName: string): boolean {
  return permissions.some((p) => p.name === permissionName);
}
