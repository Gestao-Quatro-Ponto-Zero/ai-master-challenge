import { useState, type ReactNode } from "react";
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { paginate } from "@/lib/pagination";
import { formatNumber } from "@/lib/format";
import type { Deal } from "@/hooks/useDeals";
import { cn } from "@/lib/utils";
import { EmptyState } from "./States";

export type Column = {
  key: string;
  header: string;
  align?: "right";
  cell: (d: Deal) => ReactNode;
};

export function DealTable({ deals, columns, onSelect, empty }: {
  deals: Deal[];
  columns: Column[];
  onSelect: (d: Deal) => void;
  empty: ReactNode;
}) {
  const [requestedPage, setPage] = useState(1);
  const { page, totalPages, start, items: visible } = paginate(deals, requestedPage);
  if (!deals.length) return typeof empty === "string" ? <EmptyState message={empty} /> : <>{empty}</>;
  return (
    <div>
      <div className="w-full overflow-x-auto">
        <table className="w-full min-w-[720px] font-numeric text-sm tabular-nums">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              {columns.map((c) => (
                <th key={c.key} className={cn("whitespace-nowrap px-3 py-2 font-medium", c.align === "right" && "text-right")}>
                  {c.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((d) => (
              <tr
                key={d.opportunity_id}
                tabIndex={0}
                onClick={() => onSelect(d)}
                onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onSelect(d))}
                className="cursor-pointer border-b border-border transition-colors last:border-0 hover:bg-muted focus:bg-muted focus:outline-none"
              >
                {columns.map((c) => (
                  <td key={c.key} className={cn("px-3 py-3 align-middle", c.align === "right" && "text-right tabular-nums")}>
                    {c.cell(d)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <nav aria-label="Paginação das oportunidades" className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-3 py-3 text-sm text-muted-foreground">
        <span className="font-numeric tabular-nums">{formatNumber(start + 1)}–{formatNumber(start + visible.length)} de {formatNumber(deals.length)} oportunidades</span>
        <div className="flex items-center gap-2">
          <span className="mr-1 font-numeric tabular-nums" aria-live="polite">Página {page} de {totalPages}</span>
          <Button variant="outline" size="icon" aria-label="Primeira página" title="Primeira página" disabled={page === 1} onClick={() => setPage(1)}><ChevronsLeft /></Button>
          <Button variant="outline" size="icon" aria-label="Página anterior" title="Página anterior" disabled={page === 1} onClick={() => setPage(page - 1)}><ChevronLeft /></Button>
          <Button variant="outline" size="icon" aria-label="Próxima página" title="Próxima página" disabled={page === totalPages} onClick={() => setPage(page + 1)}><ChevronRight /></Button>
          <Button variant="outline" size="icon" aria-label="Última página" title="Última página" disabled={page === totalPages} onClick={() => setPage(totalPages)}><ChevronsRight /></Button>
        </div>
      </nav>
    </div>
  );
}

