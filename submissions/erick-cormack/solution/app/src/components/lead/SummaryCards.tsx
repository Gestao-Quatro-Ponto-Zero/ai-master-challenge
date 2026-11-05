import { cn } from "@/lib/utils";
import { formatNumber, formatUSD, formatUSDCompact } from "@/lib/format";
import type { Indicadores } from "@/lib/metrics";
import { Skeleton } from "@/components/ui/skeleton";

export function SummaryCards({ ind, loading }: { ind: Indicadores | undefined; loading?: boolean }) {
  const cards = ind
    ? [
        { label: "Deals para focar", value: formatNumber(ind.focar) },
        { label: "Valor esperado em foco", value: formatUSDCompact(ind.valorEsperadoFocar), hint: formatUSD(ind.valorEsperadoFocar) },
        { label: "Na reta final", value: formatNumber(ind.retaFinal), warn: true },
        { label: "Parados para requalificar", value: formatNumber(ind.requalificar), hint: `${formatUSDCompact(ind.valorParado)} de lista travado` },
        { label: "Sem conta cadastrada", value: formatNumber(ind.semConta) },
      ]
    : [];

  return (
    <div className="grid grid-cols-2 gap-3 px-4 py-6 md:px-8 lg:grid-cols-5">
      {loading || !ind
        ? Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-24" />)
        : cards.map((c) => (
            <div key={c.label} className={cn("rounded-lg border p-4",
              c.warn ? "border-warning bg-warning-soft" : "border-border bg-card")}>
              <p className={cn("text-xs font-medium", c.warn ? "text-warning-foreground" : "text-muted-foreground")}>{c.label}</p>
              <p className={cn("mt-1 font-numeric text-3xl font-semibold not-italic tabular-nums", c.warn ? "text-warning-foreground" : "text-foreground")}>{c.value}</p>
              {c.hint && <p className="mt-0.5 text-xs text-muted-foreground">{c.hint}</p>}
            </div>
          ))}
    </div>
  );
}
