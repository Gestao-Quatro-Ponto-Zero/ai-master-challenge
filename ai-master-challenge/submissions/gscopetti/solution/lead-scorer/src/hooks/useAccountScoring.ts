import { useMemo } from 'react';
import type {
  PipelineOpportunity,
  Account,
  Product,
  AccountScore,
  ScoreFactor,
} from '@/types';
import {
  calcWinRate,
  calcAvgTicket,
  normalizeValue,
  calcRecency,
  calcActivityVolume,
  calcPipelineActiveCount,
  calcProductDiversity,
} from '@/utils/scoring';

/**
 * Hook to calculate account scores aggregated from all deals
 */
export function useAccountScoring(
  pipeline: PipelineOpportunity[],
  accounts: Account[],
  products: Product[]
): AccountScore[] {
  return useMemo(() => {
    // Group deals by account
    const dealsByAccount = new Map<string, PipelineOpportunity[]>();

    for (const deal of pipeline) {
      if (deal.account) {
        if (!dealsByAccount.has(deal.account)) {
          dealsByAccount.set(deal.account, []);
        }
        dealsByAccount.get(deal.account)!.push(deal);
      }
    }

    // Create account map
    const accountMap = new Map<string, Account>();
    for (const account of accounts) {
      if (account.account) {
        accountMap.set(account.account, account);
      }
    }

    // Calculate score for each account
    const scores: AccountScore[] = [];

    for (const [accountName, accountDeals] of dealsByAccount) {
      const accountData = accountMap.get(accountName);
      const score = calculateAccountScore(
        accountName,
        accountDeals,
        accountData,
        products,
        pipeline,
        accounts
      );
      scores.push(score);
    }

    // Sort by score descending
    scores.sort((a, b) => b.score - a.score);

    return scores;
  }, [pipeline, accounts, products]);
}

/**
 * Calculate score for a single account
 */
