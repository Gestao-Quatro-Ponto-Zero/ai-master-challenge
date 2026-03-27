import { useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, ExternalLink } from "lucide-react";
import { ScoreCircle } from "@/components/dashboard/ScoreCircle";
import { formatUSD, getCategoryBadgeClasses } from "@/lib/formatters";
import type { ScoredDeal } from "@/types/deals";

function ScoreBadge({ deal }: { deal: ScoredDeal }) {
  const classes = getCategoryBadgeClasses(deal.category);
  return <Badge variant="outline" className={classes}>{deal.score}</Badge>;
}

export function PipelineCleanupSection({ deals, fromState }: { deals: ScoredDeal[]; fromState?: Record<string, string> }) {
  const [open, setOpen] = useState(false);

  if (deals.length === 0) return null;

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <Card>
        <CollapsibleTrigger className="w-full">
          <CardHeader className="cursor-pointer hover:bg-muted/30 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base text-destructive flex items-center gap-2">
                  🧹 Limpeza de Pipeline — {deals.length} deals há mais de 130 dias
                </CardTitle>
                <p className="text-xs text-muted-foreground mt-1 text-left">
                  Revise cada um e decida: resgatar com ação forte ou fechar como Lost.
                </p>
              </div>
              <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform shrink-0 ${open ? "rotate-180" : ""}`} />
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent>
            <div className="rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16">Score</TableHead>
                    <TableHead>Account</TableHead>
                    <TableHead>Produto</TableHead>
                    <TableHead className="text-right">Dias</TableHead>
                    <TableHead className="text-right">Expected Value</TableHead>
                    <TableHead className="w-10"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {deals.map((deal) => (
                    <TableRow key={deal.id}>
                      <TableCell><ScoreBadge deal={deal} /></TableCell>
                      <TableCell className="font-medium">{deal.account || "Sem conta"}</TableCell>
                      <TableCell>{deal.product}</TableCell>
                      <TableCell className="text-right">{deal.daysInPipeline}</TableCell>
                      <TableCell className="text-right">{formatUSD(deal.expectedValue)}</TableCell>
                      <TableCell>
                        <Link to={`/deal/${deal.id}`} state={fromState} className="text-primary hover:text-primary/80">
                          <ExternalLink className="h-4 w-4" />
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}
