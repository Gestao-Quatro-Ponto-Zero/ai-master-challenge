import { useAuthorization } from '../hooks/useAuthorization';
import { AccessDenied } from './AccessDenied';
import type { ReactNode } from 'react';

interface PermissionGuardProps {
  permission: string;
  children: ReactNode;
  fallback?: ReactNode;
}

export function PermissionGuard({ permission, children, fallback }: PermissionGuardProps) {
  const { hasPermission, isLoading } = useAuthorization();

  if (isLoading) return null;

  if (!hasPermission(permission)) {
    return <>{fallback !== undefined ? fallback : <AccessDenied />}</>;
  }

  return <>{children}</>;
}
