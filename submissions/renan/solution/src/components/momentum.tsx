import type { CSSProperties } from "react";
import { history } from "@/lib/pipeline";
import { MOMENTUM_LABEL, type ScoredDeal } from "@/lib/scoring/score";

type Momentum = ScoredDeal["momentum"];

const CHIP: Record<Momentum, string> = {
  prospecting: "bg-hover text-secondary",
  early: "bg-moment-soft text-moment",
  progressing: "bg-moment-soft text-moment",
  closing: "bg-moment-soft text-moment",
  stalled: "bg-stalled-soft text-stalled",
};

/** Chip de status: "Reta final · 95/138". O número carrega a régua em qualquer largura. */
export function MomentumChip({ scored }: { scored: ScoredDeal }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[13px] font-semibold whitespace-nowrap ${CHIP[scored.momentum]}`}>
      {MOMENTUM_LABEL[scored.momentum]}
      {scored.daysOpen !== null && (
        <span className="font-mono text-[11px] font-medium tabular-nums opacity-90">
          {scored.daysOpen}/{history.maxCycle}
        </span>
      )}
    </span>
  );
}

/**
 * A régua da E2 como componente: trilho de 0 a 138 dias, marcos derivados do
 * histórico (metade das perdas, 75% dos ganhos, maior ciclo) e o marcador do deal.
 * Deals parados ficam presos no fim, além do limite.
 */
export function DayRuler({ scored, showLabels = false }: { scored: ScoredDeal; showLabels?: boolean }) {
  const max = history.maxCycle;
  const day = scored.daysOpen;
  const position = day === null ? 0 : Math.min(day, max) / max;
  const marks = [
    { day: history.lostMedianCycle, label: `${history.lostMedianCycle}d · metade das perdas` },
    { day: history.wonP75Cycle, label: `${history.wonP75Cycle}d · 75% dos ganhos` },
  ];
  const fill = scored.momentum === "stalled" ? "bg-stalled" : scored.momentum === "prospecting" ? "bg-secondary" : "bg-moment";

  return (
    <div className={showLabels ? "pb-6" : ""}>
      <div
        className="relative h-2 rounded-full bg-track"
        role="img"
        aria-label={
          day === null
            ? "Ainda em prospecção, sem dias no pipeline"
            : `${day} dias abertos numa régua de 0 a ${max} dias, o maior ciclo já fechado`
        }
      >
        <div className={`absolute inset-y-0 left-0 rounded-full ${fill} opacity-25`} style={{ width: `${position * 100}%` }} />
        {marks.map((m) => (
          <span key={m.day} className="absolute top-1/2 h-3 w-px -translate-y-1/2 bg-secondary/60" style={{ left: `${(m.day / max) * 100}%` }}>
            {showLabels && (
              <span className="absolute top-4 left-1/2 -translate-x-1/2 font-mono text-[10px] whitespace-nowrap text-secondary">{m.label}</span>
            )}
          </span>
        ))}
        <span
          className={`absolute top-1/2 size-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-surface ${fill}`}
          style={{ left: `${position * 100}%` } as CSSProperties}
        />
      </div>
      {showLabels && (
        <div className="relative mt-1 flex justify-end font-mono text-[10px] text-secondary">
          <span>{max}d · maior ciclo</span>
        </div>
      )}
    </div>
  );
}
