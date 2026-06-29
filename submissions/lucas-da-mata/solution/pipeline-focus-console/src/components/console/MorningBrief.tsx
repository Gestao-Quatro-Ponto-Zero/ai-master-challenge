import { ArrowRight, Flame, Snowflake, UserCheck } from "lucide-react";

import type { ScoredDeal } from "@/lib/types";
import { useI18n } from "@/lib/i18n-context";
import { cn } from "@/lib/utils";

function isCooling(d: ScoredDeal) {
  return d.risks.some((r) => r.code === "cooling_risk");
}

export function MorningBrief({ deals }: { deals: ScoredDeal[] }) {
  const { t, num, compactUsd } = useI18n();
  const top = deals[0];
  const high = deals.filter((d) => d.priority === "High");
  const cooling = deals.filter(isCooling);
  const review = deals.filter(
    (d) => d.nextActionCode === "managerReview" || d.confidence === "Low",
  );

  const topLabel = top?.account || top?.opportunity_id || t("morning.noDeal");
  const highValue = high.reduce((s, d) => s + d.expectedValue, 0);
  const coolingValue = cooling.reduce((s, d) => s + d.expectedValue, 0);

  const cards = [
    {
      label: t("morning.high.label"),
      value: num(high.length),
      sub: t("morning.high.sub", { value: compactUsd(highValue) }),
      icon: Flame,
      tone: "text-gold",
    },
    {
      label: t("morning.cooling.label"),
      value: num(cooling.length),
      sub: t("morning.cooling.sub", { value: compactUsd(coolingValue) }),
      icon: Snowflake,
      tone: "text-danger",
    },
    {
      label: t("morning.manager.label"),
      value: num(review.length),
      sub: t("morning.manager.sub"),
      icon: UserCheck,
      tone: "text-warning",
    },
  ];

  return (
    <section className="rounded-lg border border-gold/30 bg-gold/10 p-4 shadow-sm">
      <div className="grid gap-4 lg:grid-cols-[1.25fr_2fr]">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-gold">
            {t("morning.kicker")}
          </p>
          <h2 className="mt-1 text-lg font-bold leading-tight text-offwhite">
            {t("morning.title")}
          </h2>
          <p className="mt-1 max-w-xl text-sm text-muted-foreground">{t("morning.subtitle")}</p>
        </div>

        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-gold/30 bg-background/45 p-3 md:col-span-1">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              {t("morning.firstMove")}
            </p>
            <p className="mt-1 truncate text-base font-bold text-offwhite">{topLabel}</p>
            {top && (
              <div className="mt-2 flex items-start gap-1.5 text-xs text-muted-foreground">
                <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gold" />
                <span>
                  <span className="font-semibold text-foreground">{top.nextBestAction}</span>
                  {" · "}
                  {t("morning.score", { score: top.score, seller: top.salesAgent })}
                </span>
              </div>
            )}
          </div>

          {cards.map((c) => (
            <div key={c.label} className="rounded-lg border border-border bg-background/35 p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {c.label}
                </p>
                <c.icon className={cn("h-4 w-4", c.tone)} />
              </div>
              <p className={cn("tabular mt-2 text-xl font-bold leading-none", c.tone)}>{c.value}</p>
              <p className="mt-1.5 text-xs text-muted-foreground">{c.sub}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
