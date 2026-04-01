import {
  useState,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useCallback,
  forwardRef,
  useImperativeHandle,
  type ReactElement,
  type ReactNode,
  type RefObject,
} from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { cn } from '@/lib/utils'
import { useSellers } from '@/hooks/useSellers'
import { useDeals, useDeal, useDealBatch } from '@/hooks/useDeals'
import SellerCard from '@/components/SellerCard'
import WonValueOverTimeChart from '@/components/charts/WonValueOverTimeChart'
import ViabilityGauge from '@/components/charts/ViabilityGauge'
import type { Deal, DealStage, ScoreResult, Seller } from '@/types'

// Icons
const FeedIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 11a9 9 0 0 1 9 9" /><path d="M4 4a16 16 0 0 1 16 16" /><circle cx="5" cy="19" r="1" />
  </svg>
)

const KanbanIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="5" height="18" rx="1" /><rect x="10" y="3" width="5" height="12" rx="1" /><rect x="17" y="3" width="5" height="8" rx="1" />
  </svg>
)

const SquadIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="9" cy="7" r="3" /><path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
    <path d="M16 3.13a4 4 0 0 1 0 7.75" /><path d="M21 21v-2a4 4 0 0 0-3-3.85" />
  </svg>
)

const BackIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 12H5" /><polyline points="12 19 5 12 12 5" />
  </svg>
)

const SELLER_NAV = [
  { label: 'Feed',      targetId: 'seller-feed',      icon: <FeedIcon /> },
  { label: 'Dashboard', targetId: 'seller-dashboard', icon: <KanbanIcon /> },
  { label: 'Kanban',    targetId: 'seller-kanban',    icon: <KanbanIcon /> },
  { label: 'Squad',     targetId: 'seller-squad',     icon: <SquadIcon /> },
]

/** Subitens do Kanban (alinhados aos slides de `KanbanBoard`). */
const KANBAN_SECTIONS = ['Kanban', 'Kanban por Ação'] as const

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function SellerSidebar({
  name,
  region,
  manager,
  activeId,
  kanbanSlideIndex = 0,
  onKanbanSectionClick,
}: {
  name: string
  region: string
  manager: string
  activeId: string
  kanbanSlideIndex?: number
  onKanbanSectionClick?: (sectionIndex: number) => void
}) {
  const navigate = useNavigate()

  return (
    <div className="relative flex h-full flex-col rounded-3xl bg-white overflow-hidden shadow-[0_4px_24px_rgba(0,0,0,0.08)]">
      {/* Profile */}
      <div style={{ position: 'relative', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', borderRadius: '20px 20px 0 0', background: '#fff' }}>
        {/* Banner */}
        <div style={{ position: 'relative', height: '192px', width: '100%', backgroundColor: '#061d34', borderRadius: '20px 20px 0 0' }}>
          {/* Back button */}
          <button
            onClick={() => navigate('/home')}
            className="transition-transform duration-200 ease-out hover:scale-110"
            style={{
              position: 'absolute', top: '1rem', right: '1rem',
              background: 'rgba(255,255,255,0.12)', border: 'none', borderRadius: '8px',
              padding: '7px', display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer',
            }}
            title="Voltar"
          >
            <BackIcon />
          </button>
        </div>

        {/* Avatar */}
        <div style={{
          position: 'absolute', width: '114px', height: '114px', background: '#bb935b',
          borderRadius: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center',
          top: '135px', border: '4px solid #fff',
        }}>
          <span style={{ fontSize: '2.8rem', fontWeight: 700, color: '#fff', lineHeight: 1 }}>
            {name.charAt(0).toUpperCase()}
          </span>
        </div>

        {/* Name + role */}
        <div style={{ marginTop: '60px', fontWeight: 500, fontSize: '18px', color: '#000' }}>{name}</div>
        <div style={{ marginTop: '10px', fontWeight: 400, fontSize: '15px', color: '#78858F' }}>
          Seller · {region}
        </div>
        <div style={{ marginTop: '4px', fontWeight: 400, fontSize: '13px', color: '#aaa', marginBottom: '8px' }}>
          {manager}
        </div>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-1 px-6 pt-5">
        {SELLER_NAV.map(({ label, targetId, icon }) => {
          if (targetId === 'seller-kanban' && onKanbanSectionClick) {
            return (
              <div key={targetId} className="flex flex-col gap-1">
                <button
                  type="button"
                  onClick={() => scrollTo(targetId)}
                  className={cn(
                    'flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-colors text-left',
                    activeId === targetId
                      ? 'bg-neutral-100 text-neutral-900'
                      : 'text-neutral-400 hover:bg-neutral-50 hover:text-neutral-700',
                  )}
                >
                  {icon}
                  {label}
                </button>
                <div
                  className="ml-2 flex flex-col gap-2 border-l border-neutral-100 py-0.5 pl-3"
                  role="group"
                  aria-label="Seções do kanban"
                >
                  {KANBAN_SECTIONS.map((sectionLabel, i) => (
                    <button
                      key={sectionLabel}
                      type="button"
                      onClick={() => onKanbanSectionClick(i)}
                      className={cn(
                        'rounded-md px-2 py-1.5 text-left text-[11px] font-medium tracking-wide transition-colors',
                        kanbanSlideIndex === i && activeId === 'seller-kanban'
                          ? 'bg-neutral-100/90 text-neutral-800'
                          : 'text-neutral-400 hover:bg-neutral-50 hover:text-neutral-600',
                      )}
                    >
                      {sectionLabel}
                    </button>
                  ))}
                </div>
              </div>
            )
          }

          return (
            <button
              key={targetId}
              type="button"
              onClick={() => scrollTo(targetId)}
              className={cn(
                'flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-colors text-left',
                activeId === targetId
                  ? 'bg-neutral-100 text-neutral-900'
                  : 'text-neutral-400 hover:bg-neutral-50 hover:text-neutral-700',
              )}
            >
              {icon}
              {label}
            </button>
          )
        })}
      </nav>
    </div>
  )
}

function SectionCard({ id, label, children, contentClass }: { id: string; label?: string; children?: React.ReactNode; contentClass?: string }) {
  return (
    <div
      id={id}
      className="snap-start rounded-3xl bg-white shadow-[0_4px_24px_rgba(0,0,0,0.08)] min-h-[480px] lg:h-[calc(100svh-2rem)] overflow-hidden flex flex-col"
    >
      {label && (
        <div className="shrink-0 px-8 pt-6 pb-0">
          <span className="text-xs font-semibold tracking-widest text-neutral-400 uppercase">
            {label}
          </span>
        </div>
      )}
      <div className={cn('flex-1 min-h-0', contentClass ?? 'overflow-y-auto p-8')}>{children}</div>
    </div>
  )
}

// ─── Kanban ──────────────────────────────────────────────────────────────────

const STAGE_ICONS: Record<DealStage, ReactElement> = {
  Prospecting: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
    </svg>
  ),
  Engaging: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  ),
  Won: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  ),
  Lost: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
  ),
}

const STAGES: { stage: DealStage; label: string; accent: string }[] = [
  { stage: 'Prospecting', label: 'Prospecting', accent: '#3b82f6' },
  { stage: 'Engaging',    label: 'Engaging',    accent: '#bd9762' },
  { stage: 'Won',         label: 'Won',         accent: '#059669' },
  { stage: 'Lost',        label: 'Lost',        accent: '#e11d48' },
]

const ACTION_DETAIL_LABELS: Record<string, string> = {
  your_capacity: 'Sua capacidade',
  urgency_level: 'Nível de urgência',
  days_in_pipeline: 'Dias no pipeline',
  your_context: 'Seu contexto',
  target_context: 'Contexto do vendedor alvo',
  target_seller: 'Vendedor sugerido',
  transfer_level: 'Nível de transferência',
  hierarchy_explanation: 'Critério de hierarquia',
  why_this_helps: 'Por que ajuda',
  why_consider: 'Por que considerar',
  why_discard: 'Por que descartar',
  opportunity_cost: 'Custo de oportunidade',
  expected_impact: 'Impacto esperado',
  status: 'Status',
}

