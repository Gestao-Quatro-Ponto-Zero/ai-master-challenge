import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { supabase } from '../lib/supabaseClient';
import { getCurrentUser } from '../services/authService';
import type { AuthState } from '../types';

const initialState: AuthState = {
  user: null,
  profile: null,
  roles: [],
  permissions: [],
  isLoading: true,
  isAuthenticated: false,
};

interface AuthContextValue extends AuthState {
  refreshAuth: () => Promise<void>;
  setAuth: (state: Partial<AuthState>) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(initialState);

  const refreshAuth = async () => {
    setState((s) => ({ ...s, isLoading: true }));
    const payload = await getCurrentUser();
    if (payload) {
      setState({
        user: payload.user,
        profile: payload.profile,
        roles: payload.roles,
        permissions: payload.permissions,
        isLoading: false,
        isAuthenticated: true,
      });
    } else {
      setState({ ...initialState, isLoading: false });
    }
  };

  const setAuth = (partial: Partial<AuthState>) => {
    setState((s) => ({ ...s, ...partial }));
  };

  useEffect(() => {
    refreshAuth();

    const { data: listener } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_OUT') {
        setState({ ...initialState, isLoading: false });
      } else if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
        (async () => {
          await refreshAuth();
        })();
      }
    });

    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, refreshAuth, setAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
