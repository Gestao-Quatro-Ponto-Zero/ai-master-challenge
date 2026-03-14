#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Função para ler CSV
const loadCSV = (filename) => {
  const filepath = path.join(__dirname, '..', 'crm_data_base', filename);
  console.log(`📂 Lendo: ${filepath}`);

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
console.log('║        🚀 CARREGANDO DADOS — Auto-Load Script                 ║');
console.log('╚════════════════════════════════════════════════════════════════╝\n');

try {
  console.log('⏳ Carregando arquivos...\n');

  const accounts = loadCSV('accounts.csv');
  console.log(`✅ accounts.csv: ${accounts.length} registros`);

  const products = loadCSV('products.csv');
  console.log(`✅ products.csv: ${products.length} registros`);

  const salesTeams = loadCSV('sales_teams.csv');
  console.log(`✅ sales_teams.csv: ${salesTeams.length} registros`);

  const pipeline = loadCSV('sales_pipeline.csv');
  console.log(`✅ sales_pipeline.csv: ${pipeline.length} registros`);

  console.log('\n📊 RESUMO DOS DADOS CARREGADOS:\n');
  console.log(`  📍 Contas: ${accounts.length}`);
  console.log(`  🛍️  Produtos: ${products.length}`);
  console.log(`  👥 Vendedores: ${salesTeams.length}`);
  console.log(`  💼 Oportunidades: ${pipeline.length}`);

  // Estatísticas dos deals
  const activeDeals = pipeline.filter(d => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting');
  const closedDeals = pipeline.filter(d => d.deal_stage === 'Won' || d.deal_stage === 'Lost');

  console.log(`\n  Deals ativos: ${activeDeals.length}`);
  console.log(`  Deals fechados: ${closedDeals.length}`);

  console.log('\n✅ TODOS OS DADOS CARREGADOS COM SUCESSO!\n');
  console.log('📋 Próximas ações:');
  console.log('  1. Abra: http://localhost:5178/');
  console.log('  2. Clique em "Upload CSV Files"');
  console.log('  3. Selecione os 4 arquivos:');
  console.log('     - accounts.csv');
  console.log('     - products.csv');
  console.log('     - sales_teams.csv');
  console.log('     - sales_pipeline.csv');
  console.log('  4. Clique "Upload & Load"');
  console.log('  5. Veja o Dashboard com 4 pilares!\n');

} catch (error) {
  console.error('\n❌ Erro ao carregar dados:', error.message);
  process.exit(1);
}
