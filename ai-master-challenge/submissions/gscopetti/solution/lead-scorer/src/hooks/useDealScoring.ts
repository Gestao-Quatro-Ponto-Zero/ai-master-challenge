import { useMemo } from 'react';
import type {
  PipelineOpportunity,
  Account,
  Product,
  DealScore,
  ScoreFactor,
  SalesTeam,
} from '@/types';
import {
  calcValorPilar,
  calcMomentumPilar,
  calcFitContaPilar,
  calcQualidadeRepPilar,
} from '@/utils/scoring';

/**
 * Lead Scorer V2: 4-Pillar Data-Driven Architecture
 *
 * score = (valor_pilar × 0.40)
 *       + (momentum_pilar × 0.25)
 *       + (fit_conta × 0.15)
 *       + (qualidade_rep × 0.20)
 *
 * Based on 7 critical data discoveries from dataset analysis.
 * Replaces V1 (10-factor model) with cleaner, more data-driven approach.
 */
export function useDealScoring(
  pipeline: PipelineOpportunity[],
  accounts: Account[],
  products: Product[],
  salesTeams?: SalesTeam[]
): DealScore[] {
  // Base date for temporal scoring (last date in dataset: 2017-12-31)
  const BASE_DATE = new Date('2017-12-31');

  return useMemo(() => {
    // Filter only active deals (Engaging or Prospecting)
    const activeDeals = pipeline.filter(
      (deal) => deal.deal_stage === 'Engaging' || deal.deal_stage === 'Prospecting'
    );

    // Create a map of accounts for quick lookup
    const accountMap = new Map<string, Account>();
    for (const account of accounts) {
      if (account.account) {
        accountMap.set(account.account, account);
      }
    }

    // Create a map of sales teams for quick lookup
    const salesTeamMap = new Map<string, SalesTeam>();
    if (salesTeams) {
      for (const team of salesTeams) {
        salesTeamMap.set(team.sales_agent, team);
      }
    }

    // Get closed deals for each product (to calculate product-specific win rate)
    const closedDeals = pipeline.filter((d) => d.deal_stage === 'Won' || d.deal_stage === 'Lost');

    return activeDeals.map((deal) =>
      calculateDealScoreV2(deal, pipeline, accountMap, products, closedDeals, BASE_DATE, salesTeamMap)
    );
  }, [pipeline, accounts, products, salesTeams]);
}

/**
 * Calculate score for a single deal using 4-pillar model
 */
