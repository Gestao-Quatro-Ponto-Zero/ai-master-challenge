"use client";

import { motion } from "motion/react";
import { useMemo, useRef, useState, type KeyboardEvent } from "react";
import type { Deal, PipelineData } from "@/lib/data";
import { firstName, formatCompactUSD, formatDate, formatInt, formatPct } from "@/lib/format";
import { WINDOW_ALERT_DAYS } from "@/lib/scoring";
import {
  agentOptions,
  EMPTY_SELECTION,
  filterDeals,
  summarize,
  teamRows,
  type Selection,
  type Summary,
} from "@/lib/selection";
import { DealRow } from "./DealRow";
import { HowItWorks } from "./HowItWorks";
import { TeamTable } from "./TeamTable";

type Tab = "foco" | "janela" | "higiene" | "prospeccao" | "time" | "como";
type ListTab = "foco" | "janela" | "higiene" | "prospeccao";
const PAGE = 25;

export function Dashboard({ data }: { data: PipelineData }) {
  const [sel, setSel] = useState<Selection>(EMPTY_SELECTION);
  const [tab, setTab] = useState<Tab>("foco");
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);
  const [limit, setLimit] = useState(PAGE);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  const agentRate = useMemo(() => new Map(data.agents.map((a) => [a.name, a.winRate])), [data.agents]);
  const regions = useMemo(() => [...new Set(data.agents.map((a) => a.region))].sort(), [data.agents]);
  const managers = useMemo(
    () => [...new Set(data.agents.filter((a) => !sel.region || a.region === sel.region).map((a) => a.manager))].sort(),
    [data.agents, sel.region],
  );
  const agents = agentOptions(data.agents, sel);

  const scoped = useMemo(() => filterDeals(data.deals, sel), [data.deals, sel]);
  const summary = useMemo(() => summarize(scoped), [scoped]);
  const team = useMemo(() => teamRows(scoped, agentOptions(data.agents, sel)), [scoped, data.agents, sel]);

  const lists: Record<ListTab, Deal[]> = useMemo(
    () => ({
      foco: scoped.filter((d) => d.status === "ativo"),
      janela: scoped.filter((d) => d.status === "ativo" && (d.daysLeft ?? Infinity) <= WINDOW_ALERT_DAYS),
      higiene: scoped.filter((d) => d.status === "zumbi"),
      prospeccao: scoped.filter((d) => d.status === "prospeccao"),
    }),
    [scoped],
  );

  const q = query.trim().toLowerCase();
  const current = tab in lists ? lists[tab as ListTab] : [];
  const visible = q
    ? current.filter((d) => [d.account ?? "", d.id, d.product, d.agent, d.action].some((f) => f.toLowerCase().includes(q)))
    : current;

  function goTo(t: Tab) {
    setTab(t);
    setLimit(PAGE);
    setOpenId(null);
  }

  function update(next: Partial<Selection>) {
    setSel((s) => {
      const merged = { ...s, ...next };
      // Mantém a cascata coerente: trocar região/manager limpa o que deixou de caber.
      if ("region" in next) {
        if (merged.manager && !data.agents.some((a) => a.manager === merged.manager && (!merged.region || a.region === merged.region))) merged.manager = "";
      }
      if (merged.agent && !agentOptions(data.agents, { ...merged, agent: "" }).some((a) => a.name === merged.agent)) merged.agent = "";
      if (next.agent) {
        const a = data.agents.find((x) => x.name === next.agent);
        if (a) Object.assign(merged, { region: a.region, manager: a.manager });
      }
      return merged;
    });
    setLimit(PAGE);
    setOpenId(null);
    if (next.agent && tab === "time") setTab("foco");
  }

  const tabs: { id: Tab; label: string; count?: number }[] = [
    { id: "foco", label: "Foco da semana", count: lists.foco.length },
    { id: "janela", label: "Janela fechando", count: lists.janela.length },
    { id: "higiene", label: "Higiene do pipeline", count: lists.higiene.length },
    { id: "prospeccao", label: "Prospecção", count: lists.prospeccao.length },
    ...(sel.agent ? [] : [{ id: "time" as Tab, label: "Time" }]),
    { id: "como", label: "Como o score funciona" },
  ];

  // Padrão WAI-ARIA de abas: setas, Home e End movem o foco e a seleção.
  function onTabKey(e: KeyboardEvent<HTMLDivElement>) {
    const i = tabs.findIndex((t) => t.id === tab);
    const last = tabs.length - 1;
    const to = { ArrowRight: i === last ? 0 : i + 1, ArrowLeft: i === 0 ? last : i - 1, Home: 0, End: last }[e.key];
    if (to === undefined) return;
    e.preventDefault();
    goTo(tabs[to].id);
    tabRefs.current[tabs[to].id]?.focus();
  }

  const activeFilters = [sel.region, sel.manager, sel.agent].filter(Boolean).length;
  const hello = sel.agent
    ? `Bom dia, ${firstName(sel.agent)}.`
    : sel.manager
      ? `Time de ${sel.manager}.`
      : sel.region
        ? `Região ${sel.region}.`
        : "Visão do time comercial.";

  return (
    <div className="app-glow min-h-screen">
      <div className="mx-auto max-w-6xl px-4 pb-20 pt-6 sm:px-6 sm:pt-8">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="relative flex size-8 items-center justify-center rounded-lg border border-signal/30 bg-signal/10" aria-hidden>
              <span className="size-2 rounded-full bg-signal shadow-[0_0_12px_var(--color-signal)]" />
            </span>
            <div>
              <p className="text-sm font-semibold tracking-tight text-fg">Lead Scorer</p>
              <p className="text-xs text-fg-subtle">Onde focar esta semana</p>
            </div>
          </div>
          <p className="rounded-full border border-line bg-ink-900 px-3 py-1 text-xs text-fg-muted" title="O CRM termina nesta data; ela é usada como 'hoje' para calcular a idade dos deals.">
            Dados do CRM até <span className="text-fg">{formatDate(data.today)}</span>
          </p>
        </header>

        {/* No mobile os filtros ficam recolhidos para a lista aparecer cedo. */}
        <button
          type="button"
          onClick={() => setFiltersOpen((o) => !o)}
          aria-expanded={filtersOpen}
          aria-controls="filtros"
          className="mt-5 flex h-11 w-full items-center justify-between rounded-lg border border-line bg-ink-900 px-3 text-sm text-fg-muted sm:hidden"
        >
          <span>
            Filtros{" "}
            {activeFilters > 0 ? (
              <span className="text-fg">· {sel.agent || sel.manager || sel.region}</span>
            ) : (
              <span className="text-fg-subtle">· todo o time</span>
            )}
          </span>
          <svg aria-hidden className={`size-4 transition-transform ${filtersOpen ? "rotate-180" : ""}`} viewBox="0 0 16 16" fill="none">
            <path d="m4 6 4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>

        <section
          id="filtros"
          aria-label="Filtros"
          className={`${filtersOpen ? "grid" : "hidden"} mt-2 gap-2 sm:mt-8 sm:grid sm:grid-cols-[repeat(3,minmax(0,1fr))_auto]`}
        >
          <Select label="Região" value={sel.region} onChange={(v) => update({ region: v })} options={regions} all="Todas as regiões" />
          <Select label="Manager" value={sel.manager} onChange={(v) => update({ manager: v })} options={managers} all="Todos os managers" />
          <Select label="Vendedor" value={sel.agent} onChange={(v) => update({ agent: v })} options={agents.map((a) => a.name)} all="Todo o time" />
          <button
            type="button"
            onClick={() => update(EMPTY_SELECTION)}
            disabled={activeFilters === 0}
            className="h-11 rounded-lg border border-line px-4 text-sm text-fg-muted transition-colors hover:border-line-strong hover:text-fg disabled:opacity-40"
          >
            Limpar
          </button>
        </section>

        <section className="mt-7 sm:mt-10">
          <h1 className="text-2xl font-semibold tracking-tight text-fg sm:text-3xl">{hello}</h1>
          <p className="mt-2 max-w-2xl text-fg-muted">
            {summary.live > 0 ? (
              <>
                <span className="text-fg">{formatInt(summary.live)} deals vivos</span> de {formatInt(summary.open)} abertos.{" "}
                {summary.windowClosing > 0 && (
                  <>
                    <span className="text-warm">{summary.windowClosing} pedem decisão esta semana</span>.{" "}
                  </>
                )}
                {summary.zombies > 0 && <>{formatInt(summary.zombies)} já passaram do ciclo e só ocupam espaço.</>}
              </>
            ) : summary.open > 0 ? (
              <>
                Nenhum deal vivo no ciclo: {formatInt(summary.zombies)} zumbis e {formatInt(summary.prospects)} em prospecção.
              </>
            ) : (
              <>Nenhum deal aberto nesta seleção.</>
            )}
          </p>

          {/* Mobile: faixa rolável de uma linha (economiza altura); sm+: grade. */}
          <div className="no-scrollbar -mx-4 mt-5 flex snap-x scroll-px-4 gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:overflow-visible sm:px-0 sm:pb-0 lg:grid-cols-4 [&>*]:w-40 [&>*]:shrink-0 [&>*]:snap-start sm:[&>*]:w-auto">
            <Kpi label="Deals vivos" value={formatInt(summary.live)} hint={`de ${formatInt(summary.open)} abertos`} />
            <Kpi
              label="Decidem em 30 dias"
              value={`≈ ${formatInt(Math.round(summary.decide30Count))}`}
              hint={`${formatCompactUSD(summary.decide30Value)} em jogo`}
              accent="text-signal"
            />
            <Kpi label="Janela fechando" value={formatInt(summary.windowClosing)} hint={`≤ ${WINDOW_ALERT_DAYS} dias do limite`} accent="text-warm" />
            <Kpi
              label="Zumbis para limpar"
              value={formatInt(summary.zombies)}
              hint={`${formatPct(summary.zombieShare)} do engajado · ${formatCompactUSD(summary.zombieValue)}`}
              accent="text-risk"
            />
          </div>
        </section>

        <nav className="mt-8 border-b border-line sm:mt-10" aria-label="Seções">
          <div role="tablist" aria-label="Seções do pipeline" onKeyDown={onTabKey} className="tabs-fade -mb-px flex gap-1 overflow-x-auto pr-8 md:pr-0">
            {tabs.map((t) => {
              const selected = tab === t.id;
              return (
                <button
                  key={t.id}
                  ref={(el) => {
                    tabRefs.current[t.id] = el;
                  }}
                  role="tab"
                  id={`tab-${t.id}`}
                  aria-selected={selected}
                  aria-controls="painel"
                  tabIndex={selected ? 0 : -1}
                  onClick={() => goTo(t.id)}
                  className={`relative flex min-h-11 items-center whitespace-nowrap px-3 text-sm transition-colors ${selected ? "text-fg" : "text-fg-subtle hover:text-fg-muted"}`}
                >
                  {t.label}
                  {t.count !== undefined && <span className="tabular ml-1.5 font-mono text-xs text-fg-subtle">{formatInt(t.count)}</span>}
                  {selected && <motion.span layoutId="tab-underline" className="absolute inset-x-2 bottom-0 h-0.5 rounded-full bg-signal" />}
                </button>
              );
            })}
          </div>
        </nav>

        <section className="mt-6" role="tabpanel" id="painel" aria-labelledby={`tab-${tab}`}>
          {tab === "como" ? (
            <HowItWorks curve={data.decideCurve} maxCycle={data.maxCycleDays} globalWinRate={data.globalWinRate} />
          ) : tab === "time" ? (
            <TeamTable rows={team} onPick={(agent) => update({ agent })} />
          ) : (
            <>
              <p className="mb-4 max-w-3xl text-sm text-fg-muted">{INTRO[tab as ListTab](data.maxCycleDays)}</p>
              <div className="mb-3 flex items-center justify-between gap-3">
                <input
                  type="search"
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setLimit(PAGE);
                  }}
                  placeholder="Buscar conta, ação, ID…"
                  title="Busca por conta, produto, vendedor, ação ou ID"
                  aria-label="Buscar deals"
                  className="h-11 w-full max-w-sm rounded-lg border border-line bg-ink-900 px-3 text-sm text-fg placeholder:text-fg-subtle"
                />
                <span className="tabular shrink-0 font-mono text-xs text-fg-subtle">
                  {formatInt(Math.min(limit, visible.length))} de {formatInt(visible.length)}
                </span>
              </div>
              {visible.length === 0 ? (
                <Empty tab={tab as ListTab} filtered={!!q} summary={summary} agent={sel.agent} onGo={goTo} />
              ) : (
                <ol className="space-y-2">
                  {visible.slice(0, limit).map((d) => (
                    <DealRow
                      key={d.id}
                      deal={d}
                      open={openId === d.id}
                      onToggle={() => setOpenId((id) => (id === d.id ? null : d.id))}
                      globalWinRate={data.globalWinRate}
                      agentWinRate={agentRate.get(d.agent) ?? null}
                      showAgent={!sel.agent}
                    />
                  ))}
                </ol>
              )}
              {visible.length > limit && (
                <button
                  type="button"
                  onClick={() => setLimit((l) => l + PAGE)}
                  className="mt-4 h-11 w-full rounded-lg border border-line text-sm text-fg-muted transition-colors hover:border-line-strong hover:text-fg"
                >
                  Mostrar mais {Math.min(PAGE, visible.length - limit)}
                </button>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}

function Select({ label, value, onChange, options, all }: { label: string; value: string; onChange: (v: string) => void; options: string[]; all: string }) {
  return (
    <label className="block">
      <span className="sr-only">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`h-11 w-full rounded-lg border bg-ink-900 pl-3 pr-9 text-sm transition-colors hover:border-line-strong ${value ? "border-signal/40 text-fg" : "border-line text-fg-muted"}`}
      >
        <option value="">{all}</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

function Kpi({ label, value, hint, accent = "text-fg" }: { label: string; value: string; hint: string; accent?: string }) {
  return (
    <div className="rounded-xl border border-line bg-ink-900/80 p-3 sm:p-4">
      <p className="text-xs text-fg-muted">{label}</p>
      <p className={`tabular mt-1 text-2xl font-semibold tracking-tight sm:mt-2 sm:text-3xl ${accent}`}>{value}</p>
      <p className="mt-1 truncate text-xs text-fg-muted sm:whitespace-normal" title={hint}>{hint}</p>
    </div>
  );
}

const INTRO: Record<ListTab, (max: number) => string> = {
  foco: () =>
    "Deals vivos ordenados por score: valor do deal + chance de ele se decidir no próximo mês. No empate, vem primeiro o mais perto do limite. Abra um deal para ver o porquê.",
  janela: (max) =>
    `Deals a ${WINDOW_ALERT_DAYS} dias ou menos do limite de ${max} dias. Nessa idade a chance de decisão já caiu muito e, depois do limite, nenhum deal do histórico fechou. Não adianta mais só reengajar: force o sim ou o não esta semana.`,
  higiene: (max) =>
    `Abertos há mais de ${max} dias, o maior ciclo que já fechou. Confirme com o cliente ou marque como perdido: assim o pipeline volta a dizer a verdade.`,
  prospeccao: () => "Ainda não engajados. Sem tempo de ciclo para medir momento, ordenados só por valor.",
};

function Empty({
  tab,
  filtered,
  summary,
  agent,
  onGo,
}: {
  tab: ListTab;
  filtered: boolean;
  summary: Summary;
  agent: string;
  onGo: (t: Tab) => void;
}) {
  const who = agent ? firstName(agent) : "esta seleção";
  let text: string;
  if (filtered) text = "Nada encontrado para essa busca.";
  else if (tab === "foco") text = `Nenhum deal vivo para ${who}. O trabalho desta semana está em outra aba:`;
  else if (tab === "janela") text = "Nenhum deal com a janela fechando. Bom sinal.";
  else if (tab === "higiene") text = "Nenhum zumbi. Pipeline limpo.";
  else text = `Nenhum deal em prospecção para ${who}: tudo o que está aberto já foi engajado.`;

  const actions: { label: string; to: Tab }[] = [];
  if (!filtered && tab === "foco") {
    if (summary.zombies > 0) actions.push({ label: `Limpar ${formatInt(summary.zombies)} zumbis`, to: "higiene" });
    if (summary.prospects > 0) actions.push({ label: `Engajar ${formatInt(summary.prospects)} em prospecção`, to: "prospeccao" });
  }

  return (
    <div className="rounded-xl border border-dashed border-line px-4 py-10 text-center">
      <p className="text-sm text-fg-muted">{text}</p>
      {actions.length > 0 && (
        <div className="mt-4 flex flex-wrap justify-center gap-2">
          {actions.map((a) => (
            <button
              key={a.to}
              type="button"
              onClick={() => onGo(a.to)}
              className="min-h-11 rounded-lg border border-line-strong bg-ink-850 px-4 text-sm text-fg transition-colors hover:border-signal/50"
            >
              {a.label} →
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
