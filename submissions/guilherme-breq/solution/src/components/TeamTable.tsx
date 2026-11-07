"use client";

import { formatCompactUSD, formatPct } from "@/lib/format";
import type { TeamRow } from "@/lib/selection";

function NameButton({ r, onPick, className = "" }: { r: TeamRow; onPick: (agent: string) => void; className?: string }) {
  return (
    <button
      type="button"
      onClick={() => onPick(r.name)}
      disabled={r.summary.open === 0}
      className={`inline-flex min-h-11 items-center text-left font-medium text-fg underline-offset-4 hover:text-signal hover:underline disabled:cursor-default disabled:text-fg-subtle disabled:no-underline ${className}`}
    >
      {r.name}
    </button>
  );
}

function TopDeal({ r }: { r: TeamRow }) {
  if (!r.topDeal) return <span className="text-fg-subtle">—</span>;
  return (
    <span>
      <span className="tabular font-mono text-fg">{r.topDeal.score}</span> · {r.topDeal.account ?? r.topDeal.id} · {r.topDeal.product}
    </span>
  );
}

function ZombieBar({ r }: { r: TeamRow }) {
  const s = r.summary;
  if (s.live + s.zombies === 0) return <span className="text-fg-subtle">—</span>;
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-ink-700">
        <div className="h-full bg-risk/80" style={{ width: formatPct(s.zombieShare) }} />
      </div>
      <span className="tabular whitespace-nowrap font-mono text-xs text-fg-muted">
        {s.zombies} ({formatPct(s.zombieShare)})
      </span>
    </div>
  );
}

function Cards({ rows, onPick }: { rows: TeamRow[]; onPick: (agent: string) => void }) {
  return (
    <ul className="space-y-3 md:hidden" aria-label="Saúde do pipeline por vendedor">
      {rows.map((r) => {
        const s = r.summary;
        const empty = s.open === 0;
        return (
          <li key={r.name} className="rounded-xl border border-line bg-ink-900 p-4">
            <NameButton r={r} onPick={onPick} />
            <div className="text-xs text-fg-subtle">
              {empty ? "Sem deals abertos" : `${r.manager} · ${r.region}`}
              {r.winRate !== null && ` · taxa de ganho ${formatPct(r.winRate)}`}
            </div>
            <dl className="mt-3 grid grid-cols-2 gap-3 text-xs">
              <div>
                <dt className="text-fg-subtle">Vivos</dt>
                <dd className="tabular mt-0.5 font-mono text-sm text-fg">{s.live}</dd>
              </div>
              <div>
                <dt className="text-fg-subtle">Em decisão (30d)</dt>
                <dd className="tabular mt-0.5 whitespace-nowrap font-mono text-sm text-fg">
                  {s.decide30Value ? formatCompactUSD(s.decide30Value) : "—"}
                </dd>
              </div>
              <div>
                <dt className="text-fg-subtle">Janela fechando</dt>
                <dd className={`tabular mt-0.5 font-mono text-sm ${s.windowClosing ? "text-warm" : "text-fg-subtle"}`}>{s.windowClosing}</dd>
              </div>
              <div>
                <dt className="text-fg-subtle">Pipeline zumbi</dt>
                <dd className="mt-0.5">
                  <ZombieBar r={r} />
                </dd>
              </div>
            </dl>
            {r.topDeal && (
              <p className="mt-3 border-t border-line pt-3 text-xs text-fg-muted">
                <span className="text-fg-subtle">Deal prioritário: </span>
                <TopDeal r={r} />
              </p>
            )}
          </li>
        );
      })}
    </ul>
  );
}

export function TeamTable({ rows, onPick }: { rows: TeamRow[]; onPick: (agent: string) => void }) {
  return (
    <>
      <Cards rows={rows} onPick={onPick} />
      <div className="hidden overflow-x-auto rounded-xl border border-line md:block">
        <table className="w-full min-w-[760px] text-sm">
          <caption className="sr-only">Saúde do pipeline por vendedor</caption>
          <thead className="bg-ink-900 text-left text-xs uppercase tracking-wider text-fg-subtle">
            <tr>
              <th className="px-4 py-3 font-medium">Vendedor</th>
              <th className="px-3 py-3 text-right font-medium">Vivos</th>
              <th className="px-3 py-3 text-right font-medium" title="Valor de tabela que deve se decidir nos próximos 30 dias">Em decisão (30d)</th>
              <th className="px-3 py-3 text-right font-medium">Janela fechando</th>
              <th className="px-3 py-3 font-medium">Pipeline zumbi</th>
              <th className="px-3 py-3 text-right font-medium" title="Taxa histórica de ganho. Contexto, não entra no score">Taxa de ganho</th>
              <th className="px-4 py-3 font-medium" title="Deal aberto com maior score deste vendedor">Deal prioritário</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {rows.map((r) => {
              const s = r.summary;
              const empty = s.open === 0;
              return (
                <tr key={r.name} className="bg-ink-950 transition-colors hover:bg-ink-900">
                  <td className="px-4 py-1.5">
                    <NameButton r={r} onPick={onPick} />
                    <div className="-mt-2 pb-1.5 text-xs text-fg-subtle">{empty ? "Sem deals abertos" : `${r.manager} · ${r.region}`}</div>
                  </td>
                  <td className="tabular px-3 py-3 text-right font-mono">{s.live}</td>
                  <td className="tabular whitespace-nowrap px-3 py-3 text-right font-mono">{s.decide30Value ? formatCompactUSD(s.decide30Value) : "—"}</td>
                  <td className={`tabular px-3 py-3 text-right font-mono ${s.windowClosing ? "text-warm" : "text-fg-subtle"}`}>{s.windowClosing}</td>
                  <td className="px-3 py-3">
                    <ZombieBar r={r} />
                  </td>
                  <td className="tabular px-3 py-3 text-right font-mono text-fg-muted">{r.winRate !== null ? formatPct(r.winRate) : "—"}</td>
                  <td className="px-4 py-3 text-fg-muted">
                    <TopDeal r={r} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
