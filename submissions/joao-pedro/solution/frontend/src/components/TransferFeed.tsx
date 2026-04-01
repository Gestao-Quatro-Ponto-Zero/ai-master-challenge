import {
  useState,
  useEffect,
  useLayoutEffect,
  useRef,
  useMemo,
  type RefObject,
} from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { cn } from '@/lib/utils'
import { fetchDeals, fetchDeal } from '@/api/deals'
import { useSellers } from '@/hooks/useSellers'
import { useQueries } from '@tanstack/react-query'
import type { Deal, DealStage, ScoreResult } from '@/types'

// =============================================================================
// CONSTANTS
// =============================================================================

const STAGE_COLORS: Record<DealStage, string> = {
  Prospecting: 'bg-blue-50 text-blue-700',
  Engaging:    'bg-amber-50 text-amber-700',
  Won:         'bg-green-50 text-green-700',
  Lost:        'bg-neutral-100 text-neutral-500',
}

const ACTION_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  TRANSFER:          { bg: 'bg-orange-50',  text: 'text-orange-700', border: 'border-orange-200'  },
  CONSIDER_TRANSFER: { bg: 'bg-yellow-50',  text: 'text-yellow-700', border: 'border-yellow-200'  },
}

const ACTION_ICON: Record<string, string> = {
  TRANSFER:          '🔀',
  CONSIDER_TRANSFER: '🔀',
}

const MANAGER_ACTION_CTA_LABELS: Record<string, string> = {
  TRANSFER:          'Validar recomendação de transferência',
  CONSIDER_TRANSFER: 'Analisar viabilidade da transferência',
}

const MANAGER_ACTION_CTA_EMOJIS: Record<string, string> = {
  TRANSFER:          '✅',
  CONSIDER_TRANSFER: '🔍',
}

const MANAGER_TRANSFER_CTA_LABELS: Record<string, string> = {
  TRANSFER:          'Aprovar transferência para este vendedor',
  CONSIDER_TRANSFER: 'Agendar revisão com o vendedor',
}

const MANAGER_TRANSFER_CTA_EMOJIS: Record<string, string> = {
  TRANSFER:          '🔀',
  CONSIDER_TRANSFER: '📅',
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

// =============================================================================
// DEAL INFO CARD
// =============================================================================

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
                'rounded-full px-2.5 py-1 text-[11px] font-semibold border',
                ACTION_COLORS[deal.action]?.bg ?? 'bg-neutral-50',
                ACTION_COLORS[deal.action]?.text ?? 'text-neutral-500',
                ACTION_COLORS[deal.action]?.border ?? 'border-neutral-200',
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

// =============================================================================
// DEAL ACTION CARD
// =============================================================================

function DealActionCard({
  deal, detail, headerRef, sellerBadgeRef,
}: {
  deal: Deal
  detail?: ScoreResult
  headerRef?: RefObject<HTMLDivElement | null>
  sellerBadgeRef?: RefObject<HTMLSpanElement | null>
}) {
  const colors = ACTION_COLORS[deal.action ?? ''] ?? { bg: 'bg-neutral-50', text: 'text-neutral-500', border: 'border-neutral-200' }
  const steps = detail?.action?.details?.action_steps as string[] | undefined
  const reason = detail?.action?.reason
  const targetSeller = detail?.action?.details?.target_seller as string | undefined

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
            {[100, 80, 65].map((w, i) => (
              <div key={i} className="h-3.5 rounded bg-neutral-100 animate-pulse" style={{ width: `${w}%` }} />
            ))}
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
        {deal.action && (
          <FeedMockCtaButton
            label={MANAGER_ACTION_CTA_LABELS[deal.action] ?? 'Validar recomendação'}
            emoji={MANAGER_ACTION_CTA_EMOJIS[deal.action] ?? '✅'}
            className="mt-3"
          />
        )}
      </div>
    </div>
  )
}

// =============================================================================
// DEAL TRANSFER CARD
// =============================================================================

