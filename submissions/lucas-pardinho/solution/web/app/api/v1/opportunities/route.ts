import { apiError, parseOpportunityQuery } from "@/lib/api";
import { filterOpportunities } from "@/lib/analytics";
import { getDataStatus, getOpportunities } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const query = parseOpportunityQuery(new URL(request.url).searchParams);
    const [opportunities, status] = await Promise.all([getOpportunities(), getDataStatus()]);
    const filtered = filterOpportunities(opportunities, query);
    const start = (query.page - 1) * query.pageSize;

    return Response.json({
      data: filtered.slice(start, start + query.pageSize),
      meta: {
        source: status.source,
        page: query.page,
        pageSize: query.pageSize,
        total: filtered.length,
        totalPages: Math.max(1, Math.ceil(filtered.length / query.pageSize)),
      },
      filters: query,
    });
  } catch (error) {
    return apiError(error);
  }
}
