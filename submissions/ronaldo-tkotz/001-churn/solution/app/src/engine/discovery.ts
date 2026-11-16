/**
 * Discovery engine — the analyst that finds the stories, instead of us.
 *
 * The proactive insight feed and the deck arguments used to come from a fixed
 * catalog of detectors WE hand-authored from the dev warehouse (renewal_cliff,
 * seat_underutilisation, …). That bakes our reading of one dataset into the
 * product. This replaces it: at runtime the LLM explores whatever data is
 * connected and proposes the material findings itself.
 *
 * It stays grounded the same way the chat does — the model never states a number.
 * It returns a query (evidence_sql) plus which column to aggregate and how; OUR
 * code runs the query and computes the figure from the real rows. The model picks
 * the lens; the data supplies every number. A finding whose SQL fails or returns
 * nothing is dropped at the gate.
 *
 * Vertical-fixed, data-agnostic: the schema/domain (B2B SaaS revenue & retention)
 * is a known given handed to the model as context; the FINDINGS are discovered
 * fresh from the connected data and re-derive when the dataset rotates.
 */
import OpenAI from "openai";
import { schemaSnapshot, runQuery } from "./warehouse";
import { dataClock } from "./calendar";
import { getCache, putCache, clearCache } from "./appdb";

// Discovery's own minimal tool set — deliberately NOT the shared tools.ts layer.
// It may only read raw data and the schema; it must never reach run_metric / the
// vetted catalog (those encode rules we authored). Self-contained also breaks the
// discovery → tools → deck → discovery import cycle.
const DISCOVERY_TOOLS: OpenAI.Chat.Completions.ChatCompletionTool[] = [
  {
    type: "function",
    function: {
      name: "query_warehouse",
      description:
        "Run a single read-only SQL query (SELECT or WITH only) against the warehouse and get the rows, columns, and row count back.",
      parameters: {
        type: "object",
        properties: { sql: { type: "string", description: "A single read-only SELECT or WITH query." } },
        required: ["sql"],
        additionalProperties: false,
      },
    },
  },
  {
    type: "function",
    function: {
      name: "describe_schema",
      description: "Return the warehouse schema — every table with its column names and types.",
      parameters: { type: "object", properties: {}, additionalProperties: false },
    },
  },
];

function runDiscoveryTool(name: string, args: { sql?: string }): unknown {
  if (name === "query_warehouse") return runQuery(String(args.sql ?? ""));
  if (name === "describe_schema") return schemaSnapshot();
  throw new Error(`unknown discovery tool: ${name}`);
}

const DEFAULT_MODEL = process.env.LLM_MODEL ?? "deepseek-chat";
const BASE_URL = process.env.LLM_BASE_URL ?? "https://api.deepseek.com";

export type Severity = "critical" | "warning" | "opportunity" | "info";
export type ValueFormat = "usd" | "int" | "pct" | "raw";

/** What the model proposes — a lens + two queries, never a number itself. */
interface RawFinding {
  id?: string;
  lens?: string;
  severity?: string;
  title?: string;
  headline?: string;
  action?: string;
  metric_sql?: string; // returns ONE row whose value IS the headline number
  metric_format?: string;
  evidence_sql?: string; // returns the supporting detail rows (the evidence table)
}

/** A grounded finding — the model's lens, the data's numbers (computed by us). */
export interface Finding {
  id: string;
  lens: string;
  severity: Severity;
  title: string; // action-title assertion (becomes a slide title)
  headline: string; // one-sentence dashboard card
  action: string; // recommended move (deck recommendation)
  evidenceSql: string; // the query behind the supporting detail rows
  metricSql: string; // the scalar query that produced the headline number
  value: string; // formatted headline value — computed from the query, never typed
  rawValue: number;
  valueFormat: ValueFormat;
  rowCount: number;
  columns: string[];
  rows: Record<string, unknown>[];
  impactUsd: number; // $ impact for ranking (0 when the headline isn't money)
}

const SEVERITY_TIER: Record<Severity, number> = { critical: 0, warning: 1, opportunity: 2, info: 3 };

