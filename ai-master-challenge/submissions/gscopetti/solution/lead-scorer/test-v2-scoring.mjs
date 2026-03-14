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
console.log('║     TESTE V2: MODELO 4-PILARES DATA-DRIVEN                      ║');
console.log('╚════════════════════════════════════════════════════════════════╝\n');

// Load data
console.log('📊 Carregando dados...');
const accounts = loadCSV('accounts.csv');
const products = loadCSV('products.csv');
const pipeline = loadCSV('sales_pipeline.csv');

console.log(`   Contas:      ${accounts.length}`);
console.log(`   Produtos:    ${products.length}`);
console.log(`   Pipeline:    ${pipeline.length}\n`);

// Parse dates and numbers
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

console.log(`🎯 Deals Ativos: ${activeDeals.length}`);
console.log(`   Won:  ${closedDeals.filter(d => d.deal_stage === 'Won').length}`);
console.log(`   Lost: ${closedDeals.filter(d => d.deal_stage === 'Lost').length}\n`);

// BASE_DATE for temporal calculation
const BASE_DATE = new Date('2017-12-31');

// Helper: Calculate days in pipeline
const calcDays = (engageDate) => {
  return Math.max(0, Math.floor((BASE_DATE - new Date(engageDate)) / (1000 * 60 * 60 * 24)));
};

// NEW MODEL: Calculate 4 Pilares
console.log('🧮 Calculando 4-Pilares...\n');

const scores = activeDeals.map(deal => {
  const accountObj = parsedAccounts.find(a => a.account === deal.account);
  const productObj = parsedProducts.find(p => p.product === deal.product);
  const daysInPipeline = calcDays(deal.engage_date);

  // PILAR 1: Valor (Expected Value)
  const closedProductDeals = closedDeals.filter(d => d.product === deal.product);
  const productWinRate = closedProductDeals.length > 0
    ? closedProductDeals.filter(d => d.deal_stage === 'Won').length / closedProductDeals.length
    : 0.635;

  const expectedValue = (productObj?.sales_price || 0) * productWinRate;

  // Find max/min EV for all products
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
  const valorContrib = (valorScore / 100) * 40; // ADJUSTED: 40% (was 35%)

  // PILAR 2: Momentum (Win rate curve by time)
  let momentumRaw;
  if (daysInPipeline < 8) {
    momentumRaw = -10; // "die easy"
  } else if (daysInPipeline <= 14) {
    momentumRaw = ((daysInPipeline - 8) / 6) * 30; // 0-30
  } else if (daysInPipeline <= 30) {
    momentumRaw = 80; // sweet spot
  } else if (daysInPipeline <= 90) {
    momentumRaw = 80 - ((daysInPipeline - 30) / 60) * 10; // decline to 70
  } else {
    momentumRaw = 20; // stagnated
  }

  const momentumScore = Math.max(0, Math.min(100, 50 + momentumRaw));
  const momentumContrib = (momentumScore / 100) * 25; // ADJUSTED: 25% (was 30%)

  // PILAR 3: Fit Conta (Revenue bucket + sector)
  let fitScore = 40; // neutral default
  if (accountObj && accountObj.revenue > 0) {
    let revenueBucket = 0.3; // Small
    if (accountObj.revenue < 1_000_000) revenueBucket = 0.3;
    else if (accountObj.revenue < 50_000_000) revenueBucket = 0.6;
    else if (accountObj.revenue < 500_000_000) revenueBucket = 0.8;
    else revenueBucket = 1.0;

    const sectorBoost = 0.5;
    fitScore = Math.round(((revenueBucket + sectorBoost) / 2) * 100);
  }
  const fitContrib = (fitScore / 100) * 15; // ADJUSTED: 15% (was 20%)

  // PILAR 4: Qualidade Rep (Win rate agent normalized to 55%-70.4%)
  const agentDeals = parsedPipeline.filter(d => d.sales_agent === deal.sales_agent && (d.deal_stage === 'Won' || d.deal_stage === 'Lost'));
  const agentWinRate = agentDeals.length > 0
    ? agentDeals.filter(d => d.deal_stage === 'Won').length / agentDeals.length
    : 0.5;

  const MIN_WR = 0.55;
  const MAX_WR = 0.704;
  const qualidadeNorm = Math.max(0, Math.min(1, (agentWinRate - MIN_WR) / (MAX_WR - MIN_WR)));
  const qualidadeScore = Math.round(qualidadeNorm * 100);
  const qualidadeContrib = (qualidadeScore / 100) * 20; // ADJUSTED: 20% (was 15%)

  // NO REDUNDANT PENALTIES
  // Momentum Pilar already captures stagnation effects
  // Fit Conta already captures account data gaps
  // This keeps the model clean and 4-pillar focused

  const baseScore = valorContrib + momentumContrib + fitContrib + qualidadeContrib;
  const finalScore = Math.round(Math.max(0, Math.min(100, baseScore)));

  const tier = finalScore >= 80 ? 'HOT' : finalScore >= 60 ? 'WARM' : finalScore >= 40 ? 'COOL' : 'COLD';

  return {
    opportunity_id: deal.opportunity_id,
    product: deal.product,
    account: deal.account || '(no account)',
    agent: deal.sales_agent,
    daysInPipeline,
    score: finalScore,
    tier,
    valor: { score: valorScore, contrib: valorContrib },
    momentum: { score: momentumScore, contrib: momentumContrib },
    fit: { score: fitScore, contrib: fitContrib },
    qualidade: { score: qualidadeScore, contrib: qualidadeContrib },
  };
});

