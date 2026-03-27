import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { SortableTableHead } from "@/components/ui/sortable-table-head";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, ChevronLeft, ChevronRight } from "lucide-react";
import { formatUSD } from "@/lib/formatters";
import { useTableSort, sortData } from "@/hooks/useTableSort";
import type { ScoredDeal } from "@/types/deals";

export function DeadDealsTable({ deals }: { deals: ScoredDeal[] }) {
  const { sortConfig, toggleSort } = useTableSort("daysInPipeline", "desc");
  const sorted = useMemo(() => sortData(deals, sortConfig.key, sortConfig.direction), [deals, sortConfig]);
  const [page, setPage] = useState(0);
  const pageSize = 15;
  const totalPages = Math.ceil(sorted.length / pageSize);
  const paged = sorted.slice(page * pageSize, (page + 1) * pageSize);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-destructive" />
            Pipeline Envelhecido ({deals.length} deals &gt;130 dias)
          </CardTitle>
          {totalPages > 1 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Pág. {page + 1} de {totalPages}</span>
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="p-1 rounded-md border border-border text-muted-foreground hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed">
                <ChevronLeft className="h-3.5 w-3.5" />
              </button>
              <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page === totalPages - 1} className="p-1 rounded-md border border-border text-muted-foreground hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed">
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <SortableTableHead sortKey="account" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort}>Account</SortableTableHead>
              <SortableTableHead sortKey="agent" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort}>Vendedor</SortableTableHead>
              <SortableTableHead sortKey="product" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort}>Produto</SortableTableHead>
              <SortableTableHead sortKey="daysInPipeline" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-center">Dias</SortableTableHead>
              <SortableTableHead sortKey="salesPrice" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-right">Valor</SortableTableHead>
              <SortableTableHead sortKey="score" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-center">Score</SortableTableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paged.map(deal => (
              <TableRow key={deal.id} className="hover:bg-muted/50">
                <TableCell className="font-medium">{deal.account}</TableCell>
                <TableCell>{deal.agent}</TableCell>
                <TableCell>{deal.product}</TableCell>
                <TableCell className="text-center">
                  <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/30">
                    {deal.daysInPipeline}d
                  </Badge>
                </TableCell>
                <TableCell className="text-right">{formatUSD(deal.salesPrice)}</TableCell>
                <TableCell className="text-center">{deal.score}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
