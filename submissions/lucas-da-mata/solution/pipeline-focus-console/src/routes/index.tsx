import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Database, Loader2, RefreshCcw, Scale, Target } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

import type { Dataset, ScoredDeal } from "@/lib/types";
import { scoreDataset } from "@/lib/scoring";
import { loadFromPublic } from "@/lib/csv";

import { MetricCards } from "@/components/console/MetricCards";
import { FilterBar, EMPTY_FILTERS, type Filters } from "@/components/console/FilterBar";
import { DealsTable } from "@/components/console/DealsTable";
import { DealPanel, DealPanelBody } from "@/components/console/DealPanel";
import { ScoringLogic } from "@/components/console/ScoringLogic";
import { LanguageToggle } from "@/components/console/LanguageToggle";
import { MorningBrief } from "@/components/console/MorningBrief";
import { ManagerView } from "@/components/console/ManagerView";
import { DataQualitySummary } from "@/components/console/DataQualitySummary";
import { matchesQuick } from "@/components/console/priority";
import { useI18n } from "@/lib/i18n-context";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Pipeline Focus Console — G4 AI Master Lead Scorer" },
      {
        name: "description",
        content:
          "Prioritize the deals sellers should act on now. An explainable lead scorer for sales and RevOps.",
      },
      { property: "og:title", content: "Pipeline Focus Console — G4 AI Master" },
      {
        property: "og:description",
        content:
          "Turn thousands of opportunities into a focused queue: deal → score → reason → risk → next action.",
      },
    ],
  }),
  component: Console,
});

type Source = "none" | "public";

function Console() {
  const { t, lang } = useI18n();
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [source, setSource] = useState<Source>("none");
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [scoringOpen, setScoringOpen] = useState(false);
  const [checkedPublic, setCheckedPublic] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [isDesktop, setIsDesktop] = useState(true);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem("pipeline-focus-filters");
      if (saved) setFilters({ ...EMPTY_FILTERS, ...JSON.parse(saved) });
    } catch {
      // localStorage is non-critical; ignore malformed saved state.
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem("pipeline-focus-filters", JSON.stringify(filters));
    } catch {
      // Non-critical persistence.
    }
  }, [filters]);

  useEffect(() => {
    const mql = window.matchMedia("(min-width: 1024px)");
    const onChange = () => setIsDesktop(mql.matches);
    onChange();
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    let active = true;
    setCheckedPublic(false);
    loadFromPublic()
      .then((d) => {
        if (!active) return;
        if (d && d.pipeline.length) {
          setDataset(d);
          setSource("public");
          return;
        }
        setDataset(null);
        setSource("none");
      })
      .catch(() => {
        if (!active) return;
        setDataset(null);
        setSource("none");
      })
      .finally(() => {
        if (active) setCheckedPublic(true);
      });
    return () => {
      active = false;
    };
  }, [reloadKey]);

  const { deals, meta } = useMemo(() => {
    if (!dataset || !dataset.pipeline.length) {
      return { deals: [] as ScoredDeal[], meta: { globalWinRate: 0, referenceDate: "" } };
    }
    return scoreDataset(dataset, lang);
  }, [dataset, lang]);

  const options = useMemo(() => {
    const uniq = (arr: (string | undefined)[]) =>
      Array.from(new Set(arr.filter((v): v is string => !!v))).sort();
    return {
      sellers: uniq(deals.map((d) => d.salesAgent)),
      managers: uniq(deals.map((d) => d.manager)),
      regions: uniq(deals.map((d) => d.region)),
      stages: uniq(deals.map((d) => d.stage)),
      products: uniq(deals.map((d) => d.product)),
    };
  }, [deals]);

  const filtered = useMemo(() => {
    const q = filters.search.trim().toLowerCase();
    return deals.filter((d) => {
      if (filters.seller !== "all" && d.salesAgent !== filters.seller) return false;
      if (filters.manager !== "all" && d.manager !== filters.manager) return false;
      if (filters.region !== "all" && d.region !== filters.region) return false;
      if (filters.stage !== "all" && d.stage !== filters.stage) return false;
      if (filters.priority !== "all" && d.priority !== filters.priority) return false;
      if (filters.product !== "all" && d.product !== filters.product) return false;
      if (q && !`${d.account} ${d.opportunity_id} ${d.product}`.toLowerCase().includes(q))
        return false;
      for (const quick of filters.quick) {
        if (!matchesQuick(d, quick)) return false;
      }
      return true;
    });
  }, [deals, filters]);

  // Auto-select the #1 deal only on desktop so the side panel is never empty.
  // On mobile, keep the queue visible until the user taps a deal.
  useEffect(() => {
    if (!filtered.length) {
      if (selectedId !== null) setSelectedId(null);
      return;
    }
    if (!isDesktop) {
      if (selectedId && !filtered.some((d) => d.opportunity_id === selectedId)) {
        setSelectedId(null);
      }
      return;
    }
    if (!selectedId || !filtered.some((d) => d.opportunity_id === selectedId)) {
      setSelectedId(filtered[0].opportunity_id);
    }
  }, [filtered, isDesktop, selectedId]);

  const selected = useMemo(
    () => filtered.find((d) => d.opportunity_id === selectedId) ?? null,
    [filtered, selectedId],
  );

  const hasData = !!dataset && dataset.pipeline.length > 0;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-border bg-navy-950/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md border border-gold/40 bg-gold/10">
              <Target className="h-5 w-5 text-gold" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold leading-tight text-offwhite">
                  Pipeline Focus Console
                </h1>
                <span className="hidden rounded border border-gold/30 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-gold sm:inline">
                  G4 AI Master
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{t("app.subtitle")}</p>
            </div>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <DataStatus source={source} dataset={dataset} checked={checkedPublic} />
            <LanguageToggle />
            <Button variant="outline" size="sm" onClick={() => setScoringOpen(true)}>
              <Scale className="h-4 w-4" />{" "}
              <span className="hidden sm:inline">{t("header.scoringLogic")}</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1500px] px-4 py-5">
        {!hasData ? (
          <DataUnavailableState
            checked={checkedPublic}
            onRetry={() => setReloadKey((v) => v + 1)}
          />
        ) : (
          <div className="space-y-4">
            <MetricCards deals={deals} />
            <MorningBrief deals={deals} />
            <FilterBar
              filters={filters}
              onChange={setFilters}
              options={options}
              resultCount={filtered.length}
            />

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
              <div className="lg:col-span-8">
                <DealsTable deals={filtered} selectedId={selectedId} onSelect={setSelectedId} />
              </div>
              {/* Desktop sticky panel */}
              <div className="hidden lg:col-span-4 lg:block">
                <div className="sticky top-[4.75rem]">
                  <DealPanel deal={selected} onClose={() => setSelectedId(null)} />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
              <div className="xl:col-span-8">
                <ManagerView deals={deals} />
              </div>
              <div className="xl:col-span-4">
                <DataQualitySummary deals={deals} />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Mobile deal detail */}
      <Sheet
        open={!!selected && !isDesktop}
        onOpenChange={(v) => {
          if (!v) setSelectedId(null);
        }}
      >
        <SheetContent side="bottom" className="max-h-[88vh] overflow-y-auto bg-card lg:hidden">
          <SheetHeader className="text-left">
            <SheetTitle>{selected?.account || selected?.opportunity_id}</SheetTitle>
          </SheetHeader>
          {selected && (
            <div className="mt-4">
              <DealPanelBody deal={selected} />
            </div>
          )}
        </SheetContent>
      </Sheet>

      <ScoringLogic
        open={scoringOpen}
        onOpenChange={setScoringOpen}
        referenceDate={meta.referenceDate}
        globalWinRate={meta.globalWinRate}
      />
    </div>
  );
}

