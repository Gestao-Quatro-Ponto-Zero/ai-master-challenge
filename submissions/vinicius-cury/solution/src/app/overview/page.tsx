import { PageHeader } from "@/components/page-header";
import { OverviewDashboard } from "../overview-dashboard";

export default function OverviewPage() {
  return (
    <>
      <PageHeader
        title="Overview"
        description="KPI summary and distribution charts for support operations."
      />
      <OverviewDashboard />
    </>
  );
}
