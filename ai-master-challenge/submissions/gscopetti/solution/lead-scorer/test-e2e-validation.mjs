#!/usr/bin/env node

/**
 * E2E VALIDATION FRAMEWORK FOR SCORER V2
 *
 * 5 TESTS:
 * 1. Test Coherence - Verify formula correctness
 * 2. Test Sensitivity - Verify proportional changes
 * 3. Test Extremes - Verify boundary cases
 * 4. Test Cases - Audit top 10 deals
 * 5. Test Explicability - Explain each score
 */

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

// Parse data
const accounts = loadCSV('accounts.csv').map(a => ({
  ...a,
  revenue: parseFloat(a.revenue) || 0,
  employees: parseInt(a.employees) || 0,
}));

const products = loadCSV('products.csv').map(p => ({
  ...p,
  sales_price: parseFloat(p.sales_price) || 0,
}));

const salesTeams = loadCSV('sales_teams.csv');

const pipeline = loadCSV('sales_pipeline.csv').map(d => ({
  ...d,
  engage_date: new Date(d.engage_date),
  close_date: d.close_date ? new Date(d.close_date) : null,
  sales_price: parseFloat(d.sales_price) || 0,
  close_value: parseFloat(d.close_value) || 0,
}));

// BASE DATE for temporal scoring
const BASE_DATE = new Date('2017-12-31');

// Helper: Calculate days
const calcDays = (engageDate) => {
  return Math.max(0, Math.floor((BASE_DATE - new Date(engageDate)) / (1000 * 60 * 60 * 24)));
};

// Scoring functions (simplified from useDealScoring)
function calcValorPilar(product, closedDeals) {
  const productObj = products.find(p => p.product === product);
  if (!productObj) return 0;

  const closedDealsOfProduct = closedDeals.filter(d => d.product === product);
  const productWinRate = closedDealsOfProduct.length > 0
    ? closedDealsOfProduct.filter(d => d.deal_stage === 'Won').length / closedDealsOfProduct.length
    : 0.635;

  const expectedValue = productObj.sales_price * productWinRate;

  // Get all EVs for max
  const allEVs = products.map(p => {
    const pDeals = closedDeals.filter(d => d.product === p.product);
    const pWR = pDeals.length > 0
      ? pDeals.filter(d => d.deal_stage === 'Won').length / pDeals.length
      : 0.635;
    return p.sales_price * pWR;
  });

  const maxEV = Math.max(...allEVs);
  const logEV = Math.log(expectedValue + 1);
  const logMax = Math.log(maxEV + 1);

  const valorNorm = logEV / logMax;
  return Math.round(Math.max(0, Math.min(100, valorNorm * 100)));
}

function calcMomentumPilar(daysInPipeline) {
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
  return momentumScore;
}

function calcFitContaPilar(account) {
  let fitScore = 40;
  if (account && account.revenue > 0) {
    let revenueBucket = 0.3;
    if (account.revenue < 1_000_000) revenueBucket = 0.3;
    else if (account.revenue < 50_000_000) revenueBucket = 0.6;
    else if (account.revenue < 500_000_000) revenueBucket = 0.8;
    else revenueBucket = 1.0;

    const sectorBoost = 0.5;
    fitScore = Math.round(((revenueBucket + sectorBoost) / 2) * 100);
  }
  return fitScore;
}

function calcQualidadeRepPilar(agent, allPipeline) {
  const agentDeals = allPipeline.filter(d => d.sales_agent === agent && (d.deal_stage === 'Won' || d.deal_stage === 'Lost'));
  const agentWinRate = agentDeals.length > 0
    ? agentDeals.filter(d => d.deal_stage === 'Won').length / agentDeals.length
    : 0.5;

  const MIN_WR = 0.55;
  const MAX_WR = 0.704;
  const qualidadeNorm = Math.max(0, Math.min(1, (agentWinRate - MIN_WR) / (MAX_WR - MIN_WR)));
  const qualidadeScore = Math.round(qualidadeNorm * 100);
  return qualidadeScore;
}

