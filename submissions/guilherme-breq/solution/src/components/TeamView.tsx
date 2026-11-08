"use client";

import { useMemo, useRef, useState, type KeyboardEvent } from "react";
import type { Deal, PipelineData } from "@/lib/data";
import { formatCompactUSD, formatDate, formatInt } from "@/lib/format";
import { ageNote, buildQueue, modalPattern, nextStep, textPattern, type Step, type Window } from "@/lib/playbook";
import { decisionWindow, formatUSD, WINDOW_ALERT_DAYS } from "@/lib/scoring";
import { agentOptions, filterDeals, summarize, type Selection } from "@/lib/selection";
import { CycleMap } from "./CycleMap";
import { Brand, Empty, fold, Select } from "./ui";

type TabId = "Ligar" | "Decidir" | "Reengajar" | "Preparar" | "Lote" | "Encerrar" | "Prospecção";
type Row = { deal: Deal; step: Step };
const PAGE = 25;
const FIRST = 10;

const TAB_LABEL: Record<TabId, string> = {
  Ligar: "Ligar",
  Decidir: "Forçar sim ou não",
  Reengajar: "Reengajar",
  Preparar: "Preparar proposta",
  Lote: "Em lote",
  Encerrar: "Encerrar zumbis",
  Prospecção: "Prospecção",
};

const INTRO: Record<TabId, (max: number, w: Window) => string> = {
  Ligar: (_m, w) => `Ticket médio ou alto dentro da fase de decisão (dias ${w.start} a ${w.end}), quando a ação do vendedor mais pesa. Ordenados por score: valor até 60 + momento até 40.`,
  Decidir: (m) => `A ${WINDOW_ALERT_DAYS} dias ou menos do limite de ${m}. Depois dele, nenhum deal do histórico fechou: é forçar o sim ou o não esta semana.`,
  Reengajar: (_m, w) => `Já saíram da fase de decisão (depois do dia ${w.end}) e ainda não estão na janela final. A chance de decisão cai a cada semana.`,
  Preparar: (_m, w) => `Ainda não chegaram à fase de decisão (antes do dia ${w.start}). Deixe a proposta pronta para quando entrarem.`,
  Lote: () => "Ticket baixo: a ligação custa mais que o deal. Um e-mail resolve, sem ligação.",
  Encerrar: (m) => `Abertos há mais de ${m} dias, o maior ciclo que já fechou. Confirme com o cliente ou marque como perdido: assim o pipeline volta a dizer a verdade.`,
  Prospecção: () => "Ainda não engajados: sem tempo de ciclo para medir o momento, ordenados só por valor.",
};