// Sort by score
scores.sort((a, b) => b.score - a.score);

// Calculate distribution
const distribution = {
  HOT: scores.filter(s => s.tier === 'HOT').length,
  WARM: scores.filter(s => s.tier === 'WARM').length,
  COOL: scores.filter(s => s.tier === 'COOL').length,
  COLD: scores.filter(s => s.tier === 'COLD').length,
};

console.log('✅ 4-Pilares Calculados\n');

// Display distribution
console.log('📊 DISTRIBUIÇÃO DE TIERS:\n');
const tiers = [
  { name: 'HOT', count: distribution.HOT, expected: '5-10%' },
  { name: 'WARM', count: distribution.WARM, expected: '15-25%' },
  { name: 'COOL', count: distribution.COOL, expected: '30-40%' },
  { name: 'COLD', count: distribution.COLD, expected: '25-35%' },
];

tiers.forEach(tier => {
  const pct = ((tier.count / scores.length) * 100).toFixed(1);
  const status = (pct >= 5 && pct <= 10 && tier.name === 'HOT') ||
                 (pct >= 15 && pct <= 25 && tier.name === 'WARM') ||
                 (pct >= 30 && pct <= 40 && tier.name === 'COOL') ||
                 (pct >= 25 && pct <= 35 && tier.name === 'COLD') ? '✅' : '⚠️';
  const bar = '█'.repeat(Math.round(pct / 2));
  console.log(`${status} ${tier.name.padEnd(6)} (${tier.count.toString().padStart(4)}): ${pct.padStart(4)}% ${bar} Expected: ${tier.expected}`);
});

// Display top 15
console.log('\n🏆 TOP 15 DEALS (V2 Model):\n');
scores.slice(0, 15).forEach((deal, idx) => {
  const pillarStr = `V:${deal.valor.score}|M:${deal.momentum.score}|F:${deal.fit.score}|Q:${deal.qualidade.score}`;
  console.log(
    ` ${(idx + 1).toString().padStart(2)}. [${deal.tier}] ${deal.score.toString().padStart(3)} | ${pillarStr.padEnd(30)} | ${deal.product.padEnd(15)} | ${deal.account.substring(0, 20).padEnd(20)} | ${deal.agent.substring(0, 15)}`
  );
});

// Factor analysis
console.log('\n📈 ANÁLISE DOS 4 PILARES:\n');
const avgValor = (scores.reduce((sum, s) => sum + s.valor.score, 0) / scores.length).toFixed(1);
const avgMomentum = (scores.reduce((sum, s) => sum + s.momentum.score, 0) / scores.length).toFixed(1);
const avgFit = (scores.reduce((sum, s) => sum + s.fit.score, 0) / scores.length).toFixed(1);
const avgQualidade = (scores.reduce((sum, s) => sum + s.qualidade.score, 0) / scores.length).toFixed(1);

console.log(`Valor       (35%):  Avg ${avgValor.padStart(5)}/100 | Contrib avg: ${((parseFloat(avgValor) * 0.35) / 100).toFixed(1)}`);
console.log(`Momentum    (30%):  Avg ${avgMomentum.padStart(5)}/100 | Contrib avg: ${((parseFloat(avgMomentum) * 0.30) / 100).toFixed(1)}`);
console.log(`Fit Conta   (20%):  Avg ${avgFit.padStart(5)}/100 | Contrib avg: ${((parseFloat(avgFit) * 0.20) / 100).toFixed(1)}`);
console.log(`Qualidade   (15%):  Avg ${avgQualidade.padStart(5)}/100 | Contrib avg: ${((parseFloat(avgQualidade) * 0.15) / 100).toFixed(1)}`);

// Pillar strength analysis
const strongValor = scores.filter(s => s.valor.score >= 75).length;
const strongMomentum = scores.filter(s => s.momentum.score >= 70).length;
const strongQualidade = scores.filter(s => s.qualidade.score >= 70).length;
console.log(`\nPillar Strength:  ${strongValor} deals com forte Valor | ${strongMomentum} deals com forte Momentum | ${strongQualidade} deals com forte Rep`);

// Summary
console.log('\n📋 RESUMO FINAL:\n');
console.log(`Total de deals scored:     ${scores.length}`);
console.log(`Score médio:               ${(scores.reduce((sum, s) => sum + s.score, 0) / scores.length).toFixed(1)}`);
console.log(`Score mínimo:              ${Math.min(...scores.map(s => s.score))}`);
console.log(`Score máximo:              ${Math.max(...scores.map(s => s.score))}`);

console.log('\n╔════════════════════════════════════════════════════════════════╗');
console.log('║                  ✅ TESTE V2 COMPLETO                         ║');
console.log('╚════════════════════════════════════════════════════════════════╝\n');
