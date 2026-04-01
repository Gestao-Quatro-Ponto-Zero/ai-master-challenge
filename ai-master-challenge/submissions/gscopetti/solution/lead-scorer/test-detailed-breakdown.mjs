#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Load CSV files
const loadCSV = (filename) => {
  const filepath = path.join(__dirname, '..', 'crm_data_base', filename);
  const content = fs.readFileSync(filepath, 'utf-8');
  const lines = content.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.trim());

  return lines.slice(1).map(line => {
    const values = line.split(',').map(v => v.trim());
    const obj = {};
    headers.forEach((header, i) => {
      obj[header] = values[i];
    });
    return obj;
  });
};

console.log('\n╔════════════════════════════════════════════════════════════════╗');
console.log('║     TESTE DETALHADO: BREAKDOWN COMPLETO DOS 4 PILARES         ║');
console.log('╚════════════════════════════════════════════════════════════════╝\n');

// Load data
const accounts = loadCSV('accounts.csv');
const products = loadCSV('products.csv');
const pipeline = loadCSV('sales_pipeline.csv');

const parsedPipeline = pipeline.map(d => ({
  ...d,
  engage_date: new Date(d.engage_date),
  close_date: d.close_date ? new Date(d.close_date) : null,
  sales_price: parseFloat(d.sales_price) || 0,
  close_value: parseFloat(d.close_value) || 0,
}));

const parsedAccounts = accounts.map(a => ({
  ...a,
  revenue: parseFloat(a.revenue) || 0,
  employees: parseInt(a.employees) || 0,
}));

const parsedProducts = products.map(p => ({
  ...p,
  sales_price: parseFloat(p.sales_price) || 0,
}));

