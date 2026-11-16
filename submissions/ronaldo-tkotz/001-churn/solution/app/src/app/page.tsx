import { kpis, churnTrend, tableInventory } from "@/engine/dashboard";
import { dataClock } from "@/engine/calendar";
import { activeDataset } from "@/engine/datasets";
import { requireUser } from "@/app/lib/auth";
import { Sidebar } from "./components/dashboard/Sidebar";
import { TopBar } from "./components/dashboard/TopBar";
import { ConnectDialog } from "./components/dashboard/ConnectDialog";
import { DataSourceDialog } from "./components/dashboard/DataSourceDialog";
import { ConversationCanvas } from "./components/dashboard/ConversationCanvas";
import { ExecutiveBrief } from "./components/dashboard/ExecutiveBrief";
import { CustomDatasetBrief } from "./components/dashboard/CustomDatasetBrief";

// Computed at request time from the read-only database — never prerendered.
export const dynamic = "force-dynamic";

export default async function Home() {
  const user = await requireUser();
  const userCtx = { userId: user.id };
  const active = activeDataset(user.id);
  const tables = tableInventory(active.is_default ? {} : userCtx);

  // An uploaded database: the curated board reads the RavenStack views, so the
  // surface goes to the schema-agnostic chat — still fully grounded.
  if (!active.is_default) {
    const ctx = { source: active.label, tableCount: tables.length, asOf: "", firstDate: "", lastDate: "" };
    return (
      <div className="flex h-screen overflow-hidden bg-background">
        <div className="hidden lg:block">
          <Sidebar email={user.email} />
        </div>
        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar ctx={ctx} tables={tables} />
          <main className="flex min-h-0 flex-1 gap-4 overflow-hidden p-4">
            <ConversationCanvas idleBrief={<CustomDatasetBrief label={active.label} tables={tables} />} />
          </main>
        </div>
        <ConnectDialog />
        <DataSourceDialog />
      </div>
    );
  }

  // RavenStack: descriptive KPIs + monthly churn, then the grounded chat.
  // The model-written "discovered stories" rail stays off: conclusions come from the analysis.
  const k = kpis();
  const trend = churnTrend();
  const clock = dataClock();
  const datasetContext = {
    source: active.label,
    tableCount: tables.length,
    asOf: clock.today,
    firstDate: clock.firstDate,
    lastDate: clock.lastDate,
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <div className="hidden lg:block">
        <Sidebar email={user.email} />
      </div>

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar ctx={datasetContext} tables={tables} />
        <main className="flex min-h-0 flex-1 gap-4 overflow-hidden p-4">
          <ConversationCanvas idleBrief={<ExecutiveBrief kpis={k} trend={trend} />} />
        </main>
      </div>

      <ConnectDialog />
      <DataSourceDialog />
    </div>
  );
}
