import type { Account, PipelineOpportunity, Product } from '@/types';

/**
 * Calculate win rate from a list of deals
 * Returns 0-1 normalized value
 */
export function calcWinRate(deals: PipelineOpportunity[]): number {
  if (deals.length === 0) return 0.5; // Neutral default

  const won = deals.filter((d) => d.deal_stage === 'Won').length;
  const lost = deals.filter((d) => d.deal_stage === 'Lost').length;

  const total = won + lost;
  if (total === 0) return 0.5; // No closed deals

  return won / total;
}

/**
 * Calculate average ticket from won deals
 */
export function calcAvgTicket(wonDeals: PipelineOpportunity[]): number {
  if (wonDeals.length === 0) return 0;

  const sum = wonDeals.reduce((acc, deal) => acc + deal.close_value, 0);
  return sum / wonDeals.length;
}

/**
 * Calculate days in pipeline from engagement date to today
 */
export function calcDaysInPipeline(engageDate: Date): number {
  const today = new Date();
  const days = Math.floor((today.getTime() - engageDate.getTime()) / (1000 * 60 * 60 * 24));
  return Math.max(0, days);
}

/**
 * Calculate agent performance for a specific product or series
 * Returns win rate (0-1) for deals of this product/series
 */
export function calcAgentPerformance(
  agentName: string,
  product: string,
  allDeals: PipelineOpportunity[]
): number {
  const agentDeals = allDeals.filter((d) => d.sales_agent === agentName);

  if (agentDeals.length === 0) return 0.5; // Neutral default

  // Try exact product match first
  let relevantDeals = agentDeals.filter((d) => d.product === product);

  // If no exact matches, use all agent's deals
  if (relevantDeals.length === 0) {
    relevantDeals = agentDeals;
  }

  return calcWinRate(relevantDeals);
}

/**
 * Normalize a value to 0-1 range based on min and max
 */
export function normalizeValue(value: number, min: number, max: number): number {
  if (max === min) return 0.5; // Avoid division by zero

  const normalized = (value - min) / (max - min);
  return Math.max(0, Math.min(1, normalized)); // Clamp to 0-1
}

/**
 * Calculate account size score based on revenue and employees
 * Returns 0-1
 */
export function calcAccountSize(
  revenue: number,
  employees: number,
  allAccounts: Account[]
): number {
  if (!revenue && !employees) return 0.5; // Neutral

  // Get stats from all accounts
  const revenues = allAccounts.map((a) => a.revenue).filter((r) => r > 0);
  const employeeCounts = allAccounts.map((a) => a.employees).filter((e) => e > 0);

  const minRevenue = revenues.length > 0 ? Math.min(...revenues) : 0;
  const maxRevenue = revenues.length > 0 ? Math.max(...revenues) : 1;

  const minEmployees = employeeCounts.length > 0 ? Math.min(...employeeCounts) : 0;
  const maxEmployees = employeeCounts.length > 0 ? Math.max(...employeeCounts) : 1;

  const revenueNorm = normalizeValue(revenue, minRevenue, maxRevenue);
  const employeesNorm = normalizeValue(employees, minEmployees, maxEmployees);

  return (revenueNorm + employeesNorm) / 2;
}

/**
 * Calculate product diversity for an account
 * Returns 0-1 (how many different series they've bought)
 */
export function calcProductDiversity(
  accountDeals: PipelineOpportunity[],
  allProducts: Product[]
): number {
  const uniqueSeries = new Set<string>();

  for (const deal of accountDeals) {
    const product = allProducts.find((p) => p.product === deal.product);
    if (product) {
      uniqueSeries.add(product.series);
    }
  }

  if (allProducts.length === 0) return 0.5;

  const totalSeries = new Set(allProducts.map((p) => p.series)).size;
  return uniqueSeries.size / Math.max(1, totalSeries);
}

/**
 * Calculate recency score based on last deal date
 * Returns 0-1 (newer = higher)
 */
