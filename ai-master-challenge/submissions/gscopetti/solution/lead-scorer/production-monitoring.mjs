/**
 * Production Monitoring System
 * Correlates Scorer V2 predictions with actual Win/Loss outcomes
 *
 * Validates:
 * - Are HOT deals actually winning more?
 * - Are COLD deals actually losing more?
 * - What's the lift vs random selection?
 */

import fs from 'fs';
import path from 'path';
import { parse } from 'csv-parse/sync';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============================================================================
// 1. Load CSVs
// ============================================================================

function loadCSV(filename) {
  const filepath = path.join(__dirname, '..', 'crm_data_base', filename);
  const content = fs.readFileSync(filepath, 'utf-8');
  return parse(content, { columns: true });
}

const pipeline = loadCSV('sales_pipeline.csv');
const accounts = loadCSV('accounts.csv');
const products = loadCSV('products.csv');
const salesTeams = loadCSV('sales_teams.csv');

// ============================================================================
// 2. V2 Scoring Functions (mirrored from useDealScoring.ts)
// ============================================================================

const BASE_DATE = new Date('2017-12-31');

// Get all closed deals for calculation of win rates
const closedDeals = pipeline.filter(d => d.deal_stage === 'Won' || d.deal_stage === 'Lost');

function calcWinRate(deals) {
  if (!deals || deals.length === 0) return 0.63;
  const won = deals.filter(d => d.deal_stage === 'Won').length;
  return won / deals.length;
}

function calcValorPilar(productName, closedDealsOfProduct, allProducts) {
  const product = allProducts.find((p) => p.product === productName);
  if (!product) return 50;

  const wonCount = closedDealsOfProduct.filter((d) => d.deal_stage === 'Won').length;
  const productWinRate = closedDealsOfProduct.length > 0
    ? wonCount / closedDealsOfProduct.length
    : 0.63;

  const expectedValue = parseFloat(product.sales_price || 0) * productWinRate;

  const allProductsEV = allProducts.map((p) => {
    const pDeals = closedDeals.filter((d) => d.product === p.product);
    const pWinRate = pDeals.length > 0
      ? pDeals.filter((d) => d.deal_stage === 'Won').length / pDeals.length
      : 0.63;
    return parseFloat(p.sales_price || 0) * pWinRate;
  });

  const maxEV = Math.max(...allProductsEV, 1);
  const minEV = Math.min(...allProductsEV, 1);

  if (minEV === maxEV) return 50;
  const logEV = Math.log(expectedValue + 1);
  const logMin = Math.log(minEV + 1);
  const logMax = Math.log(maxEV + 1);

  const normalized = (logEV - logMin) / (logMax - logMin);
  return Math.round(Math.max(0, Math.min(100, normalized * 100)));
}

function calcMomentumPilar(daysInPipeline) {
  if (daysInPipeline < 8) {
    return Math.round((daysInPipeline / 8) * 50 + 50 - 10);
  }
  if (daysInPipeline <= 14) {
    return Math.round((daysInPipeline - 8) / 6 * 30);
  }
  if (daysInPipeline <= 30) {
    return 100;
  }
  if (daysInPipeline <= 60) {
    return Math.round(100 - ((daysInPipeline - 30) / 30) * 50);
  }
  if (daysInPipeline <= 90) {
    return Math.round(50 - ((daysInPipeline - 60) / 30) * 30);
  }
  return 20;
}

function calcFitContaPilar(account) {
  if (!account) return 50;

  const revenue = parseFloat(account.revenue || 0);
  let bucketScore = 0.3;

  if (revenue >= 500000000) bucketScore = 1.0;
  else if (revenue >= 50000000) bucketScore = 0.8;
  else if (revenue >= 1000000) bucketScore = 0.6;
  else bucketScore = 0.3;

  return Math.round(bucketScore * 100);
}

function calcQualidadeRepPilar(agentName, closedDealsOfAgent, allTeamMembers) {
  if (!agentName) return 50;

  const agentDeals = closedDealsOfAgent.filter(d => d.sales_agent === agentName);
  const agentWinRate = agentDeals.length > 0
    ? agentDeals.filter(d => d.deal_stage === 'Won').length / agentDeals.length
    : 0.5;

  const allWinRates = allTeamMembers.map(agent => {
    const deals = closedDealsOfAgent.filter(d => d.sales_agent === agent.sales_agent);
    return deals.length > 0
      ? deals.filter(d => d.deal_stage === 'Won').length / deals.length
      : 0.5;
  });

  const MIN = Math.min(...allWinRates, 0.4);
  const MAX = Math.max(...allWinRates, 0.8);

  const normalized = (agentWinRate - MIN) / (MAX - MIN);
  return Math.round(Math.max(0, Math.min(100, normalized * 100)));
}

