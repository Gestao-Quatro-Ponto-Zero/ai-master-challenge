import { loadData } from "@/lib/data";
import { DataFreshness, GovernanceChecklist, LimitationCallout, SectionHeader } from "@/components/ui";
import { SimpleBarChart } from "@/components/DashboardCharts";

interface Governance { cutoff: string; checks: Array<{ label: string; passed: boolean }>; assumptions: string[]; warnings: string[]; prohibited_operations: string[]; human_decision_points: string[]; decision_groups: Array<{ category: string; range: string; count: number }>; decision_count: number; limitations: string[] }

export default async function GovernancePage() {
  const governance = await loadData<Governance>("governance.json");
  return <div><SectionHeader eyebrow="Governance" title="Guardrails are part of the product." description="Privacy, temporal integrity, reproducibility, and human decision points remain visible instead of being hidden in technical appendices." /><DataFreshness cutoff={governance.cutoff} /><div className="mt-7"><GovernanceChecklist checks={governance.checks} /></div><section className="mt-7 grid gap-5 xl:grid-cols-[1fr_.9fr]"><SimpleBarChart data={governance.decision_groups} category="category" value="count" title="Recorded decisions by domain" subtitle={`${governance.decision_count} versioned decisions through Experiment Lab`} summary="Decisions span data, temporal logic, survival, journeys, graph, watchlist, and experimentation." /><div className="grid gap-4 sm:grid-cols-2"><ListPanel title="Assumptions" items={governance.assumptions} /><ListPanel title="Warnings" items={governance.warnings} /><ListPanel title="Prohibited operations" items={governance.prohibited_operations} /><ListPanel title="Human decision points" items={governance.human_decision_points} /></div></section><div className="mt-7"><LimitationCallout>Demo mode is a fixed local snapshot without authentication, production observability, outbound integrations, external databases, or an LLM.</LimitationCallout></div></div>;
}

function ListPanel({ title, items }: { title: string; items: string[] }) { return <article className="panel p-5"><h3 className="font-semibold">{title}</h3><ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">{items.map((item) => <li key={item}>{item}</li>)}</ul></article>; }