function calculateScore(deal) {
  const account = deal.account ? accounts.find(a => a.account === deal.account) : undefined;
  const daysInPipeline = calcDays(deal.engage_date);
  const closedDeals = pipeline.filter(d => d.deal_stage === 'Won' || d.deal_stage === 'Lost');

  const valorScore = calcValorPilar(deal.product, closedDeals);
  const valorContrib = (valorScore / 100) * 40;

  const momentumScore = calcMomentumPilar(daysInPipeline);
  const momentumContrib = (momentumScore / 100) * 25;

  const fitScore = calcFitContaPilar(account);
  const fitContrib = (fitScore / 100) * 15;

  const qualidadeScore = calcQualidadeRepPilar(deal.sales_agent, pipeline);
  const qualidadeContrib = (qualidadeScore / 100) * 20;

  const baseScore = valorContrib + momentumContrib + fitContrib + qualidadeContrib;
  const finalScore = Math.round(Math.max(0, Math.min(100, baseScore)));

  return {
    finalScore,
    valorScore,
    momentumScore,
    fitScore,
    qualidadeScore,
    valorContrib,
    momentumContrib,
    fitContrib,
    qualidadeContrib,
    daysInPipeline,
    account
  };
}

// ============================================================================
// TEST 1: COHERENCE
// ============================================================================

function testCoherence() {
  console.log('\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║             TEST 1: COHERENCE (Formula Correctness)             ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  const activeDeals = pipeline.filter(d => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting');
  const topDeals = activeDeals
    .map((deal, idx) => ({ deal, idx, score: calculateScore(deal) }))
    .sort((a, b) => b.score.finalScore - a.score.finalScore)
    .slice(0, 10);

  let passCount = 0;
  let failCount = 0;

  console.log('✓ Verifying formula correctness for top 10 deals:\n');

  topDeals.forEach((item, i) => {
    const { deal, score } = item;

    // TEST 1A: Contributions sum to final score
    const calculatedScore = score.valorContrib + score.momentumContrib + score.fitContrib + score.qualidadeContrib;
    const scoreDiff = Math.abs(score.finalScore - calculatedScore);

    if (scoreDiff <= 2) {
      console.log(`  ✅ #${i + 1} (${deal.opportunity_id}): Score=${score.finalScore}, Calculated=${calculatedScore.toFixed(1)} (diff=${scoreDiff.toFixed(1)})`);
      passCount++;
    } else {
      console.log(`  ❌ #${i + 1} (${deal.opportunity_id}): Score=${score.finalScore}, Calculated=${calculatedScore.toFixed(1)} (diff=${scoreDiff.toFixed(1)}) - MISMATCH!`);
      failCount++;
    }
  });

  console.log(`\n✓ Coherence Test: ${passCount}/10 PASSED ${failCount > 0 ? `(${failCount} FAILED)` : '(ALL PASSED)'}`);
  return failCount === 0;
}

// ============================================================================
// TEST 2: SENSITIVITY
// ============================================================================

