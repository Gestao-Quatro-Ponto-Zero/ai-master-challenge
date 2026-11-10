"use client"

import { Dices, Loader2, PenLine, RotateCcw, Sparkles } from "lucide-react"
import { useRef, useState } from "react"
import { toast } from "sonner"

import { errorMessage, getJson, postJson } from "@/components/console/api"
import { CategoryChip } from "@/components/console/category"
import { clearSession, recordTriage, type SessionState, useSessionState } from "@/components/console/session-store"
import { TriageResultView } from "@/components/console/triage-result"
import type { ConsoleTriageResult, HoldoutTicket } from "@/components/console/types"
import { PathBadge } from "@/components/shared/path-badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { fmt } from "@/lib/format"
import { PATHS, pathFromLevel } from "@/lib/paths"
import { CATEGORIES } from "@/lib/types"
import { cn } from "@/lib/utils"

const MAX_CHARS = 4000
const ALL = "todas"
const CATEGORY_ITEMS = [{ value: ALL, label: "Todas as categorias" }, ...CATEGORIES.map((c) => ({ value: c, label: c }))]

type Mode = "holdout" | "free_text"

export function TriageView({ freeTextEnabled, initialTicket, learned = false }: { freeTextEnabled: boolean; initialTicket: HoldoutTicket | null; learned?: boolean }) {
  const [mode, setMode] = useState<Mode>("holdout")
  const [category, setCategory] = useState<string>(ALL)
  const [ticket, setTicket] = useState<HoldoutTicket | null>(initialTicket)
  const [text, setText] = useState("")
  const [drawing, setDrawing] = useState(false)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<ConsoleTriageResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [offlineSeen, setOfflineSeen] = useState(false)
  const session = useSessionState()
  const resultRef = useRef<HTMLDivElement>(null)
  const toResult = () => {
    if (window.matchMedia("(max-width: 1023px)").matches) resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
  }

  async function draw() {
    setDrawing(true)
    setError(null)
    try {
      const qs = category !== ALL ? `?categoria=${encodeURIComponent(category)}` : ""
      setTicket(await getJson<HoldoutTicket>(`/api/triage/sample${qs}`))
      setResult(null)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setDrawing(false)
    }
  }

  async function run() {
    setRunning(true)
    setError(null)
    setResult(null)
    toResult()
    try {
      const body = mode === "holdout" ? { mode, ds2_id: ticket?.id } : { mode, ticket_text: text.trim() }
      const res = await postJson<ConsoleTriageResult>("/api/triage", body)
      setResult(res)
      recordTriage({
        at: new Date().toISOString(),
        triage_run_id: res.triage_run_id,
        ds2_id: res.ds2_id,
        excerpt: res.ticket_text.slice(0, 90),
        level: res.level,
        category: res.category,
        true_category: res.true_category ?? null,
        offline: Boolean(res.offline),
      })
      setOfflineSeen(Boolean(res.offline))
      if (res.offline) toast.message("Modo offline: classificação sem redação.")
    } catch (err) {
      const msg = errorMessage(err)
      setError(msg)
      toast.error(msg)
    } finally {
      setRunning(false)
    }
  }

  const canRun = !running && (mode === "holdout" ? Boolean(ticket) : freeTextEnabled && text.trim().length >= 15 && text.length <= MAX_CHARS)

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <div className="flex min-w-0 flex-col gap-6">
        {/* Entrada */}
        <section className="rounded-xl border border-border bg-surface p-5 shadow-soft" aria-labelledby="entrada-titulo">
          <h2 id="entrada-titulo" className="font-serif text-xl text-text-1">
            Ticket para triar
          </h2>
          <div role="tablist" aria-label="Origem do ticket" className="mt-4 inline-flex w-full rounded-full border border-border bg-surface-2 p-1">
            {(
              [
                ["holdout", "Sortear do teste", "Sortear", Dices],
                ["free_text", "Escrever um ticket", "Escrever", PenLine],
              ] as const
            ).map(([value, label, short, Icon]) => (
              <button
                key={value}
                type="button"
                role="tab"
                aria-selected={mode === value}
                onClick={() => {
                  setMode(value)
                  setError(null)
                }}
                className={cn(
                  "flex min-w-0 flex-1 items-center justify-center gap-1.5 rounded-full px-2 py-1.5 text-sm font-medium transition-all sm:px-3",
                  mode === value ? "bg-surface text-text-1 shadow-soft" : "text-text-3 hover:text-text-1",
                )}
              >
                <Icon className="size-4" aria-hidden />
                <span className="truncate sm:hidden">{short}</span>
                <span className="hidden truncate sm:inline">{label}</span>
              </button>
            ))}
          </div>

          {mode === "holdout" ? (
            <div className="mt-4 flex flex-col gap-3">
              {learned && ticket ? (
                <p className="flex items-start gap-2 rounded-lg bg-surface-2 p-3 text-sm text-text-2">
                  <Sparkles className="mt-0.5 size-4 shrink-0 text-ok" aria-hidden />
                  Este é o ticket de teste mais parecido com o item que você aprovou na fila. Faça a triagem para ver a solução aprendida em uso.
                </p>
              ) : null}
              <p className="text-sm leading-relaxed text-text-2">
                Tickets reais do conjunto de teste (holdout), que o modelo não viu. A categoria real aparece depois da triagem.
              </p>
              <div className="flex flex-col gap-2 sm:flex-row">
                <Select items={CATEGORY_ITEMS} value={category} onValueChange={(v) => setCategory((v as string) ?? ALL)}>
                  <SelectTrigger className="h-9 w-full sm:w-56" aria-label="Filtrar por categoria real">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CATEGORY_ITEMS.map((c) => (
                      <SelectItem key={c.value} value={c.value}>
                        {c.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button variant="outline" size="lg" onClick={draw} disabled={drawing || running} className="h-9 px-3">
                  {drawing ? <Loader2 className="animate-spin" aria-hidden /> : <Dices aria-hidden />}
                  {ticket ? "Sortear outro" : "Sortear ticket"}
                </Button>
              </div>
              {ticket ? (
                <figure className="rounded-lg border border-border bg-surface-2 p-3">
                  <figcaption className="font-mono text-xs text-text-3">ticket #{ticket.id}</figcaption>
                  <p className="mt-1.5 max-h-56 overflow-y-auto whitespace-pre-line break-words font-mono text-xs leading-relaxed text-text-1">{ticket.document}</p>
                </figure>
              ) : (
                <p className="rounded-lg border border-dashed border-border p-4 text-sm text-text-3">Sorteie um ticket para começar.</p>
              )}
            </div>
          ) : (
            <div className="mt-4 flex flex-col gap-3">
              <p className="text-sm leading-relaxed text-text-2">
                Escreva em inglês: a base de 38 mil tickets de treino está em inglês, e a busca por casos parecidos compara textos no mesmo idioma.
              </p>
              {freeTextEnabled && offlineSeen ? (
                <p role="status" className="rounded-lg bg-surface-2 p-3 text-sm text-text-2">
                  O fluxo de triagem está em modo offline. O texto livre volta assim que ele responder.
                </p>
              ) : null}
              {freeTextEnabled ? (
                <>
                  <label htmlFor="ticket-livre" className="sr-only">
                    Texto do ticket em inglês
                  </label>
                  <Textarea
                    id="ticket-livre"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    maxLength={MAX_CHARS}
                    rows={6}
                    placeholder="Describe the problem as a customer would…"
                    className="min-h-36 bg-surface font-mono text-sm"
                  />
                  <p className={cn("text-right font-mono text-xs tabular-nums", text.length > MAX_CHARS * 0.95 ? "text-alert" : "text-text-3")}>
                    {fmt.int(text.length)} / {fmt.int(MAX_CHARS)}
                  </p>
                </>
              ) : (
                <p role="status" className="rounded-lg bg-surface-2 p-4 text-sm text-text-2">
                  O texto livre está pausado no momento. O sorteio do conjunto de teste continua disponível.
                </p>
              )}
            </div>
          )}

          <Button size="lg" onClick={run} disabled={!canRun} className="mt-4 h-10 w-full text-sm">
            {running ? <Loader2 className="animate-spin" aria-hidden /> : null}
            {running ? "Triando…" : "Fazer a triagem"}
          </Button>
          {error ? (
            <p role="alert" className="mt-3 rounded-lg border border-alert/30 bg-alert/5 p-3 text-sm text-alert">
              {error}
            </p>
          ) : null}
        </section>

        <SessionPanel session={session} />
      </div>

      {/* Resultado */}
      <div ref={resultRef} aria-live="polite" className="min-w-0 scroll-mt-20">
        {running ? (
          <div className="flex flex-col gap-5" aria-busy="true" aria-label="Triando">
            <Skeleton className="h-36 rounded-xl" />
            <Skeleton className="h-44 rounded-xl" />
            <Skeleton className="h-28 rounded-xl" />
          </div>
        ) : result ? (
          <TriageResultView result={result} />
        ) : (
          <EmptyResult />
        )}
      </div>
    </div>
  )
}

function SessionPanel({ session }: { session: SessionState }) {
  const { history, holdoutTotal, holdoutHits } = session
  return (
    <section className="rounded-xl border border-border bg-surface p-5 shadow-soft" aria-labelledby="sessao-titulo">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="sessao-titulo" className="text-sm font-medium text-text-2">
          Sua sessão
        </h2>
        {history.length ? (
          <button type="button" onClick={clearSession} className="inline-flex items-center gap-1 text-xs text-text-3 hover:text-text-1">
            <RotateCcw className="size-3" aria-hidden />
            limpar
          </button>
        ) : null}
      </div>
      <p className="mt-2 text-sm text-text-2">
        {holdoutTotal ? (
          <>
            Acurácia nos tickets do conjunto de teste:{" "}
            <strong className="font-semibold text-text-1">
              {holdoutHits} de {holdoutTotal} ({fmt.pct(holdoutHits / holdoutTotal, 0)})
            </strong>
            {holdoutTotal < 30 ? <span className="text-text-3"> · amostra pequena</span> : null}
          </>
        ) : (
          "A acurácia acumulada aparece depois da primeira triagem de um ticket sorteado."
        )}
      </p>
      {history.length ? (
        <ol className="mt-3 flex flex-col divide-y divide-border">
          {history.map((h) => (
            <li key={`${h.at}-${h.triage_run_id ?? "off"}`} className="flex flex-col gap-1 py-2.5">
              <div className="flex flex-wrap items-center gap-2">
                <HistoryPath level={h.level} />
                <CategoryChip category={h.category} className="text-xs" />
                {h.true_category ? (
                  <span className={cn("text-xs font-semibold", h.true_category === h.category ? "text-ok" : "text-alert")}>
                    {h.true_category === h.category ? "✓" : `✗ real: ${h.true_category}`}
                  </span>
                ) : null}
                {h.offline ? <span className="text-xs text-text-3">offline</span> : null}
              </div>
              <p className="truncate font-mono text-xs text-text-3">
                {fmt.relative(h.at)} · {h.excerpt}
              </p>
            </li>
          ))}
        </ol>
      ) : null}
    </section>
  )
}

/** Selo compacto do histórico: Revisão humana sem o contorno dourado (o dourado da tela é o selo do resultado). */
function HistoryPath({ level, className }: { level: 1 | 2 | 3; className?: string }) {
  const path = pathFromLevel(level)
  if (path !== "review") return <PathBadge path={path} size="sm" className={className} />
  return <span className={cn("inline-flex items-center rounded-full border border-border px-2 py-0.5 text-xs font-semibold text-text-1", className)}>{PATHS.review.label}</span>
}

function EmptyResult() {
  return (
    <section className="flex min-h-80 flex-col justify-center rounded-xl border border-dashed border-border p-6 sm:p-8">
      <p className="font-mono text-xs uppercase tracking-[0.14em] text-text-3">O que aparece aqui</p>
      <h2 className="mt-2 font-serif text-2xl leading-snug text-text-1">Cada ticket segue um de três caminhos</h2>
      <ul className="mt-4 flex flex-col gap-3 text-sm text-text-2">
        <li className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-3">
          <PathBadge path="auto" size="sm" className="w-fit" />
          Confiança alta e solução validada: a IA responde.
        </li>
        <li className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-3">
          <HistoryPath level={2} className="w-fit" />
          Confiança intermediária: rascunho para um agente aprovar.
        </li>
        <li className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-3">
          <PathBadge path="human" size="sm" className="w-fit" />
          Categoria sensível ou confiança baixa: alerta para o time.
        </li>
      </ul>
    </section>
  )
}
