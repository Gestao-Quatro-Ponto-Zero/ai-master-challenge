import { Database, Gauge, ShieldCheck, TriangleAlert } from "lucide-react";

import type { Confidence, ScoredDeal } from "@/lib/types";
import { useI18n } from "@/lib/i18n-context";
import { cn } from "@/lib/utils";

const BAR_TONE: Record<Confidence, string> = {
  High: "bg-success",
  Medium: "bg-warning",
  Low: "bg-danger",
};

export function DataQualitySummary({ deals }: { deals: ScoredDeal[] }) {
  const { t, num } = useI18n();
  const total = Math.max(deals.length, 1);
  const counts: Record<Confidence, number> = { High: 0, Medium: 0, Low: 0 };
  let estimated = 0;
  let limited = 0;

  for (const deal of deals) {
    counts[deal.confidence] += 1;
    if (deal.valueIsEstimated) estimated += 1;
    if (deal.limitations.length > 0) limited += 1;
  }

  const confidenceRows: Confidence[] = ["High", "Medium", "Low"];

  return (
    <section className="rounded-lg border border-border bg-card p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            {t("quality.kicker")}
          </p>
          <h3 className="mt-1 text-sm font-bold text-foreground">{t("quality.title")}</h3>
        </div>
        <ShieldCheck className="h-5 w-5 text-success" />
      </div>

      <div className="mt-4 space-y-3">
        {confidenceRows.map((confidence) => {
          const count = counts[confidence];
          const width = count === 0 ? "0%" : `${Math.max(4, Math.round((count / total) * 100))}%`;
          return (
            <div key={confidence}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="font-medium text-foreground">{t(`confidence.${confidence}`)}</span>
                <span className="tabular text-muted-foreground">{num(count)}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-secondary">
                <div
                  className={cn("h-full rounded-full", BAR_TONE[confidence])}
                  style={{ width }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-2">
        <div className="rounded-md border border-border bg-secondary/35 p-3">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Gauge className="h-3.5 w-3.5 text-warning" />
            {t("quality.estimated")}
          </div>
          <p className="tabular mt-1 text-lg font-bold text-foreground">{num(estimated)}</p>
        </div>
        <div className="rounded-md border border-border bg-secondary/35 p-3">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <TriangleAlert className="h-3.5 w-3.5 text-danger" />
            {t("quality.limited")}
          </div>
          <p className="tabular mt-1 text-lg font-bold text-foreground">{num(limited)}</p>
        </div>
      </div>

      <p className="mt-3 flex items-start gap-1.5 text-xs leading-relaxed text-muted-foreground">
        <Database className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gold" />
        {t("quality.note")}
      </p>
    </section>
  );
}
