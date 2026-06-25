// src/context/AuthContext.jsx
// Contexto global de autenticação.
// Gerencia token em memória (sem localStorage — mais seguro para demo).
// Disponibiliza: user, token, login(), logout(), isAuthenticated

import { createContext, useContext, useState, useCallback } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null)
  const [user,  setUser]  = useState(null)

  const login = useCallback(async (email, password) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Email ou senha incorretos.')
    }

    const data = await res.json()
    setToken(data.access_token)

    // Busca dados do usuário logado
    const meRes = await fetch('/api/auth/me', {
      headers: { Authorization: `Bearer ${data.access_token}` },
    })
    const me = await meRes.json()
    setUser(me)

    return me
  }, [])

  const logout = useCallback(async () => {
    if (token) {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {})
    }
    setToken(null)
    setUser(null)
  }, [token])

  return (
    <AuthContext.Provider value={{
      token,
      user,
      isAuthenticated: !!token,
      login,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de AuthProvider')
  return ctx
}