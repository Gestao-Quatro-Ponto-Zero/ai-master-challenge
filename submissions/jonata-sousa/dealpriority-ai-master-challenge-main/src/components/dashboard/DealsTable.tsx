import { ArrowUpDown, ChevronRight, ChevronsLeft, ChevronLeft, ChevronRight as ChevronRightIcon, ChevronsRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PriorityBadge } from "./PriorityBadge";
import type { Deal } from "@/types/deal";

interface Props {
  deals: Deal[];
  sortAsc: boolean;
  onToggleSort: () => void;
  onSelect: (d: Deal) => void;
  selected?: Deal | null;
  page: number;
  totalPages: number;
  totalFiltered: number;
  pageSize: number;
  onPageChange: (p: number) => void;
  onPageSizeChange: (s: number) => void;
}

function ScorePill({ score }: { score: number }) {
  const color =
    score >= 40 ? "bg-primary/10 text-primary border-primary/20"
    : score >= 25 ? "bg-warning/10 text-warning border-warning/20"
    : "bg-muted text-muted-foreground border-border";

  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-bold tabular-nums ${color}`}>
      {score.toFixed(1)}
    </span>
  );
}

export function DealsTable({ deals, sortAsc, onToggleSort, onSelect, selected, page, totalPages, totalFiltered, pageSize, onPageChange, onPageSizeChange }: Props) {
  return (
    <div className="bg-card rounded-xl border shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/40">
              <Th>Conta</Th>
              <Th>Vendedor</Th>
              <Th className="hidden md:table-cell">Gestor</Th>
              <Th className="hidden lg:table-cell">Região</Th>
              <Th className="hidden lg:table-cell">Produto</Th>
              <Th className="hidden md:table-cell">Estágio</Th>
              <Th className="text-center">
                <Button variant="ghost" size="sm" onClick={onToggleSort} className="text-[11px] uppercase tracking-widest font-semibold text-muted-foreground hover:text-foreground -ml-3 h-7">
                  Score <ArrowUpDown className="h-3 w-3 ml-1" />
                </Button>
              </Th>
              <Th>Prioridade</Th>
              <Th className="hidden xl:table-cell">Ação Recomendada</Th>
              <Th className="w-8" />
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {deals.length === 0 && (
              <tr>
                <td colSpan={10} className="text-center py-16 text-muted-foreground">
                  Nenhuma oportunidade encontrada com os filtros atuais.
                </td>
              </tr>
            )}
            {deals.map((d) => {
              const isSelected = selected?.opportunity_id === d.opportunity_id;
              return (
                <tr
                  key={d.opportunity_id}
                  onClick={() => onSelect(d)}
                  className={`cursor-pointer transition-colors duration-100 group ${
                    isSelected
                      ? "bg-accent ring-1 ring-inset ring-primary/20"
                      : "hover:bg-accent/40"
                  }`}
                >
                  <td className="px-5 py-3.5 font-semibold text-foreground">{d.account || "—"}</td>
                  <td className="px-5 py-3.5 text-foreground">{d.sales_agent}</td>
                  <td className="px-5 py-3.5 text-muted-foreground hidden md:table-cell">{d.manager}</td>
                  <td className="px-5 py-3.5 text-muted-foreground hidden lg:table-cell">{d.regional_office}</td>
                  <td className="px-5 py-3.5 text-muted-foreground hidden lg:table-cell">{d.product}</td>
                  <td className="px-5 py-3.5 text-muted-foreground hidden md:table-cell">{d.deal_stage}</td>
                  <td className="px-5 py-3.5 text-center">
                    <ScorePill score={d.priority_score} />
                  </td>
                  <td className="px-5 py-3.5">
                    <PriorityBadge label={d.priority_label} />
                  </td>
                  <td className="px-5 py-3.5 text-muted-foreground text-xs hidden xl:table-cell max-w-[220px] truncate">
                    {d.recommended_action}
                  </td>
                  <td className="px-3 py-3.5">
                    <ChevronRight className="h-4 w-4 text-muted-foreground/40 group-hover:text-primary transition-colors" />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination footer */}
      <div className="px-5 py-3 border-t bg-muted/30 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">Linhas por página</span>
          <Select value={String(pageSize)} onValueChange={(v) => onPageSizeChange(Number(v))}>
            <SelectTrigger className="h-8 w-[70px] text-xs bg-background">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {[10, 25, 50, 100].map((s) => (
                <SelectItem key={s} value={String(s)}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">{totalFiltered}</span> resultado{totalFiltered !== 1 ? "s" : ""}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <span className="text-xs text-muted-foreground mr-2">
            Página <span className="font-semibold text-foreground">{page}</span> de{" "}
            <span className="font-semibold text-foreground">{totalPages}</span>
          </span>
          <Button variant="outline" size="icon" className="h-8 w-8" disabled={page <= 1} onClick={() => onPageChange(1)}>
            <ChevronsLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
            <ChevronRightIcon className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8" disabled={page >= totalPages} onClick={() => onPageChange(totalPages)}>
            <ChevronsRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

function Th({ children, className = "" }: { children?: React.ReactNode; className?: string }) {
  return (
    <th className={`text-left px-5 py-3 text-[11px] font-semibold text-muted-foreground uppercase tracking-widest ${className}`}>
      {children}
    </th>
  );
}
