import type {
  PipelineOpportunity,
  Account,
  Product,
  SPINContext,
} from '@/types';

/**
 * Build complete SPIN context from a deal and related data
 * Extracts all variables needed for script generation
 */
export function buildSPINContext(
  deal: PipelineOpportunity,
  allDeals: PipelineOpportunity[],
  account: Account | undefined,
  product: Product | undefined,
  allProducts: Product[]
): SPINContext {
  const accountDeals = account ? allDeals.filter((d) => d.account === account.account) : [];

  // === Account Data ===
  const accountName = account?.account || 'Prospect';
  const sector = account?.sector || 'Unknown';
  const employees = account?.employees || 0;
  const revenue = account?.revenue || 0;
  const location = account?.office_location || 'Unknown';

  // === Metrics ===
  const wonDeals = accountDeals.filter((d) => d.deal_stage === 'Won');
  const lostDeals = accountDeals.filter((d) => d.deal_stage === 'Lost');
  const engagingDeals = accountDeals.filter((d) => d.deal_stage === 'Engaging');
  const prospectingDeals = accountDeals.filter((d) => d.deal_stage === 'Prospecting');

  const winRate =
    wonDeals.length + lostDeals.length > 0
      ? wonDeals.length / (wonDeals.length + lostDeals.length)
      : 0;

  const avgTicket =
    wonDeals.length > 0
      ? wonDeals.reduce((sum, d) => sum + d.close_value, 0) / wonDeals.length
      : 0;

  const totalDeals = accountDeals.length;
  const activeDeals = engagingDeals.length + prospectingDeals.length;

  // === Pattern Analysis ===

  // Top product (most sold)
  const productSales = new Map<string, number>();
  for (const d of wonDeals) {
    productSales.set(d.product, (productSales.get(d.product) || 0) + 1);
  }
  const topProduct = productSales.size > 0
    ? Array.from(productSales.entries()).sort((a, b) => b[1] - a[1])[0][0]
    : product?.product || 'our solutions';

  // Failed products (lost deals)
  const failedProducts = Array.from(
    new Set(
      lostDeals
        .map((d) => d.product)
        .filter((p) => p && p !== topProduct)
    )
  );

  // Missing products (never bought)
  const boughtSeries = new Set<string>();
  for (const d of accountDeals) {
    const prod = allProducts.find((p) => p.product === d.product);
    if (prod) boughtSeries.add(prod.series);
  }

  const missingProducts = allProducts
    .filter((p) => !boughtSeries.has(p.series))
    .map((p) => p.series);

  // Best agent (most won deals with this account)
  const agentWins = new Map<string, number>();
  for (const d of wonDeals) {
    agentWins.set(d.sales_agent, (agentWins.get(d.sales_agent) || 0) + 1);
  }
  const bestAgent = agentWins.size > 0
    ? Array.from(agentWins.entries()).sort((a, b) => b[1] - a[1])[0][0]
    : 'our team';

  // Average cycle time (days from engage to close)
  const cycleTimeDays: number[] = [];
  for (const d of wonDeals) {
    if (d.close_date && d.engage_date) {
      const days = Math.floor(
        (d.close_date.getTime() - d.engage_date.getTime()) / (1000 * 60 * 60 * 24)
      );
      if (days > 0) cycleTimeDays.push(days);
    }
  }
  const avgCycleTime =
    cycleTimeDays.length > 0
      ? cycleTimeDays.reduce((a, b) => a + b, 0) / cycleTimeDays.length
      : 0;

  // Lost revenue (sum of lost deal values)
  const lostRevenue = lostDeals.reduce((sum, d) => sum + d.close_value, 0);

  // === Current Deal Info ===
  const currentProduct = deal.product;
  const currentStage = deal.deal_stage;

  const daysInPipeline = Math.floor(
    (new Date().getTime() - deal.engage_date.getTime()) / (1000 * 60 * 60 * 24)
  );

  return {
    // Account data
    accountName,
    sector,
    employees,
    revenue,
    location,

    // Metrics
    winRate,
    avgTicket,
    totalDeals,
    wonDeals: wonDeals.length,
    lostDeals: lostDeals.length,
    activeDeals,

    // Pattern analysis
    topProduct,
    failedProducts,
    missingProducts,
    bestAgent,
    avgCycleTime,
    lostRevenue,

    // Current deal
    currentProduct,
    currentStage,
    daysInPipeline,
  };
}

