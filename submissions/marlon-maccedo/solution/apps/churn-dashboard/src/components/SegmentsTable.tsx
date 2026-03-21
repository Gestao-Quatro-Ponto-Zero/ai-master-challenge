'use client'

import { useState, useMemo } from 'react'
import type { AtRiskAccount } from '@/types'

const RISK_COLOR = (score: number) => {
  if (score >= 70) return 'bg-red-100 text-red-700'
  if (score >= 40) return 'bg-yellow-100 text-yellow-700'
  return 'bg-green-100 text-green-700'
}

const PAGE_SIZE = 20

export function SegmentsTable({ accounts }: { accounts: AtRiskAccount[] }) {
  const [search, setSearch]     = useState('')
  const [industry, setIndustry] = useState('')
  const [plan, setPlan]         = useState('')
  const [page, setPage]         = useState(0)

  const industries = useMemo(() => [...new Set(accounts.map(a => a.industry))].sort(), [accounts])
  const plans      = useMemo(() => [...new Set(accounts.map(a => a.planTier))].sort(), [accounts])

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return accounts.filter(a => {
      if (industry && a.industry !== industry) return false
      if (plan && a.planTier !== plan) return false
      if (q && !a.accountName.toLowerCase().includes(q) && !a.accountId.toLowerCase().includes(q)) return false
      return true
    })
  }, [accounts, search, industry, plan])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const pageData   = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  const handleFilter = (setter: (v: string) => void) => (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    setter(e.target.value)
    setPage(0)
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Buscar conta..."
          value={search}
          onChange={handleFilter(setSearch)}
          className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm w-48 focus:outline-none focus:ring-1 focus:ring-blue-400"
        />
        <select
          value={industry}
          onChange={handleFilter(setIndustry)}
          className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        >
          <option value="">Todas as indústrias</option>
          {industries.map(i => <option key={i} value={i}>{i}</option>)}
        </select>
        <select
          value={plan}
          onChange={handleFilter(setPlan)}
          className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-blue-400"
        >
          <option value="">Todos os planos</option>
          {plans.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        <span className="text-xs text-gray-400 self-center ml-2">
          {filtered.length} contas
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {['Conta', 'Indústria', 'País', 'Plano', 'MRR', 'Risk Score', 'Alertas'].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {pageData.map(a => (
              <tr key={a.accountId} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <p className="font-medium text-gray-800">{a.accountName}</p>
                  <p className="text-xs text-gray-400">{a.accountId}</p>
                </td>
                <td className="px-4 py-3 text-gray-600">{a.industry}</td>
                <td className="px-4 py-3 text-gray-600">{a.country}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${a.planTier === 'Enterprise' ? 'bg-purple-100 text-purple-700' : a.planTier === 'Pro' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}>
                    {a.planTier}
                  </span>
                </td>
                <td className="px-4 py-3 font-medium text-gray-800">
                  ${a.mrr.toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-bold px-2 py-1 rounded-full ${RISK_COLOR(a.riskScore)}`}>
                    {a.riskScore}/100
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {a.riskFlags.map(flag => (
                      <span key={flag} className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">
                        {flag}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
            {pageData.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400 text-sm">
                  Nenhuma conta encontrada com os filtros aplicados.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">
            Página {page + 1} de {totalPages}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 disabled:opacity-40 hover:bg-gray-50"
            >
              ← Anterior
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 disabled:opacity-40 hover:bg-gray-50"
            >
              Próxima →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
