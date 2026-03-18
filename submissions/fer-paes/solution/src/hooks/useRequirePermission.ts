import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthorization } from './useAuthorization';

interface Options {
  redirectTo?: string;
}

export function useRequirePermission(permission: string, options: Options = {}): {
  isAllowed: boolean;
  isLoading: boolean;
} {
  const { hasPermission, isLoading, isAuthenticated } = useAuthorization();
  const navigate = useNavigate();
  const { redirectTo } = options;

  const isAllowed = !isLoading && isAuthenticated && hasPermission(permission);

  useEffect(() => {
    if (!isLoading && redirectTo) {
      if (!isAuthenticated) {
        navigate('/login', { replace: true });
      } else if (!hasPermission(permission)) {
        navigate(redirectTo, { replace: true });
      }
    }
  }, [isLoading, isAuthenticated, permission]);

  return { isAllowed, isLoading };
}
