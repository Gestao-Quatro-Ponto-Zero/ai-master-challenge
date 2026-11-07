// Research-only comparison. Nothing imports this file into the application.
// Run: node scripts/compare-priority.mjs [5|20]
import fs from "node:fs/promises";
import crypto from "node:crypto";

const k = Number(process.argv[2] || 5);
if (![5, 20].includes(k)) throw Error("Use k=5 ou k=20.");
const source = await fs.readFile("data/prepared.json");
const data = JSON.parse(source);
const id = (a, b) => a.opportunity_id.localeCompare(b.opportunity_id);
const score = (a, b) => b.score - a.score || id(a, b);
const eligible = data.opportunities.filter((d) => d.account);
const groups = Object.groupBy(eligible, (d) => d.sales_agent);
const rank = (rows, compare, count) => [...rows].sort(compare).slice(0, count);
const age = (d) => (Number.isFinite(d.age) ? d.age : null);
const ageRank = (direction) => (a, b) => {
  if (age(a) === null) return age(b) === null ? id(a, b) : 1;
  if (age(b) === null) return -1;
  return direction * (a.age - b.age) || id(a, b);
};
const policies = {
  current: { label: "Score atual", select: (r, n) => rank(r, score, n) },
  price: {
    label: "Maior preço de catálogo",
    select: (r, n) =>
      rank(r, (a, b) => b.sales_price - a.sales_price || id(a, b), n),
  },
  oldest: {
    label: "Negociação mais antiga",
    select: (r, n) => rank(r, ageRank(-1), n),
  },
  newest: {
    label: "Negociação mais recente",
    select: (r, n) => rank(r, ageRank(1), n),
  },
  stage: {
    label: "Estágio primeiro",
    select: (r, n) =>
      rank(
        r,
        (a, b) =>
          Number(b.deal_stage === "Engaging") -
            Number(a.deal_stage === "Engaging") || id(a, b),
        n,
      ),
  },
  discovery: {
    label: "Experimento: 20% para descoberta",
    select(rows, n) {
      // An explicit workload hypothesis, not a learned optimum or a health score.
      const discovery = rank(
        rows.filter((d) => d.deal_stage === "Prospecting"),
        score,
        Math.ceil(n / 5),
      );
      const selected = new Set(discovery.map((d) => d.opportunity_id));
      return [
        ...rank(
          rows.filter((d) => !selected.has(d.opportunity_id)),
          score,
          Math.max(0, n - discovery.length),
        ),
        ...discovery,
      ];
    },
  },
};
const percent = (n, d) => (d ? Math.round((1000 * n) / d) / 10 : null);
const average = (values) =>
  values.length
    ? Math.round((10 * values.reduce((a, b) => a + b, 0)) / values.length) / 10
    : null;
const perSeller = Object.entries(groups).map(([agent, rows]) => {
  const count = Math.min(k, rows.length);
  return {
    agent,
    eligible: rows.length,
    selections: Object.fromEntries(
      Object.entries(policies).map(([key, p]) => [
        key,
        p.select(rows, count).map((d) => d.opportunity_id),
      ]),
    ),
  };
});
const byId = new Map(eligible.map((d) => [d.opportunity_id, d]));
const summary = Object.entries(policies).map(([key, p]) => {
  const chosen = perSeller.flatMap((s) =>
    s.selections[key].map((x) => byId.get(x)),
  );
  const products = Object.entries(Object.groupBy(chosen, (d) => d.product))
    .map(([product, rows]) => ({ product, count: rows.length }))
    .sort((a, b) => b.count - a.count || a.product.localeCompare(b.product));
  return {
    key,
    label: p.label,
    selected: chosen.length,
    prospectingPercent: percent(
      chosen.filter((d) => d.deal_stage === "Prospecting").length,
      chosen.length,
    ),
    averageCatalogUnitPriceUSD: average(chosen.map((d) => d.sales_price)),
    averageKnownSnapshotAgeDays: average(
      chosen.map(age).filter((v) => v !== null),
    ),
    unknownAgePercent: percent(
      chosen.filter((d) => age(d) === null).length,
      chosen.length,
    ),
    overTwoHistoricalCyclesPercent: percent(
      chosen.filter(
        (d) =>
          age(d) !== null &&
          d.reference?.days > 0 &&
          d.age > 2 * d.reference.days,
      ).length,
      chosen.length,
    ),
    dominantProduct: products[0]?.product || null,
    dominantProductPercent: percent(products[0]?.count || 0, chosen.length),
    meanOverlapWithCurrentPercent: average(
      perSeller.map((s) =>
        percent(
          s.selections[key].filter((x) => s.selections.current.includes(x))
            .length,
          s.selections.current.length,
        ),
      ),
    ),
    products,
  };
});
const reverseTieOverlap = average(
  Object.values(groups).map((rows) => {
    const n = Math.min(k, rows.length),
      original = rank(rows, score, n);
    const reversed = new Set(
      rank(rows, (a, b) => b.score - a.score || id(b, a), n).map(
        (d) => d.opportunity_id,
      ),
    );
    return percent(
      original.filter((d) => reversed.has(d.opportunity_id)).length,
      n,
    );
  }),
);
for (const seller of perSeller)
  for (const ids of Object.values(seller.selections)) {
    if (
      ids.length !== Math.min(k, seller.eligible) ||
      new Set(ids).size !== ids.length
    )
      throw Error("Quantidade inválida ou oportunidade duplicada.");
    if (ids.some((x) => byId.get(x)?.sales_agent !== seller.agent))
      throw Error("Carteiras misturadas.");
  }
const report = {
  purpose:
    "Comparação descritiva de composição; não mede conversão, lift ou eficácia do health score futuro.",
  source: "data/prepared.json",
  sourceSha256: crypto.createHash("sha256").update(source).digest("hex"),
  asOf: data.asOf,
  k,
  eligibility: {
    open: data.opportunities.length,
    identified: eligible.length,
    missingAccountExcluded: data.opportunities.length - eligible.length,
    sellersWithEligible: perSeller.length,
    commonPoolAndCapacity: true,
  },
  missingDates:
    "Idade ausente sempre por último nos comparadores temporais; não representa data de criação nem último contato.",
  reverseIdTieOverlapWithCurrentPercent: reverseTieOverlap,
  summary,
  perSeller,
};
const output = `docs/priority-comparison-top${k}.json`;
await fs.writeFile(output, JSON.stringify(report, null, 2) + "\n");
console.log(
  JSON.stringify(
    {
      output,
      eligibility: report.eligibility,
      reverseTieOverlap,
      summary: summary.map(({ products, ...row }) => row),
    },
    null,
    2,
  ),
);
