"use client";

import { motion } from "motion/react";
import { useMemo, useState } from "react";
import type { Deal, PipelineData } from "@/lib/data";
import { firstName, formatCompactUSD, formatDate, formatInt, formatPct } from "@/lib/format";
import { WINDOW_ALERT_DAYS } from "@/lib/scoring";
import { agentOptions, EMPTY_SELECTION, filterDeals, summarize, teamRows, type Selection } from "@/lib/selection";
import { DealRow } from "./DealRow";
import { HowItWorks } from "./HowItWorks";
import { TeamTable } from "./TeamTable";

type Tab = "foco" | "janela" | "higiene" | "prospeccao" | "time" | "como";
const PAGE = 25;

export function Dashboard({ data }: { data: PipelineData }) {
  const [sel, setSel] = useState<Selection>(EMPTY_SELECTION);
  const [tab, setTab] = useState<Tab>("foco");
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);
  const [limit, setLimit] = useState(PAGE);

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

  const lists: Record<"foco" | "janela" | "higiene" | "prospeccao", Deal[]> = useMemo(
    () => ({
      foco: scoped.filter((d) => d.status === "ativo"),
      janela: scoped.filter((d) => d.status === "ativo" && (d.daysLeft ?? Infinity) <= WINDOW_ALERT_DAYS),
      higiene: scoped.filter((d) => d.status === "zumbi"),
      prospeccao: scoped.filter((d) => d.status === "prospeccao"),
    }),
    [scoped],
  );

  const q = query.trim().toLowerCase();
  const current = tab in lists ? lists[tab as keyof typeof lists] : [];
  const visible = q
    ? current.filter((d) => [d.account ?? "", d.id, d.product, d.agent].some((f) => f.toLowerCase().includes(q)))
    : current;

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

  const tabs: { id: Tab; label: string; count?: number; hidden?: boolean }[] = [
    { id: "foco", label: "Foco da semana", count: lists.foco.length },
    { id: "janela", label: "Janela fechando", count: lists.janela.length },
    { id: "higiene", label: "Higiene do pipeline", count: lists.higiene.length },
    { id: "prospeccao", label: "Prospecção", count: lists.prospeccao.length },
    { id: "time", label: "Time", hidden: !!sel.agent },
    { id: "como", label: "Como o score funciona" },
  ];

  const hello = sel.agent
    ? `Bom dia, ${firstName(sel.agent)}.`
    : sel.manager
      ? `Time de ${sel.manager}.`
      : sel.region
        ? `Região ${sel.region}.`
        : "Visão do time comercial.";

  return (
    <div className="app-glow min-h-screen">
      <div className="mx-auto max-w-6xl px-4 pb-20 pt-8 sm:px-6">
        <header className="flex flex-wrap items-center justify-between gap-4">
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

        <section aria-label="Filtros" className="mt-8 grid gap-2 sm:grid-cols-[repeat(3,minmax(0,1fr))_auto]">
          <Select label="Região" value={sel.region} onChange={(v) => update({ region: v })} options={regions} all="Todas as regiões" />
          <Select label="Manager" value={sel.manager} onChange={(v) => update({ manager: v })} options={managers} all="Todos os managers" />
          <Select
            label="Vendedor"
            value={sel.agent}
            onChange={(v) => update({ agent: v })}
            options={agents.map((a) => a.name)}
            all="Todo o time"
          />
          <button
            type="button"
            onClick={() => update(EMPTY_SELECTION)}
            disabled={!sel.region && !sel.manager && !sel.agent}
            className="h-11 rounded-lg border border-line px-4 text-sm text-fg-muted transition-colors hover:border-line-strong hover:text-fg disabled:opacity-40"
          >
            Limpar
          </button>
        </section>

        <section className="mt-10">
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
              <>Nenhum deal vivo no ciclo: {formatInt(summary.zombies)} zumbis e {formatInt(summary.prospects)} em prospecção.</>
            ) : (
              <>Nenhum deal aberto nesta seleção.</>
            )}
          </p>

          <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Kpi label="Deals vivos" value={formatInt(summary.live)} hint={`de ${formatInt(summary.open)} abertos`} />
            <Kpi
              label="Decidem em 30 dias"
              value={`≈ ${formatInt(Math.round(summary.decide30Count))}`}
              hint={`${formatCompactUSD(summary.decide30Value)} em jogo`}
              accent="text-signal"
            />
            <Kpi label="Janela fechando" value={formatInt(summary.windowClosing)} hint={`≤ ${WINDOW_ALERT_DAYS} dias para o limite`} accent="text-warm" />
            <Kpi
              label="Zumbis para limpar"
              value={formatInt(summary.zombies)}
              hint={`${formatPct(summary.zombieShare)} do engajado · ${formatCompactUSD(summary.zombieValue)}`}
              accent="text-risk"
            />
          </div>
        </section>

        <nav className="mt-10 border-b border-line" aria-label="Seções">
          <div role="tablist" className="-mb-px flex gap-1 overflow-x-auto">
            {tabs
              .filter((t) => !t.hidden)
              .map((t) => (
                <button
                  key={t.id}
                  role="tab"
                  aria-selected={tab === t.id}
                  onClick={() => {
                    setTab(t.id);
                    setLimit(PAGE);
                    setOpenId(null);
                  }}
                  className={`relative whitespace-nowrap px-3 pb-3 pt-1 text-sm transition-colors ${tab === t.id ? "text-fg" : "text-fg-subtle hover:text-fg-muted"}`}
                >
                  {t.label}
                  {t.count !== undefined && <span className="tabular ml-1.5 font-mono text-xs text-fg-subtle">{formatInt(t.count)}</span>}
                  {tab === t.id && <motion.span layoutId="tab-underline" className="absolute inset-x-2 bottom-0 h-0.5 rounded-full bg-signal" />}
                </button>
              ))}
          </div>
        </nav>

        <section className="mt-6" role="tabpanel">
          {tab === "como" ? (
            <HowItWorks curve={data.decideCurve} maxCycle={data.maxCycleDays} globalWinRate={data.globalWinRate} />
          ) : tab === "time" ? (
            <TeamTable rows={team} onPick={(agent) => update({ agent })} />
          ) : (
            <>
              <TabIntro tab={tab} maxCycle={data.maxCycleDays} />
              <div className="mb-3 flex items-center justify-between gap-3">
                <input
                  type="search"
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setLimit(PAGE);
                  }}
                  placeholder="Buscar conta, produto, vendedor ou ID"
                  aria-label="Buscar deals"
                  className="h-10 w-full max-w-sm rounded-lg border border-line bg-ink-900 px-3 text-sm text-fg placeholder:text-fg-subtle"
                />
                <span className="tabular shrink-0 font-mono text-xs text-fg-subtle">
                  {formatInt(Math.min(limit, visible.length))} de {formatInt(visible.length)}
                </span>
              </div>
              {visible.length === 0 ? (
                <Empty tab={tab} filtered={!!q} />
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
                  className="mt-4 h-10 w-full rounded-lg border border-line text-sm text-fg-muted transition-colors hover:border-line-strong hover:text-fg"
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
    <div className="rounded-xl border border-line bg-ink-900/80 p-4">
      <p className="text-xs text-fg-subtle">{label}</p>
      <p className={`tabular mt-2 text-3xl font-semibold tracking-tight ${accent}`}>{value}</p>
      <p className="mt-1 text-xs text-fg-muted">{hint}</p>
    </div>
  );
}

