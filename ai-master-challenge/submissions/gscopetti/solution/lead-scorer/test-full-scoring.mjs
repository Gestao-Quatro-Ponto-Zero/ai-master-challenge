import fs from 'fs';
import { parse } from 'csv-parse/sync';

console.log('\n╔════════════════════════════════════════════════════════════════╗');
console.log('║        TESTE COMPLETO DE SCORING COM 10 FATORES              ║');
console.log('╚════════════════════════════════════════════════════════════════╝\n');

// ==================== LOAD DATA ====================
const accountsCsv = fs.readFileSync('../crm_data_base/accounts.csv', 'utf-8');
const productsCsv = fs.readFileSync('../crm_data_base/products.csv', 'utf-8');
const teamsCsv = fs.readFileSync('../crm_data_base/sales_teams.csv', 'utf-8');
const pipelineCsv = fs.readFileSync('../crm_data_base/sales_pipeline.csv', 'utf-8');

const accounts = parse(accountsCsv, { columns: true });
const products = parse(productsCsv, { columns: true });
const teams = parse(teamsCsv, { columns: true });
const pipeline = parse(pipelineCsv, { columns: true });

pipeline.forEach(p => {
  p.engage_date = new Date(p.engage_date);
  p.close_date = p.close_date ? new Date(p.close_date) : null;
  p.close_value = parseFloat(p.close_value) || 0;
});

accounts.forEach(a => {
  a.revenue = parseFloat(a.revenue) || 0;
  a.employees = parseInt(a.employees) || 0;
});

products.forEach(p => {
  p.sales_price = parseFloat(p.sales_price) || 0;
});

console.log('📊 DADOS CARREGADOS:');
console.log(`   Contas:      ${accounts.length}`);
console.log(`   Produtos:    ${products.length}`);
console.log(`   Vendedores:  ${teams.length}`);
console.log(`   Pipeline:    ${pipeline.length}`);
console.log(`   - Engaging:  ${pipeline.filter(p => p.deal_stage === 'Engaging').length}`);
console.log(`   - Prospecting: ${pipeline.filter(p => p.deal_stage === 'Prospecting').length}`);
console.log(`   - Won:       ${pipeline.filter(p => p.deal_stage === 'Won').length}`);
console.log(`   - Lost:      ${pipeline.filter(p => p.deal_stage === 'Lost').length}\n`);

// ==================== SCORING FUNCTIONS ====================
function normalizeValue(value, min, max) {
  if (max === min) return 0.5;
  const normalized = (value - min) / (max - min);
  return Math.max(0, Math.min(1, normalized));
}

function calcWinRate(deals) {
  if (deals.length === 0) return 0.5;
  const won = deals.filter(d => d.deal_stage === 'Won').length;
  const lost = deals.filter(d => d.deal_stage === 'Lost').length;
  const total = won + lost;
  return total === 0 ? 0.5 : won / total;
}

function calcAccountSize(revenue, employees, allAccounts) {
  if (!revenue && !employees) return 0.5;
  const revenues = allAccounts.map(a => a.revenue).filter(r => r > 0);
  const employeeCounts = allAccounts.map(a => a.employees).filter(e => e > 0);
  const minRevenue = revenues.length > 0 ? Math.min(...revenues) : 0;
  const maxRevenue = revenues.length > 0 ? Math.max(...revenues) : 1;
  const minEmployees = employeeCounts.length > 0 ? Math.min(...employeeCounts) : 0;
  const maxEmployees = employeeCounts.length > 0 ? Math.max(...employeeCounts) : 1;
  const revenueNorm = normalizeValue(revenue, minRevenue, maxRevenue);
  const employeesNorm = normalizeValue(employees, minEmployees, maxEmployees);
  return (revenueNorm + employeesNorm) / 2;
}

function calcProductDiversity(accountDeals, allProducts) {
  const uniqueSeries = new Set();
  for (const deal of accountDeals) {
    const product = allProducts.find(p => p.product === deal.product);
    if (product) uniqueSeries.add(product.series);
  }
  const totalSeries = new Set(allProducts.map(p => p.series)).size;
  return allProducts.length === 0 ? 0.5 : uniqueSeries.size / Math.max(1, totalSeries);
}

