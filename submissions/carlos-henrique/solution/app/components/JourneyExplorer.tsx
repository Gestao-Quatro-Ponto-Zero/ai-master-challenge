"use client";
import { useMemo, useState } from "react";
import { CalendarDays, Circle } from "lucide-react";
import type { JourneySample } from "@/lib/types";
import { ExplainThis, LimitationCallout, QualityBadge, StabilityBadge } from "@/components/ui";
import { formatDatePtBr, formatPercentPtBr, formatStructuredLabel } from "@/lib/format";

const eventStyle: Record<string, string> = { ACCOUNT: "bg-slate-500", SUBSCRIPTION_START: "bg-blue", SUBSCRIPTION_END: "bg-slate-700", FEATURE: "bg-olive", SUPPORT_OPEN: "bg-gold", SUPPORT_CLOSE: "bg-amber-700", CHURN: "bg-pink", REACTIVATION: "bg-orange" };
const profileLabels: Record<string, string> = { DEMO_A: "Perfil A — sem churn observado", DEMO_B: "Perfil B — churn recorrente", DEMO_C: "Perfil C — reativação e retorno de uso" };
const rationales: Record<string, string> = {
  DEMO_A: "Perfil selecionado para demonstrar baixo uso sem churn observado.",
  DEMO_B: "Perfil selecionado para demonstrar uma jornada histórica com churn recorrente.",
  DEMO_C: "Perfil selecionado para demonstrar reativação e retorno de uso."
};

export function JourneyTimeline({ sample }: { sample: JourneySample }) {
  return <ol className="relative ml-2 border-l border-line" aria-label={`Linha do tempo do ${profileLabels[sample.profile] ?? "perfil anônimo"}`}>{sample.timeline.map((item, index) => <li className="relative mb-5 ml-5" key={`${item.date}-${item.event}-${index}`}><span className={`absolute -left-[1.62rem] top-1.5 h-3 w-3 rounded-full ring-4 ring-white ${eventStyle[item.event] ?? "bg-slate-400"}`} aria-hidden /><div className="flex flex-wrap items-baseline justify-between gap-2"><p className="text-sm font-semibold">{formatStructuredLabel(item.event)}</p><time className="font-mono text-xs text-muted" dateTime={item.date}>{formatDatePtBr(item.date)}</time></div>{item.count > 1 && <p className="mt-1 text-xs text-muted">{item.count} eventos nesta data</p>}</li>)}</ol>;
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
      <label className="text-sm font-medium">Perfil anônimo<select className="input-control mt-1 w-full" value={selected?.account_key ?? ""} onChange={(event) => setAccount(event.target.value)}>{filtered.map((item) => <option key={item.account_key} value={item.account_key}>{profileLabels[item.profile] ?? "Perfil anônimo"}</option>)}</select></label>
      <label className="text-sm font-medium">Desfecho observado<select className="input-control mt-1 w-full" value={outcome} onChange={(event) => setOutcome(event.target.value)}><option value="ALL">Todos os desfechos</option>{outcomes.map((value) => <option key={value} value={value}>{formatStructuredLabel(value)}</option>)}</select></label>
      <label className="text-sm font-medium">Taxonomia da jornada<select className="input-control mt-1 w-full" value={taxonomy} onChange={(event) => setTaxonomy(event.target.value)}><option value="ALL">Todas as taxonomias</option>{taxonomies.map((value) => <option key={value} value={value}>{formatStructuredLabel(value)}</option>)}</select></label>
    </div>
    {!selected ? <div className="panel p-8 text-center"><p className="font-semibold">Nenhuma jornada corresponde a estes filtros.</p><button className="button-secondary mt-4" onClick={() => { setOutcome("ALL"); setTaxonomy("ALL"); }}>Redefinir filtros</button></div> : <>
      <div className="grid gap-5 xl:grid-cols-[1.2fr_.8fr]"><article className="panel p-5 md:p-6"><div className="mb-6 flex flex-wrap items-start justify-between gap-4"><div><p className="eyebrow">{profileLabels[selected.profile] ?? "Perfil anônimo"}</p><h3 className="mt-2 text-xl font-semibold">Conta demonstrativa anonimizada</h3><p className="mt-2 text-sm text-muted">{rationales[selected.profile]}</p></div><div className="flex gap-2"><QualityBadge value={selected.quality.confidence} /><StabilityBadge value={selected.quality.stability} /></div></div><JourneyTimeline sample={selected} /></article>
      <aside className="space-y-4"><div className="panel grid grid-cols-2 gap-4 p-5"><div><p className="data-label">Desfecho observado</p><p className="mt-2 text-sm font-semibold">{formatStructuredLabel(selected.outcome)}</p></div><div><p className="data-label">Taxonomia</p><p className="mt-2 text-sm font-semibold">{formatStructuredLabel(selected.taxonomy)}</p></div><div><p className="data-label">Eventos utilizáveis</p><p className="mt-2 font-mono text-2xl font-semibold">{selected.event_count}</p></div><div><p className="data-label">Cobertura de qualidade</p><p className="mt-2 font-mono text-2xl font-semibold">{formatPercentPtBr(selected.quality.coverage)}</p></div><div><p className="data-label">Padrões promovíveis</p><p className="mt-2 font-mono text-2xl font-semibold">{selected.pattern_count}</p></div><div><p className="data-label">Escopo</p><p className="mt-2 text-sm font-semibold">Jornada completa observada</p></div></div>{selected.quality.requires_data_review && <LimitationCallout title="Revisão de qualidade obrigatória">A sobreposição de assinaturas permanece visível para este perfil. A jornada pode ser usada com governança, não para interpretação irrestrita.</LimitationCallout>}<div className="panel p-5"><p className="data-label">Amostra de padrões vinculados</p><ul className="mt-3 space-y-2">{selected.pattern_keys.map((key, index) => <li key={key} className="flex items-center gap-2 text-xs text-slate-700"><Circle size={8} fill="currentColor" aria-hidden />Padrão vinculado {String(index + 1).padStart(2, "0")}</li>)}</ul></div><div className="flex items-center gap-2 text-xs text-muted"><CalendarDays size={14} aria-hidden />{formatDatePtBr(selected.period.start)} a {formatDatePtBr(selected.period.end)}</div></aside></div>
      <ExplainThis data={{ what_was_observed: `Uma jornada histórica do ${profileLabels[selected.profile] ?? "perfil anônimo"} foi observada antes da data-limite.`, why_it_appears_here: rationales[selected.profile], evidence: { eventos_utilizaveis: selected.event_count, padroes_promoviveis: selected.pattern_count, desfecho: formatStructuredLabel(selected.outcome) }, population: "População principal, com sensibilidade estrita disponível", denominator: "Uma conta demonstrativa dentro da população observacional de 500 contas", quality: `${formatPercentPtBr(selected.quality.coverage)} de cobertura; confiança ${formatStructuredLabel(selected.quality.confidence)}`, stability: formatStructuredLabel(selected.quality.stability), limitations: ["Exemplo delimitado", "Ordenação diária", "Evidência descritiva"], authorized_next_step: "Revisar humanamente a evidência de jornada vinculada.", prohibited_interpretation: "Não inferir previsão, causalidade ou autorização de contato." }} />
    </>}
  </section>;
}
