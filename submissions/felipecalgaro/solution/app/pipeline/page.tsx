import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";

import { getAccountsRows, getProductRows, getSalesPipelineRows } from "@/utils/crm-data";
import { calculateDealScoreBreakdown } from "@/utils/deal-score";

import { PipelineDealsList } from "@/app/components/pipeline-deals-list";

const SALES_AGENT_COOKIE = "lead-scorer-sales-agent";

type StagePriority = "none" | "engaging" | "prospecting";

const DEFAULT_PAGE_SIZE = 8;
const MIN_PAGE_SIZE = 1;
const MAX_PAGE_SIZE = 100;

function normalize(value: string): string {
  return value.trim().toLowerCase();
}

function parsePositiveInteger(value?: string): number | null {
  if (!value) return null;
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0) return null;
  return parsed;
}

function parseStagePriority(value?: string): StagePriority {
  if (value === "engaging" || value === "prospecting") {
    return value;
  }
  return "none";
}

function stageOrder(stage: string, stagePriority: StagePriority): number {
  const normalizedStage = normalize(stage);
  if (stagePriority === "none") return 0;
  if (stagePriority === "engaging") {
    return normalizedStage === "engaging" ? 0 : 1;
  }
  return normalizedStage === "prospecting" ? 0 : 1;
}

function buildPipelineHref(input: {
  stagePriority: StagePriority;
  page?: number;
  pageSize?: number;
}): string {
  const params = new URLSearchParams();

  if (input.stagePriority !== "none") {
    params.set("prioritize", input.stagePriority);
  }

  if (input.page && input.page > 1) {
    params.set("page", String(input.page));
  }

  if (input.pageSize && input.pageSize !== DEFAULT_PAGE_SIZE) {
    params.set("pageSize", String(input.pageSize));
  }

  const query = params.toString();
  return query ? `/pipeline?${query}` : "/pipeline";
}

