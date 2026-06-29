import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Clock, Copy, Download, Snowflake } from "lucide-react";
import type { ScoredDeal } from "@/lib/types";
import { useI18n } from "@/lib/i18n-context";
import { cn } from "@/lib/utils";
import { PriorityBadge, ScoreChip } from "./PriorityBadge";
import { Button } from "@/components/ui/button";

const PAGE_SIZE = 75;
const COPY_LIMIT = 20;

function isCooling(d: ScoredDeal) {
  return d.risks.some((r) => r.code === "cooling_risk");
}

async function copyText(text: string) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Fall back to the legacy copy path below.
  }

  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.readOnly = true;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const copied = document.execCommand("copy");
    ta.remove();
    return copied;
  } catch {
    return false;
  }
}

export function DealsTable({
  deals,
  selectedId,
  onSelect,
}: {
  deals: ScoredDeal[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const { t, num, usd, stage } = useI18n();
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [copyFallbackText, setCopyFallbackText] = useState<string | null>(null);
  const [csvUrl, setCsvUrl] = useState<string | null>(null);

  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
    setFeedback(null);
    setCopyFallbackText(null);
    setCsvUrl(null);
  }, [deals]);

  useEffect(() => {
    return () => {
      if (csvUrl) URL.revokeObjectURL(csvUrl);
    };
  }, [csvUrl]);

  const visibleDeals = useMemo(() => deals.slice(0, visibleCount), [deals, visibleCount]);
  const hasMore = visibleCount < deals.length;

  const ageLabel = (d: ScoredDeal) => (d.ageDays == null ? "—" : `${d.ageDays}d`);
  const subLine = (d: ScoredDeal) => (d.account ? `${d.opportunity_id} · ${d.product}` : d.product);

  if (deals.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-10 text-center">
        <p className="text-sm font-medium text-foreground">{t("table.noMatch.title")}</p>
        <p className="mt-1 text-xs text-muted-foreground">{t("table.noMatch.sub")}</p>
      </div>
    );
  }

  const exportDeals = () => {
    const headers = [
      "rank",
      "opportunity_id",
      "account",
      "seller",
      "manager",
      "region",
      "stage",
      "product",
      "expected_value",
      "value_is_estimated",
      "score",
      "priority",
      "confidence",
      "next_best_action",
      "why_this_score",
      "risk",
    ];
    const escape = (value: unknown) => `"${String(value ?? "").replace(/"/g, '""')}"`;
    const rows = deals.map((d, index) =>
      [
        index + 1,
        d.opportunity_id,
        d.account,
        d.salesAgent,
        d.manager,
        d.region,
        d.stage,
        d.product,
        d.expectedValue,
        d.valueIsEstimated,
        d.score,
        d.priority,
        d.confidence,
        d.nextBestAction,
        d.whyThisScore,
        d.risk,
      ]
        .map(escape)
        .join(","),
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    setCsvUrl(url);
    const a = document.createElement("a");
    a.href = url;
    a.download = "pipeline-focus-prioritized-deals.csv";
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setCopyFallbackText(null);
    setFeedback(t("table.csvPrepared", { n: num(deals.length) }));
  };

  const copyActionList = async () => {
    const top = deals.slice(0, COPY_LIMIT);
    const lines = top.map((d, i) => {
      const who = d.account || d.opportunity_id;
      const reason = (d.risks[0]?.detail || d.risk || d.whyThisScore || "").replace(/\s+/g, " ");
      return `${i + 1}. ${who} — ${d.salesAgent} · ${t("table.col.score")} ${d.score} · ${d.nextBestAction} · ${reason}`;
    });
    const text = lines.join("\n");
    const copied = await copyText(text);
    setCopyFallbackText(copied ? null : text);
    setFeedback(copied ? t("table.copied", { n: num(top.length) }) : t("table.copyFailed"));
  };

  return (
    <div className="rounded-lg border border-border bg-card shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border px-3 py-2.5">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-foreground">{t("table.queueTitle")}</p>
          <p className="text-xs text-muted-foreground">
            {t("table.showingOf", {
              x: num(Math.min(visibleCount, deals.length)),
              y: num(deals.length),
            })}
          </p>
          {feedback && <p className="text-xs font-medium text-success">{feedback}</p>}
          {csvUrl && (
            <a
              className="mt-1 inline-flex text-xs font-semibold text-gold underline-offset-2 hover:underline"
              href={csvUrl}
              download="pipeline-focus-prioritized-deals.csv"
            >
              {t("table.downloadReady")}
            </a>
          )}
          {copyFallbackText && (
            <textarea
              aria-label={t("table.copyFallbackLabel")}
              className="mt-2 h-24 w-full max-w-2xl resize-none rounded-md border border-border bg-background p-2 text-xs text-foreground shadow-inner"
              readOnly
              value={copyFallbackText}
              onFocus={(e) => e.currentTarget.select()}
            />
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={copyActionList}
            aria-label={t("table.aria.copyList")}
            title={t("table.copyList")}
          >
            <Copy className="h-4 w-4" />
            <span className="hidden sm:inline">{t("table.copyList")}</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={exportDeals}
            aria-label={t("table.aria.export")}
            title={t("table.export")}
          >
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">{t("table.export")}</span>
          </Button>
        </div>
      </div>
      {/* Desktop table */}
      <div className="hidden overflow-x-auto lg:block">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-[11px] uppercase tracking-wider text-muted-foreground">
              <th className="px-3 py-2.5 text-left font-medium">{t("table.col.rank")}</th>
              <th className="px-3 py-2.5 text-left font-medium">{t("table.col.oppAccount")}</th>
              <th className="px-3 py-2.5 text-left font-medium">{t("table.col.sellerRegion")}</th>
              <th className="px-3 py-2.5 text-left font-medium">{t("table.col.stage")}</th>
              <th className="px-3 py-2.5 text-right font-medium">{t("table.col.value")}</th>
              <th className="px-3 py-2.5 text-center font-medium">{t("table.col.score")}</th>
              <th className="px-3 py-2.5 text-left font-medium">{t("table.col.nextAction")}</th>
            </tr>
          </thead>
          <tbody>
            {visibleDeals.map((d, i) => {
              const active = d.opportunity_id === selectedId;
              const accountLabel = d.account || d.opportunity_id;
              const cooling = isCooling(d);
              const aging = !cooling && d.ageDays != null && d.ageDays > 90;
              return (
                <tr
                  key={d.opportunity_id}
                  onClick={() => onSelect(d.opportunity_id)}
                  className={cn(
                    "cursor-pointer border-b border-border/60 transition-colors hover:bg-accent/40",
                    active && "bg-accent ring-1 ring-inset ring-gold/40",
                  )}
                >
                  <td className="tabular px-3 py-2.5 align-top text-muted-foreground">{i + 1}</td>
                  <td className="px-3 py-2.5 align-top">
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-foreground">{accountLabel}</span>
                      {cooling && (
                        <Snowflake className="h-3.5 w-3.5 shrink-0 text-danger" aria-hidden />
                      )}
                      {aging && <Clock className="h-3.5 w-3.5 shrink-0 text-warning" aria-hidden />}
                    </div>
                    <div className="text-xs text-muted-foreground">{subLine(d)}</div>
                  </td>
                  <td className="px-3 py-2.5 align-top">
                    <div className="text-foreground">{d.salesAgent}</div>
                    <div className="text-xs text-muted-foreground">
                      {d.manager ?? "—"}
                      {d.region ? ` · ${d.region}` : ""}
                    </div>
                  </td>
                  <td className="px-3 py-2.5 align-top">
                    <span className="text-foreground">{stage(d.stage)}</span>
                    <div className="text-xs text-muted-foreground">
                      {ageLabel(d)} {t("table.open")}
                    </div>
                  </td>
                  <td className="tabular px-3 py-2.5 text-right align-top font-medium text-foreground">
                    {usd(d.expectedValue)}
                    {d.valueIsEstimated && (
                      <span
                        className="block text-[10px] text-muted-foreground"
                        title={t("table.estValue")}
                      >
                        {t("table.est")}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-center align-top">
                    <div className="flex flex-col items-center gap-1">
                      <ScoreChip score={d.score} priority={d.priority} />
                      <PriorityBadge priority={d.priority} className="scale-90" />
                    </div>
                  </td>
                  <td className="px-3 py-2.5 align-top">
                    <div className="flex items-start gap-1.5 font-medium text-foreground">
                      <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gold" />
                      {d.nextBestAction}
                    </div>
                    <div className="mt-0.5 line-clamp-2 max-w-[24rem] text-xs text-muted-foreground">
                      {d.whyThisScore}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Mobile scannable list */}
      <div className="divide-y divide-border/60 lg:hidden">
        {visibleDeals.map((d, i) => {
          const active = d.opportunity_id === selectedId;
          const accountLabel = d.account || d.opportunity_id;
          const cooling = isCooling(d);
          const aging = !cooling && d.ageDays != null && d.ageDays > 90;
          return (
            <button
              key={d.opportunity_id}
              onClick={() => onSelect(d.opportunity_id)}
              className={cn(
                "block w-full px-3 py-3 text-left transition-colors active:bg-accent",
                active && "bg-accent",
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="tabular text-xs text-muted-foreground">#{i + 1}</span>
                    <span className="truncate font-semibold text-foreground">{accountLabel}</span>
                    {cooling && (
                      <Snowflake className="h-3.5 w-3.5 shrink-0 text-danger" aria-hidden />
                    )}
                    {aging && <Clock className="h-3.5 w-3.5 shrink-0 text-warning" aria-hidden />}
                  </div>
                  <div className="truncate text-xs text-muted-foreground">
                    {subLine(d)} · {d.salesAgent}
                  </div>
                </div>
                <ScoreChip score={d.score} priority={d.priority} className="shrink-0" />
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
                <PriorityBadge priority={d.priority} />
                <span className="tabular font-medium text-foreground">{usd(d.expectedValue)}</span>
                <span className="text-muted-foreground">
                  {stage(d.stage)} · {ageLabel(d)}
                </span>
              </div>
              <div className="mt-2 flex items-start gap-1.5 text-sm font-medium text-foreground">
                <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gold" />
                {d.nextBestAction}
              </div>
              <div className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                {d.whyThisScore}
              </div>
            </button>
          );
        })}
      </div>
      {hasMore && (
        <div className="flex justify-center border-t border-border p-3">
          <Button variant="outline" size="sm" onClick={() => setVisibleCount((n) => n + PAGE_SIZE)}>
            {t("table.showNext", { n: num(Math.min(PAGE_SIZE, deals.length - visibleCount)) })}
          </Button>
        </div>
      )}
    </div>
  );
}
