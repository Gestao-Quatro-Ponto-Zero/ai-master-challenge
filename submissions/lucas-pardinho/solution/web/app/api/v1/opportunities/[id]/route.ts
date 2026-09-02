import { apiError } from "@/lib/api";
import { getDataStatus, getOpportunities } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const [{ id }, opportunities, status] = await Promise.all([
      context.params,
      getOpportunities(),
      getDataStatus(),
    ]);
    const opportunity = opportunities.find((item) => item.opportunityId === id);

    if (!opportunity) {
      return Response.json(
        { error: { code: "NOT_FOUND", message: "Oportunidade não encontrada." } },
        { status: 404 },
      );
    }

    return Response.json({ data: opportunity, meta: { source: status.source } });
  } catch (error) {
    return apiError(error);
  }
}
