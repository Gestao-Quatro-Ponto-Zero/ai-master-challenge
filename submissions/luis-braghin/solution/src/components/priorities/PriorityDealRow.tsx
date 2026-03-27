import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { ArrowRight } from "lucide-react";
import { ScoreCircle } from "@/components/dashboard/ScoreCircle";
import { formatUSD, getCategoryBadgeClasses } from "@/lib/formatters";
import type { ScoredDeal, Agent } from "@/types/deals";

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

function getDealPhrase(deal: ScoredDeal, agent: Agent | null): string {
  const b = deal.breakdown;
  const dims: Array<{ key: string; value: number }> = [
    { key: "agentProductAffinity", value: b.agentProductAffinity },
    { key: "dealValue", value: b.dealValue },
    { key: "velocity", value: b.velocity ?? b.opportunityWindow ?? 0 },
    { key: "accountQuality", value: b.accountQuality },
    { key: "productSectorFit", value: b.productSectorFit },
  ];
  dims.sort((a, b) => b.value - a.value);

  function phraseForDim(dim: { key: string; value: number }): string | null {
    if (dim.key === "agentProductAffinity" && dim.value >= 70 && agent) {
      const wr = agent.productWinRates[deal.product];
      const pct = wr ? (wr.winRate * 100).toFixed(0) : "—";
      return `Sua afinidade com ${deal.product} é de ${pct}% — deal com boa chance`;
    } else if (dim.key === "dealValue" && dim.value >= 60) {
      const affinity = b.agentProductAffinity >= 60 ? "boa" : "razoável";
      return `Alto valor (${formatUSD(deal.expectedValue)}) + ${affinity} afinidade com ${deal.product}`;
    } else if (dim.key === "velocity" && dim.value >= 70 && deal.daysInPipeline >= 14 && deal.daysInPipeline <= 30) {
      return `Janela ideal (${deal.daysInPipeline} dias) — 73% win rate histórico nessa faixa`;
    } else if (dim.key === "accountQuality" && dim.value >= 70) {
      return `Conta de alto potencial — ${deal.sector}, receita ${formatUSD(deal.accountRevenue)}`;
    }
    return null;
  }

  let phrase = phraseForDim(dims[0]) ?? phraseForDim(dims[1]) ?? `Score ${deal.score} — ${deal.product} para ${deal.account || "nova conta"}`;

  if (deal.daysInPipeline > 138) {
    phrase += ` — ⚠️ ${deal.daysInPipeline}d, acima do máximo histórico de fechamento (138d)`;
  } else if (deal.daysInPipeline > 130) {
    phrase += ` — ⚠️ ${deal.daysInPipeline}d no pipeline, próximo do limite histórico`;
  } else if (deal.daysInPipeline > 90 && deal.stage === "Engaging") {
    phrase += ` ⚠️ ${deal.daysInPipeline} dias no pipeline`;
  }

  return phrase;
}

interface PriorityDealRowProps {
  deal: ScoredDeal;
  agent: Agent | null;
  fromState?: Record<string, string>;
  accountWonCounts?: Map<string, number>;
}

export function PriorityDealRow({ deal, agent, fromState, accountWonCounts }: PriorityDealRowProps) {
  const wonCount = deal.account && accountWonCounts ? (accountWonCounts.get(deal.account) ?? 0) : 0;
  const daysWarning = deal.daysInPipeline > 138;
  const daysAlert = deal.daysInPipeline > 90;

  return (
    <Link to={`/deal/${deal.id}`} state={fromState} className="block group">
      <div className="rounded-lg border bg-card hover:shadow-md hover:border-primary/30 transition-all cursor-pointer overflow-hidden">
        <div className="flex items-center gap-3 px-3 pt-3 pb-2">
          <div className="shrink-0">
            <ScoreCircle score={deal.score} category={deal.category} size={44} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-foreground truncate">{deal.account || "Sem conta"}</h3>
              <StageBadge stage={deal.stage} />
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground/0 group-hover:text-primary group-hover:translate-x-0.5 transition-all shrink-0 ml-auto" />
            </div>
            <p className="text-[11px] text-muted-foreground mt-0.5 truncate">
              {deal.sector}
              {wonCount > 0
                ? ` · Cliente recorrente (${wonCount}x)`
                : " · Conta nova"}
            </p>
          </div>
          <div className="text-right shrink-0">
            <p className="text-sm font-bold text-primary">{formatUSD(deal.salesPrice)}</p>
            <p className="text-[10px] text-muted-foreground">Valor do Deal</p>
          </div>
        </div>

        <div className="flex items-center gap-1 px-3 pb-2">
          <Badge variant="outline" className="text-[10px] font-medium px-1.5 py-0 h-5 bg-secondary/50">
            {deal.product}
          </Badge>
          <Badge
            variant="outline"
            className={`text-[10px] font-medium px-1.5 py-0 h-5 ${
              daysWarning
                ? "bg-destructive/10 text-destructive border-destructive/30"
                : daysAlert
                ? "bg-warning/10 text-warning border-warning/30"
                : "bg-secondary/50"
            }`}
          >
            ⏱ {formatDays(deal.daysInPipeline, deal.stage)}
          </Badge>
          <Badge variant="outline" className="text-[10px] font-medium px-1.5 py-0 h-5 bg-secondary/50">
            EV {formatUSD(deal.expectedValue)}
          </Badge>
          <Badge variant="outline" className={getCategoryBadgeClasses(deal.category) + " text-[10px] font-medium px-1.5 py-0 h-5"}>
            {deal.category}
          </Badge>
        </div>

        <div className="px-3 pb-3">
          <div className="rounded-md bg-muted/60 px-2.5 py-1.5">
            <p className="text-[11px] text-muted-foreground leading-snug italic">
              💡 {getDealPhrase(deal, agent)}
            </p>
          </div>
        </div>
      </div>
    </Link>
  );
}
