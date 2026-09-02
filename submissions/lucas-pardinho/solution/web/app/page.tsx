import { ExecutiveDashboard } from "@/components/executive-dashboard";
import { getDataStatus, getOpportunities } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const [opportunities, status] = await Promise.all([getOpportunities(), getDataStatus()]);
  return <ExecutiveDashboard opportunities={opportunities} status={status} />;
}