/** Visão do time (gerente, RevOps): o mapa do ciclo no topo e as pilhas de trabalho em tabela abaixo. */
export function TeamView({
  data,
  sel,
  update,
  onPickAgent,
  onHome,
  onHow,
}: {
  data: PipelineData;
  sel: Selection;
  update: (next: Partial<Selection>) => void;
  onPickAgent: (agent: string) => void;
  onHome: () => void;
  onHow: () => void;
}) {
  const win = useMemo(() => decisionWindow(data.decideCurve), [data.decideCurve]);
  const regions = useMemo(() => [...new Set(data.agents.map((a) => a.region))].sort(), [data.agents]);
  const managers = useMemo(
    () => [...new Set(data.agents.filter((a) => !sel.region || a.region === sel.region).map((a) => a.manager))].sort(),
    [data.agents, sel.region],
  );
  const agents = agentOptions(data.agents, sel);
  const scoped = useMemo(() => filterDeals(data.deals, sel), [data.deals, sel]);
  const summary = useMemo(() => summarize(scoped), [scoped]);
  const products = useMemo(() => {
    const m = new Map<string, number>();
    for (const d of data.deals) if (d.price > 0) m.set(d.product, d.price);
    return [...m].map(([name, price]) => ({ name, price })).sort((a, b) => b.price - a.price);
  }, [data.deals]);

  const queue = useMemo(() => buildQueue(scoped, win), [scoped, win]);
  const piles: Record<TabId, Row[]> = useMemo(() => {
    const by = (verb: string) => queue.work.filter((i) => i.step.verb === verb).map((i) => ({ deal: i.deal, step: i.step }));
    const plain = (ds: Deal[]): Row[] => ds.map((deal) => ({ deal, step: nextStep(deal, win) }));
    return {
      Ligar: by("Ligar"),
      Decidir: by("Decidir"),
      Reengajar: by("Reengajar"),
      Preparar: by("Preparar"),
      Lote: plain(queue.lote),
      Encerrar: plain(queue.zombies),
      Prospecção: plain(queue.prospects),
    };
  }, [queue, win]);

  const tabs = (Object.keys(TAB_LABEL) as TabId[]).filter((t) => t !== "Prospecção" || piles.Prospecção.length > 0);
  const [tab, setTab] = useState<TabId>("Ligar");
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(FIRST);
  const tabRefs = useRef<Partial<Record<TabId, HTMLButtonElement | null>>>({});

  const rows = piles[tab];
  // A ação que se repete na pilha já está na introdução; a linha de apoio só aparece nas exceções.
  const common = useMemo(() => modalPattern(rows.map((r) => r.step.text)), [rows]);
  const q = fold(query.trim());
  const visible = q ? rows.filter((r) => [r.deal.account ?? "", r.deal.id, r.deal.product, r.deal.agent, r.step.text].some((f) => fold(f).includes(q))) : rows;
  const highlight = useMemo(() => new Set(tab === "Encerrar" || tab === "Prospecção" ? [] : piles[tab].map((r) => r.deal.id)), [tab, piles]);

  function goTo(t: TabId) {
    setTab(t);
    setLimit(FIRST);
  }

  function onTabKey(e: KeyboardEvent<HTMLDivElement>) {
    const i = tabs.indexOf(tab);
    const last = tabs.length - 1;
    const to = { ArrowRight: i === last ? 0 : i + 1, ArrowLeft: i === 0 ? last : i - 1, Home: 0, End: last }[e.key];
    if (to === undefined) return;
    e.preventDefault();
    goTo(tabs[to]);
    tabRefs.current[tabs[to]]?.focus();
  }

  const scopeName = sel.manager ? `Time de ${sel.manager}` : sel.region ? `Região ${sel.region}` : "Time inteiro";
  const inWindow = scoped.filter((d) => d.status === "ativo" && d.ageDays !== null && d.ageDays >= win.start && d.ageDays <= win.end).length;
  const mapDesc =
    `${scopeName}: ${formatInt(summary.live)} deals vivos, com idade entre 0 e ${data.maxCycleDays} dias. ${formatInt(inWindow)} estão na fase de decisão (dias ${win.start} a ${win.end}) e ${formatInt(summary.windowClosing)} nos últimos ${WINDOW_ALERT_DAYS} dias. ` +
    `Depois do dia ${data.maxCycleDays}: ${formatInt(summary.zombies)} zumbis, ${formatCompactUSD(summary.zombieValue)} em valor de tabela. As pilhas abaixo trazem cada deal.`;

  return (
    <div className="mx-auto max-w-[1360px] px-4 pb-20 sm:px-10">
      <header className="flex flex-wrap items-center justify-between gap-x-6 gap-y-1 border-b border-line py-2">
        <Brand />
        <div className="flex flex-wrap items-center gap-x-4">
          <button type="button" onClick={onHome} className="min-h-11 text-sm font-semibold text-fg-2 underline-offset-4 hover:text-gold-hi hover:underline">
            Abrir como vendedor
          </button>
          <button type="button" onClick={onHow} className="min-h-11 text-sm font-semibold text-fg-2 underline-offset-4 hover:text-gold-hi hover:underline">
            Como o score funciona
          </button>
          <span className="text-[13px] text-fg-3">CRM até {formatDate(data.today)}</span>
        </div>
      </header>

      <nav aria-label="Escopo" className="mt-4 grid gap-2 min-[640px]:grid-cols-2 min-[1000px]:grid-cols-[auto_minmax(0,1fr)_minmax(0,1fr)] min-[1000px]:items-center min-[1000px]:gap-3">
        <div className="no-scrollbar -mx-4 flex gap-1 overflow-x-auto px-4 min-[640px]:col-span-2 sm:mx-0 sm:px-0 min-[1000px]:col-span-1">
          {[
            { label: "Time inteiro", on: !sel.region && !sel.manager, go: () => update({ region: "", manager: "" }) },
            ...regions.map((r) => ({ label: r, on: sel.region === r && !sel.manager, go: () => update({ region: r, manager: "" }) })),
          ].map((b) => (
            <button
              key={b.label}
              type="button"
              aria-pressed={b.on}
              onClick={b.go}
              className={`min-h-11 shrink-0 rounded-lg border px-4 text-sm font-semibold transition-colors ${b.on ? "border-fg bg-fg text-navy-deep" : "border-line text-fg-2 hover:border-line-strong hover:text-fg"}`}
            >
              {b.label}
            </button>
          ))}
        </div>
        <Select label="Manager" value={sel.manager} onChange={(v) => update({ manager: v })} options={managers} all="Todos os managers" />
        <Select label="Abrir a fila de um vendedor" value="" onChange={(v) => v && onPickAgent(v)} options={agents.map((a) => a.name)} all="Abrir a fila de…" />
      </nav>

      <section className="grid items-end gap-6 pb-6 pt-8 min-[900px]:grid-cols-[minmax(0,1fr)_auto] min-[900px]:gap-10 min-[900px]:pt-10">
        <div>
          <p className="mb-3 text-sm font-semibold text-gold-hi">{scopeName}</p>
          <h1 id="tela-titulo" tabIndex={-1} className="max-w-[22ch] text-[30px] font-light leading-[1.08] tracking-[-0.025em] text-fg outline-none min-[900px]:text-[44px]">
            Não dá para prever quem ganha. <b className="font-bold text-gold-hi">Dá para prever quando se decide.</b>
          </h1>
          <p className="mt-3 hidden max-w-[64ch] text-sm text-fg-2 min-[900px]:block">
            Em 5 datas passadas, vendedor, produto, setor e idade não separaram ganho de perda (AUC 0,50). Em 3 datas, a idade do deal previu quando ele se decide (AUC média 0,65, sinal modesto e
            instável): o pico é o dia {win.peakAge} e, depois do dia {data.maxCycleDays}, nenhum deal do histórico fechou. Cada ponto abaixo é um deal vivo, na idade em que está hoje.
          </p>
          <p className="mt-3 text-sm text-fg-2 min-[900px]:hidden">
            AUC 0,50 para prever quem ganha e 0,65 para prever quando se decide. Depois do dia {data.maxCycleDays}, nenhum deal do histórico fechou.{" "}
            <button type="button" onClick={onHow} className="font-semibold text-gold-hi underline underline-offset-4">
              Como o score funciona
            </button>
          </p>
        </div>
        <dl className="flex overflow-hidden rounded-xl border border-line">
          <Reading label="Deals vivos" value={formatInt(summary.live)} />
          <Reading label="Decidem em 30 dias" value={`≈ ${formatInt(Math.round(summary.decide30Count))}`} tone="text-gold-hi" />
          <Reading label="Zumbis" value={formatInt(summary.zombies)} tone="text-risk" />
        </dl>
      </section>

      {scoped.length === 0 ? (
        <Empty title="Nenhum deal aberto nesta seleção">Escolha outra região ou outro manager.</Empty>
      ) : (
        <>
          <section aria-labelledby="mapa-titulo" className="rounded-2xl border border-line bg-navy p-3 min-[900px]:p-5 min-[900px]:pb-3">
            <div className="mb-2 flex flex-wrap items-baseline justify-between gap-x-4">
              <h2 id="mapa-titulo" className="text-sm font-semibold">
                Pipeline no relógio do ciclo · idade do deal × produto
              </h2>
              <p className="hidden gap-4 text-[13px] text-fg-2 min-[900px]:flex">
                <Key color="bg-gold-hi">na pilha selecionada</Key>
                <Key color="bg-fg-3">outros deals vivos</Key>
                <Key color="bg-risk">zumbis, depois do dia {data.maxCycleDays}</Key>
              </p>
            </div>
            <CycleMap
              deals={scoped}
              products={products}
              win={win}
              maxCycle={data.maxCycleDays}
              peakAge={win.peakAge}
              curve={data.decideCurve}
              highlight={highlight}
              describedBy="mapa-desc"
              label={`Mapa do ciclo: ${formatInt(summary.live)} deals vivos por idade e produto, com a fase de decisão entre os dias ${win.start} e ${win.end} e o limite no dia ${data.maxCycleDays}.`}
            />
            <p id="mapa-desc" className="sr-only min-[900px]:not-sr-only min-[900px]:mx-1 min-[900px]:mb-2 min-[900px]:mt-2 min-[900px]:text-[13px] min-[900px]:text-fg-3">
              {mapDesc}
            </p>
          </section>

          <div role="tablist" aria-label="Pilhas de trabalho" onKeyDown={onTabKey} className="no-scrollbar -mx-4 mt-7 flex gap-1.5 overflow-x-auto px-4 sm:mx-0 sm:px-0">
            {tabs.map((t) => {
              const on = tab === t;
              const risk = t === "Encerrar";
              return (
                <button
                  key={t}
                  ref={(el) => {
                    tabRefs.current[t] = el;
                  }}
                  role="tab"
                  id={`tab-${t}`}
                  aria-selected={on}
                  aria-controls="painel-time"
                  tabIndex={on ? 0 : -1}
                  onClick={() => goTo(t)}
                  className={`flex min-h-16 min-w-[7.5rem] shrink-0 flex-col items-start justify-center gap-0.5 rounded-xl border px-4 py-2 text-left text-[13px] font-medium transition-colors min-[900px]:min-w-36 ${
                    on ? "border-fg bg-fg text-navy-deep" : "border-line text-fg-2 hover:border-line-strong"
                  }`}
                >
                  <b className={`text-[22px] font-bold leading-none ${on ? "text-navy-deep" : risk ? "text-risk" : "text-fg"}`}>{formatInt(piles[t].length)}</b>
                  {TAB_LABEL[t]}
                </button>
              );
            })}
          </div>

          <section role="tabpanel" id="painel-time" aria-labelledby={`tab-${tab}`} className="mt-5">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <p className="max-w-[80ch] text-sm text-fg-2">
                <b className="text-fg">{TAB_LABEL[tab]}:</b> {INTRO[tab](data.maxCycleDays, win)}
              </p>
              <label className="block w-full sm:w-64">
                <span className="sr-only">Buscar nesta pilha</span>
                <input
                  type="search"
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setLimit(FIRST);
                  }}
                  placeholder="Buscar conta, vendedor, ID…"
                  className="h-11 w-full rounded-lg border border-line-strong bg-navy px-3 text-sm text-fg placeholder:text-fg-3"
                />
              </label>
            </div>
            <p className="mb-2 text-[13px] text-fg-3" role="status" aria-live="polite">
              {formatInt(Math.min(limit, visible.length))} de {formatInt(visible.length)}
            </p>

            {visible.length === 0 ? (
              <Empty title={q ? "Nada encontrado para essa busca." : "Nada nesta pilha."}>{q ? "Limpe a busca para ver a pilha inteira." : "Nenhum deal nesta seleção cai aqui."}</Empty>
            ) : (
              <>
                <DealTable rows={visible.slice(0, limit)} win={win} common={common} maxCycle={data.maxCycleDays} onPickAgent={onPickAgent} />
                <DealCards rows={visible.slice(0, limit)} win={win} common={common} onPickAgent={onPickAgent} />
              </>
            )}
            {visible.length > limit && (
              <button
                type="button"
                onClick={() => setLimit((l) => l + PAGE)}
                className="mt-4 min-h-11 w-full rounded-lg border border-line-strong text-sm font-semibold text-fg-2 transition-colors hover:border-gold-hi hover:text-gold-hi"
              >
                Mostrar mais {Math.min(PAGE, visible.length - limit)}
              </button>
            )}
          </section>
        </>
      )}
    </div>
  );
}

