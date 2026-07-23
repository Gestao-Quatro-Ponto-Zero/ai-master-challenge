"use client";

import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Search, X } from "lucide-react";
import type { WatchlistItem } from "@/lib/types";
import { EvidenceBadge, ExplainThis, LimitationCallout, ProvenancePanel, StatusBadge } from "@/components/ui";
import { formatIntegerPtBr, formatPercentPtBr, formatStructuredLabel } from "@/lib/format";

const PAGE_SIZE = 10;

function buildExplanation(item: WatchlistItem) {
  return {
    what_was_observed: `A regra ${item.rule.id} incluiu este perfil na fila ${formatStructuredLabel(item.queue)}.`,
    why_it_appears_here: "A combinação de sinais históricos atende aos critérios determinísticos da fila e precisa de interpretação humana.",
    evidence: {
      prioridade: formatStructuredLabel(item.priority),
      força_da_evidência: formatStructuredLabel(item.evidence_strength),
      urgência_temporal: formatStructuredLabel(item.temporal_urgency),
      materialidade: formatStructuredLabel(item.materiality),
      confiança_dos_dados: formatStructuredLabel(item.data_confidence),
      faixa_de_mrr_associado: formatStructuredLabel(item.associated_mrr_band),
    },
    population: formatStructuredLabel(item.queue),
    denominator: "Um perfil anônimo nesta demonstração limitada",
    quality: `${formatPercentPtBr(item.quality_coverage)} de cobertura dos dados; confiança ${formatStructuredLabel(item.data_confidence).toLowerCase()}.`,
    stability: formatStructuredLabel(item.evidence_strength),
    limitations: `${formatIntegerPtBr(item.limitation_count)} limitação(ões) registrada(s); a fila não é uma pontuação preditiva.`,
    authorized_next_step: "Revisar o histórico e a qualidade dos dados antes de qualquer decisão operacional.",
    prohibited_interpretation: "Não tratar a inclusão na fila como previsão, causalidade ou autorização para contato automático.",
  };
}

export function WatchlistDetailDrawer({ item, accountLabel, close }: { item: WatchlistItem; accountLabel: string; close: () => void }) {
  const provenance = {
    regra: item.rule.id,
    versão: item.rule.version,
    origem: "Artefatos governados das Fases 3 a 7",
  };

  return <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-labelledby="watchlist-drawer-title">
    <button className="absolute inset-0 bg-ink/50" onClick={close} aria-label="Fechar detalhes da fila de revisão" />
    <aside className="relative h-full w-full max-w-xl overflow-y-auto bg-white p-6 shadow-2xl">
      <div className="flex items-start justify-between gap-4">
        <div><p className="eyebrow">{item.rule.id} · {formatStructuredLabel(item.queue)}</p><h2 id="watchlist-drawer-title" className="mt-2 font-mono text-xl font-semibold">{accountLabel}</h2></div>
        <button onClick={close} className="rounded-lg border border-line p-2" aria-label="Fechar detalhes"><X size={18} /></button>
      </div>
      <div className="mt-5 flex flex-wrap gap-2"><StatusBadge value={item.priority} /><EvidenceBadge value={item.evidence_strength} /><StatusBadge value={item.data_confidence} /></div>
      <dl className="mt-6 grid gap-4 sm:grid-cols-2">
        <div><dt className="data-label">Regra acionada</dt><dd className="mt-1 text-sm font-semibold">{formatStructuredLabel(item.rule.name)}</dd></div>
        <div><dt className="data-label">Responsável humano</dt><dd className="mt-1 text-sm">{formatStructuredLabel(item.human_owner)}</dd></div>
        <div><dt className="data-label">Perfil de qualidade</dt><dd className="mt-1 text-sm">{formatStructuredLabel(item.data_confidence)} · {formatPercentPtBr(item.quality_coverage)} de cobertura</dd></div>
        <div><dt className="data-label">Limitações registradas</dt><dd className="mt-1 font-mono text-lg">{formatIntegerPtBr(item.limitation_count)}</dd></div>
      </dl>
      <div className="mt-6 space-y-3">
        <p className="rounded-xl bg-olive/10 p-3 text-sm font-semibold text-olive">Revisão humana obrigatória: Sim</p>
        <p className="rounded-xl bg-orange/10 p-3 text-sm font-semibold text-orange">Intervenção automática: Não permitida</p>
      </div>
      <div className="mt-6"><ExplainThis data={buildExplanation(item)} /></div>
      <div className="mt-5"><ProvenancePanel value={provenance} /></div>
      <LimitationCallout title="Uso autorizado">Investigar o histórico e validar a qualidade dos dados. Qualquer ação posterior exige decisão humana documentada.</LimitationCallout>
    </aside>
  </div>;
}