const INTRO: Record<string, (max: number) => string> = {
  foco: () => "Deals vivos ordenados por score: valor do deal + chance de ele se decidir no próximo mês. Abra um deal para ver o porquê.",
  janela: (max) => `Deals a ${WINDOW_ALERT_DAYS} dias ou menos do limite de ${max} dias. Depois disso, nenhum deal do histórico fechou. Peça a decisão agora.`,
  higiene: (max) => `Abertos há mais de ${max} dias, o maior ciclo que já fechou. Confirme com o cliente ou marque como perdido: assim o pipeline volta a dizer a verdade.`,
  prospeccao: () => "Ainda não engajados. Sem tempo de ciclo para medir momento, ordenados só por valor.",
};

function TabIntro({ tab, maxCycle }: { tab: Tab; maxCycle: number }) {
  return <p className="mb-4 max-w-3xl text-sm text-fg-muted">{INTRO[tab]?.(maxCycle)}</p>;
}

function Empty({ tab, filtered }: { tab: Tab; filtered: boolean }) {
  const text = filtered
    ? "Nada encontrado para essa busca."
    : tab === "janela"
      ? "Nenhum deal com a janela fechando. Bom sinal."
      : tab === "higiene"
        ? "Nenhum zumbi. Pipeline limpo."
        : "Nenhum deal nesta seleção.";
  return <p className="rounded-xl border border-dashed border-line px-4 py-10 text-center text-sm text-fg-subtle">{text}</p>;
}
