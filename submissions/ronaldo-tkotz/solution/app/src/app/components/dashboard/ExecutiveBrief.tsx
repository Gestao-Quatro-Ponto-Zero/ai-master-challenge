import type { Kpi, TrendResult } from "@/engine/dashboard";
import { KpiRow } from "./KpiRow";
import { AdoptionChart } from "./AdoptionChart";

/**
 * The conversation canvas at rest: four descriptive KPIs and the monthly churn line
 * (accounts with an event and events, D21). Every number is grounded; ask to go deeper.
 */
export function ExecutiveBrief({ kpis, trend }: { kpis: Kpi[]; trend: TrendResult }) {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-[21px] font-semibold leading-tight tracking-tight text-foreground">RavenStack · churn em números</h1>
        <p className="mt-1 max-w-xl text-[13px] leading-relaxed text-muted">
          Churn = evento em churn_events. Pergunte abaixo — cada resposta mostra o SQL exato que rodou.
        </p>
      </div>

      <KpiRow kpis={kpis} />

      <div className="rounded-xl border border-edge bg-surface/50 p-4">
        <div className="mb-1.5 flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-accent" />
          <span className="text-[12.5px] font-semibold text-foreground">Churn por mês</span>
          <span className="text-[10.5px] text-faint">contas com evento e eventos · jan/2023 a dez/2024</span>
        </div>
        <AdoptionChart trend={trend} bare height={150} />
      </div>
    </div>
  );
}
