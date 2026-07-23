import fs from "node:fs";
import path from "node:path";
import { describe, expect, test } from "vitest";

const root = process.cwd();
const dataDir = path.join(root, "public", "data");
const routes = ["page.tsx", "quality/page.tsx", "journeys/page.tsx", "graph/page.tsx", "watchlist/page.tsx", "experiments/page.tsx", "governance/page.tsx", "demo/page.tsx"];
const forbiddenPhrases = ["at-risk revenue", "saved revenue", "guaranteed retention", "best action", "recommended discount", "ai decides", "causal driver"];

describe("dashboard static contract", () => {
  test("all primary routes exist", () => {
    routes.forEach((route) => expect(fs.existsSync(path.join(root, "app", route))).toBe(true));
  });

  test("all fifteen browser data files are valid JSON", () => {
    const files = fs.readdirSync(dataDir).filter((name) => name.endsWith(".json")).sort();
    expect(files).toHaveLength(15);
    files.forEach((file) => expect(() => JSON.parse(fs.readFileSync(path.join(dataDir, file), "utf8"))).not.toThrow());
  });

  test("browser data has no raw identifiers or PII fields", () => {
    const text = fs.readdirSync(dataDir).filter((name) => name.endsWith(".json")).map((name) => fs.readFileSync(path.join(dataDir, name), "utf8")).join("\n");
    expect(text).not.toMatch(/\b(?:A|S|U)-[0-9a-f]{6,}\b/i);
    expect(text.toLowerCase()).not.toMatch(/"(?:account_id|account_name|customer_id|email|feedback|source_record_id|subscription_id)"/);
  });

  test("renderable source avoids prohibited product language", () => {
    const componentText = [...routes.map((route) => path.join(root, "app", route)), ...fs.readdirSync(path.join(root, "components")).filter((name) => name.endsWith(".tsx")).map((name) => path.join(root, "components", name))].map((file) => fs.readFileSync(file, "utf8")).join("\n").toLowerCase();
    forbiddenPhrases.forEach((phrase) => expect(componentText).not.toContain(phrase));
  });

  test("demo data stays compact", () => {
    const total = fs.readdirSync(dataDir).filter((name) => name.endsWith(".json")).reduce((sum, name) => sum + fs.statSync(path.join(dataDir, name)).size, 0);
    expect(total).toBeLessThan(600_000);
  });
});
