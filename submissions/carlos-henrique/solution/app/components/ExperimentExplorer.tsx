"use client";

import { useState } from "react";
import { ArrowRight, X } from "lucide-react";
import type { Experiment } from "@/lib/types";
import { ExplainThis, LimitationCallout, StatusBadge } from "@/components/ui";
import { formatIntegerPtBr, formatPercentPtBr, formatStructuredLabel } from "@/lib/format";

function SampleSizeComparison({ available, required }: { available: number; required: number }) {
  const maximum = Math.max(1, available, required);
  return <div>
    <div className="flex justify-between text-xs text-muted"><span>Disponível: {formatIntegerPtBr(available)}</span><span>Necessário: {formatIntegerPtBr(required)}</span></div>
    <div className="mt-2 h-3 overflow-hidden rounded-full bg-slate-100"><div className="h-full bg-blue" style={{ width: `${Math.min(100, (available / maximum) * 100)}%` }} /></div>
    <div className="mt-1 h-1 bg-gold" style={{ width: `${Math.min(100, (required / maximum) * 100)}%` }} />
    <p className="sr-only">Amostra disponível: {formatIntegerPtBr(available)}; amostra necessária: {formatIntegerPtBr(required)}</p>
  </div>;
}

export function ExperimentCard({ experiment, open }: { experiment: Experiment; open: () => void }) {
  return <article className="panel flex flex-col p-5">
    <div className="flex items-start justify-between gap-3"><div><p className="eyebrow">{experiment.experiment_id}</p><h3 className="mt-2 text-lg font-semibold">{formatStructuredLabel(experiment.name)}</h3></div><StatusBadge value={experiment.status} /></div>
    <p className="mt-3 text-sm text-muted">Origem: {formatStructuredLabel(experiment.queue)}</p>
    <div className="mt-5"><SampleSizeComparison available={experiment.eligible_accounts} required={experiment.required_sample} /></div>
    <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
      <div><dt className="data-label">Métrica primária</dt><dd className="mt-1">{formatStructuredLabel(experiment.primary_metric)}</dd></div>
      <div><dt className="data-label">Status causal</dt><dd className="mt-1"><StatusBadge value={experiment.causal_status} /></dd></div>
      <div><dt className="data-label">Poder estatístico</dt><dd className="mt-1 font-mono">{formatPercentPtBr(experiment.power)}</dd></div>
      <div><dt className="data-label">Acompanhamento</dt><dd className="mt-1 font-mono">{formatIntegerPtBr(experiment.follow_up_days)} dias</dd></div>
    </dl>
    <button className="button-secondary mt-6 w-full" onClick={open} aria-label={`Abrir detalhes do experimento ${experiment.experiment_id}`}>Abrir detalhes do experimento <ArrowRight className="ml-2" size={16} /></button>
  </article>;
}