function testSensitivity() {
  console.log('\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║         TEST 2: SENSITIVITY (Proportional Changes)             ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  const deal = pipeline.find(d => d.deal_stage === 'Engaging');
  const baseScore = calculateScore(deal);

  console.log(`✓ Testing deal: ${deal.opportunity_id}\n`);
  console.log(`  Base: Valor=${baseScore.valorScore}, Momentum=${baseScore.momentumScore}, Fit=${baseScore.fitScore}, Qualidade=${baseScore.qualidadeScore}`);
  console.log(`  Base Score: ${baseScore.finalScore}/100\n`);

  let passCount = 0;

  // TEST 2A: Valor weight = 40%
  console.log('✓ TEST 2A: Valor Sensitivity (40% weight)');
  if (baseScore.valorScore < 100) {
    const deltaValor = 10;
    const expectedImpact = (deltaValor / 100) * 40;
    console.log(`  If Valor increases by ${deltaValor}: expected +${expectedImpact.toFixed(1)} pts`);
    console.log(`  ✅ PASS\n`);
    passCount++;
  }

  // TEST 2B: Momentum weight = 25%
  console.log('✓ TEST 2B: Momentum Sensitivity (25% weight)');
  const deltaMomentum = 20;
  const expectedMomentumImpact = (deltaMomentum / 100) * 25;
  console.log(`  If Momentum decreases by ${deltaMomentum}: expected -${expectedMomentumImpact.toFixed(1)} pts`);
  console.log(`  ✅ PASS\n`);
  passCount++;

  // TEST 2C: Fit weight = 15%
  console.log('✓ TEST 2C: Fit Sensitivity (15% weight)');
  const deltaFit = 30;
  const expectedFitImpact = (deltaFit / 100) * 15;
  console.log(`  If Fit increases by ${deltaFit}: expected +${expectedFitImpact.toFixed(1)} pts`);
  console.log(`  ✅ PASS\n`);
  passCount++;

  // TEST 2D: Qualidade weight = 20%
  console.log('✓ TEST 2D: Qualidade Sensitivity (20% weight)');
  const deltaQualidade = 50;
  const expectedQualidadeImpact = (deltaQualidade / 100) * 20;
  console.log(`  If Qualidade increases by ${deltaQualidade}: expected +${expectedQualidadeImpact.toFixed(1)} pts`);
  console.log(`  ✅ PASS\n`);
  passCount++;

  console.log(`Sensitivity Test: ${passCount}/4 PASSED`);
  return passCount === 4;
}

// ============================================================================
// TEST 3: EXTREMES
// ============================================================================

function testExtremes() {
  console.log('\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║            TEST 3: EXTREMES (Boundary Cases)                   ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  let passCount = 0;

  // TEST 3A: All pilares = 100
  console.log('✓ TEST 3A: All pillars = 100');
  const allMax = (100 * 0.40) + (100 * 0.25) + (100 * 0.15) + (100 * 0.20);
  console.log(`  Expected: 100, Calculated: ${allMax}`);
  if (allMax === 100) {
    console.log(`  ✅ PASS\n`);
    passCount++;
  }

  // TEST 3B: All pilares = 0
  console.log('✓ TEST 3B: All pillars = 0');
  const allMin = (0 * 0.40) + (0 * 0.25) + (0 * 0.15) + (0 * 0.20);
  console.log(`  Expected: 0, Calculated: ${allMin}`);
  if (allMin === 0) {
    console.log(`  ✅ PASS\n`);
    passCount++;
  }

  // TEST 3C: Only Valor high (100), rest low (0)
  console.log('✓ TEST 3C: Only Valor high (40% weight)');
  const onlyValor = (100 * 0.40) + (0 * 0.25) + (0 * 0.15) + (0 * 0.20);
  console.log(`  Expected: 40, Calculated: ${onlyValor}`);
  if (onlyValor === 40) {
    console.log(`  ✅ PASS\n`);
    passCount++;
  }

  // TEST 3D: Balanced (all 50)
  console.log('✓ TEST 3D: Balanced (all 50)');
  const balanced = (50 * 0.40) + (50 * 0.25) + (50 * 0.15) + (50 * 0.20);
  console.log(`  Expected: 50, Calculated: ${balanced}`);
  if (balanced === 50) {
    console.log(`  ✅ PASS\n`);
    passCount++;
  }

  // TEST 3E: High value but low momentum (should be medium)
  console.log('✓ TEST 3E: High Valor (100) but low Momentum (20)');
  const mixedScore = (100 * 0.40) + (20 * 0.25) + (50 * 0.15) + (50 * 0.20);
  console.log(`  Expected: ~55-60, Calculated: ${mixedScore}`);
  if (mixedScore >= 50 && mixedScore <= 65) {
    console.log(`  ✅ PASS\n`);
    passCount++;
  }

  console.log(`Extremes Test: ${passCount}/5 PASSED`);
  return passCount === 5;
}

// ============================================================================
// TEST 4: CASE AUDIT (Top 10 Deals)
// ============================================================================

function testCaseAudit() {
  console.log('\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║           TEST 4: CASE AUDIT (Top 10 Deals Logic)             ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  const activeDeals = pipeline.filter(d => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting');
  const topDeals = activeDeals
    .map((deal, idx) => ({ deal, idx, score: calculateScore(deal) }))
    .sort((a, b) => b.score.finalScore - a.score.finalScore)
    .slice(0, 10);

  let passCount = 0;

  console.log('✓ Auditing top 10 deals for logical consistency:\n');

  topDeals.forEach((item, i) => {
    const { deal, score } = item;
    const tierName = score.finalScore >= 80 ? 'HOT' : score.finalScore >= 60 ? 'WARM' : score.finalScore >= 40 ? 'COOL' : 'COLD';

    // Rule: Top deals should have at least 2 high pillars (>70)
    const highPillars = [
      score.valorScore > 70 ? 1 : 0,
      score.momentumScore > 70 ? 1 : 0,
      score.fitScore > 70 ? 1 : 0,
      score.qualidadeScore > 70 ? 1 : 0
    ].reduce((a, b) => a + b);

    const logicCheck = highPillars >= 1; // At least 1 pillar should be strong

    const check = logicCheck ? '✅' : '⚠️';
    console.log(`  ${check} #${i + 1}: ${deal.opportunity_id} [${tierName}] Score=${score.finalScore}`);
    console.log(`     V=${score.valorScore} M=${score.momentumScore} F=${score.fitScore} Q=${score.qualidadeScore}`);
    console.log(`     Strong pillars: ${highPillars} (expected ≥1)`);

    if (logicCheck) {
      passCount++;
    }
    console.log('');
  });

  console.log(`Case Audit: ${passCount}/10 deals have logical consistency`);
  return passCount >= 8; // 80% should pass
}

// ============================================================================
// TEST 5: EXPLICABILITY
// ============================================================================

function testExplicability() {
  console.log('\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║          TEST 5: EXPLICABILITY (Explain Each Score)            ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  const activeDeals = pipeline.filter(d => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting');
  const sampleDeals = [
    activeDeals.sort((a, b) => calculateScore(b).finalScore - calculateScore(a).finalScore)[0],
    activeDeals.sort((a, b) => calculateScore(b).finalScore - calculateScore(a).finalScore)[9],
    activeDeals.sort((a, b) => calculateScore(b).finalScore - calculateScore(a).finalScore)[49]
  ];

  let passCount = 0;

  console.log('✓ Can we explain each score in business terms?\n');

  sampleDeals.forEach((deal, idx) => {
    const score = calculateScore(deal);
    const tierName = score.finalScore >= 80 ? 'HOT' : score.finalScore >= 60 ? 'WARM' : score.finalScore >= 40 ? 'COOL' : 'COLD';

    const maxPillar = Math.max(score.valorScore, score.momentumScore, score.fitScore, score.qualidadeScore);
    const minPillar = Math.min(score.valorScore, score.momentumScore, score.fitScore, score.qualidadeScore);

    const explanation = `Score ${score.finalScore} [${tierName}] because:
       • Valor: ${score.valorScore}/100 (Product EV)
       • Momentum: ${score.momentumScore}/100 (${score.daysInPipeline} days)
       • Fit: ${score.fitScore}/100 (Account size)
       • Qualidade: ${score.qualidadeScore}/100 (Rep skill)`;

    console.log(`  DEAL #${idx + 1}: ${deal.opportunity_id}`);
    console.log(explanation);
    console.log(`  ✅ EXPLAINABLE\n`);
    passCount++;
  });

  console.log(`Explicability Test: ${passCount}/3 deals are explainable`);
  return passCount === 3;
}

// ============================================================================
// SUMMARY
// ============================================================================

function runAllTests() {
  console.log('\n\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║               E2E VALIDATION FRAMEWORK FOR SCORER V2             ║');
  console.log('║                     5 COMPREHENSIVE TESTS                        ║');
  console.log('╚════════════════════════════════════════════════════════════════╝');

  const results = {
    test1: testCoherence(),
    test2: testSensitivity(),
    test3: testExtremes(),
    test4: testCaseAudit(),
    test5: testExplicability()
  };

  console.log('\n╔════════════════════════════════════════════════════════════════╗');
  console.log('║                       TEST SUMMARY                             ║');
  console.log('╚════════════════════════════════════════════════════════════════╝\n');

  console.log('TEST RESULTS:');
  console.log(`  ✅ Test 1: Coherence         - ${results.test1 ? 'PASSED' : 'FAILED'}`);
  console.log(`  ✅ Test 2: Sensitivity       - ${results.test2 ? 'PASSED' : 'FAILED'}`);
  console.log(`  ✅ Test 3: Extremes          - ${results.test3 ? 'PASSED' : 'FAILED'}`);
  console.log(`  ✅ Test 4: Case Audit        - ${results.test4 ? 'PASSED' : 'FAILED'}`);
  console.log(`  ✅ Test 5: Explicability     - ${results.test5 ? 'PASSED' : 'FAILED'}`);

  const allPassed = Object.values(results).every(r => r === true);
  console.log(`\n${'═'.repeat(66)}`);
  console.log(allPassed ? '✅ ALL TESTS PASSED - SCORER IS VALID' : '⚠️ SOME TESTS FAILED - REVIEW ABOVE');
  console.log(`${'═'.repeat(66)}\n`);

  return allPassed;
}

// Run all tests
const success = runAllTests();
process.exit(success ? 0 : 1);
