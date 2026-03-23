import type { ElementType } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  XCircle,
} from 'lucide-react'
import { fetchSellerAlerts } from '@/api/analysis'
import { cn } from '@/lib/utils'
import type { AlertSeverity, GlobalAlert } from '@/types'

const SEVERITY_CONFIG: Record<
  AlertSeverity,
  { iconClass: string; badge: string; badgeLabel: string; Icon: ElementType }
> = {
  error: {
    iconClass: 'text-red-500',
    badge: 'bg-red-50 text-red-600 border-red-200',
    badgeLabel: 'Crítico',
    Icon: XCircle,
  },
  warning: {
    iconClass: 'text-amber-500',
    badge: 'bg-amber-50 text-amber-600 border-amber-200',
    badgeLabel: 'Aviso',
    Icon: AlertTriangle,
  },
  info: {
    iconClass: 'text-blue-500',
    badge: 'bg-blue-50 text-blue-600 border-blue-200',
    badgeLabel: 'Info',
    Icon: Info,
  },
  success: {
    iconClass: 'text-green-500',
    badge: 'bg-green-50 text-green-600 border-green-200',
    badgeLabel: 'OK',
    Icon: CheckCircle2,
  },
}

function metricLine(alert: GlobalAlert): { value: string; label: string } | null {
  const d = alert.data as Record<string, unknown>
  switch (alert.key) {
    case 'seller_no_prospecting':
      return { value: String(d.prospecting ?? '—'), label: 'prospecting' }
    case 'seller_overloaded_critical':
    case 'seller_overloaded_warning':
      return { value: String(d.active_deals ?? '—'), label: 'deals ativos' }
    case 'seller_high_discard':
      return { value: `${d.discard_pct ?? '—'}%`, label: 'dos deals para discard' }
    default:
      return null
  }
}

function SellerAlertCard({ alert }: { alert: GlobalAlert }) {
  const cfg = SEVERITY_CONFIG[alert.severity] ?? SEVERITY_CONFIG.info
  const metric = metricLine(alert)

  return (
    <div
      className={cn(
        'flex gap-3 rounded-xl border border-neutral-100/90 bg-white/95 p-4',
        'shadow-[0_1px_8px_rgba(0,0,0,0.03)]',
      )}
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-neutral-100">
        <cfg.Icon size={15} className={cfg.iconClass} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <p className="text-sm font-semibold text-neutral-900 leading-snug">{alert.title}</p>
          <span
            className={cn(
              'inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold shrink-0',
              cfg.badge,
            )}
          >
            {cfg.badgeLabel}
          </span>
        </div>

        {metric ? (
          <p className="mt-1.5 text-xl font-bold tabular-nums leading-tight text-neutral-900">
            {metric.value}
            <span className="ml-1.5 text-[11px] font-normal text-neutral-400">{metric.label}</span>
          </p>
        ) : null}
        <p className="mt-1 text-[11px] leading-snug text-neutral-500">{alert.message}</p>
      </div>
    </div>
  )
}

type Props = {
  salesAgent: string
  /** Dentro de outro card (ex.: dashboard seller): sem faixa superior nem fundo cinza. */
  embedded?: boolean
}

const shellClass = (embedded: boolean) =>
  cn(
    embedded
      ? 'w-full min-h-0 flex flex-col flex-1 px-1 py-1 sm:px-2'
      : 'border-t border-neutral-200 bg-neutral-50/40 px-4 py-4 sm:px-5',
  )

/**
 * Alertas da API GET /analysis/alerts/seller/{sales_agent} (prospecção, carga, DISCARD).
 */
export default function SellerAlertsBlock({ salesAgent, embedded = false }: Props) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['seller-alerts', salesAgent],
    queryFn: () => fetchSellerAlerts(salesAgent),
    enabled: Boolean(salesAgent),
  })

  if (!salesAgent) return null

  if (isLoading) {
    return (
      <div className={shellClass(embedded)}>
        <p className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-3">Avisos do vendedor</p>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-xl bg-neutral-100" />
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className={shellClass(embedded)}>
        <p className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-1">Avisos do vendedor</p>
        <p className="text-sm text-red-600">
          {error instanceof Error ? error.message : 'Não foi possível carregar os alertas.'}
        </p>
      </div>
    )
  }

  if (data === undefined) {
    return null
  }

  if (data === null) {
    return (
      <div className={shellClass(embedded)}>
        <p className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-1">Avisos do vendedor</p>
        <p className="text-sm text-neutral-500">
          Sem deals em Engaging para este vendedor — alertas indisponíveis.
        </p>
      </div>
    )
  }

  const triggeredOnly = data.alerts.filter((a) => a.triggered)

  if (triggeredOnly.length === 0) {
    return (
      <div className={shellClass(embedded)}>
        <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-2">Avisos do vendedor</h4>
        <p className="text-sm text-neutral-500 leading-relaxed">
          O sistema não identificou avisos para esse vendedor.
        </p>
      </div>
    )
  }

  return (
    <div className={shellClass(embedded)}>
      <h4 className="text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-3">Avisos do vendedor</h4>
      <div className="flex flex-col gap-2">
        {triggeredOnly.map((a) => (
          <SellerAlertCard key={a.key} alert={a} />
        ))}
      </div>
    </div>
  )
}
