'use client'

import { useState, useMemo } from 'react'
import { X, MapPin, Calendar, Users, DollarSign, Building2, ChevronDown } from 'lucide-react'
import DashboardNavbar from '@/components/DashboardNavbar'
import { ACCOUNTS, DEALS } from '@/lib/data'
import { computeAllAccountRatings, getRatingColor } from '@/lib/accountRating'
import { useAuth } from '@/context/AuthContext'

// ─── Helpers ────────────────────────────────────────────────────────────────

function formatRevenue(rev: number): string {
  if (rev >= 1000) return `$${(rev / 1000).toFixed(1)}B`
  return `$${rev.toFixed(0)}M`
}

function getSegment(rev: number): string {
  if (rev > 2000) return 'Enterprise'
  if (rev >= 500) return 'Mid-Market'
  return 'SMB'
}

function getSegmentColor(seg: string): string {
  if (seg === 'Enterprise') return '#0f1a45'
  if (seg === 'Mid-Market') return '#b9915b'
  return '#60708a'
}

const SECTOR_COLORS: Record<string, string> = {
  technology: '#0f1a45',
  medical: '#16a34a',
  retail: '#b9915b',
  software: '#af4332',
  finance: '#7c3aed',
  manufacturing: '#d97706',
}

function getSectorColor(sector: string): string {
  return SECTOR_COLORS[sector.toLowerCase()] ?? '#60708a'
}

// ─── Sub-components ──────────────────────────────────────────────────────────

function RatingBadge({ cls, score }: { cls: string; score: number }) {
  const color = getRatingColor(cls)
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        background: `${color}18`,
        color,
        border: `1px solid ${color}40`,
        borderRadius: '9999px',
        padding: '2px 10px',
        fontSize: '12px',
        fontWeight: 700,
        fontFamily: 'Manrope, sans-serif',
        letterSpacing: '0.02em',
      }}
    >
      {cls}
      <span style={{ fontSize: '10px', opacity: 0.75 }}>{score}</span>
    </span>
  )
}

// ─── Account Detail Modal ────────────────────────────────────────────────────