export function calcRecency(deals: PipelineOpportunity[]): number {
  if (deals.length === 0) return 0;

  // Get the most recent deal
  const sortedByDate = [...deals].sort((a, b) => {
    const dateA = a.close_date || a.engage_date;
    const dateB = b.close_date || b.engage_date;
    return dateB.getTime() - dateA.getTime();
  });

  const mostRecentDate = sortedByDate[0].close_date || sortedByDate[0].engage_date;
  const daysAgo = calcDaysInPipeline(mostRecentDate);

  // Score: 0 days = 1.0, 365 days = 0.5, 730+ days = 0.1
  if (daysAgo <= 30) return 1.0;
  if (daysAgo <= 90) return 0.8;
  if (daysAgo <= 180) return 0.6;
  if (daysAgo <= 365) return 0.4;
  return 0.1;
}

/**
 * Convert days in pipeline to normalized score
 * 0-30d = 1.0, 30-90d = 0.7, 90-180d = 0.4, >180d = 0.2
 */
export function scoreTimeInPipeline(days: number): number {
  if (days <= 30) return 1.0;
  if (days <= 90) return 0.7;
  if (days <= 180) return 0.4;
  return 0.2;
}

/**
 * Stage score for deals
 * Engaging deals are further along than Prospecting
 */
export function scoreStage(stage: string): number {
  switch (stage) {
    case 'Engaging':
      return 0.7;
    case 'Prospecting':
      return 0.4;
    default:
      return 0.5;
  }
}

/**
 * Normalize sales price to 0-1 based on product prices
 */
export function normalizeSalesPrice(price: number, allProducts: Product[]): number {
  if (allProducts.length === 0) return 0.5;

  const prices = allProducts.map((p) => p.sales_price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);

  return normalizeValue(price, minPrice, maxPrice);
}

/**
 * Calculate activity volume score
 * Returns 0-1 based on total deals count
 */
export function calcActivityVolume(totalDeals: number, allPipeline: PipelineOpportunity[]): number {
  if (allPipeline.length === 0) return 0.5;

  // Get quartiles
  const accountDealsCount = new Map<string | undefined, number>();
  for (const deal of allPipeline) {
    const account = deal.account;
    accountDealsCount.set(account, (accountDealsCount.get(account) || 0) + 1);
  }

  const counts = Array.from(accountDealsCount.values()).sort((a, b) => a - b);
  const q1 = counts[Math.floor(counts.length * 0.25)];
  const q3 = counts[Math.floor(counts.length * 0.75)];

  if (totalDeals < q1) return 0.3;
  if (totalDeals < q3) return 0.6;
  return 0.9;
}

/**
 * Calculate pipeline active count for an account
 * Returns normalized score (0-1)
 */
export function calcPipelineActiveCount(activeDeals: number, allPipeline: PipelineOpportunity[]): number {
  if (allPipeline.length === 0) return 0.5;

  const activeDealsPerAccount = new Map<string | undefined, number>();
  for (const deal of allPipeline) {
    if (deal.deal_stage === 'Engaging' || deal.deal_stage === 'Prospecting') {
      const account = deal.account;
      activeDealsPerAccount.set(account, (activeDealsPerAccount.get(account) || 0) + 1);
    }
  }

  const counts = Array.from(activeDealsPerAccount.values()).sort((a, b) => a - b);
  if (counts.length === 0) return 0.5;

  const maxActive = counts[counts.length - 1];
  return activeDeals / Math.max(1, maxActive);
}

/**
 * Score lost revenue (sum of lost deals)
 * Higher lost revenue = higher penalty
 */
export function calcLostRevenue(lostDeals: PipelineOpportunity[]): number {
  return lostDeals.reduce((sum, deal) => sum + deal.close_value, 0);
}

/**
 * Calculate account loyalty score based on past won deals
 * Returns 1.0 if account has won deals, 0.0 otherwise
 * Bonus: +15 points for loyal accounts
 */
export function calcAccountLoyalty(accountDeals: PipelineOpportunity[]): number {
  const wonDeals = accountDeals.filter((d) => d.deal_stage === 'Won');
  return wonDeals.length > 0 ? 1.0 : 0.0;
}

/**
 * Calculate regional performance multiplier based on regional office win rate
 * Returns multiplier 0.8-1.2 (20% penalty to 20% bonus)
 */