function Reading({ label, value, tone = "text-fg" }: { label: string; value: string; tone?: string }) {
  return (
    <div className="flex min-w-0 flex-1 flex-col justify-between gap-1 border-l border-line px-3 py-3 first:border-l-0 min-[900px]:min-w-44 min-[900px]:px-5">
      <dt className="text-[13px] text-fg-2">{label}</dt>
      <dd className={`mt-1 text-2xl font-semibold leading-none tracking-tight min-[900px]:text-[30px] ${tone}`}>{value}</dd>
    </div>
  );
}

function Key({ color, children }: { color: string; children: React.ReactNode }) {
  return (
    <span className="flex items-center gap-1.5">
      <i className={`size-2 rounded-full ${color}`} aria-hidden />
      {children}
    </span>
  );
}

const agePosition = (age: number, max: number) => `${Math.min(100, (age / max) * 100)}%`;

type PeakWindow = Window & { peakAge: number };

function DealTable({ rows, win, common, maxCycle, onPickAgent }: { rows: Row[]; win: PeakWindow; common: string; maxCycle: number; onPickAgent: (a: string) => void }) {
  return (
    <table className="hidden w-full border-collapse text-left min-[900px]:table">
      <thead>
        <tr className="border-b border-line-strong text-[13px] font-semibold uppercase tracking-[0.12em] text-fg-3">
          <th className="px-3.5 py-2.5 font-semibold">Score</th>
          <th className="px-3.5 py-2.5 font-semibold">Deal</th>
          <th className="px-3.5 py-2.5 text-right font-semibold">Valor</th>
          <th className="px-3.5 py-2.5 font-semibold">Idade no ciclo</th>
          <th className="px-3.5 py-2.5 font-semibold">Vendedor</th>
          <th className="px-3.5 py-2.5 font-semibold">Próximo passo</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(({ deal: d, step }) => (
          <tr key={d.id} className="border-b border-line text-sm text-fg-2 hover:bg-fg/[0.03]">
            <td className="w-16 px-3.5 py-3 text-lg font-bold text-gold-hi">{d.status === "ativo" ? d.score : "—"}</td>
            <td className="px-3.5 py-3">
              <b className="font-semibold text-fg">{d.account ?? d.product}</b>
              <small className="block text-[13px] text-fg-3">
                {d.account ? d.product : "conta não vinculada"} · {d.id}
              </small>
            </td>
            <td className="px-3.5 py-3 text-right">{formatUSD(d.price)}</td>
            <td className="px-3.5 py-3">
              {d.ageDays === null ? (
                <span className="text-fg-3">sem engajamento</span>
              ) : (
                <span className="inline-flex items-center gap-2.5">
                  <span className="relative h-1 w-28 rounded-full bg-line-strong" aria-hidden>
                    <i className="absolute -top-px h-1.5 rounded-full bg-gold/60" style={{ left: agePosition(win.start, maxCycle), width: `${((win.end - win.start) / maxCycle) * 100}%` }} />
                    <i className="absolute -top-[3px] h-2.5 w-0.5 bg-fg" style={{ left: agePosition(d.ageDays, maxCycle) }} />
                  </span>
                  <span className="text-[13px]">dia {d.ageDays}</span>
                </span>
              )}
            </td>
            <td className="px-3.5 py-3">
              <button type="button" onClick={() => onPickAgent(d.agent)} className="min-h-11 text-left underline-offset-4 hover:text-gold-hi hover:underline">
                {d.agent}
              </button>
            </td>
            <td className="px-3.5 py-3">
              <span className="block font-semibold text-fg">{ageNote(d, step, win)}</span>
              {textPattern(step.text) !== common && <small className="mt-0.5 block text-[13px] text-fg-3">{step.text}</small>}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function DealCards({ rows, win, common, onPickAgent }: { rows: Row[]; win: PeakWindow; common: string; onPickAgent: (a: string) => void }) {
  return (
    <ul className="space-y-2 min-[900px]:hidden">
      {rows.map(({ deal: d, step }) => (
        <li key={d.id} className="rounded-xl border border-line bg-navy p-3.5">
          <div className="flex items-baseline justify-between gap-3">
            <p className="min-w-0 truncate font-bold text-fg">{d.account ?? d.product}</p>
            <p className="shrink-0 text-sm text-fg-2">{formatUSD(d.price)}</p>
          </div>
          <p className="mt-0.5 text-[13px] text-fg-3">
            {d.account ? d.product : "conta não vinculada"} · {d.id}
            {d.status === "ativo" && ` · score ${d.score}`}
          </p>
          <p className="mt-2 text-sm font-semibold text-fg">{ageNote(d, step, win)}</p>
          {textPattern(step.text) !== common && <p className="mt-0.5 text-[13px] text-fg-3">{step.text}</p>}
          <button type="button" onClick={() => onPickAgent(d.agent)} className="mt-1 min-h-11 text-left text-sm text-fg-2 underline underline-offset-4 hover:text-gold-hi">
            {d.agent}
          </button>
        </li>
      ))}
    </ul>
  );
}
