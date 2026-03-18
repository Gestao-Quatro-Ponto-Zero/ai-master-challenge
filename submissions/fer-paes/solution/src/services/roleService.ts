import { supabase } from '../lib/supabaseClient';
import type { Role, Permission, RoleWithPermissions } from '../types';

export async function getRoles(): Promise<Role[]> {
  const { data, error } = await supabase.from('roles').select('*').order('name');
  if (error) throw new Error(error.message);
  return (data || []) as Role[];
}

export async function createRole(name: string, description: string): Promise<Role> {
  const { data, error } = await supabase
    .from('roles')
    .insert({ name, description })
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as Role;
}

export async function updateRole(id: string, updates: Partial<Pick<Role, 'name' | 'description'>>): Promise<Role> {
  const { data, error } = await supabase
    .from('roles')
    .update({ ...updates, updated_at: new Date().toISOString() })
    .eq('id', id)
    .select()
    .single();
  if (error) throw new Error(error.message);
  return data as Role;
}

export async function getRolePermissions(roleId: string): Promise<Permission[]> {
  const { data: rolePerms } = await supabase
    .from('role_permissions')
    .select('permission_id')
    .eq('role_id', roleId);

  if (!rolePerms || rolePerms.length === 0) return [];

  const permIds = rolePerms.map((rp: { permission_id: string }) => rp.permission_id);
  const { data, error } = await supabase.from('permissions').select('*').in('id', permIds);
  if (error) throw new Error(error.message);
  return (data || []) as Permission[];
}

export async function assignPermissionsToRole(roleId: string, permissionIds: string[]): Promise<void> {
  await supabase.from('role_permissions').delete().eq('role_id', roleId);

  if (permissionIds.length === 0) return;

  const inserts = permissionIds.map((pid) => ({ role_id: roleId, permission_id: pid }));
  const { error } = await supabase.from('role_permissions').insert(inserts);
  if (error) throw new Error(error.message);
}

export async function getAllPermissions(): Promise<Permission[]> {
  const { data, error } = await supabase.from('permissions').select('*').order('category').order('name');
  if (error) throw new Error(error.message);
  return (data || []) as Permission[];
}

export async function getRolesWithPermissions(): Promise<RoleWithPermissions[]> {
  const roles = await getRoles();
  const result: RoleWithPermissions[] = [];

  for (const role of roles) {
    const permissions = await getRolePermissions(role.id);
    result.push({ ...role, permissions });
  }

  return result;
}