function calculateDealScoreV2(deal, allProducts, closedDeals, allTeams) {
  const account = accounts.find(a => a.account === deal.account);
  const closedProductDeals = closedDeals.filter(d => d.product === deal.product);

  const valor = calcValorPilar(deal.product, closedProductDeals, allProducts);

  const daysInPipeline = Math.floor(
    (BASE_DATE.getTime() - new Date(deal.engage_date).getTime()) / (1000 * 60 * 60 * 24)
  );
  const momentum = calcMomentumPilar(daysInPipeline);

  const fit = calcFitContaPilar(account);

  const qualidade = calcQualidadeRepPilar(deal.sales_agent, closedDeals, allTeams);

  const score = (valor * 0.4) + (momentum * 0.25) + (fit * 0.15) + (qualidade * 0.2);

  let tier = 'COLD';
  if (score >= 80) tier = 'HOT';
  else if (score >= 60) tier = 'WARM';
  else if (score >= 40) tier = 'COOL';

  return { score: Math.round(score), tier, valor, momentum, fit, qualidade };
}

// ============================================================================
// 3. Score All Deals (Won/Lost only)
// ============================================================================

const allScoredDeals = closedDeals
  .map(deal => {
    const scoring = calculateDealScoreV2(deal, products, closedDeals, salesTeams);

    return {
      opportunity_id: deal.opportunity_id,
      sales_agent: deal.sales_agent,
      product: deal.product,
      account: deal.account,
      deal_stage: deal.deal_stage,
      is_won: deal.deal_stage === 'Won',
      close_value: parseFloat(deal.close_value || 0),
      score: scoring.score,
      tier: scoring.tier,
      valor: scoring.valor,
      momentum: scoring.momentum,
      fit: scoring.fit,
      qualidade: scoring.qualidade
    };
  });

console.log(`\n📊 SCORED ${allScoredDeals.length} DEALS (Won/Lost only)\n`);

// ============================================================================
// 4. Calculate Metrics
// ============================================================================

function calculateMetrics(deals) {
  const byTier = {
    HOT: { total: 0, won: 0, lost: 0, revenue: 0 },
    WARM: { total: 0, won: 0, lost: 0, revenue: 0 },
    COOL: { total: 0, won: 0, lost: 0, revenue: 0 },
    COLD: { total: 0, won: 0, lost: 0, revenue: 0 }
  };

  for (const deal of deals) {
    const tier = deal.tier;
    byTier[tier].total++;
    if (deal.is_won) {
      byTier[tier].won++;
      byTier[tier].revenue += deal.close_value;
    } else {
      byTier[tier].lost++;
    }
  }

  // Calculate win rates and metrics
  const metrics = {};
  let totalWon = 0, totalValue = 0;

  for (const [tier, data] of Object.entries(byTier)) {
    const winRate = data.total > 0 ? data.won / data.total : 0;
    const avgValue = data.won > 0 ? data.revenue / data.won : 0;

    metrics[tier] = {
      total: data.total,
      won: data.won,
      lost: data.lost,
      winRate: winRate,
      precision: (data.won / (data.won + data.lost)) || 0, // of deals in this tier, % were won
      revenue: data.revenue,
      avgValue: avgValue
    };

    totalWon += data.won;
    totalValue += data.revenue;
  }

  return { byTier: metrics, totalWon, totalValue };
}

const { byTier, totalWon, totalValue } = calculateMetrics(allScoredDeals);
const scoredDeals = allScoredDeals;

// ============================================================================
// 5. Display Results
// ============================================================================

console.log('═══════════════════════════════════════════════════════════════════════════');
console.log('📈 WIN RATES BY TIER (Actual Close Rates)');
console.log('═══════════════════════════════════════════════════════════════════════════\n');

let topTierMetrics = null;

for (const [tier, metrics] of Object.entries(byTier)) {
  const color = tier === 'HOT' ? '🔥' : tier === 'WARM' ? '🟡' : tier === 'COOL' ? '🔵' : '⚪';
  const winPercent = (metrics.winRate * 100).toFixed(1);
  const precisionPercent = (metrics.precision * 100).toFixed(1);

  console.log(`${color} ${tier.padEnd(6)} | Deals: ${metrics.total.toString().padStart(3)} | Won: ${metrics.won.toString().padStart(3)} | Lost: ${metrics.lost.toString().padStart(3)}`);
  console.log(`         Win Rate: ${winPercent}% | Precision: ${precisionPercent}% | Revenue: $${metrics.revenue.toLocaleString()}`);
  console.log('');

  if (tier === 'HOT' || tier === 'WARM') {
    if (!topTierMetrics) topTierMetrics = metrics;
  }
}

