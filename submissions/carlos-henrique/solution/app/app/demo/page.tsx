import { loadData } from "@/lib/data";
import { DataFreshness, SectionHeader } from "@/components/ui";
import { GuidedDemo } from "@/components/GuidedDemo";

interface Story { duration_minutes: string; demo_accounts: string[]; steps: Array<{ step: number; title: string; route: string; sentence: string; metric: string; insight: string; limitation: string }> }
interface Metadata { data_cutoff: string }

export default async function DemoPage() {
  const [story, metadata] = await Promise.all([loadData<Story>("demo_story.json"), loadData<Metadata>("metadata.json")]);
  return <div><SectionHeader eyebrow="Guided demo" title="Eight steps from raw data to governed decisions." description="A concise narrative for evaluators: one visual, one metric, one insight, and one limitation at each step." /><DataFreshness cutoff={metadata.data_cutoff} /><div className="mt-7"><GuidedDemo steps={story.steps} duration={story.duration_minutes} /></div><section className="mt-7 panel p-5"><p className="eyebrow">Anonymous demo accounts</p><div className="mt-4 flex flex-wrap gap-3">{story.demo_accounts.map((account, index) => <span className="rounded-lg border border-line bg-slate-50 px-3 py-2 font-mono text-xs" key={account}>DEMO_{String.fromCharCode(65 + index)} · {account}</span>)}</div></section></div>;
}