function calculateAccountScore(
  accountName: string,
  accountDeals: PipelineOpportunity[],
  accountData: Account | undefined,
  allProducts: Product[],
  allPipeline: PipelineOpportunity[],
  allAccounts: Account[]
): AccountScore {
  const factors: ScoreFactor[] = [];

  // Count deals by stage
  const wonDeals = accountDeals.filter((d) => d.deal_stage === 'Won');
  const lostDeals = accountDeals.filter((d) => d.deal_stage === 'Lost');
  const engagingDeals = accountDeals.filter((d) => d.deal_stage === 'Engaging');
  const prospectingDeals = accountDeals.filter((d) => d.deal_stage === 'Prospecting');

  // Require minimum 3 deals to be significant
  const hasEnoughData = wonDeals.length + lostDeals.length >= 3;

  // === FACTOR 1: Win Rate — 25% ===
  const winRateWeight = 25;
  const closedDeals = wonDeals.concat(lostDeals);
  const winRate = closedDeals.length > 0 ? calcWinRate(closedDeals) : 0.5;
  const winRateContribution = winRate * winRateWeight;

  factors.push({
    name: 'Win Rate',
    weight: winRateWeight,
    raw_value: `${wonDeals.length}W / ${lostDeals.length}L`,
    normalized_value: winRate,
    contribution: winRateContribution,
    explanation: `${(winRate * 100).toFixed(1)}% — ${wonDeals.length + lostDeals.length} deals fechados ${
      !hasEnoughData ? '(dados insuficientes para significância)' : ''
    }`,
  });

  // === FACTOR 2: Ticket Médio — 20% ===
  const ticketWeight = 20;
  let avgTicket = 0;
  let ticketNorm = 0;

  if (wonDeals.length > 0) {
    avgTicket = calcAvgTicket(wonDeals);

    // Get all average tickets to normalize
    const allAcctNames = new Map<string, PipelineOpportunity[]>();
    for (const deal of allPipeline) {
      if (deal.account && deal.deal_stage === 'Won') {
        if (!allAcctNames.has(deal.account)) {
          allAcctNames.set(deal.account, []);
        }
        allAcctNames.get(deal.account)!.push(deal);
      }
    }

    const allAvgTickets = Array.from(allAcctNames.values()).map((deals) => calcAvgTicket(deals));
    const minTicket = allAvgTickets.length > 0 ? Math.min(...allAvgTickets) : 0;
    const maxTicket = allAvgTickets.length > 0 ? Math.max(...allAvgTickets) : 1;

    ticketNorm = normalizeValue(avgTicket, minTicket, maxTicket);
  }

  const ticketContribution = ticketNorm * ticketWeight;

  factors.push({
    name: 'Ticket Médio',
    weight: ticketWeight,
    raw_value: `$${avgTicket.toFixed(2)}`,
    normalized_value: ticketNorm,
    contribution: ticketContribution,
    explanation: `Média de $${avgTicket.toFixed(2)} em deals Won — ${
      wonDeals.length === 0 ? 'Nenhuma venda fechada ainda' : 'Alto potencial de receita'
    }`,
  });

  // === FACTOR 3: Volume de atividade — 15% ===
  const volumeWeight = 15;
  const totalDeals = accountDeals.length;
  const volumeNorm = calcActivityVolume(totalDeals, allPipeline);
  const volumeContribution = volumeNorm * volumeWeight;

  factors.push({
    name: 'Volume de Atividade',
    weight: volumeWeight,
    raw_value: `${totalDeals} deals`,
    normalized_value: volumeNorm,
    contribution: volumeContribution,
    explanation: `Total de ${totalDeals} deals (Won+Lost+Engaging+Prospecting) — ${
      volumeNorm >= 0.7 ? 'Conta altamente engajada' : 'Conta com atividade moderada'
    }`,
  });

  // === FACTOR 4: Pipeline Ativo — 15% ===
  const activeDealsCount = engagingDeals.length + prospectingDeals.length;
  const activePipelineWeight = 15;
  const activePipelineNorm = calcPipelineActiveCount(activeDealsCount, allPipeline);
  const activePipelineContribution = activePipelineNorm * activePipelineWeight;

  factors.push({
    name: 'Pipeline Ativo',
    weight: activePipelineWeight,
    raw_value: `${activeDealsCount} deals`,
    normalized_value: activePipelineNorm,
    contribution: activePipelineContribution,
    explanation: `${engagingDeals.length} Engaging + ${prospectingDeals.length} Prospecting — Oportunidades imediatas`,
  });

  // === FACTOR 5: Recência — 10% ===
  const recencyWeight = 10;
  const recencyNorm = calcRecency(accountDeals);
  const recencyContribution = recencyNorm * recencyWeight;

  const lastDealDate = accountDeals.length > 0
    ? new Date(Math.max(...accountDeals.map((d) => (d.close_date || d.engage_date).getTime())))
    : null;

  const daysAgo = lastDealDate
    ? Math.floor((new Date().getTime() - lastDealDate.getTime()) / (1000 * 60 * 60 * 24))
    : 0;

  factors.push({
    name: 'Recência',
    weight: recencyWeight,
    raw_value: `${daysAgo} dias`,
    normalized_value: recencyNorm,
    contribution: recencyContribution,
    explanation: `Último deal há ${daysAgo} dias — ${
      recencyNorm >= 0.7 ? 'Conta ativa recentemente' : 'Conta pode estar dormindo'
    }`,
  });

  // === FACTOR 6: Tamanho da Empresa — 10% ===
  const companyWeight = 10;
  let companySizeNorm = 0.5;
  let companySizeExplanation = 'Dados da conta não disponíveis';

  if (accountData) {
    // Normalize by employees and revenue
    const employeeCounts = allAccounts.map((a) => a.employees).filter((e) => e > 0);
    const revenues = allAccounts.map((a) => a.revenue).filter((r) => r > 0);

    const minEmployees = employeeCounts.length > 0 ? Math.min(...employeeCounts) : 0;
    const maxEmployees = employeeCounts.length > 0 ? Math.max(...employeeCounts) : 1;

    const minRevenue = revenues.length > 0 ? Math.min(...revenues) : 0;
    const maxRevenue = revenues.length > 0 ? Math.max(...revenues) : 1;

    const employeesNorm = normalizeValue(accountData.employees, minEmployees, maxEmployees);
    const revenueNorm = normalizeValue(accountData.revenue, minRevenue, maxRevenue);

    companySizeNorm = (employeesNorm + revenueNorm) / 2;
    companySizeExplanation = `${accountData.employees} employees, $${accountData.revenue.toLocaleString()} revenue`;
  }

  const companySizeContribution = companySizeNorm * companyWeight;

  factors.push({
    name: 'Tamanho da Empresa',
    weight: companyWeight,
    raw_value: accountData ? `${accountData.employees}e` : '—',
    normalized_value: companySizeNorm,
    contribution: companySizeContribution,
    explanation: companySizeExplanation,
  });

  // === FACTOR 7: Diversidade de Produtos — 5% ===
  const diversityWeight = 5;
  const diversityNorm = calcProductDiversity(accountDeals, allProducts);
  const diversityContribution = diversityNorm * diversityWeight;

  const uniqueSeries = new Set(
    accountDeals.map((d) => allProducts.find((p) => p.product === d.product)?.series).filter(Boolean)
  );

  factors.push({
    name: 'Diversidade de Produtos',
    weight: diversityWeight,
    raw_value: `${uniqueSeries.size} séries`,
    normalized_value: diversityNorm,
    contribution: diversityContribution,
    explanation: `${uniqueSeries.size} séries diferentes compradas — ${
      uniqueSeries.size >= 2 ? 'Cliente bem consolidado' : 'Oportunidade de expansão'
    }`,
  });

  // Calculate final score
  const totalContribution = factors.reduce((sum, f) => sum + f.contribution, 0);
  const score = Math.round(totalContribution);

  return {
    account: accountName,
    score,
    tier: assignAccountTier(score),
    factors,
    deals_summary: {
      total: accountDeals.length,
      won: wonDeals.length,
      lost: lostDeals.length,
      engaging: engagingDeals.length,
      prospecting: prospectingDeals.length,
    },
    win_rate: winRate,
    avg_ticket: avgTicket,
    revenue_total: wonDeals.reduce((sum, d) => sum + d.close_value, 0),
    last_deal_date: lastDealDate,
    insufficient_data: !hasEnoughData,
  };
}

/**
 * Assign tier based on account score
 */
function assignAccountTier(score: number): 'HOT' | 'WARM' | 'COOL' | 'COLD' {
  if (score >= 80) return 'HOT';
  if (score >= 60) return 'WARM';
  if (score >= 40) return 'COOL';
  return 'COLD';
}
