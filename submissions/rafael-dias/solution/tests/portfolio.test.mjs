import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { portfolioSummary, sortAgentsByOpen } from "../lib/portfolio.mjs";
test("explicação das carteiras confere com os responsáveis do dataset original", async () => {
  const data = JSON.parse(await fs.readFile("data/prepared.json", "utf8"));
  const before = data.opportunities.map((d) => d.sales_agent);
  assert.deepEqual(portfolioSummary(data), {
    total: 35,
    active: 27,
    empty: 8,
    min: 31,
    max: 194,
    closedOnly: 3,
    withoutPipeline: 5,
  });
  assert.deepEqual(
    data.opportunities.map((d) => d.sales_agent),
    before,
  );
});

test("seletor ordena por abertas e desempata pelo nome", () => {
  assert.deepEqual(
    sortAgentsByOpen(["Bia", "Ana", "Caio", "Duda"], {
      Ana: 3,
      Bia: 9,
      Caio: 3,
    }),
    ["Bia", "Ana", "Caio", "Duda"],
  );
});
