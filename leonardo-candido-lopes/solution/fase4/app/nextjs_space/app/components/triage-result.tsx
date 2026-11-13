'use client'

import {
  Globe, Tag, BarChart2, ShieldCheck, AlertTriangle, AlertOctagon,
  CheckCircle2, UserCheck, Clock, ChevronDown, ChevronUp, Zap,
  ArrowRight, FileWarning
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'

const DOMAIN_CONFIG: Record<string, { color: string; bg: string; icon: any; label: string }> = {
  IT_INTERNAL: { color: 'text-blue-700 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-950/40', icon: Globe, label: 'TI Interno' },
  FINANCIAL_COMMERCIAL: { color: 'text-orange-700 dark:text-orange-400', bg: 'bg-orange-50 dark:bg-orange-950/40', icon: FileWarning, label: 'Financeiro / Comercial' },
  OUT_OF_SCOPE: { color: 'text-gray-600 dark:text-gray-400', bg: 'bg-gray-100 dark:bg-gray-800/40', icon: AlertTriangle, label: 'Fora do Escopo' },
  INDETERMINATE: { color: 'text-amber-700 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-950/40', icon: AlertTriangle, label: 'Indeterminado' },
}

const DECISION_CONFIG: Record<string, { color: string; bg: string; border: string; icon: any; label: string; desc: string }> = {
  AUTOMATIC: { color: 'text-emerald-700 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-950/30', border: 'border-emerald-200 dark:border-emerald-800', icon: CheckCircle2, label: 'Automático', desc: 'Roteamento automático sugerido' },
  ASSISTED: { color: 'text-blue-700 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-950/30', border: 'border-blue-200 dark:border-blue-800', icon: UserCheck, label: 'Assistido', desc: 'Agente deve confirmar a sugestão' },
  HUMAN_REQUIRED: { color: 'text-amber-700 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-950/30', border: 'border-amber-200 dark:border-amber-800', icon: AlertTriangle, label: 'Revisão Humana', desc: 'Requer avaliação de um agente' },
  ESCALATE: { color: 'text-red-700 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-950/30', border: 'border-red-200 dark:border-red-800', icon: AlertOctagon, label: 'Escalação', desc: 'Encaminhar imediatamente à supervisão' },
}

const PRIORITY_CONFIG: Record<string, { color: string; bg: string }> = {
  LOW: { color: 'text-gray-600 dark:text-gray-400', bg: 'bg-gray-100 dark:bg-gray-800' },
  MEDIUM: { color: 'text-blue-700 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/40' },
  HIGH: { color: 'text-orange-700 dark:text-orange-400', bg: 'bg-orange-100 dark:bg-orange-900/40' },
  CRITICAL: { color: 'text-red-700 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/40' },
}

interface TriageResultProps {
  result: any
}

export function TriageResult({ result }: TriageResultProps) {
  const [traceOpen, setTraceOpen] = useState(false)

  if (!result) return null

  const domain = result?.domain ?? 'INDETERMINATE'
  const decision = result?.decision ?? 'HUMAN_REQUIRED'
  const priority = result?.priority ?? 'MEDIUM'
  const confidence = result?.confidence ?? 0
  const confPercent = Math.round(confidence * 100)
  const categoryReliable = result?.category_reliable !== false

  const domainCfg = DOMAIN_CONFIG[domain] ?? DOMAIN_CONFIG.INDETERMINATE
  const decisionCfg = DECISION_CONFIG[decision] ?? DECISION_CONFIG.HUMAN_REQUIRED
  const priorityCfg = PRIORITY_CONFIG[priority] ?? PRIORITY_CONFIG.MEDIUM
  const DomainIcon = domainCfg.icon
  const DecisionIcon = decisionCfg.icon

  return (
    <div className="space-y-4">
      {/* Card 1: Domínio & Categoria */}
      <div className="rounded-lg border border-border/60 bg-card p-4" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
          <Globe className="h-3.5 w-3.5" />
          Domínio e Categoria
        </div>

        <div className={cn('mb-3 inline-flex items-center gap-2 rounded-md px-3 py-1.5', domainCfg.bg)}>
          <DomainIcon className={cn('h-4 w-4', domainCfg.color)} />
          <span className={cn('text-sm font-semibold', domainCfg.color)}>{domainCfg.label}</span>
        </div>

        {domain === 'IT_INTERNAL' && result?.category && (
          <div className="mb-3">
            <div className="flex flex-wrap items-center gap-2">
              <Tag className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Categoria prevista:</span>
              <span className={cn('text-sm font-semibold', categoryReliable ? 'text-foreground' : 'text-amber-700 line-through decoration-amber-500/60 dark:text-amber-400')}>{result.category}</span>
              {!categoryReliable && (
                <span className="inline-flex items-center gap-1 rounded-md border border-amber-300 bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-800 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-300">
                  <AlertTriangle className="h-3 w-3" />
                  Categoria não confiável
                </span>
              )}
            </div>
            {!categoryReliable && (
              <p className="mt-1.5 text-[11px] leading-relaxed text-amber-700 dark:text-amber-400">
                Uma regra de segurança sobrepôs a decisão do classificador. A categoria acima foi <strong>preservada apenas para rastreabilidade</strong> e <strong>não deve ser tratada como orientação válida</strong>.
              </p>
            )}
          </div>
        )}

        {/* Top 3 */}
        {(result?.top3?.length ?? 0) > 0 && (
          <div className="space-y-1.5">
            <span className="text-xs text-muted-foreground">Top 3 categorias:</span>
            {(result.top3 ?? []).map((item: any, idx: number) => {
              const cat = item?.[0] ?? 'N/A'
              const prob = item?.[1] ?? 0
              const pct = Math.round(prob * 100)
              return (
                <div key={idx} className="flex items-center gap-2">
                  <span className="w-32 truncate text-xs font-medium text-foreground">{cat}</span>
                  <div className="flex-1">
                    <Progress value={pct} className="h-2" />
                  </div>
                  <span className="w-10 text-right font-mono text-xs text-muted-foreground">{pct}%</span>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Card 2: Confiança e Decisão */}
      <div className={cn('rounded-lg border p-4', decisionCfg.border, decisionCfg.bg)} style={{ boxShadow: 'var(--shadow-sm)' }}>
        <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
          <Zap className="h-3.5 w-3.5" />
          Confiança e Decisão Operacional
        </div>

        {/* Confidence bar */}
        <div className="mb-4">
          <div className="mb-1 flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Confiança do modelo</span>
            <span className="font-mono text-sm font-bold text-foreground">{confPercent}%</span>
          </div>
          <Progress
            value={confPercent}
            className={cn('h-3', confPercent >= 70 ? '[&>div]:bg-emerald-500' : confPercent >= 55 ? '[&>div]:bg-blue-500' : '[&>div]:bg-amber-500')}
          />
        </div>

        {/* Decision */}
        <div className="flex items-center gap-3">
          <DecisionIcon className={cn('h-6 w-6', decisionCfg.color)} />
          <div>
            <div className={cn('text-base font-bold', decisionCfg.color)}>{decisionCfg.label}</div>
            <div className="text-xs text-muted-foreground">{decisionCfg.desc}</div>
          </div>
        </div>

        {result?.rule_triggered && (
          <div className="mt-3 rounded-md bg-card/50 px-3 py-2">
            <span className="text-xs text-muted-foreground">Regra ativada: </span>
            <span className="font-mono text-xs font-medium text-foreground">{result.rule_triggered}</span>
          </div>
        )}
      </div>

      {/* Card 3: Prioridade e Fila */}
      <div className="rounded-lg border border-border/60 bg-card p-4" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
          <BarChart2 className="h-3.5 w-3.5" />
          Prioridade e Fila
        </div>

        <div className="flex items-center gap-3">
          <Badge className={cn('text-xs font-bold', priorityCfg.bg, priorityCfg.color)}>
            {priority}
          </Badge>
          <div className="flex items-center gap-1.5 text-sm text-foreground">
            <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="font-medium">{result?.queue ?? 'N/A'}</span>
          </div>
        </div>
      </div>

      {/* Card 4: Justificativa */}
      <div className="rounded-lg border border-border/60 bg-card p-4" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5" />
          Justificativa
        </div>
        <p className="text-sm leading-relaxed text-foreground">
          {result?.justification ?? 'Sem justificativa disponível.'}
        </p>

        {(decision === 'HUMAN_REQUIRED' || decision === 'ESCALATE') && (
          <div className={cn(
            'mt-3 rounded-md border px-3 py-2 text-xs',
            decision === 'ESCALATE'
              ? 'border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950/30 dark:text-red-300'
              : 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-300'
          )}>
            ⚠ Esta sugestão requer validação humana antes de qualquer ação operacional.
          </div>
        )}
      </div>

      {/* Card 5: Rastreabilidade */}
      <div className="rounded-lg border border-border/60 bg-card" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <button
          onClick={() => setTraceOpen(!traceOpen)}
          className="flex w-full items-center justify-between px-4 py-3 text-left"
        >
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            <Clock className="h-3.5 w-3.5" />
            Rastreabilidade
          </div>
          {traceOpen ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </button>
        {traceOpen && (
          <div className="space-y-2 border-t border-border/40 px-4 py-3">
            <TraceRow label="Timestamp" value={result?.timestamp} mono />
            <TraceRow label="Modelo" value={`v${result?.model_version ?? '?'}`} mono />
            <TraceRow label="Domínio" value={domain} />
            <TraceRow label="Categoria" value={result?.category ?? 'N/A'} />
            <TraceRow label="Categoria (crua)" value={result?.category_raw ?? result?.category ?? 'N/A'} />
            <TraceRow label="Categoria confiável" value={categoryReliable ? 'Sim' : 'Não — sobreposta por regra de segurança'} />
            <TraceRow label="Confiança" value={`${confPercent}% (${confidence?.toFixed?.(4) ?? '0'})`} mono />
            <TraceRow label="Decisão" value={decision} />
            <TraceRow label="Regra" value={result?.rule_triggered ?? 'Nenhuma'} mono />
            <TraceRow label="Prioridade" value={priority} />
          </div>
        )}
      </div>

      {/* Aviso global */}
      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-800/50 dark:bg-amber-950/20">
        <p className="text-xs leading-relaxed text-amber-800 dark:text-amber-300">
          <strong>Aviso:</strong> Esta análise é uma <strong>sugestão do modelo</strong>. Decisões operacionais devem ser validadas por um agente humano antes da execução.
        </p>
      </div>
    </div>
  )
}

function TraceRow({ label, value, mono }: { label: string; value?: string; mono?: boolean }) {
  return (
    <div className="flex items-start gap-2">
      <span className="w-24 shrink-0 text-xs text-muted-foreground">{label}:</span>
      <span className={cn('text-xs text-foreground break-all', mono && 'font-mono')}>{value ?? '—'}</span>
    </div>
  )
}