const CAPACITY_PT: Record<string, string> = {
  good: 'Boa',
  limited: 'Limitada',
  insuficiente: 'Insuficiente',
  adequada: 'Adequada',
  moderada: 'Moderada',
}

const URGENCY_PT: Record<string, string> = {
  critical: 'Crítica',
  high: 'Alta',
  medium: 'Média',
  low: 'Baixa',
}

const STATUS_PT: Record<string, string> = {
  on_track: 'No caminho certo',
  needs_attention_soon: 'Precisa de atenção em breve',
}

function humanizeDetailKey(key: string): string {
  if (ACTION_DETAIL_LABELS[key]) return ACTION_DETAIL_LABELS[key]
  return key
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ')
}

function formatDetailScalar(key: string, value: string | number | boolean): string {
  if (typeof value === 'boolean') return value ? 'Sim' : 'Não'
  if (typeof value === 'number') return String(value)
  const s = value
  if (key === 'your_capacity') return CAPACITY_PT[s] ?? s
  if (key === 'urgency_level') return URGENCY_PT[s] ?? s
  if (key === 'status') return STATUS_PT[s] ?? s
  if (key.endsWith('capacity_assessment')) return CAPACITY_PT[s] ?? s
  return s
}

function DetailValueContent({ entryKey, value }: { entryKey: string; value: unknown }): ReactNode {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return formatDetailScalar(entryKey, value as string | number | boolean)
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return '—'
    if (value.every((x) => typeof x === 'string')) {
      return (
        <ul className="list-disc space-y-1 pl-4 text-sm leading-relaxed text-neutral-800">
          {(value as string[]).map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ul>
      )
    }
    return (
      <ul className="list-disc space-y-1 pl-4 text-sm text-neutral-800">
        {value.map((x, i) => (
          <li key={i}>{typeof x === 'string' ? x : JSON.stringify(x)}</li>
        ))}
      </ul>
    )
  }
  if (typeof value === 'object') {
    const o = value as Record<string, unknown>
    return (
      <div className="mt-1 space-y-2 rounded-lg border border-neutral-100 bg-neutral-50/80 p-2.5">
        {Object.entries(o).map(([k, v]) => (
          <div key={k}>
            <p className="text-[10px] font-semibold uppercase tracking-wide text-neutral-400">{humanizeDetailKey(k)}</p>
            <div className="mt-0.5 text-sm text-neutral-800">
              <DetailValueContent entryKey={k} value={v} />
            </div>
          </div>
        ))}
      </div>
    )
  }
  return String(value)
}

