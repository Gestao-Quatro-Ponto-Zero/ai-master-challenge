/**
 * Lead Scorer — Motor de Priorização de Pipeline
 * Pontua deals ativos do CRM usando 7 fatores ponderados calibrados com dados históricos.
 */

// ============================================================
// CONSTANTES
// ============================================================
const DATA_DIR = 'data/';
const BUCKET_THRESHOLDS = [
  { min: 85, label: 'Foco Imediato',          css: 'focus'   },
  { min: 70, label: 'Alta Prioridade',         css: 'high'    },
  { min: 50, label: 'Trabalhar Esta Semana',   css: 'week'    },
  { min: 30, label: 'Monitorar',               css: 'monitor' },
  { min: 0,  label: 'Baixa Prioridade',        css: 'low'     },
];

const FACTOR_WEIGHTS = {
  accountFit:        0.20,
  productPerformance:0.15,
  dealStage:         0.20,
  stageAging:        0.20,
  agentWinRate:      0.10,
  accountHistory:    0.05,
  expectedValue:     0.10,
};

// Data de referência — último close_date do dataset serve como "hoje"
let REFERENCE_DATE = new Date('2017-03-31');

// ============================================================
// ESTADO GLOBAL
// ============================================================
let rawData = { accounts: [], products: [], teams: [], pipeline: [] };
let historicalStats = {};
let scoredDeals = [];
let filteredDeals = [];
let currentSort = { key: 'score', asc: false };

// ============================================================
// INICIALIZAÇÃO
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  loadAllData();
});

async function loadAllData() {
  try {
    const [accounts, products, teams, pipeline] = await Promise.all([
      loadCSV('accounts.csv'),
      loadCSV('products.csv'),
      loadCSV('sales_teams.csv'),
      loadCSV('sales_pipeline.csv'),
    ]);

    rawData = { accounts, products, teams, pipeline };

    // Determinar data de referência a partir do último close_date de deals Won
    const closeDates = pipeline
      .filter(r => r.close_date && r.deal_stage === 'Won')
      .map(r => new Date(r.close_date))
      .filter(d => !isNaN(d));
    if (closeDates.length) {
      REFERENCE_DATE = new Date(Math.max(...closeDates));
    }

    historicalStats = computeHistoricalStats();
    scoredDeals = scoreActiveDeals();
    filteredDeals = [...scoredDeals];

    populateFilters();
    bindEvents();
    render();

    document.getElementById('loadingOverlay').classList.add('hidden');
  } catch (err) {
    console.error('Erro ao carregar dados:', err);
    document.querySelector('.loading-text').textContent =
      'Erro ao carregar dados. Certifique-se de estar rodando via servidor local (python -m http.server 8000).';
  }
}

function loadCSV(filename) {
  return new Promise((resolve, reject) => {
    Papa.parse(DATA_DIR + filename, {
      download: true,
      header: true,
      skipEmptyLines: true,
      dynamicTyping: true,
      complete: (results) => resolve(results.data),
      error: (err) => reject(err),
    });
  });
}

