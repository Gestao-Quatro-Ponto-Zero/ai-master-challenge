"use client";

import { useRef, useState, type ReactNode } from "react";
import { Sql } from "../Sql";
import { MarcarToggle } from "./Marcados";

/**
 * A chart panel: title and note on the left, the SQL toggle in the top-right corner (the
 * header already has that room) beside the deck mark (D44), then the chart. The SQL opens between
 * header and chart; the mark copies only the chart area.
 */
export function Painel({
  titulo,
  nota,
  sql,
  children,
  acoes,
}: {
  titulo: string;
  nota?: string;
  sql: string[];
  children: ReactNode;
  /** Extra header buttons (e.g. remove a panel from a custom screen). */
  acoes?: ReactNode;
}) {
  const [aberto, setAberto] = useState(false);
  const area = useRef<HTMLDivElement>(null);
  return (
    <section className="flex min-h-0 min-w-0 flex-col gap-1 rounded-lg border border-edge bg-panel px-3 py-2">
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-[13px] font-semibold text-foreground" title={titulo}>{titulo}</h2>
          {nota && <p className="truncate text-[11px] text-faint" title={nota}>{nota}</p>}
        </div>
        <div className="flex shrink-0 items-center gap-1">
          {acoes}
          <MarcarToggle titulo={titulo} nota={nota} sql={sql} alvo={area} />
          {sql.length > 0 && <SqlToggle aberto={aberto} onClick={() => setAberto(!aberto)} />}
        </div>
      </div>
      {aberto && <SqlList sql={sql} />}
      <div ref={area} className="flex min-h-0 flex-1 flex-col gap-1">
        {children}
      </div>
    </section>
  );
}

/** The small "SQL" switch used in panel and block headers. */
export function SqlToggle({ aberto, onClick }: { aberto: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      aria-expanded={aberto}
      title={aberto ? "Esconder o SQL" : "Ver o SQL deste gráfico"}
      className={`shrink-0 rounded border px-1.5 py-0.5 font-mono text-[10.5px] transition-colors ${
        aberto ? "border-accent text-accent" : "border-edge text-faint hover:border-edge-strong hover:text-muted"
      }`}
    >
      SQL
    </button>
  );
}

export function SqlList({ sql }: { sql: string[] }) {
  return (
    <div className="flex flex-col gap-2">
      {sql.map((q, i) => (
        <Sql key={i} sql={q} />
      ))}
    </div>
  );
}
