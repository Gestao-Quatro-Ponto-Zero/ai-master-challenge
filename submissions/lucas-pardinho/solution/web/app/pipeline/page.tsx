import { PipelineExplorer } from "@/components/pipeline-explorer";
import { getDataStatus, getOpportunities } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function PipelinePage({
  searchParams,
}: {
  searchParams: Promise<{ queue?: string; selected?: string }>;
}) {
  const [opportunities, status, params] = await Promise.all([
    getOpportunities(),
    getDataStatus(),
    searchParams,
  ]);

  return (
    <PipelineExplorer
      opportunities={opportunities}
      status={status}
      initialQueue={params.queue ?? ""}
      initialSelected={params.selected ?? ""}
    />
  );
}