// ============================================================
// ESTATÍSTICAS HISTÓRICAS (calculadas uma vez a partir de deals Won/Lost)
// ============================================================
function computeHistoricalStats() {
  const { pipeline, accounts, products, teams } = rawData;

  // Mapas de lookup
  const accountMap = {};
  accounts.forEach(a => { accountMap[a.account] = a; });

  const productMap = {};
  products.forEach(p => { productMap[p.product] = p; });

  const teamMap = {};
  teams.forEach(t => { teamMap[t.sales_agent] = t; });

  // Deals fechados (Won ou Lost)
  const closedDeals = pipeline.filter(d => d.deal_stage === 'Won' || d.deal_stage === 'Lost');

  // ---- Taxa de ganho por vendedor ----
  const agentStats = {};
  closedDeals.forEach(d => {
    if (!agentStats[d.sales_agent]) agentStats[d.sales_agent] = { won: 0, total: 0 };
    agentStats[d.sales_agent].total++;
    if (d.deal_stage === 'Won') agentStats[d.sales_agent].won++;
  });

  const agentWinRates = {};
  const allWon = closedDeals.filter(d => d.deal_stage === 'Won').length;
  const avgWinRate = allWon / Math.max(closedDeals.length, 1);
  Object.keys(agentStats).forEach(agent => {
    agentWinRates[agent] = agentStats[agent].won / Math.max(agentStats[agent].total, 1);
  });

  // ---- Performance por produto (taxa de ganho + ticket médio) ----
  const productStats = {};
  closedDeals.forEach(d => {
    const pName = normalizeProduct(d.product);
    if (!productStats[pName]) productStats[pName] = { won: 0, total: 0, totalValue: 0, wonCount: 0 };
    productStats[pName].total++;
    if (d.deal_stage === 'Won') {
      productStats[pName].won++;
      productStats[pName].totalValue += (d.close_value || 0);
      productStats[pName].wonCount++;
    }
  });

  const productPerf = {};
  Object.keys(productStats).forEach(p => {
    const s = productStats[p];
    productPerf[p] = {
      winRate: s.won / Math.max(s.total, 1),
      avgCloseValue: s.wonCount > 0 ? s.totalValue / s.wonCount : 0,
      totalDeals: s.total,
    };
  });

  // ---- Taxa de ganho por setor ----
  const sectorStats = {};
  closedDeals.forEach(d => {
    const acc = accountMap[d.account];
    const sector = acc ? acc.sector : 'desconhecido';
    if (!sectorStats[sector]) sectorStats[sector] = { won: 0, total: 0 };
    sectorStats[sector].total++;
    if (d.deal_stage === 'Won') sectorStats[sector].won++;
  });

  const sectorWinRates = {};
  Object.keys(sectorStats).forEach(s => {
    sectorWinRates[s] = sectorStats[s].won / Math.max(sectorStats[s].total, 1);
  });

  // ---- Taxa de ganho por faixa de receita ----
  const revBands = [
    { label: 'micro',       max: 100 },
    { label: 'pequena',     max: 500 },
    { label: 'média',       max: 2000 },
    { label: 'grande',      max: 5000 },
    { label: 'enterprise',  max: Infinity },
  ];

  function getRevBand(revenue) {
    for (const b of revBands) {
      if (revenue <= b.max) return b.label;
    }
    return 'enterprise';
  }

  const revBandStats = {};
  closedDeals.forEach(d => {
    const acc = accountMap[d.account];
    const rev = acc ? acc.revenue : 0;
    const band = getRevBand(rev);
    if (!revBandStats[band]) revBandStats[band] = { won: 0, total: 0 };
    revBandStats[band].total++;
    if (d.deal_stage === 'Won') revBandStats[band].won++;
  });

  const revBandWinRates = {};
  Object.keys(revBandStats).forEach(b => {
    revBandWinRates[b] = revBandStats[b].won / Math.max(revBandStats[b].total, 1);
  });

  // ---- Taxa de ganho por faixa de funcionários ----
  const empBands = [
    { label: 'micro',    max: 100 },
    { label: 'pequena',  max: 500 },
    { label: 'média',    max: 2000 },
    { label: 'grande',   max: 5000 },
    { label: 'muito grande', max: Infinity },
  ];

  function getEmpBand(employees) {
    for (const b of empBands) {
      if (employees <= b.max) return b.label;
    }
    return 'muito grande';
  }

  const empBandStats = {};
  closedDeals.forEach(d => {
    const acc = accountMap[d.account];
    const emp = acc ? acc.employees : 0;
    const band = getEmpBand(emp);
    if (!empBandStats[band]) empBandStats[band] = { won: 0, total: 0 };
    empBandStats[band].total++;
    if (d.deal_stage === 'Won') empBandStats[band].won++;
  });

  const empBandWinRates = {};
  Object.keys(empBandStats).forEach(b => {
    empBandWinRates[b] = empBandStats[b].won / Math.max(empBandStats[b].total, 1);
  });

  // ---- Histórico por conta (deals Won anteriores) ----
  const accountWonCount = {};
  closedDeals.filter(d => d.deal_stage === 'Won').forEach(d => {
    accountWonCount[d.account] = (accountWonCount[d.account] || 0) + 1;
  });

  // ---- Mediana de idade por estágio (deals Won) ----
  // Ciclo total de deals Won (engage_date → close_date)
  const wonDealAges = [];
  closedDeals.filter(d => d.deal_stage === 'Won' && d.engage_date && d.close_date).forEach(d => {
    const age = Math.round((new Date(d.close_date) - new Date(d.engage_date)) / 86400000);
    if (age > 0) wonDealAges.push(age);
  });

  function median(arr) {
    if (!arr.length) return 120;
    const sorted = [...arr].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  }

  const medianTotal = median(wonDealAges);
  // Prospecting: ciclo completo esperado (deals simples fecham rápido ou morrem)
  // Engaging: deals engajados passaram do filtro inicial e tendem a ter ciclos mais longos
  // Fator de estágio (Engaging > Prospecting) já está no Fator 3 — aqui só aging puro
  const medianAges = {
    Prospecting: medianTotal,
    Engaging:    medianTotal * 1.5,
  };

  // ---- Estatísticas gerais de valor ----
  const wonValues = closedDeals.filter(d => d.deal_stage === 'Won' && d.close_value > 0).map(d => d.close_value);
  const maxDealValue = Math.max(...wonValues, 1);
  const avgDealValue = wonValues.reduce((s, v) => s + v, 0) / Math.max(wonValues.length, 1);
  // Referência de EV: deal médio (avgDealValue × avgWinRate) → score 50; 2× → score 100
  const refExpectedValue = avgDealValue * avgWinRate * 2;

  return {
    accountMap,
    productMap,
    teamMap,
    agentWinRates,
    avgWinRate,
    productPerf,
    sectorWinRates,
    revBandWinRates,
    empBandWinRates,
    getRevBand,
    getEmpBand,
    accountWonCount,
    medianAges,
    maxDealValue,
    avgDealValue,
    refExpectedValue,
  };
}

