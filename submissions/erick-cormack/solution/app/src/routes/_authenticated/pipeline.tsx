import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { zodValidator } from "@tanstack/zod-adapter";
import { useMemo } from "react";
import { PageHeader } from "@/components/AppShell";
import { ExportButtons } from "@/components/lead/ExportButtons";
import { FilterBar } from "@/components/lead/FilterBar";
import { ManagerChart } from "@/components/lead/HomeCharts";
import { PipelineTabs } from "@/components/lead/PipelineTabs";
import { ErrorState, LoadingState } from "@/components/lead/States";
import { SummaryCards } from "@/components/lead/SummaryCards";
import { useDeals } from "@/hooks/useDeals";
import { exportPipelinePdf, exportPipelineXlsx } from "@/lib/export";
import { filterSearchSchema, matchesFilters } from "@/lib/filters";
import { calcIndicadores } from "@/lib/metrics";

export const Route = createFileRoute("/_authenticated/pipeline")({
  validateSearch: zodValidator(filterSearchSchema),
  head: () => ({
    meta: [
      { title: "Meu pipeline — Lead Scorer" },
      { name: "description", content: "Suas oportunidades priorizadas para a semana, com o motivo de cada score." },
      { property: "og:title", content: "Meu pipeline — Lead Scorer" },
      { property: "og:description", content: "Suas oportunidades priorizadas para a semana, com o motivo de cada score." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: PipelinePage,
});

function PipelinePage() {
  const filters = Route.useSearch();
  const navigate = useNavigate({ from: "/pipeline" });
  const { data, isLoading, error, refetch } = useDeals();

  const deals = useMemo(() => (data ?? []).filter((d) => matchesFilters(d, filters)), [data, filters]);
  const ind = useMemo(() => (data ? calcIndicadores(deals) : undefined), [data, deals]);

  return (
    <>
      <PageHeader title="Meu pipeline" subtitle={filters.vendedor ? `Onde ${filters.vendedor} deve focar nesta semana` : "Onde focar nesta semana"} />
      <FilterBar filters={filters} onChange={(f) => navigate({ search: f })} />
      <div className="flex justify-end px-4 pt-4 md:px-8">
        <ExportButtons
          disabled={isLoading || !!error || !ind || deals.length === 0}
          onPdf={() => ind && exportPipelinePdf(deals, filters, ind)}
          onXlsx={() => exportPipelineXlsx(deals, filters)}
        />
      </div>
      {error ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : (
        <>
          <SummaryCards ind={ind} loading={isLoading} />
          {!isLoading && deals.length > 0 && (
            <section className="px-4 pb-6 md:px-8">
              <div className="rounded-lg border border-border bg-card p-4 md:p-6">
                <h2 className="font-display text-2xl">Valor esperado em foco por manager</h2>
                <p className="mt-1 text-sm text-muted-foreground">Quanto cada manager tem em deals prontos para focar, neste recorte.</p>
                <div className="mt-4"><ManagerChart deals={deals} /></div>
              </div>
            </section>
          )}
           {isLoading ? <div className="px-4 md:px-8"><LoadingState /></div> : <PipelineTabs key={JSON.stringify(filters)} deals={deals} showVendedor={!filters.vendedor} />}
        </>
      )}
    </>
  );
}