function calculateDealScoreV2(
  deal: PipelineOpportunity,
  allPipeline: PipelineOpportunity[],
  accountMap: Map<string, Account>,
  allProducts: Product[],
  closedDeals: PipelineOpportunity[],
  baseDate: Date,
  salesTeamMap: Map<string, SalesTeam>
): DealScore {
  const factors: ScoreFactor[] = [];

  // Get account data if available
  const account = deal.account ? accountMap.get(deal.account) : undefined;

  // Calculate days in pipeline
  const daysInPipeline = Math.max(
    0,
    Math.floor((baseDate.getTime() - deal.engage_date.getTime()) / (1000 * 60 * 60 * 24))
  );

  // ==================== PILAR 1: VALOR (40%) ====================
  // Increased from 35% to 40% — Expected Value is critical differentiator
  // GTK 500 (EV=16024) vs others creates needed discrimination at top
  const closedDealsOfProduct = closedDeals.filter((d) => d.product === deal.product);
  const valorPilarScore = calcValorPilar(deal.product, closedDealsOfProduct, allProducts);
  const valorContribution = (valorPilarScore / 100) * 40;

  factors.push({
    name: 'Pilar 1: Valor (40%)',
    weight: 40,
    raw_value: `EV: ${deal.product}`,
    normalized_value: valorPilarScore / 100,
    contribution: valorContribution,
    explanation: `Expected Value do produto (price × historical win rate). Score: ${valorPilarScore}/100`,
  });

  // ==================== PILAR 2: MOMENTUM (25%) ====================
  // Reduced from 30% to 25% — Still important but not overdominant
  const momentumRawScore = calcMomentumPilar(daysInPipeline);
  const momentumScore = Math.max(0, Math.min(100, 50 + momentumRawScore)); // Base 50 + adjustment
  const momentumContribution = (momentumScore / 100) * 25;

  const momentumCategory =
    daysInPipeline < 8
      ? '"die easy" — deals fechar em <8d têm 53% WR'
      : daysInPipeline <= 30
        ? 'sweet spot — 15-30d têm 73% WR'
        : daysInPipeline <= 90
          ? 'still good — 31-90d têm WR declinante'
          : 'stagnated — >90d são frios';

  factors.push({
    name: 'Pilar 2: Momentum (25%)',
    weight: 25,
    raw_value: `${daysInPipeline}d`,
    normalized_value: momentumScore / 100,
    contribution: momentumContribution,
    explanation: `Win rate por tempo em pipeline. ${daysInPipeline} dias: ${momentumCategory}`,
  });

  // ==================== PILAR 3: FIT CONTA (15%) ====================
  const fitContaScore = calcFitContaPilar(account);
  const fitContaContribution = (fitContaScore / 100) * 15;

  const fitExplanation = account
    ? `Revenue: $${account.revenue.toLocaleString()}, Employees: ${account.employees}`
    : 'Conta não identificada — penalty -15 aplicada';

  factors.push({
    name: 'Pilar 3: Fit da Conta (15%)',
    weight: 15,
    raw_value: account ? `${account.account}` : '—',
    normalized_value: fitContaScore / 100,
    contribution: fitContaContribution,
    explanation: fitExplanation,
  });

  // ==================== PILAR 4: QUALIDADE REP (20%) ====================
  // Increased from 15% to 20% — Agent variance (55%-70.4%) is bigger than sector variance (4pp)
  const qualidadeRepScore = calcQualidadeRepPilar(deal.sales_agent, allPipeline);
  const qualidadeContribution = (qualidadeRepScore / 100) * 20;

  const agentDeals = allPipeline.filter((d) => d.sales_agent === deal.sales_agent);
  const agentWon = agentDeals.filter((d) => d.deal_stage === 'Won').length;
  const agentLost = agentDeals.filter((d) => d.deal_stage === 'Lost').length;

  factors.push({
    name: 'Pilar 4: Qualidade Rep (20%)',
    weight: 20,
    raw_value: `${agentWon}W/${agentLost}L`,
    normalized_value: qualidadeRepScore / 100,
    contribution: qualidadeContribution,
    explanation: `${deal.sales_agent}: ${agentWon > 0 ? Math.round((agentWon / (agentWon + agentLost)) * 100) : 0}% win rate historicamente`,
  });

  // ==================== SCORE FINAL (No Redundant Penalties) ====================
  // NOTE: Momentum Pilar already captures stagnation effects
  // Additional penalties would be redundant since >90d are penalized via momentum curve
  // This keeps the 4-pillar model clean and aligned with data-driven insights

  const baseScore = valorContribution + momentumContribution + fitContaContribution + qualidadeContribution;
  const finalScore = Math.round(Math.max(0, Math.min(100, baseScore)));

  // Enrich with sales team and product info for filtering
  const salesTeamMember = salesTeamMap.get(deal.sales_agent);
  const productObj = allProducts.find((p) => p.product === deal.product);

  return {
    opportunity_id: deal.opportunity_id,
    deal_stage: deal.deal_stage,
    score: finalScore,
    tier: assignTier(finalScore),
    factors,
    recommendation: getRecommendation(finalScore),
    account: deal.account,
    product: deal.product,
    sales_agent: deal.sales_agent,
    engage_date: deal.engage_date,
    region: salesTeamMember?.regional_office,
    manager: salesTeamMember?.manager,
    series: productObj?.series,
  };
}

/**
 * Assign tier based on score
 */
function assignTier(score: number): 'HOT' | 'WARM' | 'COOL' | 'COLD' {
  if (score >= 80) return 'HOT';
  if (score >= 60) return 'WARM';
  if (score >= 40) return 'COOL';
  return 'COLD';
}

/**
 * Get recommendation text based on score
 */
function getRecommendation(score: number): string {
  if (score >= 80) {
    return 'Prioridade máxima — agendar para esta semana';
  } else if (score >= 60) {
    return 'Bom potencial — nurturing ativo, follow-up quinzenal';
  } else if (score >= 40) {
    return 'Potencial moderado — manter no radar, abordagem consultiva';
  } else {
    return 'Baixa prioridade — revisar se vale manter no pipeline';
  }
}
