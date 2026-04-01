import { useState, useEffect } from 'react'
import { useData } from './Dashboard'
import { api } from '../lib/api'
import { formatCurrency } from '../lib/format'
import { stageLabel } from '../lib/labels'
import { X, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react'

interface Props {
  onClose: () => void
}

interface Explanation {
  factor: string
  impact: 'positive' | 'negative' | 'neutral'
  text: string
}

export function DealCompare({ onClose }: Props) {
  const { deals } = useData()
  const [dealA, setDealA] = useState<number>(0)
  const [dealB, setDealB] = useState<number>(0)
  const [explA, setExplA] = useState<Explanation[] | null>(null)
  const [explB, setExplB] = useState<Explanation[] | null>(null)

  useEffect(() => {
    if (dealA) api.getDealExplanation(dealA).then((d) => setExplA(d.explanations)).catch(() => setExplA([]))
    else setExplA(null)
  }, [dealA])

  useEffect(() => {
    if (dealB) api.getDealExplanation(dealB).then((d) => setExplB(d.explanations)).catch(() => setExplB([]))
    else setExplB(null)
  }, [dealB])

  const a = deals.find((d) => d.id === dealA)
  const b = deals.find((d) => d.id === dealB)

  const selectClass = "w-full px-3 py-2.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border)] text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--g4-gold)]"

  function renderDealColumn(deal: any, explanations: Explanation[] | null) {
    if (!deal) return <div className="flex-1 flex items-center justify-center text-sm text-[var(--text-muted)] py-12">Selecione uma oportunidade</div>

    const positives = explanations?.filter((e) => e.impact === 'positive') || []
    const negatives = explanations?.filter((e) => e.impact === 'negative') || []
    const scoreColor = deal.score >= 70 ? 'var(--success)' : deal.score >= 40 ? 'var(--g4-gold)' : 'var(--danger)'

    return (
      <div className="flex-1 space-y-4">
        <div className="text-center">
          <div className="text-3xl font-bold mb-1" style={{ color: scoreColor }}>{deal.score}</div>
          <div className="w-full h-2 rounded-full bg-[var(--bg-primary)] overflow-hidden">
            <div className="h-full rounded-full" style={{ width: `${deal.score}%`, background: scoreColor }} />
          </div>
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex justify-between"><span className="text-[var(--text-secondary)]">Conta</span><span className="font-medium">{deal.account_name}</span></div>
          <div className="flex justify-between"><span className="text-[var(--text-secondary)]">Produto</span><span className="font-medium">{deal.product_name}</span></div>
          <div className="flex justify-between"><span className="text-[var(--text-secondary)]">Etapa</span><span className="font-medium">{stageLabel(deal.deal_stage)}</span></div>
          <div className="flex justify-between"><span className="text-[var(--text-secondary)]">Valor</span><span className="font-semibold text-[var(--g4-gold)]">{formatCurrency(deal.potential_value)}</span></div>
          <div className="flex justify-between"><span className="text-[var(--text-secondary)]">Vendedor</span><span>{deal.agent_name}</span></div>
        </div>

        {explanations && (
          <div className="space-y-1.5 pt-3 border-t border-[var(--border)]">
            {positives.map((e, i) => (
              <div key={`p${i}`} className="flex items-start gap-1.5 text-xs">
                <CheckCircle2 size={12} className="text-[var(--success)] mt-0.5 shrink-0" />
                <span className="text-[var(--text-primary)]">{e.text}</span>
              </div>
            ))}
            {negatives.map((e, i) => (
              <div key={`n${i}`} className="flex items-start gap-1.5 text-xs">
                <AlertCircle size={12} className="text-[var(--danger)] mt-0.5 shrink-0" />
                <span className="text-[var(--text-secondary)]">{e.text}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  const winner = a && b ? (a.score > b.score ? 'A' : a.score < b.score ? 'B' : 'empate') : null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-3xl bg-[var(--bg-secondary)] rounded-2xl shadow-[var(--shadow-lg)] overflow-hidden max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-5 border-b border-[var(--border)]">
          <h3 className="text-lg font-bold text-[var(--g4-navy)]">Comparar Oportunidades</h3>
          <button onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"><X size={20} /></button>
        </div>

        <div className="p-5 overflow-y-auto">
          {/* Selectors */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wider">Oportunidade A</label>
              <select value={dealA} onChange={(e) => setDealA(Number(e.target.value))} className={selectClass}>
                <option value={0}>Selecione...</option>
                {deals.map((d) => (
                  <option key={d.id} value={d.id}>{d.account_name} — {d.product_name} (Score: {d.score})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)] mb-1.5 uppercase tracking-wider">Oportunidade B</label>
              <select value={dealB} onChange={(e) => setDealB(Number(e.target.value))} className={selectClass}>
                <option value={0}>Selecione...</option>
                {deals.filter((d) => d.id !== dealA).map((d) => (
                  <option key={d.id} value={d.id}>{d.account_name} — {d.product_name} (Score: {d.score})</option>
                ))}
              </select>
            </div>
          </div>

          {/* Recommendation */}
          {winner && winner !== 'empate' && (
            <div className="mb-6 p-4 rounded-xl bg-[var(--g4-gold)]/8 border border-[var(--g4-gold)]/20">
              <div className="flex items-center gap-2 text-sm font-semibold text-[var(--g4-navy)]">
                <ArrowRight size={16} />
                Recomendação: priorize <strong className="text-[var(--g4-gold)]">{winner === 'A' ? a?.account_name : b?.account_name}</strong> (score {winner === 'A' ? a?.score : b?.score} vs {winner === 'A' ? b?.score : a?.score})
              </div>
            </div>
          )}

          {/* Side by side */}
          <div className="flex gap-6">
            {renderDealColumn(a, explA)}
            {a && b && (
              <div className="flex items-center">
                <div className="w-px h-full bg-[var(--border)]" />
              </div>
            )}
            {renderDealColumn(b, explB)}
          </div>
        </div>
      </div>
    </div>
  )
}
