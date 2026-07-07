"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { DealCard } from "@/components/deals/DealCard";
import { DealDetailDrawer } from "@/components/deals/DealDetailDrawer";
import { Badge } from "@/components/ui/badge";
import type { ScoredDeal } from "@/lib/types";
import { cn, formatMoney } from "@/lib/utils";

export function ScoreSection({
  icon,
  title,
  subtitle,
  accent,
  deals,
  showAgent = false,
  emptyMessage = "Nenhuma negociação nesta categoria.",
  defaultCollapsed = false,
  limit = 6,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  accent: string;
  deals: ScoredDeal[];
  showAgent?: boolean;
  emptyMessage?: string;
  defaultCollapsed?: boolean;
  limit?: number;
}) {
  const [expanded, setExpanded] = useState(!defaultCollapsed);
  const [showAll, setShowAll] = useState(false);
  const [selected, setSelected] = useState<ScoredDeal | null>(null);

  const totalValue = deals.reduce((s, d) => s + d.price, 0);
  const visible = showAll ? deals : deals.slice(0, limit);

  return (
    <section className="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3.5 hover:bg-slate-50 transition-colors duration-150 text-left"
      >
        <div
          className={cn(
            "h-9 w-9 shrink-0 rounded-lg grid place-items-center",
            accent,
          )}
        >
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <div className="font-semibold text-slate-900">{title}</div>
            <Badge
              variant="secondary"
              className="bg-slate-100 text-slate-700 border-0 tabular-nums"
            >
              {deals.length}
            </Badge>
          </div>
          <div className="text-xs text-slate-500 mt-0.5 truncate">
            {subtitle}
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm font-semibold text-slate-900 tabular-nums">
            {formatMoney(totalValue)}
          </div>
          <div className="text-[11px] text-slate-400">Valor em jogo</div>
        </div>
        <ChevronDown
          className={cn(
            "h-4 w-4 text-slate-400 ml-2",
            expanded && "rotate-180",
          )}
        />
      </button>

      {expanded && (
        <div className="border-t border-slate-100 p-3 bg-slate-50/40">
          {deals.length === 0 ? (
            <div className="text-center text-sm text-slate-400 py-8">
              {emptyMessage}
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2.5">
                {visible.map((d) => (
                  <DealCard
                    key={d.id}
                    deal={d}
                    showAgent={showAgent}
                    variant="compact"
                    onClick={() => setSelected(d)}
                  />
                ))}
              </div>
              {deals.length > limit && (
                <button
                  onClick={() => setShowAll((v) => !v)}
                  className="mt-3 mx-auto block text-sm font-medium text-blue-600 hover:text-blue-700"
                >
                  {showAll
                    ? "Mostrar menos"
                    : `Ver todas as ${deals.length}`}
                </button>
              )}
            </>
          )}
        </div>
      )}

      <DealDetailDrawer
        deal={selected}
        open={!!selected}
        onOpenChange={(o) => !o && setSelected(null)}
      />
    </section>
  );
}
