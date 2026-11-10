import { ArrowRight, Check, ChevronDown, CloudOff, Inbox, ListChecks, Send, Sparkles, X } from "lucide-react"
import Link from "next/link"

import { CATEGORY_BG, CategoryChip, ConfidenceBar } from "@/components/console/category"
import { TriageStepper } from "@/components/console/triage-stepper"
import type { ConsoleTriageResult } from "@/components/console/types"
import { PathBadge } from "@/components/shared/path-badge"
import { fmt } from "@/lib/format"
import { pathFromLevel } from "@/lib/paths"
import type { Category } from "@/lib/types"
import { cn } from "@/lib/utils"

/** Resultado da triagem, de cima para baixo na ordem do PRD §4.4. */
export function TriageResultView({ result }: { result: ConsoleTriageResult }) {
  const path = pathFromLevel(result.level)
  const learned = result.resolutions?.[0]?.source === "hitl"
  return (
    <div className="flex flex-col gap-5">
      {result.offline ? (
        <div role="status" className="flex items-start gap-3 rounded-xl border border-border bg-surface-2 p-4 text-sm text-text-2">
          <CloudOff className="mt-0.5 size-4 shrink-0 text-text-3" aria-hidden />
          <p>
            <strong className="font-semibold text-text-1">Modo offline.</strong> O fluxo de triagem não respondeu. A classificação veio direto do banco, com a mesma regra de
            limiares, sem redação e sem registro.
          </p>
        </div>
      ) : null}

      {/* 1. Caminho e motivo */}
      <section className="rounded-xl border border-border bg-surface p-5 shadow-soft" aria-labelledby="caminho-titulo">
        <p id="caminho-titulo" className="font-mono text-xs uppercase tracking-[0.14em] text-text-3">
          {result.offline ? "Caminho indicado" : "Caminho"}
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <PathBadge path={path} size="lg" className={path === "review" ? "border-2" : undefined} />
        </div>
        <p className="mt-3 font-serif text-lg leading-snug text-text-1">{result.level_reason}</p>
        {result.true_category ? <TrueLabel predicted={result.category} actual={result.true_category} /> : null}
      </section>

      {/* 2. Categoria, confiança e votos */}
      <section className="rounded-xl border border-border bg-surface p-5 shadow-soft" aria-labelledby="categoria-titulo">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 id="categoria-titulo" className="text-sm font-medium text-text-2">
            Categoria prevista
          </h3>
          <span className="font-mono text-sm tabular-nums text-text-1">{fmt.pct(result.confidence, 0)} de confiança</span>
        </div>
        <CategoryChip category={result.category} className="mt-2 text-base" />
        <ConfidenceBar value={result.confidence} className="mt-3" />
        <Votes votes={result.votes} />
      </section>

      {/* 3. Ação tomada */}
      <ActionTaken result={result} learned={learned} />

      {!result.offline && result.resolutions?.length ? <Resolutions result={result} /> : null}

      {/* 4. Etapas */}
      <TriageStepper result={result} />

      {/* 5. Casos parecidos */}
      <section className="rounded-xl border border-border bg-surface p-5 shadow-soft" aria-labelledby="casos-titulo">
        <h3 id="casos-titulo" className="text-sm font-medium text-text-2">
          Os {result.similar_cases.length} casos mais parecidos na base de treino
        </h3>
        <ol className="mt-3 flex flex-col divide-y divide-border">
          {result.similar_cases.map((c) => (
            <li key={c.id} className="flex flex-col gap-1.5 py-3 first:pt-0 last:pb-0">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <CategoryChip category={c.category} />
                <span className="font-mono text-xs tabular-nums text-text-3">similaridade {fmt.dec(c.similarity, 2)}</span>
              </div>
              <p className="line-clamp-2 font-mono text-xs leading-relaxed text-text-2">{c.snippet}</p>
            </li>
          ))}
        </ol>
        <p className="mt-3 text-xs text-text-3">Texto dos casos já normalizado pelo dataset (minúsculas, sem pontuação).</p>
      </section>

      {/* 6. Rodapé técnico */}
      <TechFooter result={result} />
    </div>
  )
}

function TrueLabel({ predicted, actual }: { predicted: Category; actual: Category }) {
  const hit = predicted === actual
  return (
    <p className="mt-4 flex flex-wrap items-center gap-2 border-t border-border pt-4 text-sm text-text-2">
      <span>Categoria real:</span>
      <CategoryChip category={actual} />
      <span className={cn("inline-flex items-center gap-1 font-semibold", hit ? "text-ok" : "text-alert")}>
        {hit ? <Check className="size-4" aria-hidden /> : <X className="size-4" aria-hidden />}
        {hit ? "acerto" : "erro de classificação"}
      </span>
    </p>
  )
}

