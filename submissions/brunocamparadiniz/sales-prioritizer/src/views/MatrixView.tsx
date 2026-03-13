import { useRef, useState, useMemo } from 'react'
import type { ScoredDeal } from '../scoring'

interface TooltipState {
  deal: ScoredDeal
  x: number
  y: number
}

const M = { top: 44, right: 24, bottom: 52, left: 72 }
const W = 720 - M.left - M.right
const H = 420 - M.top - M.bottom

function dot(score: number): string {
  if (score >= 80) return '#10b981'
  if (score >= 60) return '#3b82f6'
  if (score >= 40) return '#f59e0b'
  return '#94a3b8'
}

function lerp(v: number, [d0, d1]: [number, number], [r0, r1]: [number, number]): number {
  return r0 + ((v - d0) / (d1 - d0)) * (r1 - r0)
}

export function MatrixView({ deals }: { deals: ScoredDeal[] }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [tooltip, setTooltip] = useState<TooltipState | null>(null)

  const maxPrice = useMemo(() => {
    const max = Math.max(...deals.map((d) => d.list_price))
    return max > 0 ? max * 1.08 : 6000
  }, [deals])

  const medianPrice = useMemo(() => {
    const sorted = [...deals].map((d) => d.list_price).sort((a, b) => a - b)
    return sorted[Math.floor(sorted.length / 2)] ?? maxPrice / 2
  }, [deals, maxPrice])

  const xOf = (d: ScoredDeal) => lerp(d.scoreBreakdown.winRate, [0, 100], [0, W])
  const yOf = (d: ScoredDeal) => lerp(d.list_price, [0, maxPrice], [H, 0])

  const xQ = lerp(50, [0, 100], [0, W])
  const yQ = lerp(medianPrice, [0, maxPrice], [H, 0])

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((t) => ({
    val: t * maxPrice,
    y: lerp(t * maxPrice, [0, maxPrice], [H, 0]),
    label: t * maxPrice >= 1000 ? `$${((t * maxPrice) / 1000).toFixed(0)}k` : `$${(t * maxPrice).toFixed(0)}`,
  }))

  function handleMouseEnter(e: React.MouseEvent, deal: ScoredDeal) {
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return
    setTooltip({ deal, x: e.clientX - rect.left, y: e.clientY - rect.top })
  }

  function handleMouseMove(e: React.MouseEvent, deal: ScoredDeal) {
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return
    setTooltip({ deal, x: e.clientX - rect.left, y: e.clientY - rect.top })
  }

  return (
    <div className="glass-card p-4">
      <div className="mb-4">
        <h2 className="text-slate-800 font-semibold text-sm">Matrix Risco × Recompensa</h2>
        <p className="text-slate-400 text-xs mt-0.5">
          Eixo X: Probabilidade de fechamento (Win Rate histórico) · Eixo Y: Valor do deal · {deals.length} deals ativos
        </p>
      </div>

      <div ref={containerRef} className="relative overflow-x-auto">
        <svg
          viewBox={`0 0 ${W + M.left + M.right} ${H + M.top + M.bottom}`}
          className="w-full"
          style={{ minWidth: 480 }}
        >
          <g transform={`translate(${M.left},${M.top})`}>
            {/* Quadrant fills */}
            <rect x={xQ} y={0}  width={W - xQ} height={yQ}      fill="#d1fae5" opacity={0.6} />
            <rect x={0}  y={0}  width={xQ}      height={yQ}      fill="#f1f5f9" opacity={0.6} />
            <rect x={xQ} y={yQ} width={W - xQ} height={H - yQ}  fill="#dbeafe" opacity={0.5} />
            <rect x={0}  y={yQ} width={xQ}      height={H - yQ}  fill="#f8fafc" opacity={0.4} />

            {/* Quadrant labels */}
            <text x={xQ + 8} y={14}      fill="#059669" fontSize={11} fontWeight="600">🏆 Quadrante de Ouro</text>
            <text x={8}      y={14}      fill="#94a3b8" fontSize={11}>⬆ Incerto</text>
            <text x={xQ + 8} y={H - 8}  fill="#3b82f6" fontSize={11}>⚡ Esforço (volume)</text>
            <text x={8}      y={H - 8}  fill="#cbd5e1" fontSize={11}>❄ Frio</text>

            {/* Quadrant dividers */}
            <line x1={xQ} y1={0} x2={xQ} y2={H} stroke="#cbd5e1" strokeWidth={1} strokeDasharray="5 3" />
            <line x1={0} y1={yQ} x2={W} y2={yQ} stroke="#cbd5e1" strokeWidth={1} strokeDasharray="5 3" />

            {/* Axes */}
            <line x1={0} y1={H} x2={W} y2={H} stroke="#e2e8f0" />
            <line x1={0} y1={0} x2={0} y2={H} stroke="#e2e8f0" />

            {/* Y ticks */}
            {yTicks.map(({ val, y, label }) => (
              <g key={val}>
                <line x1={-4} y1={y} x2={0} y2={y} stroke="#cbd5e1" />
                <text x={-8} y={y + 4} textAnchor="end" fill="#94a3b8" fontSize={10}>{label}</text>
              </g>
            ))}
            <text
              transform={`rotate(-90) translate(${-H / 2},${-56})`}
              textAnchor="middle" fill="#94a3b8" fontSize={11}
            >
              Valor do Deal
            </text>

            {/* X ticks */}
            {[0, 25, 50, 75, 100].map((v) => {
              const x = lerp(v, [0, 100], [0, W])
              return (
                <g key={v}>
                  <line x1={x} y1={H} x2={x} y2={H + 4} stroke="#cbd5e1" />
                  <text x={x} y={H + 15} textAnchor="middle" fill="#94a3b8" fontSize={10}>{v}%</text>
                </g>
              )
            })}
            <text x={W / 2} y={H + 38} textAnchor="middle" fill="#94a3b8" fontSize={11}>
              Probabilidade de Fechamento (Win Rate)
            </text>

            {/* Dots */}
            {deals.map((deal) => (
              <circle
                key={deal.opportunity_id}
                cx={xOf(deal)}
                cy={yOf(deal)}
                r={deal.deal_stage === 'Engaging' ? 6 : 4}
                fill={dot(deal.score)}
                opacity={0.85}
                style={{ cursor: 'pointer' }}
                onMouseEnter={(e) => handleMouseEnter(e, deal)}
                onMouseMove={(e) => handleMouseMove(e, deal)}
                onMouseLeave={() => setTooltip(null)}
              />
            ))}
          </g>
        </svg>

        {/* Tooltip */}
        {tooltip && (
          <div
            className="absolute z-10 pointer-events-none bg-white/90 backdrop-blur-md border border-slate-200 rounded-xl p-3 text-xs shadow-lg"
            style={{ left: tooltip.x + 14, top: Math.max(0, tooltip.y - 60), width: 210 }}
          >
            <div className="font-semibold text-slate-800 mb-1 truncate">{tooltip.deal.account}</div>
            <div className="text-slate-500 mb-2">{tooltip.deal.sales_agent}</div>
            <div className="space-y-1 text-slate-400">
              <div className="flex justify-between">
                <span>Score</span>
                <span className="text-slate-800 font-bold">{tooltip.deal.score}</span>
              </div>
              <div className="flex justify-between">
                <span>Valor</span>
                <span className="text-slate-700">${tooltip.deal.list_price.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span>Win Rate</span>
                <span className="text-slate-700">{tooltip.deal.scoreBreakdown.winRate}%</span>
              </div>
              <div className="flex justify-between">
                <span>Estágio</span>
                <span className="text-slate-700">{tooltip.deal.deal_stage}</span>
              </div>
              {tooltip.deal.stagnation.isStagnant && (
                <div className="text-amber-500 pt-1">⏰ Estagnado {tooltip.deal.stagnation.daysEngaging}d</div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mt-4 text-xs text-slate-400">
        {[
          { color: '#10b981', label: 'Score ≥ 80' },
          { color: '#3b82f6', label: 'Score 60–79' },
          { color: '#f59e0b', label: 'Score 40–59' },
          { color: '#94a3b8', label: 'Score < 40' },
        ].map(({ color, label }) => (
          <span key={label} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color, display: 'inline-block' }} />
            {label}
          </span>
        ))}
        <span className="flex items-center gap-2 ml-4 text-slate-400">
          <span>● Engaging</span><span className="text-xs">· Prospecting</span>
        </span>
      </div>
    </div>
  )
}
