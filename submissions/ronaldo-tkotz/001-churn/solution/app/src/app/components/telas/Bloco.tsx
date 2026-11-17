"use client";

import { useState, type ReactNode } from "react";
import { SqlList, SqlToggle } from "./Painel";

/**
 * One block of the dashboard design: the code (B1.1…), the question and the data level, with
 * the SQL toggle in the top-right corner; then the visual and the limit that affects it.
 */
export function Bloco({
  codigo,
  pergunta,
  nivel,
  limite,
  sql,
  children,
  className = "",
}: {
  codigo: string;
  pergunta: string;
  nivel: string;
  limite?: ReactNode;
  sql?: string[];
  children: ReactNode;
  className?: string;
}) {
  const [aberto, setAberto] = useState(false);
  return (
    <section className={`flex min-w-0 flex-col gap-2 rounded-lg border border-edge bg-panel px-3 py-2.5 ${className}`}>
      <header className="flex items-start gap-3">
        <div className="flex min-w-0 flex-1 flex-wrap items-baseline gap-x-2 gap-y-1">
          <span className="font-mono text-[11px] text-accent">{codigo}</span>
          <h2 className="text-[14px] font-semibold text-foreground">{pergunta}</h2>
          <span className="rounded-full border border-edge px-2 py-0.5 text-[10.5px] text-muted">nível: {nivel}</span>
        </div>
        {sql && sql.length > 0 && <SqlToggle aberto={aberto} onClick={() => setAberto(!aberto)} />}
      </header>
      {aberto && sql && <SqlList sql={sql} />}
      {children}
      {limite && <p className="text-[11.5px] leading-relaxed text-faint">Limite: {limite}</p>}
    </section>
  );
}

/** A number card for a block: label, value, note. */
export function Numero({ rotulo, valor, nota }: { rotulo: string; valor: string; nota?: string }) {
  return (
    <div className="rounded-lg border border-edge bg-surface/60 px-3 py-2">
      <div className="text-[11px] text-muted">{rotulo}</div>
      <div className="text-[20px] font-semibold leading-tight tabular-nums tracking-tight text-foreground">{valor}</div>
      {nota && <div className="mt-0.5 text-[11px] leading-snug text-faint">{nota}</div>}
    </div>
  );
}
