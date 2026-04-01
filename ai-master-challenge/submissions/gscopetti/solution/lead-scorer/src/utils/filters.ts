import type {
  DealScore,
  AccountScore,
  PipelineOpportunity,
  FilterOptions,
} from '@/types';

/**
 * Apply filters to deal scores
 */
export function filterDealScores(
  scores: DealScore[],
  pipeline: PipelineOpportunity[],
  filters: FilterOptions
): DealScore[] {
  return scores.filter((score) => {
    // Find the original deal
    const deal = pipeline.find((d) => d.opportunity_id === score.opportunity_id);
    if (!deal) return false;

    // Apply filters
    if (filters.region) {
      // Region filter would need sales team data
      // For now, skip this filter
    }

    if (filters.sales_agent && deal.sales_agent !== filters.sales_agent) {
      return false;
    }

    if (filters.series && filters.product) {
      // Product filter
      if (deal.product !== filters.product) {
        return false;
      }
    }

    if (filters.tier && score.tier !== filters.tier) {
      return false;
    }

    return true;
  });
}

/**
 * Apply filters to account scores
 */
export function filterAccountScores(
  scores: AccountScore[],
  filters: FilterOptions
): AccountScore[] {
  return scores.filter((score) => {
    if (filters.tier && score.tier !== filters.tier) {
      return false;
    }

    return true;
  });
}

/**
 * Get deals by tier
 */
export function groupDealsByTier(scores: DealScore[]): {
  [key: string]: DealScore[];
} {
  return scores.reduce(
    (acc, score) => {
      if (!acc[score.tier]) {
        acc[score.tier] = [];
      }
      acc[score.tier].push(score);
      return acc;
    },
    {} as { [key: string]: DealScore[] }
  );
}

/**
 * Get deals by account
 */
export function groupDealsByAccount(scores: DealScore[]): {
  [key: string]: DealScore[];
} {
  return scores.reduce(
    (acc, score) => {
      const account = score.account || 'No Account';
      if (!acc[account]) {
        acc[account] = [];
      }
      acc[account].push(score);
      return acc;
    },
    {} as { [key: string]: DealScore[] }
  );
}

/**
 * Get top N deals by score
 */
export function getTopDeals(scores: DealScore[], limit: number = 10): DealScore[] {
  return scores.slice(0, limit);
}

/**
 * Get deals by stage
 */
export function groupDealsByStage(scores: DealScore[]): {
  [key: string]: DealScore[];
} {
  return scores.reduce(
    (acc, score) => {
      const stage = score.deal_stage;
      if (!acc[stage]) {
        acc[stage] = [];
      }
      acc[stage].push(score);
      return acc;
    },
    {} as { [key: string]: DealScore[] }
  );
}
