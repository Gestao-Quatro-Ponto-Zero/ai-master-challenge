'use client'

import { useState } from 'react'
import { Menu, X, BarChart2, Users, TrendingUp, Settings } from 'lucide-react'
import Logo from './Logo'

const navLinks = [
  { label: 'Dashboard', href: '#dashboard', icon: BarChart2 },
  { label: 'Pipeline', href: '#pipeline', icon: TrendingUp },
  { label: 'Contas', href: '#accounts', icon: Users },
  { label: 'Configurações', href: '#settings', icon: Settings },
]

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <>
      <header
        className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12"
        style={{
          height: '70px',
          background: '#0f1a45',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
        }}
        role="banner"
      >
        {/* Logo */}
        <a href="#" aria-label="Ir para o início">
          <Logo size={36} variant="light" showWordmark />
        </a>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-8" aria-label="Navegação principal">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-sm font-medium transition-colors duration-200"
              style={{ color: 'rgba(255,255,255,0.75)' }}
              onMouseEnter={(e) => {
                ;(e.currentTarget as HTMLAnchorElement).style.color = '#b9915b'
              }}
              onMouseLeave={(e) => {
                ;(e.currentTarget as HTMLAnchorElement).style.color =
                  'rgba(255,255,255,0.75)'
              }}
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Desktop CTA */}
        <div className="hidden md:flex items-center gap-3">
          <span
            className="text-xs font-ui px-3 py-1 rounded-full"
            style={{
              background: 'rgba(185,145,91,0.15)',
              color: '#b9915b',
              border: '1px solid rgba(185,145,91,0.3)',
            }}
          >
            Q1 2024
          </span>
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
            style={{ background: '#af4332', color: '#fff' }}
            aria-label="Perfil do usuário"
          >
            PL
          </div>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden p-2 rounded-md"
          style={{ color: '#fff' }}
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-expanded={mobileOpen}
          aria-label={mobileOpen ? 'Fechar menu' : 'Abrir menu'}
        >
          {mobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </header>

      {/* Mobile menu overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 md:hidden"
          style={{ background: 'rgba(0,0,0,0.4)' }}
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile menu panel */}
      <nav
        className={`fixed top-0 right-0 bottom-0 z-50 w-72 flex flex-col pt-20 pb-8 px-6 md:hidden transition-transform duration-300 ${
          mobileOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        style={{ background: '#0f1a45', borderLeft: '1px solid rgba(255,255,255,0.08)' }}
        aria-label="Menu mobile"
        aria-hidden={!mobileOpen}
      >
        <button
          className="absolute top-5 right-5 p-2 rounded-md"
          style={{ color: '#fff' }}
          onClick={() => setMobileOpen(false)}
          aria-label="Fechar menu"
        >
          <X size={22} />
        </button>

        <div className="flex flex-col gap-1">
          {navLinks.map((link) => {
            const Icon = link.icon
            return (
              <a
                key={link.label}
                href={link.href}
                className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200"
                style={{ color: 'rgba(255,255,255,0.75)' }}
                onClick={() => setMobileOpen(false)}
                onMouseEnter={(e) => {
                  const el = e.currentTarget as HTMLAnchorElement
                  el.style.color = '#b9915b'
                  el.style.background = 'rgba(185,145,91,0.08)'
                }}
                onMouseLeave={(e) => {
                  const el = e.currentTarget as HTMLAnchorElement
                  el.style.color = 'rgba(255,255,255,0.75)'
                  el.style.background = 'transparent'
                }}
              >
                <Icon size={18} />
                {link.label}
              </a>
            )
          })}
        </div>

        <div className="mt-auto pt-6" style={{ borderTop: '1px solid rgba(255,255,255,0.1)' }}>
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
              style={{ background: '#af4332', color: '#fff' }}
            >
              PL
            </div>
            <div>
              <p className="text-sm font-semibold" style={{ color: '#fff' }}>Pedro Lorenzoni</p>
              <p className="text-xs" style={{ color: 'rgba(255,255,255,0.5)' }}>Sales Analyst</p>
            </div>
          </div>
        </div>
      </nav>
    </>
  )
}
