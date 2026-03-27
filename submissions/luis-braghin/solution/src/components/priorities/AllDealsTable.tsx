import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { SortableTableHead } from "@/components/ui/sortable-table-head";
import { Badge } from "@/components/ui/badge";
import { ExternalLink } from "lucide-react";
import { formatUSD, getCategoryBadgeClasses } from "@/lib/formatters";
import { useTableSort, sortData } from "@/hooks/useTableSort";
import type { ScoredDeal } from "@/types/deals";

function ScoreBadge({ deal }: { deal: ScoredDeal }) {
  const classes = getCategoryBadgeClasses(deal.category);
  return <Badge variant="outline" className={classes}>{deal.score}</Badge>;
}

function StageBadge({ stage }: { stage: string }) {
  if (stage === "Engaging") {
    return <Badge className="bg-primary/15 text-primary border-primary/30 text-xs">{stage}</Badge>;
  }
  return <Badge variant="secondary" className="text-xs">{stage}</Badge>;
}

function formatDays(days: number, stage: string): string {
  if (stage === "Prospecting" && days === 0) return "Novo";
  return `${days}d`;
}

export function AllDealsTable({ deals, fromState }: { deals: ScoredDeal[]; fromState?: Record<string, string> }) {
  const { sortConfig, toggleSort } = useTableSort("score", "desc");
  const sorted = useMemo(() => sortData(deals, sortConfig.key, sortConfig.direction), [deals, sortConfig]);

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <SortableTableHead sortKey="score" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="w-16">Score</SortableTableHead>
            <SortableTableHead sortKey="account" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort}>Account</SortableTableHead>
            <SortableTableHead sortKey="product" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort}>Produto</SortableTableHead>
            <SortableTableHead sortKey="stage" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort}>Stage</SortableTableHead>
            <SortableTableHead sortKey="daysInPipeline" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-right">Dias</SortableTableHead>
            <SortableTableHead sortKey="expectedValue" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-right">Expected Value</SortableTableHead>
            <SortableTableHead sortKey="salesPrice" currentSortKey={sortConfig.key} direction={sortConfig.direction} onSort={toggleSort} className="text-right">Sales Price</SortableTableHead>
            <TableHead className="w-10"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((deal) => (
            <TableRow key={deal.id}>
              <TableCell><ScoreBadge deal={deal} /></TableCell>
              <TableCell className="font-medium">{deal.account || "Sem conta"}</TableCell>
              <TableCell>{deal.product}</TableCell>
              <TableCell>
                <StageBadge stage={deal.stage} />
              </TableCell>
              <TableCell className="text-right">{formatDays(deal.daysInPipeline, deal.stage)}</TableCell>
              <TableCell className="text-right">{formatUSD(deal.expectedValue)}</TableCell>
              <TableCell className="text-right">{formatUSD(deal.salesPrice)}</TableCell>
              <TableCell>
                <Link to={`/deal/${deal.id}`} state={fromState} className="text-primary hover:text-primary/80">
                  <ExternalLink className="h-4 w-4" />
                </Link>
              </TableCell>
            </TableRow>
          ))}
          {sorted.length === 0 && (
            <TableRow>
              <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                Nenhum deal encontrado.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
