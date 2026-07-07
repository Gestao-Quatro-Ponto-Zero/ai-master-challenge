"use client";

import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { DealDetailDrawer } from "@/components/deals/DealDetailDrawer";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ScoredDeal } from "@/lib/types";
import { avatarBg, cn, formatMoney, formatPercent, initials } from "@/lib/utils";

export function ReallocationTable({ deals }: { deals: ScoredDeal[] }) {
  const [selected, setSelected] = useState<ScoredDeal | null>(null);
  const sorted = [...deals].sort(
    (a, b) => b.optimalAgentWr - b.currentAgentWr - (a.optimalAgentWr - a.currentAgentWr),
  );
  return (
    <>
      <ScrollArea className="h-[520px] rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-50 border-b border-slate-200 text-[11px] uppercase tracking-wide text-slate-500">
            <tr>
              <th className="text-left px-4 py-2.5 font-medium">Empresa</th>
              <th className="text-left px-3 py-2.5 font-medium">Setor</th>
              <th className="text-left px-3 py-2.5 font-medium">Produto</th>
              <th className="text-right px-3 py-2.5 font-medium">Valor</th>
              <th className="text-left px-3 py-2.5 font-medium">Atual</th>
              <th className="text-left px-3 py-2.5 font-medium">Ideal</th>
              <th className="text-right px-4 py-2.5 font-medium">Ganho</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sorted.map((d) => {
              const delta = d.optimalAgentWr - d.currentAgentWr;
              return (
                <tr
                  key={d.id}
                  onClick={() => setSelected(d)}
                  className="hover:bg-slate-50 cursor-pointer"
                >
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <div
                        className={cn(
                          "h-6 w-6 shrink-0 rounded grid place-items-center text-white text-[10px] font-semibold",
                          avatarBg(d.account),
                        )}
                      >
                        {initials(d.account)}
                      </div>
                      <span className="text-slate-900 font-medium truncate max-w-[160px]">
                        {d.account}
                      </span>
                    </div>
                  </td>
                  <td className="px-3 py-2.5 text-slate-600 whitespace-nowrap">
                    {d.sector}
                  </td>
                  <td className="px-3 py-2.5 text-slate-600 whitespace-nowrap">
                    {d.product}
                  </td>
                  <td className="px-3 py-2.5 text-right tabular-nums font-medium text-slate-900">
                    {formatMoney(d.price)}
                  </td>
                  <td className="px-3 py-2.5 text-slate-700 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <span className="truncate max-w-[110px]">
                        {d.currentAgent}
                      </span>
                      <span className="text-[10px] text-slate-400 tabular-nums">
                        {formatPercent(d.currentAgentWr)}
                      </span>
                    </div>
                  </td>
                  <td className="px-3 py-2.5 whitespace-nowrap">
                    <div className="flex items-center gap-1.5 text-blue-700">
                      <ArrowRight className="h-3 w-3 shrink-0" />
                      <span className="truncate max-w-[110px] font-medium">
                        {d.optimalAgent}
                      </span>
                      <span className="text-[10px] text-blue-500 tabular-nums">
                        {formatPercent(d.optimalAgentWr)}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <Badge
                      variant="outline"
                      className={cn(
                        "tabular-nums font-medium",
                        delta >= 0.25
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : delta >= 0.1
                            ? "bg-blue-50 text-blue-700 border-blue-200"
                            : "bg-slate-50 text-slate-600 border-slate-200",
                      )}
                    >
                      +{(delta * 100).toFixed(0)} p.p.
                    </Badge>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </ScrollArea>
      <DealDetailDrawer
        deal={selected}
        open={!!selected}
        onOpenChange={(o) => !o && setSelected(null)}
      />
    </>
  );
}
