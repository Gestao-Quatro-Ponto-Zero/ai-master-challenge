import { describe, expect, it } from "vitest";
import { buildDataset, DataValidationError, type RawTables } from "@/lib/data/build-dataset";

function tables(pipeline: Record<string, string>[]): RawTables {
  return {
    accounts: [
      {
        account: "Acme",
        sector: "technolgy",
        year_established: "1996",
        revenue: "1100.04",
        employees: "2822",
        office_location: "United States",
        subsidiary_of: "",
      },
    ],
    products: [{ product: "GTX Pro", series: "GTX", sales_price: "4821" }],
    salesTeams: [{ sales_agent: "Ana", manager: "Bia", regional_office: "East" }],
    pipeline,
  };
}

const deal = (overrides: Record<string, string> = {}) => ({
  opportunity_id: "D1",
  sales_agent: "Ana",
  product: "GTX Pro",
  account: "Acme",
  deal_stage: "Won",
  engage_date: "2017-01-10",
  close_date: "2017-03-01",
  close_value: "4500",
  ...overrides,
});

describe("buildDataset", () => {
  it("unifica o alias GTXPro e corrige o setor", () => {
    const ds = buildDataset(tables([deal({ product: "GTXPro" })]));
    expect(ds.deals[0]).toMatchObject({ product: "GTX Pro", listPrice: 4821, sector: "technology" });
    expect(ds.quality.map((q) => q.code)).toEqual(expect.arrayContaining(["product-alias", "sector-typo"]));
  });

  it("aceita deal aberto sem conta e sem datas", () => {
    const ds = buildDataset(
      tables([
        deal(),
        deal({ opportunity_id: "D2", deal_stage: "Prospecting", account: "", engage_date: "", close_date: "", close_value: "" }),
      ]),
    );
    expect(ds.deals[1]).toMatchObject({ account: null, sector: null, engageDate: null, closeValue: null });
  });

  it("falha se nenhum deal tem data", () => {
    expect(() =>
      buildDataset(tables([deal({ deal_stage: "Prospecting", engage_date: "", close_date: "", close_value: "" })])),
    ).toThrow(/data de referência/);
  });

  it("usa a maior data do pipeline como referência", () => {
    const ds = buildDataset(tables([deal(), deal({ opportunity_id: "D2", close_date: "2017-12-31" })]));
    expect(ds.referenceDate).toBe("2017-12-31");
  });

  it("falha com mensagem clara para produto desconhecido", () => {
    expect(() => buildDataset(tables([deal({ product: "Nada" })]))).toThrow(DataValidationError);
  });

  it("falha com mensagem clara para stage inválido", () => {
    expect(() => buildDataset(tables([deal({ deal_stage: "Closed" })]))).toThrow(/sales_pipeline.csv, linha 2/);
  });
});
