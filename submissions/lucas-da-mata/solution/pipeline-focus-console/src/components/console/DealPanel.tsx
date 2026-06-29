import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Database,
  Info,
  MousePointerClick,
  ShieldCheck,
  X,
} from "lucide-react";
import { useI18n } from "@/lib/i18n-context";
import type { Confidence, ScoredDeal } from "@/lib/types";
import { cn } from "@/lib/utils";
import { PRIORITY_STYLES } from "./priority";
import { PriorityBadge } from "./PriorityBadge";

const CONFIDENCE_STYLES: Record<Confidence, string> = {
  High: "text-success border-success/40 bg-success/10",
  Medium: "text-warning border-warning/40 bg-warning/10",
  Low: "text-danger border-danger/40 bg-danger/10",
};

function Breakdown({ deal }: { deal: ScoredDeal }) {
  return (
    <div className="space-y-2">
      {deal.breakdown.map((b) => (
        <div key={b.name}>
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">
              {b.name} <span className="opacity-60">· {Math.round(b.weight * 100)}%</span>
            </span>
            <span className="tabular font-medium text-foreground">+{Math.round(b.weighted)}</span>
          </div>
          <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-secondary">
            <div
              className="h-full rounded-full bg-gold/80"
              style={{ width: `${Math.round(b.score0to1 * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DealPanelBody({ deal }: { deal: ScoredDeal }) {
  const { t, usd } = useI18n();
  const s = PRIORITY_STYLES[deal.priority];
  return (
    <div className="space-y-5">
      {/* Executive at-a-glance band */}
      <div className="grid grid-cols-2 gap-2 rounded-lg border border-border bg-secondary/40 p-3 sm:grid-cols-4">
        <div>
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
            {t("panel.totalScore")}
          </p>
          <p className={cn("tabular text-2xl font-bold leading-none", s.text)}>{deal.score}</p>
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
            {t("panel.priority")}
          </p>
          <PriorityBadge priority={deal.priority} className="mt-1" />
        </div>
        <div>
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
            {t("confidence.label")}
          </p>
          <span
            className={cn(
              "mt-1 inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[11px] font-semibold",
              CONFIDENCE_STYLES[deal.confidence],
            )}
            title={t(`confidence.${deal.confidence}.desc`)}
          >
            <ShieldCheck className="h-3 w-3" />
            {t(`confidence.${deal.confidence}`)}
          </span>
        </div>
        <div className="col-span-2 sm:col-span-1">
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
            {t("panel.nextBestAction")}
          </p>
          <p className="mt-0.5 text-sm font-semibold leading-tight text-foreground">
            {deal.nextBestAction}
          </p>
        </div>
      </div>

      {/* Meta row */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span className="tabular font-medium text-foreground">
          {usd(deal.expectedValue)}
          {deal.valueIsEstimated ? ` · ${t("table.est")}` : ""}
        </span>
        {deal.ageDays != null && <span>{t("panel.daysOpen", { n: deal.ageDays })}</span>}
      </div>

      {deal.valueIsEstimated && (
        <div className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 p-2.5 text-xs text-warning">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          {t("panel.estimatedValue")}
        </div>
      )}

      {/* Why this score */}
      <section>
        <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {t("panel.whyThisScore")}
        </h4>
        <p className="text-sm leading-relaxed text-foreground">{deal.whyThisScore}</p>
      </section>

      {/* Next best action */}
      <div className="flex items-center gap-2 rounded-lg border border-gold/40 bg-gold/10 p-3">
        <ArrowRight className="h-4 w-4 shrink-0 text-gold" />
        <div>
          <p className="text-[11px] uppercase tracking-wider text-gold/80">
            {t("panel.nextBestAction")}
          </p>
          <p className="text-sm font-semibold text-foreground">{deal.nextBestAction}</p>
        </div>
      </div>

      {/* Positives */}
      {deal.positives.length > 0 && (
        <section>
          <h4 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-success">
            <CheckCircle2 className="h-3.5 w-3.5" /> {t("panel.positiveFactors")}
          </h4>
          <ul className="space-y-2">
            {deal.positives.map((f, i) => (
              <li key={i} className="flex gap-2 text-sm">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-success" />
                <span>
                  <span className="font-medium text-foreground">{f.label}.</span>{" "}
                  <span className="text-muted-foreground">{f.detail}</span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Risks */}
      <section>
        <h4 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-danger">
          <AlertTriangle className="h-3.5 w-3.5" /> {t("panel.riskFactors")}
        </h4>
        {deal.risks.length ? (
          <ul className="space-y-2">
            {deal.risks.map((f, i) => (
              <li key={i} className="flex gap-2 text-sm">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-danger" />
                <span>
                  <span className="font-medium text-foreground">{f.label}.</span>{" "}
                  <span className="text-muted-foreground">{f.detail}</span>
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">{deal.risk}</p>
        )}
      </section>

      {/* Score breakdown */}
      <section>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {t("panel.scoreBreakdown")}
        </h4>
        <Breakdown deal={deal} />
      </section>

      {/* Data used */}
      <section>
        <h4 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <Database className="h-3.5 w-3.5" /> {t("panel.dataUsed")}
        </h4>
        <ul className="space-y-1 text-xs text-muted-foreground">
          {deal.dataUsed.map((d, i) => (
            <li key={i} className="flex gap-1.5">
              <span className="text-gold">·</span>
              {d}
            </li>
          ))}
        </ul>
      </section>

      {/* Limitations */}
      <section>
        <h4 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <Info className="h-3.5 w-3.5" /> {t("panel.limitations")}
        </h4>
        {deal.limitations.length ? (
          <ul className="space-y-1 text-xs text-muted-foreground">
            {deal.limitations.map((l, i) => (
              <li key={i} className="flex gap-1.5">
                <span className="text-warning">·</span>
                {l}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">{t("panel.noLimitations")}</p>
        )}
      </section>
    </div>
  );
}

/** Desktop sticky panel. */
export function DealPanel({ deal, onClose }: { deal: ScoredDeal | null; onClose: () => void }) {
  const { t } = useI18n();
  if (!deal) {
    return (
      <div className="flex h-full min-h-[20rem] flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card/50 p-8 text-center">
        <MousePointerClick className="h-6 w-6 text-muted-foreground" />
        <p className="mt-3 text-sm font-medium text-foreground">{t("panel.selectDeal")}</p>
        <p className="mt-1 text-xs text-muted-foreground">{t("panel.selectDeal.sub")}</p>
      </div>
    );
  }
  const accountLabel = deal.account || deal.opportunity_id;
  const sub = deal.account ? `${deal.opportunity_id} · ${deal.product}` : deal.product;
  return (
    <div className="rounded-lg border border-border bg-card shadow-sm">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-foreground">{accountLabel}</p>
          <p className="truncate text-xs text-muted-foreground">{sub}</p>
        </div>
        <button
          onClick={onClose}
          aria-label="Close"
          className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="max-h-[calc(100vh-9rem)] overflow-y-auto p-4">
        <DealPanelBody deal={deal} />
      </div>
    </div>
  );
}
