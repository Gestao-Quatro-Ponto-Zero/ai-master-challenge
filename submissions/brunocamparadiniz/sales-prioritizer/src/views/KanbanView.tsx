import { useEffect, useState } from 'react'
import { Trophy, XCircle, DollarSign, Clock } from 'lucide-react'
import { db, type PipelineRow } from '../db'
import type { ScoredDeal } from '../scoring'

function scoreBorder(score: number) {
  if (score >= 80) return 'border-l-emerald-500'
  if (score < 30)  return 'border-l-red-400'
  return 'border-l-slate-200'
}

function scoreText(score: number) {
  if (score >= 80) return 'text-emerald-600'
  if (score < 30)  return 'text-red-500'
  return 'text-slate-400'
}

function ActiveCard({ deal }: { deal: ScoredDeal }) {
  return (
    <div className={`bg-white/70 rounded-xl p-3 border-l-4 ${scoreBorder(deal.score)} mb-2 last:mb-0 shadow-sm`}
      style={{ boxShadow: '0 1px 4px 0 rgb(148 163 184 / 0.08)' }}>
      <div className="flex justify-between items-start gap-2 mb-1">
        <span className="text-slate-800 text-xs font-semibold leading-tight">{deal.account}</span>
        <span className={`text-xs font-bold flex-shrink-0 ${scoreText(deal.score)}`}>{deal.score}</span>
      </div>
      <div className="text-slate-400 text-xs">{deal.sales_agent}</div>
      <div className="flex items-center gap-3 text-xs text-slate-400 mt-1.5">
        <span className="flex items-center gap-1"><DollarSign size={10} />${deal.list_price.toLocaleString()}</span>
        {deal.stagnation.isStagnant && (
          <span className="flex items-center gap-1 text-amber-600">
            <Clock size={10} />{deal.stagnation.daysEngaging}d
          </span>
        )}
      </div>
      <div className="mt-1.5 text-xs text-slate-400 leading-tight line-clamp-2">{deal.justification}</div>
    </div>
  )
}

function HistoricalCard({ row, type }: { row: PipelineRow; type: 'Won' | 'Lost' }) {
  return (
    <div
      className={`bg-white/70 rounded-xl p-3 border-l-4 ${type === 'Won' ? 'border-l-emerald-400' : 'border-l-red-300'} mb-2 last:mb-0`}
      style={{ boxShadow: '0 1px 4px 0 rgb(148 163 184 / 0.08)' }}
    >
      <div className="text-slate-800 text-xs font-semibold leading-tight mb-1">{row.account}</div>
      <div className="text-slate-400 text-xs">{row.sales_agent}</div>
      <div className="flex items-center gap-3 text-xs text-slate-400 mt-1.5">
        <span className="flex items-center gap-1"><DollarSign size={10} />${(row.close_value || 0).toLocaleString()}</span>
        <span>{row.close_date}</span>
      </div>
    </div>
  )
}

interface ColumnProps {
  title: string
  count: number
  pipelineValue?: number
  headerColor: string
  borderColor: string
  icon?: React.ReactNode
  children: React.ReactNode
}

function KanbanColumn({ title, count, pipelineValue, headerColor, borderColor, icon, children }: ColumnProps) {
  return (
    <div className={`flex-shrink-0 w-72 glass-panel border ${borderColor} flex flex-col`}>
      <div className="px-4 pt-4 pb-3 border-b border-white/40 flex-shrink-0">
        <div className="flex items-center gap-2">
          {icon}
          <span className={`font-semibold text-sm ${headerColor}`}>{title}</span>
          <span className="ml-auto text-slate-400 text-xs bg-white/60 px-2 py-0.5 rounded-full font-medium">{count}</span>
        </div>
        {pipelineValue !== undefined && (
          <div className="text-slate-400 text-xs mt-1">
            ${(pipelineValue / 1000).toFixed(0)}k pipeline
          </div>
        )}
      </div>
      <div className="p-3 overflow-y-auto flex-1" style={{ maxHeight: '72vh' }}>
        {children}
      </div>
    </div>
  )
}

