import { CircleAlert } from "lucide-react"

import { getDiagnosticData } from "@/components/painel/diagnostic-data"
import { DiagnosticExplorer } from "@/components/painel/diagnostic-explorer"
import { Headline } from "@/components/shared/headline"
import { KpiCard } from "@/components/shared/kpi-card"
import { fmt } from "@/lib/format"

/** Painel › Diagnóstico (PRD §4.1). Protagonista dourado: 33,3% sem 1ª resposta. */
export async function DiagnosticoView() {
  const { summary, dimensions, overall } = await getDiagnosticData()
  const o = summary.overview

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-5" aria-labelledby="diag-resumo">
        <div className="grid gap-4 sm:grid-cols-3">
          <KpiCard protagonist label="Sem 1ª resposta" value={fmt.pct(o.pct_open)} origin="medido" hint={`${fmt.int(Math.round(o.pct_open * o.n))} tickets com status Open no DS1.`} />
          <KpiCard label="Aguardando o cliente" value={fmt.pct(o.pct_pending)} origin="medido" hint="Status Pending Customer Response: o ticket depende de um retorno do cliente." />
          <KpiCard
            label="1ª resposta → resolução"
            value={fmt.hours(o.hours_median_coherent)}
            origin="medido"
            hint={`Mediana, calculada só nos ${fmt.pct(o.pct_coherent_closed)} de fechados com registro coerente (resolução depois da resposta).`}
          />
        </div>
        <Headline>
          <span id="diag-resumo">
            Um terço dos {fmt.int(o.n)} tickets está parado antes da 1ª resposta, e outro terço espera o cliente
          </span>
        </Headline>
      </section>

      <DiagnosticExplorer dimensions={dimensions} overall={overall} />

      <section className="flex flex-col gap-3 rounded-xl border border-border bg-surface-2/60 p-5" aria-labelledby="diag-csat">
        <p className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.14em] text-text-3">
          <CircleAlert className="size-4" aria-hidden /> Quem não é medido
        </p>
        <p id="diag-csat" className="font-serif text-lg leading-snug text-text-1">
          O CSAT existe só para os {fmt.pct(o.pct_closed)} de tickets fechados.
        </p>
        <p className="max-w-3xl text-sm leading-relaxed text-text-2">
          Os {fmt.pct(1 - o.pct_closed)} sem resolução, os mais prováveis de gerar insatisfação, ficam fora da nota. A média de {fmt.dec(o.csat_mean, 2)} descreve só quem chegou ao fim do
          atendimento.
        </p>
      </section>

      <p className="text-xs leading-relaxed text-text-3">
        Fonte: DS1 (Customer Support Tickets, {fmt.int(o.n)} tickets). Testes: qui-quadrado para o status, Kruskal-Wallis para tempo e CSAT. Intervalos: Wilson para proporções, bootstrap
        para a mediana do tempo, erro padrão para o CSAT. Scripts em <span className="font-mono">solution/analysis/02_diagnostic_cuts.py</span>,{" "}
        <span className="font-mono">11_app_summary.py</span> e <span className="font-mono">12_painel_extras.py</span>.
      </p>
    </div>
  )
}
