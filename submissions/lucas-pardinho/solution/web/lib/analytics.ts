import { QUEUES, type ExecutiveMetrics, type Opportunity, type Queue } from "@/lib/types";

export function scoreOf(opportunity: Opportunity): number | null {
  return opportunity.priorityScore ?? opportunity.qualificationScore;
}

export function weightedValue(opportunity: Opportunity): number {
  if (
    opportunity.probability === null ||
    opportunity.dataQualityFlags.includes("outside_historical_cycle")
  ) {
    return 0;
  }
  const probability = opportunity.probability <= 1 ? opportunity.probability : opportunity.probability / 100;
  return opportunity.estimatedValue * Math.max(0, Math.min(1, probability));
}

export function summarizeOpportunities(opportunities: Opportunity[]): ExecutiveMetrics {
  const scored = opportunities
    .map(scoreOf)
    .filter((score): score is number => score !== null && Number.isFinite(score));

  const queueMap = new Map<Queue, { count: number; estimatedValue: number; weightedValue: number }>(
    QUEUES.map((queue) => [queue, { count: 0, estimatedValue: 0, weightedValue: 0 }]),
  );
  const regionMap = new Map<string, { count: number; estimatedValue: number }>();
  const confidence = { high: 0, medium: 0, low: 0 };

  for (const opportunity of opportunities) {
    const queue = queueMap.get(opportunity.queue);
    if (queue) {
      queue.count += 1;
      queue.estimatedValue += opportunity.estimatedValue;
      queue.weightedValue += weightedValue(opportunity);
    }

    const region = regionMap.get(opportunity.regionalOffice) ?? { count: 0, estimatedValue: 0 };
    region.count += 1;
    region.estimatedValue += opportunity.estimatedValue;
    regionMap.set(opportunity.regionalOffice, region);
    confidence[opportunity.confidence] += 1;
  }

  const topOpportunities = [...opportunities]
    .filter((opportunity) => opportunity.queue === "Foco agora" || opportunity.queue === "Acelerar")
    .sort((a, b) => (scoreOf(b) ?? -1) - (scoreOf(a) ?? -1))
    .slice(0, 8);

  return {
    openDeals: opportunities.length,
    estimatedPipeline: opportunities.reduce((sum, item) => sum + item.estimatedValue, 0),
    weightedPipeline: opportunities.reduce((sum, item) => sum + weightedValue(item), 0),
    focusNow: opportunities.filter((item) => item.queue === "Foco agora").length,
    staleDeals: opportunities.filter((item) => item.queue === "Resgatar ou desqualificar").length,
    averageScore: scored.length ? scored.reduce((sum, score) => sum + score, 0) / scored.length : null,
    queues: QUEUES.map((queue) => ({ queue, ...(queueMap.get(queue) ?? { count: 0, estimatedValue: 0, weightedValue: 0 }) })),
    confidence,
    regions: [...regionMap.entries()]
      .map(([name, values]) => ({ name, ...values }))
      .sort((a, b) => b.estimatedValue - a.estimatedValue),
    topOpportunities,
    dataIssueDeals: opportunities.filter((item) => item.dataQualityFlags.length > 0).length,
  };
}

export interface OpportunityFilters {
  search?: string;
  queue?: string;
  salesAgent?: string;
  manager?: string;
  regionalOffice?: string;
  dealStage?: string;
  sort?: "score" | "value" | "age" | "probability";
  order?: "asc" | "desc";
}

export function filterOpportunities(
  opportunities: Opportunity[],
  filters: OpportunityFilters,
): Opportunity[] {
  const search = filters.search?.trim().toLocaleLowerCase("pt-BR");
  const filtered = opportunities.filter((item) => {
    if (filters.queue && item.queue !== filters.queue) return false;
    if (filters.salesAgent && item.salesAgent !== filters.salesAgent) return false;
    if (filters.manager && item.manager !== filters.manager) return false;
    if (filters.regionalOffice && item.regionalOffice !== filters.regionalOffice) return false;
    if (filters.dealStage && item.dealStage !== filters.dealStage) return false;
    if (
      search &&
      ![item.opportunityId, item.account ?? "", item.product, item.salesAgent]
        .join(" ")
        .toLocaleLowerCase("pt-BR")
        .includes(search)
    ) {
      return false;
    }
    return true;
  });

  const sort = filters.sort ?? "score";
  const direction = filters.order === "asc" ? 1 : -1;
  const numberFor = (item: Opportunity): number => {
    if (sort === "value") return item.estimatedValue;
    if (sort === "age") return item.ageDays ?? -1;
    if (sort === "probability") return item.probability ?? -1;
    return scoreOf(item) ?? -1;
  };

  return [...filtered].sort((a, b) => (numberFor(a) - numberFor(b)) * direction);
}
