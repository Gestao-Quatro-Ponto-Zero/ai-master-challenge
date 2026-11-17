"use client";

import { useState, type ReactNode } from "react";
import { Sql } from "../Sql";

/**
 * A chart panel: title and note on the left, the SQL toggle in the top-right corner (the
 * header already has that room), then the chart. The SQL opens between header and chart.
 */
export function Painel({
  titulo,
  nota,
  sql,
  children,
}: {
  titulo: string;
  nota?: string;
  sql: string[];
  children: ReactNode;
}) {
  const [aberto, setAberto] = useState(false);
  return (
    <section className="flex min-h-0 min-w-0 flex-col gap-1 rounded-lg border border-edge bg-panel px-3 py-2">
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-[13px] font-semibold text-foreground" title={titulo}>{titulo}</h2>
          {nota && <p className="truncate text-[11px] text-faint" title={nota}>{nota}</p>}
        </div>
        {sql.length > 0 && <SqlToggle aberto={aberto} onClick={() => setAberto(!aberto)} />}
      </div>
      {aberto && <SqlList sql={sql} />}
      {children}
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