/** Conteúdo do objeto `action.details`: passos numerados + demais campos em texto (sem JSON bruto). */
function ActionDetailsReadout({ details }: { details?: Record<string, unknown> }) {
  if (!details || Object.keys(details).length === 0) {
    return <span className="text-sm text-neutral-400">—</span>
  }
  const rawSteps = details.action_steps
  const steps = Array.isArray(rawSteps) ? rawSteps : null
  const rest = Object.fromEntries(Object.entries(details).filter(([k]) => k !== 'action_steps'))
  const hasSteps = steps != null && steps.length > 0
  const hasRest = Object.keys(rest).length > 0
  if (!hasSteps && !hasRest) {
    return <span className="text-sm text-neutral-400">—</span>
  }

  return (
    <div className="flex flex-col gap-3">
      {hasSteps ? (
        <ol className="list-decimal space-y-1.5 pl-4 text-sm leading-relaxed text-neutral-800">
          {steps!.map((s, i) => (
            <li key={i}>{typeof s === 'string' ? s : JSON.stringify(s)}</li>
          ))}
        </ol>
      ) : null}
      {hasRest ? (
        <dl className="space-y-2.5">
          {Object.entries(rest).map(([k, v]) => (
            <div key={k}>
              <dt className="text-[10px] font-semibold uppercase tracking-wide text-neutral-400">{humanizeDetailKey(k)}</dt>
              <dd className="mt-1 text-neutral-800">
                <DetailValueContent entryKey={k} value={v} />
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
    </div>
  )
}

function ActionFieldSkeleton() {
  return (
    <div className="flex flex-col gap-2 pt-0.5">
      <div className="h-3.5 w-full rounded bg-neutral-100 animate-pulse" />
      <div className="h-3.5 w-[85%] rounded bg-neutral-100 animate-pulse" />
      <div className="h-3.5 w-[70%] rounded bg-neutral-100 animate-pulse" />
    </div>
  )
}

/** Painel lateral com campos equivalentes a `deal_info` (GET /deals/:id). */
function DealInfoPopup({ deal, onClose }: { deal: Deal; onClose: () => void }) {
  const { data: scoreDetail, isLoading: actionLoading, isError: actionError } = useDeal(deal.opportunity_id)
  const action = scoreDetail?.action

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prev
    }
  }, [])

  const fmtMoney = (n: number) =>
    n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

  const suggestionBadge: ReactNode =
    deal.action != null ? (
      <span
        className={cn(
          'inline-flex max-w-full items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold',
          ACTION_COLORS[deal.action]?.bg ?? 'bg-neutral-50',
          ACTION_COLORS[deal.action]?.text ?? 'text-neutral-700',
          ACTION_COLORS[deal.action]?.border ?? 'border-neutral-200',
        )}
      >
        <span aria-hidden>{ACTION_ICON[deal.action] ?? ''}</span>
        <span className="truncate">
          {FEED_ACTIONS.find((a) => a.key === deal.action)?.label ?? deal.action.replace(/_/g, ' ')}
        </span>
      </span>
    ) : (
      <span className="text-sm text-neutral-400">—</span>
    )

  const actionRows = useMemo((): { label: string; value: string | ReactNode }[] => {
    if (actionLoading) {
      return [
        { label: 'Mensagem', value: <ActionFieldSkeleton /> },
        { label: 'Motivo', value: <ActionFieldSkeleton /> },
        { label: 'Detalhes', value: <ActionFieldSkeleton /> },
      ]
    }
    const msgList = (deal.message && deal.message.trim()) || ''
    if (actionError || !action) {
      return [
        { label: 'Mensagem', value: msgList || '—' },
        { label: 'Motivo', value: actionError ? 'Não foi possível carregar.' : '—' },
        { label: 'Detalhes', value: '—' },
      ]
    }
    const messageText = (action.message && action.message.trim()) || msgList || '—'
    const reasonText = (action.reason && action.reason.trim()) || '—'
    return [
      { label: 'Mensagem', value: messageText },
      { label: 'Motivo', value: reasonText },
      { label: 'Detalhes', value: <ActionDetailsReadout details={action.details} /> },
    ]
  }, [action, actionError, actionLoading, deal.message])

  const rows: { label: string; value: string | ReactNode }[] = [
    { label: 'Conta', value: deal.account || '—' },
    { label: 'Produto', value: deal.product || '—' },
    { label: 'Vendedor', value: deal.sales_agent || '—' },
    { label: 'Região', value: deal.regional_office || '—' },
    { label: 'Estágio', value: deal.deal_stage || '—' },
    { label: 'Valor (estimativa: Histórico vendedor × produto)', value: fmtMoney(deal.close_value) },
    { label: 'Dias no pipeline', value: String(deal.days_in_pipeline) },
    { label: 'Deal ID', value: deal.opportunity_id || '—' },
    { label: 'Sugestão', value: suggestionBadge },
    ...actionRows,
  ]

  return (
    <div
      className="fixed inset-0 z-[100] flex flex-row"
      role="dialog"
      aria-modal="true"
      aria-labelledby="deal-info-popup-title"
    >
      <button
        type="button"
        className="min-h-0 min-w-0 flex-1 cursor-default bg-black/40 transition-opacity"
        onClick={onClose}
        aria-label="Fechar painel"
      />
      <div className="flex h-full w-[min(100%,22rem)] shrink-0 flex-col border-l border-neutral-200 bg-white shadow-[-4px_0_24px_rgba(0,0,0,0.08)]">
        <div className="flex shrink-0 items-center justify-between gap-3 border-b border-neutral-100 px-4 py-3">
          <h2 id="deal-info-popup-title" className="text-sm font-semibold text-neutral-900">
            Detalhes do deal
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-neutral-400 transition-colors hover:bg-neutral-100 hover:text-neutral-700"
            aria-label="Fechar"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
        <div className="flex min-h-0 flex-1 flex-col gap-0 overflow-y-auto overscroll-y-contain px-4 py-4">
          {rows.map((row) => (
            <div
              key={row.label}
              className="border-b border-neutral-100 py-3 last:border-b-0"
            >
              <p className="text-[10px] font-semibold uppercase tracking-wide text-neutral-400">{row.label}</p>
              <div className="mt-1 text-sm text-neutral-900 break-words">
                {typeof row.value === 'string' ? <p>{row.value}</p> : row.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function DealCard({
  deal,
  showAction,
  onVerDetalhes,
}: {
  deal: Deal
  showAction?: boolean
  onVerDetalhes?: (deal: Deal) => void
}) {
  if (showAction === undefined) showAction = deal.deal_stage === 'Prospecting' || deal.deal_stage === 'Engaging'

  return (
    <div className="rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-4 flex flex-col gap-3">
      {/* Account + product + Ver detalhes */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-neutral-900 leading-snug truncate">{deal.account}</p>
          <p className="text-xs text-neutral-500 mt-0.5 truncate">{deal.product}</p>
        </div>
        {onVerDetalhes ? (
          <button
            type="button"
            onClick={() => onVerDetalhes(deal)}
            className="shrink-0 rounded-lg border border-neutral-200/90 bg-neutral-50/80 px-2 py-1 text-[10px] font-medium text-neutral-600 transition-colors hover:bg-neutral-100 hover:text-neutral-900"
          >
            Ver detalhes
          </button>
        ) : null}
      </div>

      {/* Value + days */}
      <div className="flex items-center justify-between gap-2">
        {deal.deal_stage === 'Won' ? (
          <span className="text-xs font-semibold tabular-nums text-emerald-600 bg-emerald-50 rounded-full px-2 py-0.5">
            {deal.close_value.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
          </span>
        ) : deal.deal_stage === 'Lost' ? (
          <span className="text-xs font-semibold tabular-nums text-rose-600 bg-rose-50 rounded-full px-2 py-0.5">
            {deal.close_value.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
          </span>
        ) : !showAction ? (
          <span className={cn('self-start shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold', STAGE_COLORS[deal.deal_stage])}>
            {deal.deal_stage}
          </span>
        ) : null}
        <span className="text-[11px] text-neutral-400 tabular-nums ml-auto">{deal.days_in_pipeline}d</span>
      </div>

      {/* Score bar */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-1.5 rounded-full bg-neutral-100 overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{ width: `${Math.min(deal.score, 100)}%`, backgroundColor: '#bd9762' }}
          />
        </div>
        <span className="text-[10px] tabular-nums text-neutral-400 w-6 text-right">{Math.round(deal.score)}</span>
      </div>

      {/* Action badge — Kanban: neutro; emoji mantido */}
      {showAction && deal.action && (
        <span className="self-start shrink-0 rounded-full border border-neutral-200/90 bg-neutral-50 px-2 py-0.5 text-[10px] font-medium text-neutral-600">
          {ACTION_ICON[deal.action]} {deal.action.replace(/_/g, ' ')}
        </span>
      )}
    </div>
  )
}

const ACTIONS: { key: string; label: string; accent: string }[] = [
  { key: 'PUSH_HARD',         label: 'Push Hard',         accent: '#1d4ed8' },
  { key: 'ACCELERATE',        label: 'Accelerate',        accent: '#60a5fa' },
  { key: 'MONITOR',           label: 'Monitor',           accent: '#9ca3af' },
  { key: 'INVESTIGATE',       label: 'Investigate',       accent: '#ea580c' },
  { key: 'TRANSFER',          label: 'Transfer',          accent: '#7e22ce' },
  { key: 'CONSIDER_TRANSFER', label: 'Consider Transfer', accent: '#a855f7' },
  { key: 'DISCARD',           label: 'Discard',           accent: '#e11d48' },
  { key: 'RE_QUALIFY',        label: 'Re-qualify',        accent: '#ca8a04' },
]

function KanbanColumn({
  label,
  accent,
  stage,
  actionKey,
  deals,
  showAction = true,
  onVerDetalhes,
}: {
  label: string
  accent: string
  stage?: DealStage
  actionKey?: string
  deals: Deal[]
  showAction?: boolean
  /** Abre o painel lateral com dados do deal (Kanban por estágio e por ação). */
  onVerDetalhes?: (deal: Deal) => void
}) {
  return (
    <div className="flex flex-col flex-1 min-w-[220px] h-full">
      <div className="shrink-0 flex items-center gap-2.5 mb-3">
        {stage ? (
          <span className="shrink-0 flex items-center justify-center w-6 h-6 rounded-lg" style={{ backgroundColor: '#bd976220', color: '#bd9762' }}>
            {STAGE_ICONS[stage]}
          </span>
        ) : actionKey ? (
          <span className="w-full rounded-full border border-neutral-200/90 bg-neutral-50 px-2 py-1 text-left text-xs font-medium text-neutral-600">
            {ACTION_ICON[actionKey]} {label}
          </span>
        ) : (
          <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: accent }} />
        )}
        {!actionKey && <span className="text-sm font-semibold text-neutral-900">{label}</span>}
        <span className="ml-auto text-xs font-semibold tabular-nums text-neutral-400 bg-neutral-100 rounded-full px-2 py-0.5">
          {deals.length}
        </span>
      </div>
      <div className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-3 pr-1">
        {deals.length === 0 ? (
          <div className="flex items-center justify-center h-24 rounded-2xl border border-dashed border-neutral-200 text-xs text-neutral-400">
            Nenhum deal
          </div>
        ) : (
          deals.map((d) => (
            <DealCard key={d.opportunity_id} deal={d} showAction={showAction} onVerDetalhes={onVerDetalhes} />
          ))
        )}
      </div>
    </div>
  )
}

const SLIDE_LABELS = [
  { title: 'Kanban', subtitle: 'Seus deals por estágio' },
  { title: 'Kanban por Ação', subtitle: 'Seus deals por recomendação' },
]

type KanbanBoardRef = {
  scrollToSlide: (index: number) => void
}

const KanbanBoard = forwardRef<
  KanbanBoardRef,
  { sellerName: string; onSlideIndexChange?: (index: number) => void }
>(function KanbanBoard({ sellerName, onSlideIndexChange }, ref) {
  const { data: deals = [], isLoading } = useDeals({ sales_agent: sellerName, all_stages: true })
  const [slideIndex, setSlideIndex] = useState(0)
  const [dealInfoDeal, setDealInfoDeal] = useState<Deal | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const maxSlide = SLIDE_LABELS.length - 1

  const scrollToSlide = useCallback(
    (rawIndex: number) => {
      const el = scrollRef.current
      if (!el) return
      const i = Math.max(0, Math.min(rawIndex, maxSlide))
      el.scrollTo({ left: i * el.clientWidth, behavior: 'smooth' })
      setSlideIndex(i)
      onSlideIndexChange?.(i)
    },
    [maxSlide, onSlideIndexChange],
  )

  useImperativeHandle(
    ref,
    () => ({
      scrollToSlide: (i: number) => scrollToSlide(i),
    }),
    [scrollToSlide],
  )

  const handleScroll = () => {
    const el = scrollRef.current
    if (!el) return
    const i = Math.max(0, Math.min(Math.round(el.scrollLeft / (el.clientWidth || 1)), maxSlide))
    setSlideIndex(i)
    onSlideIndexChange?.(i)
  }

  return (
    <div className="flex flex-col h-full px-8 pt-6 pb-6 min-h-0">
      {/* Header: title + dot nav */}
      <div className="shrink-0 mb-6 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-neutral-900 tracking-tight">
            {SLIDE_LABELS[slideIndex].title}
          </h2>
          <p className="text-sm text-neutral-500 mt-0.5">{SLIDE_LABELS[slideIndex].subtitle}</p>
        </div>
        <div className="flex items-center gap-2 pt-1">
          {SLIDE_LABELS.map((_, i) => (
            <button
              key={i}
              type="button"
              onClick={() => scrollToSlide(i)}
              className="transition-all duration-200"
              style={{
                width: slideIndex === i ? '20px' : '8px',
                height: '8px',
                borderRadius: '9999px',
                backgroundColor: slideIndex === i ? '#bd9762' : '#d4d4d4',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
              }}
            />
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex gap-4 flex-1">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="flex-1 animate-pulse rounded-2xl bg-neutral-100" />
          ))}
        </div>
      ) : (
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="flex-1 min-h-0 flex snap-x snap-mandatory overflow-x-auto"
        >
          {/* Slide 1 — por estágio */}
          <div className="min-w-full w-full shrink-0 snap-start flex gap-4 min-h-0 overflow-x-auto pb-1">
            {STAGES.map(({ stage, label, accent }) => (
              <KanbanColumn
                key={stage}
                label={label}
                accent={accent}
                stage={stage}
                deals={deals.filter((d) => d.deal_stage === stage)}
                onVerDetalhes={(d) => setDealInfoDeal(d)}
              />
            ))}
          </div>

          {/* Slide 2 — por ação */}
          <div className="min-w-full w-full shrink-0 snap-start flex gap-4 min-h-0 overflow-x-auto pb-1">
            {ACTIONS.map(({ key, label, accent }) => (
              <KanbanColumn
                key={key}
                label={label}
                accent={accent}
                actionKey={key}
                deals={deals.filter((d) => d.action === key)}
                showAction={false}
                onVerDetalhes={(d) => setDealInfoDeal(d)}
              />
            ))}
          </div>
        </div>
      )}

      {dealInfoDeal ? (
        <DealInfoPopup deal={dealInfoDeal} onClose={() => setDealInfoDeal(null)} />
      ) : null}
    </div>
  )
})

// =============================================================================
// DASHBOARD RIGHT CARD
// =============================================================================

const CompanyIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
    <polyline points="9 22 9 12 15 12 15 22"/>
  </svg>
)

function DashboardRightCard({ sellerName, seller }: { sellerName: string; seller?: Seller }) {
  const { data: deals = [] } = useDeals({ sales_agent: sellerName, all_stages: true })

  const topDeals = [...deals].filter(d => d.action !== null && d.account).sort((a, b) => b.score - a.score).slice(0, 3)

  const openValue = deals
    .filter(d => d.deal_stage === 'Prospecting' || d.deal_stage === 'Engaging')
    .reduce((sum, d) => sum + (d.close_value ?? 0), 0)

  const openValueProspecting = deals
    .filter(d => d.deal_stage === 'Prospecting')
    .reduce((sum, d) => sum + (d.close_value ?? 0), 0)

  const openValueEngaging = deals
    .filter(d => d.deal_stage === 'Engaging')
    .reduce((sum, d) => sum + (d.close_value ?? 0), 0)


  return (
    <div className="flex flex-col gap-5 h-full p-5">
      {/* Estimativa de valor em aberto */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-5 flex flex-col gap-3 h-full">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-xl bg-[#bd9762]/10 text-[#bd9762] flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold tracking-tight tabular-nums text-neutral-900">
              {openValue.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-neutral-700">Estimativa em aberto (Prospecting + Engaging)</p>
            <p className="text-xs text-neutral-400 mt-0.5">Soma da estimativa em aberto dos deals em Prospecting + Engaging</p>
          </div>
        </div>
      </div>

      {/* Estimativa Prospecting */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-5 flex flex-col gap-3 h-full">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-xl bg-[#bd9762]/10 text-[#bd9762] flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold tracking-tight tabular-nums text-neutral-900">
              {openValueProspecting.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-neutral-700">Estimativa em aberto (Prospecting)</p>
            <p className="text-xs text-neutral-400 mt-0.5">Soma do ticket médio histórico do vendedor × produto</p>
          </div>
        </div>
      </div>

      {/* Estimativa Engaging */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-5 flex flex-col gap-3 h-full">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-xl bg-[#bd9762]/10 text-[#bd9762] flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
            </div>
          </div>
          <div>
            <p className="text-2xl font-bold tracking-tight tabular-nums text-neutral-900">
              {openValueEngaging.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-neutral-700">Estimativa em aberto (Engaging)</p>
            <p className="text-xs text-neutral-400 mt-0.5">Soma do ticket médio histórico do vendedor × produto</p>
          </div>
        </div>
      </div>

      {/* Viability gauge */}
      {seller && <ViabilityGauge seller={seller} />}

      <div className="border-t border-neutral-100" />

      {/* Mini-cards: top 3 deals */}
      <div className="flex flex-col gap-2">
        <div className="mb-1 flex items-center justify-between gap-3">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-neutral-400">
            Deals prioritários
          </p>
          <button
            type="button"
            onClick={() => scrollTo('seller-kanban')}
            className="shrink-0 text-[9px] font-medium tracking-wide text-neutral-400 transition-colors hover:text-[#bd9762]"
          >
            Ver prioritários →
          </button>
        </div>
        {topDeals.length > 0 ? (
          topDeals.map((deal) => (
            <button
              key={deal.opportunity_id}
              type="button"
              onClick={() => scrollTo('seller-kanban')}
              className="flex w-full items-center gap-3 rounded-2xl border border-neutral-100 bg-white p-3 text-left shadow-[0_4px_16px_rgba(0,0,0,0.08)] transition-all duration-200 hover:border-neutral-200/45 hover:bg-neutral-50/90 hover:shadow-[0_8px_22px_rgba(0,0,0,0.11)] active:scale-[0.99] active:shadow-[0_2px_10px_rgba(0,0,0,0.06)]"
            >
              <div className="w-7 h-7 rounded-lg bg-[#bd9762]/10 text-[#bd9762] flex items-center justify-center shrink-0">
                <CompanyIcon />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-neutral-900 truncate">{deal.account}</p>
                <p className="text-[10px] text-neutral-400 font-mono">{deal.opportunity_id}</p>
              </div>
              <span
                className={cn(
                  'shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold',
                  deal.action != null
                    ? [
                        ACTION_COLORS[deal.action]?.bg ?? 'bg-neutral-50',
                        ACTION_COLORS[deal.action]?.text ?? 'text-neutral-500',
                        ACTION_COLORS[deal.action]?.border ?? 'border-neutral-200',
                      ]
                    : 'bg-neutral-50 text-neutral-500 border-neutral-200',
                )}
              >
                {deal.action != null ? (
                  <>
                    {ACTION_ICON[deal.action]} {deal.action.replace(/_/g, ' ')}
                  </>
                ) : (
                  '—'
                )}
              </span>
            </button>
          ))
        ) : (
          <div className="rounded-xl border border-neutral-100 bg-neutral-50 h-20 flex items-center justify-center">
            <p className="text-xs text-neutral-400">Nenhum deal</p>
          </div>
        )}
        <div className="border-t border-neutral-100" aria-hidden />
      </div>

    </div>
  )
}

// =============================================================================
// FEED — sub-components
// =============================================================================


const STAGE_COLORS: Record<DealStage, string> = {
  Prospecting: 'bg-blue-50 text-blue-700',
  Engaging:    'bg-amber-50 text-amber-700',
  Won:         'bg-green-50 text-green-700',
  Lost:        'bg-neutral-100 text-neutral-500',
}

function DealInfoCard({ deal, badgeRef }: { deal: Deal; badgeRef?: RefObject<HTMLSpanElement | null> }) {
  return (
    <div className="w-[500px] h-full shrink-0 rounded-2xl border border-neutral-100 bg-neutral-50/50 pt-6 px-6 pb-0 flex flex-col gap-5 overflow-y-auto">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#bd9762]/10 text-[#bd9762] flex items-center justify-center shrink-0">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
          </div>
          <div className="min-w-0">
            {deal.account
              ? <h3 className="text-base font-semibold text-neutral-900 truncate">{deal.account}</h3>
              : <h3 className="text-base italic text-neutral-400 truncate">Sem nome</h3>
            }
            <p className="text-[10px] text-neutral-400 font-mono truncate mt-0.5">aberto há {deal.days_in_pipeline} dias</p>
          </div>
        </div>
        <span className={cn('shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium', STAGE_COLORS[deal.deal_stage])}>
          {deal.deal_stage}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        {([
          { label: 'Vendedor', value: deal.sales_agent },
          { label: 'Região',   value: deal.regional_office },
          { label: 'Produto',  value: deal.product },
          { label: 'Pipeline', value: `${deal.days_in_pipeline} dias` },
        ] as { label: string; value: string }[]).map(({ label, value }) => (
          <div key={label} className="rounded-xl bg-neutral-50 p-3">
            <p className="text-[10px] text-neutral-400 uppercase tracking-wide">{label}</p>
            <p className="text-sm font-medium text-neutral-800 mt-0.5 truncate">{value}</p>
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wide">Sugestão</span>
          {deal.action && (
            <span
              ref={badgeRef}
              className={cn(
                'rounded-full px-2.5 py-1 text-[11px] font-semibold',
                ACTION_COLORS[deal.action]?.bg ?? 'bg-neutral-50',
                ACTION_COLORS[deal.action]?.text ?? 'text-neutral-500',
                ACTION_COLORS[deal.action]?.border ?? 'border-neutral-200',
                'border',
              )}
            >
              {ACTION_ICON[deal.action]}
            </span>
          )}
        </div>
        <div className="border-t border-neutral-100 pt-3 flex items-center justify-between">
          <span className="text-xs font-semibold text-neutral-400 uppercase tracking-wide">Score</span>
          <span className="text-2xl font-bold text-neutral-900">{Math.round(deal.score)}</span>
        </div>
        <div className="h-[180px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={[
                { name: 'Urgência',      value: Math.round(deal.urgency),     desc: 'Tempo parado no pipeline vs. média do produto' },
                { name: 'Probabilidade', value: Math.round(deal.probability), desc: 'Win rate do vendedor ponderado pelo estágio' },
                { name: 'Valor',         value: Math.round(deal.value),       desc: 'Ticket estimado vs. média histórica do portfólio' },
                { name: 'Viabilidade',   value: Math.round(deal.viability),   desc: 'Índice geral de saúde e contexto do deal' },
              ]}
              barCategoryGap="18%"
              margin={{ top: 4, right: 8, left: 4, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#525252' }} tickLine={false} axisLine={{ stroke: '#e5e7eb' }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#525252' }} tickLine={false} axisLine={false} width={28} />
              <Tooltip
                cursor={{ fill: 'rgba(245,245,245,0.6)' }}
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null
                  const item = payload[0].payload as { name: string; value: number; desc: string }
                  return (
                    <div style={{ background: 'white', border: '1px solid #e5e5e5', borderRadius: '10px', padding: '8px 12px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                      <p style={{ fontWeight: 600, fontSize: '12px', color: '#171717' }}>{item.name}: {item.value}</p>
                      <p style={{ fontSize: '11px', color: '#737373', marginTop: '2px', maxWidth: '180px' }}>{item.desc}</p>
                    </div>
                  )
                }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={36} fill="#bd9762" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="rounded-2xl border border-neutral-100 bg-neutral-50/80 p-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-[#bd9762]/10 text-[#bd9762] flex items-center justify-center shrink-0">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="1" x2="12" y2="23" />
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </div>
          <div>
            <p className="text-lg font-bold text-neutral-900 tabular-nums">
              {(deal.close_value ?? 0).toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
            </p>
            <p className="text-xs font-medium text-neutral-700">Estimativa do valor do deal</p>
            <p className="text-[10px] text-neutral-400 mt-0.5">Ticket médio histórico do vendedor × produto</p>
          </div>
        </div>
      </div>
    </div>
  )
}

const ACTION_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  PUSH_HARD:         { bg: 'bg-red-50',     text: 'text-red-700',    border: 'border-red-200'     },
  ACCELERATE:        { bg: 'bg-amber-50',   text: 'text-amber-700',  border: 'border-amber-200'   },
  MONITOR:           { bg: 'bg-blue-50',    text: 'text-blue-700',   border: 'border-blue-200'    },
  INVESTIGATE:       { bg: 'bg-purple-50',  text: 'text-purple-700', border: 'border-purple-200'  },
  TRANSFER:          { bg: 'bg-orange-50',  text: 'text-orange-700', border: 'border-orange-200'  },
  CONSIDER_TRANSFER: { bg: 'bg-yellow-50',  text: 'text-yellow-700', border: 'border-yellow-200'  },
  DISCARD:           { bg: 'bg-neutral-50', text: 'text-neutral-500',border: 'border-neutral-200' },
  RE_QUALIFY:        { bg: 'bg-teal-50',    text: 'text-teal-700',   border: 'border-teal-200'    },
}

const FEED_TRANSFER_ACTIONS = new Set<string>(['TRANSFER', 'CONSIDER_TRANSFER'])

/** CTA mock no feed (MVP): um rótulo por tipo de sugestão, exceto transferências. */
const FEED_ACTION_CTA_LABELS: Record<string, string> = {
  PUSH_HARD: 'Agendar prioridade com o cliente',
  ACCELERATE: 'Acelerar próxima etapa do deal',
  MONITOR: 'Agendar revisão de monitoramento',
  INVESTIGATE: 'Abrir checklist de investigação',
  DISCARD: 'Registrar encerramento do deal',
  RE_QUALIFY: 'Iniciar fluxo de requalificação',
}

/** CTA mock no 3º card (transferências). */
const FEED_TRANSFER_CTA_LABELS: Record<string, string> = {
  TRANSFER: 'Iniciar transferência para o vendedor sugerido',
  CONSIDER_TRANSFER: 'Abrir avaliação de transferência',
}

const FEED_ACTION_CTA_EMOJIS: Record<string, string> = {
  PUSH_HARD: '🔥',
  ACCELERATE: '⚡',
  MONITOR: '📌',
  INVESTIGATE: '🔍',
  DISCARD: '🗑️',
  RE_QUALIFY: '🔄',
}

const FEED_TRANSFER_CTA_EMOJIS: Record<string, string> = {
  TRANSFER: '🔀',
  CONSIDER_TRANSFER: '💬',
}

function FeedMockCtaButton({ label, emoji, className }: { label: string; emoji: string; className?: string }) {
  return (
    <button
      type="button"
      onClick={() => window.alert('Esta funcionalidade ainda não está disponível no MVP.')}
      className={cn(
        'flex w-full items-center justify-center gap-3 rounded-2xl px-4 py-3.5 text-center',
        'bg-[#bd9762] text-white shadow-[0_6px_20px_rgba(189,151,98,0.38)]',
        'text-sm font-semibold leading-snug tracking-tight',
        'transition-all duration-200',
        'hover:bg-[#a88550] hover:shadow-[0_8px_26px_rgba(189,151,98,0.48)]',
        'active:scale-[0.99] active:shadow-[0_4px_14px_rgba(189,151,98,0.35)]',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#bd9762]',
        className,
      )}
    >
      <span className="shrink-0 text-lg leading-none select-none" aria-hidden>
        {emoji}
      </span>
      <span>{label}</span>
    </button>
  )
}

function DealActionCard({ deal, detail, headerRef, sellerBadgeRef }: { deal: Deal; detail?: ScoreResult; headerRef?: RefObject<HTMLDivElement | null>; sellerBadgeRef?: RefObject<HTMLSpanElement | null> }) {
  const colors = deal.action != null ? (ACTION_COLORS[deal.action] ?? ACTION_COLORS.MONITOR) : ACTION_COLORS.MONITOR
  const steps = detail?.action?.details?.action_steps as string[] | undefined
  const reason = detail?.action?.reason
  const targetSeller = detail?.action?.details?.target_seller as string | undefined
  const showFeedCta = Boolean(deal.action && !FEED_TRANSFER_ACTIONS.has(deal.action))
  const feedCtaLabel = deal.action ? FEED_ACTION_CTA_LABELS[deal.action] ?? 'Executar próxima ação' : ''
  const feedCtaEmoji = deal.action ? FEED_ACTION_CTA_EMOJIS[deal.action] ?? '✨' : ''

  return (
    <div className="w-[500px] h-full shrink-0 rounded-2xl border border-neutral-100 bg-neutral-50/50 p-6 flex flex-col gap-6 overflow-y-auto">
      <div ref={headerRef} className={cn('rounded-xl border p-4 flex flex-col gap-2', colors.bg, colors.border)}>
        <span className={cn('text-[10px] font-bold tracking-widest uppercase flex items-center gap-1.5', colors.text)}>
          {deal.action && ACTION_ICON[deal.action]} {deal.action?.replace(/_/g, ' ')}
        </span>
        <p className="text-sm font-semibold text-neutral-900 leading-snug">{deal.message}</p>
      </div>

      <div className="flex flex-col gap-2">
        <p className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">Por quê</p>
        {reason != null ? (
          <p className="text-sm text-neutral-700 leading-relaxed">{reason}</p>
        ) : (
          <div className="flex flex-col gap-2">
            <div className="h-3.5 w-full rounded bg-neutral-100 animate-pulse" />
            <div className="h-3.5 w-4/5 rounded bg-neutral-100 animate-pulse" />
            <div className="h-3.5 w-2/3 rounded bg-neutral-100 animate-pulse" />
          </div>
        )}
      </div>

      <div className="flex flex-col gap-3">
        <p className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">Próximos passos</p>
        {steps != null ? (
          <ol className="flex flex-col gap-3">
            {steps.map((step, i) => (
              <li key={i} className="flex gap-3 items-start">
                <span className="shrink-0 w-5 h-5 rounded-full bg-[#bd9762]/15 text-[#bd9762] text-[10px] font-bold flex items-center justify-center mt-0.5">
                  {i + 1}
                </span>
                {i === 0 && targetSeller && step.includes(targetSeller) ? (
                  <span className="text-sm text-neutral-700 leading-snug flex items-center gap-1.5 flex-wrap">
                    {step.split(targetSeller).map((part, j, arr) => (
                      <span key={j} className="contents">
                        {part}
                        {j < arr.length - 1 && (
                          <span ref={sellerBadgeRef} className={cn('rounded-full px-2.5 py-1 text-[11px] font-semibold border', colors.bg, colors.text, colors.border)}>
                            {targetSeller}
                          </span>
                        )}
                      </span>
                    ))}
                  </span>
                ) : (
                  <span className="text-sm text-neutral-700 leading-snug">{step}</span>
                )}
              </li>
            ))}
          </ol>
        ) : (
          <div className="flex flex-col gap-2.5">
            {[80, 65, 90].map((w, i) => (
              <div key={i} className="flex gap-3 items-center">
                <div className="shrink-0 w-5 h-5 rounded-full bg-neutral-100 animate-pulse" />
                <div className="h-3.5 rounded bg-neutral-100 animate-pulse" style={{ width: `${w}%` }} />
              </div>
            ))}
          </div>
        )}
        {showFeedCta && <FeedMockCtaButton label={feedCtaLabel} emoji={feedCtaEmoji} className="mt-3" />}
      </div>
    </div>
  )
}

function DealTransferCard({
  containerRef,
  avatarRef,
  detail,
  action,
}: {
  containerRef?: RefObject<HTMLDivElement | null>
  avatarRef?: RefObject<HTMLDivElement | null>
  detail?: ScoreResult
  action?: Deal['action']
}) {
  const targetSeller = detail?.action?.details?.target_seller as string | undefined
  const targetContext = detail?.action?.details?.target_context as { viability?: number } | undefined
  const viability = targetContext?.viability
  const whyHelps = detail?.action?.details?.why_this_helps as string[] | undefined

  return (
    <div ref={containerRef} className="w-[500px] h-full shrink-0 rounded-2xl border border-neutral-100 bg-neutral-50/50 p-6 flex flex-col gap-6 overflow-y-auto">

      {/* Header: avatar + nome + viabilidade */}
      {targetSeller != null ? (
        <div className="flex items-center gap-3">
          <div ref={avatarRef} className="shrink-0 w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: '#bb935b' }}>
            <span className="text-sm font-bold text-white">
              {targetSeller.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <p className="text-sm font-semibold text-neutral-900 leading-tight">{targetSeller}</p>
            {viability != null && (
              <p className="text-xs text-neutral-400">Viabilidade {Math.round(viability)}</p>
            )}
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-3">
          <div className="shrink-0 w-10 h-10 rounded-full bg-neutral-100 animate-pulse" />
          <div className="flex flex-col gap-1.5">
            <div className="h-3.5 w-32 rounded bg-neutral-100 animate-pulse" />
            <div className="h-3 w-20 rounded bg-neutral-100 animate-pulse" />
          </div>
        </div>
      )}

      {/* Por que essa transferência ajuda */}
      <div className="flex flex-col gap-3">
        <p className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">Por que essa transferência ajuda</p>
        {whyHelps != null ? (
          whyHelps.length > 0 ? (
            <ul className="flex flex-col gap-3">
              {whyHelps.map((item, i) => (
                <li key={i} className="flex gap-3 items-start">
                  <span className="shrink-0 w-5 h-5 rounded-full bg-[#bd9762]/15 text-[#bd9762] flex items-center justify-center mt-0.5">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </span>
                  <span className="text-sm text-neutral-700 leading-snug">{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-neutral-400">Nenhum dado disponível</p>
          )
        ) : (
          <div className="flex flex-col gap-2.5">
            {[85, 70, 90].map((w, i) => (
              <div key={i} className="flex gap-3 items-center">
                <div className="shrink-0 w-5 h-5 rounded-full bg-neutral-100 animate-pulse" />
                <div className="h-3.5 rounded bg-neutral-100 animate-pulse" style={{ width: `${w}%` }} />
              </div>
            ))}
          </div>
        )}
      </div>

      {action && FEED_TRANSFER_ACTIONS.has(action) && (
        <FeedMockCtaButton
          label={FEED_TRANSFER_CTA_LABELS[action] ?? 'Avançar com transferência'}
          emoji={FEED_TRANSFER_CTA_EMOJIS[action] ?? '🔀'}
        />
      )}
    </div>
  )
}

type Ports = { x1: number; y1: number; x2: number; y2: number }

function DealCardPair({ deal, detail }: { deal: Deal; detail?: ScoreResult }) {
  const isTransfer = deal.action === 'TRANSFER' || deal.action === 'CONSIDER_TRANSFER'

  const containerRef = useRef<HTMLDivElement>(null)
  const badgeRef = useRef<HTMLSpanElement>(null)
  const headerRef = useRef<HTMLDivElement>(null)
  const transferRef = useRef<HTMLDivElement>(null)
  const sellerBadgeRef = useRef<HTMLSpanElement>(null)
  const avatarRef = useRef<HTMLDivElement>(null)

  const [path, setPath] = useState('')
  const [ports, setPorts] = useState<Ports | null>(null)
  const [path3, setPath3] = useState('')
  const [ports3, setPorts3] = useState<Ports | null>(null)

  useLayoutEffect(() => {
    const badge = badgeRef.current
    const header = headerRef.current
    const container = containerRef.current
    if (!badge || !header || !container) return

    const cr = container.getBoundingClientRect()
    const br = badge.getBoundingClientRect()
    const hr = header.getBoundingClientRect()

    const x1 = br.right - cr.left
    const y1 = br.top + br.height / 2 - cr.top
    const x2 = hr.left - cr.left
    const y2 = hr.top + hr.height / 2 - cr.top
    const dx = (x2 - x1) * 0.5

    setPath(`M${x1},${y1} C${x1 + dx},${y1} ${x2 - dx},${y2} ${x2},${y2}`)
    setPorts({ x1, y1, x2, y2 })

    if (isTransfer && avatarRef.current) {
      const avr = avatarRef.current.getBoundingClientRect()
      const sx1 = hr.right - cr.left
      const sy1 = hr.top + hr.height / 2 - cr.top
      const sx2 = avr.left - cr.left
      const sy2 = avr.top + avr.height / 2 - cr.top
      const sdx = (sx2 - sx1) * 0.5

      setPath3(`M${sx1},${sy1} C${sx1 + sdx},${sy1} ${sx2 - sdx},${sy2} ${sx2},${sy2}`)
      setPorts3({ x1: sx1, y1: sy1, x2: sx2, y2: sy2 })
    } else {
      setPath3('')
      setPorts3(null)
    }
  }, [deal, detail, isTransfer])

  return (
    <div ref={containerRef} className="relative px-6 pb-6 pt-0 flex gap-4 w-full h-full items-start justify-center">
      <DealInfoCard deal={deal} badgeRef={badgeRef} />
      <DealActionCard deal={deal} detail={detail} headerRef={headerRef} sellerBadgeRef={sellerBadgeRef} />
      {isTransfer && (
        <DealTransferCard containerRef={transferRef} avatarRef={avatarRef} detail={detail} action={deal.action} />
      )}
      <svg className="absolute inset-0 w-full h-full pointer-events-none overflow-visible">
        {path && ports && (
          <>
            <path d={path} stroke="#cbd5e1" strokeWidth="1.5" fill="none" strokeDasharray="4 3" />
            <circle cx={ports.x1} cy={ports.y1} r="3" fill="white" stroke="#cbd5e1" strokeWidth="1.5" />
            <circle cx={ports.x2} cy={ports.y2} r="3" fill="white" stroke="#cbd5e1" strokeWidth="1.5" />
          </>
        )}
        {path3 && ports3 && (
          <>
            <path d={path3} stroke="#cbd5e1" strokeWidth="1.5" fill="none" strokeDasharray="4 3" />
            <circle cx={ports3.x1} cy={ports3.y1} r="3" fill="white" stroke="#cbd5e1" strokeWidth="1.5" />
            <circle cx={ports3.x2} cy={ports3.y2} r="3" fill="white" stroke="#cbd5e1" strokeWidth="1.5" />
          </>
        )}
      </svg>
    </div>
  )
}

function FeedCanvas({ deals, active, toggles }: { deals: Deal[]; active: string; toggles: React.ReactNode }) {
  const filtered = deals.filter(d => d.action === active)
  const [index, setIndex] = useState(0)
  const scrollRef = useRef<HTMLDivElement>(null)
  const detailResults = useDealBatch(filtered.map(d => d.opportunity_id))

  useEffect(() => {
    setIndex(0)
    if (scrollRef.current) scrollRef.current.scrollLeft = 0
  }, [active])

  useEffect(() => {
    const el = scrollRef.current
    if (!el || filtered.length === 0) return

    const syncFromScroll = () => {
      const w = el.clientWidth || 1
      const maxIdx = Math.max(0, filtered.length - 1)
      const i = Math.min(maxIdx, Math.round(el.scrollLeft / w))
      setIndex(i)
    }

    let raf = 0
    const onScroll = () => {
      cancelAnimationFrame(raf)
      raf = requestAnimationFrame(syncFromScroll)
    }

    el.addEventListener('scroll', onScroll, { passive: true })
    el.addEventListener('scrollend', onScroll as EventListener)
    const ro = new ResizeObserver(() => {
      syncFromScroll()
    })
    ro.observe(el)
    syncFromScroll()

    return () => {
      cancelAnimationFrame(raf)
      el.removeEventListener('scroll', onScroll)
      el.removeEventListener('scrollend', onScroll as EventListener)
      ro.disconnect()
    }
  }, [active, filtered.length])

  return (
    <div className="rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] flex flex-col flex-1 min-h-0 overflow-hidden">
      {/* Toggles */}
      <div className="shrink-0 flex justify-center gap-4 pt-16 pb-2 px-4" role="group" aria-label="Filtrar por ação">
        {toggles}
      </div>

      {/* Canvas */}
      {filtered.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-neutral-400">Nenhum deal com essa ação</p>
        </div>
      ) : (
        <>
          <div
            ref={scrollRef}
            className="flex overflow-x-auto snap-x snap-mandatory scrollbar-none flex-1 min-h-0"
            style={{ scrollbarWidth: 'none' }}
          >
            {filtered.map((deal, i) => (
              <div key={deal.opportunity_id} className="min-w-full shrink-0 snap-start h-full">
                <DealCardPair deal={deal} detail={detailResults[i]?.data} />
              </div>
            ))}
          </div>

          {/* Scroll hint */}
          <div className="shrink-0 flex items-center justify-center gap-1.5 py-1 select-none">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-300">
              <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 5 5 12 12 19" />
            </svg>
            <span className="text-[10px] font-medium tracking-widest uppercase text-neutral-300">Role horizontalmente para visualizar</span>
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-300">
              <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
            </svg>
          </div>

          {/* Página atual (sincronizada com o scroll horizontal) */}
          <div className="shrink-0 flex items-center justify-center py-2 select-none">
            <span
              className="text-[9px] font-medium tabular-nums text-neutral-400"
              aria-live="polite"
              aria-atomic="true"
            >
              {index + 1} / {filtered.length}
            </span>
          </div>
        </>
      )}
    </div>
  )
}

const FEED_ACTIONS = [
  { key: 'PUSH_HARD',         label: 'Push Hard',        icon: '🔥' },
  { key: 'RE_QUALIFY',        label: 'Re-qualify',       icon: '🔄' },
  { key: 'TRANSFER',          label: 'Transfer',         icon: '🔀' },
  { key: 'DISCARD',           label: 'Discard',          icon: '❌' },
  { key: 'ACCELERATE',        label: 'Accelerate',       icon: '⚡' },
  { key: 'CONSIDER_TRANSFER', label: 'Consider Transfer',icon: '🔀' },
  { key: 'MONITOR',           label: 'Monitor',          icon: '⏸' },
  { key: 'INVESTIGATE',       label: 'Investigate',      icon: '🔍' },
] as const

const ACTION_ICON: Record<string, string> = Object.fromEntries(
  FEED_ACTIONS.map(({ key, icon }) => [key, icon])
)

function FeedContent({ sellerName }: { sellerName: string }) {
  const [active, setActive] = useState<string>(FEED_ACTIONS[0].key)
  const { data: deals = [] } = useDeals({ sales_agent: sellerName, all_stages: true })

  const countByAction = deals.reduce<Record<string, number>>((acc, d) => {
    if (d.action != null) acc[d.action] = (acc[d.action] ?? 0) + 1
    return acc
  }, {})

  useEffect(() => {
    const firstWithDeals = FEED_ACTIONS.find(a => (countByAction[a.key] ?? 0) > 0)
    if (firstWithDeals) setActive(firstWithDeals.key)
  }, [deals.length])

  const toggles = [...FEED_ACTIONS]
    .sort((a, b) => ((countByAction[b.key] ?? 0) > 0 ? 1 : 0) - ((countByAction[a.key] ?? 0) > 0 ? 1 : 0))
    .map(({ key }) => {
      const count = countByAction[key] ?? 0
      const isActive = active === key
      return (
        <div key={key} className="flex flex-col items-center gap-2">
          <button
            type="button"
            onClick={() => setActive(key)}
            className={cn(
              'relative flex items-center justify-center rounded-full transition-all duration-200',
              'w-14 h-14 text-2xl',
              isActive
                ? 'bg-neutral-50 shadow-[0_4px_20px_rgba(0,0,0,0.12)] scale-110 ring-2 ring-[#bd9762]/30'
                : count > 0
                  ? 'bg-neutral-100 hover:bg-neutral-50 hover:shadow-md hover:scale-105'
                  : 'bg-neutral-100 opacity-40',
            )}
          >
            {ACTION_ICON[key]}
            {count > 0 && (
              <span className={cn(
                'absolute -top-0.5 -right-0.5 flex items-center justify-center rounded-full text-[9px] font-bold leading-none w-4 h-4',
                isActive ? 'bg-[#bd9762] text-white' : 'bg-neutral-400 text-white',
              )}>
                {count}
              </span>
            )}
          </button>
          {isActive && (
            <span className={cn(
              'self-start shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold whitespace-nowrap',
              ACTION_COLORS[key]?.bg ?? 'bg-neutral-50',
              ACTION_COLORS[key]?.text ?? 'text-neutral-500',
              ACTION_COLORS[key]?.border ?? 'border-neutral-200',
            )}>
              {ACTION_ICON[key]} {FEED_ACTIONS.find(a => a.key === key)?.label}
            </span>
          )}
        </div>
      )
    })

  return (
    <div className="flex flex-col h-full">
      <FeedCanvas deals={deals} active={active} toggles={toggles} />
    </div>
  )
}

export default function SellerPage() {
  const { name: encodedName } = useParams<{ name: string }>()
  const navigate = useNavigate()
  const sellerName = encodedName ? decodeURIComponent(encodedName) : ''

  const { data: sellers = [] } = useSellers()
  const [activeId, setActiveId] = useState('seller-feed')
  const [kanbanSlideIndex, setKanbanSlideIndex] = useState(0)
  const kanbanBoardRef = useRef<KanbanBoardRef>(null)

  const goToKanbanSection = useCallback((index: number) => {
    document.getElementById('seller-kanban')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    window.setTimeout(() => {
      kanbanBoardRef.current?.scrollToSlide(index)
    }, 220)
  }, [])

  const seller = sellers.find((s) => s.sales_agent === sellerName)

  useEffect(() => {
    document.title = 'Seller view'
  }, [])

  // Redirect if seller not found (once data loaded)
  useEffect(() => {
    if (sellers.length > 0 && !seller) navigate('/home', { replace: true })
  }, [sellers, seller, navigate])

  // Intersection observer for active nav
  useEffect(() => {
    const ids = SELLER_NAV.map((n) => n.targetId)
    const observers: IntersectionObserver[] = []
    ids.forEach((id) => {
      const el = document.getElementById(id)
      if (!el) return
      const obs = new IntersectionObserver(([entry]) => {
        if (entry.isIntersecting) setActiveId(id)
      }, { threshold: 0.4 })
      obs.observe(el)
      observers.push(obs)
    })
    return () => observers.forEach((o) => o.disconnect())
  }, [seller])

  if (!seller) return null

  // Squad: all sellers with same manager
  const squadMembers = sellers.filter((s) => s.manager === seller.manager)

  return (
    <main className="bg-gray-100 text-neutral-900 h-screen overflow-y-auto scroll-smooth snap-y snap-mandatory scroll-pt-4">
      <section className="px-4 pt-4 pb-16 lg:pb-4">
        <div className="grid h-full grid-cols-1 gap-4 lg:grid-cols-[420px_1fr]">

          {/* Sidebar */}
          <aside className="lg:sticky lg:top-4 lg:h-[calc(100svh-2rem)]">
            <SellerSidebar
              name={seller.sales_agent}
              region={seller.regional_office}
              manager={seller.manager}
              activeId={activeId}
              kanbanSlideIndex={kanbanSlideIndex}
              onKanbanSectionClick={goToKanbanSection}
            />
          </aside>

          {/* Content */}
          <div className="min-w-0 space-y-4">

            <SectionCard id="seller-feed" contentClass="flex flex-col min-h-0 p-8">
              <FeedContent sellerName={sellerName} />
            </SectionCard>

            <SectionCard id="seller-dashboard" label="Dashboard" contentClass="flex flex-col min-h-0 p-8">
              <div className="flex flex-col gap-6 flex-1 min-h-0">
                <div>
                  <h2 className="text-lg font-semibold text-neutral-900 tracking-tight">Dashboard</h2>
                  <p className="text-sm text-neutral-500 mt-0.5">Visão geral do vendedor</p>
                </div>

                {/* grid: 7 cols, 2 rows — row1: auto, row2: flex restante */}
                <div className="grid grid-cols-5 grid-rows-[auto_1fr] gap-4 flex-1 min-h-0">

                  {/* Metric cards — row 1, all 5 cols */}
                  <div className="col-span-5 row-start-1 grid grid-cols-5 gap-4">
                  {([
                    {
                      icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>,
                      value: seller.active_deals,
                      suffix: '',
                      label: 'Deals Ativos',
                      sub: 'Prospecting + Engaging',
                    },
                    {
                      icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>,
                      value: seller.prospecting,
                      suffix: '',
                      label: 'Prospecting',
                      sub: 'Deals em prospecção',
                    },
                    {
                      icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
                      value: seller.active_deals - seller.prospecting,
                      suffix: '',
                      label: 'Engaging',
                      sub: 'Deals em negociação',
                    },
                    {
                      icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>,
                      value: seller.avg_ticket.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }),
                      suffix: '',
                      label: 'Ticket Médio',
                      sub: 'Média dos deals Won',
                    },
                    {
                      icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>,
                      value: seller.win_rate.toFixed(1),
                      suffix: '%',
                      label: 'Win Rate',
                      sub: 'Taxa de conversão histórica',
                    },
                  ] as { icon: React.ReactNode; value: string | number; suffix: string; label: string; sub: string }[]).map(({ icon, value, suffix, label, sub }, i) => (
                    <div key={i} className="rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-5 flex flex-col gap-3">
                      <div className="flex items-center justify-between">
                        <div className="w-8 h-8 rounded-xl bg-[#bd9762]/10 text-[#bd9762] flex items-center justify-center">
                          {icon}
                        </div>
                      </div>
                      <div>
                        <p className="text-2xl font-bold text-neutral-900 tracking-tight">{value}{suffix}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-neutral-700">{label}</p>
                        <p className="text-xs text-neutral-400 mt-0.5">{sub}</p>
                      </div>
                    </div>
                  ))}
                  </div>{/* end metric cards col-span-5 */}

                  {/* Vertical card — row 2, cols 6-7 */}
                  {/* Left card — row 2, cols 1-3 */}
                  <div className="col-span-3 row-start-2 rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
                    <WonValueOverTimeChart sellerName={sellerName} />
                  </div>

                  {/* Right card — row 2, cols 4-5 */}
                  <div className="col-start-4 col-span-2 row-start-2 rounded-2xl border border-neutral-100 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.04)] overflow-y-auto">
                    <DashboardRightCard sellerName={sellerName} seller={seller} />
                  </div>

                </div>{/* end grid 7cols */}
              </div>{/* end flex-col */}
            </SectionCard>

            <SectionCard id="seller-kanban" label="Kanban" contentClass="overflow-hidden flex flex-col min-h-0">
              <KanbanBoard
                ref={kanbanBoardRef}
                sellerName={sellerName}
                onSlideIndexChange={setKanbanSlideIndex}
              />
            </SectionCard>

            <SectionCard id="seller-squad" label="Squad">
              <div className="mb-6">
                <h2 className="text-lg font-semibold text-neutral-900 tracking-tight">Squad</h2>
                <p className="text-sm text-neutral-500 mt-0.5">Membros do seu time</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
                {squadMembers.map((s) => (
                  <SellerCard
                    key={s.sales_agent}
                    name={s.sales_agent}
                    title={s.sales_agent === sellerName ? 'Você' : 'Seller'}
                    region={s.regional_office}
                    prospect={s.prospecting}
                    engaging={s.active_deals}
                    won={s.won_deals}
                    lost={s.closed_deals - s.won_deals}
                    onClick={
                      s.sales_agent !== sellerName
                        ? () => navigate(`/sellers/${encodeURIComponent(s.sales_agent)}`)
                        : undefined
                    }
                  />
                ))}
              </div>
            </SectionCard>

          </div>
        </div>
      </section>
    </main>
  )
}
