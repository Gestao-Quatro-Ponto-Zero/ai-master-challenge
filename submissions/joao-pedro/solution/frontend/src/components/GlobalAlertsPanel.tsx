import { useEffect, useState } from 'react'
import {
  AlertTriangle,
  ArrowLeftRight,
  BarChart2,
  CheckCircle2,
  Clock,
  Info,
  MapPin,
  Package,
  XCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useGlobalAlerts } from '@/hooks/useGlobalAlerts'
import type { AlertSeverity, GlobalAlert, GlobalAlertsScopePayload } from '@/types'

// =============================================================================
// CONFIG
// =============================================================================

const SEVERITY_CONFIG: Record<
  AlertSeverity,
  { border: string; iconClass: string; badge: string; badgeLabel: string; Icon: React.ElementType }
> = {
  error: {
    border: 'border-l-red-400',
    iconClass: 'text-red-500',
    badge: 'bg-red-50 text-red-600 border-red-200',
    badgeLabel: 'Crítico',
    Icon: XCircle,
  },
  warning: {
    border: 'border-l-amber-400',
    iconClass: 'text-amber-500',
    badge: 'bg-amber-50 text-amber-600 border-amber-200',
    badgeLabel: 'Aviso',
    Icon: AlertTriangle,
  },
  info: {
    border: 'border-l-blue-400',
    iconClass: 'text-blue-500',
    badge: 'bg-blue-50 text-blue-600 border-blue-200',
    badgeLabel: 'Info',
    Icon: Info,
  },
  success: {
    border: 'border-l-green-400',
    iconClass: 'text-green-500',
    badge: 'bg-green-50 text-green-600 border-green-200',
    badgeLabel: 'OK',
    Icon: CheckCircle2,
  },
}

const CATEGORIES: { key: string; label: string; Icon: React.ElementType; keys: string[] }[] = [
  {
    key: 'actions',
    label: 'Ações',
    Icon: BarChart2,
    keys: ['action_high_discard', 'action_high_transfer', 'action_low_push'],
  },
  {
    key: 'pipeline',
    label: 'Pipeline',
    Icon: Clock,
    keys: ['pipeline_ratio', 'pipeline_no_prospecting'],
  },
  {
    key: 'regional',
    label: 'Regional',
    Icon: MapPin,
    keys: ['regional_load_imbalance', 'regional_inter_transfers'],
  },
  {
    key: 'products',
    label: 'Produtos',
    Icon: Package,
    keys: ['product_most_stuck', 'product_high_discard'],
  },
  {
    key: 'transfers',
    label: 'Transferências',
    Icon: ArrowLeftRight,
    keys: ['transfer_hierarchy_balance'],
  },
]

// =============================================================================
// METRIC HELPERS
// =============================================================================

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getMetric(alert: GlobalAlert): string {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const d = alert.data as any
  switch (alert.key) {
    case 'action_high_discard':        return `${d.discard_pct}%`
    case 'action_high_transfer':       return `${d.transfer_pct}%`
    case 'action_low_push':            return `${d.push_pct}%`
    case 'pipeline_ratio':             return d.ratio != null ? `${d.ratio}×` : '—'
    case 'pipeline_no_prospecting':    return `${d.pct_no_prospecting}%`
    case 'regional_load_imbalance':    return `${d.load_ratio}×`
    case 'regional_inter_transfers':   return `${d.inter_regional_pct}%`
    case 'product_most_stuck':         return d.engaging_vs_won_ratio != null ? `${d.engaging_vs_won_ratio}×` : '—'
    case 'product_high_discard':       return `${d.discard_pct}%`
    case 'transfer_hierarchy_balance':
      if (d.well_allocated == null) return '—'
      return d.well_allocated ? String(d.same_team) : String(d.other_region)
    default: return '—'
  }
}

