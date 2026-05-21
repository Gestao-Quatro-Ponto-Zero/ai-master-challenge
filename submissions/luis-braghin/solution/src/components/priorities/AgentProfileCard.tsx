import { useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Trophy, User } from "lucide-react";
import { formatUSD } from "@/lib/formatters";
import type { Agent, ScoredDeal } from "@/types/deals";

export function AgentProfileCard({ agent, deals }: { agent: Agent; deals: ScoredDeal[] }) {
  const totalEV = deals.reduce((s, d) => s + d.expectedValue, 0);
  const totalPipeline = deals.reduce((s, d) => s + d.salesPrice, 0);

  const strongProducts = useMemo(() => {
    return Object.entries(agent.productWinRates)
      .filter(([, data]) => data.total >= 5)
      .sort(([, a], [, b]) => b.winRate - a.winRate)
      .slice(0, 3);
  }, [agent]);

  const weakProducts = useMemo(() => {
    return Object.entries(agent.productWinRates)
      .filter(([, data]) => data.total >= 5 && data.winRate < 0.45)
      .sort(([, a], [, b]) => a.winRate - b.winRate);
  }, [agent]);

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex flex-col md:flex-row md:items-start gap-6">
          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center">
              <User className="h-7 w-7 text-primary" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Olá, {agent.name}</h2>
              <p className="text-sm text-muted-foreground">{agent.manager} • {agent.regionalOffice}</p>
            </div>
          </div>

          <div className="flex-1 grid grid-cols-4 gap-4">
            <div className="text-center p-3 rounded-lg bg-muted/50">
              <p className="text-2xl font-bold text-foreground">{(agent.winRate * 100).toFixed(0)}%</p>
              <p className="text-xs text-muted-foreground">Win Rate</p>
            </div>
            <div className="text-center p-3 rounded-lg bg-muted/50">
              <p className="text-2xl font-bold text-foreground">{deals.length}</p>
              <p className="text-xs text-muted-foreground">Deals Ativos</p>
            </div>
            <div className="text-center p-3 rounded-lg bg-muted/50">
              <p className="text-2xl font-bold text-foreground">{formatUSD(totalPipeline)}</p>
              <p className="text-xs text-muted-foreground">Pipeline Total</p>
            </div>
            <div className="text-center p-3 rounded-lg bg-muted/50">
              <p className="text-2xl font-bold text-foreground">{formatUSD(totalEV)}</p>
              <p className="text-xs text-muted-foreground">Expected Value</p>
            </div>
          </div>
        </div>

        {strongProducts.length > 0 && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-sm font-medium text-foreground mb-2">Seus pontos fortes</p>
            <div className="flex flex-wrap gap-2">
              {strongProducts.map(([product, data]) => (
                <Badge key={product} variant="secondary" className="text-xs gap-1">
                  <Trophy className="h-3 w-3" />
                  {product} — {(data.winRate * 100).toFixed(0)}% win rate
                </Badge>
              ))}
            </div>
          </div>
        )}

        {weakProducts.length > 0 && (
          <div className="mt-3 p-3 rounded-lg bg-chart-3/5 border border-chart-3/20">
            <p className="text-xs text-chart-3">
              💡 Dica: Seus deals de{" "}
              {weakProducts.map(([p, d]) => `${p} (${(d.winRate * 100).toFixed(0)}%)`).join(", ")}{" "}
              têm win rate baixo. Considere pedir apoio de um colega especialista.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
