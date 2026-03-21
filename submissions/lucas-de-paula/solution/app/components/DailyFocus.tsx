"use client";

import { type ScoredDeal } from "@/lib/scoring";
import { InfoTooltip } from "./InfoTooltip";

interface DailyFocusProps {
  deals: ScoredDeal[];
  onSelectDeal: (deal: ScoredDeal) => void;
}

function urgencyColor(days: number) {
  if (days > 90) return { border: "border-red-500/40", bg: "bg-red-500/5", badge: "bg-red-500/15 text-red-400", label: "Zumbi" };
  if (days > 30) return { border: "border-amber-500/40", bg: "bg-amber-500/5", badge: "bg-amber-500/15 text-amber-400", label: "Em risco" };
  return { border: "border-emerald-500/40", bg: "bg-emerald-500/5", badge: "bg-emerald-500/15 text-emerald-400", label: "Saudável" };
}

export function DailyFocus({ deals, onSelectDeal }: DailyFocusProps) {
  // Top 3: Engaging deals ordered by score desc, prioritising at-risk (31-90d)
  const atRisk = deals
    .filter((d) => d.deal_stage === "Engaging" && d.days_in_stage > 30 && d.days_in_stage <= 90)
    .sort((a, b) => b.score - a.score);

  const zombies = deals
    .filter((d) => d.deal_stage === "Engaging" && d.days_in_stage > 90)
    .sort((a, b) => b.score - a.score);

  const healthy = deals
    .filter((d) => d.deal_stage === "Engaging" && d.days_in_stage <= 30)
    .sort((a, b) => b.score - a.score);

  const top3: ScoredDeal[] = [...atRisk, ...zombies, ...healthy].slice(0, 3);

  if (top3.length === 0) return null;

  return (
    <div className="bg-gray-900/60 border border-violet-500/20 rounded-2xl p-4 sm:p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-violet-400 text-sm font-bold uppercase tracking-wider">Foco do Dia</span>
        <InfoTooltip text={`Top ${top3.length} deals que precisam de ação hoje — priorizados por urgência (Em risco 31–90d primeiro) e score. Filtre por vendedor para ver o foco individual de cada um. Clique em qualquer card para ver o detalhamento completo.`} />
        <span className="text-xs text-gray-500">— {top3.length} deals críticos</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {top3.map((deal, i) => {
          const style = urgencyColor(deal.days_in_stage);
          return (
            <button
              key={deal.opportunity_id}
              onClick={() => onSelectDeal(deal)}
              className={`text-left rounded-xl border ${style.border} ${style.bg} p-4 hover:brightness-110 transition-all space-y-2`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-[10px] text-gray-500 font-mono">#{i + 1}</span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${style.badge}`}>
                  {style.label}
                </span>
              </div>

              <div>
                <p className="text-white font-semibold text-sm leading-tight truncate">{deal.account || "—"}</p>
                <p className="text-gray-400 text-xs truncate">{deal.product || "—"}</p>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">{deal.days_in_stage}d no stage</span>
                <span className="text-sm font-black text-violet-300">{deal.score}pts</span>
              </div>

              <p className="text-[10px] text-gray-500 truncate">{deal.sales_agent}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
