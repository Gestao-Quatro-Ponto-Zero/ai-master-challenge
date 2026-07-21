import { AlertTriangle, CheckCircle2, CircleSlash2, DatabaseZap, Info, SearchX } from "lucide-react";
import type { ExplainData, JsonValue, Metric } from "@/lib/types";
import { formatNumber, humanize } from "@/lib/format";

export function SectionHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <header className="mb-7 max-w-4xl"><p className="eyebrow">{eyebrow}</p><h2 className="mt-2 text-3xl font-semibold tracking-tight md:text-4xl">{title}</h2><p className="mt-3 max-w-3xl text-base leading-7 text-muted">{description}</p></header>;
}

export function MetricCard({ metric }: { metric: Metric }) {
  return <article className="panel p-5"><p className="data-label">{metric.label}</p><p className="mt-3 font-mono text-3xl font-semibold tracking-tight">{formatNumber(metric.value)}</p><p className="mt-2 text-sm text-muted">{metric.context}</p></article>;
}

const styles: Record<string, string> = {
  READY_FOR_REVIEW: "border-blue/30 bg-blue/10 text-blue",
  PILOT_ONLY: "border-gold/40 bg-gold/10 text-amber-800",
  UNDERPOWERED: "border-orange/40 bg-orange/10 text-orange-800",
  NOT_FEASIBLE: "border-slate-300 bg-slate-100 text-slate-700",
  UNTESTED: "border-slate-300 bg-white text-slate-700",
  P1: "border-orange/40 bg-orange/10 text-orange-800",
  P2: "border-gold/40 bg-gold/10 text-amber-800",
  P3: "border-blue/30 bg-blue/10 text-blue",
  P4: "border-slate-300 bg-slate-100 text-slate-700",
  HIGH: "border-pink/30 bg-pink/10 text-pink",
  MEDIUM: "border-gold/30 bg-gold/10 text-amber-800",
  LOW: "border-slate-300 bg-slate-100 text-slate-700",
  ROBUST: "border-olive/40 bg-olive/10 text-olive",
  SENSITIVE: "border-gold/40 bg-gold/10 text-amber-800"
};

export function StatusBadge({ value }: { value: string }) {
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-[0.68rem] font-bold uppercase tracking-wide ${styles[value] ?? "border-slate-300 bg-slate-50 text-slate-700"}`}>{humanize(value)}</span>;
}
export const EvidenceBadge = StatusBadge;
export const QualityBadge = StatusBadge;
export const StabilityBadge = StatusBadge;
export const PopulationBadge = StatusBadge;

export function LimitationCallout({ children, title = "Interpretation boundary" }: { children: React.ReactNode; title?: string }) {
  return <aside className="rounded-xl border border-gold/40 bg-amber-50 p-4" role="note"><div className="flex gap-3"><AlertTriangle className="mt-0.5 shrink-0 text-gold" size={19} aria-hidden /><div><p className="text-sm font-semibold text-ink">{title}</p><div className="mt-1 text-sm leading-6 text-slate-700">{children}</div></div></div></aside>;
}

function printable(value: JsonValue | undefined): string {
  if (value === undefined || value === null) return "Not available";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

const explainFields: Array<[keyof ExplainData, string]> = [
  ["what_was_observed", "What was observed"], ["why_it_appears_here", "Why it appears here"],
  ["evidence", "Evidence"], ["population", "Population"], ["denominator", "Denominator"],
  ["quality", "Quality"], ["stability", "Stability"], ["limitations", "Limitations"],
  ["authorized_next_step", "Authorized next step"], ["prohibited_interpretation", "Prohibited interpretation"]
];

export function ExplainThis({ data, label = "Explain this evidence" }: { data: ExplainData; label?: string }) {
  return <details className="rounded-xl border border-line bg-slate-50"><summary className="cursor-pointer list-none px-4 py-3 text-sm font-semibold text-blue">{label}</summary><dl className="grid gap-4 border-t border-line p-4 md:grid-cols-2">{explainFields.map(([key, title]) => <div key={key} className={key === "limitations" || key === "prohibited_interpretation" ? "md:col-span-2" : ""}><dt className="data-label">{title}</dt><dd className="mt-1 whitespace-pre-wrap text-sm leading-6 text-slate-700">{printable(data[key] as JsonValue)}</dd></div>)}</dl></details>;
}

export function ProvenancePanel({ value }: { value: JsonValue }) {
  return <details className="text-sm"><summary className="cursor-pointer font-semibold text-blue">View provenance</summary><pre className="mt-2 max-h-72 overflow-auto rounded-xl bg-ink p-4 text-xs text-slate-100">{printable(value)}</pre></details>;
}

export function GovernanceChecklist({ checks }: { checks: Array<{ label: string; passed: boolean }> }) {
  return <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{checks.map((check) => <div className="panel flex items-center gap-3 p-4" key={check.label}>{check.passed ? <CheckCircle2 className="text-olive" size={21} aria-hidden /> : <CircleSlash2 className="text-orange" size={21} aria-hidden />}<span className="text-sm font-medium">{check.label}</span></div>)}</div>;
}

export function EmptyState({ title, message }: { title: string; message: string }) {
  return <div className="panel flex min-h-64 flex-col items-center justify-center p-8 text-center" role="status"><SearchX className="text-muted" size={36} aria-hidden /><h2 className="mt-4 text-xl font-semibold">{title}</h2><p className="mt-2 max-w-md text-sm text-muted">{message}</p></div>;
}

export function ErrorState({ title, message, action }: { title: string; message: string; action?: () => void }) {
  return <div className="panel flex min-h-64 flex-col items-center justify-center border-orange/30 p-8 text-center" role="alert"><DatabaseZap className="text-orange" size={36} aria-hidden /><h2 className="mt-4 text-xl font-semibold">{title}</h2><p className="mt-2 max-w-md text-sm text-muted">{message}</p>{action && <button className="button-primary mt-5" onClick={action}>Try again</button>}</div>;
}

export function DataFreshness({ cutoff }: { cutoff: string }) {
  return <div className="inline-flex items-center gap-2 text-xs text-muted"><Info size={14} aria-hidden /><span>Historical data through Dec 31, 2024 · fixed local snapshot</span><span className="sr-only">Machine cutoff {cutoff}</span></div>;
}
