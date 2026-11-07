"use client";

import { formatCompactUSD, formatPct } from "@/lib/format";
import type { TeamRow } from "@/lib/selection";

export function TeamTable({ rows, onPick }: { rows: TeamRow[]; onPick: (agent: string) => void }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line">
      <table className="w-full min-w-[760px] text-sm">
        <caption className="sr-only">Saúde do pipeline por vendedor</caption>
        <thead className="bg-ink-900 text-left text-xs uppercase tracking-wider text-fg-subtle">
          <tr>
            <th className="px-4 py-3 font-medium">Vendedor</th>
            <th className="px-3 py-3 text-right font-medium">Vivos</th>
            <th className="px-3 py-3 text-right font-medium" title="Valor de tabela que deve se decidir nos próximos 30 dias">Em decisão (30d)</th>
            <th className="px-3 py-3 text-right font-medium">Janela fechando</th>
            <th className="px-3 py-3 font-medium">Pipeline zumbi</th>
            <th className="px-3 py-3 text-right font-medium" title="Taxa histórica de vitória. Contexto, não entra no score">Win rate</th>
            <th className="px-4 py-3 font-medium">Foco nº 1</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((r) => {
            const s = r.summary;
            const empty = s.open === 0;
            return (
              <tr key={r.name} className="bg-ink-950 transition-colors hover:bg-ink-900">
                <td className="px-4 py-3">
                  <button
                    type="button"
                    onClick={() => onPick(r.name)}
                    disabled={empty}
                    className="text-left font-medium text-fg underline-offset-4 hover:text-signal hover:underline disabled:cursor-default disabled:text-fg-subtle disabled:no-underline"
                  >
                    {r.name}
                  </button>
                  <div className="text-xs text-fg-subtle">{empty ? "Sem deals abertos" : `${r.manager} · ${r.region}`}</div>
                </td>
                <td className="tabular px-3 py-3 text-right font-mono">{s.live}</td>
                <td className="tabular px-3 py-3 text-right font-mono">{s.decide30Value ? formatCompactUSD(s.decide30Value) : "—"}</td>
                <td className={`tabular px-3 py-3 text-right font-mono ${s.windowClosing ? "text-warm" : "text-fg-subtle"}`}>{s.windowClosing}</td>
                <td className="px-3 py-3">
                  {s.live + s.zombies > 0 ? (
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-ink-700">
                        <div className="h-full bg-risk/80" style={{ width: formatPct(s.zombieShare) }} />
                      </div>
                      <span className="tabular font-mono text-xs text-fg-muted">
                        {s.zombies} ({formatPct(s.zombieShare)})
                      </span>
                    </div>
                  ) : (
                    <span className="text-fg-subtle">—</span>
                  )}
                </td>
                <td className="tabular px-3 py-3 text-right font-mono text-fg-muted">{r.winRate !== null ? formatPct(r.winRate) : "—"}</td>
                <td className="px-4 py-3 text-fg-muted">
                  {r.topDeal ? (
                    <span>
                      <span className="tabular font-mono text-fg">{r.topDeal.score}</span> · {r.topDeal.account ?? r.topDeal.id} · {r.topDeal.product}
                    </span>
                  ) : (
                    <span className="text-fg-subtle">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