function normalizeProduct(name) {
  if (!name) return '';
  return name.replace(/GTXPro/gi, 'GTX Pro').trim();
}

// ============================================================
// MOTOR DE SCORING
// ============================================================
function scoreActiveDeals() {
  const { pipeline } = rawData;
  const activeDeals = pipeline.filter(d =>
    d.deal_stage === 'Prospecting' || d.deal_stage === 'Engaging'
  );

  return activeDeals.map(deal => scoreDeal(deal)).sort((a, b) => b.score - a.score);
}

function scoreDeal(deal) {
  const s = historicalStats;
  const account = s.accountMap[deal.account] || {};
  const product = s.productMap[normalizeProduct(deal.product)] || {};
  const team = s.teamMap[deal.sales_agent] || {};

  const factors = {};
  const explanations = {};

  // ---- 1. Aderência da Conta (20%) ----
  {
    const sector = account.sector || 'desconhecido';
    const sectorWR = s.sectorWinRates[sector] || s.avgWinRate;
    const revBand = s.getRevBand(account.revenue || 0);
    const revWR = s.revBandWinRates[revBand] || s.avgWinRate;
    const empBand = s.getEmpBand(account.employees || 0);
    const empWR = s.empBandWinRates[empBand] || s.avgWinRate;

    // Média ponderada consistente das 3 dimensões (setor > receita > porte)
    // Normalizado pelo avgWinRate: conta "média" → score 50
    const compositeWR = sectorWR * 0.5 + revWR * 0.3 + empWR * 0.2;
    const score = clamp((compositeWR / Math.max(s.avgWinRate, 0.01)) * 50, 0, 100);
    factors.accountFit = score;

    if (!deal.account) {
      explanations.accountFit = 'Sem conta associada — não é possível avaliar aderência.';
    } else if (score >= 70) {
      explanations.accountFit = `Setor ${sector} e perfil de receita ${revBand} combinam com padrões de alta conversão.`;
    } else if (score >= 40) {
      explanations.accountFit = `Setor ${sector} apresenta conversão média para este perfil de empresa.`;
    } else {
      explanations.accountFit = `Setor ${sector} e faixa de receita ${revBand} historicamente abaixo da média.`;
    }
  }

  // ---- 2. Performance do Produto (15%) ----
  {
    const pName = normalizeProduct(deal.product);
    const perf = s.productPerf[pName] || { winRate: s.avgWinRate, avgCloseValue: s.avgDealValue };

    const wrNorm = Math.min(perf.winRate / Math.max(s.avgWinRate * 1.2, 0.01), 1.5);
    const wrScore = wrNorm * 60;

    const valNorm = Math.min(perf.avgCloseValue / Math.max(s.avgDealValue * 1.5, 1), 1.2);
    const valScore = valNorm * 40;

    const score = clamp(wrScore + valScore, 0, 100);
    factors.productPerformance = score;

    if (score >= 70) {
      explanations.productPerformance = `${pName} tem forte conversão (${(perf.winRate * 100).toFixed(0)}% de taxa de ganho) e bom ticket médio.`;
    } else if (score >= 40) {
      explanations.productPerformance = `${pName} apresenta desempenho médio (${(perf.winRate * 100).toFixed(0)}% de taxa de ganho).`;
    } else {
      explanations.productPerformance = `${pName} historicamente tem conversão mais baixa (${(perf.winRate * 100).toFixed(0)}% de taxa de ganho).`;
    }
  }

  // ---- 3. Força do Estágio (20%) ----
  {
    let score;
    if (deal.deal_stage === 'Engaging') {
      score = 75;
      explanations.dealStage = 'Estágio Engaging — o prospect demonstrou interesse ativo, conversão historicamente maior.';
    } else {
      score = 40;
      explanations.dealStage = 'Estágio Prospecting — início do pipeline, menor probabilidade de conversão mas vale nutrir.';
    }
    factors.dealStage = score;
  }

  // ---- 4. Saúde de Idade no Pipeline (20%) ----
  {
    const engageDate = deal.engage_date ? new Date(deal.engage_date) : null;
    let ageInDays;

    if (engageDate && !isNaN(engageDate)) {
      ageInDays = Math.max(0, Math.round((REFERENCE_DATE - engageDate) / 86400000));
    } else {
      ageInDays = 90;
    }

    const medianAge = s.medianAges[deal.deal_stage] || 120;
    const ratio = ageInDays / medianAge;

    let score;
    if (ratio <= 0.5) {
      score = 65;
      explanations.stageAging = `Deal recente (${ageInDays} dias). Ainda na fase inicial — acompanhe de perto.`;
    } else if (ratio <= 0.9) {
      score = 90;
      explanations.stageAging = `Janela ideal de conversão (${ageInDays} dias). Momento certo para avançar.`;
    } else if (ratio <= 1.2) {
      score = 70;
      explanations.stageAging = `Deal amadurecendo (${ageInDays} dias). Próximo do prazo típico — agir em breve.`;
    } else if (ratio <= 1.8) {
      score = 45;
      explanations.stageAging = `Deal envelhecendo (${ageInDays} dias). Além do ciclo típico de ganho — precisa de atenção.`;
    } else if (ratio <= 3.0) {
      score = 25;
      explanations.stageAging = `Deal significativamente atrasado (${ageInDays} dias). Risco alto de esfriar — ação urgente.`;
    } else {
      score = 10;
      explanations.stageAging = `Deal crítico (${ageInDays} dias). Muito além do ciclo normal — avaliar se ainda está vivo.`;
    }

    factors.stageAging = score;
    deal._ageInDays = ageInDays;
  }

  // ---- 5. Taxa de Ganho do Vendedor (10%) ----
  {
    const agentWR = s.agentWinRates[deal.sales_agent] || s.avgWinRate;
    const ratio = agentWR / Math.max(s.avgWinRate, 0.01);
    // Simétrico em torno de 50: vendedor médio → 50, 1.67× média → 100, 0 → -10 (clamped 0)
    const score = clamp(50 + (ratio - 1) * 60, 0, 100);

    factors.agentWinRate = score;
    if (ratio >= 1.1) {
      explanations.agentWinRate = `${deal.sales_agent} tem taxa de ganho acima da média (${(agentWR * 100).toFixed(0)}%).`;
    } else if (ratio >= 0.9) {
      explanations.agentWinRate = `${deal.sales_agent} tem taxa de ganho próxima da média do time (${(agentWR * 100).toFixed(0)}%).`;
    } else {
      explanations.agentWinRate = `${deal.sales_agent} tem taxa de ganho abaixo da média do time (${(agentWR * 100).toFixed(0)}%). Pode precisar de apoio.`;
    }
  }

  // ---- 6. Histórico da Conta (5%) ----
  {
    const pastWins = s.accountWonCount[deal.account] || 0;
    let score;
    if (pastWins >= 5) {
      score = 100;
      explanations.accountHistory = `${deal.account || 'Desconhecida'} tem ${pastWins} deals ganhos anteriores — relacionamento forte.`;
    } else if (pastWins >= 2) {
      score = 70;
      explanations.accountHistory = `${deal.account || 'Desconhecida'} tem ${pastWins} deals ganhos anteriores — cliente recorrente.`;
    } else if (pastWins === 1) {
      score = 45;
      explanations.accountHistory = `${deal.account || 'Desconhecida'} tem 1 deal ganho anterior — alguma confiança estabelecida.`;
    } else {
      score = 20;
      explanations.accountHistory = deal.account
        ? `Sem deals ganhos anteriores com ${deal.account}. Relacionamento novo.`
        : 'Sem conta associada.';
    }
    factors.accountHistory = score;
  }

  // ---- 7. Valor Esperado (10%) ----
  {
    const pName = normalizeProduct(deal.product);
    const perf = s.productPerf[pName] || { winRate: s.avgWinRate, avgCloseValue: s.avgDealValue };
    const agentWR = s.agentWinRates[deal.sales_agent] || s.avgWinRate;

    // Usa APENAS taxa do vendedor × ticket médio do produto
    // (taxa do produto já pesa no Fator 2 — elimina dupla-contagem)
    const estimatedValue = perf.avgCloseValue * agentWR;
    const score = clamp((estimatedValue / Math.max(s.refExpectedValue, 1)) * 100, 0, 100);

    factors.expectedValue = score;
    deal._expectedValue = Math.round(estimatedValue);
    deal._estimatedWR = agentWR;

    if (score >= 60) {
      explanations.expectedValue = `Alto valor esperado: R$${formatNumber(deal._expectedValue)} (taxa do vendedor ${(deal._estimatedWR * 100).toFixed(0)}% × ticket médio do produto).`;
    } else if (score >= 30) {
      explanations.expectedValue = `Valor esperado moderado: R$${formatNumber(deal._expectedValue)}.`;
    } else {
      explanations.expectedValue = `Baixo valor esperado: R$${formatNumber(deal._expectedValue)}. Considere esforço vs. retorno.`;
    }
  }

  // ---- SCORE COMPOSTO ----
  let totalScore = 0;
  for (const [key, weight] of Object.entries(FACTOR_WEIGHTS)) {
    totalScore += (factors[key] || 0) * weight;
  }
  totalScore = Math.round(clamp(totalScore, 0, 100));

  // ---- BUCKET DE PRIORIDADE ----
  const bucket = getBucket(totalScore);

  // ---- INSIGHT PRINCIPAL (Explainability nível 1) ----
  const topInsight = getTopInsight(factors, explanations, deal);

  return {
    ...deal,
    _product: normalizeProduct(deal.product),
    _account: deal.account || '—',
    _team: historicalStats.teamMap[deal.sales_agent] || {},
    score: totalScore,
    bucket,
    factors,
    explanations,
    topInsight,
  };
}

