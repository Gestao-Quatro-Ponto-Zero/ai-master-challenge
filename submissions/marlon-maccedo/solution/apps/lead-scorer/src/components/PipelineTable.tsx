'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
} from '@tanstack/react-table'
import Link from 'next/link'
import type { Deal } from '@/types'
import type { PipelinePage } from '@/lib/queries'
import { ScoreBadge } from './ScoreBadge'

const col = createColumnHelper<Deal>()

const SORTABLE_COLUMNS: Partial<Record<keyof Deal, string>> = {
  score: 'Score',
  deal_stage: 'Stage',
  account: 'Conta',
  product: 'Produto',
  sales_price: 'Valor ($)',
  sales_agent: 'Agente',
  regional_office: 'Região',
  days_in_pipeline: 'Dias',
}

const columns = [
  col.accessor('score', {
    header: 'Score',
    cell: (i) => <ScoreBadge score={i.getValue()} />,
  }),
  col.accessor('opportunity_id', {
    header: 'ID',
    cell: (i) => (
      <Link href={`/pipeline/${i.getValue()}`} className="text-blue-600 hover:underline font-mono text-xs">
        {i.getValue()}
      </Link>
    ),
  }),
  col.accessor('deal_stage', {
    header: 'Stage',
    cell: (i) => (
      <span className={`text-xs font-medium px-2 py-0.5 rounded ${
        i.getValue() === 'Engaging' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'
      }`}>
        {i.getValue()}
      </span>
    ),
  }),
  col.accessor('account', { header: 'Conta' }),
  col.accessor('product', { header: 'Produto' }),
  col.accessor('sales_price', {
    header: 'Valor ($)',
    cell: (i) => i.getValue() != null ? `$${i.getValue().toLocaleString()}` : '—',
  }),
  col.accessor('sales_agent', { header: 'Agente' }),
  col.accessor('regional_office', { header: 'Região' }),
  col.accessor('days_in_pipeline', {
    header: 'Dias',
    cell: (i) => (
      <span className={i.getValue() > 200 ? 'text-red-500 font-medium' : ''}>
        {i.getValue()}
      </span>
    ),
  }),
]

export function PipelineTable({ agentFilter }: { agentFilter?: string }) {
  const [data, setData] = useState<PipelinePage | null>(null)
  const [loading, setLoading] = useState(true)
  const [sorting, setSorting] = useState<SortingState>([{ id: 'score', desc: true }])
  const [page, setPage] = useState(1)
  const [q, setQ] = useState('')
  const [stage, setStage] = useState('all')
  const [region, setRegion] = useState('all')
  const [agent, setAgent] = useState(agentFilter ?? 'all')

  // Debounce search
  const searchTimeout = useRef<ReturnType<typeof setTimeout>>(undefined)
  const [debouncedQ, setDebouncedQ] = useState('')
  useEffect(() => {
    clearTimeout(searchTimeout.current)
    searchTimeout.current = setTimeout(() => {
      setDebouncedQ(q)
      setPage(1)
    }, 300)
    return () => clearTimeout(searchTimeout.current)
  }, [q])

  // Reset page on filter/sort change
  const handleFilterChange = useCallback((setter: (v: string) => void) => (v: string) => {
    setter(v)
    setPage(1)
  }, [])

  const fetch = useCallback(async () => {
    setLoading(true)
    const sort = sorting[0]
    const params = new URLSearchParams({
      page: String(page),
      pageSize: '50',
      sort: sort?.id ?? 'score',
      order: sort?.desc ? 'desc' : 'asc',
      q: debouncedQ,
      stage,
      region,
      agent,
    })
    try {
      const res = await globalThis.fetch(`/api/pipeline?${params}`)
      const json = await res.json()
      setData(json)
    } finally {
      setLoading(false)
    }
  }, [page, sorting, debouncedQ, stage, region, agent])

  useEffect(() => { fetch() }, [fetch])

  const table = useReactTable({
    data: data?.deals ?? [],
    columns,
    state: { sorting },
    onSortingChange: (updater) => {
      setSorting(updater)
      setPage(1)
    },
    getCoreRowModel: getCoreRowModel(),
    manualSorting: true,
    manualFiltering: true,
    manualPagination: true,
  })

  const regions = data?.regions ?? []
  const agents = data?.agents ?? []
  const hot  = data?.deals.filter(d => d.score >= 70).length ?? 0
  const warm = data?.deals.filter(d => d.score >= 40 && d.score < 70).length ?? 0
  const cold = data?.deals.filter(d => d.score < 40).length ?? 0

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center gap-4 text-sm">
        {loading ? (
          <span className="text-gray-400">Carregando…</span>
        ) : (
          <>
            <span className="text-gray-500">{data?.total ?? 0} deals</span>
            <span className="text-red-600 font-medium">🔥 {hot} hot</span>
            <span className="text-yellow-600 font-medium">☀️ {warm} warm</span>
            <span className="text-blue-500 font-medium">❄️ {cold} cold</span>
          </>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="Buscar conta, agente, produto…"
          className="border border-gray-200 rounded px-3 py-1.5 text-sm w-64 focus:outline-none focus:ring-1 focus:ring-gray-400"
        />
        <Select value={stage} onChange={handleFilterChange(setStage)}
          options={['all', 'Engaging', 'Prospecting']} label="Stage" />
        <Select value={region} onChange={handleFilterChange(setRegion)}
          options={['all', ...regions]} label="Região" />
        {!agentFilter && (
          <Select value={agent} onChange={handleFilterChange(setAgent)}
            options={['all', ...agents]} label="Agente" />
        )}
      </div>

      {/* Table */}
      <div className={`overflow-x-auto rounded-lg border border-gray-200 bg-white transition-opacity ${loading ? 'opacity-50' : ''}`}>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                {hg.headers.map(h => {
                  const sortable = h.id in SORTABLE_COLUMNS
                  return (
                    <th
                      key={h.id}
                      onClick={sortable ? h.column.getToggleSortingHandler() : undefined}
                      className={`px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide select-none ${sortable ? 'cursor-pointer hover:text-gray-900' : ''}`}
                    >
                      {flexRender(h.column.columnDef.header, h.getContext())}
                      {h.column.getIsSorted() === 'asc' ? ' ↑' : h.column.getIsSorted() === 'desc' ? ' ↓' : ''}
                    </th>
                  )
                })}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading && !data ? (
              Array.from({ length: 10 }).map((_, i) => (
                <tr key={i}>
                  {columns.map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-gray-100 rounded animate-pulse w-20" />
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              table.getRowModel().rows.map(row => (
                <tr key={row.id} className="hover:bg-gray-50">
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id} className="px-4 py-3 whitespace-nowrap">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && data.totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>
            Página {data.page} de {data.totalPages} — {data.total} deals
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={data.page <= 1}
              className="px-3 py-1.5 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              ← Anterior
            </button>
            <button
              onClick={() => setPage(p => Math.min(data.totalPages, p + 1))}
              disabled={data.page >= data.totalPages}
              className="px-3 py-1.5 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Próxima →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function Select({ value, onChange, options, label }: {
  value: string
  onChange: (v: string) => void
  options: string[]
  label: string
}) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className="border border-gray-200 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-gray-400 bg-white"
    >
      <option value="all">Todos {label}s</option>
      {options.filter(o => o !== 'all').map(o => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  )
}