export function calcRegionalPerformance(
  regionalOffice: string,
  allDeals: PipelineOpportunity[],
  salesTeams: Array<{ sales_agent: string; regional_office: string }>
): number {
  // Get all agents in this region
  const agentsInRegion = salesTeams
    .filter((t) => t.regional_office === regionalOffice)
    .map((t) => t.sales_agent);

  if (agentsInRegion.length === 0) return 1.0; // No regional data, neutral

  // Get regional win rate
  const regionalDeals = allDeals.filter((d) => agentsInRegion.includes(d.sales_agent));
  const closedRegionalDeals = regionalDeals.filter((d) => d.deal_stage === 'Won' || d.deal_stage === 'Lost');

  if (closedRegionalDeals.length === 0) return 1.0; // No closed deals, neutral

  const regionalWinRate = closedRegionalDeals.filter((d) => d.deal_stage === 'Won').length / closedRegionalDeals.length;

  // Global win rate
  const globalWinRate = calcWinRate(allDeals.filter((d) => d.deal_stage === 'Won' || d.deal_stage === 'Lost'));

  // Calculate multiplier: ±20% based on regional performance vs global
  // If regional > global, boost by 20%
  // If regional < global, penalty of 20%
  const performanceDiff = regionalWinRate - globalWinRate;
  const multiplier = 1.0 + performanceDiff; // Max ±100% diff, but clamped below

  return Math.max(0.8, Math.min(1.2, multiplier)); // Clamp to 0.8-1.2
}

/**
 * Calculate manager bonus multiplier based on benchmarking against team average
 * Returns multiplier 0.85-1.15 (15% penalty to 15% bonus)
 */
export function calcManagerBonus(
  salesAgent: string,
  allDeals: PipelineOpportunity[],
  salesTeams: Array<{ sales_agent: string; manager: string }>
): number {
  // Find manager for this agent
  const agentTeam = salesTeams.find((t) => t.sales_agent === salesAgent);
  if (!agentTeam) return 1.0; // No manager data, neutral

  const manager = agentTeam.manager;

  // Get all agents under this manager
  const teamAgents = salesTeams.filter((t) => t.manager === manager).map((t) => t.sales_agent);

  // Calculate agent's performance
  const agentDeals = allDeals.filter((d) => d.sales_agent === salesAgent);
  const agentClosed = agentDeals.filter((d) => d.deal_stage === 'Won' || d.deal_stage === 'Lost');
  const agentWinRate = agentClosed.length > 0 ? calcWinRate(agentClosed) : 0.5;

  // Calculate manager team average performance
  const teamDeals = allDeals.filter((d) => teamAgents.includes(d.sales_agent));
  const teamClosed = teamDeals.filter((d) => d.deal_stage === 'Won' || d.deal_stage === 'Lost');
  const teamAvgWinRate = teamClosed.length > 0 ? calcWinRate(teamClosed) : 0.5;

  // Calculate multiplier: ±15% based on individual vs team average
  const performanceDiff = agentWinRate - teamAvgWinRate;
  const multiplier = 1.0 + performanceDiff * 0.75; // Reduce impact to max ±15%

  return Math.max(0.85, Math.min(1.15, multiplier)); // Clamp to 0.85-1.15
}

/**
 * NEW MODEL: Calculate Valor Pilar (40%)
 * Based on Expected Value (EV) of the product using log scale
 * EV = close_price × average_win_rate_for_product
 */
