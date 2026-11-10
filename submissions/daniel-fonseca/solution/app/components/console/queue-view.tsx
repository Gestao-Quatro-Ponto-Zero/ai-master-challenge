"use client"

import { ArrowRight, CheckCircle2, ChevronDown, Loader2, Sparkles } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useRef, useState } from "react"
import { toast } from "sonner"

import { ApiFailure, errorMessage, postJson } from "@/components/console/api"
import { CategoryChip, ConfidenceBar } from "@/components/console/category"
import { DemoResetButton } from "@/components/console/demo-reset-button"
import type { HitlApiResult, QueueItem } from "@/components/console/types"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { fmt } from "@/lib/format"
import { CATEGORIES, type Category } from "@/lib/types"
import { cn } from "@/lib/utils"

type Tab = "pending" | "decided"

const STATUS_LABEL: Record<QueueItem["status"], string> = {
  pending: "Pendente",
  approved: "Aprovado sem edição",
  edited: "Editado e aprovado",
  rejected: "Rejeitado",
}

/** Console › Fila (PRD §4.5): lista à esquerda, detalhe à direita. */
export function QueueView({ pending, decided, initialId }: { pending: QueueItem[]; decided: QueueItem[]; initialId: number | null }) {
  const initialTab: Tab = initialId && decided.some((d) => d.id === initialId) ? "decided" : "pending"
  const [tab, setTab] = useState<Tab>(initialTab)
  const known = initialId != null && [...pending, ...decided].some((i) => i.id === initialId)
  const [selectedId, setSelectedId] = useState<number | null>(known ? initialId : (pending[0]?.id ?? null))
  const [outcomes, setOutcomes] = useState<Record<number, HitlApiResult>>({})
  const detailRef = useRef<HTMLDivElement>(null)

  const list = tab === "pending" ? pending : decided
  const selected = [...pending, ...decided].find((i) => i.id === selectedId) ?? null

  function select(id: number) {
    setSelectedId(id)
    const url = new URL(window.location.href)
    url.searchParams.set("item", String(id))
    window.history.replaceState(null, "", url)
    if (window.matchMedia("(max-width: 1023px)").matches) detailRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
  }

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-6 lg:grid-cols-[minmax(0,4fr)_minmax(0,7fr)]">
      <section className="rounded-xl border border-border bg-surface shadow-soft" aria-labelledby="fila-titulo">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border p-4">
          <h2 id="fila-titulo" className="font-serif text-xl text-text-1">
            Fila de revisão
          </h2>
          <DemoResetButton />
        </div>
        <div role="tablist" aria-label="Situação dos itens" className="flex gap-1 border-b border-border px-4 pt-2">
          {(
            [
              ["pending", `Pendentes · ${pending.length}`],
              ["decided", `Decididos · ${decided.length}`],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              role="tab"
              aria-selected={tab === value}
              onClick={() => setTab(value)}
              className={cn(
                "-mb-px border-b-2 px-3 py-2 text-sm font-medium transition-colors",
                tab === value ? "border-text-1 text-text-1" : "border-transparent text-text-3 hover:text-text-1",
              )}
            >
              {label}
            </button>
          ))}
        </div>
        {list.length ? (
          <ul className="max-h-[32rem] divide-y divide-border overflow-y-auto">
            {list.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => select(item.id)}
                  aria-current={item.id === selectedId ? "true" : undefined}
                  aria-label={`Item #${item.id} · ${item.category} · ${item.ticket_text.slice(0, 60)}`}
                  className={cn("flex w-full flex-col gap-1.5 px-4 py-3 text-left transition-colors hover:bg-surface-2", item.id === selectedId && "bg-surface-2")}
                >
                  <div className="flex items-center justify-between gap-2">
                    <CategoryChip category={item.category} />
                    <span className="shrink-0 font-mono text-xs text-text-3">{fmt.relative(tab === "pending" ? item.created_at : (item.decided_at ?? item.created_at))}</span>
                  </div>
                  <p className="line-clamp-2 font-mono text-xs leading-relaxed text-text-2">{item.ticket_text}</p>
                  {tab === "decided" ? <span className="text-xs font-medium text-text-3">{STATUS_LABEL[item.status]}</span> : null}
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <div className="p-6 text-sm text-text-2">
            {tab === "pending" ? "A fila está vazia. Restaure a demonstração ou faça uma triagem que caia em Revisão humana." : "Nenhum item decidido ainda."}
          </div>
        )}
      </section>

      <div ref={detailRef} className="min-w-0 scroll-mt-24">
        {selected ? (
          <QueueDetail
            key={selected.id}
            item={selected}
            outcome={outcomes[selected.id] ?? null}
            onDecided={(r) => {
              setOutcomes((o) => ({ ...o, [r.hitl_id]: r }))
            }}
          />
        ) : (
          <div className="rounded-xl border border-dashed border-border p-6 text-sm text-text-2">Selecione um item da fila para revisar.</div>
        )}
      </div>
    </div>
  )
}

