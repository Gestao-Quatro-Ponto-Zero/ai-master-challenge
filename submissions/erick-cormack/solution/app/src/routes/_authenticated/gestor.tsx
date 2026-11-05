import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { zodValidator } from "@tanstack/zod-adapter";
import { useMemo } from "react";
import { PageHeader } from "@/components/AppShell";
import { ExportButtons } from "@/components/lead/ExportButtons";
import { FilterBar } from "@/components/lead/FilterBar";
import { ResumoTable } from "@/components/lead/ResumoTable";
import { ErrorState } from "@/components/lead/States";
import { SummaryCards } from "@/components/lead/SummaryCards";
import { useDeals } from "@/hooks/useDeals";
import { useResumoVendedores } from "@/hooks/useResumoVendedores";
import { exportGestorPdf, exportGestorXlsx, type ResumoRow } from "@/lib/export";
import { filterSearchSchema, matchesFilters } from "@/lib/filters";
import { calcIndicadores, pctParado } from "@/lib/metrics";

export const Route = createFileRoute("/_authenticated/gestor")({
  validateSearch: zodValidator(filterSearchSchema),
  head: () => ({
    meta: [
      { title: "Visão do gestor — Lead Scorer" },
      { name: "description", content: "Pipeline do time por vendedor: foco, deals parados e alertas de cadastro." },
      { property: "og:title", content: "Visão do gestor — Lead Scorer" },
      { property: "og:description", content: "Pipeline do time por vendedor: foco, deals parados e alertas de cadastro." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: GestorPage,
});

function GestorPage() {
  const filters = Route.useSearch();
  const navigate = useNavigate({ from: "/gestor" });
  const { data, isLoading, error, refetch } = useDeals();
  const { data: resumo } = useResumoVendedores();
  const ind = useMemo(() => (data ? calcIndicadores(data.filter((d) => matchesFilters(d, filters))) : undefined), [data, filters]);
  const rows = useMemo<ResumoRow[]>(
    () =>
      (resumo ?? [])
        .filter((r) => matchesFilters(r, filters))
        .map((r) => ({ ...r, pct_parado: pctParado(r.deals_focar ?? 0, r.deals_requalificar ?? 0, r.deals_prospectar ?? 0) })),
    [resumo, filters],
  );

  return (
    <>
      <PageHeader title="Visão do gestor" subtitle="Como está o pipeline do time" />
      <FilterBar filters={filters} onChange={(f) => navigate({ search: f })} />
      <div className="flex justify-end px-4 pt-4 md:px-8">
        <ExportButtons
          disabled={isLoading || !!error || !ind || rows.length === 0}
          onPdf={() => ind && exportGestorPdf(rows, filters, ind)}
          onXlsx={() => exportGestorXlsx(rows, filters)}
        />
      </div>
      {error ? <ErrorState error={error} onRetry={() => refetch()} /> : <SummaryCards ind={ind} loading={isLoading} />}
      <ResumoTable filters={filters} />
    </>
  );
}
