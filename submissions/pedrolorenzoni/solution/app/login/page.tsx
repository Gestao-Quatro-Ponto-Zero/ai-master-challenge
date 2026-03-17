'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronDown, Shield, User, ArrowRight } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { SALES_AGENTS } from '../../lib/data'
import Button from '../../components/ui/Button'

export default function LoginPage() {
  const { login } = useAuth()
  const router = useRouter()

  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const [loadingSeller, setLoadingSeller] = useState(false)
  const [loadingAdmin, setLoadingAdmin] = useState(false)

  const handleSellerLogin = async () => {
    if (!selectedAgent) return
    setLoadingSeller(true)
    // Brief delay for UX
    await new Promise((r) => setTimeout(r, 300))
    login('seller', selectedAgent)
    router.push('/dashboard')
  }

  const handleAdminLogin = async () => {
    setLoadingAdmin(true)
    await new Promise((r) => setTimeout(r, 300))
    login('admin')
    router.push('/dashboard')
  }

  return (
    <main
      className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden"
      style={{ background: '#0f1a45' }}
    >
      {/* Background decoration */}
      <div
        className="absolute inset-0 pointer-events-none"
        aria-hidden="true"
        style={{
          background:
            'radial-gradient(ellipse at 20% 50%, rgba(185,145,91,0.08) 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, rgba(175,67,50,0.06) 0%, transparent 60%)',
        }}
      />
      <div
        className="absolute bottom-0 left-0 right-0 h-px pointer-events-none"
        aria-hidden="true"
        style={{ background: 'linear-gradient(90deg, transparent 0%, #b9915b 50%, transparent 100%)' }}
      />

      {/* Card */}
      <div
        className="relative w-full max-w-sm mx-4 rounded-xl p-8"
        style={{
          background: '#ffffff',
          boxShadow: '0 24px 80px rgba(0,0,0,0.45)',
        }}
      >
        {/* Logo area */}
        <div className="flex flex-col items-center mb-8">
          {/* Wordmark logo since no PNG guaranteed */}
          <div className="flex items-center gap-2 mb-4">
            <div
              className="w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg select-none"
              style={{ background: '#af4332', color: '#ffffff' }}
              aria-hidden="true"
            >
              G4
            </div>
            <div>
              <div className="font-bold text-xl text-text-main leading-none" style={{ letterSpacing: '-0.02em' }}>
                G4 Business
              </div>
              <div className="text-xs text-text-muted font-ui mt-0.5">CRM Sales Analytics</div>
            </div>
          </div>

          {/* Gold separator */}
          <div
            className="w-16 h-px"
            style={{ background: 'linear-gradient(90deg, transparent 0%, #b9915b 50%, transparent 100%)' }}
            aria-hidden="true"
          />
        </div>

        <h1 className="text-h5 font-bold text-text-main mb-1 text-center">
          Acessar Dashboard
        </h1>
        <p className="text-xs text-text-muted text-center mb-6">
          Selecione seu perfil para continuar
        </p>

        {/* Seller login */}
        <div
          className="rounded-xl p-5 mb-4"
          style={{ background: 'var(--color-fade)', border: '1px solid var(--color-border)' }}
        >
          <div className="flex items-center gap-2 mb-3">
            <User size={15} style={{ color: '#0f1a45' }} />
            <span className="text-sm font-semibold text-text-main">Entrar como Vendedor</span>
          </div>

          <div className="relative mb-3">
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="w-full rounded-lg bg-surface border text-sm pl-3 pr-9 py-2.5 outline-none appearance-none"
              style={{
                borderColor: selectedAgent ? '#af4332' : 'var(--color-border)',
                color: selectedAgent ? 'var(--color-text)' : 'var(--color-text-muted)',
                fontFamily: 'var(--font-sans)',
                boxShadow: selectedAgent ? '0 0 0 3px rgba(175,67,50,0.12)' : 'none',
                transition: 'all 0.2s ease',
              }}
              aria-label="Selecionar vendedor"
            >
              <option value="" disabled>Selecione um vendedor...</option>
              {SALES_AGENTS.map((a) => (
                <option key={a.sales_agent} value={a.sales_agent}>
                  {a.sales_agent} — {a.regional_office}
                </option>
              ))}
            </select>
            <ChevronDown
              size={14}
              className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none"
              style={{ color: 'var(--color-text-muted)' }}
            />
          </div>

          <Button
            variant="primary"
            className="w-full justify-center"
            onClick={handleSellerLogin}
            disabled={!selectedAgent}
            loading={loadingSeller}
          >
            {!loadingSeller && <ArrowRight size={15} />}
            Entrar como Vendedor
          </Button>
        </div>

        {/* Divider */}
        <div className="flex items-center gap-3 my-4">
          <div className="flex-1 h-px" style={{ background: 'var(--color-border)' }} />
          <span className="text-xs text-text-muted">ou</span>
          <div className="flex-1 h-px" style={{ background: 'var(--color-border)' }} />
        </div>

        {/* Admin login */}
        <Button
          variant="gold"
          className="w-full justify-center"
          onClick={handleAdminLogin}
          loading={loadingAdmin}
        >
          {!loadingAdmin && <Shield size={15} />}
          Entrar como Admin
        </Button>

        <p className="text-center text-xs text-text-muted mt-5 font-ui">
          Admin vê todos os deals de todos os vendedores
        </p>
      </div>

      {/* Footer */}
      <p className="mt-6 text-xs" style={{ color: 'rgba(255,255,255,0.3)' }}>
        G4 Business &copy; 2024 — Pipeline CRM
      </p>
    </main>
  )
}
