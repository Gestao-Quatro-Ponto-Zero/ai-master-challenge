"use client";

import { motion } from "motion/react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Deal, PipelineData } from "@/lib/data";
import { firstName, formatCompactUSD, formatDate, formatInt } from "@/lib/format";
import { isResolved, type Mark, type Marks } from "@/lib/marks";
import { buildQueue, type Verb, type Window, type WorkItem } from "@/lib/playbook";
import { formatUSD, WINDOW_ALERT_DAYS } from "@/lib/scoring";
import { DealSheet } from "./DealSheet";
import { PileView, type Pile } from "./PileView";
import { Brand, ghostButton, plural } from "./ui";

const GROUP_LABEL: Partial<Record<Verb, string>> = { Ligar: "Ligar", Decidir: "Forçar sim ou não", Reengajar: "Reengajar", Preparar: "Preparar proposta" };
const MOBILE = "(max-width: 899px)";

/** O vendedor abre e vê a fila da semana (esquerda) e a ficha do deal selecionado (direita). */
export function WorkView({
  data,
  agent,
  win,
  marks,
  setMark,
  onChangeAgent,
  onTeam,
  onHow,
}: {
  data: PipelineData;
  agent: string;
  win: Window;
  marks: Marks;
  setMark: (id: string, m: Mark | null) => void;
  onChangeAgent: () => void;
  onTeam: () => void;
  onHow: () => void;
}) {
  const info = data.agents.find((a) => a.name === agent);
  const own = useMemo(() => data.deals.filter((d) => d.agent === agent), [data.deals, agent]);
  const queue = useMemo(() => buildQueue(own, win), [own, win]);
  const catalog = useMemo(() => {
    const prices = data.deals.map((d) => d.price).filter((p) => p > 0);
    return { min: Math.min(...prices), max: Math.max(...prices) };
  }, [data.deals]);

  // Ordem de exibição: cada grupo sem os adiados; os adiados vão juntos para o fim.
  const display = useMemo(() => {
    const groups = queue.groups
      .map((g) => ({ verb: g.verb, items: g.items.filter((i) => marks[i.deal.id] !== "adiado") }))
      .filter((g) => g.items.length > 0);
    const snoozed = queue.work.filter((i) => marks[i.deal.id] === "adiado");
    return { groups, snoozed, flat: [...groups.flatMap((g) => g.items), ...snoozed] };
  }, [queue, marks]);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [pile, setPile] = useState<Pile | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [announce, setAnnounce] = useState("");
  const focusTarget = useRef<"sheet" | "item" | null>(null);

  const firstPending = display.flat.find((i) => !isResolved(marks[i.deal.id]) && marks[i.deal.id] !== "adiado") ?? display.flat[0] ?? null;
  const current: WorkItem<Deal> | null = display.flat.find((i) => i.deal.id === selectedId) ?? firstPending;

  const piles: { id: Pile; deals: Deal[] }[] = [
    { id: "lote", deals: queue.lote },
    { id: "zumbis", deals: queue.zombies },
    { id: "prospeccao", deals: queue.prospects },
  ];
  const defaultPile = piles.find((p) => p.deals.length > 0)?.id ?? null;
  const shownPile = pile ?? (current ? null : defaultPile);
  // Nada para mostrar (vendedor sem nenhum deal aberto): a tela explica e oferece saída, no mobile também.
  const empty = !current && !shownPile;

  const total = queue.work.length;
  const doneCount = queue.work.filter((i) => isResolved(marks[i.deal.id])).length;
  const inPlay = queue.work.filter((i) => !isResolved(marks[i.deal.id])).reduce((s, i) => s + i.deal.price, 0);
  const allDone = total > 0 && doneCount === total;

  const isMobile = () => typeof window !== "undefined" && window.matchMedia(MOBILE).matches;

  function openDeal(id: string) {
    setPile(null);
    setSelectedId(id);
    setSheetOpen(true);
    if (isMobile()) {
      focusTarget.current = "sheet";
      window.scrollTo(0, 0);
    }
  }

  function openPile(p: Pile) {
    setPile(p);
    setSheetOpen(true);
    if (isMobile()) {
      focusTarget.current = "sheet";
      window.scrollTo(0, 0);
    }
  }

  function backToQueue() {
    setSheetOpen(false);
    focusTarget.current = "item";
  }

  const markCurrent = useCallback(
    (m: Mark | null) => {
      if (!current) return;
      const id = current.deal.id;
      setMark(id, m);
      if (m === null) {
        setAnnounce("Marcação desfeita.");
        return;
      }
      // Avança para o próximo ainda pendente (na ordem exibida, voltando ao início se preciso).
      const i = display.flat.findIndex((x) => x.deal.id === id);
      const order = [...display.flat.slice(i + 1), ...display.flat.slice(0, i)];
      const next = order.find((x) => !isResolved(marks[x.deal.id]) && marks[x.deal.id] !== "adiado");
      const label = m === "feito" ? "marcado como feito" : m === "adiado" ? "adiado para o fim da fila" : "marcado como não vivo";
      const nowDone = doneCount + (m !== "adiado" && !isResolved(marks[id]) ? 1 : 0);
      setAnnounce(`${current.deal.account ?? current.deal.product} ${label}. ${nowDone} de ${total} feitas.${next ? "" : " Fila zerada."}`);
      if (next) setSelectedId(next.deal.id);
      focusTarget.current = "sheet";
    },
    [current, display.flat, marks, doneCount, total, setMark],
  );

  const move = useCallback(
    (dir: 1 | -1) => {
      if (!display.flat.length) return;
      const i = current ? display.flat.findIndex((x) => x.deal.id === current.deal.id) : -1;
      const to = display.flat[Math.min(display.flat.length - 1, Math.max(0, i + dir))];
      setPile(null);
      setSelectedId(to.deal.id);
      requestAnimationFrame(() => document.querySelector<HTMLElement>(`[data-item-id="${to.deal.id}"]`)?.focus());
    },
    [display.flat, current],
  );

  // Setas dentro da fila: só o item atual é parada de Tab (roving tabindex); as setas andam entre os itens.
  function onListKey(e: React.KeyboardEvent<HTMLElement>) {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    if (!(e.target as HTMLElement).closest("[data-item-id]")) return;
    e.preventDefault();
    move(e.key === "ArrowDown" ? 1 : -1);
  }

  // Teclado: J/K navegam, E marca feito, A adia. Não captura quando o foco está num campo de texto.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.ctrlKey || e.metaKey || e.altKey || e.defaultPrevented) return;
      const el = e.target as HTMLElement | null;
      if (el && (el.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName))) return;
      const k = e.key.toLowerCase();
      if (k === "j") move(1);
      else if (k === "k") move(-1);
      else if ((k === "e" || k === "a") && current && !shownPile) markCurrent(k === "e" ? "feito" : "adiado");
      else return;
      e.preventDefault();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [move, markCurrent, current, shownPile]);

  // Foco depois de a tela mudar: ficha (ao abrir no mobile ou marcar) ou o item da fila (ao voltar).
  useEffect(() => {
    const t = focusTarget.current;
    if (!t) return;
    focusTarget.current = null;
    const el = t === "sheet" ? document.getElementById("ficha-titulo") : document.querySelector<HTMLElement>(`[data-item-id="${current?.deal.id}"]`);
    el?.focus({ preventScroll: t === "item" ? false : true });
  });

  const lotePrices = new Set(queue.lote.map((d) => d.price));
  const loteClosing = queue.lote.filter((d) => (d.daysLeft ?? Infinity) <= WINDOW_ALERT_DAYS).length;
  const poolDone = (ds: Deal[]) => ds.filter((d) => isResolved(marks[d.id])).length;
  const zombieValue = queue.zombies.reduce((s, d) => s + d.price, 0);
  const first = firstName(agent);

  function position(item: WorkItem<Deal>) {
    const g = queue.groups.find((x) => x.verb === item.step.verb);
    const idx = g ? g.items.findIndex((x) => x.deal.id === item.deal.id) + 1 : 1;
    const label = GROUP_LABEL[item.step.verb] ?? item.step.verb;
    return `${label} · ${idx} de ${g?.items.length ?? 1}`;
  }

  return (
    <div className="fila-root min-h-screen min-[900px]:grid min-[900px]:grid-cols-[420px_minmax(0,1fr)]">
      <nav
        aria-label="Fila da semana"
        onKeyDown={onListKey}
        className={`bg-navy min-[900px]:sticky min-[900px]:top-0 min-[900px]:h-screen min-[900px]:scroll-pt-28 min-[900px]:overflow-y-auto ${sheetOpen ? "max-[899px]:hidden" : ""}`}
      >
        {/* Cabeçalho do painel fica fixo no topo: Trocar, Time e Como funciona nunca saem de vista, mesmo com Tab até o fim da fila. */}
        <div className="flex items-center justify-between gap-3 bg-navy px-4 pb-1 pt-5 min-[900px]:sticky min-[900px]:top-0 min-[900px]:z-20 min-[900px]:px-6 min-[900px]:pt-6">
          <Brand />
          <div className="-mr-2 flex items-center">
            <button type="button" onClick={onChangeAgent} className="min-h-11 px-2 text-[13px] font-semibold text-fg-2 underline-offset-4 hover:text-gold-hi hover:underline">
              Trocar
            </button>
            <button type="button" onClick={onTeam} className="min-h-11 px-2 text-[13px] font-semibold text-fg-2 underline-offset-4 hover:text-gold-hi hover:underline">
              Time
            </button>
            <button type="button" onClick={onHow} className="min-h-11 px-2 text-[13px] font-semibold text-fg-2 underline-offset-4 hover:text-gold-hi hover:underline">
              Como funciona
            </button>
          </div>
        </div>

        <div className="flex flex-col px-4 pb-4 min-[900px]:px-6">
        <h1 id="tela-titulo" tabIndex={-1} className="mb-1 mt-3 text-[26px] font-bold leading-tight tracking-[-0.02em] text-fg outline-none">
          Bom dia, {first}.
        </h1>
        <p className="text-sm text-fg-2">
          {info ? `${info.region} · ${info.manager} · ` : ""}CRM até {formatDate(data.today)}
        </p>

        {total > 0 && (
        <div className="mt-5">
          <div
            role="progressbar"
            aria-label="Deals da fila feitos esta semana"
            aria-valuemin={0}
            aria-valuemax={total}
            aria-valuenow={doneCount}
            className="h-1.5 overflow-hidden rounded-full bg-line"
          >
            <motion.div className="h-full rounded-full bg-gold" initial={false} animate={{ width: total ? `${(doneCount / total) * 100}%` : "0%" }} transition={{ duration: 0.4, ease: [0.2, 0.8, 0.2, 1] }} />
          </div>
          <p className="mt-1.5 flex justify-between gap-3 text-[13px] text-fg-2">
            <span>{allDone ? "Fila zerada. Bom trabalho." : `${doneCount} de ${total} feitas esta semana`}</span>
            {!allDone && <span>{formatUSD(inPlay)} em jogo</span>}
          </p>
          <p className="mt-2 hidden text-[13px] text-fg-3 min-[900px]:block">
            <Kbd>J</Kbd> <Kbd>K</Kbd> navegar &nbsp; <Kbd>E</Kbd> feito &nbsp; <Kbd>A</Kbd> adiar
          </p>
        </div>
        )}
        <p className="sr-only" role="status" aria-live="polite">
          {announce}
        </p>

        {display.groups.map((g) => (
          <Group key={g.verb} label={GROUP_LABEL[g.verb] ?? g.verb} count={g.items.length}>
            {g.items.map((i) => (
              <QueueItem key={i.deal.id} item={i} mark={marks[i.deal.id]} current={!shownPile && current?.deal.id === i.deal.id} tabStop={current?.deal.id === i.deal.id} onOpen={() => openDeal(i.deal.id)} />
            ))}
          </Group>
        ))}
        {display.snoozed.length > 0 && (
          <Group label="Adiados" count={display.snoozed.length}>
            {display.snoozed.map((i) => (
              <QueueItem key={i.deal.id} item={i} mark="adiado" current={!shownPile && current?.deal.id === i.deal.id} tabStop={current?.deal.id === i.deal.id} onOpen={() => openDeal(i.deal.id)} showVerb />
            ))}
          </Group>
        )}

        {queue.lote.length > 0 && (
          <Group label="Em lote" count={queue.lote.length}>
            <PileCard onClick={() => openPile("lote")} active={shownPile === "lote"}>
              <b>
                {queue.lote.length} deals {lotePrices.size === 1 ? `de ${formatUSD([...lotePrices][0])}` : "de ticket baixo"} · um e-mail resolve
              </b>
              <span>
                {loteClosing > 0 ? `${loteClosing} com até ${WINDOW_ALERT_DAYS} dias para o limite · ` : ""}
                {formatUSD(queue.lote.reduce((s, d) => s + d.price, 0))} no total
                {poolDone(queue.lote) > 0 && ` · ${plural(poolDone(queue.lote), "feito", "feitos")}`}
              </span>
            </PileCard>
          </Group>
        )}
        {queue.zombies.length > 0 && (
          <Group label="Encerrar" count={queue.zombies.length}>
            <PileCard onClick={() => openPile("zumbis")} active={shownPile === "zumbis"} risk>
              <b>
                {queue.zombies.length} zumbis · {formatCompactUSD(zombieValue)} parados
              </b>
              <span>
                Abertos há mais de {data.maxCycleDays} dias. Nenhum deal assim fechou no histórico.
                {poolDone(queue.zombies) > 0 && ` ${plural(poolDone(queue.zombies), "feito", "feitos")}.`}
              </span>
            </PileCard>
          </Group>
        )}
        {queue.prospects.length > 0 && (
          <Group label="Prospecção" count={queue.prospects.length}>
            <PileCard onClick={() => openPile("prospeccao")} active={shownPile === "prospeccao"}>
              <b>{queue.prospects.length} ainda sem contato</b>
              <span>Agendar o primeiro contato · {formatCompactUSD(queue.prospects.reduce((s, d) => s + d.price, 0))} de tabela</span>
            </PileCard>
          </Group>
        )}
        </div>
      </nav>

      <main className={`on-paper bg-paper px-4 pb-12 pt-3 text-ink min-[900px]:px-14 min-[900px]:pb-10 min-[900px]:pt-9 ${sheetOpen || empty ? "" : "max-[899px]:hidden"}`}>
        <div className="max-w-[1080px]">
          {shownPile ? (
            <PileView
              key={shownPile}
              pile={shownPile}
              deals={piles.find((p) => p.id === shownPile)?.deals ?? []}
              win={win}
              maxCycle={data.maxCycleDays}
              marks={marks}
              onMark={setMark}
              onBack={backToQueue}
              notice={!pile && !current ? `Nenhum deal vivo para ${first}: o trabalho desta semana está nesta pilha.` : undefined}
            />
          ) : current ? (
            <DealSheet
              key={current.deal.id}
              deal={current.deal}
              step={current.step}
              position={marks[current.deal.id] === "adiado" ? `Adiado · ${GROUP_LABEL[current.step.verb] ?? current.step.verb}` : position(current)}
              win={win}
              maxCycle={data.maxCycleDays}
              curve={data.decideCurve}
              catalog={catalog}
              globalWinRate={data.globalWinRate}
              mark={marks[current.deal.id]}
              onMark={markCurrent}
              onBack={backToQueue}
            />
          ) : (
            <div className="mt-4 min-[900px]:mt-0">
              <h1 id="ficha-titulo" tabIndex={-1} className="text-3xl font-extrabold tracking-tight outline-none">
                Nenhum deal aberto para {first}
              </h1>
              <p className="mt-2 max-w-xl text-ink-2">Não há nada para ligar, resolver por e-mail ou encerrar nesta carteira. Se a pessoa trocou de carteira ou o CRM está desatualizado, vale conferir antes de seguir.</p>
              <div className="mt-6 flex flex-wrap gap-2">
                <button type="button" onClick={onChangeAgent} className={ghostButton(true)}>
                  Trocar de vendedor
                </button>
                <button type="button" onClick={onTeam} className={ghostButton(true)}>
                  Ver o time
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function Group({ label, count, children }: { label: string; count: number; children: React.ReactNode }) {
  const id = `grupo-${label.replace(/\s+/g, "-").toLowerCase()}`;
  return (
    <section className="mt-4" aria-labelledby={id}>
      <h2 id={id} className="sticky top-0 z-10 -mx-1 mb-1 flex justify-between min-[900px]:top-[72px] bg-navy px-1 py-1.5 text-[13px] font-bold uppercase tracking-[0.14em] text-fg-3">
        <span>{label}</span>
        <span>{formatInt(count)}</span>
      </h2>
      <ul className="space-y-0.5">{children}</ul>
    </section>
  );
}

function QueueItem({ item, mark, current, tabStop, onOpen, showVerb }: { item: WorkItem<Deal>; mark: Mark | undefined; current: boolean; tabStop: boolean; onOpen: () => void; showVerb?: boolean }) {
  const d = item.deal;
  const resolved = isResolved(mark);
  const dead = mark === "morto";
  return (
    <li>
      <button
        type="button"
        data-item-id={d.id}
        tabIndex={tabStop ? 0 : -1}
        aria-current={current ? "true" : undefined}
        onClick={onOpen}
        className="grid min-h-[52px] w-full grid-cols-[18px_minmax(0,1fr)_auto] items-center gap-2.5 rounded-[10px] px-3 py-2 text-left transition-colors hover:bg-fg/5 aria-[current=true]:bg-fg aria-[current=true]:text-ink"
      >
        <span
          aria-hidden
          className={`flex size-[18px] items-center justify-center rounded-full border-[1.5px] ${
            dead ? (current ? "border-brick text-brick" : "border-risk text-risk") : resolved ? "border-gold bg-gold text-navy-deep" : current ? "border-gold-ink" : "border-fg-3"
          }`}
        >
          {mark === "feito" && (
            <svg viewBox="0 0 12 12" className="size-3" fill="none">
              <path d="m2.5 6.2 2.4 2.3 4.6-5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
          {dead && (
            <svg viewBox="0 0 12 12" className="size-3" fill="none">
              <path d="m3.2 3.2 5.6 5.6m0-5.6-5.6 5.6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          )}
        </span>
        <span className="min-w-0">
          <span className={`block truncate text-[15px] font-bold ${mark === "feito" ? "line-through" : ""} ${current ? "" : resolved ? "text-fg-2" : "text-fg"}`}>
            {d.account ?? d.product}
          </span>
          <span className={`block truncate text-[13px] font-medium ${current ? "text-ink-2" : "text-fg-2"}`}>
            {showVerb && `${item.step.verb} · `}
            {d.account ? d.product : "conta não vinculada"} · dia {d.ageDays}
            {mark === "feito" && <span className="sr-only">, feito</span>}
            {dead && <span className={`font-semibold ${current ? "text-brick" : "text-risk"}`}> · não vivo</span>}
            {mark === "adiado" && <span className="sr-only">, adiado</span>}
          </span>
        </span>
        <span className={`text-[13px] font-semibold ${current ? "text-ink-2" : "text-fg-2"}`}>{formatUSD(d.price)}</span>
      </button>
    </li>
  );
}

function PileCard({ children, onClick, active, risk }: { children: React.ReactNode; onClick: () => void; active: boolean; risk?: boolean }) {
  return (
    <li className="list-none">
      <button
        type="button"
        onClick={onClick}
        aria-current={active ? "true" : undefined}
        className={`block min-h-14 w-full rounded-[10px] border border-dashed p-3 text-left text-fg [&>b]:block [&>b]:font-bold [&>span]:block [&>span]:text-[13px] [&>span]:text-fg-2 ${risk ? "border-risk/50 [&>b]:text-risk" : "border-line-strong"} ${active ? "bg-fg/10" : "hover:bg-fg/5"}`}
      >
        {children}
      </button>
    </li>
  );
}

function Kbd({ children }: { children: React.ReactNode }) {
  return <kbd className="inline-block min-w-5 rounded border border-line px-1.5 py-px text-center text-[13px] font-semibold text-fg-2">{children}</kbd>;
}
