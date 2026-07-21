"use client";

import { useMemo, useState } from "react";
import { CalendarDays, Circle } from "lucide-react";
import type { JourneySample } from "@/lib/types";
import { ExplainThis, LimitationCallout, QualityBadge, StabilityBadge } from "@/components/ui";
import { formatPercent, humanize } from "@/lib/format";

const eventStyle: Record<string, string> = {
  ACCOUNT: "bg-slate-500",
  SUBSCRIPTION_START: "bg-blue",
  SUBSCRIPTION_END: "bg-slate-700",
  FEATURE: "bg-olive",
  SUPPORT_OPEN: "bg-gold",
  SUPPORT_CLOSE: "bg-amber-700",
  CHURN: "bg-pink",
  REACTIVATION: "bg-orange"
};

export function JourneyTimeline({ sample }: { sample: JourneySample }) {
  return <ol className="relative ml-2 border-l border-line" aria-label={`Timeline for ${sample.account_key}`}>
    {sample.timeline.map((item, index) => <li className="relative mb-5 ml-5" key={`${item.date}-${item.event}-${index}`}><span className={`absolute -left-[1.62rem] top-1.5 h-3 w-3 rounded-full ring-4 ring-white ${eventStyle[item.event] ?? "bg-slate-400"}`} aria-hidden /><div className="flex flex-wrap items-baseline justify-between gap-2"><p className="text-sm font-semibold">{humanize(item.event)}</p><time className="font-mono text-xs text-muted">{item.date}</time></div>{item.count > 1 && <p className="mt-1 text-xs text-muted">{item.count} events on this date</p>}</li>)}
  </ol>;
}

export function JourneyExplorer({ samples }: { samples: JourneySample[] }) {
  const [account, setAccount] = useState(samples[0]?.account_key ?? "");
  const [outcome, setOutcome] = useState("ALL");
  const [taxonomy, setTaxonomy] = useState("ALL");
  const filtered = useMemo(() => samples.filter((item) => (outcome === "ALL" || item.outcome === outcome) && (taxonomy === "ALL" || item.taxonomy === taxonomy)), [samples, outcome, taxonomy]);
  const selected = filtered.find((item) => item.account_key === account) ?? filtered[0];
  const outcomes = Array.from(new Set(samples.map((item) => item.outcome))).sort();
  const taxonomies = Array.from(new Set(samples.map((item) => item.taxonomy))).sort();
  return <section className="space-y-5">
    <div className="panel grid gap-4 p-4 md:grid-cols-3">
      <label className="text-sm font-medium">Anonymous account<select className="input-control mt-1 w-full" value={selected?.account_key ?? ""} onChange={(event) => setAccount(event.target.value)}>{filtered.map((item) => <option key={item.account_key} value={item.account_key}>{item.profile} · {item.account_key}</option>)}</select></label>
      <label className="text-sm font-medium">Observed outcome<select className="input-control mt-1 w-full" value={outcome} onChange={(event) => setOutcome(event.target.value)}><option value="ALL">All outcomes</option>{outcomes.map((value) => <option key={value}>{value}</option>)}</select></label>
      <label className="text-sm font-medium">Journey taxonomy<select className="input-control mt-1 w-full" value={taxonomy} onChange={(event) => setTaxonomy(event.target.value)}><option value="ALL">All taxonomies</option>{taxonomies.map((value) => <option key={value}>{value}</option>)}</select></label>
    </div>
    {!selected ? <div className="panel p-8 text-center"><p className="font-semibold">No journey matches these filters.</p><button className="button-secondary mt-4" onClick={() => { setOutcome("ALL"); setTaxonomy("ALL"); }}>Reset filters</button></div> : <>
      <div className="grid gap-5 xl:grid-cols-[1.2fr_.8fr]">
        <article className="panel p-5 md:p-6"><div className="mb-6 flex flex-wrap items-start justify-between gap-4"><div><p className="eyebrow">{selected.profile}</p><h3 className="mt-2 font-mono text-xl font-semibold">{selected.account_key}</h3><p className="mt-2 text-sm text-muted">{selected.selection_rationale}</p></div><div className="flex gap-2"><QualityBadge value={selected.quality.confidence} /><StabilityBadge value={selected.quality.stability} /></div></div><JourneyTimeline sample={selected} /></article>
        <aside className="space-y-4"><div className="panel grid grid-cols-2 gap-4 p-5"><div><p className="data-label">Observed outcome</p><p className="mt-2 text-sm font-semibold">{humanize(selected.outcome)}</p></div><div><p className="data-label">Taxonomy</p><p className="mt-2 text-sm font-semibold">{humanize(selected.taxonomy)}</p></div><div><p className="data-label">Usable events</p><p className="mt-2 font-mono text-2xl font-semibold">{selected.event_count}</p></div><div><p className="data-label">Quality coverage</p><p className="mt-2 font-mono text-2xl font-semibold">{formatPercent(selected.quality.coverage)}</p></div><div><p className="data-label">Promotable patterns</p><p className="mt-2 font-mono text-2xl font-semibold">{selected.pattern_count}</p></div><div><p className="data-label">Scope</p><p className="mt-2 text-sm font-semibold">Full observed</p></div></div>{selected.quality.requires_data_review && <LimitationCallout title="Data quality review required">Subscription overlap remains visible for this demo account. The journey is usable with governance, not unrestricted interpretation.</LimitationCallout>}<div className="panel p-5"><p className="data-label">Linked pattern sample</p><ul className="mt-3 space-y-2">{selected.pattern_keys.map((key) => <li key={key} className="flex items-center gap-2 font-mono text-xs text-slate-700"><Circle size={8} fill="currentColor" aria-hidden />{key}</li>)}</ul></div><div className="flex items-center gap-2 text-xs text-muted"><CalendarDays size={14} aria-hidden />{selected.period.start.slice(0, 10)} to {selected.period.end.slice(0, 10)}</div></aside>
      </div>
      <ExplainThis data={selected.explanation} />
    </>}
  </section>;
}
