import { Account, SalesTeam, Product, Deal, ScoredDeal, ScoreExplanation } from '../types';

// Scoring Weights
export const WEIGHT_MATURITY = 0.35;
export const WEIGHT_AGENT = 0.30;
export const WEIGHT_PRODUCT = 0.20;
export const WEIGHT_FIRMOGRAPHICS = 0.15;

export function calculateDaysInDeal(engageDate: string, dealStage: string, referenceDate: Date = new Date()): { days: number; zone: string } {
  if (dealStage === 'Prospecting') {
    return { days: 0, zone: 'prospecting' };
  }

  if (!engageDate) {
    return { days: 0, zone: 'no_date' };
  }

  const engage = new Date(engageDate);
  if (isNaN(engage.getTime())) return { days: 0, zone: 'error' };

  const diffTime = referenceDate.getTime() - engage.getTime();
  const days = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  let zone = 'expired';
  if (days <= 15) zone = 'death_zone';
  else if (days <= 120) zone = 'maturity';
  else if (days <= 150) zone = 'late';

  return { days: Math.max(0, days), zone };
}

export function calculateMaturityScore(days: number, zone: string, dealStage: string): { score: number; explanation: string } {
  if (dealStage === 'Prospecting') {
    return { score: 50, explanation: "Deal em Prospecting - aguardando início do engajamento" };
  }

  let score = 50;
  let explanation = "Dados insuficientes";

  if (zone === 'death_zone') {
    score = 20 + (days / 15) * 30;
    explanation = `⚠️ ZONA DE RISCO: ${days} dias - 56% de conversão histórica nesta fase`;
  } else if (zone === 'maturity') {
    if (days <= 30) {
      score = 50 + ((days - 15) / 15) * 25;
      explanation = `✅ EM DESENVOLVIMENTO: ${days} dias - Conversão subindo para 71%`;
    } else {
      score = 75 + ((days - 30) / 90) * 20;
      explanation = `🎯 ZONA DE OURO: ${days} dias - Alta probabilidade de fechamento`;
    }
  } else if (zone === 'late') {
    score = 95 - ((days - 120) / 30) * 25;
    explanation = `⏰ ATENÇÃO: ${days} dias - Ainda viável, mas requer ação`;
  } else if (zone === 'expired') {
    score = 0;
    explanation = `❌ EXPIRADO: ${days} dias - 0% de conversão após 5 meses`;
  }

  return { score: Math.min(100, Math.max(0, score)), explanation };
}

export function calculateAgentScore(salesAgent: string, salesTeams: SalesTeam[], salesPipeline: Deal[]): { score: number; explanation: string } {
  const agentExists = salesTeams.some(t => t.sales_agent === salesAgent);
  if (!salesAgent || !agentExists) {
    return { score: 50, explanation: "Agente não identificado - score neutro aplicado" };
  }

  const agentDeals = salesPipeline.filter(d => d.sales_agent === salesAgent);
  const historicalDeals = agentDeals.filter(d => d.deal_stage === 'Won' || d.deal_stage === 'Lost');
  const wonDeals = historicalDeals.filter(d => d.deal_stage === 'Won');

  if (historicalDeals.length === 0) {
    return { score: 50, explanation: "Agente novo - sem histórico suficiente" };
  }

  const conversionRate = wonDeals.length / historicalDeals.length;
  const minRate = 0.55;
  const maxRate = 0.70;

  let score = 50;
  if (conversionRate < minRate) {
    score = 30 + (conversionRate / minRate) * 20;
  } else if (conversionRate > maxRate) {
    score = 90 + Math.min(10, (conversionRate - maxRate) * 100);
  } else {
    score = 50 + ((conversionRate - minRate) / (maxRate - minRate)) * 40;
  }

  return { 
    score: Math.min(100, Math.max(0, score)), 
    explanation: `👤 ${salesAgent}: ${(conversionRate * 100).toFixed(1)}% de conversão (${wonDeals.length}/${historicalDeals.length} deals)` 
  };
}

