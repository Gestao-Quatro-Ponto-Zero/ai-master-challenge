import { MethodologyContent } from "@/components/methodology-content";
import { getDataQualityReport, getDataStatus, getModelReport, getOpportunities } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function MethodologyPage() {
  const [opportunities, modelReport, dataQuality, status] = await Promise.all([
    getOpportunities(),
    getModelReport(),
    getDataQualityReport(),
    getDataStatus(),
  ]);

  return (
    <MethodologyContent
      opportunities={opportunities}
      modelReport={modelReport}
      dataQuality={dataQuality}
      status={status}
    />
  );
}