function getBucket(score) {
  for (const b of BUCKET_THRESHOLDS) {
    if (score >= b.min) return b;
  }
  return BUCKET_THRESHOLDS[BUCKET_THRESHOLDS.length - 1];
}

function getTopInsight(factors, explanations, deal) {
  const sorted = Object.entries(factors).sort((a, b) => b[1] - a[1]);
  const best = sorted[0];
  const worst = sorted[sorted.length - 1];

  const labels = {
    accountFit: 'Aderência da conta',
    productPerformance: 'Desempenho do produto',
    dealStage: 'Estágio do deal',
    stageAging: 'Saúde no pipeline',
    agentWinRate: 'Histórico do vendedor',
    accountHistory: 'Histórico da conta',
    expectedValue: 'Valor esperado',
  };

  if (best[1] >= 70 && worst[1] >= 50) {
    return `✅ ${labels[best[0]]} forte`;
  } else if (worst[1] < 30) {
    return `⚠️ ${labels[worst[0]]} é uma preocupação`;
  } else if (best[1] >= 70) {
    return `✅ ${labels[best[0]]} forte · ⚠️ Atenção: ${labels[worst[0]].toLowerCase()}`;
  }
  return `${labels[best[0]]} é o principal impulsionador`;
}

function clamp(val, min, max) { return Math.min(Math.max(val, min), max); }

