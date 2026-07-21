import { loadData } from "@/lib/data";
import type { JourneySample } from "@/lib/types";
import { DataFreshness, SectionHeader } from "@/components/ui";
import { JourneyExplorer } from "@/components/JourneyExplorer";
import { MultiColorBarChart, SimpleBarChart } from "@/components/DashboardCharts";

interface Samples { cutoff: string; samples: JourneySample[] }
interface JourneyIndex { outcome_distribution: Array<{ outcome: string; accounts: number }>; taxonomy_distribution: Array<{ taxonomy: string; accounts: number }> }

export default async function JourneysPage() {
  const [samples, index] = await Promise.all([loadData<Samples>("journey_samples.json"), loadData<JourneyIndex>("journey_index.json")]);
  return <div><SectionHeader eyebrow="Journey explorer" title="Three real journeys, bounded for explanation." description="Select an anonymous account to inspect its governed timeline, observed outcome, taxonomy, quality coverage, linked patterns, and interpretation limits." /><DataFreshness cutoff={samples.cutoff} /><div className="mt-7"><JourneyExplorer samples={samples.samples} /></div><section className="mt-8 grid gap-5 xl:grid-cols-2"><MultiColorBarChart data={index.outcome_distribution} category="outcome" value="accounts" title="Journey outcome distribution" subtitle="Unique accounts · full observed journey · MAIN population" summary="No observed churn, single churn, recurring churn, and reactivation are historical outcome classes." /><SimpleBarChart data={index.taxonomy_distribution.slice(0, 8)} category="taxonomy" value="accounts" title="Journey taxonomy distribution" subtitle="Top deterministic primary classes · unique accounts" summary="Taxonomy labels organize evidence; they are not scores or forecasts." /></section></div>;
}
