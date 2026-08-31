import assert from 'node:assert/strict';
import test from 'node:test';
import { buildScoringModel } from './scoring.mjs';

const base = { manager: 'Manager', regional_office: 'Central', series: 'GTX', sales_price: 5000, sector: 'software' };
const rows = [
  { ...base, opportunity_id: 'W1', sales_agent: 'Ana', product: 'Pro', account: 'Acme', deal_stage: 'Won', engage_date: '2017-07-01', close_date: '2017-09-01', close_value: 5000 },
  { ...base, opportunity_id: 'L1', sales_agent: 'Ana', product: 'Pro', account: 'Acme', deal_stage: 'Lost', engage_date: '2017-08-01', close_date: '2017-10-01', close_value: 0 },
  { ...base, opportunity_id: 'O1', sales_agent: 'Ana', product: 'Pro', account: 'Acme', deal_stage: 'Engaging', engage_date: '2017-08-01' },
  { ...base, opportunity_id: 'O2', sales_agent: 'Ana', product: 'Pro', account: null, deal_stage: 'Prospecting', engage_date: null },
  { ...base, opportunity_id: 'P2', sales_agent: 'Ana', product: 'Basic', account: 'Acme', deal_stage: 'Won', engage_date: '2017-10-01', close_date: '2017-11-01', close_value: 500, sales_price: 500 },
];

test('focus score is the visible sum of three components', () => {
  const model = buildScoringModel(rows);
  model.open.forEach((deal) => {
    const sum = deal.score_explanation.reduce((total, part) => total + part.points, 0);
    assert.equal(deal.focus_score, sum);
    assert.equal(deal.score_explanation.length, 3);
    assert.ok(deal.focus_score >= 0 && deal.focus_score <= 100);
    assert.ok(deal.reasons.length <= 2);
  });
});

test('small regional sample falls back to general product history', () => {
  const deal = buildScoringModel(rows).byId.get('O1');
  const history = deal.score_explanation.find((part) => part.key === 'history');
  assert.equal(deal.chance_score, 50);
  assert.equal(history.points, 20);
  assert.equal(deal.history_scope, 'product_fallback');
  assert.match(history.detail, /histórico geral do produto/);
});

test('product history uses the opportunity region when the sample is sufficient', () => {
  const regionalRows = [];
  for (let index = 0; index < 30; index += 1) {
    regionalRows.push({ ...base, opportunity_id: `CENTRAL-${index}`, sales_agent: 'Ana', product: 'Regional', account: `Central ${index}`, regional_office: 'Central', deal_stage: 'Won', engage_date: '2017-09-01', close_date: '2017-10-01', close_value: 5000 });
    regionalRows.push({ ...base, opportunity_id: `EAST-${index}`, sales_agent: 'Bruno', product: 'Regional', account: `East ${index}`, regional_office: 'East', deal_stage: 'Lost', engage_date: '2017-09-01', close_date: '2017-10-01', close_value: 0 });
  }
  regionalRows.push({ ...base, opportunity_id: 'OPEN-CENTRAL', sales_agent: 'Ana', product: 'Regional', account: 'Central aberta', regional_office: 'Central', deal_stage: 'Prospecting' });
  regionalRows.push({ ...base, opportunity_id: 'OPEN-EAST', sales_agent: 'Bruno', product: 'Regional', account: 'East aberta', regional_office: 'East', deal_stage: 'Prospecting' });
  const model = buildScoringModel(regionalRows);
  const central = model.byId.get('OPEN-CENTRAL');
  const east = model.byId.get('OPEN-EAST');
  assert.equal(central.history_scope, 'region');
  assert.equal(east.history_scope, 'region');
  assert.equal(central.chance_score, 100);
  assert.equal(east.chance_score, 0);
  assert.match(central.score_explanation.find((part) => part.key === 'history').detail, /região Central/);
});

test('prospecting receives a next-step action without assuming qualification', () => {
  const deal = buildScoringModel(rows).byId.get('O2');
  assert.equal(deal.action_key, 'Definir próximo passo');
  assert.equal(deal.timing_score, 10);
  assert.match(deal.recommended_action, /confirmar o estágio atual/);
  assert.doesNotMatch(deal.score_explanation.find((part) => part.key === 'moment').detail, /não foi qualificad/i);
});

test('small product sample uses the global product clock', () => {
  const deal = buildScoringModel(rows).byId.get('O1');
  assert.equal(deal.product_clock.usedFallback, true);
  assert.equal(deal.product_clock.sourceSampleSize, 1);
  assert.equal(deal.action_key, 'Requalificar ou encerrar');
  assert.equal(deal.timing_score, 0);
});

test('product-specific clock changes the recommended action', () => {
  const clockRows = Array.from({ length: 30 }, (_, index) => ({
    ...base, opportunity_id: `FAST-${index}`, sales_agent: 'Ana', product: 'Fast', account: `Conta ${index}`,
    deal_stage: 'Won', engage_date: '2017-11-01', close_date: '2017-11-11', close_value: 5000,
  }));
  clockRows.push({ ...base, opportunity_id: 'FAST-OPEN', sales_agent: 'Ana', product: 'Fast', account: 'Acme', deal_stage: 'Engaging', engage_date: '2017-12-16' });
  const deal = buildScoringModel(clockRows).byId.get('FAST-OPEN');
  assert.equal(deal.product_clock.usedFallback, false);
  assert.equal(deal.product_clock.p90Days, 10);
  assert.equal(deal.action_key, 'Requalificar ou encerrar');
});