function getMetricLabel(alert: GlobalAlert): string {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const d = alert.data as any
  switch (alert.key) {
    case 'action_high_discard':        return 'dos deals para discard'
    case 'action_high_transfer':       return 'dos deals para transfer'
    case 'action_low_push':            return 'com ação imediata'
    case 'pipeline_ratio':             return 'acima da mediana Won'
    case 'pipeline_no_prospecting':    return 'dos vendedores sem prospecting'
    case 'regional_load_imbalance':    return 'ratio de carga entre regiões'
    case 'regional_inter_transfers':   return 'das transferências são inter-regionais'
    case 'product_most_stuck':         return 'acima do ciclo histórico Won'
    case 'product_high_discard':       return `de discard em ${d.product ?? 'produto'}`
    case 'transfer_hierarchy_balance':
      if (d.well_allocated == null) return ''
      return d.well_allocated ? 'transfers resolvíveis no mesmo time' : 'transfers para outras regiões'
    default: return ''
  }
}

// =============================================================================
// ALERT CARD
// =============================================================================

function AlertCard({ alert }: { alert: GlobalAlert }) {
  const cfg = SEVERITY_CONFIG[alert.severity] ?? SEVERITY_CONFIG.info

  return (
    <div
      className={cn(
        'flex gap-3 rounded-xl border border-neutral-100/90 bg-white/95 p-4',
        'shadow-[0_1px_8px_rgba(0,0,0,0.03)]',
        !alert.triggered && 'opacity-40',
      )}
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-neutral-100">
        <cfg.Icon size={15} className={alert.triggered ? cfg.iconClass : 'text-neutral-400'} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <p className="text-sm font-semibold text-neutral-900 leading-snug">{alert.title}</p>
          {alert.triggered ? (
            <span
              className={cn(
                'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold shrink-0',
                cfg.badge,
              )}
            >
              {cfg.badgeLabel}
            </span>
          ) : (
            <span className="inline-flex items-center rounded-full border border-neutral-200 bg-neutral-50 px-2 py-0.5 text-[10px] font-semibold text-neutral-400 shrink-0">
              Normal
            </span>
          )}
        </div>

        {alert.triggered && (
          <>
            <p className="mt-1.5 text-xl font-bold tabular-nums leading-tight text-neutral-900">
              {getMetric(alert)}
              <span className="ml-1.5 text-[11px] font-normal text-neutral-400">
                {getMetricLabel(alert)}
              </span>
            </p>
            <p className="mt-1 text-[11px] leading-snug text-neutral-500">{alert.message}</p>
          </>
        )}
      </div>
    </div>
  )
}

// =============================================================================
// LISTA (único modo de visualização)
// =============================================================================

function AlertsListView({
  data,
  showAll,
}: {
  data: GlobalAlertsScopePayload
  showAll: boolean
}) {
  const { alerts, triggered_count: triggeredCount } = data
  const alertMap = Object.fromEntries(alerts.map(a => [a.key, a]))

  return (
    <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden space-y-5 pr-1 overscroll-y-contain [scrollbar-gutter:stable]">
      {CATEGORIES.map(({ key, label, Icon, keys }) => {
        const categoryAlerts = keys.map(k => alertMap[k]).filter(Boolean) as GlobalAlert[]
        const visible = showAll ? categoryAlerts : categoryAlerts.filter(a => a.triggered)

        if (visible.length === 0) return null

        return (
          <div key={key}>
            <div className="mb-2.5 flex items-center gap-2">
              <Icon size={12} className="text-neutral-400" />
              <p className="text-[10px] font-semibold uppercase tracking-wider text-neutral-400">
                {label}
              </p>
            </div>
            <div className="flex flex-col gap-2">
              {visible.map(alert => (
                <AlertCard key={alert.key} alert={alert} />
              ))}
            </div>
          </div>
        )
      })}

      {!showAll && triggeredCount === 0 && (
        <div className="flex h-40 flex-col items-center justify-center gap-2 text-neutral-400">
          <CheckCircle2 size={32} className="text-green-400" />
          <p className="text-sm font-medium text-neutral-500">Nenhum alerta disparado</p>
          <p className="text-xs text-neutral-400">
            Todos os indicadores estão dentro dos thresholds
          </p>
        </div>
      )}
    </div>
  )
}

// =============================================================================
// MAIN PANEL
// =============================================================================

type Props = {
  /** Manager selecionado na Manager view: habilita o escopo Squad na API e no toggle. */
  managerName?: string
}

