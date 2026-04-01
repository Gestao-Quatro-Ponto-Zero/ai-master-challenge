import { useState } from 'react'

interface Props {
  onSendOtp: (email: string) => Promise<void>
  onVerifyOtp: (email: string, token: string) => Promise<void>
}

export function LoginPage({ onSendOtp, onVerifyOtp }: Props) {
  const [email, setEmail] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [token, setToken] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSendOtp(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onSendOtp(email)
      setOtpSent(true)
    } catch (err: any) {
      setError(err.message || 'Erro ao enviar código')
    } finally {
      setLoading(false)
    }
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onVerifyOtp(email, token)
    } catch (err: any) {
      setError(err.message || 'Código inválido')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-sidebar)]">
      <div className="w-full max-w-sm p-8 rounded-2xl bg-[var(--bg-secondary)] shadow-[var(--shadow-lg)]">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-[var(--g4-navy)] tracking-tight">Lead Scorer</h1>
          <div className="w-12 h-0.5 bg-[var(--g4-gold)] mx-auto mt-3 mb-2 rounded-full" />
          <p className="text-sm text-[var(--text-secondary)]">Priorize suas oportunidades</p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-[var(--danger)] text-sm">
            {error}
          </div>
        )}

        {!otpSent ? (
          <form onSubmit={handleSendOtp} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wider">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                required
                className="w-full px-4 py-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--g4-gold)] focus:ring-2 focus:ring-[var(--g4-gold)]/20 transition-all"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg bg-[var(--g4-gold)] hover:bg-[var(--accent-hover)] text-[var(--g4-deep)] font-semibold transition-all disabled:opacity-50 shadow-sm"
            >
              {loading ? 'Enviando...' : 'Enviar código'}
            </button>
          </form>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-[var(--text-secondary)] text-center">
              Código enviado para <strong className="text-[var(--text-primary)]">{email}</strong>
            </p>
            <form onSubmit={handleVerify} className="space-y-4">
              <input
                type="text"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="000000"
                required
                className="w-full px-4 py-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--g4-gold)] focus:ring-2 focus:ring-[var(--g4-gold)]/20 text-center text-2xl tracking-[0.5em] font-semibold transition-all"
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-lg bg-[var(--g4-gold)] hover:bg-[var(--accent-hover)] text-[var(--g4-deep)] font-semibold transition-all disabled:opacity-50 shadow-sm"
              >
                {loading ? 'Verificando...' : 'Verificar'}
              </button>
            </form>
            <button
              onClick={() => { setOtpSent(false); setToken('') }}
              className="w-full py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              ← Voltar
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
