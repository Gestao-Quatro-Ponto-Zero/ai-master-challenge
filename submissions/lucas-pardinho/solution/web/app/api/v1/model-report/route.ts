import { apiError } from "@/lib/api";
import { getDataQualityReport, getDataStatus, getModelReport } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const [model, dataQuality, status] = await Promise.all([
      getModelReport(),
      getDataQualityReport(),
      getDataStatus(),
    ]);

    return Response.json({
      data: { model, dataQuality },
      meta: { source: status.source },
    });
  } catch (error) {
    return apiError(error);
  }
}
