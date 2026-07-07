"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, Search, Sparkles, XCircle } from "lucide-react";
import { ClosedDealDrawer } from "@/components/deals/ClosedDealDrawer";
import { DealDetailDrawer } from "@/components/deals/DealDetailDrawer";
import { FunnelDealCard } from "@/components/deals/FunnelDealCard";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ClosedDeal, ScoredDeal } from "@/lib/types";
import { cn, formatMoney } from "@/lib/utils";

const OPEN_STAGES = ["Prospecting", "Engaging"] as const;
const CLOSED_LIMIT = 30;

const STAGE_META: Record<
  string,
  { label: string; icon: React.ReactNode; header: string; accent: string; text: string; border: string }
> = {
  Prospecting: {
    label: "Prospecção",
    icon: <Search className="h-3.5 w-3.5" />,
    header: "bg-slate-50",
    accent: "border-slate-200",
    text: "text-slate-700",
    border: "border-slate-200",
  },
  Engaging: {
    label: "Em negociação",
    icon: <Sparkles className="h-3.5 w-3.5" />,
    header: "bg-blue-50",
    accent: "border-blue-200",
    text: "text-blue-700",
    border: "border-blue-200",
  },
  Won: {
    label: "Vendas fechadas",
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    header: "bg-emerald-50",
    accent: "border-emerald-200",
    text: "text-emerald-700",
    border: "border-emerald-200",
  },
  Lost: {
    label: "Perdidas",
    icon: <XCircle className="h-3.5 w-3.5" />,
    header: "bg-red-50",
    accent: "border-red-200",
    text: "text-red-700",
    border: "border-red-200",
  },
};

export function FunnelBoard({
  openDeals,
  closedDeals,
  showAgent = true,
}: {
  openDeals: ScoredDeal[];
  closedDeals: ClosedDeal[];
  showAgent?: boolean;
}) {
  const [selectedOpen, setSelectedOpen] = useState<ScoredDeal | null>(null);
  const [selectedClosed, setSelectedClosed] = useState<ClosedDeal | null>(null);
  const [wonExpanded, setWonExpanded] = useState(false);
  const [lostExpanded, setLostExpanded] = useState(false);

  const grouped = useMemo(() => {
    const byStage = {
      Prospecting: openDeals
        .filter((d) => d.stage === "Prospecting")
        .sort((a, b) => b.score - a.score),
      Engaging: openDeals
        .filter((d) => d.stage === "Engaging")
        .sort((a, b) => b.score - a.score),
      Won: closedDeals
        .filter((d) => d.stage === "Won")
        .sort((a, b) => (b.closeValue || b.price) - (a.closeValue || a.price)),
      Lost: closedDeals
        .filter((d) => d.stage === "Lost")
        .sort((a, b) => b.price - a.price),
    };
    return byStage;
  }, [openDeals, closedDeals]);

  const columns: Array<{
    key: keyof typeof grouped;
    items: (ScoredDeal | ClosedDeal)[];
    fullCount: number;
    totalValue: number;
    isClosed: boolean;
    expanded?: boolean;
    setExpanded?: (v: boolean) => void;
  }> = [
    {
      key: "Prospecting",
      items: grouped.Prospecting,
      fullCount: grouped.Prospecting.length,
      totalValue: grouped.Prospecting.reduce((s, d) => s + d.price, 0),
      isClosed: false,
    },
    {
      key: "Engaging",
      items: grouped.Engaging,
      fullCount: grouped.Engaging.length,
      totalValue: grouped.Engaging.reduce((s, d) => s + d.price, 0),
      isClosed: false,
    },
    {
      key: "Won",
      items: wonExpanded ? grouped.Won : grouped.Won.slice(0, CLOSED_LIMIT),
      fullCount: grouped.Won.length,
      totalValue: grouped.Won.reduce(
        (s, d) => s + ((d as ClosedDeal).closeValue || d.price),
        0,
      ),
      isClosed: true,
      expanded: wonExpanded,
      setExpanded: setWonExpanded,
    },
    {
      key: "Lost",
      items: lostExpanded
        ? grouped.Lost
        : grouped.Lost.slice(0, CLOSED_LIMIT),
      fullCount: grouped.Lost.length,
      totalValue: grouped.Lost.reduce((s, d) => s + d.price, 0),
      isClosed: true,
      expanded: lostExpanded,
      setExpanded: setLostExpanded,
    },
  ];

  return (
    <>
      <div className="grid grid-cols-4 gap-4">
        {columns.map((col) => {
          const meta = STAGE_META[col.key];
          const hidden = col.fullCount - col.items.length;
          return (
            <div
              key={col.key}
              className={cn(
                "rounded-xl border bg-slate-50/50 flex flex-col min-h-[300px]",
                meta.border,
              )}
            >
              <div
                className={cn(
                  "px-4 py-3 rounded-t-xl border-b",
                  meta.header,
                  meta.border,
                )}
              >
                <div className="flex items-center justify-between">
                  <div
                    className={cn(
                      "text-sm font-semibold flex items-center gap-1.5",
                      meta.text,
                    )}
                  >
                    {meta.icon}
                    {meta.label}
                  </div>
                  <span
                    className={cn(
                      "text-xs font-medium tabular-nums",
                      meta.text,
                    )}
                  >
                    {col.fullCount}
                  </span>
                </div>
                <div
                  className={cn(
                    "text-[11px] mt-0.5 font-medium",
                    meta.text,
                    "opacity-80",
                  )}
                >
                  {formatMoney(col.totalValue)}
                  {col.isClosed && (
                    <span className="ml-1 opacity-70">
                      {col.key === "Won" ? "· fechado" : "· potencial perdido"}
                    </span>
                  )}
                </div>
              </div>

              <ScrollArea className="flex-1 max-h-[calc(100vh-260px)]">
                <div className="p-2.5 space-y-2">
                  {col.items.length === 0 && (
                    <div className="text-center text-xs text-slate-400 py-6">
                      Nenhuma negociação
                    </div>
                  )}
                  {col.items.map((d) => (
                    <FunnelDealCard
                      key={d.id}
                      deal={d}
                      showAgent={showAgent}
                      onClick={() => {
                        if (col.isClosed) setSelectedClosed(d as ClosedDeal);
                        else setSelectedOpen(d as ScoredDeal);
                      }}
                    />
                  ))}
                  {col.isClosed && hidden > 0 && !col.expanded && (
                    <button
                      onClick={() => col.setExpanded?.(true)}
                      className="w-full mt-2 py-2 text-xs font-medium text-slate-500 hover:text-blue-600 border border-dashed border-slate-300 rounded-md hover:border-blue-300 transition-colors duration-150"
                    >
                      Ver todas as {col.fullCount} · {hidden} restantes
                    </button>
                  )}
                  {col.isClosed && col.expanded && (
                    <button
                      onClick={() => col.setExpanded?.(false)}
                      className="w-full mt-2 py-2 text-xs font-medium text-slate-500 hover:text-blue-600 border border-dashed border-slate-300 rounded-md transition-colors duration-150"
                    >
                      Mostrar apenas top {CLOSED_LIMIT}
                    </button>
                  )}
                </div>
              </ScrollArea>
            </div>
          );
        })}
      </div>

      <DealDetailDrawer
        deal={selectedOpen}
        open={!!selectedOpen}
        onOpenChange={(o) => !o && setSelectedOpen(null)}
      />
      <ClosedDealDrawer
        deal={selectedClosed}
        open={!!selectedClosed}
        onOpenChange={(o) => !o && setSelectedClosed(null)}
      />
    </>
  );
}
