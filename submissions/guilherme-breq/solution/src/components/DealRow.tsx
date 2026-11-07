"use client";

import { AnimatePresence, motion } from "motion/react";
import type { Deal } from "@/lib/data";
import { formatPct } from "@/lib/format";
import { formatUSD, MOMENTUM_WEIGHT, VALUE_WEIGHT, type Reason } from "@/lib/scoring";

function scoreTone(score: number) {
  if (score >= 70) return "text-signal border-signal/40 bg-signal/10";
  if (score >= 45) return "text-warm border-warm/40 bg-warm/10";
  return "text-fg-muted border-line-strong bg-ink-800";
}

function ScoreBadge({ deal }: { deal: Deal }) {
  if (deal.status === "zumbi") {
    return (
      <div className="flex h-12 w-14 shrink-0 flex-col items-center justify-center rounded-lg border border-risk/30 bg-risk/10 text-risk">
        <span className="tabular font-mono text-sm font-semibold">+{deal.daysOverCycle}d</span>
        <span className="text-[10px] uppercase tracking-wider opacity-80">zumbi</span>
      </div>
    );
  }
  return (
    <div
      className={`flex h-12 w-14 shrink-0 flex-col items-center justify-center rounded-lg border ${scoreTone(deal.score)}`}
      aria-label={`Score ${deal.score} de 100`}
    >
      <span className="tabular font-mono text-lg font-semibold leading-none">{deal.score}</span>
      <span className="mt-0.5 text-[10px] uppercase tracking-wider opacity-70">score</span>
    </div>
  );
}

const TONE_DOT: Record<Reason["tone"], string> = {
  pos: "bg-signal",
  neutro: "bg-cool",
  neg: "bg-risk",
};

function Breakdown({ deal }: { deal: Deal }) {
  if (deal.status === "zumbi") return null;
  const isProspect = deal.status === "prospeccao";
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between text-xs text-fg-muted">
        <span>Composição do score</span>
        <span className="tabular font-mono">
          valor <span className="text-fg">{deal.valuePts}</span>/{VALUE_WEIGHT}
          {!isProspect && (
            <>
              {" "}+ momento <span className="text-fg">{deal.momentumPts}</span>/{MOMENTUM_WEIGHT}
            </>
          )}
        </span>
      </div>
      <div className="flex h-2 overflow-hidden rounded-full bg-ink-700" role="img" aria-label={`Valor ${deal.valuePts} pontos, momento ${deal.momentumPts} pontos`}>
        <div className="h-full bg-cool" style={{ width: `${deal.valuePts}%` }} />
        <div className="h-full bg-signal" style={{ width: `${deal.momentumPts}%` }} />
      </div>
      <div className="mt-1.5 flex gap-4 text-[11px] text-fg-subtle">
        <span className="flex items-center gap-1.5"><i className="size-2 rounded-full bg-cool" />Valor do deal</span>
        {!isProspect && <span className="flex items-center gap-1.5"><i className="size-2 rounded-full bg-signal" />Momento de decisão</span>}
      </div>
    </div>
  );
}

export function DealRow({
  deal,
  open,
  onToggle,
  globalWinRate,
  agentWinRate,
  showAgent,
}: {
  deal: Deal;
  open: boolean;
  onToggle: () => void;
  globalWinRate: number;
  agentWinRate: number | null;
  showAgent: boolean;
}) {
  const panelId = `deal-${deal.id}`;
  const meta =
    deal.status === "prospeccao"
      ? "Prospecção"
      : deal.status === "zumbi"
        ? `${deal.ageDays} dias aberto`
        : `${deal.ageDays} dias · ${deal.daysLeft} restantes no ciclo`;

  return (
    <li className={`rounded-xl border transition-colors ${open ? "border-line-strong bg-ink-850" : "border-line bg-ink-900 hover:border-line-strong hover:bg-ink-850"}`}>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        aria-controls={panelId}
        className="flex w-full items-center gap-4 rounded-xl px-4 py-3 text-left"
      >
        <ScoreBadge deal={deal} />
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2">
            <span className={`truncate font-medium ${deal.account ? "text-fg" : "italic text-fg-muted"}`}>
              {deal.account ?? "Conta não vinculada"}
            </span>
            <span className="shrink-0 font-mono text-[11px] text-fg-subtle">{deal.id}</span>
          </div>
          <div className="mt-0.5 flex flex-wrap gap-x-3 text-sm text-fg-muted">
            <span>{deal.product}</span>
            <span className="tabular">{formatUSD(deal.price)}</span>
            <span className="tabular text-fg-subtle">{meta}</span>
            {showAgent && <span className="text-fg-subtle">{deal.agent}</span>}
          </div>
        </div>
        <span className="hidden max-w-64 text-right text-sm text-fg md:block">{deal.action}</span>
        <svg
          aria-hidden
          className={`size-4 shrink-0 text-fg-subtle transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          viewBox="0 0 16 16"
          fill="none"
        >
          <path d="m4 6 4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id={panelId}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: [0.2, 0.8, 0.2, 1] }}
            className="overflow-hidden"
          >
            <div className="grid gap-5 border-t border-line px-4 pb-4 pt-4 md:grid-cols-[1.3fr_1fr]">
              <div>
                <p className="mb-2 text-xs uppercase tracking-wider text-fg-subtle">Por que este deal está aqui</p>
                <ul className="space-y-2">
                  {deal.reasons.map((r) => (
                    <li key={r.kind + r.text} className="flex gap-2.5 text-sm text-fg">
                      <i className={`mt-1.5 size-1.5 shrink-0 rounded-full ${TONE_DOT[r.tone]}`} aria-hidden />
                      <span>{r.text}</span>
                    </li>
                  ))}
                </ul>
                <p className="mt-4 rounded-lg border border-line bg-ink-900 px-3 py-2 text-sm md:hidden">
                  <span className="text-fg-subtle">Próximo passo: </span>
                  {deal.action}
                </p>
              </div>
              <div className="space-y-4">
                <Breakdown deal={deal} />
                <div className="rounded-lg border border-line bg-ink-900 px-3 py-2.5 text-xs leading-relaxed text-fg-muted">
                  <span className="text-fg">Chance de ganhar: ~{formatPct(globalWinRate)}</span>, a média do time.
                  {agentWinRate !== null && <> Histórico de {deal.agent.split(" ")[0]}: {formatPct(agentWinRate)}.</>}{" "}
                  Testamos vendedor, produto, setor e idade: nenhum mudou essa chance de forma confiável, por isso ela não entra no score.
                </div>
                {deal.sector && (
                  <p className="text-xs text-fg-subtle">
                    Setor da conta: <span className="text-fg-muted">{deal.sector}</span> · gerente {deal.manager} · {deal.region}
                  </p>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </li>
  );
}