function DataStatus({
  source,
  dataset,
  checked,
}: {
  source: Source;
  dataset: Dataset | null;
  checked: boolean;
}) {
  const { t, num } = useI18n();
  let label: string;
  let tone: string;
  const n = num(dataset?.pipeline.length ?? 0);
  if (source === "public") {
    label = t("status.liveCsvs", { n });
    tone = "text-success border-success/40 bg-success/10";
  } else {
    label = checked ? t("status.noData") : t("status.checking");
    tone = "text-muted-foreground border-border bg-secondary/40";
  }
  return (
    <span
      className={cn(
        "hidden items-center gap-1.5 rounded-md border px-2 py-1 text-xs font-medium md:inline-flex",
        tone,
      )}
    >
      <Database className="h-3.5 w-3.5" /> {label}
    </span>
  );
}

function DataUnavailableState({ checked, onRetry }: { checked: boolean; onRetry: () => void }) {
  const { t } = useI18n();
  const title = checked ? t("empty.unavailable.title") : t("empty.loading.title");
  const body = checked ? t("empty.unavailable.body") : t("empty.loading.body");

  return (
    <div className="mx-auto mt-10 max-w-md rounded-lg border border-border bg-card p-8 text-center shadow-sm">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg border border-gold/40 bg-gold/10">
        {checked ? (
          <Database className="h-6 w-6 text-gold" />
        ) : (
          <Loader2 className="h-6 w-6 animate-spin text-gold" />
        )}
      </div>
      <h2 className="mt-4 text-lg font-bold text-foreground">{title}</h2>
      <p className="mx-auto mt-2 max-w-sm text-sm text-muted-foreground">{body}</p>
      {checked && (
        <div className="mt-6">
          <Button onClick={onRetry}>
            <RefreshCcw className="h-4 w-4" /> {t("empty.retry")}
          </Button>
        </div>
      )}
    </div>
  );
}
