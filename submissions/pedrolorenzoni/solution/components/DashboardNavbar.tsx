'use client'

import { List, Columns, LogOut, User, Shield, BarChart2, Users, Package, Briefcase, TrendingUp, Info } from 'lucide-react'
import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import Logo from './Logo'
import { useAuth } from '../context/AuthContext'
import InfoModal from './InfoModal'

interface DashboardNavbarProps {
  view?: 'list' | 'kanban'
  onViewChange?: (view: 'list' | 'kanban') => void
}

const NAV_LINKS = [
  { href: '/dashboard', label: 'Dashboard', icon: BarChart2 },
  { href: '/accounts', label: 'Contas', icon: Users },
  { href: '/products', label: 'Produtos', icon: Package },
  { href: '/team', label: 'Equipe', icon: Briefcase },
  { href: '/deals', label: 'Deals', icon: List },
  { href: '/performance', label: 'Performance', icon: TrendingUp },
]

export default function DashboardNavbar({ view, onViewChange }: DashboardNavbarProps) {
  const { role, agent, logout } = useAuth()
  const pathname = usePathname()
  const router = useRouter()
  const [showInfo, setShowInfo] = useState(false)

  const initials = agent
    ? agent
        .split(' ')
        .map((n) => n[0])
        .join('')
        .slice(0, 2)
        .toUpperCase()
    : 'AD'

  const showViewToggle = view !== undefined && onViewChange !== undefined && pathname === '/dashboard'
  const handleLogout = () => {
    logout()
    router.replace('/login')
  }

  return (
    <>
    <header
      className="fixed top-0 left-0 right-0 z-50 flex items-center"
      style={{
        height: '70px',
        background: '#0f1a45',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        padding: '0 24px',
        gap: '24px',
      }}
      role="banner"
    >
      {/* Logo */}
      <Logo size={32} variant="light" showWordmark={false} />

      {/* Primary Nav Links */}
      <nav
        className="hidden md:flex items-center gap-1"
        role="navigation"
        aria-label="Navegação principal"
        style={{ flex: 1 }}
      >
        {(role === 'seller'
          ? NAV_LINKS.filter(l => l.href !== '/deals' && l.href !== '/performance')
          : NAV_LINKS
        ).map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || (href !== '/dashboard' && pathname.startsWith(href))
          return (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all duration-200"
              style={{
                color: isActive ? '#ffffff' : 'rgba(255,255,255,0.55)',
                background: isActive ? 'rgba(255,255,255,0.1)' : 'transparent',
                borderBottom: isActive ? '2px solid #b9915b' : '2px solid transparent',
                textDecoration: 'none',
              }}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={13} />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Info button */}
      <button
        onClick={() => setShowInfo(true)}
        title="Como funciona a plataforma"
        aria-label="Informações sobre a plataforma"
        style={{
          color: 'rgba(255,255,255,0.55)',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '6px',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          transition: 'color 0.2s'
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = 'rgba(255,255,255,0.9)')}
        onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(255,255,255,0.55)')}
      >
        <Info size={18} />
      </button>

      {/* View toggle — only on dashboard */}
      {showViewToggle && (
        <div
          className="flex items-center gap-1 rounded-lg p-1"
          style={{ background: 'rgba(255,255,255,0.08)' }}
          role="group"
          aria-label="Alternância de visualização"
        >
          <button
            onClick={() => onViewChange!('list')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all duration-200"
            style={{
              background: view === 'list' ? '#ffffff' : 'transparent',
              color: view === 'list' ? '#0f1a45' : 'rgba(255,255,255,0.65)',
            }}
            aria-pressed={view === 'list'}
            title="Vista Lista"
          >
            <List size={14} />
            Lista
          </button>
          <button
            onClick={() => onViewChange!('kanban')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all duration-200"
            style={{
              background: view === 'kanban' ? '#ffffff' : 'transparent',
              color: view === 'kanban' ? '#0f1a45' : 'rgba(255,255,255,0.65)',
            }}
            aria-pressed={view === 'kanban'}
            title="Vista Kanban"
          >
            <Columns size={14} />
            Kanban
          </button>
        </div>
      )}

      {/* Spacer when no toggle */}
      {!showViewToggle && <div style={{ flex: 0 }} />}

      {/* User info + logout */}
      <div className="flex items-center gap-3" style={{ marginLeft: 'auto' }}>
        {/* Role badge */}
        <span
          className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
          style={{
            background: role === 'admin' ? 'rgba(185,145,91,0.18)' : 'rgba(255,255,255,0.08)',
            color: role === 'admin' ? '#b9915b' : 'rgba(255,255,255,0.65)',
            border: role === 'admin' ? '1px solid rgba(185,145,91,0.3)' : '1px solid rgba(255,255,255,0.1)',
          }}
        >
          {role === 'admin' ? <Shield size={12} /> : <User size={12} />}
          {role === 'admin' ? 'Admin' : agent ?? 'Vendedor'}
        </span>

        {/* Avatar */}
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold select-none"
          style={{ background: '#af4332', color: '#fff' }}
          aria-label={`Usuário: ${agent ?? 'Admin'}`}
          title={agent ?? 'Admin'}
        >
          {initials}
        </div>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors duration-200"
          style={{ color: 'rgba(255,255,255,0.55)' }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.color = '#ffffff' }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.55)' }}
          title="Sair"
          aria-label="Sair do sistema"
        >
          <LogOut size={14} />
          <span className="hidden sm:inline">Sair</span>
        </button>
      </div>
    </header>
    {showInfo && <InfoModal onClose={() => setShowInfo(false)} />}
    </>
  )
}