export function calculateProductScore(productName: string, products: Product[], closeValue: number): { score: number; explanation: string } {
  const productInfo = products.find(p => p.product === productName);
  if (!productName || !productInfo) {
    return { score: 50, explanation: "Produto não identificado - score neutro aplicado" };
  }

  const salesPrice = productInfo.sales_price;
  const series = productInfo.series;

  let valueTier = 'standard';
  let discountRate = 0;

  if (!closeValue || closeValue === 0) {
    valueTier = 'standard';
  } else {
    discountRate = (salesPrice - closeValue) / salesPrice;
    if (discountRate < 0) valueTier = 'upsell';
    else if (discountRate < 0.1) valueTier = 'premium';
    else if (discountRate < 0.25) valueTier = 'standard';
    else valueTier = 'discount';
  }

  const tierScores: Record<string, number> = {
    upsell: 95,
    premium: 85,
    standard: 70,
    discount: 45
  };

  let baseScore = tierScores[valueTier] || 70;
  const seriesBonus: Record<string, number> = {
    GTX: 5,
    MG: 0,
    GTK: 10
  };

  const score = baseScore + (seriesBonus[series] || 0);
  let explanation = `📦 ${productName} (${series}): ${valueTier.toUpperCase()} - R$ ${salesPrice.toLocaleString()}`;
  if (discountRate !== 0) {
    explanation += ` (${discountRate > 0 ? '-' : '+'}${Math.abs(discountRate * 100).toFixed(1)}% vs tabela)`;
  }

  return { score: Math.min(100, Math.max(0, score)), explanation };
}

export function calculateFirmographicsScore(accountName: string, accounts: Account[]): { score: number; explanation: string } {
  const accountInfo = accounts.find(a => a.account === accountName);
  if (!accountName || !accountInfo) {
    return { score: 60, explanation: "⚠️ Account não vinculado - 68% do pipeline nesta situação (não penalizado)" };
  }

  const sector = accountInfo.sector;
  const employees = accountInfo.employees;

  const sectorScores: Record<string, number> = {
    marketing: 85,
    entertainment: 84,
    software: 82,
    technolgy: 81,
    technology: 81,
    services: 80,
    retail: 79,
    employment: 78,
    telecommunications: 77,
    medical: 76,
    finance: 74
  };

  const baseSectorScore = sectorScores[sector.toLowerCase()] || 75;
  let sizeScore = 60;
  let sizeLabel = "Pequena";

  if (employees >= 5000) {
    sizeScore = 90;
    sizeLabel = "Enterprise";
  } else if (employees >= 1000) {
    sizeScore = 80;
    sizeLabel = "Grande";
  } else if (employees >= 100) {
    sizeScore = 70;
    sizeLabel = "Média";
  }

  const score = baseSectorScore * 0.4 + sizeScore * 0.6;
  const explanation = `🏢 ${accountName}: ${sizeLabel} (${employees.toLocaleString()} func.) - Setor: ${sector}`;

  return { score: Math.min(100, Math.max(0, score)), explanation };
}

export function calculateDealScore(row: Deal, accounts: Account[], salesTeams: SalesTeam[], products: Product[], salesPipeline: Deal[], referenceDate: Date = new Date()): { score: number; explanation: ScoreExplanation } {
  const { days, zone } = calculateDaysInDeal(row.engage_date, row.deal_stage, referenceDate);
  const maturity = calculateMaturityScore(days, zone, row.deal_stage);
  const agent = calculateAgentScore(row.sales_agent, salesTeams, salesPipeline);
  const product = calculateProductScore(row.product, products, row.close_value);
  const firmographics = calculateFirmographicsScore(row.account, accounts);

  const finalScore = (
    maturity.score * WEIGHT_MATURITY +
    agent.score * WEIGHT_AGENT +
    product.score * WEIGHT_PRODUCT +
    firmographics.score * WEIGHT_FIRMOGRAPHICS
  );

  const fullExplanation: ScoreExplanation = {
    score: Number(finalScore.toFixed(1)),
    maturity: { score: Number(maturity.score.toFixed(1)), explanation: maturity.explanation, weight: `${WEIGHT_MATURITY * 100}%` },
    agent: { score: Number(agent.score.toFixed(1)), explanation: agent.explanation, weight: `${WEIGHT_AGENT * 100}%` },
    product: { score: Number(product.score.toFixed(1)), explanation: product.explanation, weight: `${WEIGHT_PRODUCT * 100}%` },
    firmographics: { score: Number(firmographics.score.toFixed(1)), explanation: firmographics.explanation, weight: `${WEIGHT_FIRMOGRAPHICS * 100}%` },
    days_in_deal: days,
    zone: zone
  };

  return { score: finalScore, explanation: fullExplanation };
}