export default function GlobalAlertsPanel({ managerName }: Props) {
  const { data, isLoading } = useGlobalAlerts(managerName)
  const [scopeUi, setScopeUi] = useState<'geral' | 'squad'>('geral')
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    if (!managerName && scopeUi === 'squad') {
      setScopeUi('geral')
    }
  }, [managerName, scopeUi])

  useEffect(() => {
    setShowAll(false)
  }, [scopeUi])

  if (isLoading) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center">
        <p className="text-sm text-neutral-400">Carregando alertas...</p>
      </div>
    )
  }

  if (!data) return null

  const { geral, squad } = data
  const activePayload: GlobalAlertsScopePayload | null =
    scopeUi === 'geral' ? geral : squad ?? null

  const triggeredCount = activePayload?.triggered_count ?? 0
  const totalAlerts = activePayload?.total_alerts ?? 0
  const alerts = activePayload?.alerts ?? []

  const errorCount   = alerts.filter(a => a.triggered && a.severity === 'error').length
  const warningCount = alerts.filter(a => a.triggered && a.severity === 'warning').length
  const infoCount    = alerts.filter(a => a.triggered && a.severity === 'info').length

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-5">
      {/* Escopo: Geral vs Squad (lista única) */}
      <div
        className="inline-flex w-fit shrink-0 rounded-xl border border-neutral-200 bg-neutral-50/80 p-1 gap-0.5 shadow-sm"
        role="group"
        aria-label="Escopo dos alertas"
      >
        <button
          type="button"
          disabled={!managerName || !squad}
          title={
            !managerName
              ? 'Selecione um manager no painel à esquerda'
              : !squad
                ? 'Dados do squad indisponíveis'
                : undefined
          }
          onClick={() => setScopeUi('squad')}
          className={cn(
            'min-w-[88px] rounded-lg px-4 py-2 text-sm font-medium transition-colors',
            scopeUi === 'squad'
              ? 'bg-white text-neutral-900 shadow-sm'
              : 'text-neutral-500 hover:text-neutral-800',
            (!managerName || !squad) && 'cursor-not-allowed opacity-45 hover:text-neutral-500',
          )}
        >
          Squad
        </button>
        <button
          type="button"
          onClick={() => setScopeUi('geral')}
          className={cn(
            'min-w-[88px] rounded-lg px-4 py-2 text-sm font-medium transition-colors',
            scopeUi === 'geral'
              ? 'bg-white text-neutral-900 shadow-sm'
              : 'text-neutral-500 hover:text-neutral-800',
          )}
        >
          Geral
        </button>
      </div>

      {activePayload ? (
        <div className="flex min-h-0 flex-1 flex-col gap-5">
          <p className="text-xs text-neutral-500 shrink-0">
            {scopeUi === 'geral'
              ? 'Indicadores consolidados de todo o pipeline.'
              : squad
                ? `Deals e vendedores do manager ${squad.manager}.`
                : null}
          </p>

          {/* Summary header */}
          <div className="flex items-center justify-between gap-3 flex-wrap shrink-0">
            <div className="flex items-center gap-3 flex-wrap">
              <p className="text-[13px] text-neutral-500 leading-none">
                <span className="text-2xl font-bold tabular-nums text-neutral-900 mr-1.5">
                  {triggeredCount}
                </span>
                de {totalAlerts} alertas disparados
              </p>
              <div className="flex items-center gap-1.5">
                {errorCount > 0 && (
                  <span className="inline-flex items-center rounded-full border border-red-200 bg-red-50 px-2 py-0.5 text-[10px] font-semibold text-red-600">
                    {errorCount} crítico{errorCount > 1 ? 's' : ''}
                  </span>
                )}
                {warningCount > 0 && (
                  <span className="inline-flex items-center rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-600">
                    {warningCount} aviso{warningCount > 1 ? 's' : ''}
                  </span>
                )}
                {infoCount > 0 && (
                  <span className="inline-flex items-center rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-600">
                    {infoCount} info
                  </span>
                )}
              </div>
            </div>

            <button
              type="button"
              onClick={() => setShowAll(v => !v)}
              className="text-xs text-neutral-400 transition-colors hover:text-neutral-600"
            >
              {showAll ? 'Ver apenas ativos' : 'Ver todos'}
            </button>
          </div>

          <AlertsListView data={activePayload} showAll={showAll} />
        </div>
      ) : (
        <p className="text-sm text-neutral-500">
          Selecione um manager no painel à esquerda para ver os alertas do squad.
        </p>
      )}
    </div>
  )
}
