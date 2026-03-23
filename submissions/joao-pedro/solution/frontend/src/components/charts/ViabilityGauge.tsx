import { useEffect, useId, useState } from 'react'
import { HelpCircle } from 'lucide-react'
import SellerAlertsBlock from '@/components/SellerAlertsBlock'
import { cn } from '@/lib/utils'
import type { Seller } from '@/types'

const VIABILITY_TOOLTIP =
  'A viabilidade média é um índice de 0 a 100 que resume o quão favorável é o cenário dos seus deals abertos para avançar no pipeline, com base em score e contexto.'

const RED = '#ef4444'
const AMBER = '#f59e0b'
const GREEN = '#22c55e'

function zoneColor(v: number) {
  if (v >= 60) return GREEN
  if (v >= 40) return AMBER
  return RED
}

/** Contagem de 0 até `target` com ease-out (efeito crescente). */
function useCountUp(target: number, durationMs = 900) {
  const [value, setValue] = useState(0)

  useEffect(() => {
    const to = Math.min(Math.max(target, 0), 100)
    let start: number | null = null
    let raf = 0

    const easeOutCubic = (t: number) => 1 - (1 - t) ** 3

    const tick = (now: number) => {
      if (start === null) start = now
      const elapsed = now - start
      const p = Math.min(elapsed / durationMs, 1)
      const eased = easeOutCubic(p)
      setValue(to * eased)
      if (p < 1) raf = requestAnimationFrame(tick)
    }

    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [target, durationMs])

  return value
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function ViabilityGauge({ seller }: { seller: Seller }) {
  const tooltipId = useId()
  const { viability, viability_label } = seller

  const color = zoneColor(viability)
  const animated = useCountUp(viability)

  const gaugeCardClass =
    'flex w-full shrink-0 flex-col items-center justify-center rounded-2xl border border-neutral-100 bg-white p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)] sm:max-w-[min(100%,280px)]'

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-stretch sm:gap-4 sm:min-h-[200px]">
      <div className={cn(gaugeCardClass, 'relative !pt-4 sm:h-full')}>
        <div className="flex w-full flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-xl bg-[#bd9762]/10 text-[#bd9762] flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a10 10 0 1 0 10 10" />
                <path d="M12 6v6l4 2" />
              </svg>
            </div>
            <div className="group relative flex items-center">
              <button
                type="button"
                className={cn(
                  'rounded-full p-0.5 text-neutral-300 transition-colors',
                  'hover:text-neutral-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-300 focus-visible:ring-offset-1',
                )}
                aria-label="Sobre a viabilidade média"
                aria-describedby={tooltipId}
              >
                <HelpCircle className="h-3.5 w-3.5" strokeWidth={2} aria-hidden />
              </button>
              <div
                id={tooltipId}
                role="tooltip"
                className={cn(
                  'pointer-events-none absolute bottom-full right-0 z-20 mb-1.5 w-[min(17rem,calc(100vw-2rem))]',
                  'rounded-lg border border-neutral-100 bg-white px-3 py-2.5 text-left text-[11px] leading-snug text-neutral-600',
                  'shadow-[0_4px_20px_rgba(0,0,0,0.08)]',
                  'invisible opacity-0 transition-opacity duration-150',
                  'group-hover:visible group-hover:opacity-100',
                )}
              >
                {VIABILITY_TOOLTIP}
              </div>
            </div>
          </div>
          <div>
            <p
              className="text-2xl font-bold tabular-nums tracking-tight text-neutral-900"
              aria-live="polite"
            >
              {Math.round(animated)}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-neutral-700">Viabilidade média</p>
            <p className="text-xs font-semibold mt-0.5" style={{ color }}>{viability_label}</p>
          </div>
        </div>
      </div>

      <div className="flex min-h-0 min-w-0 w-full flex-1 flex-col self-stretch">
        <div
          className={cn(
            'flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-neutral-100 bg-white',
            'p-4 shadow-[0_2px_12px_rgba(0,0,0,0.04)] sm:h-full sm:min-h-0 sm:max-w-none',
          )}
        >
          <div className="min-h-0 flex-1 overflow-y-auto overscroll-y-contain [scrollbar-gutter:stable]">
            <SellerAlertsBlock salesAgent={seller.sales_agent} embedded />
          </div>
        </div>
      </div>
    </div>
  )
}