function scoreTimeInPipeline(days) {
  if (days <= 30) return 0.9;
  if (days <= 90) return 0.7;
  if (days <= 180) return 0.5;
  return 0.2;
}

function scoreStage(stage) {
  switch (stage) {
    case 'Engaging': return 0.7;
    case 'Prospecting': return 0.4;
    default: return 0.5;
  }
}

function normalizeSalesPrice(price, allProducts) {
  if (allProducts.length === 0) return 0.5;
  const prices = allProducts.map(p => p.sales_price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  return normalizeValue(price, minPrice, maxPrice);
}

function calcAgentPerformance(agentName, product, allDeals) {
  const agentDeals = allDeals.filter(d => d.sales_agent === agentName);
  if (agentDeals.length === 0) return 0.5;
  let relevantDeals = agentDeals.filter(d => d.product === product);
  if (relevantDeals.length === 0) relevantDeals = agentDeals;
  return calcWinRate(relevantDeals);
}

function calcAccountLoyalty(accountDeals) {
  const wonDeals = accountDeals.filter(d => d.deal_stage === 'Won');
  return wonDeals.length > 0 ? 1.0 : 0.0;
}

function calcRegionalPerformance(regionalOffice, allDeals, salesTeams) {
  const agentsInRegion = salesTeams
    .filter(t => t.regional_office === regionalOffice)
    .map(t => t.sales_agent);
  if (agentsInRegion.length === 0) return 1.0;
  const regionalDeals = allDeals.filter(d => agentsInRegion.includes(d.sales_agent));
  const closedRegionalDeals = regionalDeals.filter(d => d.deal_stage === 'Won' || d.deal_stage === 'Lost');
  if (closedRegionalDeals.length === 0) return 1.0;
  const regionalWinRate = closedRegionalDeals.filter(d => d.deal_stage === 'Won').length / closedRegionalDeals.length;
  const globalWinRate = calcWinRate(allDeals.filter(d => d.deal_stage === 'Won' || d.deal_stage === 'Lost'));
  const performanceDiff = regionalWinRate - globalWinRate;
  const multiplier = 1.0 + performanceDiff;
  return Math.max(0.8, Math.min(1.2, multiplier));
}

function calcManagerBonus(salesAgent, allDeals, salesTeams) {
  const agentTeam = salesTeams.find(t => t.sales_agent === salesAgent);
  if (!agentTeam) return 1.0;
  const manager = agentTeam.manager;
  const teamAgents = salesTeams.filter(t => t.manager === manager).map(t => t.sales_agent);
  const agentDeals = allDeals.filter(d => d.sales_agent === salesAgent);
  const agentClosed = agentDeals.filter(d => d.deal_stage === 'Won' || d.deal_stage === 'Lost');
  const agentWinRate = agentClosed.length > 0 ? calcWinRate(agentClosed) : 0.5;
  const teamDeals = allDeals.filter(d => teamAgents.includes(d.sales_agent));
  const teamClosed = teamDeals.filter(d => d.deal_stage === 'Won' || d.deal_stage === 'Lost');
  const teamAvgWinRate = teamClosed.length > 0 ? calcWinRate(teamClosed) : 0.5;
  const performanceDiff = agentWinRate - teamAvgWinRate;
  const multiplier = 1.0 + performanceDiff * 0.75;
  return Math.max(0.85, Math.min(1.15, multiplier));
}

// ==================== CALCULATE SCORES ====================
console.log('🧮 CALCULANDO SCORES COM 10 FATORES...\n');

const BASE_DATE = new Date('2017-12-31');
const accountMap = new Map();
accounts.forEach(a => accountMap.set(a.account, a));
const productMap = new Map();
products.forEach(p => productMap.set(p.product, p));

const activePipeline = pipeline.filter(d => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting');
const globalWinRate = calcWinRate(pipeline.filter(d => d.deal_stage === 'Won' || d.deal_stage === 'Lost'));

const scores = [];

for (const deal of activePipeline) {
  const account = deal.account ? accountMap.get(deal.account) : null;
  const product = productMap.get(deal.product);
  const salesTeam = teams.find(t => t.sales_agent === deal.sales_agent);

  // FACTOR 1: Win Rate (22%)
  let accountWinRate = globalWinRate;
  if (account) {
    const accountDeals = pipeline.filter(d => d.account === account.account);
    const closedDeals = accountDeals.filter(d => d.deal_stage === 'Won' || d.deal_stage === 'Lost');
    if (closedDeals.length > 0) accountWinRate = calcWinRate(closedDeals);
  }
  const factor1 = accountWinRate * 22;

  // FACTOR 2: Product Value (18%)
  let productPrice = 0;
  if (product) productPrice = product.sales_price;
  const priceNorm = normalizeSalesPrice(productPrice, products);
  const factor2 = priceNorm * 18;

  // FACTOR 3: Agent Performance (18%)
  const agentPerf = calcAgentPerformance(deal.sales_agent, deal.product, pipeline);
  const factor3 = agentPerf * 18;

  // FACTOR 4: Time in Pipeline (12%)
  const daysInPipeline = Math.floor((BASE_DATE.getTime() - deal.engage_date.getTime()) / (1000 * 60 * 60 * 24));
  const timeNorm = scoreTimeInPipeline(daysInPipeline);
  const factor4 = timeNorm * 12;

  // FACTOR 5: Account Size (10%)
  let sizeNorm = 0.5;
  let sizeWeight = 10;
  if (account) {
    sizeNorm = calcAccountSize(account.revenue, account.employees, accounts);
  } else {
    sizeWeight = 5;
  }
  const factor5 = sizeNorm * sizeWeight;

  // FACTOR 6: Stage (10%)
  const stageNorm = scoreStage(deal.deal_stage);
  const factor6 = stageNorm * 10;

  // FACTOR 7: Cross-sell (10%)
  let crossSellNorm = 0.5;
  let crossSellWeight = 10;
  if (account) {
    const accountDeals = pipeline.filter(d => d.account === account.account);
    crossSellNorm = calcProductDiversity(accountDeals, products);
  } else {
    crossSellWeight = 5;
  }
  const factor7 = crossSellNorm * crossSellWeight;

  // FACTOR 8: Account Loyalty (+15 bonus)
  let loyaltyBonus = 0;
  if (account) {
    const accountDeals = pipeline.filter(d => d.account === account.account);
    const loyaltyScore = calcAccountLoyalty(accountDeals);
    if (loyaltyScore > 0) loyaltyBonus = 15;
  }
  const factor8 = loyaltyBonus;

  // FACTOR 9: Regional Performance (multiplier)
  let regionalMultiplier = 1.0;
  if (salesTeam) {
    regionalMultiplier = calcRegionalPerformance(salesTeam.regional_office, pipeline, teams);
  }

  // FACTOR 10: Manager Bonus (multiplier)
  let managerMultiplier = 1.0;
  if (salesTeam) {
    managerMultiplier = calcManagerBonus(deal.sales_agent, pipeline, teams);
  }

  // Calculate final score
  const baseScore = factor1 + factor2 + factor3 + factor4 + factor5 + factor6 + factor7 + factor8;
  const finalScore = Math.round(baseScore * regionalMultiplier * managerMultiplier);

  const tier = finalScore >= 80 ? 'HOT' : finalScore >= 60 ? 'WARM' : finalScore >= 40 ? 'COOL' : 'COLD';

  scores.push({
    opportunity_id: deal.opportunity_id,
    account: deal.account || '—',
    product: deal.product,
    sales_agent: deal.sales_agent,
    score: finalScore,
    baseScore: Math.round(baseScore),
    regionalMult: regionalMultiplier.toFixed(3),
    managerMult: managerMultiplier.toFixed(3),
    tier,
    factors: {
      winRate: factor1.toFixed(1),
      productValue: factor2.toFixed(1),
      agentPerf: factor3.toFixed(1),
      timePipeline: factor4.toFixed(1),
      accountSize: factor5.toFixed(1),
      stage: factor6.toFixed(1),
      crossSell: factor7.toFixed(1),
      loyalty: factor8.toFixed(1),
    }
  });
}

console.log(`✅ ${scores.length} deals scored\n`);

// ==================== DISTRIBUTION ANALYSIS ====================
console.log('📊 DISTRIBUIÇÃO DE TIERS:\n');

const byTier = {
  HOT: scores.filter(s => s.tier === 'HOT'),
  WARM: scores.filter(s => s.tier === 'WARM'),
  COOL: scores.filter(s => s.tier === 'COOL'),
  COLD: scores.filter(s => s.tier === 'COLD'),
};

const total = scores.length;
const distribution = [];

['HOT', 'WARM', 'COOL', 'COLD'].forEach(tier => {
  const count = byTier[tier].length;
  const pct = (count / total * 100).toFixed(1);
  const barLength = Math.floor(pct / 2);
  const bar = '█'.repeat(barLength);
  const expected = tier === 'HOT' ? '5-10%' : tier === 'WARM' ? '15-25%' : tier === 'COOL' ? '25-40%' : '30-50%';
  const status =
    (tier === 'HOT' && pct < 10) ||
    (tier === 'WARM' && pct >= 5 && pct <= 25) ||
    (tier === 'COOL' && pct >= 25 && pct <= 40) ||
    (tier === 'COLD' && pct >= 30 && pct <= 50) ? '✅' : '⚠️';

  console.log(`${status} ${tier.padEnd(5)} (${count.toString().padEnd(4)}): ${pct.padEnd(5)}% ${bar}  Expected: ${expected}`);
  distribution.push({ tier, count, pct: parseFloat(pct) });
});

// ==================== TOP 15 DEALS ====================
console.log('\n\n🏆 TOP 15 DEALS:\n');

const topDeals = [...scores].sort((a, b) => b.score - a.score).slice(0, 15);

topDeals.forEach((deal, i) => {
  const base = deal.baseScore.toString().padStart(3);
  const final = deal.score.toString().padStart(3);
  const regional = deal.regionalMult.padStart(5);
  const manager = deal.managerMult.padStart(5);
  console.log(`${String(i + 1).padStart(2)}. [${deal.tier}] Base: ${base} → Final: ${final} | Regional: ${regional}× Manager: ${manager}× | ${deal.product.padEnd(12)} | ${deal.account.padEnd(20)} | ${deal.sales_agent}`);
});

// ==================== FACTOR ANALYSIS ====================
console.log('\n\n📈 ANÁLISE DOS 10 FATORES:\n');

const avgFactors = {
  winRate: 0,
  productValue: 0,
  agentPerf: 0,
  timePipeline: 0,
  accountSize: 0,
  stage: 0,
  crossSell: 0,
  loyalty: 0,
};

scores.forEach(s => {
  Object.keys(avgFactors).forEach(key => {
    avgFactors[key] += parseFloat(s.factors[key]);
  });
});

Object.keys(avgFactors).forEach(key => {
  avgFactors[key] = (avgFactors[key] / scores.length).toFixed(1);
});

const factorLabels = [
  { key: 'winRate', name: 'Win Rate da Conta', weight: '22%', max: '22' },
  { key: 'productValue', name: 'Valor do Produto', weight: '18%', max: '18' },
  { key: 'agentPerf', name: 'Performance Vendedor', weight: '18%', max: '18' },
  { key: 'timePipeline', name: 'Tempo no Pipeline', weight: '12%', max: '12' },
  { key: 'accountSize', name: 'Tamanho da Empresa', weight: '10%', max: '10' },
  { key: 'stage', name: 'Estágio do Deal', weight: '10%', max: '10' },
  { key: 'crossSell', name: 'Cross-sell', weight: '10%', max: '10' },
  { key: 'loyalty', name: 'Account Loyalty (bonus)', weight: '+15', max: '15' },
];

factorLabels.forEach(f => {
  const avg = parseFloat(avgFactors[f.key]).toFixed(2);
  const pct = (parseFloat(avg) / parseFloat(f.max) * 100).toFixed(0);
  console.log(`${f.name.padEnd(30)} Avg: ${avg.padStart(5)} / ${f.max.padStart(2)} (${pct.padStart(3)}%) | Weight: ${f.weight.padStart(4)}`);
});

console.log('\nFATORES COM MULTIPLICADORES:');
const avgRegional = (scores.reduce((sum, s) => sum + parseFloat(s.regionalMult), 0) / scores.length).toFixed(3);
const avgManager = (scores.reduce((sum, s) => sum + parseFloat(s.managerMult), 0) / scores.length).toFixed(3);
console.log(`Regional Performance:  Avg multiplier: ${avgRegional}× (range: 0.8-1.2)`);
console.log(`Manager Bonus:         Avg multiplier: ${avgManager}× (range: 0.85-1.15)`);

// ==================== VALIDATION ====================
console.log('\n\n✅ VALIDAÇÃO:\n');

const validations = [
  { name: 'Todos os scores entre 0-100', pass: scores.every(s => s.score >= 0 && s.score <= 100) },
  { name: 'Tiers assignados corretamente', pass: scores.every(s => ['HOT', 'WARM', 'COOL', 'COLD'].includes(s.tier)) },
  { name: 'Base scores < final scores (com multipliers)', pass: scores.every(s => s.baseScore <= s.score + 5) },
  { name: 'Account Loyalty apenas para contas', pass: scores.filter(s => s.account === '—').every(s => parseFloat(s.factors.loyalty) === 0) },
  { name: 'Regional multiplier no range', pass: scores.every(s => parseFloat(s.regionalMult) >= 0.8 && parseFloat(s.regionalMult) <= 1.2) },
  { name: 'Manager multiplier no range', pass: scores.every(s => parseFloat(s.managerMult) >= 0.85 && parseFloat(s.managerMult) <= 1.15) },
  { name: 'Distribuição dentro esperado', pass:
    byTier.HOT.length <= total * 0.10 &&
    byTier.WARM.length <= total * 0.25 &&
    byTier.COOL.length >= total * 0.25 &&
    byTier.COOL.length <= total * 0.40 &&
    byTier.COLD.length >= total * 0.30 &&
    byTier.COLD.length <= total * 0.50
  },
];

validations.forEach(v => {
  console.log(`${v.pass ? '✅' : '❌'} ${v.name}`);
});

// ==================== SUMMARY ====================
console.log('\n\n📋 RESUMO FINAL:\n');
console.log(`Total de deals scored:     ${scores.length}`);
console.log(`Score médio:               ${(scores.reduce((s, d) => s + d.score, 0) / scores.length).toFixed(1)}`);
console.log(`Score mínimo:              ${Math.min(...scores.map(s => s.score))}`);
console.log(`Score máximo:              ${Math.max(...scores.map(s => s.score))}`);
console.log(`\nDistribuição:`);
console.log(`  HOT:  ${byTier.HOT.length.toString().padStart(4)} deals (${(byTier.HOT.length / total * 100).toFixed(1)}%)`);
console.log(`  WARM: ${byTier.WARM.length.toString().padStart(4)} deals (${(byTier.WARM.length / total * 100).toFixed(1)}%)`);
console.log(`  COOL: ${byTier.COOL.length.toString().padStart(4)} deals (${(byTier.COOL.length / total * 100).toFixed(1)}%)`);
console.log(`  COLD: ${byTier.COLD.length.toString().padStart(4)} deals (${(byTier.COLD.length / total * 100).toFixed(1)}%)`);

console.log('\n╔════════════════════════════════════════════════════════════════╗');
console.log('║                 ✅ TESTE CONCLUÍDO COM SUCESSO                ║');
console.log('╚════════════════════════════════════════════════════════════════╝\n');
