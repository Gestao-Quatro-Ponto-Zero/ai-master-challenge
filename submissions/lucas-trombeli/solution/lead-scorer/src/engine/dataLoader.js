// Data Loader — Parses all 4 CSVs and merges into unified pipeline data
import Papa from 'papaparse';

const CSV_FILES = {
  accounts: '/data/accounts.csv',
  products: '/data/products.csv',
  salesTeams: '/data/sales_teams.csv',
  pipeline: '/data/sales_pipeline.csv',
};

function parseCSV(url) {
  return new Promise((resolve, reject) => {
    Papa.parse(url, {
      download: true,
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (results) => resolve(results.data),
      error: (error) => reject(error),
    });
  });
}

export async function loadAllData() {
  const [accounts, products, salesTeams, pipeline] = await Promise.all([
    parseCSV(CSV_FILES.accounts),
    parseCSV(CSV_FILES.products),
    parseCSV(CSV_FILES.salesTeams),
    parseCSV(CSV_FILES.pipeline),
  ]);

  // Build lookup maps
  const accountMap = new Map();
  accounts.forEach((a) => accountMap.set(a.account, a));

  const productMap = new Map();
  products.forEach((p) => productMap.set(p.product, p));

  // Fix product name mismatch: pipeline has "GTXPro", products has "GTX Pro"
  const productNameFix = { GTXPro: 'GTX Pro' };

  const teamMap = new Map();
  salesTeams.forEach((t) => teamMap.set(t.sales_agent, t));

  // Compute reference date (latest close_date in dataset as "today")
  const closeDates = pipeline
    .map((d) => d.close_date)
    .filter(Boolean)
    .sort();
  const referenceDate = new Date(closeDates[closeDates.length - 1]);

  // Enrich pipeline deals
  const enrichedPipeline = pipeline.map((deal) => {
    const productKey = productNameFix[deal.product] || deal.product;
    const account = deal.account ? accountMap.get(deal.account) : null;
    const product = productMap.get(productKey);
    const team = teamMap.get(deal.sales_agent);

    const engageDate = deal.engage_date ? new Date(deal.engage_date) : null;
    const closeDate = deal.close_date ? new Date(deal.close_date) : null;

    // Calculate days in pipeline
    let daysInPipeline = null;
    if (engageDate) {
      const endDate = closeDate || referenceDate;
      daysInPipeline = Math.max(
        0,
        Math.round((endDate - engageDate) / (1000 * 60 * 60 * 24))
      );
    }

    return {
      ...deal,
      // Enriched fields
      accountData: account,
      productData: product,
      teamData: team,
      engageDateParsed: engageDate,
      closeDateParsed: closeDate,
      daysInPipeline,
      productValue: product?.sales_price || 0,
      sector: account?.sector || null,
      revenue: account?.revenue || null,
      employees: account?.employees || null,
      officeLocation: account?.office_location || null,
      subsidiaryOf: account?.subsidiary_of || null,
      manager: team?.manager || null,
      regionalOffice: team?.regional_office || null,
      hasAccount: !!account,
    };
  });

  return {
    accounts,
    products,
    salesTeams,
    pipeline: enrichedPipeline,
    referenceDate,
  };
}

// Compute historical statistics needed for scoring
export function computeHistoricalStats(pipeline) {
  // Only use closed deals (Won/Lost) for historical rates
  const closedDeals = pipeline.filter(
    (d) => d.deal_stage === 'Won' || d.deal_stage === 'Lost'
  );

  // Agent win rates
  const agentStats = new Map();
  closedDeals.forEach((d) => {
    if (!agentStats.has(d.sales_agent)) {
      agentStats.set(d.sales_agent, { won: 0, total: 0 });
    }
    const stat = agentStats.get(d.sales_agent);
    stat.total++;
    if (d.deal_stage === 'Won') stat.won++;
  });
  const agentWinRates = new Map();
  agentStats.forEach((stat, agent) => {
    agentWinRates.set(agent, stat.total > 0 ? stat.won / stat.total : 0.5);
  });

  // Product win rates
  const productStats = new Map();
  closedDeals.forEach((d) => {
    if (!productStats.has(d.product)) {
      productStats.set(d.product, { won: 0, total: 0 });
    }
    const stat = productStats.get(d.product);
    stat.total++;
    if (d.deal_stage === 'Won') stat.won++;
  });
  const productWinRates = new Map();
  productStats.forEach((stat, product) => {
    productWinRates.set(
      product,
      stat.total > 0 ? stat.won / stat.total : 0.5
    );
  });

  // Sector win rates
  const sectorStats = new Map();
  closedDeals
    .filter((d) => d.sector)
    .forEach((d) => {
      if (!sectorStats.has(d.sector)) {
        sectorStats.set(d.sector, { won: 0, total: 0 });
      }
      const stat = sectorStats.get(d.sector);
      stat.total++;
      if (d.deal_stage === 'Won') stat.won++;
    });
  const sectorWinRates = new Map();
  sectorStats.forEach((stat, sector) => {
    sectorWinRates.set(sector, stat.total > 0 ? stat.won / stat.total : 0.5);
  });

  // Global win rate
  const globalWinRate =
    closedDeals.filter((d) => d.deal_stage === 'Won').length /
    closedDeals.length;

  // Product value stats (for normalization)
  const productValues = [
    ...new Set(pipeline.map((d) => d.productValue).filter(Boolean)),
  ];
  const maxProductValue = Math.max(...productValues);
  const minProductValue = Math.min(...productValues);

  // Account size stats (for normalization)
  const revenues = pipeline
    .map((d) => d.revenue)
    .filter((r) => r != null && r > 0);
  const employees = pipeline
    .map((d) => d.employees)
    .filter((e) => e != null && e > 0);
  const maxRevenue = Math.max(...revenues);
  const maxEmployees = Math.max(...employees);

  return {
    agentWinRates,
    productWinRates,
    sectorWinRates,
    globalWinRate,
    maxProductValue,
    minProductValue,
    maxRevenue,
    maxEmployees,
  };
}
