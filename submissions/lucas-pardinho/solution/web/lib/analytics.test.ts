import { describe, expect, it } from "vitest";
import {
  filterOpportunities,
  summarizeOpportunities,
  weightedValue,
} from "@/lib/analytics";
import { parseOpportunityQuery } from "@/lib/api";
import { formatCurrency, formatFullCurrency, formatNumber } from "@/lib/format";
import { SAMPLE_OPPORTUNITIES } from "@/lib/sample-data";

describe("analytics contract", () => {
  it("keeps rescue deals out of the weighted pipeline", () => {
    const rescue = SAMPLE_OPPORTUNITIES.find(
      (item) => item.queue === "Resgatar ou desqualificar",
    );

    expect(rescue).toBeDefined();
    expect(weightedValue(rescue!)).toBe(0);
  });

  it("summarizes all operational queues", () => {
    const summary = summarizeOpportunities(SAMPLE_OPPORTUNITIES);

    expect(summary.openDeals).toBe(5);
    expect(summary.focusNow).toBe(1);
    expect(summary.staleDeals).toBe(1);
    expect(summary.queues.map((item) => item.count)).toEqual([1, 1, 1, 1, 1]);
  });

  it("filters and sorts without mutating the source", () => {
    const source = [...SAMPLE_OPPORTUNITIES];
    const result = filterOpportunities(source, {
      regionalOffice: "Central",
      dealStage: "Engaging",
      sort: "score",
    });

    expect(result).toHaveLength(4);
    expect(result[0]?.opportunityId).toBe("DEV-FOCUS-01");
    expect(source).toEqual(SAMPLE_OPPORTUNITIES);
  });

  it("bounds pagination and accepts only supported sort values", () => {
    const query = parseOpportunityQuery(
      new URLSearchParams("page=2&pageSize=999&sort=unknown&order=asc"),
    );

    expect(query).toMatchObject({ page: 2, pageSize: 100, sort: "score", order: "asc" });
  });

  it("formats numbers deterministically on server and browser", () => {
    expect(formatNumber(2089)).toBe("2.089");
    expect(formatCurrency(4_966_215)).toBe("US$ 5,0 mi");
    expect(formatCurrency(245_264)).toBe("US$ 245,3 mil");
    expect(formatFullCurrency(5482)).toBe("US$ 5.482");
  });
});
