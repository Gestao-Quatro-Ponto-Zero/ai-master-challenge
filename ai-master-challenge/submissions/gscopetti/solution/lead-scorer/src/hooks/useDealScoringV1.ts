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
  calcWinRate,
  calcAgentPerformance,
  calcAccountSize,
  calcProductDiversity,
  scoreTimeInPipeline,
  scoreStage,
  normalizeSalesPrice,
  calcAccountLoyalty,
  calcRegionalPerformance,
  calcManagerBonus,
} from '@/utils/scoring';

/**
 * Hook to calculate deal scores for all active opportunities
 */
export function useDealScoring(
  pipeline: PipelineOpportunity[],
  accounts: Account[],
  products: Product[],
  salesTeams: SalesTeam[] = []
): DealScore[] {
  // Base date for temporal scoring (last date in dataset: 2017-12-31)
  // This ensures consistent scoring regardless of when the function is run
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

    // Create a map of products
    const productMap = new Map<string, Product>();
    for (const product of products) {
      productMap.set(product.product, product);
    }

    // Calculate win rate for the entire pipeline (for defaults)
    const globalWinRate = calcWinRate(pipeline.filter((d) => d.deal_stage === 'Won' || d.deal_stage === 'Lost'));

    return activeDeals.map((deal) => calculateDealScore(deal, pipeline, accountMap, productMap, products, globalWinRate, BASE_DATE, accounts, salesTeams));
  }, [pipeline, accounts, products, salesTeams]);
}

/**
 * Calculate score for a single deal
 */
