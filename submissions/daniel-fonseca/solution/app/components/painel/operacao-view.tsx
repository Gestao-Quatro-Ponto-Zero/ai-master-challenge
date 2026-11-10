import { Info } from "lucide-react"
import Link from "next/link"

import { RefreshButton } from "@/components/painel/refresh-button"
import { Headline } from "@/components/shared/headline"
import { KpiCard } from "@/components/shared/kpi-card"
import { PathBadge } from "@/components/shared/path-badge"
import { fmt } from "@/lib/format"
import { PATHS } from "@/lib/paths"
import { getMetric } from "@/lib/queries/analysis"
import { getOpsSummary } from "@/lib/queries/ops"
import type { PathKey } from "@/lib/types"
import { cn } from "@/lib/utils"

const SMALL = 30

function SmallSample({ n, what }: { n: number; what: string }) {
  if (n >= SMALL) return null
  return (
    <p className="flex items-start gap-1.5 text-xs leading-relaxed text-text-3">
      <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden />
      Amostra pequena: {fmt.int(n)} {what}. Com menos de {SMALL}, o número oscila muito a cada nova triagem.
    </p>
  )
}

/** Painel › Operação (PRD §4.3): indicadores do sistema real, lidos a cada carregamento. */
export async function OperacaoView() {
  const [s, rag] = await Promise.all([getOpsSummary(), getMetric<{ accuracy: number }>("rag_only_policy")])
  const total = s.triagens
  const share = (n: number) => (total > 0 ? n / total : 0)
  const autonomy = share(s.automaticas)
  const accuracy = s.holdout_total > 0 ? s.holdout_acertos / s.holdout_total : null
  const decided = s.hitl_aprovadas + s.hitl_editadas + s.hitl_rejeitadas
  const paths: { key: PathKey; n: number }[] = [
    { key: "auto", n: s.automaticas },
    { key: "review", n: s.revisao_humana },
    { key: "human", n: s.somente_humano },
  ]
  const fill: Record<PathKey, string> = { auto: "bg-path-auto", review: "bg-path-review", human: "bg-path-human" }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <Headline>
          {total > 0
            ? `${fmt.pct(autonomy)} das ${fmt.int(total)} triagens feitas no sistema saíram com Resposta automática`
            : "O sistema ainda não registrou triagens"}
        </Headline>
        <RefreshButton />
      </div>

      <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
        <div className="flex flex-col gap-2">
          <KpiCard protagonist label="Triagens com autonomia da IA" value={fmt.pct(autonomy)} origin="medido" hint={`${fmt.int(s.automaticas)} de ${fmt.int(total)} triagens.`} />
          <SmallSample n={total} what="triagens" />
        </div>

        <section aria-labelledby="ops-caminhos" className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-5 shadow-soft">
          <div className="flex items-baseline justify-between gap-3">
            <h2 id="ops-caminhos" className="text-sm font-medium text-text-2">
              Distribuição pelos 3 caminhos
            </h2>
            <span className="text-sm text-text-3 tabular-nums">{fmt.int(total)} triagens</span>
          </div>
          <div className="flex h-3 w-full gap-0.5 overflow-hidden rounded-full bg-surface-2" aria-hidden>
            {paths.map((p) => (p.n > 0 ? <div key={p.key} className={cn("h-full first:rounded-l-full last:rounded-r-full", fill[p.key])} style={{ width: `${share(p.n) * 100}%` }} /> : null))}
          </div>
          <ul className="grid gap-3 sm:grid-cols-3">
            {paths.map((p) => (
              <li key={p.key} className="flex flex-col gap-1.5">
                <PathBadge path={p.key} size="sm" />
                <span className="text-2xl font-semibold tabular-nums text-text-1">{fmt.pct(share(p.n))}</span>
                <span className="text-xs leading-relaxed text-text-3">
                  {fmt.int(p.n)} triagens · {PATHS[p.key].description}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="flex flex-col gap-2">
          <KpiCard
            label="Acurácia ao vivo (holdout)"
            value={accuracy === null ? "—" : fmt.pct(accuracy)}
            origin="medido"
            hint={`Categoria prevista igual ao rótulo real em ${fmt.int(s.holdout_acertos)} de ${fmt.int(s.holdout_total)} tickets do holdout. Referência offline: ${fmt.pct(rag.accuracy)} em 9.567 tickets.`}
          />
          <SmallSample n={s.holdout_total} what="tickets do holdout" />
        </div>
        <KpiCard
          label="Latência da triagem"
          value={s.latencia_p50_ms === null ? "—" : fmt.ms(s.latencia_p50_ms)}
          origin="medido"
          hint={s.latencia_p95_ms === null ? "Mediana (p50)." : `Mediana (p50). p95 de ${fmt.ms(s.latencia_p95_ms)}, com a redação pelo LLM.`}
        />
        <KpiCard
          label="Custo OpenAI acumulado"
          value={fmt.usd(s.custo_usd_total, 2)}
          origin="medido"
          hint={total > 0 ? `${fmt.usd(s.custo_usd_total / total, 4)} por triagem, com embeddings e redação.` : "Soma dos tokens gravados em cada triagem."}
        />
        <KpiCard
          label="Base de conhecimento"
          value={`${fmt.int(s.base_playbook)} + ${fmt.int(s.base_aprendidas)}`}
          origin="medido"
          hint={`${fmt.int(s.base_playbook)} soluções do playbook inicial e ${fmt.int(s.base_aprendidas)} ${s.base_aprendidas === 1 ? "aprendida" : "aprendidas"} com a Revisão humana.`}
        />
      </div>

      <section aria-labelledby="ops-revisao" className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-5 shadow-soft">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <h2 id="ops-revisao" className="text-sm font-medium text-text-2">
            Revisão humana
          </h2>
          <Link href="/console?aba=fila" className="text-sm text-text-2 underline underline-offset-4 hover:text-text-1">
            Abrir a fila ({fmt.int(s.hitl_pendentes)} pendentes)
          </Link>
        </div>
        <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { label: "Aprovadas sem edição", n: s.hitl_aprovadas },
            { label: "Editadas e aprovadas", n: s.hitl_editadas },
            { label: "Rejeitadas", n: s.hitl_rejeitadas },
          ].map((x) => (
            <div key={x.label} className="flex flex-col gap-0.5">
              <dt className="text-xs text-text-3">{x.label}</dt>
              <dd className="text-2xl font-semibold tabular-nums text-text-1">{fmt.int(x.n)}</dd>
              <dd className="text-xs text-text-3 tabular-nums">{decided > 0 ? fmt.pct(x.n / decided) : "—"} das decisões</dd>
            </div>
          ))}
          <div className="flex flex-col gap-0.5">
            <dt className="text-xs text-text-3">Tempo médio na fila</dt>
            <dd className="text-2xl font-semibold tabular-nums text-text-1">{s.hitl_tempo_medio_s === null ? "—" : formatDuration(s.hitl_tempo_medio_s)}</dd>
            <dd className="text-xs text-text-3">da entrada na fila até a decisão</dd>
          </div>
        </dl>
        <SmallSample n={decided} what="decisões" />
      </section>

      <p className="text-xs leading-relaxed text-text-3">
        Fonte: tabelas triage_runs, hitl_queue e validated_resolutions do Supabase (view v_ops_summary), lidas a cada carregamento. Inclui as triagens dos testes de ponta a ponta e as feitas pelos
        visitantes no Console.
      </p>
    </div>
  )
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)} s`
  if (seconds < 3600) return `${Math.round(seconds / 60)} min`
  if (seconds < 86_400) return fmt.hours(seconds / 3600)
  return `${fmt.dec(seconds / 86_400, 1)} dias`
}