function QueueDetail({ item, outcome, onDecided }: { item: QueueItem; outcome: HitlApiResult | null; onDecided: (r: HitlApiResult) => void }) {
  const router = useRouter()
  const [draft, setDraft] = useState(item.draft_text)
  const [checked, setChecked] = useState<boolean[]>(() => item.checks.map(() => false))
  const [category, setCategory] = useState<Category>(item.category)
  const [note, setNote] = useState("")
  const [busy, setBusy] = useState<null | "approve" | "edit" | "reject">(null)
  const edited = draft.trim() !== item.draft_text.trim()
  const isPending = item.status === "pending" && !outcome

  async function decide(decision: "approve" | "edit" | "reject") {
    setBusy(decision)
    try {
      const res = await postJson<HitlApiResult>("/api/hitl", {
        hitl_id: item.id,
        decision,
        ...(decision === "edit" ? { final_text: draft.trim() } : {}),
        ...(category !== item.category ? { final_category: category } : {}),
        ...(note.trim() ? { note: note.trim() } : {}),
      })
      onDecided(res)
      toast.success(decision === "reject" ? "Rascunho rejeitado: o ticket volta para atendimento manual." : "Resposta aprovada e enviada ao cliente.")
      router.refresh()
    } catch (err) {
      toast.error(errorMessage(err))
      if (err instanceof ApiFailure && err.status === 409) router.refresh()
    } finally {
      setBusy(null)
    }
  }

  const categoryItems = CATEGORIES.map((c) => ({ value: c, label: c === item.category ? `${c} (prevista)` : c }))

  return (
    <article className="flex flex-col gap-5" aria-labelledby="item-titulo">
      <section className="rounded-xl border border-border bg-surface p-5 shadow-soft">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 id="item-titulo" className="font-serif text-xl text-text-1">
            Item #{item.id}
          </h2>
          <span className="font-mono text-xs text-text-3">
            triagem #{item.triage_run_id} · {fmt.relative(item.created_at)}
          </span>
        </div>
        <p className="mt-4 text-xs font-medium uppercase tracking-wider text-text-3">Ticket original</p>
        <p className="mt-1.5 max-h-48 overflow-y-auto whitespace-pre-line rounded-lg bg-surface-2 p-3 font-mono text-xs leading-relaxed text-text-1">{item.ticket_text}</p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs text-text-3">Categoria prevista</p>
            <CategoryChip category={item.category} className="mt-1" />
            <div className="mt-2 flex items-center gap-2">
              <ConfidenceBar value={item.confidence} />
              <span className="shrink-0 font-mono text-xs tabular-nums text-text-2">{fmt.pct(item.confidence, 0)}</span>
            </div>
          </div>
          {item.level_reason ? (
            <div>
              <p className="text-xs text-text-3">Por que veio para a revisão</p>
              <p className="mt-1 text-sm text-text-1">{item.level_reason}</p>
            </div>
          ) : null}
        </div>
        {item.similar_cases.length ? (
          <details className="group mt-4 border-t border-border pt-3">
            <summary className="flex cursor-pointer list-none items-center justify-between text-sm font-medium text-text-2 hover:text-text-1 [&::-webkit-details-marker]:hidden">
              {item.similar_cases.length} casos parecidos
              <ChevronDown className="size-4 transition-transform group-open:rotate-180" aria-hidden />
            </summary>
            <ul className="mt-2 flex flex-col gap-2">
              {item.similar_cases.map((c) => (
                <li key={c.id} className="flex flex-col gap-0.5">
                  <span className="flex items-center justify-between gap-2">
                    <CategoryChip category={c.category} className="text-xs" />
                    <span className="font-mono text-xs text-text-3">{fmt.dec(c.similarity, 2)}</span>
                  </span>
                  <span className="line-clamp-1 font-mono text-xs text-text-3">{c.snippet}</span>
                </li>
              ))}
            </ul>
          </details>
        ) : null}
      </section>

      {isPending ? (
        <section className="rounded-xl border border-border bg-surface p-5 shadow-soft" aria-labelledby="revisao-titulo">
          <h3 id="revisao-titulo" className="text-sm font-semibold text-text-1">
            Rascunho da IA
          </h3>
          <label htmlFor="rascunho" className="sr-only">
            Rascunho da resposta
          </label>
          <Textarea id="rascunho" value={draft} onChange={(e) => setDraft(e.target.value)} maxLength={4000} className="mt-2 min-h-40 bg-surface text-sm leading-relaxed" />
          <div className="mt-1 flex justify-between gap-2 text-xs text-text-3">
            <span>{edited ? "Rascunho editado" : "Texto original da IA"}</span>
            {edited ? (
              <button type="button" className="hover:text-text-1" onClick={() => setDraft(item.draft_text)}>
                desfazer edição
              </button>
            ) : null}
          </div>

          {item.checks.length ? (
            <fieldset className="mt-5">
              <legend className="text-sm font-semibold text-text-1">
                O que conferir{" "}
                <span className="font-normal text-text-3">
                  ({checked.filter(Boolean).length} de {item.checks.length})
                </span>
              </legend>
              <ul className="mt-2 flex flex-col gap-2">
                {item.checks.map((c, i) => (
                  <li key={i}>
                    <label className="flex cursor-pointer items-start gap-2.5 text-sm text-text-2">
                      <input
                        type="checkbox"
                        checked={checked[i]}
                        onChange={(e) => setChecked((prev) => prev.map((v, j) => (j === i ? e.target.checked : v)))}
                        className="mt-0.5 size-4 shrink-0 accent-[var(--text-1)]"
                      />
                      <span className={cn(checked[i] && "text-text-3 line-through")}>{c}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </fieldset>
          ) : null}

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <div>
              <p id="categoria-final" className="text-sm font-semibold text-text-1">
                Categoria
              </p>
              <Select items={categoryItems} value={category} onValueChange={(v) => v && setCategory(v as Category)}>
                <SelectTrigger className="mt-2 h-9 w-full" aria-labelledby="categoria-final">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {categoryItems.map((c) => (
                    <SelectItem key={c.value} value={c.value}>
                      {c.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {category !== item.category ? <p className="mt-1 text-xs text-text-3">A solução fica registrada como {category}.</p> : null}
            </div>
            <div>
              <label htmlFor="nota" className="text-sm font-semibold text-text-1">
                Nota <span className="font-normal text-text-3">(opcional)</span>
              </label>
              <input
                id="nota"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                maxLength={500}
                placeholder="Motivo da rejeição ou da edição"
                className="mt-2 h-9 w-full rounded-lg border border-input bg-surface px-2.5 text-sm text-text-1 outline-none placeholder:text-text-3 focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              />
            </div>
          </div>

          <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
            <Button
              size="lg"
              onClick={() => decide("approve")}
              disabled={Boolean(busy) || edited}
              className="h-10 bg-gold px-4 text-sm font-semibold text-navy hover:bg-gold/85 dark:text-navy"
            >
              {busy === "approve" ? <Loader2 className="animate-spin" aria-hidden /> : <CheckCircle2 aria-hidden />}
              Aprovar
            </Button>
            <Button variant="outline" size="lg" onClick={() => decide("edit")} disabled={Boolean(busy) || !edited} className="h-10 px-4 text-sm">
              {busy === "edit" ? <Loader2 className="animate-spin" aria-hidden /> : null}
              Editar e aprovar
            </Button>
            <Button variant="destructive" size="lg" onClick={() => decide("reject")} disabled={Boolean(busy)} className="h-10 px-4 text-sm sm:ml-auto">
              {busy === "reject" ? <Loader2 className="animate-spin" aria-hidden /> : null}
              Rejeitar
            </Button>
          </div>
          <p className="mt-2 text-xs text-text-3">
            {edited ? "Você editou o rascunho: use Editar e aprovar para enviar a sua versão." : "Edite o texto acima para habilitar Editar e aprovar."} A decisão fica registrada como visitante.
          </p>
        </section>
      ) : (
        <DecidedPanel item={item} outcome={outcome} />
      )}
    </article>
  )
}

function DecidedPanel({ item, outcome }: { item: QueueItem; outcome: HitlApiResult | null }) {
  const decision = outcome?.decision ?? (item.status === "rejected" ? "reject" : item.status === "edited" ? "edit" : "approve")
  const status: QueueItem["status"] = outcome ? (decision === "reject" ? "rejected" : decision === "edit" ? "edited" : "approved") : item.status
  const finalText = item.final_text ?? (decision === "reject" ? null : item.draft_text)
  return (
    <section className="flex flex-col gap-4">
      {outcome && decision !== "reject" ? (
        <div className="rounded-xl border border-border bg-surface p-5 shadow-soft" role="status">
          <p className="flex items-center gap-2 font-serif text-lg text-text-1">
            <Sparkles className="size-5 text-ok" aria-hidden />
            Esta solução agora atende tickets parecidos
          </p>
          <p className="mt-2 text-sm text-text-2">
            A resposta aprovada entrou na base de soluções validadas
            {outcome.resolution_id ? <span className="font-mono text-xs"> (#{outcome.resolution_id})</span> : null} de {item.final_category ?? item.category}. Ela passa a ser
            candidata nas triagens de tickets parecidos dessa categoria.
          </p>
          {outcome.neighbor ? (
            <div className="mt-4 rounded-lg bg-surface-2 p-3">
              <p className="font-mono text-xs text-text-3">
                ticket de teste #{outcome.neighbor.id} · similaridade {fmt.dec(outcome.neighbor.similarity, 2)}
              </p>
              <p className="mt-1 line-clamp-3 font-mono text-xs leading-relaxed text-text-1">{outcome.neighbor.excerpt}</p>
              <Link
                href={`/console?ds2=${outcome.neighbor.id}&origem=aprendeu`}
                className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-text-1 px-3 py-2 text-sm font-medium text-bg hover:opacity-90"
              >
                Triar este ticket parecido <ArrowRight className="size-4" aria-hidden />
              </Link>
            </div>
          ) : null}
        </div>
      ) : null}
      <div className="rounded-xl border border-border bg-surface p-5 shadow-soft">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="text-sm font-semibold text-text-1">{STATUS_LABEL[status]}</h3>
          <span className="font-mono text-xs text-text-3">
            {item.reviewer ?? "visitante"}
            {item.decided_at ? ` · ${fmt.relative(item.decided_at)}` : ""}
          </span>
        </div>
        {item.final_category && item.final_category !== item.category ? (
          <p className="mt-2 flex items-center gap-2 text-sm text-text-2">
            Categoria corrigida para <CategoryChip category={item.final_category} />
          </p>
        ) : null}
        {finalText ? <p className="mt-3 whitespace-pre-line rounded-lg bg-surface-2 p-3 text-sm leading-relaxed text-text-1">{finalText}</p> : null}
        {decision === "reject" ? <p className="mt-3 text-sm text-text-2">O ticket voltou para atendimento manual.</p> : null}
        {item.review_note ? <p className="mt-3 text-sm text-text-3">Nota: {item.review_note}</p> : null}
      </div>
    </section>
  )
}
