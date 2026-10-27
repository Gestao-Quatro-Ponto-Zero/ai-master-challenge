import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { pct, usd } from "@/lib/format";
import type { ScoredDeal } from "@/lib/scoring/score";
import { DayRuler, MomentumChip } from "./momentum";
import { Bar } from "./ui";

/** Tabela de deals em card; no celular, cada linha vira um bloco empilhado. */
export function DealTable({ rows, caption }: { rows: ScoredDeal[]; caption: string }) {
  return (
    <div className="card overflow-hidden">
      <table className="w-full border-collapse text-left text-[14px]">
        <caption className="sr-only">{caption}</caption>
        <thead className="hidden border-b border-line bg-hover/60 lg:table-header-group">
          <tr>
            {["Score", "Deal", "Vendedor", "Momento", "Dias na régua", "Chance", "Valor esperado", ""].map((h, i) => (
              <th key={i} scope="col" className={`field px-4 py-3 font-medium ${i >= 5 && i <= 6 ? "text-right" : ""}`}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {rows.map((s) => (
            <tr key={s.deal.id} className="relative block px-4 py-4 transition-colors hover:bg-hover lg:table-row lg:p-0">
              <td className="hidden px-4 py-3 lg:table-cell">
                {s.score === null ? (
                  <span className="text-secondary">—</span>
                ) : (
                  <span className="rounded-full bg-primary px-2 py-0.5 font-mono text-[11px] font-semibold text-surface tabular-nums">{s.score}</span>
                )}
              </td>
              <td className="block lg:table-cell lg:px-4 lg:py-3">
                <Link href={`/deal/${s.deal.id}`} className="font-semibold after:absolute after:inset-0 hover:underline">
                  {s.deal.product}
                </Link>
                <p className="deal-id text-[12px] text-secondary">
                  {s.deal.id}
                  {s.deal.account ? <span className="block font-sans">{s.deal.account}</span> : <span className="block font-sans text-stalled">Sem conta</span>}
                </p>
              </td>
              <td className="block pt-1 text-secondary lg:table-cell lg:px-4 lg:py-3 lg:text-primary">{s.deal.agent}</td>
              <td className="block pt-2 lg:table-cell lg:px-4 lg:py-3">
                <MomentumChip scored={s} />
              </td>
              <td className="hidden w-[180px] px-4 py-3 lg:table-cell">
                <DayRuler scored={s} />
              </td>
              <td className="inline-block w-1/2 pt-3 align-top lg:table-cell lg:w-[120px] lg:px-4 lg:py-3 lg:text-right">
                <span className="field lg:hidden">Chance </span>
                {s.winProbability === null ? (
                  <span className="text-secondary">sem base</span>
                ) : (
                  <>
                    <span className="font-semibold tabular-nums">{pct(s.winProbability)}</span>
                    <div className="mt-1.5 hidden lg:block">
                      <Bar value={s.winProbability} />
                    </div>
                  </>
                )}
              </td>
              <td className="inline-block w-1/2 pt-3 text-right align-top lg:table-cell lg:w-auto lg:px-4 lg:py-3">
                <span className="field lg:hidden">Valor esperado </span>
                {s.winProbability === null ? (
                  <span className="text-stalled tabular-nums">{usd(s.deal.listPrice)} parado</span>
                ) : (
                  <span className="font-semibold tabular-nums">{usd(s.expectedValue)}</span>
                )}
              </td>
              <td className="hidden pr-4 text-secondary lg:table-cell">
                <ChevronRight className="size-4" aria-hidden />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
