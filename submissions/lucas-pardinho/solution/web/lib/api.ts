import type { OpportunityFilters } from "@/lib/analytics";

export interface OpportunityQuery extends OpportunityFilters {
  page: number;
  pageSize: number;
}

export function parseOpportunityQuery(searchParams: URLSearchParams): OpportunityQuery {
  const page = positiveInteger(searchParams.get("page"), 1);
  const pageSize = Math.min(100, positiveInteger(searchParams.get("pageSize"), 25));
  const sortValue = searchParams.get("sort");
  const orderValue = searchParams.get("order");

  return {
    page,
    pageSize,
    search: clean(searchParams.get("search")),
    queue: clean(searchParams.get("queue")),
    salesAgent: clean(searchParams.get("salesAgent")),
    manager: clean(searchParams.get("manager")),
    regionalOffice: clean(searchParams.get("regionalOffice")),
    dealStage: clean(searchParams.get("dealStage")),
    sort:
      sortValue === "value" || sortValue === "age" || sortValue === "probability"
        ? sortValue
        : "score",
    order: orderValue === "asc" ? "asc" : "desc",
  };
}

function positiveInteger(value: string | null, fallback: number): number {
  if (!value) return fallback;
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function clean(value: string | null): string | undefined {
  const cleaned = value?.trim();
  return cleaned || undefined;
}

export function apiError(error: unknown, message = "Não foi possível carregar os dados."): Response {
  const detail = process.env.NODE_ENV === "development" && error instanceof Error ? error.message : undefined;
  return Response.json(
    { error: { code: "DATA_UNAVAILABLE", message, ...(detail ? { detail } : {}) } },
    { status: 503 },
  );
}