/**
 * Format context for display in templates
 */
export function formatContextForDisplay(context: SPINContext): Record<string, string> {
  return {
    accountName: context.accountName || 'Prospect',
    sector: context.sector || 'Unknown',
    employees: (context.employees ?? 0).toLocaleString(),
    revenue: `$${(context.revenue ?? 0).toLocaleString()}`,
    location: context.location || 'Unknown',
    winRate: `${((context.winRate ?? 0) * 100).toFixed(0)}%`,
    avgTicket: `$${(context.avgTicket ?? 0).toFixed(0)}`,
    totalDeals: (context.totalDeals ?? 0).toString(),
    wonDeals: (context.wonDeals ?? 0).toString(),
    lostDeals: (context.lostDeals ?? 0).toString(),
    activeDeals: (context.activeDeals ?? 0).toString(),
    topProduct: context.topProduct || 'our solutions',
    failedProducts: (context.failedProducts?.join(', ') ?? '') || 'none',
    missingProducts: (context.missingProducts?.join(', ') ?? '') || 'none',
    bestAgent: context.bestAgent || 'our team',
    avgCycleTime: (context.avgCycleTime ?? 0) > 0 ? `${Math.round(context.avgCycleTime ?? 0)} dias` : '—',
    lostRevenue: `$${(context.lostRevenue ?? 0).toFixed(0)}`,
    currentProduct: context.currentProduct || 'solution',
    currentStage: context.currentStage || 'Prospecting',
    daysInPipeline: (context.daysInPipeline ?? 0).toString(),
  };
}

/**
 * Get high-value insights from context
 */
export function getContextInsights(context: SPINContext): string[] {
  const insights: string[] = [];

  // Win rate insights
  if ((context.winRate ?? 0) >= 0.7) {
    insights.push(`Conta com histórico de sucesso: ${((context.winRate ?? 0) * 100).toFixed(0)}% de closes`);
  } else if ((context.winRate ?? 0) <= 0.3) {
    insights.push(`Conta com histórico desafiador: apenas ${((context.winRate ?? 0) * 100).toFixed(0)}% de closes`);
  }

  // Ticket insights
  if ((context.avgTicket ?? 0) > 5000) {
    insights.push(`Alto valor: ticket médio de $${(context.avgTicket ?? 0).toFixed(0)}`);
  }

  // Failed products
  if ((context.failedProducts?.length ?? 0) > 0) {
    insights.push(`Produtos com dificuldade: ${context.failedProducts?.slice(0, 2).join(', ')}`);
  }

  // Cross-sell opportunities
  if ((context.missingProducts?.length ?? 0) > 0) {
    insights.push(`Oportunidade de cross-sell: ${context.missingProducts?.slice(0, 2).join(', ')}`);
  }

  // Activity insights
  if ((context.activeDeals ?? 0) >= 3) {
    insights.push(`Conta altamente engajada: ${context.activeDeals} deals ativos`);
  }

  // Cycle time
  if ((context.avgCycleTime ?? 0) > 100) {
    insights.push(`Ciclo de venda longo: média de ${Math.round(context.avgCycleTime ?? 0)} dias`);
  }

  // Days in current pipeline
  if ((context.daysInPipeline ?? 0) > 180) {
    insights.push(`Deal travado: ${context.daysInPipeline} dias em pipeline`);
  }

  return insights;
}