function Votes({ votes }: { votes: Partial<Record<Category, number>> }) {
  const entries = (Object.entries(votes ?? {}) as [Category, number][]).filter(([, v]) => v >= 0.005).sort((a, b) => b[1] - a[1])
  if (!entries.length) return null
  return (
    <div className="mt-4">
      <p className="text-xs text-text-3">Distribuição dos votos dos 50 vizinhos</p>
      <ul className="mt-2 flex flex-col gap-1.5">
        {entries.map(([cat, v]) => (
          <li key={cat} className="grid grid-cols-[minmax(0,9rem)_1fr_3rem] items-center gap-2 text-xs sm:grid-cols-[11rem_1fr_3rem]">
            <span className="truncate text-text-2">{cat}</span>
            <span className="h-1.5 overflow-hidden rounded-full bg-surface-2">
              <span className={cn("block h-full rounded-full", CATEGORY_BG[cat] ?? "bg-text-3")} style={{ width: `${Math.max(2, v * 100)}%` }} />
            </span>
            <span className="text-right font-mono tabular-nums text-text-2">{fmt.pct(v, 0)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function ActionTaken({ result, learned }: { result: ConsoleTriageResult; learned: boolean }) {
  const linkCls = "inline-flex items-center gap-1 font-semibold text-text-1 underline underline-offset-4 hover:no-underline"
  let icon = <CloudOff className="size-4" aria-hidden />
  let title = "Nenhuma ação"
  let body: React.ReactNode = "No modo offline a triagem só classifica. A resposta, o rascunho ou o alerta voltam quando o fluxo responder."

  if (!result.offline && result.status === "auto_answered") {
    icon = <Send className="size-4" aria-hidden />
    title = "Resposta enviada ao cliente"
    body = (
      <>
        {learned ? (
          <p className="mb-3 inline-flex items-center gap-1.5 text-sm font-medium text-ok">
            <Sparkles className="size-4" aria-hidden />
            Adaptada de uma solução aprendida na revisão humana
          </p>
        ) : null}
        <blockquote className="whitespace-pre-line rounded-lg border-l-2 border-path-auto bg-surface-2 p-4 text-sm leading-relaxed text-text-1">{result.response_text}</blockquote>
      </>
    )
  } else if (!result.offline && result.hitl) {
    icon = <ListChecks className="size-4" aria-hidden />
    title = "Rascunho na fila de revisão"
    body = (
      <p>
        Um agente aprova, edita ou rejeita antes do envio.{" "}
        <Link href={`/console?aba=fila&item=${result.hitl.hitl_id}`} className={linkCls}>
          Abrir item #{result.hitl.hitl_id} na fila <ArrowRight className="size-3.5" aria-hidden />
        </Link>
      </p>
    )
  } else if (!result.offline && result.notification) {
    icon = <Inbox className="size-4" aria-hidden />
    title = "Alerta na caixa para o time"
    body = (
      <p>
        A IA não respondeu ao cliente: resumiu o pedido e avisou o time.{" "}
        <Link href={`/console?aba=caixa&item=${result.notification.notification_id}`} className={linkCls}>
          Abrir alerta na caixa <ArrowRight className="size-3.5" aria-hidden />
        </Link>
      </p>
    )
  }

  return (
    <section className="rounded-xl border border-border bg-surface p-5 shadow-soft" aria-labelledby="acao-titulo">
      <h3 id="acao-titulo" className="flex items-center gap-2 text-sm font-semibold text-text-1">
        {icon}
        {title}
      </h3>
      <div className="mt-2 text-sm leading-relaxed text-text-2">{body}</div>
    </section>
  )
}

function Resolutions({ result }: { result: ConsoleTriageResult }) {
  return (
    <section className="rounded-xl border border-border bg-surface p-5 shadow-soft" aria-labelledby="solucoes-titulo">
      <h3 id="solucoes-titulo" className="text-sm font-medium text-text-2">
        Soluções validadas de {result.category} usadas pela IA
      </h3>
      <ol className="mt-3 flex flex-col gap-3">
        {result.resolutions.map((r) => (
          <li key={r.id} className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className={cn("inline-flex items-center gap-1 text-xs font-medium", r.source === "hitl" ? "text-ok" : "text-text-3")}>
                {r.source === "hitl" ? <Sparkles className="size-3.5" aria-hidden /> : null}
                {r.source === "hitl" ? "aprendida na revisão humana" : "playbook"} · #{r.id}
              </span>
              <span className="font-mono text-xs tabular-nums text-text-3">similaridade {fmt.dec(r.similarity, 2)}</span>
            </div>
            <p className="line-clamp-2 text-sm leading-relaxed text-text-2">{r.resolution_text}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}

function TechFooter({ result }: { result: ConsoleTriageResult }) {
  const rows: [string, string][] = [
    ["ID da triagem", result.triage_run_id ? `#${result.triage_run_id}` : "sem registro (offline)"],
    ["Ticket do holdout", result.ds2_id ? `#${result.ds2_id}` : "texto livre"],
    ["Tempo total no app", result.latency_ms != null ? fmt.ms(result.latency_ms) : "—"],
    ["Tempo no fluxo n8n", result.n8n_latency_ms != null ? fmt.ms(result.n8n_latency_ms) : "—"],
    ["Classificação", result.step_ms?.classificacao != null ? fmt.ms(result.step_ms.classificacao) : "—"],
    ["Redação", result.step_ms?.redacao != null ? fmt.ms(result.step_ms.redacao) : "—"],
    ["Tokens (entrada · saída)", result.tokens_in != null ? `${fmt.int(result.tokens_in)} · ${fmt.int(result.tokens_out ?? 0)}` : "—"],
    ["Custo OpenAI da chamada", result.cost_usd != null ? fmt.usd(result.cost_usd, 6) : "—"],
  ]
  return (
    <details className="group rounded-xl border border-border bg-surface px-5 py-3">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-2 py-1 text-sm font-medium text-text-2 hover:text-text-1 [&::-webkit-details-marker]:hidden">
        Detalhes técnicos
        <ChevronDown className="size-4 transition-transform group-open:rotate-180" aria-hidden />
      </summary>
      <dl className="mt-3 grid grid-cols-1 gap-x-6 gap-y-2 pb-2 text-sm sm:grid-cols-2">
        {rows.map(([k, v]) => (
          <div key={k} className="flex items-baseline justify-between gap-3 border-b border-border pb-1.5">
            <dt className="text-text-3">{k}</dt>
            <dd className="font-mono text-xs tabular-nums text-text-1">{v}</dd>
          </div>
        ))}
      </dl>
    </details>
  )
}
