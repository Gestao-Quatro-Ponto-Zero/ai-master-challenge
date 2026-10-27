import { ArrowRight, Building2, CircleAlert } from "lucide-react";
import Link from "next/link";
import { pct, usd } from "@/lib/format";
import type { ScoredDeal } from "@/lib/scoring/score";
import { DayRuler, MomentumChip } from "./momentum";
import { Bar } from "./ui";

/** Card de um deal da pauta: decisão (produto, chance, valor) e a régua de dias. */
export function DealCard({ scored, rank }: { scored: ScoredDeal; rank: number }) {
  const { deal } = scored;
  return (
    <li>
      <Link href={`/deal/${deal.id}`} className="card group flex h-full flex-col p-5 transition-[transform,box-shadow,border-color] hover:-translate-y-0.5 hover:border-secondary/50 hover:shadow-md motion-reduce:hover:translate-y-0">
        <div className="flex items-start gap-3">
          <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-hover font-mono text-[13px] font-semibold text-secondary tabular-nums">
            {String(rank).padStart(2, "0")}
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[19px] leading-tight font-semibold tracking-[-0.02em] group-hover:underline group-hover:underline-offset-4">
              {deal.product}
            </p>
            <p className="mt-0.5 truncate text-[13px] text-secondary">
              <span className="deal-id">{deal.id}</span> · {deal.agent}
            </p>
          </div>
          {scored.score !== null && (
            <span className="rounded-full bg-primary px-2.5 py-1 font-mono text-[11px] font-semibold text-surface tabular-nums" title="Score de prioridade (0–100)">
              {scored.score}
            </span>
          )}
        </div>

        <dl className="mt-5 grid grid-cols-2 gap-4">
          <div>
            <dt className="field">Chance</dt>
            <dd className="mt-1 text-[22px] leading-none font-bold tabular-nums">{pct(scored.winProbability ?? 0)}</dd>
            <div className="mt-2">
              <Bar value={scored.winProbability ?? 0} />
            </div>
          </div>
          <div>
            <dt className="field">Valor esperado</dt>
            <dd className="mt-1 text-[22px] leading-none font-bold tabular-nums">{usd(scored.expectedValue)}</dd>
            <p className="mt-2 text-[12px] text-secondary">de {usd(deal.listPrice)} de tabela</p>
          </div>
        </dl>

        <div className="mt-5">
          <div className="mb-2 flex items-center justify-between gap-2">
            <MomentumChip scored={scored} />
            {deal.account ? (
              <span className="flex min-w-0 items-center gap-1 truncate text-[12px] text-secondary">
                <Building2 className="size-3.5 shrink-0" aria-hidden />
                {deal.account}
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[12px] text-stalled">
                <CircleAlert className="size-3.5" aria-hidden />
                Sem conta
              </span>
            )}
          </div>
          <DayRuler scored={scored} />
        </div>

        <p className="mt-auto flex items-start gap-2 pt-5 text-[14px] font-medium text-moment">
          <ArrowRight className="mt-0.5 size-4 shrink-0" aria-hidden />
          {scored.nextAction}
        </p>
      </Link>
    </li>
  );
}
