import { useState, useEffect } from 'react'
import { ScoreBadge } from './ScoreBadge'
import { api } from '../lib/api'
import { formatCurrency } from '../lib/format'
import { stageLabel } from '../lib/labels'
import { CheckCircle2, AlertCircle, Info, ChevronDown, ChevronUp, Sparkles, Trophy, XCircle } from 'lucide-react'

interface Deal {
  id: number
  opportunity_id: string
  deal_stage: string
  score: number
  product_name: string
  account_name: string
  agent_name: string
  potential_value: number
  engage_date: string | null
}

interface Explanation {
  factor: string
  impact: 'positive' | 'negative' | 'neutral'
  text: string
}

interface Props {
  deal: Deal
  onClassified?: () => void
}

export function DealCard({ deal, onClassified }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [explanations, setExplanations] = useState<Explanation[] | null>(null)
  const [aiAnalysis, setAiAnalysis] = useState<string | null>(null)
  const [loadingExpl, setLoadingExpl] = useState(false)
  const [loadingAi, setLoadingAi] = useState(false)
  const [classifying, setClassifying] = useState<string | null>(null)
  const [showClassifyValue, setShowClassifyValue] = useState(false)
  const [closeValue, setCloseValue] = useState('')

  useEffect(() => {
    if (expanded && !explanations && !loadingExpl) {
      setLoadingExpl(true)
      api.getDealExplanation(deal.id)
        .then((data) => setExplanations(data.explanations))
        .catch(() => setExplanations([]))
        .finally(() => setLoadingExpl(false))
    }
  }, [expanded])

  async function requestAI(e: React.MouseEvent) {
    e.stopPropagation()
    setLoadingAi(true)
    try {
      const data = await api.getDealAIAnalysis(deal.id)
      setAiAnalysis(data.analysis)
    } catch (err: any) {
      setAiAnalysis('<p style="color:var(--danger)">Erro ao gerar análise</p>')
    } finally {
      setLoadingAi(false)
    }
  }

  async function handleClassify(stage: string, value: number = 0) {
    setClassifying(stage)
    try {
      await api.classifyDeal(deal.id, stage, value)
      onClassified?.()
    } catch (err: any) {
      alert('Erro: ' + err.message)
    } finally {
      setClassifying(null)
    }
  }

  const positives = explanations?.filter((e) => e.impact === 'positive') || []
  const negatives = explanations?.filter((e) => e.impact === 'negative') || []
  const neutrals = explanations?.filter((e) => e.impact === 'neutral') || []

  return (
    <div className="rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] overflow-hidden shadow-[var(--shadow-sm)] hover:shadow-[var(--shadow-md)] transition-all">
      <div
        className="flex items-center gap-4 p-4 cursor-pointer hover:bg-[var(--bg-hover)] transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-[var(--text-primary)] truncate">{deal.account_name} — {deal.product_name}</p>
          <p className="text-sm text-[var(--text-secondary)]">
            {stageLabel(deal.deal_stage)} | {deal.agent_name}
            {deal.engage_date && ` | ${new Date(deal.engage_date).toLocaleDateString('pt-BR')}`}
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="font-semibold text-[var(--text-primary)]">{formatCurrency(deal.potential_value)}</p>
          <p className="text-xs text-[var(--text-secondary)]">potencial</p>
        </div>
        <ScoreBadge score={deal.score} />
        {expanded ? <ChevronUp size={18} className="text-[var(--text-muted)] ml-1" /> : <ChevronDown size={18} className="text-[var(--text-muted)] ml-1" />}
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t border-[var(--border)]">
          {loadingExpl ? (
            <div className="py-4 text-center text-sm text-[var(--text-secondary)]">Analisando fatores...</div>
          ) : explanations && explanations.length > 0 ? (
            <div className="pt-4 space-y-4">
              <h4 className="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">
                Por que esse score?
              </h4>

              {positives.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-xs font-semibold text-[var(--success)] flex items-center gap-1.5">
                    <CheckCircle2 size={16} strokeWidth={1.8} />
                    Fatores positivos
                  </p>
                  {positives.map((exp, i) => (
                    <div key={`p${i}`} className="ml-7 pl-3 border-l-2 border-[var(--success)]/30 py-1">
                      <p className="text-sm text-[var(--text-primary)]">{exp.text}</p>
                    </div>
                  ))}
                </div>
              )}

              {negatives.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-xs font-semibold text-[var(--danger)] flex items-center gap-1.5">
                    <AlertCircle size={16} strokeWidth={1.8} />
                    Pontos de atenção
                  </p>
                  {negatives.map((exp, i) => (
                    <div key={`n${i}`} className="ml-7 pl-3 border-l-2 border-[var(--danger)]/30 py-1">
                      <p className="text-sm text-[var(--text-primary)]">{exp.text}</p>
                    </div>
                  ))}
                </div>
              )}

              {neutrals.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-xs font-semibold text-[var(--text-secondary)] flex items-center gap-1.5">
                    <Info size={16} strokeWidth={1.8} />
                    Contexto
                  </p>
                  {neutrals.map((exp, i) => (
                    <div key={`c${i}`} className="ml-7 pl-3 border-l-2 border-[var(--border)] py-1">
                      <p className="text-sm text-[var(--text-secondary)]">{exp.text}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Score bar */}
              <div className="mt-3 pt-3 border-t border-[var(--border)]">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[var(--text-secondary)]">Score</span>
                  <div className="flex-1 h-2 rounded-full bg-[var(--bg-hover)] overflow-hidden">
                    <div className="h-full rounded-full transition-all" style={{
                      width: `${deal.score}%`,
                      background: deal.score >= 70 ? 'var(--success)' : deal.score >= 40 ? 'var(--g4-gold)' : 'var(--danger)',
                    }} />
                  </div>
                  <span className="text-xs font-bold" style={{
                    color: deal.score >= 70 ? 'var(--success)' : deal.score >= 40 ? 'var(--g4-gold)' : 'var(--danger)',
                  }}>{deal.score}/100</span>
                </div>
              </div>

              {/* Actions row */}
              <div className="mt-3 pt-3 border-t border-[var(--border)] flex items-center gap-2 flex-wrap">
                {/* AI analysis */}
                {!aiAnalysis ? (
                  <button onClick={requestAI} disabled={loadingAi}
                    className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg bg-[var(--g4-navy)] text-white hover:bg-[var(--g4-deep)] transition-colors disabled:opacity-50 font-medium"
                  >
                    <Sparkles size={14} />
                    {loadingAi ? 'Gerando...' : 'Recomendação IA'}
                  </button>
                ) : null}

                {/* Classify buttons */}
                <div className="ml-auto flex items-center gap-2">
                  {!showClassifyValue ? (
                    <>
                      <button
                        onClick={(e) => { e.stopPropagation(); setShowClassifyValue(true) }}
                        disabled={!!classifying}
                        className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border border-[var(--success)]/40 text-[var(--success)] hover:bg-[var(--success)]/10 transition-colors font-medium disabled:opacity-50"
                      >
                        <Trophy size={14} />
                        Ganho
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleClassify('Lost') }}
                        disabled={!!classifying}
                        className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg border border-[var(--danger)]/40 text-[var(--danger)] hover:bg-[var(--danger)]/10 transition-colors font-medium disabled:opacity-50"
                      >
                        <XCircle size={14} />
                        {classifying === 'Lost' ? 'Salvando...' : 'Perdido'}
                      </button>
                    </>
                  ) : (
                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="number"
                        placeholder="Valor fechado (R$)"
                        value={closeValue}
                        onChange={(e) => setCloseValue(e.target.value)}
                        className="w-40 px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--success)]/40 text-sm focus:outline-none focus:border-[var(--success)]/50"
                        autoFocus
                      />
                      <button
                        onClick={() => handleClassify('Won', Number(closeValue) || 0)}
                        disabled={!!classifying || !closeValue}
                        className="px-3 py-2 rounded-lg bg-[var(--success)] text-white text-sm font-medium hover:bg-[var(--success)]/80 transition-colors disabled:opacity-50"
                      >
                        {classifying === 'Won' ? 'Salvando...' : 'Confirmar'}
                      </button>
                      <button
                        onClick={() => setShowClassifyValue(false)}
                        className="px-2 py-2 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                      >
                        <XCircle size={16} />
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* AI Analysis result (HTML) */}
              {aiAnalysis && (
                <div className="p-4 rounded-lg bg-[var(--g4-navy)]/5 border border-[var(--g4-navy)]/10">
                  <p className="text-xs font-bold text-[var(--g4-navy)] mb-2 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles size={14} /> Análise IA
                  </p>
                  <div
                    className="text-sm text-[var(--text-primary)] leading-relaxed [&_h4]:font-bold [&_h4]:text-[var(--g4-navy)] [&_h4]:mt-3 [&_h4]:mb-1 [&_ul]:ml-4 [&_ul]:list-disc [&_li]:mb-1 [&_p]:mb-2"
                    dangerouslySetInnerHTML={{ __html: aiAnalysis }}
                  />
                </div>
              )}
            </div>
          ) : (
            <div className="py-4 text-center text-sm text-[var(--text-secondary)]">Sem dados de análise disponíveis.</div>
          )}
        </div>
      )}
    </div>
  )
}
