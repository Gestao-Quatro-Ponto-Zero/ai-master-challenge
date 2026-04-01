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
console.log('║          🧪 TESTE: ENRIQUECIMENTO DE DADOS DOS DEALS          ║');
console.log('╚════════════════════════════════════════════════════════════════╝\n');

// Load data
const accounts = loadCSV('accounts.csv');
const products = loadCSV('products.csv');
const pipeline = loadCSV('sales_pipeline.csv');
const salesTeams = loadCSV('sales_teams.csv');

const BASE_DATE = new Date('2017-12-31');

// Create maps for lookup
const salesTeamMap = new Map();
for (const team of salesTeams) {
  salesTeamMap.set(team.sales_agent, team);
}

const productMap = new Map();
for (const product of products) {
  productMap.set(product.product, product);
}

// Filter active deals
const activeDeals = pipeline.filter(d =>
  d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
);

console.log(`📊 DADOS CARREGADOS:\n`);
console.log(`  ✅ ${activeDeals.length} deals ativos`);
console.log(`  ✅ ${salesTeams.length} vendedores`);
console.log(`  ✅ ${products.length} produtos\n`);

// Enrich first 10 deals with region, manager, series
console.log('📝 ENRIQUECIMENTO DE DADOS (primeiros 10 deals):\n');

const enrichedDeals = activeDeals.slice(0, 10).map((deal, idx) => {
  const salesTeamMember = salesTeamMap.get(deal.sales_agent);
  const productObj = productMap.get(deal.product);

  return {
    idx,
    opportunity_id: deal.opportunity_id,
    sales_agent: deal.sales_agent,
    product: deal.product,

    // Enriquecidos:
    region: salesTeamMember?.regional_office || '(missing)',
    manager: salesTeamMember?.manager || '(missing)',
    series: productObj?.series || '(missing)',
  };
});

enrichedDeals.forEach(deal => {
  console.log(`#${deal.idx + 1} | Agent: ${deal.sales_agent.padEnd(20)} | Region: ${deal.region?.padEnd(12)} | Manager: ${deal.manager?.padEnd(15)} | Series: ${deal.series}`);
});

// Validate data completeness
console.log('\n\n✅ VALIDAÇÃO DE COMPLETUDE:\n');

const dealsWithoutRegion = enrichedDeals.filter(d => d.region === '(missing)');
const dealsWithoutManager = enrichedDeals.filter(d => d.manager === '(missing)');
const dealsWithoutSeries = enrichedDeals.filter(d => d.series === '(missing)');

console.log(`  ✅ Deals com region: ${enrichedDeals.length - dealsWithoutRegion.length}/${enrichedDeals.length}`);
console.log(`  ✅ Deals com manager: ${enrichedDeals.length - dealsWithoutManager.length}/${enrichedDeals.length}`);
console.log(`  ✅ Deals com series: ${enrichedDeals.length - dealsWithoutSeries.length}/${enrichedDeals.length}`);

// Count unique values
const uniqueRegions = new Set(enrichedDeals.map(d => d.region));
const uniqueManagers = new Set(enrichedDeals.map(d => d.manager));
const uniqueSeries = new Set(enrichedDeals.map(d => d.series));

console.log(`\n📊 DISTRIBUIÇÃO DE VALORES:\n`);
console.log(`  🌍 Regiões únicas: ${uniqueRegions.size}`);
Array.from(uniqueRegions).sort().forEach(region => {
  const count = enrichedDeals.filter(d => d.region === region).length;
  console.log(`     - ${region}: ${count} deals`);
});

console.log(`\n  👔 Gerentes únicos: ${uniqueManagers.size}`);
Array.from(uniqueManagers).sort().forEach(manager => {
  const count = enrichedDeals.filter(d => d.manager === manager).length;
  console.log(`     - ${manager}: ${count} deals`);
});

console.log(`\n  📦 Séries únicas: ${uniqueSeries.size}`);
Array.from(uniqueSeries).sort().forEach(series => {
  const count = enrichedDeals.filter(d => d.series === series).length;
  console.log(`     - ${series}: ${count} deals`);
});

// Test filtering logic
console.log('\n\n🔍 TESTE DE FILTRAGEM:\n');

// Test 1: Filter by Region
const firstRegion = Array.from(uniqueRegions)[0];
const dealsInRegion = enrichedDeals.filter(d => d.region === firstRegion);
console.log(`  ✅ Filter Region="${firstRegion}": ${dealsInRegion.length} deals`);

// Test 2: Filter by Manager
const firstManager = Array.from(uniqueManagers)[0];
const dealsWithManager = enrichedDeals.filter(d => d.manager === firstManager);
console.log(`  ✅ Filter Manager="${firstManager}": ${dealsWithManager.length} deals`);

// Test 3: Filter by Series
const firstSeries = Array.from(uniqueSeries)[0];
const dealsWithSeries = enrichedDeals.filter(d => d.series === firstSeries);
console.log(`  ✅ Filter Series="${firstSeries}": ${dealsWithSeries.length} deals`);

// Test 4: Combined filters
const combinedFilter = enrichedDeals.filter(d =>
  d.region === firstRegion && d.series === firstSeries
);
console.log(`  ✅ Filter Region="${firstRegion}" AND Series="${firstSeries}": ${combinedFilter.length} deals`);

console.log(`\n\n╔════════════════════════════════════════════════════════════════╗`);
console.log(`║          ✅ VALIDAÇÃO COMPLETA — FILTROS PRONTOS            ║`);
console.log(`╚════════════════════════════════════════════════════════════════╝\n`);

console.log('📋 PRÓXIMAS AÇÕES:\n');
console.log('  1. Abra: http://localhost:5179/');
console.log('  2. Upload dos 4 CSVs');
console.log('  3. Clique em "Ajustar Filtros"');
console.log('  4. Teste cada filtro:');
console.log(`     - Region: Selecione "${firstRegion}"`);
console.log(`     - Manager: Selecione "${firstManager}"`);
console.log(`     - Series: Selecione "${firstSeries}"`);
console.log('  5. Verifique se a lista de deals é filtrada corretamente\n');
