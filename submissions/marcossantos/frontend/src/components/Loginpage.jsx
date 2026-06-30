// src/components/LoginPage.jsx
// Tela de login com visual CRM — consistente com o dashboard.

import { useState } from 'react'
import { BarChart2, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

// Credenciais de demo para facilitar o acesso
const DEMO_USERS = [
  { label: 'Admin',   email: 'admin@leadscorer.com',  password: 'admin123', role: 'admin' },
  { label: 'Manager', email: 'melanie@leadscorer.com', password: 'senha123', role: 'manager' },
  { label: 'Agent',   email: 'hayden@leadscorer.com',  password: 'senha123', role: 'agent' },
]

export default function LoginPage() {
  const { login } = useAuth()
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function fillDemo(user) {
    setEmail(user.email)
    setPassword(user.password)
    setError(null)
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--navy)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 24,
    }}>
      <div style={{ width: '100%', maxWidth: 400 }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 48, height: 48,
            background: 'var(--accent)',
            borderRadius: 10,
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 12,
          }}>
            <BarChart2 size={24} color="#fff" />
          </div>
          <h1 style={{ color: '#fff', fontSize: 20, fontWeight: 700, margin: 0 }}>
            Lead Scorer
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 4 }}>
            Sales Intelligence Platform
          </p>
        </div>

        {/* Card de login */}
        <div style={{
          background: 'var(--surface)',
          borderRadius: 12,
          padding: 28,
          boxShadow: 'var(--shadow-lg)',
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20, color: 'var(--text-primary)' }}>
            Entrar na plataforma
          </h2>

          <form onSubmit={handleSubmit}>
            {/* Email */}
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 6 }}>
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="seu@email.com"
                required
                autoFocus
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  border: `1px solid ${error ? 'var(--hot)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius)',
                  fontSize: 13,
                  fontFamily: 'var(--font)',
                  outline: 'none',
                  background: 'var(--bg)',
                  color: 'var(--text-primary)',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            {/* Senha */}
            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 6 }}>
                Senha
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  style={{
                    width: '100%',
                    padding: '9px 36px 9px 12px',
                    border: `1px solid ${error ? 'var(--hot)' : 'var(--border)'}`,
                    borderRadius: 'var(--radius)',
                    fontSize: 13,
                    fontFamily: 'var(--font)',
                    outline: 'none',
                    background: 'var(--bg)',
                    color: 'var(--text-primary)',
                    boxSizing: 'border-box',
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(p => !p)}
                  style={{
                    position: 'absolute', right: 10, top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none', border: 'none',
                    cursor: 'pointer', color: 'var(--text-muted)',
                    display: 'flex', padding: 0,
                  }}
                >
                  {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            {/* Erro */}
            {error && (
              <div style={{
                background: 'var(--hot-bg)',
                border: '1px solid var(--hot-border)',
                borderRadius: 'var(--radius)',
                padding: '8px 12px',
                fontSize: 12,
                color: 'var(--hot)',
                marginBottom: 16,
              }}>
                {error}
              </div>
            )}

            {/* Botão */}
            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '10px',
                background: loading ? '#93C5FD' : 'var(--accent)',
                color: '#fff',
                border: 'none',
                borderRadius: 'var(--radius)',
                fontSize: 13,
                fontWeight: 600,
                fontFamily: 'var(--font)',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background 0.15s',
              }}
            >
              {loading ? 'Entrando…' : 'Entrar'}
            </button>
          </form>

          {/* Demo users */}
          <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
            <p style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
              Acesso rápido (demo)
            </p>
            <div style={{ display: 'flex', gap: 6 }}>
              {DEMO_USERS.map(u => (
                <button
                  key={u.email}
                  onClick={() => fillDemo(u)}
                  style={{
                    flex: 1,
                    padding: '6px 4px',
                    background: 'var(--bg)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 11,
                    fontFamily: 'var(--font)',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={e => e.target.style.borderColor = 'var(--accent)'}
                  onMouseLeave={e => e.target.style.borderColor = 'var(--border)'}
                >
                  {u.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}