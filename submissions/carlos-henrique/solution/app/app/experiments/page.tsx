import { loadData } from "@/lib/data";
import type { Experiment } from "@/lib/types";
import { DataFreshness, LimitationCallout, SectionHeader } from "@/components/ui";
import { GroupedSampleChart, MultiColorBarChart } from "@/components/DashboardCharts";
import { ExperimentExplorer } from "@/components/ExperimentExplorer";

interface Registry { cutoff: string; experiments: Experiment[] }
interface Details { experiments: Experiment[] }

export default async function ExperimentsPage() {
  const [registry, details] = await Promise.all([loadData<Registry>("experiment_registry.json"), loadData<Details>("experiment_details.json")]);
  const samples = registry.experiments.map((item) => ({ experiment: item.experiment_id, available: item.eligible_accounts, required: item.required_sample }));
  const statusMap = new Map<string, number>(); registry.experiments.forEach((item) => statusMap.set(item.status, (statusMap.get(item.status) ?? 0) + 1));
  const statuses = Array.from(statusMap, ([status, experiments]) => ({ status, experiments }));
  return <div><SectionHeader eyebrow="Experiment lab" title="Observation is not causality." description="Eight future designs turn governed observations into falsifiable hypotheses. Feasibility, sample size, SAP, and ethics are visible before any operational review." /><DataFreshness cutoff={registry.cutoff} /><div className="mt-7"><LimitationCallout title="Untested hypothesis">Every causal status is UNTESTED. Simulated assignments validate design mechanics only; no experiment or intervention has been executed.</LimitationCallout></div><section className="mt-6 grid gap-5 xl:grid-cols-2"><GroupedSampleChart data={samples} /><MultiColorBarChart data={statuses} category="status" value="experiments" title="Experiment feasibility status" subtitle="Eight governed designs · no success or failure state" summary="One design is ready for review; the remainder are pilot-only, underpowered, or not feasible." /></section><div className="mt-8"><ExperimentExplorer registry={registry.experiments} details={details.experiments} /></div></div>;
}
