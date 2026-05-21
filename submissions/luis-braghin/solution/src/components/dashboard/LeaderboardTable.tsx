import { useMemo, useState } from "react";
import { Table, TableBody, TableCell, TableHeader, TableRow } from "@/components/ui/table";
import { SortableTableHead } from "@/components/ui/sortable-table-head";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { formatPercent, formatUSD } from "@/lib/formatters";
import { useTableSort, sortData } from "@/hooks/useTableSort";
import { useDeals } from "@/hooks/useG4Data";
import type { Agent } from "@/types/deals";

interface LeaderboardTableProps {
  agents: Agent[];
  limit?: number;
  pageSize?: number;
}

export function LeaderboardTable({ agents, limit = 100, pageSize = 15 }: LeaderboardTableProps) {
  const { sortConfig, toggleSort } = useTableSort("winRate", "desc");
  const { data: allDeals = [] } = useDeals();
  const [page, setPage] = useState(0);

  const pipelineMap = useMemo(() => {
    const map: Record<string, number> = {};
    allDeals.forEach(d => {
      map[d.agent] = (map[d.agent] || 0) + d.salesPrice;
    });
    return map;
  }, [allDeals]);

  const sorted = useMemo(() => {
    const enriched = [...agents]
      .slice(0, limit)
      .map(a => ({ ...a, pipeline: pipelineMap[a.name] || 0 }));
    return sortData(enriched, sortConfig.key, sortConfig.direction);
  }, [agents, limit, sortConfig, pipelineMap]);

  const totalPages = Math.ceil(sorted.length / pageSize);
  const paged = sorted.slice(page * pageSize, (page + 1) * pageSize);

  return (
    <div className="space-y-3">
      <Table>
        <TableHeader>
          <TableRow>
            <SortableTableHead sortKey="name" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="w-12 text-center">#</SortableTableHead>
            <SortableTableHead sortKey="name" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort}>Vendedor</SortableTableHead>
            <SortableTableHead sortKey="manager" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort}>Manager</SortableTableHead>
            <SortableTableHead sortKey="winRate" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-right">Win Rate</SortableTableHead>
            <SortableTableHead sortKey="pipeline" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-right">Pipeline</SortableTableHead>
            <SortableTableHead sortKey="totalRevenue" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-right">Receita</SortableTableHead>
            <SortableTableHead sortKey="activeDeals" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-right">Deals Ativos</SortableTableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {paged.map((agent, i) => (
            <TableRow key={agent.name} className="hover:bg-muted/50">
              <TableCell className="text-center font-medium text-muted-foreground">{page * pageSize + i + 1}</TableCell>
              <TableCell className="font-medium">{agent.name}</TableCell>
              <TableCell className="text-muted-foreground">{agent.manager}</TableCell>
              <TableCell className="text-right">
                <Badge
                  variant="outline"
                  className={
                    agent.winRate >= 0.65
                      ? "bg-success/10 text-success border-success/30"
                      : agent.winRate >= 0.58
                      ? "bg-warning/10 text-warning border-warning/30"
                      : "bg-destructive/10 text-destructive border-destructive/30"
                  }
                >
                  {formatPercent(agent.winRate)}
                </Badge>
              </TableCell>
              <TableCell className="text-right">{formatUSD(agent.pipeline)}</TableCell>
              <TableCell className="text-right">{formatUSD(agent.totalRevenue)}</TableCell>
              <TableCell className="text-right">{agent.activeDeals}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {totalPages > 1 && (
        <div className="flex items-center justify-end gap-2">
          <span className="text-xs text-muted-foreground">
            Pág. {page + 1} de {totalPages} — {sorted.length} vendedores
          </span>
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="p-1 rounded-md border border-border text-muted-foreground hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page === totalPages - 1}
            className="p-1 rounded-md border border-border text-muted-foreground hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