test('moment uses a product clock specific to the opportunity region', () => {
  const regionalClockRows = [];
  for (let index = 0; index < 30; index += 1) {
    regionalClockRows.push({ ...base, opportunity_id: `FAST-CENTRAL-${index}`, sales_agent: 'Ana', product: 'Clock', account: `Central ${index}`, regional_office: 'Central', deal_stage: 'Won', engage_date: '2017-11-01', close_date: '2017-11-11', close_value: 5000 });
    regionalClockRows.push({ ...base, opportunity_id: `SLOW-EAST-${index}`, sales_agent: 'Bruno', product: 'Clock', account: `East ${index}`, regional_office: 'East', deal_stage: 'Won', engage_date: '2017-10-01', close_date: '2017-11-10', close_value: 5000 });
  }
  regionalClockRows.push({ ...base, opportunity_id: 'OPEN-CLOCK-CENTRAL', sales_agent: 'Ana', product: 'Clock', account: 'Central aberta', regional_office: 'Central', deal_stage: 'Engaging', engage_date: '2017-12-16' });
  regionalClockRows.push({ ...base, opportunity_id: 'OPEN-CLOCK-EAST', sales_agent: 'Bruno', product: 'Clock', account: 'East aberta', regional_office: 'East', deal_stage: 'Engaging', engage_date: '2017-12-16' });
  const model = buildScoringModel(regionalClockRows);
  const central = model.byId.get('OPEN-CLOCK-CENTRAL');
  const east = model.byId.get('OPEN-CLOCK-EAST');
  assert.equal(central.product_clock.sourceScope, 'region');
  assert.equal(east.product_clock.sourceScope, 'region');
  assert.equal(central.product_clock.p90Days, 10);
  assert.equal(east.product_clock.p90Days, 40);
  assert.equal(central.action_key, 'Requalificar ou encerrar');
  assert.equal(east.action_key, 'Avançar agora');
  assert.match(east.score_explanation.find((part) => part.key === 'moment').detail, /região East/);
});

test('database Date values keep the historical age calculation', () => {
  const model = buildScoringModel(rows.map((row) => ({
    ...row,
    engage_date: row.engage_date ? new Date(`${row.engage_date}T00:00:00Z`) : null,
    close_date: row.close_date ? new Date(`${row.close_date}T00:00:00Z`) : null,
  })));
  assert.equal(model.byId.get('O1').age_days, 152);
});

test('recovery score is explained and gives more weight to a recent loss', () => {
  const recoveryRows = [
    ...rows,
    { ...base, opportunity_id: 'RECENT', sales_agent: 'Ana', product: 'Pro', account: 'Conta recente', deal_stage: 'Lost', close_date: '2017-12-25', close_value: 0 },
    { ...base, opportunity_id: 'OLDER', sales_agent: 'Ana', product: 'Pro', account: 'Conta antiga', deal_stage: 'Lost', close_date: '2017-11-01', close_value: 0 },
  ];
  const recovery = buildScoringModel(recoveryRows).recovery;
  const recent = recovery.find((deal) => deal.opportunity_id === 'RECENT');
  const older = recovery.find((deal) => deal.opportunity_id === 'OLDER');
  assert.ok(recent.recovery_score > older.recovery_score);
  assert.equal(recent.recovery_score, recent.recovery_explanation.reduce((sum, part) => sum + part.points, 0));
  assert.deepEqual(recent.recovery_explanation.map((part) => part.max), [40, 40, 20]);
});

test('recovery suggests another seller only with sufficient context history', () => {
  const contextualRows = [];
  const addHistory = (seller, manager, region, count, wins) => {
    for (let index = 0; index < count; index += 1) contextualRows.push({
      ...base,
      manager,
      regional_office: region,
      opportunity_id: `${seller}-${index}`,
      sales_agent: seller,
      product: 'Pro',
      account: `${seller} Conta ${index}`,
      deal_stage: index < wins ? 'Won' : 'Lost',
      close_date: '2017-10-01',
      close_value: index < wins ? 5000 : 0,
    });
  };
  addHistory('Ana', 'Manager Central', 'Central', 15, 6);
  addHistory('Dan', 'Manager Central', 'Central', 15, 7);
  addHistory('Bruno', 'Outro Manager', 'Central', 15, 13);
  addHistory('Carla', 'Outro Manager', 'Central', 15, 10);
  addHistory('Vendedor East', 'Manager East', 'East', 15, 15);
  addHistory('Apoio East', 'Manager East', 'East', 15, 14);
  contextualRows.push({ ...base, manager: 'Manager Central', regional_office: 'Central', opportunity_id: 'TARGET', sales_agent: 'Ana', product: 'Pro', account: 'Conta alvo', deal_stage: 'Lost', close_date: '2017-12-20', close_value: 0 });

  const target = buildScoringModel(contextualRows).recovery.find((deal) => deal.opportunity_id === 'TARGET');
  assert.equal(target.redistribution.recommended, true);
  assert.equal(target.redistribution.seller, 'Bruno');
  assert.equal(target.redistribution.region, 'Central');
  assert.equal(target.redistribution.region, target.regional_office);
  assert.ok(target.redistribution.seller_sample >= 15);
  assert.ok(target.redistribution.region_sample >= 30);
});
