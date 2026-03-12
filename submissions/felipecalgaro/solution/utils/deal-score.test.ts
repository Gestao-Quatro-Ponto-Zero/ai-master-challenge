import { describe, expect, it } from "vitest";

import {
  getAccountsRows,
  getProductRows,
  getSalesPipelineRows,
  type AccountRow,
  type ProductRow,
  type SalesPipelineRow,
} from "./crm-data";
import { calculateDealScore } from "./deal-score";

function buildClosedDeal(input: {
  id: string;
  salesAgent: string;
  product: string;
  account: string;
  stage: "Won" | "Lost";
  engageDate: string;
  closeDate: string;
  closeValue?: string;
}): SalesPipelineRow {
  return {
    opportunity_id: input.id,
    sales_agent: input.salesAgent,
    product: input.product,
    account: input.account,
    deal_stage: input.stage,
    engage_date: input.engageDate,
    close_date: input.closeDate,
    close_value: input.closeValue ?? "1000",
  };
}

function buildOpenDeal(input: {
  id: string;
  salesAgent: string;
  product: string;
  account: string;
  stage?: "Engaging" | "Prospecting";
  engageDate: string;
}): SalesPipelineRow {
  return {
    opportunity_id: input.id,
    sales_agent: input.salesAgent,
    product: input.product,
    account: input.account,
    deal_stage: input.stage ?? "Engaging",
    engage_date: input.engageDate,
    close_date: null,
    close_value: null,
  };
}

const BASE_PRODUCTS: ProductRow[] = [
  { product: "Fast Product", sales_price: "1000" },
  { product: "Slow Product", sales_price: "1000" },
];

const BASE_ACCOUNTS: AccountRow[] = [
  { account: "Fast Corp", sector: "tech", revenue: "5000" },
  { account: "Slow Corp", sector: "tech", revenue: "5000" },
  { account: "Neutral Corp", sector: "tech", revenue: "5000" },
];