export default async function PipelinePage({
  searchParams,
}: {
  searchParams?: Promise<{
    prioritize?: string;
    page?: string;
    pageSize?: string;
  }>;
}) {
  const cookieStore = await cookies();
  const selectedSalesAgent = cookieStore.get(SALES_AGENT_COOKIE)?.value;

  if (!selectedSalesAgent) {
    redirect("/");
  }

  const params = await searchParams;
  const stagePriority = parseStagePriority(params?.prioritize);
  const pageSize = Math.min(
    MAX_PAGE_SIZE,
    Math.max(
      MIN_PAGE_SIZE,
      parsePositiveInteger(params?.pageSize) ?? DEFAULT_PAGE_SIZE,
    ),
  );

  const [salesPipeline, accounts, products] = await Promise.all([
    getSalesPipelineRows(),
    getAccountsRows(),
    getProductRows(),
  ]);

  const selectedAgentDeals = salesPipeline.filter(
    (row) => normalize(row.sales_agent) === normalize(selectedSalesAgent),
  );

  const openAgentDeals = selectedAgentDeals.filter((row) => {
    const stage = normalize(row.deal_stage);
    return stage === "engaging" || stage === "prospecting";
  });

  const rankedDeals = openAgentDeals
    .map((deal) => {
      const scoreBreakdown = calculateDealScoreBreakdown({
        deal,
        salesPipeline,
        accounts,
        products,
      });

      return {
        ...deal,
        score: scoreBreakdown.finalScore,
        scoreBreakdown,
      };
    })
    .sort((left, right) => {
      const stageDiff =
        stageOrder(left.deal_stage, stagePriority) -
        stageOrder(right.deal_stage, stagePriority);

      if (stageDiff !== 0) {
        return stageDiff;
      }

      if (right.score !== left.score) {
        return right.score - left.score;
      }

      return left.opportunity_id.localeCompare(right.opportunity_id);
    });

  const totalDeals = rankedDeals.length;
  const totalPages = Math.max(1, Math.ceil(totalDeals / pageSize));
  const requestedPage = parsePositiveInteger(params?.page) ?? 1;
  const currentPage = Math.min(requestedPage, totalPages);
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedDeals = rankedDeals.slice(startIndex, startIndex + pageSize);
  const paginatedDealsWithViewModel = paginatedDeals.map((deal, index) => ({
    opportunityId: deal.opportunity_id,
    salesAgent: deal.sales_agent,
    product: deal.product,
    account: deal.account,
    stage: deal.deal_stage,
    score: deal.score,
    rank: startIndex + index + 1,
    topPositiveFactors: deal.scoreBreakdown.topPositiveFactors,
    topNegativeFactors: deal.scoreBreakdown.topNegativeFactors,
  }));

  const activePriorityLabel =
    stagePriority === "none"
      ? "Somente score"
      : stagePriority === "engaging"
        ? "Engajamento primeiro"
        : "Prospecção primeiro";

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#f4ede2,#efe7db)] px-6 py-10 text-stone-900 sm:px-10 lg:px-16">
      <div className="mx-auto max-w-6xl space-y-8">
        <header className="rounded-4xl border border-stone-900/10 bg-white/85 px-8 py-8 shadow-[0_20px_60px_rgba(76,61,43,0.12)] backdrop-blur">
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-stone-500">
            Funil
          </p>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-stone-950">
                {selectedSalesAgent}
              </h1>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-600">
                Negócios abertos sao ranqueados por score, com prioridade opcional
                por etapa para exibir Engajamento ou Prospecção primeiro.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Link
                className="inline-flex items-center justify-center rounded-2xl border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 transition hover:border-stone-950 hover:text-stone-950"
                href="/"
              >
                Trocar vendedor
              </Link>
              <span className="rounded-2xl bg-stone-950 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-stone-50">
                {activePriorityLabel}
              </span>
            </div>
          </div>
        </header>

        <section className="rounded-4xl border border-stone-900/10 bg-white/85 p-6 shadow-[0_20px_60px_rgba(76,61,43,0.12)] backdrop-blur sm:p-8">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm font-medium text-stone-600">Prioridade de etapa:</span>
            <Link
              className={`rounded-xl px-3 py-2 text-sm font-medium transition ${stagePriority === "none"
                ? "bg-stone-950 text-stone-50"
                : "bg-stone-100 text-stone-700 hover:bg-stone-200"
                }`}
              href={buildPipelineHref({
                stagePriority: "none",
                page: 1,
                pageSize,
              })}
            >
              Somente score
            </Link>
            <Link
              className={`rounded-xl px-3 py-2 text-sm font-medium transition ${stagePriority === "engaging"
                ? "bg-stone-950 text-stone-50"
                : "bg-stone-100 text-stone-700 hover:bg-stone-200"
                }`}
              href={buildPipelineHref({
                stagePriority: "engaging",
                page: 1,
                pageSize,
              })}
            >
              Engajamento primeiro
            </Link>
            <Link
              className={`rounded-xl px-3 py-2 text-sm font-medium transition ${stagePriority === "prospecting"
                ? "bg-stone-950 text-stone-50"
                : "bg-stone-100 text-stone-700 hover:bg-stone-200"
                }`}
              href={buildPipelineHref({
                stagePriority: "prospecting",
                page: 1,
                pageSize,
              })}
            >
              Prospecção primeiro
            </Link>
          </div>

          <form className="mt-4 flex flex-wrap items-center gap-3" method="get">
            {stagePriority !== "none" ? (
              <input name="prioritize" type="hidden" value={stagePriority} />
            ) : null}
            <label className="text-sm font-medium text-stone-600" htmlFor="pageSize">
              Negócios por pagina
            </label>
            <input
              className="w-24 rounded-xl border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900"
              defaultValue={pageSize}
              id="pageSize"
              max={MAX_PAGE_SIZE}
              min={MIN_PAGE_SIZE}
              name="pageSize"
              type="number"
            />
            <button
              className="rounded-xl bg-stone-950 px-3 py-2 text-sm font-medium text-stone-50 transition hover:bg-stone-800"
              type="submit"
            >
              Aplicar
            </button>
          </form>

          {rankedDeals.length === 0 ? (
            <p className="mt-6 rounded-2xl border border-stone-200 bg-stone-50 px-4 py-6 text-sm text-stone-600">
              Nenhum negócio em Engajamento ou Prospecção foi encontrado para este vendedor.
            </p>
          ) : (
            <div className="mt-6 space-y-4">
              <div className="text-sm text-stone-600">
                Exibindo {startIndex + 1}-{Math.min(startIndex + pageSize, totalDeals)} de {totalDeals} negócios.
              </div>

              <div className="overflow-x-auto">
                <PipelineDealsList deals={paginatedDealsWithViewModel} />
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Link
                  aria-disabled={currentPage === 1}
                  className={`rounded-xl px-3 py-2 text-sm font-medium transition ${currentPage === 1
                    ? "pointer-events-none bg-stone-100 text-stone-400"
                    : "bg-stone-950 text-stone-50 hover:bg-stone-800"
                    }`}
                  href={buildPipelineHref({
                    stagePriority,
                    page: Math.max(1, currentPage - 1),
                    pageSize,
                  })}
                >
                  Anterior
                </Link>

                <span className="px-2 text-sm text-stone-600">
                  Pagina {currentPage} de {totalPages}
                </span>

                <Link
                  aria-disabled={currentPage === totalPages}
                  className={`rounded-xl px-3 py-2 text-sm font-medium transition ${currentPage === totalPages
                    ? "pointer-events-none bg-stone-100 text-stone-400"
                    : "bg-stone-950 text-stone-50 hover:bg-stone-800"
                    }`}
                  href={buildPipelineHref({
                    stagePriority,
                    page: Math.min(totalPages, currentPage + 1),
                    pageSize,
                  })}
                >
                  Proxima
                </Link>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}