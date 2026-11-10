import { ExternalLink } from "lucide-react"

import { content, isAiError, isHumanJudgment, type Adr, type JudgmentEntry } from "@/components/metodo/content"
import { Section } from "@/components/metodo/section"
import { cn } from "@/lib/utils"

const ORIGIN: Record<Adr["originKind"], string> = {
  daniel: "Daniel",
  daniel_ia: "Daniel + IA",
  ia_daniel: "IA + Daniel",
  ia: "IA",
}

const fmtDate = (d: string | null) => (d ? d.split("-").reverse().slice(0, 2).join("/") : "")

/** Como foi feito › Decisões (PRD §4.7): linha do tempo das ADRs + destaques do judgment log. */
export function DecisoesView() {
  const { adrs, judgment } = content
  const errors = judgment.filter(isAiError)
  const human = judgment.filter(isHumanJudgment)

  return (
    <div className="flex flex-col gap-10">
      <Section
        eyebrow="Linha do tempo das ADRs"
        title={`${adrs.length} decisões registradas, cada uma com quem decidiu e o status`}
        lead="Origem: quem trouxe a ideia aparece primeiro. Daniel + IA = ideia do Daniel e desenho da IA; IA + Daniel = proposta da IA validada ou ajustada pelo Daniel."
      >
        <ol className="relative flex flex-col gap-0 border-l border-border pl-5">
          {adrs.map((a) => (
            <li key={a.number} className="relative pb-5 last:pb-0">
              <span className={cn("absolute top-1.5 -left-[25px] size-2.5 rounded-full ring-4 ring-bg", a.statusKind === "aceita" ? "bg-text-1" : "border border-text-3 bg-bg")} aria-hidden />
              <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:gap-3">
                <span className="shrink-0 font-mono text-xs text-text-3">
                  {a.number} · {fmtDate(a.date)}
                </span>
                <a href={a.href} target="_blank" rel="noreferrer" className="group inline-flex items-baseline gap-1.5 text-sm font-medium text-text-1 hover:underline hover:underline-offset-4">
                  {a.title}
                  <ExternalLink className="size-3 shrink-0 translate-y-0.5 text-text-3 opacity-0 transition-opacity group-hover:opacity-100" aria-hidden />
                </a>
              </div>
              <div className="mt-1.5 flex flex-wrap items-center gap-2">
                <span className={cn("rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider", a.statusKind === "aceita" ? "border-border text-text-2" : "border-dashed border-text-3 text-text-3")}>
                  {a.statusKind === "aceita" ? "Aceita" : a.statusKind === "proposta" ? "Proposta" : a.status}
                </span>
                <span className="font-mono text-[10px] uppercase tracking-wider text-text-3">Origem: {ORIGIN[a.originKind]}</span>
              </div>
            </li>
          ))}
        </ol>
      </Section>

      <Section
        eyebrow="Judgment log"
        title={`${errors.length} erros da IA corrigidos e ${human.length} julgamentos que vieram do Daniel`}
        lead={`Registro feito no momento em que cada caso aconteceu, com ${judgment.length} entradas no total.`}
      >
        <div className="grid gap-4 lg:grid-cols-2">
          <JudgmentList title="Onde a IA errou" items={errors} />
          <JudgmentList title="O que o Daniel decidiu" items={human} limit={7} />
        </div>
        <a href={content.judgmentHref} target="_blank" rel="noreferrer" className="inline-flex w-fit items-center gap-1.5 text-sm text-text-2 underline underline-offset-4 hover:text-text-1">
          Ler o judgment log completo <ExternalLink className="size-3.5" aria-hidden />
        </a>
      </Section>
    </div>
  )
}

function JudgmentList({ title, items, limit }: { title: string; items: JudgmentEntry[]; limit?: number }) {
  const shown = limit ? items.slice(-limit).reverse() : [...items].reverse()
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-surface p-5 shadow-soft">
      <h3 className="text-sm font-semibold text-text-1">
        {title} <span className="font-normal text-text-3">· {items.length}</span>
      </h3>
      <ul className="flex flex-col divide-y divide-border">
        {shown.map((j) => (
          <li key={j.n} className="flex flex-col gap-1 py-3 first:pt-0 last:pb-0">
            <span className="font-mono text-[10px] uppercase tracking-wider text-text-3">
              #{j.n} · {fmtDate(j.date)} · {j.type}
            </span>
            <p className="text-sm leading-relaxed text-text-1">{j.what}</p>
            <p className="text-xs leading-relaxed text-text-3">→ {j.result}</p>
          </li>
        ))}
      </ul>
      {limit && items.length > limit ? <p className="text-xs text-text-3">Os {limit} mais recentes de {items.length}.</p> : null}
    </div>
  )
}
