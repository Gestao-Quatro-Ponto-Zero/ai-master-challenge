import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScoreCircle } from "./ScoreCircle";
import { getCategoryBadgeClasses, formatUSD } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { Building2, User, Package, Clock, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import type { ScoredDeal } from "@/types/deals";

interface DealCardProps {
  deal: ScoredDeal;
  linkState?: Record<string, unknown>;
}

export function DealCard({ deal, linkState }: DealCardProps) {
  return (
    <Link to={`/deal/${deal.id}`} state={linkState}>
      <Card className="p-4 transition-all hover:shadow-md hover:border-primary/20 cursor-pointer">
        <div className="flex items-start gap-4">
          <ScoreCircle score={deal.score} category={deal.category} />
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-semibold truncate">{deal.account}</h3>
              <div className="flex items-center gap-2 shrink-0">
                <Badge variant="outline" className={getCategoryBadgeClasses(deal.category)}>
                  {deal.category}
                </Badge>
                {deal.stage && (
                  <Badge variant="secondary" className={cn("text-[10px]", deal.stage === "Engaging" && "bg-primary/10 text-primary border-primary/30")}>
                    {deal.stage}
                  </Badge>
                )}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Package className="h-3 w-3" /> {deal.product}
              </span>
              <span className="flex items-center gap-1">
                <User className="h-3 w-3" /> {deal.agent}
              </span>
              <span className="flex items-center gap-1">
                <Building2 className="h-3 w-3" /> {deal.sector}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" /> {deal.daysInPipeline}d
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div className="text-sm">
                <span className="text-muted-foreground">Valor: </span>
                <span className="font-medium">{formatUSD(deal.salesPrice)}</span>
                <span className="text-muted-foreground mx-1">→</span>
                <span className="font-medium text-primary">{formatUSD(deal.expectedValue)}</span>
              </div>
            </div>

            <div className="flex items-start gap-1.5 rounded-md bg-muted/50 p-2">
              <Sparkles className="h-3 w-3 text-primary mt-0.5 shrink-0" />
              <p className="text-xs text-muted-foreground line-clamp-2">{deal.aiSummary}</p>
            </div>
          </div>
        </div>
      </Card>
    </Link>
  );
}