function usd(n: number): string {
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${Math.round(n)}`;
}

function formatValue(n: number, f: ValueFormat): string {
  switch (f) {
    case "usd":
      return usd(n);
    case "pct":
      return `${Math.round(n)}%`;
    case "int":
      return Math.round(n).toLocaleString("en-US");
    default:
      // raw — keep at most two decimals so averages don't print 16 digits.
      return String(Math.round(n * 100) / 100);
  }
}

/** The headline number, read from the metric query's single cell — never typed by the model. */
function scalarOf(res: { rows: Record<string, unknown>[] }): number | null {
  const row = res.rows[0];
  if (!row) return null;
  for (const v of Object.values(row)) {
    const n = Number(v);
    if (Number.isFinite(n)) return n;
  }
  return null;
}

const asSeverity = (s: unknown): Severity =>
  s === "critical" || s === "warning" || s === "opportunity" || s === "info" ? s : "info";
const asFormat = (s: unknown): ValueFormat =>
  s === "usd" || s === "pct" || s === "int" || s === "raw" ? s : "int";

function discoveryBrief(): string {
  const schema = schemaSnapshot()
    .map((t) => `  ${t.table}(${t.columns.map((c) => `${c.name} ${c.type}`).join(", ")})`)
    .join("\n");
  const clock = dataClock();
  return [
    "You are Veta's discovery analyst — a sharp B2B SaaS revenue & retention analyst doing a first review of a company's data warehouse.",
    "You do NOT know this specific company. Learn its story from the data itself.",
    "",
    "YOUR JOB: surface the few MATERIAL commercial stories an experienced operator would want flagged on a dashboard — the real risks and opportunities living in THIS data right now. The actual stories this dataset supports, not a generic checklist.",
    "",
    "HOW TO WORK:",
    "- Explore with query_warehouse (read-only SELECT/WITH). Look at the schema, distributions, segments, time trends, and outliers.",
    "- The lenses an analyst typically uses in this vertical are retention/renewal risk, customer sentiment, product adoption/usage, expansion/upsell, and revenue concentration — but let the DATA decide which actually apply, and at what cut points. Don't force a lens the data doesn't support; do surface a real story even if it's outside these lenses.",
    "- Choose thresholds from what the data shows (what 'low' utilisation or 'critical' health means HERE), not from assumptions.",
    "",
    "GROUNDING — non-negotiable. You never state a number yourself; you write queries and our code reads the result:",
    "- metric_sql: a query returning ONE row whose value IS the headline number (e.g. SELECT COUNT(*) AS v FROM vw_conta WHERE churn_rotulo = 1). Scope its WHERE/LIMIT to the EXACT set your headline describes — if the headline is about the top 5, the metric is over those 5; if about one product, filter to it. We run it and read the single value.",
    "- evidence_sql: a query returning the supporting detail rows (the named accounts/products/quarters) for an inspectable evidence table.",
    "- Rank by material $ impact.",
    `- "Today" is ${clock.today}; the data spans ${clock.firstDate} to ${clock.lastDate}.`,
    clock.partialMonth
      ? `- ${clock.partialMonth} is a PARTIAL, incomplete month — never read it as a real decline or trend.`
      : "- Every month in range is complete.",
    "",
    "OUTPUT: when done exploring, reply with ONLY a JSON object (no prose, no code fences):",
    '{ "findings": [ { "id", "lens", "severity", "title", "headline", "action", "metric_sql", "metric_format", "evidence_sql" } ] }',
    "- id: short slug. lens: 1-2 word MECE label (e.g. Concentration, Sentiment). severity: critical|warning|opportunity|info.",
    "- title: a full action-title assertion carrying the so-what (becomes a slide title).",
    "- headline: one sentence for a dashboard card; cite the metric_sql number itself (not a separately-remembered figure) so the card's number and sentence agree. action: the recommended next move.",
    "- metric_sql: the scalar query for the headline number. metric_format: usd | int | pct | raw.",
    "- evidence_sql: the SELECT/WITH returning the supporting rows.",
    "Return 3-6 findings, most material first. Both queries must run and return rows; the metric_sql number must match what the headline claims.",
    "",
    "WAREHOUSE SCHEMA:",
    schema,
  ].join("\n");
}

/** Pull the first balanced JSON object out of the model's final message. */
function extractJson(text: string): string | null {
  const start = text.indexOf("{");
  if (start === -1) return null;
  let depth = 0;
  let inStr = false;
  let esc = false;
  for (let i = start; i < text.length; i++) {
    const ch = text[i];
    if (inStr) {
      if (esc) esc = false;
      else if (ch === "\\") esc = true;
      else if (ch === '"') inStr = false;
    } else if (ch === '"') inStr = true;
    else if (ch === "{") depth++;
    else if (ch === "}") {
      depth--;
      if (depth === 0) return text.slice(start, i + 1);
    }
  }
  return null;
}

/** Run the discovery agent loop and return the raw findings the model proposed. */
async function runDiscoveryAgent(model: string, maxSteps: number): Promise<RawFinding[]> {
  const client = new OpenAI({ apiKey: process.env.LLM_API_KEY, baseURL: BASE_URL });
  const tools = DISCOVERY_TOOLS;

  const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
    { role: "system", content: discoveryBrief() },
    { role: "user", content: "Explore the warehouse and return the material findings as the specified JSON." },
  ];

  const dbg = process.env.DISCOVERY_DEBUG;
  let finalText = "";
  for (let step = 0; step < maxSteps; step++) {
    const res = await client.chat.completions.create({
      model,
      max_tokens: 8000,
      temperature: 0.2,
      messages,
      tools,
      tool_choice: "auto",
    });
    const msg = res.choices[0]?.message;
    if (!msg) break;
    const calls = msg.tool_calls ?? [];
    if (dbg) console.error(`[discovery] step ${step}: finish=${res.choices[0]?.finish_reason} toolCalls=${calls.length} contentLen=${(msg.content ?? "").length}`);
    messages.push({
      role: "assistant",
      content: msg.content ?? "",
      ...(calls.length > 0 ? { tool_calls: msg.tool_calls } : {}),
    });
    if (calls.length === 0) {
      finalText = (msg.content ?? "").trim();
      break;
    }
    for (const call of calls) {
      if (call.type !== "function") continue;
      let result: unknown;
      try {
        const input = call.function.arguments ? JSON.parse(call.function.arguments) : {};
        result = runDiscoveryTool(call.function.name, input);
      } catch (e) {
        result = { error: e instanceof Error ? e.message : String(e) };
      }
      messages.push({
        role: "tool",
        tool_call_id: call.id,
        content: JSON.stringify(result).slice(0, 60_000),
      });
    }
  }

  // If exploration ran out of steps without finalising, force the extraction: one
  // more turn with no tools, so the model must emit the findings JSON it gathered.
  if (!finalText) {
    if (dbg) console.error("[discovery] no natural finish — forcing extraction turn (no tools)");
    const finalRes = await client.chat.completions.create({
      model,
      max_tokens: 8000,
      temperature: 0.2,
      messages: [
        ...messages,
        {
          role: "user",
          content:
            "Stop exploring now. Based on everything you have queried, output ONLY the findings JSON object specified in your instructions — no prose, no code fences.",
        },
      ],
    });
    finalText = (finalRes.choices[0]?.message?.content ?? "").trim();
  }

  if (dbg) console.error(`[discovery] finalText length=${finalText.length}\n--- finalText head ---\n${finalText.slice(0, 1200)}\n--- end ---`);
  if (!finalText) return [];
  const json = extractJson(finalText);
  if (!json) {
    if (dbg) console.error("[discovery] extractJson found no JSON object in finalText");
    return [];
  }
  try {
    const parsed = JSON.parse(json) as { findings?: RawFinding[] };
    const raw = Array.isArray(parsed.findings) ? parsed.findings : [];
    if (dbg) console.error(`[discovery] parsed ${raw.length} raw findings`);
    return raw;
  } catch (e) {
    if (dbg) console.error("[discovery] JSON.parse failed:", e instanceof Error ? e.message : String(e));
    return [];
  }
}

/**
 * The grounding gate: re-run each proposed query, compute the headline number
 * from the real rows, and drop anything whose SQL fails or returns nothing.
 * This is what makes LLM-discovered findings as trustworthy as the hardcoded
 * detectors were — every number is code-computed from inspectable rows.
 */
function groundFindings(raw: RawFinding[]): Finding[] {
  const dbg = process.env.DISCOVERY_DEBUG;
  const grounded: Finding[] = [];
  for (const f of raw) {
    const evSql = (f.evidence_sql ?? "").trim();
    const mSql = (f.metric_sql ?? "").trim();
    const tag = f.id ?? f.lens ?? "?";
    if (!evSql || !mSql) {
      if (dbg) console.error(`[gate] drop "${tag}": missing metric_sql or evidence_sql`);
      continue;
    }

    let ev, mv;
    try {
      ev = runQuery(evSql);
    } catch (e) {
      if (dbg) console.error(`[gate] drop "${tag}": evidence_sql error: ${e instanceof Error ? e.message : String(e)}`);
      continue;
    }
    if (ev.rowCount === 0) {
      if (dbg) console.error(`[gate] drop "${tag}": evidence_sql returned 0 rows`);
      continue;
    }
    try {
      mv = runQuery(mSql);
    } catch (e) {
      if (dbg) console.error(`[gate] drop "${tag}": metric_sql error: ${e instanceof Error ? e.message : String(e)}`);
      continue;
    }
    const rawValue = scalarOf(mv);
    if (rawValue === null) {
      if (dbg) console.error(`[gate] drop "${tag}": metric_sql returned no numeric value`);
      continue;
    }

    const format = asFormat(f.metric_format);
    grounded.push({
      id: f.id?.toString().slice(0, 64) || `finding-${grounded.length + 1}`,
      lens: (f.lens ?? "Signal").toString().slice(0, 24),
      severity: asSeverity(f.severity),
      title: (f.title ?? f.headline ?? "Finding").toString(),
      headline: (f.headline ?? f.title ?? "").toString(),
      action: (f.action ?? "").toString(),
      evidenceSql: ev.sql,
      metricSql: mv.sql,
      value: formatValue(rawValue, format),
      rawValue,
      valueFormat: format,
      rowCount: ev.rowCount,
      columns: ev.columns,
      rows: ev.rows.slice(0, 25),
      impactUsd: format === "usd" ? Math.abs(rawValue) : 0,
    });
  }

  return grounded.sort(
    (a, b) => SEVERITY_TIER[a.severity] - SEVERITY_TIER[b.severity] || b.impactUsd - a.impactUsd || b.rowCount - a.rowCount,
  );
}

/** A cheap fingerprint of the connected dataset — changes when the data rotates. */
function datasetFingerprint(): string {
  const clock = dataClock();
  let counts = "";
  try {
    const r = runQuery(
      "SELECT (SELECT COUNT(*) FROM accounts) AS a, (SELECT COUNT(*) FROM feature_usage) AS u",
    );
    const row = (r.rows[0] ?? {}) as { a?: number; u?: number };
    counts = `${row.a ?? 0}:${row.u ?? 0}`;
  } catch {
    counts = "na";
  }
  return `${clock.firstDate}|${clock.lastDate}|${counts}`;
}

const inFlight = new Map<string, Promise<Finding[]>>();

/**
 * The findings for the connected dataset — cached per fingerprint so a warm cache
 * is instant; only a rotated dataset or `force` triggers a fresh LLM run.
 */
export async function discoverFindings(opts: { force?: boolean; model?: string; maxSteps?: number } = {}): Promise<Finding[]> {
  const fp = datasetFingerprint();
  const key = `findings:${fp}`;

  if (!opts.force) {
    const cached = getCache<Finding[]>(key);
    if (cached && cached.length > 0) return cached;
    const pending = inFlight.get(key);
    if (pending) return pending;
  } else {
    clearCache(key);
  }

  const run = (async () => {
    const raw = await runDiscoveryAgent(opts.model ?? DEFAULT_MODEL, opts.maxSteps ?? 12);
    const findings = groundFindings(raw);
    if (findings.length > 0) putCache(key, findings);
    return findings;
  })();

  inFlight.set(key, run);
  try {
    return await run;
  } finally {
    inFlight.delete(key);
  }
}

/** Force a fresh discovery pass (the "Re-analyze" control). */
export function reanalyzeFindings(): Promise<Finding[]> {
  return discoverFindings({ force: true });
}

/** Warm-cache read only — the findings already discovered for this dataset, or
 *  null if none yet. Synchronous (no LLM): lets the page server-render instantly
 *  when the cache is warm and fall back to a client-driven pass when it's cold. */
export function getCachedFindings(): Finding[] | null {
  const cached = getCache<Finding[]>(`findings:${datasetFingerprint()}`);
  return cached && cached.length > 0 ? cached : null;
}
