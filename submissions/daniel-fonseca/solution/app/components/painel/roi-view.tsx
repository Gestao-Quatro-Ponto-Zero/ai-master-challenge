import type { AppSummary } from "@/components/painel/diagnostic-data"
import { RoiCalculator, type PremiseMeta } from "@/components/painel/roi-calculator"
import { Headline } from "@/components/shared/headline"
import { fmt } from "@/lib/format"
import { getMetric } from "@/lib/queries/analysis"
import { defaultInputs, type PremiseSource } from "@/lib/roi"

interface Premise {
  value: number
  unit: string
  source: string
  url?: string
}
type CostPremises = PremiseSource & Record<string, Premise | string | object>

/** Painel › ROI (PRD §4.2). Protagonista dourado: R$/ano. */
export async function RoiView() {
  const [premises, summary] = await Promise.all([getMetric<CostPremises>("cost_premises"), getMetric<AppSummary>("app_summary")])
  const roi = summary.roi_inputs
  const defaults = defaultInputs(premises, roi)
  const p = (k: string) => premises[k] as Premise

  const meta: PremiseMeta[] = [
    { key: "annualVolume", label: "Volume anual", origin: "premissa", source: p("annual_ticket_volume").source },
    { key: "handleMinutes", label: "Minutos por ticket", origin: "benchmark", source: p("handle_time_minutes").source, href: p("handle_time_minutes").url },
    {
      key: "hourlyCost",
      label: "Custo por hora do agente",
      origin: "benchmark",
      source: `${p("agent_hourly_cost_brl").source}. ${p("agent_monthly_cost_brl").source}.`,
      href: p("agent_monthly_cost_brl").url,
    },
    {
      key: "autonomyShare",
      label: "Casos elegíveis com autonomia da IA",
      origin: "medido",
      source: `Medido no holdout de 9.567 tickets do DS2: a Resposta automática acerta a categoria em ${fmt.pct(roi.ds2_autonomy_precision)} desses casos.`,
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <Headline>
        A IA resolveria sozinha {fmt.pct(roi.total_autonomy_share)} do volume e devolveria à equipe as horas desses atendimentos
      </Headline>
      <RoiCalculator defaults={defaults} premises={meta} eligibleRule={`ficam fora ${roi.ds1_eligible_rule.replace(/^fora:\s*/, "").replace(/\s*\(sempre humano\)/, "")}, que seguem sempre para atendimento humano`} autonomyRule={roi.autonomy_rule} />
    </div>
  )
}