function calculateDealScore(
  deal: PipelineOpportunity,
  allPipeline: PipelineOpportunity[],
  accountMap: Map<string, Account>,
  productMap: Map<string, Product>,
  allProducts: Product[],
  globalWinRate: number,
  baseDate: Date,
  accounts: Account[],
  salesTeams: SalesTeam[]
): DealScore {
  const factors: ScoreFactor[] = [];

  // Get account data if available
  const account = deal.account ? accountMap.get(deal.account) : undefined;

  // Get product data
  const product = productMap.get(deal.product);

  // === FACTOR 1: Histórico da conta (Win Rate) — 20% ===
  let accountWinRate = globalWinRate;
  let accountWinRateRaw: string | number = `${(globalWinRate * 100).toFixed(1)}%`;

  if (account) {
    const accountDeals = allPipeline.filter((d) => d.account === account.account);
    const wonDeals = accountDeals.filter((d) => d.deal_stage === 'Won');
    const lostDeals = accountDeals.filter((d) => d.deal_stage === 'Lost');

    if (wonDeals.length > 0 || lostDeals.length > 0) {
      accountWinRate = calcWinRate(accountDeals.filter((d) => d.deal_stage === 'Won' || d.deal_stage === 'Lost'));
      accountWinRateRaw = `${wonDeals.length} Won / ${lostDeals.length} Lost`;
    }
  }

  const winRateWeight = 22; // Increased from 20 (better predictor)
  const winRateNorm = accountWinRate;
  const winRateContribution = winRateNorm * winRateWeight;

  factors.push({
    name: 'Win Rate da Conta',
    weight: winRateWeight,
    raw_value: accountWinRateRaw,
    normalized_value: winRateNorm,
    contribution: winRateContribution,
    explanation: `${(winRateNorm * 100).toFixed(1)}% — ${
      accountWinRate >= globalWinRate
        ? 'Acima da média geral'
        : 'Abaixo da média geral'
    }. ${account ? 'Histórico desta conta' : 'Usando média geral (conta sem histórico)'}`,
  });

  // === FACTOR 2: Valor potencial do produto — 20% ===
  let productPrice = 0;
  if (product) {
    productPrice = product.sales_price;
  }

  const priceWeight = 15; // Reduced from 20 (GTK 500 dominates too much)
  const priceNorm = normalizeSalesPrice(productPrice, allProducts);
  const priceContribution = priceNorm * priceWeight;

  factors.push({
    name: 'Valor Potencial do Produto',
    weight: priceWeight,
    raw_value: `$${productPrice.toFixed(2)}`,
    normalized_value: priceNorm,
    contribution: priceContribution,
    explanation: `Produto: ${deal.product} — Preço normalizado entre produtos disponíveis`,
  });

  // === FACTOR 3: Performance do vendedor — 18% ===
  const agentWeight = 18; // Increased from 15 (better discriminator)
  const agentPerf = calcAgentPerformance(deal.sales_agent, deal.product, allPipeline);
  const agentContribution = agentPerf * agentWeight;

  // Count agent's performance
  const agentDeals = allPipeline.filter((d) => d.sales_agent === deal.sales_agent);
  const agentWon = agentDeals.filter((d) => d.deal_stage === 'Won').length;
  const agentLost = agentDeals.filter((d) => d.deal_stage === 'Lost').length;

  factors.push({
    name: 'Performance do Vendedor',
    weight: agentWeight,
    raw_value: `${agentWon} Won / ${agentLost} Lost`,
    normalized_value: agentPerf,
    contribution: agentContribution,
    explanation: `${deal.sales_agent}: ${(agentPerf * 100).toFixed(1)}% win rate em deals similares`,
  });

  // === FACTOR 4: Tempo no pipeline — 15% ===
  const daysInPipeline = (() => {
    const days = Math.floor((baseDate.getTime() - deal.engage_date.getTime()) / (1000 * 60 * 60 * 24));
    return Math.max(0, days);
  })();

  const timeWeight = 12; // Adjusted from 15 (was penalizing 59% of deals too much)
  const timeNorm = scoreTimeInPipeline(daysInPipeline);
  const timeContribution = timeNorm * timeWeight;

  const timeCategory =
    daysInPipeline <= 30 ? 'ótimo' : daysInPipeline <= 90 ? 'ok' : daysInPipeline <= 180 ? 'atenção' : 'frio';

  factors.push({
    name: 'Tempo no Pipeline',
    weight: timeWeight,
    raw_value: `${daysInPipeline} dias`,
    normalized_value: timeNorm,
    contribution: timeContribution,
    explanation: `${daysInPipeline} dias desde engagement — ${timeCategory}. Deals muito antigos provavelmente estão parados`,
  });

  // === FACTOR 5: Tamanho da conta — 10% ===
  let sizeWeight = 10;
  let sizeNorm = 0.5;
  let sizeExplanation = 'Conta não identificada — usando valor neutro';

  if (account) {
    const accountSize = calcAccountSize(account.revenue, account.employees, accounts);
    sizeNorm = accountSize;
    sizeExplanation = `${account.employees} employees, $${account.revenue.toLocaleString()} revenue`;
  } else {
    // Penalize lack of account data
    sizeWeight = 5; // Reduce weight if no account
  }

  const sizeContribution = sizeNorm * sizeWeight;

  factors.push({
    name: 'Tamanho da Empresa',
    weight: sizeWeight,
    raw_value: account ? `${account.employees} emps` : '—',
    normalized_value: sizeNorm,
    contribution: sizeContribution,
    explanation: sizeExplanation,
  });

  // === FACTOR 6: Estágio do deal — 10% ===
  const stageWeight = 10;
  const stageNorm = scoreStage(deal.deal_stage);
  const stageContribution = stageNorm * stageWeight;

  factors.push({
    name: 'Estágio do Deal',
    weight: stageWeight,
    raw_value: deal.deal_stage,
    normalized_value: stageNorm,
    contribution: stageContribution,
    explanation: `${deal.deal_stage} — Deals em Engaging estão mais avançados que Prospecting`,
  });

  // === FACTOR 7: Cross-sell opportunity — 10% ===
  let crossSellWeight = 10;
  let crossSellNorm = 0.5;
  let crossSellExplanation = 'Não há histórico de compras para avaliar cross-sell';

  if (account) {
    const accountDeals = allPipeline.filter((d) => d.account === account.account);
    const diversity = calcProductDiversity(accountDeals, allProducts);
    crossSellNorm = diversity;
    const uniqueSeries = new Set(
      accountDeals
        .map((d) => allProducts.find((p) => p.product === d.product)?.series)
        .filter(Boolean)
    );
    crossSellExplanation = `${uniqueSeries.size} séries diferentes já compradas — ${
      uniqueSeries.size >= 2 ? 'Cliente consolidado' : 'Oportunidade de expansão'
    }`;
  } else {
    crossSellWeight = 5; // Reduce if no account
  }

  const crossSellContribution = crossSellNorm * crossSellWeight;

  factors.push({
    name: 'Oportunidade Cross-sell',
    weight: crossSellWeight,
    raw_value: account ? '✓' : '—',
    normalized_value: crossSellNorm,
    contribution: crossSellContribution,
    explanation: crossSellExplanation,
  });

  // === FACTOR 8: Account Loyalty — +15 bonus ===
  let loyaltyBonus = 0;
  let loyaltyExplanation = 'Conta sem histórico de deals Won';

  if (account) {
    const accountDeals = allPipeline.filter((d) => d.account === account.account);
    const loyaltyScore = calcAccountLoyalty(accountDeals);
    if (loyaltyScore > 0) {
      loyaltyBonus = 15; // Fixed bonus for loyal accounts
      const wonCount = accountDeals.filter((d) => d.deal_stage === 'Won').length;
      loyaltyExplanation = `Conta leal: ${wonCount} deals Won anteriores — +15 pontos bônus`;
    }
  }

  factors.push({
    name: 'Account Loyalty (+15)',
    weight: 0, // Bonus, not weight-based
    raw_value: loyaltyBonus > 0 ? `${loyaltyBonus} pts` : '—',
    normalized_value: loyaltyBonus / 15, // Normalized to 0-1 for display
    contribution: loyaltyBonus,
    explanation: loyaltyExplanation,
  });

  // === FACTOR 9: Regional Performance — Multiplicador ===
  let regionalMultiplier = 1.0;
  let regionalExplanation = 'Sem dados de região';

  const salesTeam = salesTeams.find((t) => t.sales_agent === deal.sales_agent);
  if (salesTeam) {
    regionalMultiplier = calcRegionalPerformance(salesTeam.regional_office, allPipeline, salesTeams);
    const multiplierPct = ((regionalMultiplier - 1.0) * 100).toFixed(0);
    const sign = regionalMultiplier > 1.0 ? '+' : '';
    regionalExplanation = `Região ${salesTeam.regional_office}: ${sign}${multiplierPct}% (multiplier: ${regionalMultiplier.toFixed(2)})`;
  }

  // Regional performance factor (multiplier applied to score)
  const regionalContribution = (regionalMultiplier - 1.0) * 10; // Max ±2 points

  factors.push({
    name: 'Regional Performance',
    weight: 0, // Multiplicador, não peso
    raw_value: `${(regionalMultiplier * 100).toFixed(0)}%`,
    normalized_value: regionalMultiplier,
    contribution: regionalContribution,
    explanation: regionalExplanation,
  });

  // === FACTOR 10: Manager Bonus — Benchmarking ===
  let managerMultiplier = 1.0;
  let managerExplanation = 'Sem dados de manager';

  if (salesTeam) {
    managerMultiplier = calcManagerBonus(deal.sales_agent, allPipeline, salesTeams);
    const multiplierPct = ((managerMultiplier - 1.0) * 100).toFixed(0);
    const sign = managerMultiplier > 1.0 ? '+' : '';
    managerExplanation = `Manager ${salesTeam.manager}: ${sign}${multiplierPct}% vs team average (multiplier: ${managerMultiplier.toFixed(2)})`;
  }

  // Manager bonus factor (multiplier applied to score)
  const managerContribution = (managerMultiplier - 1.0) * 10; // Max ±1.5 points

  factors.push({
    name: 'Manager Bonus',
    weight: 0, // Multiplicador, não peso
    raw_value: `${(managerMultiplier * 100).toFixed(0)}%`,
    normalized_value: managerMultiplier,
    contribution: managerContribution,
    explanation: managerExplanation,
  });

  // Calculate final score with multipliers
  const baseContribution = factors
    .filter((f) => f.weight > 0) // Only factors with weights
    .reduce((sum, f) => sum + f.contribution, 0);

  // Apply regional and manager multipliers to base score
  const bonusContribution = loyaltyBonus + regionalContribution + managerContribution;
  const totalContribution = baseContribution + bonusContribution;
  const score = Math.round(totalContribution);

  return {
    opportunity_id: deal.opportunity_id,
    deal_stage: deal.deal_stage,
    score,
    tier: assignTier(score),
    factors,
    recommendation: getRecommendation(score),
    account: deal.account,
    product: deal.product,
    sales_agent: deal.sales_agent,
    engage_date: deal.engage_date,
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
 * Get action recommendation based on score
 */
function getRecommendation(score: number): string {
  if (score >= 80) return 'Prioridade máxima — agendar contato esta semana';
  if (score >= 60) return 'Bom potencial — nurturing ativo, follow-up quinzenal';
  if (score >= 40) return 'Potencial moderado — manter no radar, abordagem consultiva';
  return 'Baixa prioridade — revisar se vale manter no pipeline';
}