// ============================================================================
// 6. Calculate Lift vs Random Selection
// ============================================================================

const baselineWinRate = totalWon / scoredDeals.length;
const topTierWinRate = byTier.HOT.winRate;
const warmTierWinRate = byTier.WARM.winRate;
const combinedTopWinRate = (byTier.HOT.won + byTier.WARM.won) / (byTier.HOT.total + byTier.WARM.total);

const lift = baselineWinRate > 0 ? (topTierWinRate / baselineWinRate) : 0;
const warmLift = baselineWinRate > 0 ? (warmTierWinRate / baselineWinRate) : 0;
const combinedLift = baselineWinRate > 0 ? (combinedTopWinRate / baselineWinRate) : 0;

console.log('═══════════════════════════════════════════════════════════════════════════');
console.log('🎯 LIFT vs RANDOM SELECTION');
console.log('═══════════════════════════════════════════════════════════════════════════\n');

console.log(`Random Baseline Win Rate: ${(baselineWinRate * 100).toFixed(1)}%`);
console.log(`HOT Tier Win Rate: ${(topTierWinRate * 100).toFixed(1)}% (Lift: ${lift.toFixed(2)}x)`);
console.log(`WARM Tier Win Rate: ${(warmTierWinRate * 100).toFixed(1)}% (Lift: ${warmLift.toFixed(2)}x)`);
console.log(`HOT + WARM Win Rate: ${(combinedTopWinRate * 100).toFixed(1)}% (Lift: ${combinedLift.toFixed(2)}x)`);
console.log('');

// ============================================================================
// 7. ROI Analysis
// ============================================================================

const topTierDeals = scoredDeals.filter(d => d.tier === 'HOT' || d.tier === 'WARM');
const topTierRevenue = topTierDeals.filter(d => d.is_won).reduce((sum, d) => sum + d.close_value, 0);
const topTierAttempts = topTierDeals.length;
const topTierWins = topTierDeals.filter(d => d.is_won).length;

const focusOnTopRevenue = topTierRevenue;
const focusOnTopAttempts = topTierAttempts;
const focusROI = topTierWins > 0 ? (focusOnTopRevenue / focusOnTopAttempts).toFixed(0) : 0;

console.log('═══════════════════════════════════════════════════════════════════════════');
console.log('💰 ROI ANALYSIS - Focus on HOT + WARM Tiers');
console.log('═══════════════════════════════════════════════════════════════════════════\n');

console.log(`Deals Attempted (HOT + WARM): ${topTierAttempts}`);
console.log(`Deals Won: ${topTierWins}`);
console.log(`Total Revenue Generated: $${topTierRevenue.toLocaleString()}`);
console.log(`Revenue per Attempt: $${focusROI}`);
console.log(`Win Rate: ${((topTierWins / topTierAttempts) * 100).toFixed(1)}%`);
console.log('');

// ============================================================================
// 8. Top Performers Analysis
// ============================================================================

console.log('═══════════════════════════════════════════════════════════════════════════');
console.log('⭐ TOP DEALS BY SCORE (Actually Won)');
console.log('═══════════════════════════════════════════════════════════════════════════\n');

const topWonDeals = scoredDeals
  .filter(d => d.is_won)
  .sort((a, b) => b.score - a.score)
  .slice(0, 10);

let counter = 1;
for (const deal of topWonDeals) {
  const tierColor = deal.tier === 'HOT' ? '🔥' : '🟡';
  console.log(`${counter}. ${tierColor} Score ${deal.score} | ${deal.product.padEnd(16)} | $${deal.close_value.toString().padStart(5)} | ${deal.sales_agent}`);
  counter++;
}
console.log('');

// ============================================================================
// 9. False Positives (Scored High but Lost)
// ============================================================================

console.log('═══════════════════════════════════════════════════════════════════════════');
console.log('⚠️  FALSE POSITIVES (Scored HOT/WARM but Lost)');
console.log('═══════════════════════════════════════════════════════════════════════════\n');

const falsePositives = scoredDeals
  .filter(d => !d.is_won && (d.tier === 'HOT' || d.tier === 'WARM'))
  .sort((a, b) => b.score - a.score)
  .slice(0, 5);

if (falsePositives.length > 0) {
  let counter2 = 1;
  for (const deal of falsePositives) {
    console.log(`${counter2}. Score ${deal.score} [${deal.tier}] | ${deal.product.padEnd(16)} | ${deal.sales_agent}`);
    console.log(`   Valor: ${deal.valor}/100 | Momentum: ${deal.momentum}/100 | Fit: ${deal.fit}/100 | Qualidade: ${deal.qualidade}/100`);
    counter2++;
  }
} else {
  console.log('✅ No false positives! All HOT/WARM deals were actually won.');
}
console.log('');

