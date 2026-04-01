import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import { formatCurrency } from '../lib/format'
import { stageLabel } from '../lib/labels'
import { CheckCircle2, AlertCircle } from 'lucide-react'

interface Deal {
  id: number
  score: number
  product_name: string
  account_name: string
  agent_name: string
  potential_value: number
  deal_stage: string
  engage_date: string | null
}

interface Explanation {
  factor: string
  impact: 'positive' | 'negative' | 'neutral'
  text: string
}

function FocusCard({ deal, rank }: { deal: Deal; rank: number }) {
  const [explanations, setExplanations] = useState<Explanation[] | null>(null)

  useEffect(() => {
    api.getDealExplanation(deal.id)
      .then((data) => setExplanations(data.explanations))
      .catch(() => setExplanations([]))
  }, [deal.id])

  const isFirst = rank === 0
  const positives = explanations?.filter((e) => e.impact === 'positive') || []
  const negatives = explanations?.filter((e) => e.impact === 'negative') || []
  const scoreColor = deal.score >= 70 ? 'var(--success)' : deal.score >= 40 ? 'var(--g4-gold)' : 'var(--danger)'

  return (
    <div
      className="relative p-5 rounded-xl border flex flex-col shadow-[var(--shadow-sm)] hover:shadow-[var(--shadow-md)] transition-all"
      style={{
        background: isFirst ? 'linear-gradient(135deg, rgba(185,145,91,0.06) 0%, rgba(15,26,69,0.04) 100%)' : 'var(--bg-secondary)',
        borderColor: isFirst ? 'var(--g4-gold)' : 'var(--border)',
      }}
    >
      {isFirst && (
        <span className="absolute -top-2.5 left-3 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[var(--g4-gold)] text-[var(--g4-deep)] tracking-wider uppercase">
          #1 Prioridade
        </span>
      )}

      <div className="flex items-start justify-between mb-3">
        <span className="text-xs text-[var(--text-muted)] font-medium">#{rank + 1}</span>
        <div className="flex flex-col items-end">
          <span className="text-2xl font-bold" style={{ color: scoreColor }}>{deal.score}</span>
          <div className="w-16 h-1.5 rounded-full bg-[var(--bg-hover)] mt-1 overflow-hidden">
            <div className="h-full rounded-full" style={{ width: `${deal.score}%`, background: scoreColor }} />
          </div>
        </div>
      </div>

      <p className="font-bold text-sm text-[var(--text-primary)]">{deal.account_name}</p>
      <p className="text-xs text-[var(--text-secondary)] mb-1">{deal.product_name}</p>

      <div className="flex items-center justify-between mt-1 mb-3">
        <span className="text-sm font-semibold text-[var(--g4-gold)]">
          {formatCurrency(deal.potential_value)}
        </span>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
          deal.deal_stage === 'Engaging' ? 'bg-[var(--engaging-bg)] text-[var(--engaging-text)] font-semibold' : 'bg-[var(--prospecting-bg)] text-[var(--prospecting-text)] font-semibold'
        }`}>
          {stageLabel(deal.deal_stage)}
        </span>
      </div>

      <div className="border-t border-[var(--border)] my-2" />

      {!explanations ? (
        <div className="flex-1 flex items-center justify-center py-2">
          <span className="text-xs text-[var(--text-muted)]">Analisando...</span>
        </div>
      ) : (
        <div className="flex-1 space-y-1.5 mt-1">
          {positives.slice(0, 2).map((exp, i) => (
            <div key={`p${i}`} className="flex items-start gap-1.5">
              <CheckCircle2 size={12} strokeWidth={2} className="text-[var(--success)] mt-0.5 shrink-0" />
              <p className="text-xs text-[var(--text-primary)] leading-snug">{exp.text}</p>
            </div>
          ))}
          {negatives.slice(0, 1).map((exp, i) => (
            <div key={`n${i}`} className="flex items-start gap-1.5">
              <AlertCircle size={12} strokeWidth={2} className="text-[var(--danger)] mt-0.5 shrink-0" />
              <p className="text-xs text-[var(--text-secondary)] leading-snug">{exp.text}</p>
            </div>
          ))}
          {positives.length === 0 && negatives.length === 0 && (
            <p className="text-xs text-[var(--text-muted)]">Sem fatores destacados</p>
          )}
        </div>
      )}

      <div className="mt-3 pt-2 border-t border-[var(--border)]">
        <p className="text-[10px] text-[var(--text-muted)]">
          {deal.agent_name}
          {deal.engage_date && ` · ${new Date(deal.engage_date).toLocaleDateString('pt-BR')}`}
        </p>
      </div>
    </div>
  )
}

export function FocusSection({ deals }: { deals: Deal[] }) {
  return (
    <section>
      <div className="mb-4">
        <h2 className="text-lg font-bold text-[var(--g4-navy)]">Foco Hoje</h2>
        <p className="text-sm text-[var(--text-secondary)]">
          As 5 oportunidades com maior probabilidade de fechamento. Priorize estes contatos.
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {deals.map((deal, i) => (
          <FocusCard key={deal.id} deal={deal} rank={i} />
        ))}
      </div>
    </section>
  )
}
