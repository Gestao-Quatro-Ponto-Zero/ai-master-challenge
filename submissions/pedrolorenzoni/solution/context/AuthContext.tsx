'use client'

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

export type AuthRole = 'seller' | 'admin' | null

export interface AuthState {
  role: AuthRole
  agent: string | null
}

interface AuthContextValue extends AuthState {
  login: (role: 'seller' | 'admin', agent?: string) => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

const STORAGE_KEY = 'g4crm_auth'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState>({ role: null, agent: null })

  // Restore from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored) as AuthState
        if (parsed.role) setAuth(parsed)
      }
    } catch {
      // ignore parse errors
    }
  }, [])

  const login = useCallback((role: 'seller' | 'admin', agent?: string) => {
    const newAuth: AuthState = {
      role,
      agent: role === 'seller' ? (agent ?? null) : null,
    }
    setAuth(newAuth)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newAuth))
  }, [])

  const logout = useCallback(() => {
    setAuth({ role: null, agent: null })
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        ...auth,
        login,
        logout,
        isAuthenticated: auth.role !== null,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