describe("calculateDealScore", () => {
  it("keeps score deterministic and bounded in [0, 100]", async () => {
    const [salesPipeline, accounts, products] = await Promise.all([
      getSalesPipelineRows(),
      getAccountsRows(),
      getProductRows(),
    ]);

    const candidate =
      salesPipeline.find((row) => {
        const stage = row.deal_stage.trim().toLowerCase();
        return stage === "engaging" || stage === "prospecting";
      }) ?? salesPipeline[0];

    const asOfDate = "2017-07-01";

    const scoreA = calculateDealScore({
      deal: candidate,
      salesPipeline,
      accounts,
      products,
      asOfDate,
    });

    const scoreB = calculateDealScore({
      deal: candidate,
      salesPipeline,
      accounts,
      products,
      asOfDate,
    });

    expect(Number.isFinite(scoreA)).toBe(true);
    expect(scoreA).toBeGreaterThanOrEqual(0);
    expect(scoreA).toBeLessThanOrEqual(100);
    expect(scoreA).toBe(scoreB);
  });

  it("returns a finite score even with sparse or unknown references", () => {
    const score = calculateDealScore({
      deal: {
        opportunity_id: "UNKNOWN-1",
        sales_agent: "Unknown Agent",
        product: "Unknown Product",
        account: "Unknown Account",
        deal_stage: "Engaging",
        engage_date: "2017-01-01",
        close_date: null,
        close_value: null,
      },
      salesPipeline: [],
      accounts: [],
      products: [],
      asOfDate: "2017-06-01",
    });

    expect(Number.isFinite(score)).toBe(true);
    expect(score).toBeGreaterThanOrEqual(0);
    expect(score).toBeLessThanOrEqual(100);
  });

  it("gives higher score when rep-product historical win rate is better (criterion 1)", () => {
    const history: SalesPipelineRow[] = [];

    for (let index = 0; index < 8; index += 1) {
      history.push(
        buildClosedDeal({
          id: `A-WIN-${index}`,
          salesAgent: "Alice",
          product: "Fast Product",
          account: "Neutral Corp",
          stage: "Won",
          engageDate: "2016-01-01",
          closeDate: "2016-02-01",
        }),
      );
    }

    for (let index = 0; index < 2; index += 1) {
      history.push(
        buildClosedDeal({
          id: `A-LOSE-${index}`,
          salesAgent: "Alice",
          product: "Fast Product",
          account: "Neutral Corp",
          stage: "Lost",
          engageDate: "2016-01-01",
          closeDate: "2016-02-01",
        }),
      );
    }

    for (let index = 0; index < 1; index += 1) {
      history.push(
        buildClosedDeal({
          id: `B-WIN-${index}`,
          salesAgent: "Alice",
          product: "Slow Product",
          account: "Neutral Corp",
          stage: "Won",
          engageDate: "2016-01-01",
          closeDate: "2016-02-01",
        }),
      );
    }

    for (let index = 0; index < 9; index += 1) {
      history.push(
        buildClosedDeal({
          id: `B-LOSE-${index}`,
          salesAgent: "Alice",
          product: "Slow Product",
          account: "Neutral Corp",
          stage: "Lost",
          engageDate: "2016-01-01",
          closeDate: "2016-02-01",
        }),
      );
    }

    const fastDeal = buildOpenDeal({
      id: "OPEN-FAST",
      salesAgent: "Alice",
      product: "Fast Product",
      account: "Neutral Corp",
      engageDate: "2017-01-01",
    });

    const slowDeal = buildOpenDeal({
      id: "OPEN-SLOW",
      salesAgent: "Alice",
      product: "Slow Product",
      account: "Neutral Corp",
      engageDate: "2017-01-01",
    });

    const fastScore = calculateDealScore({
      deal: fastDeal,
      salesPipeline: history,
      accounts: BASE_ACCOUNTS,
      products: BASE_PRODUCTS,
      asOfDate: "2017-04-01",
    });

    const slowScore = calculateDealScore({
      deal: slowDeal,
      salesPipeline: history,
      accounts: BASE_ACCOUNTS,
      products: BASE_PRODUCTS,
      asOfDate: "2017-04-01",
    });

    expect(fastScore).toBeGreaterThan(slowScore);
  });

  it("rewards faster product/account cycle and penalizes stale deals (criteria 2, 3, 8)", () => {
    const history: SalesPipelineRow[] = [
      buildClosedDeal({
        id: "F-1",
        salesAgent: "Alice",
        product: "Fast Product",
        account: "Fast Corp",
        stage: "Won",
        engageDate: "2016-01-01",
        closeDate: "2016-01-10",
      }),
      buildClosedDeal({
        id: "F-2",
        salesAgent: "Alice",
        product: "Fast Product",
        account: "Fast Corp",
        stage: "Lost",
        engageDate: "2016-02-01",
        closeDate: "2016-02-12",
      }),
      buildClosedDeal({
        id: "S-1",
        salesAgent: "Alice",
        product: "Slow Product",
        account: "Slow Corp",
        stage: "Won",
        engageDate: "2016-01-01",
        closeDate: "2016-04-20",
      }),
      buildClosedDeal({
        id: "S-2",
        salesAgent: "Alice",
        product: "Slow Product",
        account: "Slow Corp",
        stage: "Lost",
        engageDate: "2016-02-01",
        closeDate: "2016-05-25",
      }),
    ];

    const fastRecentDeal = buildOpenDeal({
      id: "OPEN-FAST-RECENT",
      salesAgent: "Alice",
      product: "Fast Product",
      account: "Fast Corp",
      engageDate: "2017-03-20",
    });

    const slowOldDeal = buildOpenDeal({
      id: "OPEN-SLOW-OLD",
      salesAgent: "Alice",
      product: "Slow Product",
      account: "Slow Corp",
      engageDate: "2016-10-01",
    });

    const fastScore = calculateDealScore({
      deal: fastRecentDeal,
      salesPipeline: history,
      accounts: BASE_ACCOUNTS,
      products: BASE_PRODUCTS,
      asOfDate: "2017-04-01",
    });

    const slowScore = calculateDealScore({
      deal: slowOldDeal,
      salesPipeline: history,
      accounts: BASE_ACCOUNTS,
      products: BASE_PRODUCTS,
      asOfDate: "2017-04-01",
    });

    expect(fastScore).toBeGreaterThan(slowScore);
  });

  it("penalizes overloaded reps compared to balanced workload (criterion 7)", () => {
    const history: SalesPipelineRow[] = [
      buildClosedDeal({
        id: "ALICE-HIST-1",
        salesAgent: "Alice",
        product: "Fast Product",
        account: "Neutral Corp",
        stage: "Won",
        engageDate: "2016-01-01",
        closeDate: "2016-02-01",
      }),
      buildClosedDeal({
        id: "BOB-HIST-1",
        salesAgent: "Bob",
        product: "Fast Product",
        account: "Neutral Corp",
        stage: "Won",
        engageDate: "2016-01-01",
        closeDate: "2016-02-01",
      }),
      ...Array.from({ length: 20 }, (_, index) =>
        buildOpenDeal({
          id: `ALICE-OPEN-${index}`,
          salesAgent: "Alice",
          product: "Fast Product",
          account: "Neutral Corp",
          engageDate: "2017-01-01",
        }),
      ),
      ...Array.from({ length: 2 }, (_, index) =>
        buildOpenDeal({
          id: `BOB-OPEN-${index}`,
          salesAgent: "Bob",
          product: "Fast Product",
          account: "Neutral Corp",
          engageDate: "2017-01-01",
        }),
      ),
    ];

    const aliceDeal = buildOpenDeal({
      id: "ALICE-CANDIDATE",
      salesAgent: "Alice",
      product: "Fast Product",
      account: "Neutral Corp",
      engageDate: "2017-03-01",
    });

    const bobDeal = buildOpenDeal({
      id: "BOB-CANDIDATE",
      salesAgent: "Bob",
      product: "Fast Product",
      account: "Neutral Corp",
      engageDate: "2017-03-01",
    });

    const aliceScore = calculateDealScore({
      deal: aliceDeal,
      salesPipeline: history,
      accounts: BASE_ACCOUNTS,
      products: BASE_PRODUCTS,
      asOfDate: "2017-04-01",
    });

    const bobScore = calculateDealScore({
      deal: bobDeal,
      salesPipeline: history,
      accounts: BASE_ACCOUNTS,
      products: BASE_PRODUCTS,
      asOfDate: "2017-04-01",
    });

    expect(bobScore).toBeGreaterThan(aliceScore);
  });

  it("produces a sensible temporal ranking signal on real data", async () => {
    const [salesPipeline, accounts, products] = await Promise.all([
      getSalesPipelineRows(),
      getAccountsRows(),
      getProductRows(),
    ]);

    const parseDate = (value?: string | null): Date | null => {
      if (!value) return null;
      const parsed = new Date(value);
      return Number.isNaN(parsed.getTime()) ? null : parsed;
    };

    const isClosed = (row: SalesPipelineRow): boolean => {
      const stage = row.deal_stage.trim().toLowerCase();
      return stage === "won" || stage === "lost";
    };

    const closed = salesPipeline
      .filter((row) => isClosed(row) && parseDate(row.close_date) !== null)
      .sort((left, right) => {
        const leftTime = parseDate(left.close_date)?.getTime() ?? 0;
        const rightTime = parseDate(right.close_date)?.getTime() ?? 0;
        return leftTime - rightTime;
      });

    const splitIndex = Math.floor(closed.length * 0.7);
    const history = closed.slice(0, splitIndex);
    const evaluation = closed.slice(splitIndex);

    expect(history.length).toBeGreaterThan(100);
    expect(evaluation.length).toBeGreaterThan(100);

    const scored = evaluation.map((deal) => {
      const closeDate = parseDate(deal.close_date);
      const asOfDate = closeDate
        ? new Date(closeDate.getTime() - 86_400_000)
        : new Date("2018-01-01");

      const score = calculateDealScore({
        deal: {
          ...deal,
          // Avoid target leakage from closed value during evaluation.
          close_value: null,
        },
        salesPipeline: history,
        accounts,
        products,
        asOfDate,
      });

      return {
        score,
        won: deal.deal_stage.trim().toLowerCase() === "won",
      };
    });

    const sorted = scored
      .slice()
      .sort((left, right) => right.score - left.score);
    const quartileSize = Math.max(1, Math.floor(sorted.length * 0.25));

    const topQuartile = sorted.slice(0, quartileSize);
    const bottomQuartile = sorted.slice(-quartileSize);

    const winRate = (rows: Array<{ won: boolean }>): number => {
      if (rows.length === 0) return 0;
      const wins = rows.filter((row) => row.won).length;
      return wins / rows.length;
    };

    const topWinRate = winRate(topQuartile);
    const bottomWinRate = winRate(bottomQuartile);

    expect(Number.isFinite(topWinRate)).toBe(true);
    expect(Number.isFinite(bottomWinRate)).toBe(true);
    expect(Math.abs(topWinRate - bottomWinRate)).toBeGreaterThan(0.02);
  }, 30_000);
});
