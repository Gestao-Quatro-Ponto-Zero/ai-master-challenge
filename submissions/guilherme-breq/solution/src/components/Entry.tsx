"use client";

import { motion } from "motion/react";
import { useMemo, useState } from "react";
import { formatDate, formatInt } from "@/lib/format";
import type { TeamRow } from "@/lib/selection";
import { Brand, fold, ghostButton } from "./ui";

/** Primeira tela: "quem está abrindo?". O vendedor entra pelo próprio nome; gerente e RevOps pelo time. */
export function Entry({
  rows,
  today,
  onPick,
  onTeam,
  onHow,
}: {
  rows: TeamRow[];
  today: string;
  onPick: (agent: string) => void;
  onTeam: () => void;
  onHow: () => void;
}) {
  const [query, setQuery] = useState("");
  const sorted = useMemo(() => [...rows].sort((a, b) => a.name.localeCompare(b.name)), [rows]);
  const q = fold(query.trim());
  const shown = q ? sorted.filter((r) => fold(r.name).includes(q)) : sorted;
  // Quem tem fila vem primeiro; quem não tem deals vivos fica num grupo atenuado, sem disputar atenção.
  const active = shown.filter((r) => r.summary.live > 0);
  const idle = shown.filter((r) => r.summary.live === 0);

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 pb-16 pt-6 sm:px-6 sm:pt-8">
      <header className="flex items-center justify-between gap-3">
        <Brand />
        <button type="button" onClick={onHow} className="min-h-11 text-sm font-semibold text-fg-2 underline-offset-4 hover:text-gold-hi hover:underline">
          Como o score funciona
        </button>
      </header>

      <main className="mt-10 sm:mt-16">
        <p className="text-sm text-fg-2">Dados do CRM até {formatDate(today)}</p>
        <h1 id="tela-titulo" tabIndex={-1} className="mt-3 text-4xl font-extrabold leading-[1.05] tracking-tight text-fg outline-none sm:text-6xl">
          Bom dia.
          <br />
          <span className="font-light text-gold-hi">Quem está abrindo?</span>
        </h1>
        <p className="mt-5 max-w-xl text-fg-2">
          Escolha o seu nome e a fila da semana abre pronta: quem ligar, quem forçar a decidir, o que resolver por e-mail e o que encerrar.
        </p>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
          <label className="block flex-1 sm:max-w-sm">
            <span className="sr-only">Buscar vendedor pelo nome</span>
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Digite o seu nome"
              autoComplete="off"
              className="h-12 w-full rounded-lg border border-line-strong bg-navy px-4 text-fg placeholder:text-fg-3"
            />
          </label>
          <button type="button" onClick={onTeam} className={ghostButton(false, "sm:ml-auto")}>
            Sou gerente ou RevOps: ver o time →
          </button>
        </div>

        <p className="mt-4 text-[13px] text-fg-3" role="status" aria-live="polite">
          {q ? `${formatInt(shown.length)} de ${formatInt(sorted.length)} vendedores` : `${formatInt(sorted.length)} vendedores`}
        </p>

        {shown.length === 0 ? (
          <p className="mt-4 rounded-xl border border-dashed border-line-strong px-4 py-8 text-center text-sm text-fg-2">
            Ninguém com esse nome. Confira a grafia ou veja o time inteiro.
          </p>
        ) : (
          <>
            {active.length > 0 && <Group title="Com deals vivos" rows={active} offset={0} onPick={onPick} />}
            {idle.length > 0 && <Group title="Sem deals vivos" rows={idle} offset={active.length} onPick={onPick} idle />}
          </>
        )}
      </main>
    </div>
  );
}

function Group({ title, rows, offset, onPick, idle = false }: { title: string; rows: TeamRow[]; offset: number; onPick: (a: string) => void; idle?: boolean }) {
  const id = `entrada-${idle ? "sem" : "com"}-vivos`;
  return (
    <section className="mt-5" aria-labelledby={id}>
      <h2 id={id} className="mb-2 text-[13px] font-bold uppercase tracking-[0.12em] text-fg-3">
        {title} · {formatInt(rows.length)}
      </h2>
      <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {rows.map((r, i) => (
          <motion.li
            key={r.name}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: Math.min(offset + i, 12) * 0.02, ease: [0.2, 0.8, 0.2, 1] }}
          >
            <button
              type="button"
              onClick={() => onPick(r.name)}
              className={`flex min-h-16 w-full items-center justify-between gap-3 rounded-xl border px-4 py-3 text-left transition-colors hover:border-gold ${idle ? "border-line bg-transparent" : "border-line bg-navy"}`}
            >
              <span className="min-w-0">
                <span className={`block truncate font-bold ${idle ? "text-fg-2" : "text-fg"}`}>{r.name}</span>
                <span className={`block truncate text-[13px] ${idle ? "text-fg-3" : "text-fg-2"}`}>
                  {r.region} · {r.manager}
                </span>
              </span>
              {idle ? (
                <span className="shrink-0 text-right text-[13px] text-fg-3">{r.summary.open === 0 ? "sem deals abertos" : "sem vivos"}</span>
              ) : (
                <span className="shrink-0 text-right text-[13px] text-fg-2">
                  <span className="block text-base font-bold text-gold-hi">{r.summary.live}</span>
                  {r.summary.live === 1 ? "vivo" : "vivos"}
                </span>
              )}
            </button>
          </motion.li>
        ))}
      </ul>
    </section>
  );
}