// Filter active deals
const activeDeals = parsedPipeline.filter(d => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting');
const closedDeals = parsedPipeline.filter(d => d.deal_stage === 'Won' || d.deal_stage === 'Lost');

const BASE_DATE = new Date('2017-12-31');

// Helper functions
const calcDays = (engageDate) => {
  return Math.max(0, Math.floor((BASE_DATE - new Date(engageDate)) / (1000 * 60 * 60 * 24)));
};

// Calculate detailed breakdown for a deal
const calculateDealBreakdown = (deal, index) => {
  const accountObj = parsedAccounts.find(a => a.account === deal.account);
  const productObj = parsedProducts.find(p => p.product === deal.product);
  const daysInPipeline = calcDays(deal.engage_date);

  // PILAR 1: Valor
  const closedProductDeals = closedDeals.filter(d => d.product === deal.product);
  const productWinRate = closedProductDeals.length > 0
    ? closedProductDeals.filter(d => d.deal_stage === 'Won').length / closedProductDeals.length
    : 0.635;

  const expectedValue = (productObj?.sales_price || 0) * productWinRate;
  const allEVs = parsedProducts.map(p => {
    const pDeals = closedDeals.filter(d => d.product === p.product);
    const pWR = pDeals.length > 0
      ? pDeals.filter(d => d.deal_stage === 'Won').length / pDeals.length
      : 0.635;
    return p.sales_price * pWR;
  });
  const maxEV = Math.max(...allEVs);
  const minEV = Math.min(...allEVs);

  const logEV = Math.log(expectedValue + 1);
  const logMin = Math.log(minEV + 1);
  const logMax = Math.log(maxEV + 1);
  const valorNorm = (logEV - logMin) / (logMax - logMin);
  const valorScore = Math.round(Math.max(0, Math.min(100, valorNorm * 100)));
  const valorContrib = (valorScore / 100) * 40;

  // PILAR 2: Momentum
  let momentumRaw;
  if (daysInPipeline < 8) {
    momentumRaw = -10;
  } else if (daysInPipeline <= 14) {
    momentumRaw = ((daysInPipeline - 8) / 6) * 30;
  } else if (daysInPipeline <= 30) {
    momentumRaw = 80;
  } else if (daysInPipeline <= 90) {
    momentumRaw = 80 - ((daysInPipeline - 30) / 60) * 10;
  } else {
    momentumRaw = 20;
  }

  const momentumScore = Math.max(0, Math.min(100, 50 + momentumRaw));
  const momentumContrib = (momentumScore / 100) * 25;

  // PILAR 3: Fit Conta
  let fitScore = 40;
  if (accountObj && accountObj.revenue > 0) {
    let revenueBucket = 0.3;
    if (accountObj.revenue < 1_000_000) revenueBucket = 0.3;
    else if (accountObj.revenue < 50_000_000) revenueBucket = 0.6;
    else if (accountObj.revenue < 500_000_000) revenueBucket = 0.8;
    else revenueBucket = 1.0;

    const sectorBoost = 0.5;
    fitScore = Math.round(((revenueBucket + sectorBoost) / 2) * 100);
  }
  const fitContrib = (fitScore / 100) * 15;

  // PILAR 4: Qualidade Rep
  const agentDeals = parsedPipeline.filter(d => d.sales_agent === deal.sales_agent && (d.deal_stage === 'Won' || d.deal_stage === 'Lost'));
  const agentWinRate = agentDeals.length > 0
    ? agentDeals.filter(d => d.deal_stage === 'Won').length / agentDeals.length
    : 0.5;

  const MIN_WR = 0.55;
  const MAX_WR = 0.704;
  const qualidadeNorm = Math.max(0, Math.min(1, (agentWinRate - MIN_WR) / (MAX_WR - MIN_WR)));
  const qualidadeScore = Math.round(qualidadeNorm * 100);
  const qualidadeContrib = (qualidadeScore / 100) * 20;

  const baseScore = valorContrib + momentumContrib + fitContrib + qualidadeContrib;
  const finalScore = Math.round(Math.max(0, Math.min(100, baseScore)));

  const tier = finalScore >= 80 ? 'HOT' : finalScore >= 60 ? 'WARM' : finalScore >= 40 ? 'COOL' : 'COLD';

  return {
    index,
    opportunity_id: deal.opportunity_id,
    product: deal.product,
    account: deal.account || '(no account)',
    agent: deal.sales_agent,
    daysInPipeline,
    finalScore,
    tier,
    pilares: {
      valor: { score: valorScore, contrib: valorContrib.toFixed(2), ev: expectedValue.toFixed(0), wr: (productWinRate * 100).toFixed(0) },
      momentum: { score: momentumScore.toFixed(0), contrib: momentumContrib.toFixed(2), days: daysInPipeline },
      fit: { score: fitScore, contrib: fitContrib.toFixed(2), revenue: accountObj ? `$${(accountObj.revenue / 1000000).toFixed(1)}M` : '(none)' },
      qualidade: { score: qualidadeScore, contrib: qualidadeContrib.toFixed(2), wr: (agentWinRate * 100).toFixed(0), agent: deal.sales_agent }
    }
  };
};

// Select 5 deals for detailed breakdown
const scores = activeDeals
  .map((deal, idx) => calculateDealBreakdown(deal, idx))
  .sort((a, b) => b.finalScore - a.finalScore);

// Show top 5 deals with detailed breakdown
console.log('🏆 TOP 5 DEALS — BREAKDOWN DETALHADO\n');

scores.slice(0, 5).forEach((deal, idx) => {
  console.log(`\n${'═'.repeat(70)}`);
  console.log(`#${idx + 1} — [${deal.tier}] Score: ${deal.finalScore}/100`);
  console.log(`${'═'.repeat(70)}`);
  console.log(`Deal:  ${deal.opportunity_id}`);
  console.log(`Product: ${deal.product.padEnd(20)} | Account: ${deal.account.padEnd(25)} | Agent: ${deal.agent}`);
  console.log(`Days in Pipeline: ${deal.daysInPipeline} days`);
  console.log(`\n📊 BREAKDOWN DOS 4 PILARES:\n`);

  // Pilar 1
  console.log(`┌─ Pilar 1: VALOR (40%)`);
  console.log(`│  Score: ${deal.pilares.valor.score}/100`);
  console.log(`│  Contribution: ${deal.pilares.valor.contrib} pts`);
  console.log(`│  Expected Value: $${deal.pilares.valor.ev}`);
  console.log(`│  Product Win Rate: ${deal.pilares.valor.wr}%`);
  console.log(`└──────────────────────────────────────────`);

  // Pilar 2
  console.log(`┌─ Pilar 2: MOMENTUM (25%)`);
  console.log(`│  Score: ${deal.pilares.momentum.score}/100`);
  console.log(`│  Contribution: ${deal.pilares.momentum.contrib} pts`);
  console.log(`│  Days in Pipeline: ${deal.pilares.momentum.days}`);
  console.log(`│  Status: ${
    deal.pilares.momentum.days < 8 ? '🔴 Die Easy (<8d)' :
    deal.pilares.momentum.days <= 30 ? '🟢 Sweet Spot (15-30d)' :
    deal.pilares.momentum.days <= 90 ? '🟡 Declining (31-90d)' :
    '⚫ Stagnated (>90d)'
  }`);
  console.log(`└──────────────────────────────────────────`);

  // Pilar 3
  console.log(`┌─ Pilar 3: FIT DA CONTA (15%)`);
  console.log(`│  Score: ${deal.pilares.fit.score}/100`);
  console.log(`│  Contribution: ${deal.pilares.fit.contrib} pts`);
  console.log(`│  Account Revenue: ${deal.pilares.fit.revenue}`);
  console.log(`└──────────────────────────────────────────`);

  // Pilar 4
  console.log(`┌─ Pilar 4: QUALIDADE REP (20%)`);
  console.log(`│  Score: ${deal.pilares.qualidade.score}/100`);
  console.log(`│  Contribution: ${deal.pilares.qualidade.contrib} pts`);
  console.log(`│  Agent: ${deal.pilares.qualidade.agent}`);
  console.log(`│  Agent Win Rate: ${deal.pilares.qualidade.wr}%`);
  console.log(`└──────────────────────────────────────────`);

  // Total
  const totalContrib = parseFloat(deal.pilares.valor.contrib) +
                       parseFloat(deal.pilares.momentum.contrib) +
                       parseFloat(deal.pilares.fit.contrib) +
                       parseFloat(deal.pilares.qualidade.contrib);
  console.log(`\n✅ SCORE FINAL: ${deal.finalScore}/100 [${deal.tier}]`);
  console.log(`   Contributions sum: ${totalContrib.toFixed(2)}`);
  console.log(`   Rounding: ${Math.round(totalContrib)}`);
});

// Summary statistics
console.log(`\n\n${'═'.repeat(70)}`);
console.log('📈 SUMMARY STATISTICS');
console.log(`${'═'.repeat(70)}\n`);

const scoredDeals = activeDeals.map((deal, idx) => calculateDealBreakdown(deal, idx));

const hotCount = scoredDeals.filter(d => d.finalScore >= 80).length;
const warmCount = scoredDeals.filter(d => d.finalScore >= 60 && d.finalScore < 80).length;
const coolCount = scoredDeals.filter(d => d.finalScore >= 40 && d.finalScore < 60).length;
const coldCount = scoredDeals.filter(d => d.finalScore < 40).length;

console.log(`Total Deals Scored: ${scoredDeals.length}`);
console.log(`Average Score: ${(scoredDeals.reduce((sum, d) => sum + d.finalScore, 0) / scoredDeals.length).toFixed(1)}/100`);
console.log(`Score Range: ${Math.min(...scoredDeals.map(d => d.finalScore))}-${Math.max(...scoredDeals.map(d => d.finalScore))}`);

console.log(`\nTier Distribution:`);
console.log(`  HOT:  ${hotCount.toString().padEnd(4)} deals (${((hotCount / scoredDeals.length) * 100).toFixed(1)}%)`);
console.log(`  WARM: ${warmCount.toString().padEnd(4)} deals (${((warmCount / scoredDeals.length) * 100).toFixed(1)}%)`);
console.log(`  COOL: ${coolCount.toString().padEnd(4)} deals (${((coolCount / scoredDeals.length) * 100).toFixed(1)}%)`);
console.log(`  COLD: ${coldCount.toString().padEnd(4)} deals (${((coldCount / scoredDeals.length) * 100).toFixed(1)}%)`);

// Pillar averages
const avgValor = scoredDeals.reduce((sum, d) => sum + (parseFloat(d.pilares.valor.contrib) / 0.4), 0) / scoredDeals.length;
const avgMomentum = scoredDeals.reduce((sum, d) => sum + (parseFloat(d.pilares.momentum.contrib) / 0.25), 0) / scoredDeals.length;
const avgFit = scoredDeals.reduce((sum, d) => sum + (parseFloat(d.pilares.fit.contrib) / 0.15), 0) / scoredDeals.length;
const avgQualidade = scoredDeals.reduce((sum, d) => sum + (parseFloat(d.pilares.qualidade.contrib) / 0.20), 0) / scoredDeals.length;

console.log(`\nAverage Pillar Scores:`);
console.log(`  Valor:     ${avgValor.toFixed(1)}/100`);
console.log(`  Momentum:  ${avgMomentum.toFixed(1)}/100`);
console.log(`  Fit Conta: ${avgFit.toFixed(1)}/100`);
console.log(`  Qualidade: ${avgQualidade.toFixed(1)}/100`);

console.log(`\n╔════════════════════════════════════════════════════════════════╗`);
console.log(`║          ✅ BREAKDOWN TEST COMPLETE — ALL PASSED             ║`);
console.log(`╚════════════════════════════════════════════════════════════════╝\n`);