interface Props {
  activeDeals: ScoredDeal[]
  agentFilter: string
  managerFilter: string
  officeFilter: string
}

export function KanbanView({ activeDeals, agentFilter, managerFilter, officeFilter }: Props) {
  const [recentWon, setRecentWon] = useState<PipelineRow[]>([])
  const [recentLost, setRecentLost] = useState<PipelineRow[]>([])

  useEffect(() => {
    async function load() {
      let agentSet: Set<string> | null = null
      if (agentFilter) {
        agentSet = new Set([agentFilter])
      } else if (managerFilter) {
        const rows = await db.sales_teams.where('manager').equals(managerFilter).toArray()
        agentSet = new Set(rows.map((t) => t.sales_agent))
      } else if (officeFilter) {
        const rows = await db.sales_teams.where('regional_office').equals(officeFilter).toArray()
        agentSet = new Set(rows.map((t) => t.sales_agent))
      }

      const [wonRows, lostRows] = await Promise.all([
        db.pipeline.where('deal_stage').equals('Won').toArray(),
        db.pipeline.where('deal_stage').equals('Lost').toArray(),
      ])

      const applyFilter = (rows: PipelineRow[]) =>
        agentSet ? rows.filter((r) => agentSet!.has(r.sales_agent)) : rows
      const sortByDate = (rows: PipelineRow[]) =>
        rows.sort((a, b) => (b.close_date || '').localeCompare(a.close_date || ''))

      setRecentWon(sortByDate(applyFilter(wonRows)).slice(0, 12))
      setRecentLost(sortByDate(applyFilter(lostRows)).slice(0, 12))
    }
    load()
  }, [agentFilter, managerFilter, officeFilter])

  const prospecting = activeDeals.filter((d) => d.deal_stage === 'Prospecting')
  const engaging = activeDeals.filter((d) => d.deal_stage === 'Engaging')
  const pipelineOf = (deals: ScoredDeal[]) => deals.reduce((s, d) => s + d.list_price, 0)
  const empty = <p className="text-slate-300 text-xs text-center py-6">Nenhum deal</p>

  return (
    <div className="flex gap-4 overflow-x-auto pb-4 min-h-[60vh]">
      <KanbanColumn title="Prospecting" count={prospecting.length} pipelineValue={pipelineOf(prospecting)}
        headerColor="text-purple-600" borderColor="border-purple-200/60">
        {prospecting.length === 0 ? empty : prospecting.map((d) => <ActiveCard key={d.opportunity_id} deal={d} />)}
      </KanbanColumn>

      <KanbanColumn title="Engaging" count={engaging.length} pipelineValue={pipelineOf(engaging)}
        headerColor="text-blue-600" borderColor="border-blue-200/60">
        {engaging.length === 0 ? empty : engaging.map((d) => <ActiveCard key={d.opportunity_id} deal={d} />)}
      </KanbanColumn>

      <KanbanColumn title="Won" count={recentWon.length}
        headerColor="text-emerald-600" borderColor="border-emerald-200/60"
        icon={<Trophy size={14} className="text-emerald-500" />}>
        {recentWon.length === 0 ? <p className="text-slate-300 text-xs text-center py-6">Sem histórico</p>
          : recentWon.map((r) => <HistoricalCard key={r.opportunity_id} row={r} type="Won" />)}
      </KanbanColumn>

      <KanbanColumn title="Lost" count={recentLost.length}
        headerColor="text-red-500" borderColor="border-red-200/60"
        icon={<XCircle size={14} className="text-red-400" />}>
        {recentLost.length === 0 ? <p className="text-slate-300 text-xs text-center py-6">Sem histórico</p>
          : recentLost.map((r) => <HistoricalCard key={r.opportunity_id} row={r} type="Lost" />)}
      </KanbanColumn>
    </div>
  )
}
