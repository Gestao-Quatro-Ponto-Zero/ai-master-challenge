import { apiError } from "@/lib/api";
import { summarizeOpportunities } from "@/lib/analytics";
import { getDashboardFile, getDataStatus, getOpportunities } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const [opportunities, generated, status] = await Promise.all([
      getOpportunities(),
      getDashboardFile(),
      getDataStatus(),
    ]);

    return Response.json({
      data: {
        summary: summarizeOpportunities(opportunities),
        generated,
      },
      meta: { source: status.source, generatedAt: new Date().toISOString() },
    });
  } catch (error) {
    return apiError(error);
  }
}
