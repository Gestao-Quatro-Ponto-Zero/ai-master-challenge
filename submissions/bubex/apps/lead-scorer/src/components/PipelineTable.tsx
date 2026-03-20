'use client'

import { useState, useMemo } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
  createColumnHelper,
  type SortingState,
} from '@tanstack/react-table'
import Link from 'next/link'
import type { Deal } from '@/types'
import { ScoreBadge } from './ScoreBadge'

const col = createColumnHelper<Deal>()

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
        i.getValue() === 'Engaging'
          ? 'bg-purple-100 text-purple-700'
          : 'bg-gray-100 text-gray-600'
      }`}>
        {i.getValue()}
      </span>
    ),
  }),
  col.accessor('account', { header: 'Conta' }),
  col.accessor('product', { header: 'Produto' }),
  col.accessor('sales_price', {
    header: 'Valor ($)',
    cell: (i) => `$${i.getValue().toLocaleString()}`,
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

interface Props {
  deals: Deal[]
}

export function PipelineTable({ deals }: Props) {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'score', desc: true }])
  const [globalFilter, setGlobalFilter] = useState('')
  const [stageFilter, setStageFilter] = useState<string>('all')
  const [regionFilter, setRegionFilter] = useState<string>('all')
  const [agentFilter, setAgentFilter] = useState<string>('all')

  const regions = useMemo(() => ['all', ...Array.from(new Set(deals.map(d => d.regional_office))).sort()], [deals])
  const agents = useMemo(() => ['all', ...Array.from(new Set(deals.map(d => d.sales_agent))).sort()], [deals])

  const filtered = useMemo(() => deals.filter(d => {
    if (stageFilter !== 'all' && d.deal_stage !== stageFilter) return false
    if (regionFilter !== 'all' && d.regional_office !== regionFilter) return false
    if (agentFilter !== 'all' && d.sales_agent !== agentFilter) return false
    return true
  }), [deals, stageFilter, regionFilter, agentFilter])

  const hot = filtered.filter(d => d.score >= 70).length
  const warm = filtered.filter(d => d.score >= 40 && d.score < 70).length
  const cold = filtered.filter(d => d.score < 40).length

  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  return (
    <div className="space-y-4">
      {/* Summary chips */}
      <div className="flex items-center gap-4 text-sm">
        <span className="text-gray-500">{filtered.length} deals</span>
        <span className="text-red-600 font-medium">🔥 {hot} hot</span>
        <span className="text-yellow-600 font-medium">☀️ {warm} warm</span>
        <span className="text-blue-500 font-medium">❄️ {cold} cold</span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          value={globalFilter}
          onChange={e => setGlobalFilter(e.target.value)}
          placeholder="Buscar conta, agente, produto…"
          className="border border-gray-200 rounded px-3 py-1.5 text-sm w-64 focus:outline-none focus:ring-1 focus:ring-gray-400"
        />
        <Select value={stageFilter} onChange={setStageFilter} options={['all', 'Engaging', 'Prospecting']} label="Stage" />
        <Select value={regionFilter} onChange={setRegionFilter} options={regions} label="Região" />
        <Select value={agentFilter} onChange={setAgentFilter} options={agents} label="Agente" />
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            {table.getHeaderGroups().map(hg => (
              <tr key={hg.id}>
                {hg.headers.map(h => (
                  <th
                    key={h.id}
                    onClick={h.column.getToggleSortingHandler()}
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none hover:text-gray-900"
                  >
                    {flexRender(h.column.columnDef.header, h.getContext())}
                    {h.column.getIsSorted() === 'asc' ? ' ↑' : h.column.getIsSorted() === 'desc' ? ' ↓' : ''}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-gray-100">
            {table.getRowModel().rows.map(row => (
              <tr key={row.id} className="hover:bg-gray-50">
                {row.getVisibleCells().map(cell => (
                  <td key={cell.id} className="px-4 py-3 whitespace-nowrap">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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
