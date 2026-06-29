import { ArrowRight, Snowflake, Users } from "lucide-react";

import type { ScoredDeal } from "@/lib/types";
import { useI18n } from "@/lib/i18n-context";

interface ManagerRow {
  manager: string;
  region: string;
  open: number;
  high: number;
  cooling: number;
  riskValue: number;
  avgScore: number;
  topDeal: ScoredDeal;
}

interface ManagerAccumulator extends Omit<ManagerRow, "avgScore" | "topDeal"> {
  scoreSum: number;
  topDeal?: ScoredDeal;
}

function isCooling(d: ScoredDeal) {
  return d.risks.some((r) => r.code === "cooling_risk");
}

export function ManagerView({ deals }: { deals: ScoredDeal[] }) {
  const { t, num, compactUsd } = useI18n();
  const rows = Array.from(
    deals
      .reduce((map, deal) => {
        const key = deal.manager || t("manager.unknown");
        const row = map.get(key) ?? {
          manager: key,
          region: deal.region || "—",
          open: 0,
          high: 0,
          cooling: 0,
          riskValue: 0,
          scoreSum: 0,
          topDeal: deal,
        };
        row.open += 1;
        row.scoreSum += deal.score;
        if (deal.priority === "High") row.high += 1;
        if (isCooling(deal)) {
          row.cooling += 1;
          row.riskValue += deal.expectedValue;
        }
        if (!row.topDeal || deal.score > row.topDeal.score) row.topDeal = deal;
        if (row.region === "—" && deal.region) row.region = deal.region;
        map.set(key, row);
        return map;
      }, new Map<string, ManagerAccumulator>())
      .values(),
  )
    .filter((row): row is ManagerAccumulator & { topDeal: ScoredDeal } => Boolean(row.topDeal))
    .map(({ scoreSum, ...row }) => ({
      ...row,
      avgScore: Math.round(scoreSum / Math.max(row.open, 1)),
    }))
    .sort((a, b) => b.high - a.high || b.cooling - a.cooling || b.riskValue - a.riskValue)
    .slice(0, 6);

  return (
    <section className="rounded-lg border border-border bg-card shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border px-4 py-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            {t("manager.kicker")}
          </p>
          <h3 className="mt-1 text-sm font-bold text-foreground">{t("manager.title")}</h3>
        </div>
        <Users className="h-5 w-5 text-gold" />
      </div>

      <div className="divide-y divide-border/60">
        {rows.map((row) => {
          const topLabel = row.topDeal.account || row.topDeal.opportunity_id;
          return (
            <div key={row.manager} className="grid gap-3 px-4 py-3 md:grid-cols-[1fr_24rem]">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                  <p className="font-semibold text-foreground">{row.manager}</p>
                  <span className="rounded border border-border bg-secondary/60 px-1.5 py-0.5 text-[11px] text-muted-foreground">
                    {row.region}
                  </span>
                </div>
                <div className="mt-2 grid grid-cols-4 gap-2 text-xs">
                  <Metric label={t("manager.open")} value={num(row.open)} />
                  <Metric label={t("manager.high")} value={num(row.high)} tone="text-gold" />
                  <Metric
                    label={t("manager.cooling")}
                    value={num(row.cooling)}
                    tone="text-danger"
                  />
                  <Metric label={t("manager.avg")} value={String(row.avgScore)} />
                </div>
              </div>

              <div className="rounded-md border border-border bg-secondary/35 p-3">
                <div className="flex items-start gap-2">
                  <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gold" />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-foreground">{topLabel}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {row.topDeal.nextBestAction} ·{" "}
                      {t("manager.score", { score: row.topDeal.score })}
                    </p>
                  </div>
                </div>
                <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Snowflake className="h-3.5 w-3.5 text-danger" />
                  {t("manager.riskValue", { value: compactUsd(row.riskValue) })}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function Metric({
  label,
  value,
  tone = "text-foreground",
}: {
  label: string;
  value: string;
  tone?: string;
}) {
  return (
    <div>
      <p className="truncate text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className={`tabular mt-0.5 text-sm font-bold ${tone}`}>{value}</p>
    </div>
  );
}
