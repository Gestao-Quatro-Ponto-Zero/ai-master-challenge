"use client";

import { Clock, User } from "lucide-react";
import { ScoreBar } from "./ScoreBar";
import { tierEmoji, tierLabel } from "@/lib/data";
import type { ClosedDeal, ScoredDeal } from "@/lib/types";
import { avatarBg, cn, formatMoney, initials, tierColor } from "@/lib/utils";

type AnyDeal = ScoredDeal | ClosedDeal;

function isClosed(d: AnyDeal): d is ClosedDeal {
  return (d as ClosedDeal).closeValue !== undefined;
}

export function FunnelDealCard({
  deal,
  onClick,
  showAgent = true,
}: {
  deal: AnyDeal;
  onClick?: () => void;
  showAgent?: boolean;
}) {
  const closed = isClosed(deal);
  const value = closed ? deal.closeValue || deal.price : deal.price;
  const agent = closed ? deal.agent : deal.currentAgent;

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full text-left bg-white rounded-lg border border-slate-200 hover:border-blue-300 transition-colors duration-150 p-3 space-y-2 shadow-[var(--shadow-card)] hover:shadow-[var(--shadow-card-hover)]"
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
            <span className="font-medium text-slate-700">{deal.product}</span>{" "}
            · {deal.sector}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-sm font-semibold text-slate-900 tabular-nums">
            {formatMoney(value)}
          </div>
          {closed && deal.stage === "Won" && deal.closeValue !== deal.price && (
            <div className="text-[10px] text-emerald-600 tabular-nums">
              lista {formatMoney(deal.price)}
            </div>
          )}
        </div>
      </div>

      {showAgent && (
        <div className="flex items-center justify-between gap-2 text-[11px]">
          <span className="inline-flex items-center gap-1 text-slate-500 truncate max-w-[60%]">
            <User className="h-3 w-3 shrink-0" />
            <span className="truncate">{agent}</span>
          </span>
          {closed && deal.daysToClose !== null && (
            <span className="inline-flex items-center gap-1 text-slate-400 tabular-nums">
              <Clock className="h-3 w-3" />
              {deal.daysToClose}d
            </span>
          )}
        </div>
      )}

      {!closed && (
        <div className="flex items-center gap-2 pt-1 border-t border-slate-100">
          <ScoreBar
            score={deal.score}
            tier={deal.tier}
            showLabel={false}
            className="flex-1"
          />
          <span className="text-xs font-semibold text-slate-700 tabular-nums w-6 text-right">
            {deal.score}
          </span>
          <span
            className={cn(
              "inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-medium border",
              tierColor[deal.tier].bg,
              tierColor[deal.tier].text,
              tierColor[deal.tier].border,
            )}
          >
            <span>{tierEmoji[deal.tier]}</span>
            {tierLabel[deal.tier]}
          </span>
        </div>
      )}
    </button>
  );
}