// ============================================================
// FILTROS, BUSCA, ORDENAÇÃO
// ============================================================
function populateFilters() {
  const { teams } = rawData;

  const regions = [...new Set(teams.map(t => t.regional_office))].sort();
  const managers = [...new Set(teams.map(t => t.manager))].sort();
  const agents = [...new Set(teams.map(t => t.sales_agent))].sort();

  fillSelect('filterRegion', regions);
  fillSelect('filterManager', managers);
  fillSelect('filterAgent', agents);
}

function fillSelect(id, items) {
  const select = document.getElementById(id);
  const first = select.options[0];
  select.innerHTML = '';
  select.appendChild(first);
  items.forEach(item => {
    const opt = document.createElement('option');
    opt.value = item; opt.textContent = item;
    select.appendChild(opt);
  });
}

function applyFilters() {
  const search = document.getElementById('searchInput').value.toLowerCase().trim();
  const region = document.getElementById('filterRegion').value;
  const manager = document.getElementById('filterManager').value;
  const agent = document.getElementById('filterAgent').value;
  const stage = document.getElementById('filterStage').value;
  const bucket = document.getElementById('filterBucket').value;

  filteredDeals = scoredDeals.filter(deal => {
    if (region && (deal._team.regional_office !== region)) return false;
    if (manager && (deal._team.manager !== manager)) return false;
    if (agent && (deal.sales_agent !== agent)) return false;
    if (stage && (deal.deal_stage !== stage)) return false;
    if (bucket && (deal.bucket.label !== bucket)) return false;
    if (search) {
      const hay = [
        deal._account, deal.sales_agent, deal._product,
        deal.opportunity_id, deal.bucket.label,
      ].join(' ').toLowerCase();
      if (!hay.includes(search)) return false;
    }
    return true;
  });

  sortDeals();
  render();
}

function clearFilters() {
  document.getElementById('searchInput').value = '';
  document.getElementById('filterRegion').value = '';
  document.getElementById('filterManager').value = '';
  document.getElementById('filterAgent').value = '';
  document.getElementById('filterStage').value = '';
  document.getElementById('filterBucket').value = '';
  applyFilters();
}

