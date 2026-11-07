import fs from "node:fs/promises";
import { parse } from "csv-parse/sync";
import {
  buildReferences,
  normalizeProduct,
  scoreDeal,
  daysBetween,
  REFERENCE_DATE,
  median,
} from "../lib/scoring.mjs";
const tables = {};
for (const name of ["accounts", "products", "sales_teams", "sales_pipeline"]) {
  tables[name] = parse(await fs.readFile(`data/raw/${name}.csv`, "utf8"), {
    columns: true,
    skip_empty_lines: true,
    bom: true,
  }).map((row) =>
    Object.fromEntries(
      Object.entries(row).map(([k, v]) => [k, v === "" ? null : v]),
    ),
  );
}
const ids = tables.sales_pipeline.map((d) => d.opportunity_id);
if (new Set(ids).size !== ids.length) throw Error("Duplicate opportunity IDs");
const products = tables.products.map((p) => ({
  ...p,
  sales_price: Number(p.sales_price),
}));
const refs = buildReferences(tables.sales_pipeline);
const accountHistory = Object.fromEntries(
  tables.accounts.map((a) => {
    const rows = tables.sales_pipeline.filter(
      (d) =>
        d.account === a.account &&
        ["Won", "Lost"].includes(d.deal_stage) &&
        d.close_date &&
        d.close_date <= REFERENCE_DATE,
    );
    const wins = rows
      .filter((d) => d.deal_stage === "Won")
      .sort((a, b) => b.close_date.localeCompare(a.close_date));
    return [
      a.account,
      {
        won: wins.length,
        lost: rows.length - wins.length,
        lastWonDate: wins[0]?.close_date ?? null,
        lastWonProduct: wins[0] ? normalizeProduct(wins[0].product) : null,
      },
    ];
  }),
);
const opportunities = tables.sales_pipeline
  .filter((d) => ["Engaging", "Prospecting"].includes(d.deal_stage))
  .map((d) => {
    const productName = normalizeProduct(d.product),
      product = products.find((p) => p.product === productName),
      team = tables.sales_teams.find((t) => t.sales_agent === d.sales_agent),
      account = tables.accounts.find((a) => a.account === d.account);
    if (!product || !team || (d.account && !account))
      throw Error(`Invalid relationship ${d.opportunity_id}`);
    return {
      ...d,
      product: productName,
      close_date: undefined,
      close_value: undefined,
      ...team,
      sector: account?.sector ?? null,
      employees: account ? Number(account.employees) : null,
      revenue: account ? Number(account.revenue) : null,
      location: account?.office_location ?? null,
      year_established: account?.year_established ?? null,
      account_history: account ? accountHistory[account.account] : null,
      sales_price: product.sales_price,
      reference: refs[productName],
      ...scoreDeal(d, product, refs[productName]),
    };
  });
const history = tables.sales_pipeline.filter((d) =>
  ["Won", "Lost"].includes(d.deal_stage),
);
const cycles = Object.fromEntries(
  ["Won", "Lost", "All"].map((stage) => {
    const rows = history.filter(
      (d) => stage === "All" || d.deal_stage === stage,
    );
    const days = rows.map((d) => daysBetween(d.engage_date, d.close_date));
    return [
      stage,
      {
        count: rows.length,
        mean: days.reduce((a, b) => a + b, 0) / days.length,
        median: median(days),
      },
    ];
  }),
);
// Separate historical outcomes support reporting only. Never pass them to scoreDeal.
const historicalByAgent = tables.sales_teams.map((team) => {
  const rows = history.filter((d) => d.sales_agent === team.sales_agent),
    won = rows.filter((d) => d.deal_stage === "Won");
  return {
    ...team,
    won: won.length,
    lost: rows.length - won.length,
    revenue: won.reduce((n, d) => n + Number(d.close_value), 0),
  };
});
const dataset = {
  asOf: REFERENCE_DATE,
  source: "local",
  opportunities,
  historicalByAgent,
  summary: {
    total: ids.length,
    open: opportunities.length,
    missingAccounts: opportunities.filter((d) => !d.account).length,
    normalizedProducts: tables.sales_pipeline.filter(
      (d) => d.product === "GTXPro",
    ).length,
    cycles,
  },
  references: refs,
};
await fs.writeFile("data/prepared.json", JSON.stringify(dataset));
await fs.writeFile(
  "docs/data-profile.json",
  JSON.stringify({ ...dataset.summary, references: refs }, null, 2),
);
console.log(JSON.stringify(dataset.summary, null, 2));
