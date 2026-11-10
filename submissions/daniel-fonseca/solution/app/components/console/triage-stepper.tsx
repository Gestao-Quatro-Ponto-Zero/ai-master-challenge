import { Check, Minus } from "lucide-react"

import type { ConsoleTriageResult } from "@/components/console/types"
import { fmt } from "@/lib/format"
import { cn } from "@/lib/utils"

/**
 * Etapas da triagem (PRD §4.4): embedding → casos parecidos → regra de decisão → redação.
 * Os tempos vêm de triage_runs.step_ms, medidos pelo n8n depois da resposta (sem simular progresso).
 * O fluxo mede a classificação (as 3 primeiras etapas) e a redação.
 */
export function TriageStepper({ result }: { result: ConsoleTriageResult }) {
  const writing =
    result.status === "auto_answered"
      ? "Adaptação da solução validada (LLM)"
      : result.status === "pending_review"
        ? "Rascunho e checagens para o revisor (LLM)"
        : result.status === "awaiting_human"
          ? "Resumo e sinais de risco para o time (LLM)"
          : "Redação"
  const classMs = result.step_ms?.classificacao
  const writeMs = result.step_ms?.redacao

  const groups = [
    {
      label: "Classificação",
      time: result.offline ? "no banco" : classMs != null ? fmt.ms(classMs) : null,
      steps: ["Embedding do ticket (OpenAI)", "Busca dos 50 casos mais parecidos (pgvector)", "Regra de decisão (limiares de confiança e categorias sensíveis)"],
      done: true,
    },
    {
      label: "Redação",
      time: result.offline ? "não executada" : writeMs != null ? fmt.ms(writeMs) : null,
      steps: [writing],
      done: !result.offline,
    },
  ]

  return (
    <section className="rounded-xl border border-border bg-surface p-5 shadow-soft" aria-labelledby="etapas-titulo">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 id="etapas-titulo" className="text-sm font-medium text-text-2">
          Etapas da triagem
        </h3>
        {result.latency_ms != null ? <span className="font-mono text-xs tabular-nums text-text-3">total {fmt.ms(result.latency_ms)}</span> : null}
      </div>
      <ol className="mt-4 flex flex-col gap-4">
        {groups.map((g, gi) => (
          <li key={g.label} className="relative pl-8 transition-opacity duration-300 motion-safe:animate-in motion-safe:fade-in" style={{ animationDelay: `${gi * 120}ms` }}>
            <span
              className={cn(
                "absolute left-0 top-0.5 flex size-5 items-center justify-center rounded-full border",
                g.done ? "border-transparent bg-text-1 text-bg" : "border-border bg-surface-2 text-text-3",
              )}
              aria-hidden
            >
              {g.done ? <Check className="size-3" /> : <Minus className="size-3" />}
            </span>
            {gi < groups.length - 1 ? <span className="absolute left-2.5 top-6 h-[calc(100%-0.5rem)] w-px bg-border" aria-hidden /> : null}
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-sm font-semibold text-text-1">{g.label}</p>
              {g.time ? <span className="font-mono text-xs tabular-nums text-text-2">{g.time}</span> : null}
            </div>
            <ul className="mt-1 space-y-0.5 text-sm text-text-2">
              {g.steps.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </li>
        ))}
      </ol>
    </section>
  )
}