// ============================================================================
// 10. False Negatives (Scored Low but Won)
// ============================================================================

console.log('═══════════════════════════════════════════════════════════════════════════');
console.log('💎 FALSE NEGATIVES (Scored COOL/COLD but Won - Hidden Gems)');
console.log('═══════════════════════════════════════════════════════════════════════════\n');

const falseNegatives = scoredDeals
  .filter(d => d.is_won && (d.tier === 'COOL' || d.tier === 'COLD'))
  .sort((a, b) => b.score - a.score)
  .slice(0, 5);

if (falseNegatives.length > 0) {
  let counter3 = 1;
  for (const deal of falseNegatives) {
    console.log(`${counter3}. Score ${deal.score} [${deal.tier}] | ${deal.product.padEnd(16)} | $${deal.close_value.toString().padStart(5)} | ${deal.sales_agent}`);
    counter3++;
  }
} else {
  console.log('✅ No false negatives! All won deals were properly scored as HOT/WARM.');
}
console.log('');

// ============================================================================
// 11. Scorer Correlation Statistics
// ============================================================================

console.log('═══════════════════════════════════════════════════════════════════════════');
console.log('📊 CORRELATION ANALYSIS (Pillar Impact on Win Rate)');
console.log('═══════════════════════════════════════════════════════════════════════════\n');

// Group by pillar scores
const pillarAnalysis = {
  valor: { high: [], low: [] },
  momentum: { high: [], low: [] },
  fit: { high: [], low: [] },
  qualidade: { high: [], low: [] }
};

for (const deal of scoredDeals) {
  if (deal.valor >= 70) pillarAnalysis.valor.high.push(deal);
  else pillarAnalysis.valor.low.push(deal);

  if (deal.momentum >= 70) pillarAnalysis.momentum.high.push(deal);
  else pillarAnalysis.momentum.low.push(deal);

  if (deal.fit >= 70) pillarAnalysis.fit.high.push(deal);
  else pillarAnalysis.fit.low.push(deal);

  if (deal.qualidade >= 70) pillarAnalysis.qualidade.high.push(deal);
  else pillarAnalysis.qualidade.low.push(deal);
}

const pillars = ['valor', 'momentum', 'fit', 'qualidade'];
for (const pillar of pillars) {
  const highWR = pillarAnalysis[pillar].high.filter(d => d.is_won).length / pillarAnalysis[pillar].high.length;
  const lowWR = pillarAnalysis[pillar].low.filter(d => d.is_won).length / pillarAnalysis[pillar].low.length;
  const impact = highWR - lowWR;

  console.log(`📍 ${pillar.padEnd(10)} | High (>=70): ${(highWR * 100).toFixed(1)}% | Low (<70): ${(lowWR * 100).toFixed(1)}% | Impact: ${(impact * 100).toFixed(1)}%`);
}
console.log('');

// ============================================================================
// 12. Export Summary
// ============================================================================

const summary = {
  timestamp: new Date().toISOString(),
  totalDeals: scoredDeals.length,
  totalWon: totalWon,
  baselineWinRate: baselineWinRate,
  byTier,
  lift: {
    hot: lift,
    warm: warmLift,
    combined: combinedLift
  },
  roi: {
    topTierAttempts,
    topTierWins,
    topTierRevenue,
    revenuePerAttempt: focusROI
  }
};

console.log('═══════════════════════════════════════════════════════════════════════════');
console.log('✅ CONCLUSION: Scorer V2 Validation');
console.log('═══════════════════════════════════════════════════════════════════════════\n');

if (lift > 1.5) {
  console.log(`✅ EXCELLENT: HOT tier has ${lift.toFixed(2)}x better win rate than baseline`);
} else if (lift > 1.2) {
  console.log(`✅ GOOD: HOT tier has ${lift.toFixed(2)}x better win rate than baseline`);
} else {
  console.log(`⚠️  WARNING: HOT tier has only ${lift.toFixed(2)}x better win rate. Model needs tuning.`);
}

if (combinedLift > 1.3) {
  console.log(`✅ STRONG: HOT+WARM combined has ${combinedLift.toFixed(2)}x better win rate`);
}

if (falseNegatives.length === 0) {
  console.log('✅ PERFECT: No hidden gems - model captures all winners');
} else {
  console.log(`⚠️  ${falseNegatives.length} false negatives - review model calibration`);
}

console.log(`✅ ROI: Focusing on HOT+WARM yields $${focusROI} per attempt`);
console.log('\n');

// Save summary to JSON for dashboard
fs.writeFileSync(
  path.join(__dirname, 'production-monitoring-summary.json'),
  JSON.stringify(summary, null, 2)
);

console.log('📁 Summary saved to: production-monitoring-summary.json');
console.log('');
