import { useState } from 'react'
import { Vendedor } from './views/Vendedor'
import { Manager  } from './views/Manager'
import { RevOps   } from './views/RevOps'

const DOT_COLOR = { vendedor: '#1D9E75', manager: '#4F8EF7', revops: '#F0A500' }

const TABS = [
  { id: 'vendedor', label: 'Vendedor' },
  { id: 'manager',  label: 'Gerente' },
  { id: 'revops',   label: 'Visão Estratégica' },
]

export default function App() {
  const [view, setView] = useState('vendedor')

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {/* ── Header ── */}
      <header style={{
        background: 'var(--bg-card)',
        borderBottom: '0.5px solid var(--border)',
        height: 56,
        display: 'flex',
        alignItems: 'center',
        padding: '0 32px',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        gap: 0,
      }}>
        {/* Logo */}
        <div style={{ marginRight: 32, flexShrink: 0, lineHeight: 1 }}>
          <div style={{
            fontSize: 14, fontWeight: 900, color: 'var(--text-primary)',
            letterSpacing: '-0.03em',
          }}>
            PULSE REVENUE
          </div>
          <div style={{
            fontSize: 10, color: 'var(--text-muted)', fontWeight: 400,
            letterSpacing: '0.08em', textTransform: 'uppercase', marginTop: 2,
          }}>
            Pipeline Intelligence
          </div>
        </div>

        {/* Tabs */}
        <nav style={{ display: 'flex', gap: 2, height: '100%', alignItems: 'stretch' }}>
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setView(t.id)}
              style={{
                display: 'flex', alignItems: 'center',
                padding: '0 18px',
                background: 'none',
                border: 'none',
                borderBottom: view === t.id
                  ? '2px solid var(--blue-accent)'
                  : '2px solid transparent',
                color: view === t.id ? 'var(--text-primary)' : 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'border-color 0.15s ease, color 0.15s ease',
              }}
            >
              <span style={{
                display: 'inline-block',
                width: 6, height: 6,
                borderRadius: '50%',
                background: DOT_COLOR[t.id],
                marginRight: 6,
                flexShrink: 0,
              }} />
              <span style={{ fontSize: 13, fontWeight: 500 }}>{t.label}</span>
            </button>
          ))}
        </nav>

        {/* Right side */}
        <div style={{
          marginLeft: 'auto', fontSize: 11,
          color: 'var(--text-muted)', fontStyle: 'italic',
        }}>
          Powered by Pulse Consultoria
        </div>
      </header>

      {/* ── Main ── */}
      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '28px 32px' }}>
        {view === 'vendedor' && <Vendedor />}
        {view === 'manager'  && <Manager  />}
        {view === 'revops'   && <RevOps   />}
      </main>
    </div>
  )
}
