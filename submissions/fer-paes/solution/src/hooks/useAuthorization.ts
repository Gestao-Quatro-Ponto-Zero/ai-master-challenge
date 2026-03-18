import { useAuth } from '../contexts/AuthContext';
import { userHasPermission } from '../services/permissionService';

export interface AuthorizationState {
  isAuthenticated: boolean;
  isLoading: boolean;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
}

export function useAuthorization(): AuthorizationState {
  const { isAuthenticated, isLoading, permissions, user } = useAuth();

  function hasPermission(permission: string): boolean {
    if (!isAuthenticated || !user) return false;
    return userHasPermission(permissions, permission);
  }

  function hasAnyPermission(perms: string[]): boolean {
    return perms.some((p) => hasPermission(p));
  }

  function hasAllPermissions(perms: string[]): boolean {
    return perms.every((p) => hasPermission(p));
  }

  return {
    isAuthenticated,
    isLoading,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
  };
}