export function calcValorPilar(
  productName: string,
  closedDealsOfProduct: PipelineOpportunity[],
  allProducts: Product[]
): number {
  const product = allProducts.find((p) => p.product === productName);
  if (!product) return 50; // Neutral if product not found

  // Calculate win rate for this specific product
  const wonCount = closedDealsOfProduct.filter((d) => d.deal_stage === 'Won').length;
  const productWinRate = closedDealsOfProduct.length > 0
    ? wonCount / closedDealsOfProduct.length
    : 0.63; // Use global average

  // Expected Value = product_price × win_rate
  const expectedValue = product.sales_price * productWinRate;

  // Find max EV across all products for normalization
  const allProductsEV = allProducts.map((p) => {
    const pDeals = closedDealsOfProduct.filter((d) => d.product === p.product);
    const pWinRate = pDeals.length > 0
      ? pDeals.filter((d) => d.deal_stage === 'Won').length / pDeals.length
      : 0.63;
    return p.sales_price * pWinRate;
  });

  const maxEV = Math.max(...allProductsEV, 1);
  const minEV = Math.min(...allProductsEV, 1);

  // Log scale normalization (handles 445× variance better than linear)
  if (minEV === maxEV) return 50;
  const logEV = Math.log(expectedValue + 1);
  const logMin = Math.log(minEV + 1);
  const logMax = Math.log(maxEV + 1);

  const normalized = (logEV - logMin) / (logMax - logMin);
  return Math.round(Math.max(0, Math.min(100, normalized * 100)));
}

/**
 * NEW MODEL: Calculate Momentum Pilar (25%)
 * Based on win rate curve by days in pipeline
 * <8d = 53%, 15-30d = 73% (sweet spot), >90d = cold
 */
export function calcMomentumPilar(daysInPipeline: number): number {
  if (daysInPipeline < 8) {
    // <8d = 53% WR — "die easy" deals get penalty
    return -10;
  }
  if (daysInPipeline <= 14) {
    // 8-14d = inflection point, start improving
    return Math.round((daysInPipeline - 8) / 6 * 30); // Scale from 0 to 30
  }
  if (daysInPipeline <= 30) {
    // 15-30d = 73% WR — sweet spot, full credit
    return 80;
  }
  if (daysInPipeline <= 90) {
    // 31-90d = still good but declining
    const daysSince30 = daysInPipeline - 30;
    return Math.round(80 - (daysSince30 / 60) * 10); // Decline to 70
  }

  // >90d = stagnated, heavily penalized
  return 20; // Will get -25 bonus penalty below
}

/**
 * NEW MODEL: Calculate Fit da Conta Pilar (15%)
 * Based on revenue bucket + sector historical win rate
 */
export function calcFitContaPilar(
  account: Account | undefined
): number {
  if (!account || !account.revenue) {
    // No account data = -15 penalty
    return 40; // Neutral with penalty applied separately
  }

  // Revenue bucket classification
  const revenue = account.revenue;
  let revenueBucketScore = 0.5;

  if (revenue < 1_000_000) {
    revenueBucketScore = 0.3; // Small
  } else if (revenue < 50_000_000) {
    revenueBucketScore = 0.6; // Mid
  } else if (revenue < 500_000_000) {
    revenueBucketScore = 0.8; // Large
  } else {
    revenueBucketScore = 1.0; // Enterprise
  }

  // Sector win rate (if available)
  // For now, using account revenue bucket + a small random boost for variety
  // In production, this would query historical sector performance
  const sectorBoost = 0.5; // Neutral (61-65% range, small effect)

  const fitScore = (revenueBucketScore + sectorBoost) / 2;
  return Math.round(fitScore * 100);
}

/**
 * NEW MODEL: Calculate Qualidade Rep Pilar (15%)
 * Win rate agent normalized to observed range: 55% (min) to 70.4% (max)
 * Global observed: min=0.55, max=0.704
 */
export function calcQualidadeRepPilar(
  salesAgent: string,
  allDeals: PipelineOpportunity[]
): number {
  const agentDeals = allDeals.filter((d) => d.sales_agent === salesAgent);
  const agentClosed = agentDeals.filter((d) => d.deal_stage === 'Won' || d.deal_stage === 'Lost');

  if (agentClosed.length === 0) {
    return 50; // Neutral default
  }

  const agentWinRate = agentClosed.filter((d) => d.deal_stage === 'Won').length / agentClosed.length;

  // Normalize to observed range: 55% (min) to 70.4% (max)
  const MIN_WIN_RATE = 0.55;
  const MAX_WIN_RATE = 0.704;

  const normalized = (agentWinRate - MIN_WIN_RATE) / (MAX_WIN_RATE - MIN_WIN_RATE);
  const clamped = Math.max(0, Math.min(1, normalized));

  return Math.round(clamped * 100);
}
