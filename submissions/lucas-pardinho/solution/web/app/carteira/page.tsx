import { PortfolioView } from "@/components/portfolio-view";
import { getDataStatus, getOpportunities } from "@/lib/data";

export const dynamic = "force-dynamic";

export default async function PortfolioPage() {
  const [opportunities, status] = await Promise.all([getOpportunities(), getDataStatus()]);
  return <PortfolioView opportunities={opportunities} status={status} />;
}
