import { Search, X, SlidersHorizontal } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import type { Filters } from "@/hooks/useDeals";

interface Props {
  filters: Filters;
  setFilters: (f: Filters) => void;
  options: Record<string, string[]>;
  resetFilters: () => void;
}

const filterConfig: { key: keyof Filters; label: string }[] = [
  { key: "sales_agent", label: "Vendedor" },
  { key: "manager", label: "Gestor" },
  { key: "regional_office", label: "Região" },
  { key: "product", label: "Produto" },
  { key: "deal_stage", label: "Estágio" },
  { key: "priority_label", label: "Prioridade" },
];

export function FiltersBar({ filters, setFilters, options, resetFilters }: Props) {
  const activeCount = Object.entries(filters).filter(([k, v]) => k !== "search" && v).length;

  return (
    <div className="bg-card rounded-xl border shadow-sm">
      <div className="px-5 py-3 border-b flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-semibold text-foreground">Filtros</span>
          {activeCount > 0 && (
            <span className="inline-flex items-center justify-center h-5 w-5 rounded-full bg-primary text-primary-foreground text-[10px] font-bold">
              {activeCount}
            </span>
          )}
        </div>
        {(activeCount > 0 || filters.search) && (
          <Button variant="ghost" size="sm" onClick={resetFilters} className="text-xs text-muted-foreground hover:text-foreground h-7">
            <X className="h-3 w-3 mr-1" /> Limpar
          </Button>
        )}
      </div>
      <div className="p-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar conta, ID ou vendedor..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="pl-9 h-9 text-sm bg-background"
          />
        </div>
        {filterConfig.map(({ key, label }) => (
          <Select
            key={key}
            value={filters[key] || "all"}
            onValueChange={(v) => setFilters({ ...filters, [key]: v === "all" ? "" : v })}
          >
            <SelectTrigger className="h-9 text-sm bg-background">
              <SelectValue placeholder={label} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos — {label}</SelectItem>
              {(options[key] || []).map((o) => (
                <SelectItem key={o} value={o}>
                  {o}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ))}
      </div>
    </div>
  );
}
