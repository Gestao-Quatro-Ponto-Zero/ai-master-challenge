"use client";

import type { TableInfo } from "@/engine/dashboard";

/** Ask a question by firing the chat's `veta:ask` event (same path the rail uses). */
function ask(question: string): void {
  window.dispatchEvent(new CustomEvent("veta:ask", { detail: { question } }));
}

const compact = (n: number): string => (n >= 1000 ? `${Math.round(n / 1000)}k` : String(n));

const STARTERS = [
  "What tables are here and how do they relate?",
  "Give me the row count of every table.",
  "What's the most interesting pattern in this data?",
];

/**
 * The idle canvas for an uploaded dataset. The curated board reads the RavenStack views,
 * so a custom database hands the surface to the chat — still fully
 * grounded: the agent discovers the schema and writes its own SQL.
 */
export function CustomDatasetBrief({ label, tables }: { label: string; tables: TableInfo[] }) {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="mb-1.5 inline-flex items-center gap-2 rounded-full border border-accent/40 bg-accent/5 px-2.5 py-1 text-[11px] text-accent">
          <span className="h-1.5 w-1.5 rounded-full bg-accent" />
          Connected · read-only
        </div>
        <h1 className="text-[21px] font-semibold leading-tight tracking-tight text-foreground">{label}</h1>
        <p className="mt-1 max-w-xl text-[13px] leading-relaxed text-muted">
          Your warehouse, opened read-only. Ask anything — the agent discovers the schema and cites the exact SQL it
          ran. The curated dashboard reads the built-in RavenStack views.
        </p>
      </div>

      {tables.length > 0 && (
        <div>
          <div className="mb-1.5 text-[10px] font-medium uppercase tracking-wider text-faint">
            {tables.length} tables
          </div>
          <div className="flex flex-wrap gap-1.5">
            {tables.map((t) => (
              <span
                key={t.name}
                className="inline-flex items-center gap-1.5 rounded-md border border-edge bg-background/60 px-2 py-1 font-mono text-[11px] text-muted"
              >
                {t.name}
                <span className="text-faint tabular-nums">{compact(t.rows)}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div>
        <div className="mb-1.5 text-[10px] font-medium uppercase tracking-wider text-faint">Try</div>
        <div className="flex flex-col gap-1.5">
          {STARTERS.map((q) => (
            <button
              key={q}
              onClick={() => ask(q)}
              className="group flex items-center gap-2 rounded-lg border border-edge bg-surface/50 px-3 py-2 text-left text-[12.5px] text-muted transition-colors hover:border-edge-strong hover:text-foreground"
            >
              <span className="text-accent">›</span>
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