function DealTransferCard({
  containerRef, avatarRef, detail, action,
}: {
  containerRef?: RefObject<HTMLDivElement | null>
  avatarRef?: RefObject<HTMLDivElement | null>
  detail?: ScoreResult
  action?: string
}) {
  const targetSeller = detail?.action?.details?.target_seller as string | undefined
  const targetContext = detail?.action?.details?.target_context as { viability?: number } | undefined
  const viability = targetContext?.viability
  const whyHelps = detail?.action?.details?.why_this_helps as string[] | undefined

  return (
    <div ref={containerRef} className="w-[500px] h-full shrink-0 rounded-2xl border border-neutral-100 bg-neutral-50/50 p-6 flex flex-col gap-6 overflow-y-auto">
      {targetSeller != null ? (
        <div className="flex items-center gap-3">
          <div ref={avatarRef} className="shrink-0 w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: '#bb935b' }}>
            <span className="text-sm font-bold text-white">{targetSeller.charAt(0).toUpperCase()}</span>
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

      {action && (
        <FeedMockCtaButton
          label={MANAGER_TRANSFER_CTA_LABELS[action] ?? 'Aprovar transferência'}
          emoji={MANAGER_TRANSFER_CTA_EMOJIS[action] ?? '🔀'}
        />
      )}
    </div>
  )
}

// =============================================================================
// DEAL CARD PAIR
// =============================================================================

type Ports = { x1: number; y1: number; x2: number; y2: number }

function DealCardPair({ deal, detail }: { deal: Deal; detail?: ScoreResult }) {
  const isTransfer = deal.action === 'TRANSFER' || deal.action === 'CONSIDER_TRANSFER'

  const containerRef = useRef<HTMLDivElement>(null)
  const badgeRef     = useRef<HTMLSpanElement>(null)
  const headerRef    = useRef<HTMLDivElement>(null)
  const transferRef  = useRef<HTMLDivElement>(null)
  const sellerBadgeRef = useRef<HTMLSpanElement>(null)
  const avatarRef    = useRef<HTMLDivElement>(null)

  const [path, setPath]   = useState('')
  const [ports, setPorts] = useState<Ports | null>(null)
  const [path3, setPath3]   = useState('')
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
    <div ref={containerRef} className="relative px-6 pb-3 pt-0 flex gap-4 w-full h-full items-start justify-center">
      <DealInfoCard deal={deal} badgeRef={badgeRef} />
      <DealActionCard deal={deal} detail={detail} headerRef={headerRef} sellerBadgeRef={sellerBadgeRef} />
      {isTransfer && <DealTransferCard containerRef={transferRef} avatarRef={avatarRef} detail={detail} action={deal.action ?? undefined} />}
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

// =============================================================================
// FEED CANVAS (transfer-only)
// =============================================================================

type FeedAction = 'TRANSFER' | 'CONSIDER_TRANSFER'

function TransferFeedCanvas({ deals }: { deals: Deal[] }) {
  const [active, setActive] = useState<FeedAction>('TRANSFER')
  const [index, setIndex] = useState(0)
  const scrollRef = useRef<HTMLDivElement>(null)

  const filtered = useMemo(() => deals.filter(d => d.action === active), [deals, active])

  const detailResults = useQueries({
    queries: filtered.map(d => ({
      queryKey: ['deal', d.opportunity_id],
      queryFn: () => fetchDeal(d.opportunity_id),
      enabled: Boolean(d.opportunity_id),
    })),
  })

  const transferCount  = useMemo(() => deals.filter(d => d.action === 'TRANSFER').length, [deals])
  const considerCount  = useMemo(() => deals.filter(d => d.action === 'CONSIDER_TRANSFER').length, [deals])

  const visibleActions = useMemo(() => (
    ([
      { key: 'TRANSFER',          label: 'Transfer',          icon: '🔀', count: transferCount  },
      { key: 'CONSIDER_TRANSFER', label: 'Consider Transfer', icon: '🔀', count: considerCount  },
    ] as { key: FeedAction; label: string; icon: string; count: number }[]).filter(a => a.count > 0)
  ), [transferCount, considerCount])

  // auto-switch if active action has no deals
  useEffect(() => {
    if (visibleActions.length > 0 && !visibleActions.find(a => a.key === active)) {
      setActive(visibleActions[0].key)
    }
  }, [visibleActions, active])

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
      setIndex(Math.min(maxIdx, Math.round(el.scrollLeft / w)))
    }
    let raf = 0
    const onScroll = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(syncFromScroll) }
    el.addEventListener('scroll', onScroll, { passive: true })
    el.addEventListener('scrollend', onScroll as EventListener)
    const ro = new ResizeObserver(syncFromScroll)
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
      {/* Toggle */}
      <div className="shrink-0 flex justify-center gap-4 pt-6 pb-2 px-4" role="group">
        {visibleActions.map(({ key, label, icon, count }) => {
          const isActive = active === key
          const colors = ACTION_COLORS[key]
          return (
            <div key={key} className="flex flex-col items-center gap-1">
              <button
                type="button"
                onClick={() => setActive(key)}
                className={cn(
                  'relative flex h-10 w-10 items-center justify-center rounded-xl text-base transition-all',
                  isActive ? 'bg-white shadow-md ring-1 ring-neutral-200' : 'bg-neutral-100 opacity-40',
                )}
              >
                {icon}
                {count > 0 && (
                  <span className={cn(
                    'absolute -top-0.5 -right-0.5 flex items-center justify-center rounded-full text-[9px] font-bold leading-none w-4 h-4',
                    isActive ? 'bg-neutral-900 text-white' : 'bg-neutral-300 text-neutral-600',
                  )}>
                    {count > 99 ? '99+' : count}
                  </span>
                )}
              </button>
              {isActive && (
                <span className={cn(
                  'self-start shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold whitespace-nowrap',
                  colors?.bg ?? 'bg-neutral-50',
                  colors?.text ?? 'text-neutral-500',
                  colors?.border ?? 'border-neutral-200',
                )}>
                  {icon} {label}
                </span>
              )}
            </div>
          )
        })}
      </div>

      {/* Canvas */}
      {filtered.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-neutral-400">Nenhum deal com essa ação no escopo</p>
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

          <div className="shrink-0 flex items-center justify-center py-2 pb-6 select-none">
            <span className="text-[9px] font-medium tabular-nums text-neutral-400" aria-live="polite">
              {index + 1} / {filtered.length}
            </span>
          </div>
        </>
      )}
    </div>
  )
}

