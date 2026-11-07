import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import {
  scoreDeal,
  buildReferences,
  normalizeProduct,
} from "../lib/scoring.mjs";
const base = {
  opportunity_id: "test",
  account: "Conta",
  product: "GTX Basic",
  deal_stage: "Engaging",
  engage_date: "2017-12-01",
};
const product = { sales_price: 550 },
  reference = { days: 45, count: 100 };
test("resultado e valor realizados não alteram pontos de oportunidade aberta", () => {
  const clean = scoreDeal(base, product, reference);
  const contaminated = scoreDeal(
    { ...base, close_value: 999999, close_date: "2099-01-01" },
    product,
    reference,
  );
  assert.deepEqual(clean, contaminated);
  assert.equal(
    scoreDeal({ ...base, deal_stage: "Won" }, product, reference),
    null,
  );
});
test("conta ausente gera ação e alerta sem penalizar score", () => {
  const missing = scoreDeal({ ...base, account: null }, product, reference);
  assert.equal(missing.score, scoreDeal(base, product, reference).score);
  assert.match(missing.action, /Identificar/);
});
test("referência ignora resultados futuros e usa fallback em amostras pequenas", () => {
  const rows = [
    {
      ...base,
      deal_stage: "Won",
      engage_date: "2017-01-01",
      close_date: "2017-01-11",
    },
    {
      ...base,
      deal_stage: "Won",
      engage_date: "2017-01-01",
      close_date: "2018-01-01",
    },
  ];
  const result = buildReferences(rows)["GTX Basic"];
  assert.equal(result.count, 1);
  assert.equal(result.days, 10);
  assert.equal(result.fallback, true);
});
test("negociação longa é sinalizada e sem data não inventa idade", () => {
  assert.equal(
    scoreDeal({ ...base, engage_date: "2017-01-01" }, product, reference)
      .review,
    true,
  );
  assert.equal(
    scoreDeal(
      { ...base, deal_stage: "Prospecting", engage_date: null },
      product,
      reference,
    ).age,
    null,
  );
  assert.equal(
    scoreDeal({ ...base, engage_date: "2018-01-01" }, product, reference),
    null,
  );
});
test("snapshot reconcilia dados e composição dos scores", async () => {
  const d = JSON.parse(await fs.readFile("data/prepared.json", "utf8"));
  assert.equal(d.opportunities.length, 2089);
  assert.equal(d.summary.total, 8800);
  assert.equal(d.opportunities.filter((r) => !r.account).length, 1425);
  assert.equal(
    new Set(d.opportunities.map((r) => r.opportunity_id)).size,
    2089,
  );
  for (const r of d.opportunities) {
    assert.ok(r.score >= 0 && r.score <= 100);
    assert.equal(
      r.score,
      r.factors.reduce((n, f) => n + f.points, 0),
    );
    assert.equal(r.close_value, undefined);
    assert.equal(r.close_date, undefined);
    assert.notEqual(r.product, "GTXPro");
  }
  assert.equal(normalizeProduct("GTXPro"), "GTX Pro");
});
