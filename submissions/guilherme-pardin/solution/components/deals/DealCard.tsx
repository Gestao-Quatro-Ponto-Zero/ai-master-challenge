"use client";

import { AlertTriangle, ArrowRightLeft } from "lucide-react";
import type { ScoredDeal } from "@/lib/types";
import { avatarBg, cn, formatMoney, initials, stageLabel } from "@/lib/utils";
import { ScoreBar } from "./ScoreBar";
import { TierBadge } from "./TierBadge";

export function DealCard({
  deal,
  onClick,
  showAgent = false,
  variant = "default",
}: {
  deal: ScoredDeal;
  onClick?: () => void;
  showAgent?: boolean;
  variant?: "default" | "compact";
}) {
  const outOfZone = deal.isReallocated && !showAgent;
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full text-left bg-white rounded-lg border border-slate-200 hover:border-blue-300 transition-colors duration-150 p-3 space-y-2.5 shadow-[var(--shadow-card)] hover:shadow-[var(--shadow-card-hover)]",
        variant === "compact" && "p-2.5 space-y-2",
      )}
    >
      <div className="flex items-start gap-2.5">
        <div
          className={cn(
            "h-9 w-9 shrink-0 rounded-md grid place-items-center text-white text-[11px] font-semibold",
            avatarBg(deal.account),
          )}
        >
          {initials(deal.account)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="font-medium text-sm text-slate-900 truncate">
            {deal.account}
          </div>
          <div className="text-[11px] text-slate-500 truncate">
            {deal.product} · {deal.sector}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-sm font-semibold text-slate-900 tabular-nums">
            {formatMoney(deal.price)}
          </div>
          <div className="text-[10px] text-slate-400 uppercase tracking-wide">
            {stageLabel[deal.stage] ?? deal.stage}
          </div>
        </div>
      </div>

      <ScoreBar score={deal.score} tier={deal.tier} />

      <div className="flex items-center justify-between gap-2">
        <TierBadge tier={deal.tier} className="text-[11px]" />
        {showAgent && (
          <span className="text-[11px] text-slate-500 truncate">
            {deal.currentAgent}
          </span>
        )}
        {outOfZone && (
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded px-1.5 py-0.5">
            <AlertTriangle className="h-3 w-3" />
            Fora da zona forte
          </span>
        )}
      </div>

      {deal.isReallocated && (
        <div className="flex items-center gap-1.5 text-[11px] text-blue-700 bg-blue-50 rounded px-2 py-1 border border-blue-100">
          <ArrowRightLeft className="h-3 w-3 shrink-0" />
          <span className="truncate">
            Sugestão: <span className="font-medium">{deal.optimalAgent}</span>
          </span>
        </div>
      )}
    </button>
  );
}