export function WatchlistTable({ items }: { items: WatchlistItem[] }) {
  const [query, setQuery] = useState("");
  const [queue, setQueue] = useState("ALL");
  const [category, setCategory] = useState("BEHAVIORAL_INVESTIGATION");
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<WatchlistItem | null>(null);
  const queues = Array.from(new Set(items.map((item) => item.queue))).sort();
  const aliases = useMemo(() => new Map(Array.from(new Set(items.map((item) => item.account_key))).sort().map((accountKey, index) => [accountKey, `Perfil anônimo ${String(index + 1).padStart(3, "0")}`])), [items]);
  const filtered = useMemo(() => items.filter((item) => {
    const accountLabel = aliases.get(item.account_key) ?? "Perfil anônimo";
    return item.category === category && (queue === "ALL" || item.queue === queue) && accountLabel.toLocaleLowerCase("pt-BR").includes(query.toLocaleLowerCase("pt-BR"));
  }).sort((a, b) => a.priority.localeCompare(b.priority) || (aliases.get(a.account_key) ?? "").localeCompare(aliases.get(b.account_key) ?? "", "pt-BR")), [aliases, category, items, query, queue]);
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const visible = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const setFilter = (callback: () => void) => { callback(); setPage(0); };

  return <section className="space-y-4">
    <div className="panel flex flex-wrap gap-3 p-4">
      <div className="inline-flex rounded-lg border border-line p-1" aria-label="Categoria da fila de revisão">
        <button className={`rounded-md px-3 py-2 text-sm font-semibold ${category === "BEHAVIORAL_INVESTIGATION" ? "bg-ink text-white" : "text-muted"}`} onClick={() => setFilter(() => setCategory("BEHAVIORAL_INVESTIGATION"))}>Revisão comportamental</button>
        <button className={`rounded-md px-3 py-2 text-sm font-semibold ${category === "DATA_QUALITY_BACKLOG" ? "bg-ink text-white" : "text-muted"}`} onClick={() => setFilter(() => setCategory("DATA_QUALITY_BACKLOG"))}>Revisão de qualidade dos dados</button>
      </div>
      <label className="relative min-w-64 flex-1"><span className="sr-only">Buscar perfil anônimo</span><Search className="absolute left-3 top-3 text-muted" size={16} aria-hidden /><input className="input-control w-full pl-9" value={query} onChange={(event) => setFilter(() => setQuery(event.target.value))} placeholder="Buscar perfil anônimo" /></label>
      <label><span className="sr-only">Filtrar por fila</span><select className="input-control" value={queue} onChange={(event) => setFilter(() => setQueue(event.target.value))}><option value="ALL">Todas as filas</option>{queues.map((value) => <option key={value} value={value}>{formatStructuredLabel(value)}</option>)}</select></label>
    </div>
    <div className="panel overflow-hidden">
      {visible.length === 0 ? <div className="p-8 text-center"><p className="font-semibold">Nenhum item de revisão corresponde aos filtros.</p><button className="button-secondary mt-4" onClick={() => { setQuery(""); setQueue("ALL"); setPage(0); }}>Limpar filtros</button></div> : <>
        <div className="hidden overflow-x-auto md:block"><table className="w-full border-collapse text-left text-sm"><caption className="sr-only">Itens anônimos da demonstração limitada da fila de revisão</caption><thead className="bg-slate-50 text-xs uppercase tracking-wide text-muted"><tr>{["Perfil", "Fila", "Prioridade", "Evidência", "Urgência", "Materialidade", "Confiança", "Faixa de MRR", "Revisão"].map((label) => <th className="px-4 py-3" key={label} scope="col">{label}</th>)}</tr></thead><tbody>{visible.map((item) => <tr className="border-t border-line hover:bg-slate-50" key={item.watchlist_item_key}><td className="px-4 py-3 font-mono text-xs">{aliases.get(item.account_key)}</td><td className="px-4 py-3">{formatStructuredLabel(item.queue)}</td><td className="px-4 py-3"><StatusBadge value={item.priority} /></td><td className="px-4 py-3">{formatStructuredLabel(item.evidence_strength)}</td><td className="px-4 py-3">{formatStructuredLabel(item.temporal_urgency)}</td><td className="px-4 py-3">{formatStructuredLabel(item.materiality)}</td><td className="px-4 py-3">{formatStructuredLabel(item.data_confidence)}</td><td className="px-4 py-3">{formatStructuredLabel(item.associated_mrr_band)}</td><td className="px-4 py-3"><button className="font-semibold text-blue underline-offset-4 hover:underline" onClick={() => setSelected(item)}>Ver evidência</button></td></tr>)}</tbody></table></div>
        <div className="space-y-3 p-4 md:hidden">{visible.map((item) => <article className="rounded-xl border border-line p-4" key={item.watchlist_item_key}><div className="flex items-start justify-between gap-2"><p className="font-mono text-xs">{aliases.get(item.account_key)}</p><StatusBadge value={item.priority} /></div><p className="mt-3 text-sm font-semibold">{formatStructuredLabel(item.queue)}</p><p className="mt-1 text-xs text-muted">Evidência {formatStructuredLabel(item.evidence_strength).toLowerCase()} · confiança {formatStructuredLabel(item.data_confidence).toLowerCase()}</p><button className="button-secondary mt-4 w-full" onClick={() => setSelected(item)}>Ver evidência</button></article>)}</div>
      </>}
      <div className="flex items-center justify-between border-t border-line px-4 py-3 text-sm"><span>{formatIntegerPtBr(filtered.length)} itens limitados da demonstração</span><div className="flex items-center gap-2"><button className="rounded border border-line p-2 disabled:opacity-30" disabled={page === 0} onClick={() => setPage((value) => Math.max(0, value - 1))} aria-label="Página anterior"><ChevronLeft size={16} /></button><span className="font-mono text-xs">{page + 1} / {pages}</span><button className="rounded border border-line p-2 disabled:opacity-30" disabled={page + 1 >= pages} onClick={() => setPage((value) => Math.min(pages - 1, value + 1))} aria-label="Próxima página"><ChevronRight size={16} /></button></div></div>
    </div>
    {selected && <WatchlistDetailDrawer item={selected} accountLabel={aliases.get(selected.account_key) ?? "Perfil anônimo"} close={() => setSelected(null)} />}
  </section>;
}
