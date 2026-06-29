import { Flame, Layers, Snowflake, TrendingUp } from "lucide-react";
import { useI18n } from "@/lib/i18n-context";
import type { ScoredDeal } from "@/lib/types";
import { cn } from "@/lib/utils";

export function MetricCards({ deals }: { deals: ScoredDeal[] }) {
  const { t, num, compactUsd } = useI18n();
  const open = deals.length;
  const high = deals.filter((d) => d.priority === "High").length;
  const prioritizedValue = deals
    .filter((d) => d.priority === "High" || d.priority === "Priority")
    .reduce((s, d) => s + d.expectedValue, 0);
  const isCooling = (d: ScoredDeal) => d.risks.some((r) => r.code === "cooling_risk");
  const atRisk = deals.filter(isCooling).length;
  const atRiskValue = deals.filter(isCooling).reduce((s, d) => s + d.expectedValue, 0);

  const cards = [
    {
      label: t("metric.openDeals"),
      value: num(open),
      sub: t("metric.openDeals.sub"),
      icon: Layers,
      tone: "text-offwhite",
    },
    {
      label: t("metric.highPriority"),
      value: num(high),
      sub: t("metric.highPriority.sub"),
      icon: Flame,
      tone: "text-gold",
    },
    {
      label: t("metric.prioritizedValue"),
      value: compactUsd(prioritizedValue),
      sub: t("metric.prioritizedValue.sub"),
      icon: TrendingUp,
      tone: "text-success",
    },
    {
      label: t("metric.coolingRisk"),
      value: num(atRisk),
      sub: t("metric.coolingRisk.sub", { value: compactUsd(atRiskValue) }),
      icon: Snowflake,
      tone: "text-danger",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {cards.map((c) => (
        <div key={c.label} className="rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="flex items-start justify-between">
            <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              {c.label}
            </p>
            <c.icon className={cn("h-4 w-4", c.tone)} />
          </div>
          <p className={cn("tabular mt-2 text-2xl font-bold leading-none", c.tone)}>{c.value}</p>
          <p className="mt-1.5 text-xs text-muted-foreground">{c.sub}</p>
        </div>
      ))}
    </div>
  );
}