function AccountModal({ accountName, onClose }: { accountName: string; onClose: () => void }) {
  const allRatings = computeAllAccountRatings()
  const rating = allRatings.find(r => r.account === accountName) ?? null
  const account = ACCOUNTS.find(a => a.account === accountName)
  const accountDeals = DEALS.filter(d => d.account === accountName)
  const wonDeals = accountDeals.filter(d => d.deal_stage === 'Won')
  const lostDeals = accountDeals.filter(d => d.deal_stage === 'Lost')
  const activeDeals = accountDeals.filter(d => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting')

  const SIGNALS = rating ? [
    { label: 'Recência', value: rating.recencia_score, weight: '25%' },
    { label: 'Taxa de Conversão', value: rating.taxa_conversao_score, weight: '20%' },
    { label: 'Expansão', value: rating.expansao_score, weight: '20%' },
    { label: 'Recorrência', value: rating.recorrencia_score, weight: '15%' },
    { label: 'Ticket Médio', value: rating.ticket_medio_score, weight: '10%' },
    { label: 'LTV', value: rating.ltv_score, weight: '10%' },
  ] : []

  const stageColors: Record<string, string> = {
    Won: '#16a34a',
    Lost: '#af4332',
    Engaging: '#b9915b',
    Prospecting: '#60708a',
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.5)',
        zIndex: 200,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
      }}
      onClick={onClose}
      aria-modal="true"
      role="dialog"
      aria-label={`Detalhes da conta ${accountName}`}
    >
      <div
        style={{
          background: '#ffffff',
          width: '520px',
          maxWidth: '100vw',
          height: '100vh',
          overflowY: 'auto',
          padding: '32px 28px',
          boxShadow: '-12px 0 50px rgba(0,0,0,0.2)',
          position: 'relative',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Close */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            background: 'rgba(0,31,53,0.06)',
            border: 'none',
            borderRadius: '8px',
            width: '32px',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: '#60708a',
          }}
          aria-label="Fechar"
        >
          <X size={16} />
        </button>

        {/* Header */}
        <div style={{ marginBottom: '24px' }}>
          <h2
            style={{
              fontSize: '22px',
              fontWeight: 700,
              color: '#001f35',
              fontFamily: 'Manrope, sans-serif',
              marginBottom: '4px',
              paddingRight: '40px',
            }}
          >
            {accountName}
          </h2>
          {account && (
            <p style={{ fontSize: '13px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
              {account.sector} · {account.office_location}
            </p>
          )}
          {rating && (
            <div style={{ marginTop: '12px' }}>
              <RatingBadge cls={rating.classificacao} score={rating.rating_final} />
            </div>
          )}
        </div>

        {/* Account info */}
        {account && (
          <div
            style={{
              background: '#f8f9fa',
              borderRadius: '12px',
              padding: '16px',
              marginBottom: '24px',
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '12px',
            }}
          >
            {[
              { icon: DollarSign, label: 'Receita', value: formatRevenue(account.revenue) },
              { icon: Users, label: 'Funcionários', value: account.employees.toLocaleString() },
              { icon: Calendar, label: 'Fundada em', value: account.year_established },
              { icon: MapPin, label: 'Localização', value: account.office_location },
            ].map(({ icon: Icon, label, value }) => (
              <div key={label}>
                <p style={{ fontSize: '11px', color: '#60708a', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '2px', fontFamily: 'Inter, sans-serif' }}>
                  {label}
                </p>
                <p style={{ fontSize: '14px', fontWeight: 600, color: '#001f35', fontFamily: 'Manrope, sans-serif', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Icon size={13} style={{ color: '#b9915b', flexShrink: 0 }} />
                  {value}
                </p>
              </div>
            ))}
            {account.subsidiary_of && (
              <div style={{ gridColumn: '1 / -1' }}>
                <p style={{ fontSize: '11px', color: '#60708a', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '2px', fontFamily: 'Inter, sans-serif' }}>
                  Subsidiária de
                </p>
                <p style={{ fontSize: '14px', fontWeight: 600, color: '#0f1a45', fontFamily: 'Manrope, sans-serif' }}>
                  {account.subsidiary_of}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Rating breakdown */}
        {rating && (
          <div style={{ marginBottom: '24px' }}>
            <h3
              style={{
                fontSize: '13px',
                fontWeight: 700,
                color: '#60708a',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                marginBottom: '12px',
                fontFamily: 'Inter, sans-serif',
              }}
            >
              Rating Breakdown
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {SIGNALS.map(({ label, value, weight }) => (
                <div key={label}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                    <span style={{ fontSize: '13px', color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>
                      {label}
                      <span style={{ fontSize: '11px', color: '#60708a', marginLeft: '4px' }}>({weight})</span>
                    </span>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>
                      {Math.round(value)}
                    </span>
                  </div>
                  <div style={{ height: '6px', background: '#f0f0f0', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div
                      style={{
                        height: '100%',
                        width: `${Math.min(100, value)}%`,
                        background: value >= 70 ? '#16a34a' : value >= 45 ? '#b9915b' : '#af4332',
                        borderRadius: '9999px',
                        transition: 'width 0.4s ease',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <p style={{ fontSize: '12px', color: '#60708a', marginTop: '10px', fontStyle: 'italic', fontFamily: 'Inter, sans-serif' }}>
              {rating.recomendacao}
            </p>
          </div>
        )}

        {/* Deals */}
        <div>
          <h3
            style={{
              fontSize: '13px',
              fontWeight: 700,
              color: '#60708a',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              marginBottom: '12px',
              fontFamily: 'Inter, sans-serif',
            }}
          >
            Deals ({accountDeals.length})
            <span style={{ marginLeft: '8px', gap: '6px', display: 'inline-flex' }}>
              <span style={{ background: '#16a34a20', color: '#16a34a', borderRadius: '4px', padding: '1px 6px', fontSize: '11px' }}>{wonDeals.length}W</span>
              <span style={{ background: '#af433220', color: '#af4332', borderRadius: '4px', padding: '1px 6px', fontSize: '11px' }}>{lostDeals.length}L</span>
              <span style={{ background: '#b9915b20', color: '#b9915b', borderRadius: '4px', padding: '1px 6px', fontSize: '11px' }}>{activeDeals.length}A</span>
            </span>
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '300px', overflowY: 'auto' }}>
            {accountDeals.length === 0 && (
              <p style={{ fontSize: '13px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>Sem deals registrados.</p>
            )}
            {accountDeals.slice(0, 30).map(deal => (
              <div
                key={deal.opportunity_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  background: '#f8f9fa',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              >
                <div>
                  <span style={{ fontWeight: 600, color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>{deal.product}</span>
                  <span style={{ color: '#60708a', marginLeft: '6px', fontFamily: 'Inter, sans-serif' }}>{deal.sales_agent.split(' ')[0]}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {deal.close_value > 0 && (
                    <span style={{ fontWeight: 600, color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>
                      ${deal.close_value.toLocaleString()}
                    </span>
                  )}
                  <span
                    style={{
                      background: `${stageColors[deal.deal_stage]}18`,
                      color: stageColors[deal.deal_stage],
                      borderRadius: '9999px',
                      padding: '2px 8px',
                      fontWeight: 600,
                      fontFamily: 'Inter, sans-serif',
                    }}
                  >
                    {deal.deal_stage}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Account Card ────────────────────────────────────────────────────────────

function AccountCard({ account, rating, onClick }: {
  account: typeof ACCOUNTS[0]
  rating: ReturnType<typeof computeAllAccountRatings>[0] | undefined
  onClick: () => void
}) {
  const segment = getSegment(account.revenue)
  const ratingCls = rating?.classificacao ?? null
  const ratingScore = rating?.rating_final ?? null
  const sectorColor = getSectorColor(account.sector)

  return (
    <div
      onClick={onClick}
      style={{
        background: '#ffffff',
        border: `1px solid rgba(0,31,53,0.12)`,
        borderRadius: '16px',
        padding: '20px',
        boxShadow: '0 0 22px rgba(0,0,0,0.07)',
        cursor: 'pointer',
        transition: 'box-shadow 0.2s ease, border-color 0.2s ease',
        position: 'relative',
        overflow: 'hidden',
      }}
      onMouseEnter={e => {
        const el = e.currentTarget as HTMLDivElement
        el.style.boxShadow = '6px 6px 9px rgba(0,0,0,0.12)'
        el.style.borderColor = '#b9915b'
        el.style.borderWidth = '2px'
      }}
      onMouseLeave={e => {
        const el = e.currentTarget as HTMLDivElement
        el.style.boxShadow = '0 0 22px rgba(0,0,0,0.07)'
        el.style.borderColor = 'rgba(0,31,53,0.12)'
        el.style.borderWidth = '1px'
      }}
      role="button"
      aria-label={`Ver detalhes de ${account.account}`}
    >
      {/* Rating D red dot */}
      {ratingCls === 'D' && (
        <div
          style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            background: '#af4332',
            boxShadow: '0 0 6px rgba(175,67,50,0.5)',
          }}
          title="Rating D — Conta crítica"
        />
      )}

      {/* Account name */}
      <h3
        style={{
          fontSize: '16px',
          fontWeight: 700,
          color: '#001f35',
          fontFamily: 'Manrope, sans-serif',
          marginBottom: '8px',
          paddingRight: ratingCls === 'D' ? '20px' : '0',
          lineHeight: 1.3,
        }}
      >
        {account.account}
      </h3>

      {/* Sector + Segment badges */}
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '12px' }}>
        <span
          style={{
            background: `${sectorColor}18`,
            color: sectorColor,
            borderRadius: '9999px',
            padding: '3px 10px',
            fontSize: '11px',
            fontWeight: 600,
            textTransform: 'capitalize',
            fontFamily: 'Inter, sans-serif',
          }}
        >
          {account.sector}
        </span>
        <span
          style={{
            background: `${getSegmentColor(segment)}12`,
            color: getSegmentColor(segment),
            borderRadius: '9999px',
            padding: '3px 10px',
            fontSize: '11px',
            fontWeight: 600,
            fontFamily: 'Inter, sans-serif',
          }}
        >
          {segment}
        </span>
      </div>

      {/* Metadata row */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
          <MapPin size={12} style={{ flexShrink: 0, color: '#b9915b' }} />
          {account.office_location}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
          <Calendar size={12} style={{ flexShrink: 0, color: '#b9915b' }} />
          Est. {account.year_established}
        </div>
        {account.subsidiary_of && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
            <Building2 size={12} style={{ flexShrink: 0, color: '#b9915b' }} />
            Sub. of {account.subsidiary_of}
          </div>
        )}
      </div>

      {/* Footer: Revenue + Employees + Rating */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderTop: '1px solid rgba(0,31,53,0.08)',
          paddingTop: '12px',
        }}
      >
        <div>
          <p style={{ fontSize: '18px', fontWeight: 800, color: '#001f35', fontFamily: 'Manrope, sans-serif', lineHeight: 1 }}>
            {formatRevenue(account.revenue)}
          </p>
          <p style={{ fontSize: '11px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
            <Users size={10} style={{ display: 'inline', marginRight: '3px' }} />
            {account.employees.toLocaleString()} emp.
          </p>
        </div>
        {ratingCls && ratingScore !== null ? (
          <RatingBadge cls={ratingCls} score={ratingScore} />
        ) : (
          <span style={{ fontSize: '11px', color: '#aaa', fontFamily: 'Inter, sans-serif' }}>Sem rating</span>
        )}
      </div>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AccountsPage() {
  const { role, agent } = useAuth()
  const [search, setSearch] = useState('')
  const [filterSector, setFilterSector] = useState('')
  const [filterLocation, setFilterLocation] = useState('')
  const [filterRating, setFilterRating] = useState('')
  const [filterSegment, setFilterSegment] = useState('')
  const [sortBy, setSortBy] = useState<'revenue' | 'rating' | 'name'>('revenue')
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null)

  const allRatings = useMemo(() => computeAllAccountRatings(), [])
  const ratingMap = useMemo(() => new Map(allRatings.map(r => [r.account, r])), [allRatings])

  const sellerAccountNames = useMemo(() => {
    if (role !== 'seller' || !agent) return null
    return new Set(DEALS.filter(d => d.sales_agent === agent).map(d => d.account).filter(Boolean))
  }, [role, agent])

  const sectors = useMemo(() => Array.from(new Set(ACCOUNTS.map(a => a.sector))).sort(), [])
  const locations = useMemo(() => Array.from(new Set(ACCOUNTS.map(a => a.office_location))).sort(), [])

  const filtered = useMemo(() => {
    let list = [...ACCOUNTS]

    if (sellerAccountNames) {
      list = list.filter(a => sellerAccountNames.has(a.account))
    }

    if (search) {
      const q = search.toLowerCase()
      list = list.filter(a => a.account.toLowerCase().includes(q))
    }
    if (filterSector) list = list.filter(a => a.sector === filterSector)
    if (filterLocation) list = list.filter(a => a.office_location === filterLocation)
    if (filterRating) list = list.filter(a => (ratingMap.get(a.account)?.classificacao ?? 'N/A') === filterRating)
    if (filterSegment) list = list.filter(a => getSegment(a.revenue) === filterSegment)

    list.sort((a, b) => {
      if (sortBy === 'name') return a.account.localeCompare(b.account)
      if (sortBy === 'revenue') return b.revenue - a.revenue
      if (sortBy === 'rating') {
        const ra = ratingMap.get(a.account)?.rating_final ?? -1
        const rb = ratingMap.get(b.account)?.rating_final ?? -1
        return rb - ra
      }
      return 0
    })

    return list
  }, [search, filterSector, filterLocation, filterRating, filterSegment, sortBy, ratingMap, sellerAccountNames])

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      <DashboardNavbar />

      <main
        style={{
          paddingTop: '94px',
          paddingLeft: '24px',
          paddingRight: '24px',
          paddingBottom: '48px',
          maxWidth: '1400px',
          margin: '0 auto',
        }}
      >
        {/* Page header */}
        <div style={{ marginBottom: '28px' }}>
          <h1
            style={{
              fontSize: '28px',
              fontWeight: 800,
              color: '#001f35',
              fontFamily: 'Manrope, sans-serif',
              marginBottom: '4px',
            }}
          >
            Contas
          </h1>
          <p style={{ fontSize: '14px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
            {filtered.length} de {ACCOUNTS.length} contas
          </p>
        </div>

        {/* Filter bar */}
        <div
          style={{
            display: 'flex',
            gap: '12px',
            flexWrap: 'wrap',
            marginBottom: '24px',
            alignItems: 'center',
          }}
        >
          <input
            type="text"
            placeholder="Buscar conta..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              border: '1px solid #e5e7eb',
              borderRadius: '10px',
              padding: '10px 16px',
              fontSize: '14px',
              color: '#001f35',
              background: '#ffffff',
              outline: 'none',
              fontFamily: 'Manrope, sans-serif',
              minWidth: '220px',
              flex: '1 1 220px',
            }}
            aria-label="Buscar por nome de conta"
          />

          {([
            { value: filterSector, setter: setFilterSector, options: sectors, placeholder: 'Setor', aria: 'Filtrar por setor' },
            { value: filterLocation, setter: setFilterLocation, options: locations, placeholder: 'Localização', aria: 'Filtrar por localização' },
            { value: filterRating, setter: setFilterRating, options: ['A', 'B', 'C', 'D'], placeholder: 'Rating', aria: 'Filtrar por rating' },
            { value: filterSegment, setter: setFilterSegment, options: ['Enterprise', 'Mid-Market', 'SMB'], placeholder: 'Segmento', aria: 'Filtrar por segmento' },
          ] as const).map(({ value, setter, options, placeholder, aria }) => (
            <div key={placeholder} style={{ position: 'relative' }}>
              <select
                value={value}
                onChange={e => (setter as (v: string) => void)(e.target.value)}
                style={{
                  border: '1px solid #e5e7eb',
                  borderRadius: '10px',
                  padding: '10px 36px 10px 14px',
                  fontSize: '13px',
                  color: value ? '#001f35' : '#60708a',
                  background: '#ffffff',
                  outline: 'none',
                  cursor: 'pointer',
                  fontFamily: 'Manrope, sans-serif',
                  appearance: 'none',
                  WebkitAppearance: 'none',
                  minWidth: '140px',
                }}
                aria-label={aria}
              >
                <option value="">{placeholder} (todos)</option>
                {options.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
              <ChevronDown size={14} style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', color: '#60708a', pointerEvents: 'none' }} />
            </div>
          ))}

          <div style={{ position: 'relative' }}>
            <select
              value={sortBy}
              onChange={e => setSortBy(e.target.value as typeof sortBy)}
              style={{
                border: '1px solid #e5e7eb',
                borderRadius: '10px',
                padding: '10px 36px 10px 14px',
                fontSize: '13px',
                color: '#001f35',
                background: '#ffffff',
                outline: 'none',
                cursor: 'pointer',
                fontFamily: 'Manrope, sans-serif',
                appearance: 'none',
                WebkitAppearance: 'none',
                minWidth: '160px',
              }}
              aria-label="Ordenar contas"
            >
              <option value="revenue">Ordenar: Receita</option>
              <option value="rating">Ordenar: Rating</option>
              <option value="name">Ordenar: Nome</option>
            </select>
            <ChevronDown size={14} style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', color: '#60708a', pointerEvents: 'none' }} />
          </div>
        </div>

        {/* Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '20px',
          }}
        >
          {filtered.map(account => (
            <AccountCard
              key={account.account}
              account={account}
              rating={ratingMap.get(account.account)}
              onClick={() => setSelectedAccount(account.account)}
            />
          ))}
          {filtered.length === 0 && (
            <div
              style={{
                gridColumn: '1 / -1',
                textAlign: 'center',
                padding: '64px 24px',
                color: '#60708a',
                fontFamily: 'Manrope, sans-serif',
              }}
            >
              Nenhuma conta encontrada com os filtros aplicados.
            </div>
          )}
        </div>
      </main>

      {/* Modal */}
      {selectedAccount && (
        <AccountModal accountName={selectedAccount} onClose={() => setSelectedAccount(null)} />
      )}
    </div>
  )
}
