import test from "node:test";
import assert from "node:assert/strict";
import {
  selectSellerWorkspace,
  selectResultsScope,
} from "../lib/workspace-selectors.mjs";
import { createDailyPlan, localDay } from "../lib/sales-guide.mjs";
const now = "2026-11-06T15:00:00Z";
const deals = Array.from({ length: 8 }, (_, i) => ({
  opportunity_id: `D${i}`,
  sales_agent: i < 7 ? "Ana" : "Bia",
  account: `Conta ${i}`,
  score: 90 - i,
  status: "new",
  manager: i < 7 ? "M1" : "M2",
  regional_office: i < 7 ? "East" : "West",
  activities: [],
}));
test("projeção mantém plano fixo, conclusão e separação entre vendedores sem mutar dados", () => {
  const before = structuredClone(deals);
  const plan = createDailyPlan(
    deals.filter((d) => d.sales_agent === "Ana"),
    now,
  );
  const plans = { [`${localDay(now)}|Ana`]: plan };
  const events = [
    {
      opportunityId: "D0",
      agent: "Ana",
      type: "contact",
      at: "2026-11-06T15:01:00Z",
    },
  ];
  const model = selectSellerWorkspace(
    deals,
    "Ana",
    events,
    plans,
    "2026-11-06T16:00:00Z",
  );
  assert.equal(model.mine.length, 7);
  assert.deepEqual(
    model.top.map((d) => d.opportunity_id),
    ["D1", "D2", "D3", "D4"],
  );
  assert.equal(model.progress.completed, 1);
  assert.equal(model.contactsToday, 1);
  assert.deepEqual(deals, before);
  assert.equal(
    selectSellerWorkspace(deals, "Sem carteira", [], {}, now).top.length,
    0,
  );
});
test("resultados aplicam simultaneamente carteira, gestor e região", () => {
  assert.deepEqual(
    selectResultsScope(deals, {
      scope: "mine",
      agent: "Ana",
      manager: "M2",
      region: "",
    }),
    [],
  );
  assert.equal(
    selectResultsScope(deals, {
      scope: "company",
      agent: "Ana",
      manager: "M2",
      region: "West",
    })[0].sales_agent,
    "Bia",
  );
  assert.equal(
    selectResultsScope(deals, {
      scope: "company",
      agent: "Ana",
      manager: "",
      region: "East",
    }).length,
    7,
  );
});
