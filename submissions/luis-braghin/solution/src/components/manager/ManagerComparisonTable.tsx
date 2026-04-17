import { useMemo } from "react";
import { Table, TableBody, TableCell, TableHeader, TableRow } from "@/components/ui/table";
import { SortableTableHead } from "@/components/ui/sortable-table-head";
import { Badge } from "@/components/ui/badge";
import { formatUSD, formatPercent } from "@/lib/formatters";
import { useTableSort, sortData } from "@/hooks/useTableSort";
import type { ManagerStats } from "./types";

export function ManagerComparisonTable({ stats }: { stats: ManagerStats[] }) {
  const { sortConfig, toggleSort } = useTableSort("ev", "desc");
  const sorted = useMemo(() => sortData(stats, sortConfig.key, sortConfig.direction), [stats, sortConfig]);

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <SortableTableHead sortKey="name" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort}>Manager</SortableTableHead>
          <SortableTableHead sortKey="agents" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-center">Vendedores</SortableTableHead>
          <SortableTableHead sortKey="totalDeals" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-center">Deals</SortableTableHead>
          <SortableTableHead sortKey="pipeline" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-right">Pipeline</SortableTableHead>
          <SortableTableHead sortKey="ev" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-right">Expected Value</SortableTableHead>
          <SortableTableHead sortKey="avgWinRate" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-right">Win Rate Média</SortableTableHead>
          <SortableTableHead sortKey="avgScore" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-right">Score Médio</SortableTableHead>
          <SortableTableHead sortKey="hotWarm" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-center">HOT+WARM</SortableTableHead>
          <SortableTableHead sortKey="over130d" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-center">Envelhecidos</SortableTableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sorted.map(m => (
          <TableRow key={m.name} className="hover:bg-muted/50">
            <TableCell className="font-semibold">{m.name}</TableCell>
            <TableCell className="text-center">{m.agents}</TableCell>
            <TableCell className="text-center">{m.totalDeals}</TableCell>
            <TableCell className="text-right">{formatUSD(m.pipeline)}</TableCell>
            <TableCell className="text-right font-medium">{formatUSD(m.ev)}</TableCell>
            <TableCell className="text-right">
              <Badge variant="outline" className={
                m.avgWinRate >= 0.65
                  ? "bg-success/10 text-success border-success/30"
                  : m.avgWinRate >= 0.58
                  ? "bg-warning/10 text-warning border-warning/30"
                  : "bg-destructive/10 text-destructive border-destructive/30"
              }>
                {formatPercent(m.avgWinRate)}
              </Badge>
            </TableCell>
            <TableCell className="text-right">{m.avgScore.toFixed(0)}</TableCell>
            <TableCell className="text-center">
              <Badge variant="outline" className="bg-success/10 text-success border-success/30">{m.hotWarm}</Badge>
            </TableCell>
            <TableCell className="text-center">
              {m.over130d > 0 ? (
                <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/30">{m.over130d}</Badge>
              ) : (
                <span className="text-muted-foreground">0</span>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
