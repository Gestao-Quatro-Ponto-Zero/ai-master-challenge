"use client";

import { useState } from "react";
import type { Deal } from "@/lib/data";
import { formatInt } from "@/lib/format";
import { isResolved, type Mark, type Marks } from "@/lib/marks";
import { nextStep, type Window } from "@/lib/playbook";
import { formatUSD, WINDOW_ALERT_DAYS } from "@/lib/scoring";
import { plural, SavedNote } from "./ui";

export type Pile = "lote" | "zumbis" | "prospeccao";
const PAGE = 25;

const COPY: Record<Pile, { title: string; intro: (n: number, closing: number, max: number) => string }> = {
  lote: {
    title: "Em lote",
    intro: (n, closing) =>
      `Ticket baixo: a ligação custa mais que o deal. Resolva por e-mail, sem ligação. Os de prazo mais curto vêm primeiro.${closing ? ` ${closing} de ${n} têm até ${WINDOW_ALERT_DAYS} dias para o limite e pedem um e-mail de sim ou não.` : ""}`,
  },
  zumbis: {
    title: "Encerrar",
    intro: (_n, _c, max) =>
      `Abertos há mais de ${max} dias, o maior ciclo que já fechou. No histórico, nenhum deal assim fechou. Confirme com o cliente ou encerre no CRM: assim o pipeline volta a dizer a verdade.`,
  },
  prospeccao: {
    title: "Prospecção",
    intro: () => "Ainda não engajados: sem tempo de ciclo para medir o momento, ordenados só por valor. O próximo passo é agendar o primeiro contato.",
  },
};

/** Pilhas em massa (lote, zumbis, prospecção): uma linha por deal, com Feito em cada uma. */
export function PileView({
  pile,
  deals,
  win,
  maxCycle,
  marks,
  onMark,
  onBack,
  notice,
}: {
  pile: Pile;
  deals: Deal[];
  win: Window;
  maxCycle: number;
  marks: Marks;
  onMark: (id: string, m: Mark | null) => void;
  onBack: () => void;
  /** Aviso no topo (ex.: "Nenhum deal vivo para Carl: o trabalho desta semana está aqui"). */
  notice?: string;
}) {
  const [limit, setLimit] = useState(PAGE);
  const [announce, setAnnounce] = useState("");
  const copy = COPY[pile];
  const closing = deals.filter((d) => (d.daysLeft ?? Infinity) <= WINDOW_ALERT_DAYS).length;
  const done = deals.filter((d) => isResolved(marks[d.id])).length;

  function toggle(d: Deal, resolved: boolean) {
    onMark(d.id, resolved ? null : "feito");
    const nowDone = done + (resolved ? -1 : 1);
    setAnnounce(`${d.account ?? d.product} ${resolved ? "desmarcado" : "marcado como feito"}. ${plural(nowDone, "feito", "feitos")} de ${formatInt(deals.length)}.`);
  }

  return (
    <section aria-labelledby="ficha-titulo">
      <div className="flex items-center justify-between text-sm text-ink-3">
        <button type="button" onClick={onBack} className="-ml-2 inline-flex min-h-11 items-center px-2 font-semibold text-ink min-[900px]:hidden">
          ← Fila
        </button>
        <span className="text-[13px] font-bold uppercase tracking-wider text-gold-ink">Pilha</span>
        <span>
          {formatInt(done)} de {formatInt(deals.length)} feitos
        </span>
      </div>
      <h1 id="ficha-titulo" tabIndex={-1} className="mb-2.5 mt-3 text-[40px] font-extrabold leading-none tracking-[-0.035em] text-ink outline-none min-[900px]:mt-5 min-[900px]:text-6xl">
        {copy.title}
      </h1>
      {notice && <p className="mb-2 max-w-2xl font-semibold text-ink">{notice}</p>}
      <p className="max-w-2xl text-ink-2">{copy.intro(deals.length, closing, maxCycle)}</p>
      <SavedNote pile className="mt-2 text-ink-3" />
      <p className="sr-only" role="status" aria-live="polite">
        {announce}
      </p>

      <ul className="mt-6 divide-y divide-rule rounded-2xl border border-rule bg-card">
        {deals.slice(0, limit).map((d) => {
          const m = marks[d.id];
          const resolved = isResolved(m);
          const step = nextStep(d, win);
          const urgent = pile === "lote" && (d.daysLeft ?? Infinity) <= WINDOW_ALERT_DAYS;
          return (
            <li key={d.id} className="flex items-center gap-3 px-4 py-3">
              <div className="min-w-0 flex-1">
                <p className={`truncate font-bold ${resolved ? "text-ink-3 line-through" : "text-ink"}`}>{d.account ?? d.product}</p>
                <p className="text-[13px] text-ink-2">
                  {d.account ? `${d.product} · ` : "conta não vinculada · "}
                  {formatUSD(d.price)}
                  {d.ageDays !== null && ` · dia ${d.ageDays}`}
                  {pile === "zumbis" && d.daysOverCycle !== null && ` · ${d.daysOverCycle} além do limite`}
                </p>
                <p className="text-[13px] text-ink-3">
                  <span className="select-all">ID {d.id}</span>
                </p>
                {pile === "lote" && <p className={`text-[13px] ${urgent ? "font-semibold text-brick" : "text-ink-3"}`}>{step.text}</p>}
              </div>
              <button
                type="button"
                aria-pressed={resolved}
                onClick={() => toggle(d, resolved)}
                className={`min-h-11 shrink-0 rounded-[10px] border px-4 text-sm font-bold ${resolved ? "border-gold bg-gold text-navy-deep" : "border-ink/30 text-ink hover:border-ink"}`}
              >
                <span className="sr-only">{d.account ?? d.product}: </span>
                {resolved ? "Feito ✓" : "Feito"}
              </button>
            </li>
          );
        })}
      </ul>
      {deals.length > limit && (
        <button
          type="button"
          onClick={() => setLimit((l) => l + PAGE)}
          className="mt-4 min-h-11 w-full rounded-lg border border-ink/30 text-sm font-semibold text-ink hover:border-ink"
        >
          Mostrar mais {Math.min(PAGE, deals.length - limit)}
        </button>
      )}
    </section>
  );
}