function sortDeals() {
  const { key, asc } = currentSort;
  const dir = asc ? 1 : -1;

  filteredDeals.sort((a, b) => {
    let va, vb;
    switch (key) {
      case 'score':         va = a.score; vb = b.score; break;
      case 'bucket':        va = a.score; vb = b.score; break;
      case 'account':       va = a._account; vb = b._account; return va.localeCompare(vb) * dir;
      case 'product':       va = a._product; vb = b._product; return va.localeCompare(vb) * dir;
      case 'stage':         va = a.deal_stage; vb = b.deal_stage; return va.localeCompare(vb) * dir;
      case 'agent':         va = a.sales_agent; vb = b.sales_agent; return va.localeCompare(vb) * dir;
      case 'expectedValue': va = a._expectedValue || 0; vb = b._expectedValue || 0; break;
      case 'age':           va = a._ageInDays || 0; vb = b._ageInDays || 0; break;
      default:              va = a.score; vb = b.score;
    }
    return (va - vb) * dir;
  });
}

// ============================================================
// RENDERIZAÇÃO
// ============================================================
function render() {
  renderKPIs();
  renderSpotlights();
  renderBuckets();
  renderTable();
}

function renderKPIs() {
  const deals = filteredDeals;
  const totalDeals = deals.length;
  const engCount = deals.filter(d => d.deal_stage === 'Engaging').length;
  const prosCount = deals.filter(d => d.deal_stage === 'Prospecting').length;

  const totalEV = deals.reduce((s, d) => s + (d._expectedValue || 0), 0);
  const avgScore = totalDeals > 0
    ? Math.round(deals.reduce((s, d) => s + d.score, 0) / totalDeals)
    : 0;

  const agentsInView = new Set(deals.map(d => d.sales_agent)).size;
  const managersInView = new Set(deals.map(d => d._team.manager).filter(Boolean)).size;

  document.getElementById('kpiDeals').textContent = totalDeals;
  document.getElementById('kpiDealsDetail').textContent = `${engCount} Engaging · ${prosCount} Prospecting`;
  document.getElementById('kpiValue').textContent = 'R$' + formatNumber(totalEV);
  document.getElementById('kpiAvgScore').textContent = avgScore;
  document.getElementById('kpiAgents').textContent = agentsInView;
  document.getElementById('kpiAgentsDetail').textContent = `${managersInView} managers`;
}

function renderSpotlights() {
  // Top 5
  const top5 = filteredDeals.slice(0, 5);
  const topList = document.getElementById('topDealsList');
  topList.innerHTML = top5.map(d => spotlightItem(d)).join('');
  topList.querySelectorAll('.spotlight-deal').forEach((el, i) => {
    el.addEventListener('click', () => openModal(top5[i]));
  });

  // Em risco: deals com stageAging baixo mas score razoável
  const atRisk = filteredDeals
    .filter(d => d.factors.stageAging < 45 && d.score >= 25)
    .sort((a, b) => a.factors.stageAging - b.factors.stageAging)
    .slice(0, 5);
  const riskList = document.getElementById('atRiskList');
  if (atRisk.length === 0) {
    riskList.innerHTML = '<div style="color:var(--text-muted);font-size:0.82rem;padding:8px 16px;">Nenhum deal em risco na visualização atual.</div>';
  } else {
    riskList.innerHTML = atRisk.map(d => spotlightItem(d, true)).join('');
    riskList.querySelectorAll('.spotlight-deal').forEach((el, i) => {
      el.addEventListener('click', () => openModal(atRisk[i]));
    });
  }
}

function spotlightItem(deal, isRisk = false) {
  const css = deal.bucket.css;
  return `
    <div class="spotlight-deal">
      <div class="deal-info">
        <div class="deal-account">${escHtml(deal._account)}</div>
        <div class="deal-meta">${escHtml(deal._product)} · ${escHtml(deal.sales_agent)} · ${deal._ageInDays || '?'}d ${isRisk ? '· ⏰ envelhecendo' : ''}</div>
      </div>
      <div class="deal-score-mini">
        <span class="score-badge ${css}">${deal.score}</span>
      </div>
    </div>
  `;
}

function renderBuckets() {
  const counts = {};
  BUCKET_THRESHOLDS.forEach(b => { counts[b.label] = 0; });
  scoredDeals.forEach(d => { counts[d.bucket.label]++; });

  const max = Math.max(...Object.values(counts), 1);
  const container = document.getElementById('bucketBars');
  container.innerHTML = BUCKET_THRESHOLDS.map(b => {
    const count = counts[b.label];
    const height = Math.max((count / max) * 56, 4);
    const colors = {
      focus: 'var(--score-focus)', high: 'var(--score-high)',
      week: 'var(--score-week)', monitor: 'var(--score-monitor)', low: 'var(--score-low)',
    };
    return `
      <div class="bucket-item">
        <div class="bucket-count" style="color:${colors[b.css]}">${count}</div>
        <div class="bucket-bar-wrapper">
          <div class="bucket-bar" style="height:${height}px;background:${colors[b.css]}"></div>
        </div>
        <div class="bucket-label">${b.label}</div>
      </div>
    `;
  }).join('');
}

