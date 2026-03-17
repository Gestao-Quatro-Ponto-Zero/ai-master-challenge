'use client'

import { useState, useMemo } from 'react'
import { Search, SlidersHorizontal, ChevronDown } from 'lucide-react'
import { ACCOUNTS, DEALS } from '../lib/data'
import { computeAccountScores, getScoreColor } from '../lib/scores'
import { useAuth } from '../context/AuthContext'

interface AccountsSidebarProps {
  selectedAccount: string | null
  onSelectAccount: (account: string | null) => void
}

type SortKey = 'dealSmell' | 'killerScore' | 'revenue' | 'name'

const SECTORS = Array.from(new Set(ACCOUNTS.map((a) => a.sector))).sort()
const LOCATIONS = Array.from(new Set(ACCOUNTS.map((a) => a.office_location))).sort()

export default function AccountsSidebar({
  selectedAccount,
  onSelectAccount,
}: AccountsSidebarProps) {
  const { role, agent } = useAuth()
  const isSellerView = role === 'seller' && !!agent

  const [search, setSearch] = useState('')
  const [sectorFilter, setSectorFilter] = useState<string>('')
  const [locationFilter, setLocationFilter] = useState<string>('')
  const [sortBy, setSortBy] = useState<SortKey>('dealSmell')
  const [filtersOpen, setFiltersOpen] = useState(false)

  const dealsInScope = useMemo(() => {
    if (isSellerView) {
      return DEALS.filter((d) => d.sales_agent === agent)
    }
    return DEALS
  }, [isSellerView, agent])

  const accountsWithScores = useMemo(() => {
    const accountNames = new Set(
      dealsInScope
        .map((d) => d.account)
        .filter((account): account is string => Boolean(account))
    )

    const baseAccounts = isSellerView
      ? ACCOUNTS.filter((acc) => accountNames.has(acc.account))
      : ACCOUNTS

    return baseAccounts.map((acc) => {
      const accountDeals = dealsInScope.filter((d) => d.account === acc.account)
      const activeDeals = accountDeals.filter(
        (d) => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
      )
      const scores = computeAccountScores(acc.account, dealsInScope)

      return {
        ...acc,
        ...scores,
        hasOnlyClosedDeals: accountDeals.length > 0 && activeDeals.length === 0,
      }
    })
  }, [dealsInScope, isSellerView])

  const filtered = useMemo(() => {
    let list = accountsWithScores

    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter((a) => a.account.toLowerCase().includes(q))
    }
    if (sectorFilter) {
      list = list.filter((a) => a.sector === sectorFilter)
    }
    if (locationFilter) {
      list = list.filter((a) => a.office_location === locationFilter)
    }

    list = [...list].sort((a, b) => {
      if (isSellerView && a.hasOnlyClosedDeals !== b.hasOnlyClosedDeals) {
        return Number(a.hasOnlyClosedDeals) - Number(b.hasOnlyClosedDeals)
      }

      switch (sortBy) {
        case 'dealSmell': return b.dealSmell - a.dealSmell
        case 'killerScore': return b.killerScore - a.killerScore
        case 'revenue': return b.revenue - a.revenue
        case 'name': return a.account.localeCompare(b.account)
        default: return 0
      }
    })

    return list
  }, [accountsWithScores, search, sectorFilter, locationFilter, sortBy, isSellerView])

  return (
    <aside className="dashboard-sidebar flex flex-col" aria-label="Painel de contas">
      {/* Header */}
      <div
        className="px-4 py-3 border-b sticky top-0 z-10 bg-surface"
        style={{ borderColor: 'var(--color-border)' }}
      >
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-text-main">
            Contas{' '}
            <span
              className="ml-1 text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{ background: 'rgba(175,67,50,0.1)', color: '#af4332' }}
            >
              {filtered.length}
            </span>
          </h2>
          <button
            onClick={() => setFiltersOpen(!filtersOpen)}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-text-muted transition-colors hover:text-text-main hover:bg-fade"
            aria-expanded={filtersOpen}
            aria-label="Abrir filtros"
          >
            <SlidersHorizontal size={13} />
            Filtros
            <ChevronDown
              size={12}
              className="transition-transform duration-200"
              style={{ transform: filtersOpen ? 'rotate(180deg)' : 'rotate(0)' }}
            />
          </button>
        </div>

        {isSellerView && (
          <button
            onClick={() => onSelectAccount(null)}
            disabled={!selectedAccount}
            className="w-full mb-3 text-xs font-semibold rounded-md border py-2 px-3 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            style={{
              borderColor: 'var(--color-border)',
              color: '#af4332',
              background: selectedAccount ? 'rgba(175,67,50,0.08)' : 'transparent',
            }}
            aria-label="Resetar para todas as deals ativas"
          >
            Ver todas as deals ativas
          </button>
        )}

        {/* Search */}
        <div className="relative">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
            style={{ color: 'var(--color-text-muted)' }}
          />
          <input
            type="search"
            placeholder="Buscar conta..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-md bg-fade border text-sm pl-9 pr-3 py-2 outline-none transition-all"
            style={{
              borderColor: 'var(--color-border)',
              color: 'var(--color-text)',
              fontFamily: 'var(--font-sans)',
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = '#af4332'
              e.currentTarget.style.boxShadow = '0 0 0 3px rgba(175,67,50,0.12)'
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = 'var(--color-border)'
              e.currentTarget.style.boxShadow = 'none'
            }}
            aria-label="Buscar conta"
          />
        </div>

        {/* Filters panel */}
        {filtersOpen && (
          <div className="mt-3 flex flex-col gap-2">
            <div>
              <label className="text-xs text-text-muted font-medium block mb-1">Setor</label>
              <select
                value={sectorFilter}
                onChange={(e) => setSectorFilter(e.target.value)}
                className="w-full text-xs rounded-md bg-fade border py-1.5 px-2 outline-none"
                style={{ borderColor: 'var(--color-border)', color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}
              >
                <option value="">Todos</option>
                {SECTORS.map((s) => (
                  <option key={s} value={s}>
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-text-muted font-medium block mb-1">Região</label>
              <select
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                className="w-full text-xs rounded-md bg-fade border py-1.5 px-2 outline-none"
                style={{ borderColor: 'var(--color-border)', color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}
              >
                <option value="">Todas</option>
                {LOCATIONS.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-text-muted font-medium block mb-1">Ordenar por</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortKey)}
                className="w-full text-xs rounded-md bg-fade border py-1.5 px-2 outline-none"
                style={{ borderColor: 'var(--color-border)', color: 'var(--color-text)', fontFamily: 'var(--font-sans)' }}
              >
                <option value="dealSmell">Deal Smell</option>
                <option value="killerScore">Killer Score</option>
                <option value="revenue">Revenue</option>
                <option value="name">Nome</option>
              </select>
            </div>
            {(sectorFilter || locationFilter) && (
              <button
                onClick={() => { setSectorFilter(''); setLocationFilter('') }}
                className="text-xs text-primary font-semibold text-left hover:underline"
              >
                Limpar filtros
              </button>
            )}
          </div>
        )}
      </div>

      {/* Account list */}
      <div className="flex-1 overflow-y-auto py-2">
        {filtered.length === 0 ? (
          <div className="px-4 py-8 text-center text-xs text-text-muted">
            Nenhuma conta encontrada
          </div>
        ) : (
          filtered.map((acc) => {
            const isSelected = selectedAccount === acc.account
            const isAtRisk = acc.dealSmell < 40

            return (
              <button
                key={acc.account}
                onClick={() => onSelectAccount(isSelected ? null : acc.account)}
                className="w-full text-left px-4 py-3 transition-all duration-150 border-l-2"
                style={{
                  background: isSelected ? 'rgba(175,67,50,0.06)' : 'transparent',
                  borderLeftColor: isSelected ? '#af4332' : 'transparent',
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    (e.currentTarget as HTMLButtonElement).style.background = 'rgba(0,0,0,0.025)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                  }
                }}
                aria-pressed={isSelected}
                aria-label={`Filtrar por ${acc.account}`}
              >
                {/* Row 1: name + risk dot */}
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span
                    className="text-xs font-semibold text-text-main truncate"
                    title={acc.account}
                  >
                    {acc.account}
                  </span>
                  <span
                    className="flex-shrink-0 w-2 h-2 rounded-full"
                    style={{
                      background: isAtRisk ? '#af4332' : '#25D366',
                    }}
                    title={isAtRisk ? 'Risco alto' : 'Saudável'}
                    aria-label={isAtRisk ? 'Conta em risco' : 'Conta saudável'}
                  />
                </div>

                {/* Row 2: sector • location */}
                <p className="text-xs text-text-muted mb-2 truncate">
                  {acc.sector} &bull; {acc.office_location}
                </p>

                {/* Row 3: scores + revenue + deals */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className="text-xs font-semibold"
                    style={{ color: getScoreColor(acc.dealSmell) }}
                  >
                    DS: {acc.dealSmell}
                  </span>
                  <span className="text-xs text-text-muted">·</span>
                  <span
                    className="text-xs font-semibold"
                    style={{ color: getScoreColor(acc.killerScore) }}
                  >
                    KS: {acc.killerScore}
                  </span>
                  {acc.revenue > 0 && (
                    <>
                      <span className="text-xs text-text-muted">·</span>
                      <span className="text-xs text-text-muted">
                        ${(acc.revenue / 1000).toFixed(1)}B
                      </span>
                    </>
                  )}
                  {acc.activeDeals > 0 && (
                    <>
                      <span className="text-xs text-text-muted">·</span>
                      <span className="text-xs text-text-muted">
                        {acc.activeDeals} deal{acc.activeDeals !== 1 ? 's' : ''}
                      </span>
                    </>
                  )}
                </div>
              </button>
            )
          })
        )}
      </div>
    </aside>
  )
}
