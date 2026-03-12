export type DealScoreInput = {
  deal: {
    opportunity_id: string;
    sales_agent: string;
    product: string;
    account: string;
    deal_stage: string;
    engage_date: string;
    close_date?: string | null;
    close_value?: string | number | null;
  };
  salesPipeline: Array<{
    opportunity_id: string;
    sales_agent: string;
    product: string;
    account: string;
    deal_stage: string;
    engage_date: string;
    close_date?: string | null;
    close_value?: string | number | null;
  }>;
  accounts: Array<{
    account: string;
    sector: string;
    revenue: string | number;
  }>;
  products: Array<{
    product: string;
    sales_price: string | number;
  }>;
  asOfDate?: Date | string;
};

export type ScoreFactor = {
  criterion: string;
  label: string;
  weight: number;
  multiple: number;
  signedImpact: number;
  reason: string;
};

export type DealScoreBreakdown = {
  finalScore: number;
  factors: ScoreFactor[];
  topPositiveFactors: ScoreFactor[];
  topNegativeFactors: ScoreFactor[];
};

export function calculateDealScoreBreakdown(
  input: DealScoreInput,
): DealScoreBreakdown {
  const { deal, salesPipeline, accounts, products } = input;
  const asOfDate = input.asOfDate ? new Date(input.asOfDate) : new Date();

  const WEIGHTS = {
    criterion1: 1.35,
    criterion2: -1.0,
    criterion3: -0.85,
    criterion4: 1.1,
    criterion5: 1.25,
    criterion6: 0.9,
    criterion7: 0.8,
    criterion8: 1.15,
    criterion9: 1.0,
  } as const;

  const normalize = (value: string | null | undefined): string =>
    (value ?? "").trim().toLowerCase();

  const normalizeProduct = (value: string | null | undefined): string =>
    normalize(value).replace(/\s+/g, "");

  const parseNumber = (value: string | number | null | undefined): number => {
    const parsed = typeof value === "number" ? value : Number(value ?? 0);
    return Number.isFinite(parsed) ? parsed : 0;
  };

  const parseDate = (value: string | null | undefined): Date | null => {
    if (!value) return null;
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  };

  const daysBetween = (
    startDate: Date | null,
    endDate: Date | null,
  ): number | null => {
    if (!startDate || !endDate) return null;
    const diffMs = endDate.getTime() - startDate.getTime();
    if (!Number.isFinite(diffMs)) return null;
    return Math.max(0, diffMs / 86_400_000);
  };

  const mean = (values: number[]): number => {
    if (values.length === 0) return 0;
    const total = values.reduce((sum, value) => sum + value, 0);
    return total / values.length;
  };

  const ratio = (numerator: number, denominator: number): number => {
    if (denominator <= 0 || !Number.isFinite(denominator)) return 1;
    if (!Number.isFinite(numerator)) return 1;
    const raw = numerator / denominator;
    if (!Number.isFinite(raw) || raw <= 0) return 1;
    return raw;
  };

  const inverse = (multiple: number): number => {
    if (!Number.isFinite(multiple) || multiple <= 0) return 1;
    return 1 / multiple;
  };

  const accountByName = new Map(
    accounts.map((account) => [normalize(account.account), account]),
  );

  const priceByProduct = new Map(
    products.map((product) => [
      normalizeProduct(product.product),
      parseNumber(product.sales_price),
    ]),
  );

  const isClosedDeal = (row: (typeof salesPipeline)[number]): boolean => {
    const stage = normalize(row.deal_stage);
    return stage === "won" || stage === "lost";
  };

  const isWonDeal = (row: (typeof salesPipeline)[number]): boolean =>
    normalize(row.deal_stage) === "won";

  const historicalClosedDeals = salesPipeline.filter(
    (row) => isClosedDeal(row) && parseDate(row.close_date) !== null,
  );

  const historicalWonDeals = historicalClosedDeals.filter(isWonDeal);

  const winRate = (rows: (typeof salesPipeline)[number][]): number => {
    if (rows.length === 0) return 0;
    const wins = rows.filter(isWonDeal).length;
    return wins / rows.length;
  };

  const cycleDays = (row: (typeof salesPipeline)[number]): number | null =>
    daysBetween(parseDate(row.engage_date), parseDate(row.close_date));

  const cycleDaysForRows = (rows: (typeof salesPipeline)[number][]): number[] =>
    rows
      .map(cycleDays)
      .filter(
        (value): value is number => value !== null && Number.isFinite(value),
      );

  const currentAgent = normalize(deal.sales_agent);
  const currentProduct = normalizeProduct(deal.product);
  const currentAccount = normalize(deal.account);
  const currentSector = normalize(accountByName.get(currentAccount)?.sector);

  // CRITERION 1
  const closedByAgent = historicalClosedDeals.filter(
    (row) => normalize(row.sales_agent) === currentAgent,
  );
  const closedByAgentAndProduct = closedByAgent.filter(
    (row) => normalizeProduct(row.product) === currentProduct,
  );
  const productWinRateByAgent = winRate(closedByAgentAndProduct);

  const otherProductsByAgent = Array.from(
    new Set(
      closedByAgent
        .map((row) => normalizeProduct(row.product))
        .filter((productKey) => productKey !== currentProduct),
    ),
  );

  const averageOtherProductWinRate = mean(
    otherProductsByAgent.map((productKey) => {
      const rows = closedByAgent.filter(
        (row) => normalizeProduct(row.product) === productKey,
      );
      return winRate(rows);
    }),
  );

  const criterion1Multiple = ratio(
    productWinRateByAgent,
    averageOtherProductWinRate,
  );

  // CRITERION 2
  const closedByProduct = historicalClosedDeals.filter(
    (row) => normalizeProduct(row.product) === currentProduct,
  );
  const closedByOtherProducts = historicalClosedDeals.filter(
    (row) => normalizeProduct(row.product) !== currentProduct,
  );

  const avgDaysProduct = mean(cycleDaysForRows(closedByProduct));
  const avgDaysOtherProducts = mean(cycleDaysForRows(closedByOtherProducts));
  const criterion2Multiple = ratio(avgDaysProduct, avgDaysOtherProducts);

  // CRITERION 3
  const closedByAccount = historicalClosedDeals.filter(
    (row) => normalize(row.account) === currentAccount,
  );
  const closedByOtherAccounts = historicalClosedDeals.filter(
    (row) => normalize(row.account) !== currentAccount,
  );

  const avgDaysAccount = mean(cycleDaysForRows(closedByAccount));
  const avgDaysOtherAccounts = mean(cycleDaysForRows(closedByOtherAccounts));
  const criterion3Multiple = ratio(avgDaysAccount, avgDaysOtherAccounts);

  // CRITERION 4
  const wonInSector = historicalWonDeals.filter((row) => {
    const accountSector = normalize(
      accountByName.get(normalize(row.account))?.sector,
    );
    return accountSector === currentSector;
  });

  const winsInSectorForProduct = wonInSector.filter(
    (row) => normalizeProduct(row.product) === currentProduct,
  ).length;

  const frequencyProductInSector = ratio(
    winsInSectorForProduct,
    wonInSector.length || 1,
  );

  const otherProductsInSector = Array.from(
    new Set(
      wonInSector
        .map((row) => normalizeProduct(row.product))
        .filter((productKey) => productKey !== currentProduct),
    ),
  );

  const avgOtherProductFrequencyInSector = mean(
    otherProductsInSector.map((productKey) => {
      const wins = wonInSector.filter(
        (row) => normalizeProduct(row.product) === productKey,
      ).length;
      return ratio(wins, wonInSector.length || 1);
    }),
  );

  const criterion4Multiple = ratio(
    frequencyProductInSector,
    avgOtherProductFrequencyInSector,
  );

  // CRITERION 5
  const allAgentClosedDeals = historicalClosedDeals.filter(
    (row) => normalize(row.sales_agent) === currentAgent,
  );

  const recentStart = new Date(asOfDate);
  recentStart.setMonth(recentStart.getMonth() - 3);

  const recentAgentClosedDeals = allAgentClosedDeals.filter((row) => {
    const closeDate = parseDate(row.close_date);
    return (
      closeDate !== null && closeDate >= recentStart && closeDate <= asOfDate
    );
  });

  const agentRecentWinRate = winRate(recentAgentClosedDeals);
  const agentOverallWinRate = winRate(allAgentClosedDeals);
  const criterion5Multiple = ratio(agentRecentWinRate, agentOverallWinRate);

  // CRITERION 6 (inverse multiple)
  const dealValue = Math.max(
    parseNumber(deal.close_value),
    priceByProduct.get(currentProduct) ?? 0,
  );

  const revenuesOfSimilarWonAccounts = historicalWonDeals
    .filter((row) => {
      const accountSector = normalize(
        accountByName.get(normalize(row.account))?.sector,
      );
      return accountSector === currentSector;
    })
    .map((row) =>
      parseNumber(accountByName.get(normalize(row.account))?.revenue),
    )
    .filter((revenue) => revenue > 0);

  const avgRevenueSimilarWonAccounts = mean(revenuesOfSimilarWonAccounts);
  const criterion6Multiple = ratio(dealValue, avgRevenueSimilarWonAccounts);

  // CRITERION 7 (inverse multiple)
  const openDeals = salesPipeline.filter((row) => !isClosedDeal(row));
  const openByAgentCount = openDeals.filter(
    (row) => normalize(row.sales_agent) === currentAgent,
  ).length;

  const openDealsByAgentMap = new Map<string, number>();
  for (const row of openDeals) {
    const agent = normalize(row.sales_agent);
    openDealsByAgentMap.set(agent, (openDealsByAgentMap.get(agent) ?? 0) + 1);
  }
  const avgOpenDealsByAgent = mean(Array.from(openDealsByAgentMap.values()));
  const criterion7Multiple = ratio(openByAgentCount, avgOpenDealsByAgent);

  // CRITERION 8 (inverse multiple)
  // Approximation: the CSV has no stage-entry timestamp, so we use deal age since engage_date.
  const currentAgeDays =
    daysBetween(parseDate(deal.engage_date), asOfDate) ?? 0;

  const historicalAverageCycleDays = mean(
    cycleDaysForRows(historicalClosedDeals),
  );

  const criterion8Multiple = ratio(currentAgeDays, historicalAverageCycleDays);

  // CRITERION 9
  const companyWonCount = historicalWonDeals.filter(
    (row) => normalize(row.account) === currentAccount,
  ).length;

  const wonCountByCompany = new Map<string, number>();
  for (const row of historicalWonDeals) {
    const account = normalize(row.account);
    wonCountByCompany.set(account, (wonCountByCompany.get(account) ?? 0) + 1);
  }

  const otherCompanyWonCounts = Array.from(wonCountByCompany.entries())
    .filter(([account]) => account !== currentAccount)
    .map(([, count]) => count);

  const avgOtherCompanyWonCount = mean(otherCompanyWonCounts);
  const criterion9Multiple = ratio(companyWonCount, avgOtherCompanyWonCount);

  const factors: ScoreFactor[] = [
    {
      criterion: "criterion1",
      label: "Aderencia do vendedor a este produto",
      weight: WEIGHTS.criterion1,
      multiple: criterion1Multiple,
      signedImpact: WEIGHTS.criterion1 * (criterion1Multiple - 1),
      reason:
        "Compara a taxa de ganho deste vendedor no produto com a taxa de ganho dele em outros produtos.",
    },
    {
      criterion: "criterion2",
      label: "Velocidade do ciclo do produto",
      weight: WEIGHTS.criterion2,
      multiple: criterion2Multiple,
      signedImpact: WEIGHTS.criterion2 * (criterion2Multiple - 1),
      reason:
        "Compara o tempo medio de fechamento deste produto com o de outros produtos.",
    },
    {
      criterion: "criterion3",
      label: "Velocidade do ciclo da conta",
      weight: WEIGHTS.criterion3,
      multiple: criterion3Multiple,
      signedImpact: WEIGHTS.criterion3 * (criterion3Multiple - 1),
      reason:
        "Compara o tempo medio de fechamento desta conta com o de outras contas.",
    },
    {
      criterion: "criterion4",
      label: "Demanda do produto no setor",
      weight: WEIGHTS.criterion4,
      multiple: criterion4Multiple,
      signedImpact: WEIGHTS.criterion4 * (criterion4Multiple - 1),
      reason:
        "Mede com que frequencia este produto vence no setor da conta em relação as alternativas.",
    },
    {
      criterion: "criterion5",
      label: "Momento recente do vendedor",
      weight: WEIGHTS.criterion5,
      multiple: criterion5Multiple,
      signedImpact: WEIGHTS.criterion5 * (criterion5Multiple - 1),
      reason:
        "Compara a taxa de ganho do vendedor nos ultimos 3 meses com sua linha de base de longo prazo.",
    },
    {
      criterion: "criterion6",
      label: "Tamanho do negócio vs contas similares",
      weight: WEIGHTS.criterion6,
      multiple: criterion6Multiple,
      signedImpact: WEIGHTS.criterion6 * (inverse(criterion6Multiple) - 1),
      reason:
        "Negócios acima do tamanho tipico em setores similares sao tratados como mais dificeis de fechar.",
    },
    {
      criterion: "criterion7",
      label: "Equilibrio de carga do vendedor",
      weight: WEIGHTS.criterion7,
      multiple: criterion7Multiple,
      signedImpact: WEIGHTS.criterion7 * (inverse(criterion7Multiple) - 1),
      reason:
        "Compara a quantidade de negócios abertos do vendedor com a media do time.",
    },
    {
      criterion: "criterion8",
      label: "Recencia do negócio",
      weight: WEIGHTS.criterion8,
      multiple: criterion8Multiple,
      signedImpact: WEIGHTS.criterion8 * (inverse(criterion8Multiple) - 1),
      reason:
        "Negócios abertos ha mais tempo recebem penalização em relação ao ciclo medio historico.",
    },
    {
      criterion: "criterion9",
      label: "Historico de ganhos da conta",
      weight: WEIGHTS.criterion9,
      multiple: criterion9Multiple,
      signedImpact: WEIGHTS.criterion9 * (criterion9Multiple - 1),
      reason:
        "Favorece contas em que a empresa venceu com frequencia acima da media.",
    },
  ];

  const rawScore = factors.reduce(
    (sum, factor) => sum + factor.signedImpact,
    0,
  );
  const scaledScore = 50 + rawScore * 15;
  const finalScore = Math.max(0, Math.min(100, Number(scaledScore.toFixed(2))));

  const topPositiveFactors = factors
    .filter((factor) => factor.signedImpact > 0)
    .sort((left, right) => right.signedImpact - left.signedImpact)
    .slice(0, 3);

  const topNegativeFactors = factors
    .filter((factor) => factor.signedImpact < 0)
    .sort((left, right) => left.signedImpact - right.signedImpact)
    .slice(0, 3);

  return {
    finalScore,
    factors,
    topPositiveFactors,
    topNegativeFactors,
  };
}

export function calculateDealScore(input: DealScoreInput): number {
  return calculateDealScoreBreakdown(input).finalScore;
}