// =============================================================================
// MAIN EXPORT
// =============================================================================

type Props = {
  managerName?: string
  scope: 'squad' | 'geral'
}

export default function TransferFeed({ managerName, scope }: Props) {
  const [regionFilter, setRegionFilter] = useState<string>('')

  const { data: transferDeals = [], isLoading: loadingT } = useQuery({
    queryKey: ['deals', { action: 'TRANSFER' }],
    queryFn: () => fetchDeals({ action: 'TRANSFER' }),
  })

  const { data: considerDeals = [], isLoading: loadingC } = useQuery({
    queryKey: ['deals', { action: 'CONSIDER_TRANSFER' }],
    queryFn: () => fetchDeals({ action: 'CONSIDER_TRANSFER' }),
  })

  const { data: sellers = [] } = useSellers()

  const squadAgents = useMemo(() => {
    if (scope === 'geral' || !managerName) return null
    return new Set(sellers.filter(s => s.manager === managerName).map(s => s.sales_agent))
  }, [sellers, managerName, scope])

  // deals filtered by scope only (used to derive available regions)
  const scopedDeals = useMemo(() => {
    const all = [...transferDeals, ...considerDeals]
    return squadAgents ? all.filter(d => squadAgents.has(d.sales_agent)) : all
  }, [transferDeals, considerDeals, squadAgents])

  const regions = useMemo(
    () => Array.from(new Set(scopedDeals.map(d => d.regional_office).filter(Boolean))).sort(),
    [scopedDeals],
  )

  /** Sem opção "Todos": usa a 1ª região até o usuário escolher outra válida. */
  const selectedRegion = useMemo(() => {
    if (regions.length === 0) return ''
    if (regionFilter && regions.includes(regionFilter)) return regionFilter
    return regions[0]
  }, [regions, regionFilter])

  // final deals after region filter
  const deals = useMemo(() => {
    if (regions.length === 0) return scopedDeals
    return scopedDeals.filter(d => d.regional_office === selectedRegion)
  }, [scopedDeals, regions.length, selectedRegion])

  const transferCount = useMemo(() => deals.filter(d => d.action === 'TRANSFER').length, [deals])
  const considerCount = useMemo(() => deals.filter(d => d.action === 'CONSIDER_TRANSFER').length, [deals])

  if (loadingT || loadingC) {
    return <div className="flex-1 min-h-0 animate-pulse rounded-2xl bg-neutral-100" />
  }

  return (
    <div className="flex flex-col flex-1 min-h-0 gap-3">
      {scope === 'geral' && (
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          {regions.length > 0 && (
            <>
              <span className="text-[11px] font-medium tracking-widest text-neutral-400 uppercase">Região</span>
              {regions.map((region) => (
                <button
                  key={region}
                  type="button"
                  onClick={() => setRegionFilter(region)}
                  className={cn(
                    'rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors',
                    selectedRegion === region
                      ? 'border-neutral-900 bg-neutral-900 text-white'
                      : 'border-neutral-200 bg-white text-neutral-500 hover:text-neutral-800',
                  )}
                >
                  {region}
                </button>
              ))}
            </>
          )}
          <span className={cn('text-[11px] text-neutral-400', regions.length > 0 && 'ml-1')}>
            {deals.length} resultado{deals.length !== 1 ? 's' : ''}
            {deals.length > 0 && (
              <> · <span className="text-orange-500">{transferCount} Transfer</span> · <span className="text-yellow-600">{considerCount} Consider</span></>
            )}
          </span>
        </div>
      )}
      <TransferFeedCanvas deals={deals} />
    </div>
  )
}