function renderTable() {
  const tbody = document.getElementById('dealsBody');
  const emptyEl = document.getElementById('emptyState');
  const wrapper = document.querySelector('.table-wrapper');

  if (filteredDeals.length === 0) {
    wrapper.style.display = 'none';
    emptyEl.style.display = 'block';
    return;
  }

  wrapper.style.display = '';
  emptyEl.style.display = 'none';

  tbody.innerHTML = filteredDeals.map(deal => {
    const css = deal.bucket.css;
    const stageCSS = deal.deal_stage === 'Engaging' ? 'engaging' : 'prospecting';
    const ev = deal._expectedValue ? 'R$' + formatNumber(deal._expectedValue) : '—';
    return `
      <tr data-id="${deal.opportunity_id}">
        <td><span class="score-badge ${css}">${deal.score}</span></td>
        <td><span class="priority-tag ${css}">${deal.bucket.label}</span></td>
        <td>${escHtml(deal._account)}</td>
        <td>${escHtml(deal._product)}</td>
        <td><span class="stage-tag ${stageCSS}">${deal.deal_stage}</span></td>
        <td>${escHtml(deal.sales_agent)}</td>
        <td>${ev}</td>
        <td>${deal._ageInDays != null ? deal._ageInDays : '—'}</td>
        <td><span class="explain-snippet">${escHtml(deal.topInsight)}</span></td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('tr').forEach(tr => {
    tr.addEventListener('click', () => {
      const id = tr.dataset.id;
      const deal = filteredDeals.find(d => d.opportunity_id === id);
      if (deal) openModal(deal);
    });
  });

  document.getElementById('tableFooter').textContent =
    `Exibindo ${filteredDeals.length} de ${scoredDeals.length} deals ativos`;

  document.querySelectorAll('.deals-table th[data-sort]').forEach(th => {
    th.classList.toggle('sorted', th.dataset.sort === currentSort.key);
    const arrow = th.querySelector('.sort-arrow');
    if (arrow && th.dataset.sort === currentSort.key) {
      arrow.textContent = currentSort.asc ? '▲' : '▼';
    }
  });
}

// ============================================================
// MODAL
// ============================================================
function openModal(deal) {
  const overlay = document.getElementById('modalOverlay');
  overlay.classList.add('active');

  document.getElementById('modalDealId').textContent = deal.opportunity_id;
  document.getElementById('modalDealTitle').textContent = deal._account;

  const ev = deal._expectedValue ? 'R$' + formatNumber(deal._expectedValue) : '—';
  const wrPct = deal._estimatedWR ? (deal._estimatedWR * 100).toFixed(0) + '%' : '—';
  const engDate = deal.engage_date || '—';

  document.getElementById('modalOverview').innerHTML = `
    <div class="overview-item"><span class="overview-label">Produto</span><span class="overview-value">${escHtml(deal._product)}</span></div>
    <div class="overview-item"><span class="overview-label">Vendedor</span><span class="overview-value">${escHtml(deal.sales_agent)}</span></div>
    <div class="overview-item"><span class="overview-label">Estágio</span><span class="overview-value">${deal.deal_stage}</span></div>
    <div class="overview-item"><span class="overview-label">Idade</span><span class="overview-value">${deal._ageInDays != null ? deal._ageInDays + ' dias' : '—'}</span></div>
    <div class="overview-item"><span class="overview-label">Região</span><span class="overview-value">${deal._team.regional_office || '—'}</span></div>
    <div class="overview-item"><span class="overview-label">Manager</span><span class="overview-value">${deal._team.manager || '—'}</span></div>
    <div class="overview-item"><span class="overview-label">Data de Engajamento</span><span class="overview-value">${engDate}</span></div>
    <div class="overview-item"><span class="overview-label">Taxa Est. de Ganho</span><span class="overview-value">${wrPct}</span></div>
  `;

  const css = deal.bucket.css;
  document.getElementById('modalScoreHero').innerHTML = `
    <div class="score-circle ${css}">${deal.score}</div>
    <div class="score-hero-info">
      <div class="score-hero-bucket" style="color:var(--score-${css})">${deal.bucket.label}</div>
      <div class="score-hero-ev">Valor Esperado: ${ev}</div>
      <div class="score-hero-explain">${escHtml(deal.topInsight)}</div>
    </div>
  `;

  // Detalhamento dos fatores
  const factorMeta = {
    accountFit:         { name: 'Aderência da Conta',        maxPts: FACTOR_WEIGHTS.accountFit * 100 },
    productPerformance: { name: 'Desempenho do Produto',     maxPts: FACTOR_WEIGHTS.productPerformance * 100 },
    dealStage:          { name: 'Força do Estágio',          maxPts: FACTOR_WEIGHTS.dealStage * 100 },
    stageAging:         { name: 'Saúde de Idade no Pipeline',maxPts: FACTOR_WEIGHTS.stageAging * 100 },
    agentWinRate:       { name: 'Taxa de Ganho do Vendedor', maxPts: FACTOR_WEIGHTS.agentWinRate * 100 },
    accountHistory:     { name: 'Histórico da Conta',        maxPts: FACTOR_WEIGHTS.accountHistory * 100 },
    expectedValue:      { name: 'Valor Esperado do Deal',    maxPts: FACTOR_WEIGHTS.expectedValue * 100 },
  };

  const factorsHtml = Object.entries(deal.factors)
    .sort((a, b) => FACTOR_WEIGHTS[b[0]] - FACTOR_WEIGHTS[a[0]])
    .map(([key, rawScore]) => {
      const meta = factorMeta[key];
      const contribution = Math.round(rawScore * FACTOR_WEIGHTS[key]);
      const maxContrib = Math.round(meta.maxPts);
      const pct = Math.round(rawScore);
      const explain = deal.explanations[key] || '';

      let barColor;
      if (pct >= 70) barColor = 'var(--score-focus)';
      else if (pct >= 50) barColor = 'var(--score-high)';
      else if (pct >= 30) barColor = 'var(--score-week)';
      else barColor = 'var(--score-low)';

      return `
        <div class="factor-item">
          <div class="factor-header">
            <span class="factor-name">${meta.name}</span>
            <span class="factor-score">${contribution}/${maxContrib} pts</span>
          </div>
          <div class="factor-bar-bg">
            <div class="factor-bar-fill" style="width:${pct}%;background:${barColor}"></div>
          </div>
          <div class="factor-explain">${escHtml(explain)}</div>
        </div>
      `;
    }).join('');

  document.getElementById('modalFactors').innerHTML = factorsHtml;
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('active');
}

// ============================================================
// EXPORTAR
// ============================================================
function exportCSV() {
  if (filteredDeals.length === 0) return;

  const headers = [
    'ID Oportunidade', 'Score', 'Prioridade', 'Conta', 'Produto', 'Estágio',
    'Vendedor', 'Manager', 'Região', 'Valor Esperado', 'Idade (dias)', 'Insight',
  ];

  const rows = filteredDeals.map(d => [
    d.opportunity_id,
    d.score,
    d.bucket.label,
    d._account,
    d._product,
    d.deal_stage,
    d.sales_agent,
    d._team.manager || '',
    d._team.regional_office || '',
    d._expectedValue || '',
    d._ageInDays || '',
    d.topInsight,
  ]);

  let csv = headers.join(',') + '\n';
  rows.forEach(row => {
    csv += row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',') + '\n';
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `lead_scorer_export_${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

// ============================================================
// EVENTOS
// ============================================================
function bindEvents() {
  ['filterRegion', 'filterManager', 'filterAgent', 'filterStage', 'filterBucket'].forEach(id => {
    document.getElementById(id).addEventListener('change', applyFilters);
  });

  let searchTimer;
  document.getElementById('searchInput').addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(applyFilters, 250);
  });

  document.getElementById('btnClearFilters').addEventListener('click', clearFilters);
  document.getElementById('btnClearEmpty').addEventListener('click', clearFilters);

  document.querySelectorAll('.deals-table th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.sort;
      if (currentSort.key === key) {
        currentSort.asc = !currentSort.asc;
      } else {
        currentSort.key = key;
        currentSort.asc = false;
      }
      sortDeals();
      renderTable();
    });
  });

  document.getElementById('btnThemeToggle').addEventListener('click', toggleTheme);
  document.getElementById('btnExport').addEventListener('click', exportCSV);

  document.getElementById('modalClose').addEventListener('click', closeModal);
  document.getElementById('modalOverlay').addEventListener('click', (e) => {
    if (e.target === document.getElementById('modalOverlay')) closeModal();
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
}

function toggleTheme() {
  document.body.classList.toggle('light-mode');
  const isLight = document.body.classList.contains('light-mode');
  localStorage.setItem('ls_theme', isLight ? 'light' : 'dark');
  document.getElementById('btnThemeToggle').innerHTML = isLight ? '🌙' : '☀️';
}

function initTheme() {
  const saved = localStorage.getItem('ls_theme');
  if (saved === 'light') {
    document.body.classList.add('light-mode');
    document.getElementById('btnThemeToggle').innerHTML = '🌙';
  }
}

// ============================================================
// UTILITÁRIOS
// ============================================================
function formatNumber(n) {
  if (n == null || isNaN(n)) return '0';
  return n.toLocaleString('pt-BR', { maximumFractionDigits: 0 });
}

function escHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
