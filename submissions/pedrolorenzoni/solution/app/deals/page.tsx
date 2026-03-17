'use client'

import { useState, useMemo, useEffect } from 'react'
import { ChevronDown, ChevronLeft, ChevronRight, X } from 'lucide-react'
import { useRouter } from 'next/navigation'
import DashboardNavbar from '@/components/DashboardNavbar'
import { DEALS, SALES_AGENTS, PRODUCTS } from '@/lib/data'
import { useAuth } from '@/context/AuthContext'
import { computeAllAccountRatings, getRatingColor } from '@/lib/accountRating'
import { computeAllKillScores, getKillScoreColor } from '@/lib/killScore'

// ─── Helpers ─────────────────────────────────────────────────────────────────

const PAGE_SIZE = 50

function formatValue(v: number): string {
  if (v === 0) return '—'
  return '$' + v.toLocaleString('en-US')
}

const STAGE_COLORS: Record<string, string> = {
  Won: '#16a34a',
  Lost: '#af4332',
  Engaging: '#b9915b',
  Prospecting: '#60708a',
}

// ─── Deal Detail Modal ────────────────────────────────────────────────────────

function DealDetailModal({ dealId, onClose }: { dealId: string; onClose: () => void }) {
  const deal = DEALS.find(d => d.opportunity_id === dealId)
  if (!deal) return null

  const allRatings = computeAllAccountRatings()
  const rating = deal.account ? allRatings.find(r => r.account === deal.account) : null

  const allKillScores = computeAllKillScores()
  const killScore = allKillScores.find(k => k.opportunity_id === dealId)

  const isActive = deal.deal_stage === 'Engaging' || deal.deal_stage === 'Prospecting'

  return (
    <div
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}
      onClick={onClose}
    >
      <div
        style={{ background: '#ffffff', width: '460px', maxWidth: '100vw', height: '100vh', overflowY: 'auto', padding: '32px 28px', boxShadow: '-12px 0 50px rgba(0,0,0,0.2)', position: 'relative' }}
        onClick={e => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '16px', right: '16px', background: 'rgba(0,31,53,0.06)', border: 'none', borderRadius: '8px', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#60708a' }}
          aria-label="Fechar"
        >
          <X size={16} />
        </button>

        <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#001f35', fontFamily: 'Manrope, sans-serif', marginBottom: '4px', paddingRight: '40px' }}>
          {deal.opportunity_id}
        </h2>
        <span
          style={{
            display: 'inline-block',
            background: `${STAGE_COLORS[deal.deal_stage]}18`,
            color: STAGE_COLORS[deal.deal_stage],
            borderRadius: '9999px',
            padding: '3px 10px',
            fontSize: '12px',
            fontWeight: 700,
            fontFamily: 'Inter, sans-serif',
            marginBottom: '24px',
          }}
        >
          {deal.deal_stage}
        </span>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
          {[
            { label: 'Produto', value: deal.product },
            { label: 'Agente', value: deal.sales_agent },
            { label: 'Conta', value: deal.account || '—' },
            { label: 'Valor', value: formatValue(deal.close_value) },
            { label: 'Data Engajamento', value: deal.engage_date || '—' },
            { label: 'Data Fechamento', value: deal.close_date || '—' },
          ].map(({ label, value }) => (
            <div key={label} style={{ background: '#f8f9fa', borderRadius: '10px', padding: '12px 14px' }}>
              <p style={{ fontSize: '11px', color: '#60708a', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', fontFamily: 'Inter, sans-serif', marginBottom: '2px' }}>{label}</p>
              <p style={{ fontSize: '14px', fontWeight: 600, color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>{value}</p>
            </div>
          ))}
        </div>

        {rating && (
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ fontSize: '12px', fontWeight: 700, color: '#60708a', textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'Inter, sans-serif', marginBottom: '8px' }}>
              Account Rating
            </h3>
            <div style={{ background: '#f8f9fa', borderRadius: '10px', padding: '12px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>{deal.account}</span>
              <span
                style={{
                  background: `${getRatingColor(rating.classificacao)}18`,
                  color: getRatingColor(rating.classificacao),
                  border: `1px solid ${getRatingColor(rating.classificacao)}40`,
                  borderRadius: '9999px',
                  padding: '2px 10px',
                  fontSize: '12px',
                  fontWeight: 700,
                  fontFamily: 'Inter, sans-serif',
                }}
              >
                {rating.classificacao} ({rating.rating_final})
              </span>
            </div>
          </div>
        )}

        {isActive && killScore && (
          <div>
            <h3 style={{ fontSize: '12px', fontWeight: 700, color: '#60708a', textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: 'Inter, sans-serif', marginBottom: '8px' }}>
              Kill Score
            </h3>
            <div style={{ background: '#f8f9fa', borderRadius: '10px', padding: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span
                  style={{
                    background: `${getKillScoreColor(killScore.kill_classificacao)}18`,
                    color: getKillScoreColor(killScore.kill_classificacao),
                    border: `1px solid ${getKillScoreColor(killScore.kill_classificacao)}40`,
                    borderRadius: '9999px',
                    padding: '3px 12px',
                    fontSize: '12px',
                    fontWeight: 700,
                    fontFamily: 'Inter, sans-serif',
                  }}
                >
                  {killScore.kill_classificacao} ({killScore.kill_score})
                </span>
                <span style={{ fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
                  {killScore.dias_no_pipeline}d pipeline
                </span>
              </div>
              <p style={{ fontSize: '12px', color: '#60708a', fontStyle: 'italic', fontFamily: 'Inter, sans-serif' }}>
                {killScore.recomendacao}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function DealsPage() {
  const { role, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (isAuthenticated && role === 'seller') {
      router.replace('/dashboard')
    }
  }, [isAuthenticated, role, router])

  const [filterStage, setFilterStage] = useState('Engaging')
  const [filterAgent, setFilterAgent] = useState('')
  const [filterProduct, setFilterProduct] = useState('')
  const [sortCol, setSortCol] = useState<'kill_score' | 'close_value' | 'account' | 'sales_agent' | 'deal_stage'>('kill_score')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(0)
  const [selectedDeal, setSelectedDeal] = useState<string | null>(null)

  const allRatings = useMemo(() => computeAllAccountRatings(), [])
  const ratingMap = useMemo(() => new Map(allRatings.map(r => [r.account, r])), [allRatings])

  const allKillScores = useMemo(() => computeAllKillScores(), [])
  const killMap = useMemo(() => new Map(allKillScores.map(k => [k.opportunity_id, k])), [allKillScores])

  const agents = useMemo(() => Array.from(new Set(SALES_AGENTS.map(a => a.sales_agent))).sort(), [])
  const products = useMemo(() => Array.from(new Set(PRODUCTS.map(p => p.product))).sort(), [])

  const filtered = useMemo(() => {
    let list = DEALS

    if (filterStage !== 'All' && filterStage) {
      list = list.filter(d => d.deal_stage === filterStage)
    }
    if (filterAgent) list = list.filter(d => d.sales_agent === filterAgent)
    if (filterProduct) list = list.filter(d => d.product === filterProduct)

    // Sort
    list = [...list].sort((a, b) => {
      let va: number | string = 0
      let vb: number | string = 0

      if (sortCol === 'kill_score') {
        va = killMap.get(a.opportunity_id)?.kill_score ?? -1
        vb = killMap.get(b.opportunity_id)?.kill_score ?? -1
      } else if (sortCol === 'close_value') {
        va = a.close_value
        vb = b.close_value
      } else if (sortCol === 'account') {
        va = a.account ?? ''
        vb = b.account ?? ''
      } else if (sortCol === 'sales_agent') {
        va = a.sales_agent
        vb = b.sales_agent
      } else if (sortCol === 'deal_stage') {
        va = a.deal_stage
        vb = b.deal_stage
      }

      if (typeof va === 'string' && typeof vb === 'string') {
        return sortDir === 'asc' ? va.localeCompare(vb) : vb.localeCompare(va)
      }
      return sortDir === 'asc' ? (va as number) - (vb as number) : (vb as number) - (va as number)
    })

    return list
  }, [filterStage, filterAgent, filterProduct, sortCol, sortDir, killMap])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  function handleSort(col: typeof sortCol) {
    if (col === sortCol) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortCol(col); setSortDir('desc') }
    setPage(0)
  }

  function SortIndicator({ col }: { col: typeof sortCol }) {
    if (col !== sortCol) return <span style={{ color: '#ccc', marginLeft: '4px' }}>↕</span>
    return <span style={{ color: '#b9915b', marginLeft: '4px' }}>{sortDir === 'asc' ? '↑' : '↓'}</span>
  }

  const cols: { label: string; col?: typeof sortCol; width?: string }[] = [
    { label: 'ID', col: undefined, width: '120px' },
    { label: 'Conta', col: 'account' },
    { label: 'Agente', col: 'sales_agent' },
    { label: 'Produto', col: undefined },
    { label: 'Estágio', col: 'deal_stage' },
    { label: 'Valor', col: 'close_value', width: '100px' },
    { label: 'Rating', col: undefined, width: '90px' },
    { label: 'Kill Score', col: 'kill_score', width: '110px' },
  ]

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
        <div style={{ marginBottom: '24px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: 800, color: '#001f35', fontFamily: 'Manrope, sans-serif', marginBottom: '4px' }}>
            Deals
          </h1>
          <p style={{ fontSize: '14px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
            {filtered.length.toLocaleString()} deals · Página {page + 1} de {totalPages}
          </p>
        </div>

        {/* Filter bar */}
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '20px', alignItems: 'center' }}>
          {/* Stage */}
          <div style={{ position: 'relative' }}>
            <select
              value={filterStage}
              onChange={e => { setFilterStage(e.target.value); setPage(0) }}
              style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px 36px 10px 14px', fontSize: '13px', color: '#001f35', background: '#ffffff', outline: 'none', cursor: 'pointer', fontFamily: 'Manrope, sans-serif', appearance: 'none', WebkitAppearance: 'none', minWidth: '150px' }}
              aria-label="Filtrar por estágio"
            >
              <option value="All">Todos os estágios</option>
              <option value="Won">Won</option>
              <option value="Lost">Lost</option>
              <option value="Engaging">Engaging</option>
              <option value="Prospecting">Prospecting</option>
            </select>
            <ChevronDown size={14} style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', color: '#60708a', pointerEvents: 'none' }} />
          </div>

          {/* Agent */}
          <div style={{ position: 'relative' }}>
            <select
              value={filterAgent}
              onChange={e => { setFilterAgent(e.target.value); setPage(0) }}
              style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px 36px 10px 14px', fontSize: '13px', color: filterAgent ? '#001f35' : '#60708a', background: '#ffffff', outline: 'none', cursor: 'pointer', fontFamily: 'Manrope, sans-serif', appearance: 'none', WebkitAppearance: 'none', minWidth: '180px' }}
              aria-label="Filtrar por agente"
            >
              <option value="">Todos os agentes</option>
              {agents.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
            <ChevronDown size={14} style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', color: '#60708a', pointerEvents: 'none' }} />
          </div>

          {/* Product */}
          <div style={{ position: 'relative' }}>
            <select
              value={filterProduct}
              onChange={e => { setFilterProduct(e.target.value); setPage(0) }}
              style={{ border: '1px solid #e5e7eb', borderRadius: '10px', padding: '10px 36px 10px 14px', fontSize: '13px', color: filterProduct ? '#001f35' : '#60708a', background: '#ffffff', outline: 'none', cursor: 'pointer', fontFamily: 'Manrope, sans-serif', appearance: 'none', WebkitAppearance: 'none', minWidth: '160px' }}
              aria-label="Filtrar por produto"
            >
              <option value="">Todos os produtos</option>
              {products.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
            <ChevronDown size={14} style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', color: '#60708a', pointerEvents: 'none' }} />
          </div>
        </div>

        {/* Table */}
        <div
          style={{
            background: '#ffffff',
            border: '1px solid rgba(0,31,53,0.1)',
            borderRadius: '16px',
            boxShadow: '0 0 22px rgba(0,0,0,0.07)',
            overflow: 'hidden',
          }}
        >
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid rgba(0,31,53,0.08)', background: '#fafbfc' }}>
                  {cols.map(({ label, col, width }) => (
                    <th
                      key={label}
                      onClick={col ? () => handleSort(col) : undefined}
                      style={{
                        padding: '12px 16px',
                        textAlign: 'left',
                        fontSize: '11px',
                        fontWeight: 700,
                        color: '#60708a',
                        textTransform: 'uppercase',
                        letterSpacing: '0.06em',
                        fontFamily: 'Inter, sans-serif',
                        whiteSpace: 'nowrap',
                        cursor: col ? 'pointer' : 'default',
                        userSelect: 'none',
                        width: width ?? 'auto',
                      }}
                    >
                      {label}
                      {col && <SortIndicator col={col} />}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paginated.map(deal => {
                  const rating = deal.account ? ratingMap.get(deal.account) : undefined
                  const killScore = killMap.get(deal.opportunity_id)
                  const isActive = deal.deal_stage === 'Engaging' || deal.deal_stage === 'Prospecting'

                  return (
                    <tr
                      key={deal.opportunity_id}
                      onClick={() => setSelectedDeal(deal.opportunity_id)}
                      style={{ borderBottom: '1px solid rgba(0,31,53,0.06)', cursor: 'pointer', transition: 'background 0.15s' }}
                      onMouseEnter={e => (e.currentTarget as HTMLTableRowElement).style.background = '#f8f9fa'}
                      onMouseLeave={e => (e.currentTarget as HTMLTableRowElement).style.background = 'transparent'}
                    >
                      <td style={{ padding: '10px 16px', fontSize: '12px', color: '#60708a', fontFamily: 'Inter, sans-serif', whiteSpace: 'nowrap' }}>
                        {deal.opportunity_id}
                      </td>
                      <td style={{ padding: '10px 16px', fontSize: '13px', fontWeight: 600, color: '#001f35', fontFamily: 'Manrope, sans-serif' }}>
                        {deal.account || <span style={{ color: '#bbb' }}>—</span>}
                      </td>
                      <td style={{ padding: '10px 16px', fontSize: '13px', color: '#001f35', fontFamily: 'Manrope, sans-serif', whiteSpace: 'nowrap' }}>
                        {deal.sales_agent}
                      </td>
                      <td style={{ padding: '10px 16px', fontSize: '13px', color: '#001f35', fontFamily: 'Manrope, sans-serif', whiteSpace: 'nowrap' }}>
                        {deal.product}
                      </td>
                      <td style={{ padding: '10px 16px' }}>
                        <span
                          style={{
                            background: `${STAGE_COLORS[deal.deal_stage]}18`,
                            color: STAGE_COLORS[deal.deal_stage],
                            borderRadius: '9999px',
                            padding: '3px 10px',
                            fontSize: '11px',
                            fontWeight: 700,
                            fontFamily: 'Inter, sans-serif',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {deal.deal_stage}
                        </span>
                      </td>
                      <td style={{ padding: '10px 16px', fontSize: '13px', fontWeight: 600, color: deal.close_value > 0 ? '#001f35' : '#ccc', fontFamily: 'Manrope, sans-serif', whiteSpace: 'nowrap' }}>
                        {formatValue(deal.close_value)}
                      </td>
                      <td style={{ padding: '10px 16px' }}>
                        {rating ? (
                          <span
                            style={{
                              background: `${getRatingColor(rating.classificacao)}18`,
                              color: getRatingColor(rating.classificacao),
                              border: `1px solid ${getRatingColor(rating.classificacao)}40`,
                              borderRadius: '9999px',
                              padding: '2px 8px',
                              fontSize: '11px',
                              fontWeight: 700,
                              fontFamily: 'Inter, sans-serif',
                            }}
                          >
                            {rating.classificacao}
                          </span>
                        ) : (
                          <span style={{ color: '#bbb', fontSize: '12px' }}>—</span>
                        )}
                      </td>
                      <td style={{ padding: '10px 16px' }}>
                        {isActive && killScore ? (
                          <span
                            style={{
                              background: `${getKillScoreColor(killScore.kill_classificacao)}18`,
                              color: getKillScoreColor(killScore.kill_classificacao),
                              border: `1px solid ${getKillScoreColor(killScore.kill_classificacao)}40`,
                              borderRadius: '9999px',
                              padding: '2px 8px',
                              fontSize: '11px',
                              fontWeight: 700,
                              fontFamily: 'Inter, sans-serif',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {killScore.kill_classificacao} {killScore.kill_score}
                          </span>
                        ) : (
                          <span style={{ color: '#bbb', fontSize: '12px' }}>—</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
                {paginated.length === 0 && (
                  <tr>
                    <td colSpan={8} style={{ padding: '48px 24px', textAlign: 'center', color: '#60708a', fontFamily: 'Manrope, sans-serif', fontSize: '14px' }}>
                      Nenhum deal encontrado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '14px 20px',
              borderTop: '1px solid rgba(0,31,53,0.08)',
              background: '#fafbfc',
            }}
          >
            <p style={{ fontSize: '13px', color: '#60708a', fontFamily: 'Inter, sans-serif' }}>
              {filtered.length === 0 ? '0 deals' : `${page * PAGE_SIZE + 1}–${Math.min((page + 1) * PAGE_SIZE, filtered.length)} de ${filtered.length.toLocaleString()}`}
            </p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '6px 14px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  background: '#ffffff',
                  color: page === 0 ? '#bbb' : '#001f35',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: page === 0 ? 'not-allowed' : 'pointer',
                  fontFamily: 'Manrope, sans-serif',
                }}
              >
                <ChevronLeft size={14} />
                Anterior
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '6px 14px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  background: '#ffffff',
                  color: page >= totalPages - 1 ? '#bbb' : '#001f35',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: page >= totalPages - 1 ? 'not-allowed' : 'pointer',
                  fontFamily: 'Manrope, sans-serif',
                }}
              >
                Próximo
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </div>
      </main>

      {selectedDeal && (
        <DealDetailModal dealId={selectedDeal} onClose={() => setSelectedDeal(null)} />
      )}
    </div>
  )
}