export function ExperimentDetail({ experiment, close }: { experiment: Experiment; close: () => void }) {
  const flow = ["Observação", "Hipótese", "Intervenção candidata", "Desenho", "Elegibilidade", "Métrica primária", "Tamanho da amostra", "Controles de governança"];
  const guardrailCount = Array.isArray(experiment.guardrails) ? experiment.guardrails.length : 0;
  const stoppingRuleCount = Array.isArray(experiment.stopping_rules) ? experiment.stopping_rules.length : 0;
  const explanation = {
    what_was_observed: `O desenho ${experiment.experiment_id} foi proposto a partir de evidência histórica da fila ${formatStructuredLabel(experiment.queue)}.`,
    why_it_appears_here: "A hipótese foi registrada para avaliação metodológica, sem execução e sem resultado causal.",
    evidence: {
      métrica_primária: formatStructuredLabel(experiment.primary_metric),
      efeito_mínimo_detectável: formatPercentPtBr(Number(experiment.mde)),
      poder_estatístico: formatPercentPtBr(experiment.power),
      desenho: formatStructuredLabel(experiment.design),
    },
    population: formatStructuredLabel(experiment.queue),
    denominator: `${formatIntegerPtBr(experiment.eligible_accounts)} contas elegíveis no recorte histórico`,
    quality: "Baseline histórico auditado; não constitui grupo de controle.",
    stability: formatStructuredLabel(experiment.status),
    limitations: "Nenhum experimento foi executado e nenhum resultado está disponível.",
    authorized_next_step: "Submeter o desenho à revisão metodológica, ética e operacional.",
    prohibited_interpretation: "Não descrever o desenho como executado, eficaz ou causal.",
  };

  return <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-labelledby="experiment-title">
    <button className="absolute inset-0 bg-ink/50" onClick={close} aria-label="Fechar detalhes do experimento" />
    <article className="relative h-full w-full max-w-3xl overflow-y-auto bg-white p-6 md:p-8">
      <div className="flex items-start justify-between gap-3"><div><p className="eyebrow">{experiment.experiment_id} · Hipótese não testada</p><h2 id="experiment-title" className="mt-2 text-2xl font-semibold">{formatStructuredLabel(experiment.name)}</h2></div><button className="rounded-lg border border-line p-2" onClick={close} aria-label="Fechar detalhes"><X size={18} /></button></div>
      <p className="mt-4 rounded-xl bg-blue/10 p-4 text-sm font-semibold text-blue">O desenho permanece disponível para revisão; nenhuma intervenção foi executada.</p>
      <ol className="mt-6 flex flex-wrap items-center gap-2 text-xs">{flow.map((step, index) => <li className="flex items-center gap-2" key={step}><span className="rounded-full border border-line bg-slate-50 px-3 py-2 font-semibold">{step}</span>{index < flow.length - 1 && <ArrowRight size={13} className="text-muted" aria-hidden />}</li>)}</ol>
      <div className="mt-7 grid gap-5 sm:grid-cols-2"><div className="panel p-5"><p className="data-label">Amostra disponível</p><p className="mt-2 font-mono text-3xl font-semibold">{formatIntegerPtBr(experiment.eligible_accounts)}</p></div><div className="panel p-5"><p className="data-label">Amostra ajustada necessária</p><p className="mt-2 font-mono text-3xl font-semibold">{formatIntegerPtBr(experiment.required_sample)}</p></div></div>
      <div className="mt-5"><SampleSizeComparison available={experiment.eligible_accounts} required={experiment.required_sample} /></div>
      <dl className="mt-7 grid gap-4 sm:grid-cols-2">
        <div><dt className="data-label">Unidade de randomização</dt><dd className="mt-1 text-sm">{formatStructuredLabel(String(experiment.unit_of_randomization))}</dd></div>
        <div><dt className="data-label">Atribuição simulada</dt><dd className="mt-1 text-sm">Sim · somente para validação do desenho</dd></div>
        <div><dt className="data-label">Alertas de balanceamento</dt><dd className="mt-1 font-mono text-lg">{formatIntegerPtBr(Number(experiment.balance_warnings))}</dd></div>
        <div><dt className="data-label">Déficit amostral</dt><dd className="mt-1 font-mono text-lg">{formatIntegerPtBr(Number(experiment.sample_gap))}</dd></div>
        <div><dt className="data-label">Risco de contaminação</dt><dd className="mt-1 text-sm">{formatStructuredLabel(experiment.contamination_risk)}</dd></div>
        <div><dt className="data-label">Risco ético</dt><dd className="mt-1 text-sm">{formatStructuredLabel(experiment.ethical_risk)}</dd></div>
      </dl>
      <div className="mt-7"><ExplainThis data={explanation} /></div>
      <section className="mt-7"><h3 className="text-lg font-semibold">Plano de análise estatística</h3><dl className="mt-3 grid gap-4 rounded-xl border border-line bg-slate-50 p-4 sm:grid-cols-2"><div><dt className="data-label">Desenho</dt><dd className="mt-1 text-sm">{formatStructuredLabel(experiment.design)}</dd></div><div><dt className="data-label">Métrica primária</dt><dd className="mt-1 text-sm">{formatStructuredLabel(experiment.primary_metric)}</dd></div><div><dt className="data-label">Efeito mínimo detectável</dt><dd className="mt-1 font-mono text-sm">{formatPercentPtBr(Number(experiment.mde))}</dd></div><div><dt className="data-label">Acompanhamento</dt><dd className="mt-1 font-mono text-sm">{formatIntegerPtBr(experiment.follow_up_days)} dias</dd></div></dl><p className="mt-3 text-sm text-muted">A especificação completa permanece preservada no artefato governado para revisão técnica.</p></section>
      <section className="mt-7"><h3 className="text-lg font-semibold">Salvaguardas e regras de interrupção</h3><p className="mt-2 text-sm text-muted">{formatIntegerPtBr(guardrailCount)} salvaguardas · {formatIntegerPtBr(stoppingRuleCount)} regras de interrupção · apenas especificação</p></section>
      <LimitationCallout title="Limite de execução">Nenhum experimento foi executado. Nenhum cliente foi contatado, atribuído a grupo ou exposto a uma intervenção.</LimitationCallout>
    </article>
  </div>;
}

export function ExperimentExplorer({ registry, details }: { registry: Experiment[]; details: Experiment[] }) {
  const [selectedId, setSelectedId] = useState("");
  const selected = details.find((item) => item.experiment_id === selectedId);
  return <><div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">{registry.map((experiment) => <ExperimentCard key={experiment.experiment_id} experiment={experiment} open={() => setSelectedId(experiment.experiment_id)} />)}</div>{selected && <ExperimentDetail experiment={selected} close={() => setSelectedId("")} />}</>;
}
