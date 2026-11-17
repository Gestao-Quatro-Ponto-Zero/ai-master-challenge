/**
 * Deck generation — the grounded executive deck, built as a Minto pyramid.
 *
 * Structure is deterministic; the DATA decides the content. The key arguments are
 * no longer a fixed set of detectors we authored — they are whatever the discovery
 * engine (discovery.ts) found in the connected data at runtime. The LLM picks the
 * lenses; our code grounds every number (each argument's headline value comes from
 * a query result, never the model). Rotate the dataset and the deck re-derives.
 *
 * The cover/context/recommendation scaffold uses portfolio aggregates (total ARR,
 * segment mix) — descriptive facts about the book, not inferred stories.
 *
 * One engine, two faces: exposed as the `generate_deck` tool (chat + MCP).
 */
import OpenAI from "openai";
import { runQuery } from "./warehouse";
import { METRICS } from "./metrics";
import { dataClock } from "./calendar";
import { mrrByPlan } from "./dashboard";
import { discoverFindings, type Finding } from "./discovery";
import { getCache, putCache, listCacheByPrefix, deleteCache, type SavedInsight } from "./appdb";
import { activeDatasetId } from "./datasets";
import type { ChartSpec } from "./tools"; // type-only — no runtime import cycle
import { applyTransform, coerceTablePayload, coerceTransform, type ArtifactTransform, type SlideLineage } from "./parts"; // the artifact-layer contract

const num = (v: unknown): number => Number(v ?? 0);
const usd = (n: number): string =>
  n >= 1e6 ? `$${(n / 1e6).toFixed(1)}M` : n >= 1e3 ? `$${(n / 1e3).toFixed(0)}K` : `$${n.toFixed(0)}`;

export type SlideLayout = "cover" | "context" | "divider" | "argument" | "recommendation";

export interface DeckChart {
  /** A bar/line approximation for the .pptx export face (pptxgenjs draws bar/line). */
  kind: "line" | "bar";
  title: string;
  categories: string[];
  series: { name: string; values: number[]; color?: string }[];
  /**
   * The TRUE re-grounded chart. When present, the in-app deck (SlideView) renders it
   * via the same ChartView the chat uses — so a pinned pie/scatter/radar/column/combo
   * draws its real shape on the slide, not the bar/line approximation. The .pptx face
   * still falls back to `kind`+`categories`+`series` (export never breaks on an exotic type).
   */
  spec?: ChartSpec;
}

export interface DeckTable {
  columns: string[];
  rows: (string | number)[][];
  /** column indices to right-align in mono (the numeric ones). */
  numericColumns: number[];
}

/** The grounding behind a slide's headline — value derived from SQL, never typed. */
export interface Evidence {
  label: string; // what the headline number measures
  value: string; // formatted headline value (computed from the query)
  rowCount: number; // rows behind it
  sql: string; // the cited, inspectable query
}

export interface Slide {
  layout: SlideLayout;
  title: string; // action title — a full so-what assertion
  subtitle?: string;
  sectionNumber?: string; // "01" on dividers
  body?: string[]; // narrative — carries no number absent from evidence
  chart?: DeckChart;
  table?: DeckTable;
  evidence?: Evidence;
  /** Artifact layer: trace back to the chat that produced this slide's pin. */
  lineage?: SlideLineage;
}

export interface DeckSpec {
  id: string;
  title: string;
  subtitle: string;
  asOf: string; // the dataset's "today" — the analysis is as of this date
  governingThought: string; // apex assertion
  scqa: { situation: string; complication: string; question: string };
  datasetFrame: { today: string; firstDate: string; lastDate: string };
  slides: Slide[];
  citedSql: string[]; // the full grounding trail (every distinct query behind the deck)
  /** Artifact layer: a built pin-deck starts as an editable draft; publishing
   *  freezes it. Absent (legacy decks) reads as published. Edits touch prose
   *  only — grounded material (evidence/chart/table/citedSql) is immutable. */
  status?: "draft" | "published";
}

/** A key argument — a grounded finding, ready to narrate as a slide. */
interface KeyArgument {
  id: string;
  lens: string;
  tier: number; // severity tier for ordering (0 = most severe)
  impactUsd: number; // ranking within a tier
  title: string; // action title with the live number
  body: string[];
  action: string; // the recommended move this argument implies
  evidence: Evidence;
  table?: DeckTable;
  citedSql: string[];
}

const SEV_TIER: Record<string, number> = { critical: 0, warning: 1, opportunity: 2, info: 3 };

// ── Finding → argument: shape a discovered finding into a deck slide ───────────

/** Light formatting for a raw evidence cell, by column name + value shape. */
function formatCell(col: string, v: unknown): string | number {
  if (v === null || v === undefined) return "";
  const n = Number(v);
  const numeric = typeof v === "number" || (typeof v === "string" && v.trim() !== "" && Number.isFinite(n));
  if (!numeric) return String(v).slice(0, 48);
  const c = col.toLowerCase();
  if (/(arr|amount|usd|mrr|revenue|acv|tcv)/.test(c) && Math.abs(n) >= 1000) return usd(n);
  if (/(pct|percent|rate|util)/.test(c)) return `${Math.round(n)}%`;
  return Number.isInteger(n) ? n : Math.round(n * 10) / 10;
}

/** A column is numeric if most of its raw values parse as finite numbers. */
function isNumericColumn(col: string, rows: Record<string, unknown>[]): boolean {
  let numericCount = 0;
  let total = 0;
  for (const r of rows) {
    const v = r[col];
    if (v === null || v === undefined || v === "") continue;
    total++;
    if (Number.isFinite(Number(v))) numericCount++;
  }
  return total > 0 && numericCount / total >= 0.6;
}

/** Build a readable evidence table from a finding's grounded rows. */
function findingTable(f: Finding): DeckTable | undefined {
  if (f.columns.length === 0 || f.rows.length === 0) return undefined;
  const cols = f.columns.slice(0, 6);
  const sample = f.rows.slice(0, 6);
  return {
    columns: cols.map((c) => c.replace(/_/g, " ")),
    rows: sample.map((r) => cols.map((c) => formatCell(c, r[c]))),
    numericColumns: cols.map((_, i) => i).filter((i) => isNumericColumn(cols[i], f.rows)),
  };
}

function findingToArgument(f: Finding): KeyArgument {
  return {
    id: f.id,
    lens: f.lens,
    tier: SEV_TIER[f.severity] ?? 3,
    impactUsd: f.impactUsd,
    title: f.title,
    body: f.headline ? [f.headline] : [],
    action: f.action || "Act on this finding.",
    evidence: { label: f.lens, value: f.value, rowCount: f.rowCount, sql: f.evidenceSql },
    table: findingTable(f),
    citedSql: [f.metricSql, f.evidenceSql],
  };
}

/** Quarter label for a YYYY-MM-DD date, e.g. "Q2 2026". */
function periodLabel(today: string): string {
  const [y, m] = today.split("-").map(Number);
  return `Q${Math.floor(((m || 1) - 1) / 3) + 1} ${y}`;
}

const pad2 = (n: number): string => String(n).padStart(2, "0");
const uniq = (xs: string[]): string[] => [...new Set(xs)];

/** Descriptive framing of the RavenStack base for cover/context slides (D20/D23). */
function baseFraming() {
  const portfolio = runQuery(METRICS.base_resumo.sql);
  const p = (portfolio.rows[0] ?? {}) as Record<string, number>;
  const seg = mrrByPlan();
  const mrrValue = num(p.mrr_sem_fim);
  const situation =
    `A RavenStack tem ${num(p.contas)} contas e ${num(p.assinaturas).toLocaleString("pt-BR")} assinaturas; ` +
    `as ${num(p.assinaturas_sem_fim).toLocaleString("pt-BR")} sem data de fim somam ${usd(mrrValue)} de MRR. ` +
    `${num(p.contas_com_evento)} contas tiveram evento de churn (${num(p.eventos_churn)} eventos).`;
  const contextTitle = `${num(p.contas)} contas, ${usd(mrrValue)} de MRR sem data de fim, ${num(p.contas_com_evento)} contas com evento de churn`;
  return { portfolio, seg, situation, contextTitle, mrrLabel: "MRR sem data de fim", mrrValue };
}

/**
 * Build the curated executive review — a grounded Minto pyramid over whatever the
 * discovery engine found. Arguments are the top findings (≤4, ranked by severity
 * then $ impact); if none fire, the deck says so honestly.
 */
export async function buildExecutiveReview(): Promise<DeckSpec> {
  const clock = dataClock();
  const period = periodLabel(clock.today);
  const title = `${period} Revenue & Retention Review`;

  const findings = await discoverFindings();
  const args = findings
    .slice()
    .sort((a, b) => (SEV_TIER[a.severity] ?? 3) - (SEV_TIER[b.severity] ?? 3) || b.impactUsd - a.impactUsd)
    .slice(0, 4)
    .map(findingToArgument);

  // Situation — size of the base (descriptive aggregates, D20/D23).
  const { portfolio, seg, situation, contextTitle, mrrLabel, mrrValue } = baseFraming();

  const top = args[0];
  const governingThought = top ? top.title : "Nenhum achado foi fundamentado nos dados.";

  const scqa = {
    situation,
    complication: top ? top.body[0] ?? top.title : "Nenhum achado foi fundamentado nos dados.",
    question: "O que está causando o churn, quais contas estão em risco e o que fazer?",
  };

  const slides: Slide[] = [];

  // 1 — Cover (governing thought as the hero).
  slides.push({ layout: "cover", title, subtitle: governingThought, evidence: top?.evidence });

  // 2 — Context (Situation → Complication → Question), grounded by the segment mix.
  slides.push({
    layout: "context",
    title: contextTitle,
    body: [scqa.situation, scqa.complication, scqa.question],
    chart: {
      kind: "bar",
      title: "MRR por plano (assinaturas sem data de fim)",
      categories: seg.data.map((d) => d.label),
      series: [{ name: "MRR", values: seg.data.map((d) => d.value), color: "#e3b341" }],
    },
    evidence: { label: mrrLabel, value: usd(mrrValue), rowCount: portfolio.rowCount, sql: portfolio.sql },
  });

  // 3..n — One section divider + one argument slide per discovered finding.
  args.forEach((a, i) => {
    slides.push({ layout: "divider", title: a.lens, sectionNumber: pad2(i + 1), subtitle: a.title });
    slides.push({ layout: "argument", title: a.title, body: a.body, table: a.table, evidence: a.evidence });
  });

  // Last — Recommended actions (only the moves the discovered findings imply).
  const actions = args.map((a) => a.action);
  slides.push({
    layout: "recommendation",
    title: "Recommended actions",
    body: actions.length > 0 ? actions : ["Maintain coverage; no urgent intervention indicated by the current data."],
  });

  const citedSql = uniq([portfolio.sql, seg.sql, ...args.flatMap((a) => a.citedSql)]);

  return {
    id: `exec-review-${clock.today}`,
    title,
    subtitle: `RavenStack · corte em ${clock.today}`,
    asOf: clock.today,
    governingThought,
    scqa,
    datasetFrame: { today: clock.today, firstDate: clock.firstDate, lastDate: clock.lastDate },
    slides,
    citedSql,
  };
}

// ════════════════════════════════════════════════════════════════════════════
// Phase 3 — the deck the user composes: a grounded Minto deck from PINNED insights.
//
// The exec review (above) is the autonomous, zero-pin default. This path is the
// human-curated one: the user pins grounded answers into the deck draft, then asks
// Veta to assemble them. Division of labour is the same grounding invariant the
// whole app runs on — the ARRANGER (an LLM) decides the narrative (apex, order,
// SCQA, action titles); OUR code re-runs each pin's cited SQL to fill every number.
// A pin whose SQL no longer grounds is dropped at the gate, exactly like a finding.
// The arranger never emits a figure: if the LLM is unreachable or returns garbage,
// a deterministic arrangement still produces a correct, grounded deck.
// ════════════════════════════════════════════════════════════════════════════

const ARRANGER_MODEL = process.env.LLM_MODEL ?? "deepseek-chat";
const ARRANGER_BASE_URL = process.env.LLM_BASE_URL ?? "https://api.deepseek.com";

/** Format a metric scalar by what its column name suggests it measures. */
function headlineValueFmt(col: string, n: number): string {
  const c = col.toLowerCase();
  if (/(arr|amount|usd|mrr|revenue|acv|tcv|exposure|expansion|spend|cost)/.test(c) && Math.abs(n) >= 1000) return usd(n);
  if (/(pct|percent|rate|util|share|ratio)/.test(c)) return `${Math.round(n)}%`;
  if (Number.isInteger(n)) return n.toLocaleString("en-US");
  return String(Math.round(n * 10) / 10);
}

interface RanQuery {
  sql: string;
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
}

// Column names that read as a headline metric (vs an id/dimension column).
const METRIC_NAME = /(arr|mrr|revenue|total|sum|amount|count|exposure|expansion|spend|cost|value|score|nps|seat|user|account|churn|risk|pct|percent|rate)/i;

/**
 * The headline number for a metric-shaped (single-row) result. Chat-cited queries
 * usually select several columns, so we pick the most headline-worthy numeric cell:
 * a metric-named column when present, else the largest-magnitude number. A query
 * with more than one row is a detail table, not a headline (returns null).
 */
function bestNumericCell(q: RanQuery): { col: string; value: number } | null {
  if (q.rows.length !== 1) return null;
  const row = q.rows[0];
  const numeric: { col: string; value: number }[] = [];
  for (const [col, v] of Object.entries(row)) {
    const n = Number(v);
    if (v !== null && v !== "" && Number.isFinite(n)) numeric.push({ col, value: n });
  }
  if (numeric.length === 0) return null;
  const named = numeric.filter((x) => METRIC_NAME.test(x.col));
  const pool = named.length > 0 ? named : numeric;
  return pool.slice().sort((a, b) => Math.abs(b.value) - Math.abs(a.value))[0];
}

/** Build a readable evidence table from raw grounded rows (≤6×6, numeric cols right-aligned). */
function buildTable(columns: string[], rows: Record<string, unknown>[]): DeckTable | undefined {
  if (columns.length === 0 || rows.length === 0) return undefined;
  const cols = columns.slice(0, 6);
  const sample = rows.slice(0, 6);
  return {
    columns: cols.map((c) => c.replace(/_/g, " ")),
    rows: sample.map((r) => cols.map((c) => formatCell(c, r[c]))),
    numericColumns: cols.map((_, i) => i).filter((i) => isNumericColumn(cols[i], rows)),
  };
}

/** A pin re-grounded against the live warehouse — headline value + evidence table, all from SQL. */
interface GroundedPin {
  pin: SavedInsight;
  evidence: Evidence;
  table?: DeckTable;
  chart?: DeckChart;
  citedSql: string[];
}

// The renderable chart types — mirrors CHART_TYPES in tools.ts (kept local to avoid a
// runtime import cycle: tools.ts imports buildExecutiveReview from this file).
const RENDERABLE_CHART_TYPES = ["bar", "column", "stacked", "line", "area", "pie", "donut", "scatter", "radar", "combo"] as const;
function isRenderableType(v: unknown): v is ChartSpec["type"] {
  return typeof v === "string" && (RENDERABLE_CHART_TYPES as readonly string[]).includes(v);
}
const CHART_PALETTE = ["#e3b341", "#8a90ad", "#5fb3a1", "#c98bdb"];

/**
 * Re-ground a pinned chart for the deck. If one of the pin's re-run queries still
 * carries the chart's x + y columns, rebuild from those FRESH rows — so a pinned chart
 * re-grounds like every other number on the slide. Otherwise fall back to the snapshot
 * stored at pin time (still grounded by its cited query, just not re-run). Returns the
 * TRUE re-grounded ChartSpec on `.spec` (any of the 10 types) for in-app rendering, plus
 * a bar/line approximation for the .pptx face. Undefined when the pin carried no chart.
 */
function chartFromPin(pin: SavedInsight, ran: RanQuery[]): DeckChart | undefined {
  let parsedSpec: ChartSpec | null = null;
  let transform: ArtifactTransform | undefined;
  try {
    const parsed = pin.chart_json ? (JSON.parse(pin.chart_json) as Partial<ChartSpec> & { transform?: unknown }) : null;
    if (parsed && isRenderableType(parsed.type) && typeof parsed.x === "string" && Array.isArray(parsed.y)) {
      parsedSpec = { type: parsed.type, title: typeof parsed.title === "string" ? parsed.title : "", x: parsed.x, y: parsed.y, data: Array.isArray(parsed.data) ? parsed.data : [] };
      transform = coerceTransform(parsed.transform);
    }
  } catch {
    parsedSpec = null;
  }
  if (!parsedSpec) return undefined;
  const spec = parsedSpec; // const-narrowed for use inside the callbacks below

  const yFields = spec.y.filter((f): f is string => typeof f === "string" && f.length > 0);
  if (yFields.length === 0) return undefined;

  // Prefer fresh rows from a re-run query that still carries the chart's columns.
  const fresh = ran.find((q) => q.columns.includes(spec.x) && yFields.every((f) => q.columns.includes(f)));
  const rows = fresh ? fresh.rows : spec.data;
  if (rows.length === 0) return undefined;

  const title = spec.title || yFields[0].replace(/_/g, " ");
  // Re-apply the user's displayed transform (type switch + sort) AFTER re-grounding:
  // fresh rows first, then their projection — freshness never erases the user's view.
  const projected = applyTransform({ type: spec.type, title, x: spec.x, y: yFields, data: rows }, transform);
  // line-like types degrade to a line in pptx; everything else to bars. The
  // approximation derives from the TRANSFORMED type, not the original spec's.
  const lineish = projected.type === "line" || projected.type === "area" || projected.type === "combo";
  return {
    kind: lineish ? "line" : "bar",
    title,
    categories: projected.data.map((r) => String(r[spec.x] ?? "")),
    series: yFields.slice(0, 4).map((f, i) => ({
      name: f.replace(/_/g, " "),
      values: projected.data.map((r) => num(r[f])),
      color: CHART_PALETTE[i % CHART_PALETTE.length],
    })),
    // the true re-grounded + re-projected chart — fresh rows when available.
    spec: projected,
  };
}

/**
 * Fresh-first table for a "table" part pin: rebuild from the re-run query that
 * still carries the pinned table's columns; only when every re-run misses them
 * fall back to the snapshot stored at pin time (mirrors the chart fallback).
 */
function tableFromPin(pin: SavedInsight, ran: RanQuery[]): DeckTable | undefined {
  let payload: ReturnType<typeof coerceTablePayload> = null;
  try {
    payload = pin.table_json ? coerceTablePayload(JSON.parse(pin.table_json)) : null;
  } catch {
    payload = null;
  }
  if (!payload) return undefined;
  const cols = payload.columns;
  const fresh = ran.find((q) => cols.every((c) => q.columns.includes(c)));
  // FRESH-ONLY (Cato 2026-07-04): a pinned table's cell snapshot may derive from
  // LLM-formatted answer prose (markdown-table pins). Putting that snapshot on a
  // slide would render ungrounded numbers as authoritative — the exact failure
  // this product exists to prevent. If no re-run query carries the pinned
  // columns, return undefined and let the caller fall back to the best RE-RUN
  // rows (grounded, possibly different columns) — honesty beats fidelity.
  return fresh ? buildTable(cols, fresh.rows) : undefined;
}

/**
 * The deck-time grounding gate for one pin: (1) the DATASET gate — a pin grounded
 * against a dataset that is not the builder's active one is dropped outright (its
 * SQL would run against the wrong warehouse and "ground" a lie); (2) re-run every
 * query the pin cited, drop the ones that error or return nothing, and read the
 * headline number from the rows — never from the pin's stored prose. Returns null
 * (pin dropped) if NOTHING re-grounds, so a stale pin can never put an
 * unverifiable number on a slide.
 */
function groundPin(pin: SavedInsight, activeDataset: string, userId?: string): GroundedPin | null {
  if (pin.dataset_id && pin.dataset_id !== activeDataset) return null; // the dataset gate
  let queries: string[] = [];
  try {
    const arr = JSON.parse(pin.cited_sql_json ?? "[]");
    if (Array.isArray(arr)) queries = arr.filter((s): s is string => typeof s === "string" && s.trim().length > 0);
  } catch {
    queries = [];
  }
  const ran: RanQuery[] = [];
  for (const sql of uniq(queries)) {
    try {
      // Re-run with the builder's warehouse context (Cato 2026-07-04): without it,
      // a pin grounded on the user's ACTIVE custom dataset would re-run against the
      // default RavenStack database — the dataset gate admitted it, so ground it there.
      const r = runQuery(sql, userId ? { userId } : undefined);
      if (r.rowCount > 0) ran.push({ sql: r.sql, columns: r.columns, rows: r.rows, rowCount: r.rowCount });
    } catch {
      /* a failed query is dropped — the pin survives on whichever of its queries still ground */
    }
  }
  if (ran.length === 0) return null; // the gate

  // Headline: prefer a metric-shaped (single-row) query and read its best numeric
  // cell from the rows; else fall back to the size of the richest result set.
  let evidence: Evidence | null = null;
  for (const q of ran) {
    const cell = bestNumericCell(q);
    if (cell) {
      evidence = { label: cell.col.replace(/_/g, " "), value: headlineValueFmt(cell.col, cell.value), rowCount: q.rowCount, sql: q.sql };
      break;
    }
  }
  const best = ran.slice().sort((a, b) => b.rows.length - a.rows.length || b.columns.length - a.columns.length)[0];
  if (!evidence) {
    evidence = { label: "rows", value: best.rowCount.toLocaleString("en-US"), rowCount: best.rowCount, sql: best.sql };
  }
  // Per-kind composition: a "chart" pin puts its chart (only) on the slide; a
  // "table" pin its pinned table, fresh-first; a "narrative" pin carries no visual
  // (the re-ground is its evidence); turn/finding keep the legacy chart+table pair.
  const kind = pin.source_kind;
  const table =
    kind === "table" ? (tableFromPin(pin, ran) ?? buildTable(best.columns, best.rows)) :
    kind === "chart" || kind === "narrative" ? undefined :
    buildTable(best.columns, best.rows);
  const chart = kind === "table" || kind === "narrative" ? undefined : chartFromPin(pin, ran);
  return { pin, evidence, table, chart, citedSql: ran.map((r) => r.sql) };
}

/** What the arranger proposes — narrative only; every number stays ours. */
interface Arrangement {
  title: string;
  governingThought: string;
  scqa: { situation: string; complication: string; question: string };
  order: { pinIndex: number; lens?: string; actionTitle: string; body: string[] }[];
  recommendations: string[];
}

/** Pull the first balanced JSON object out of the model's reply. */
function extractJsonObject(text: string): string | null {
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

const firstSentence = (s: string): string => {
  const t = s.trim().replace(/\s+/g, " ");
  const m = /^(.*?[.!?])(\s|$)/.exec(t);
  return (m ? m[1] : t).slice(0, 240);
};

/** 2–4 sentence lines from a narrative pin's answer — the pinned prose IS the slide body.
 *  The answer may carry markdown furniture (table rows, headers, bold markers); slides
 *  render plain text, so strip STRUCTURE before sentence-splitting — a table row is not
 *  a sentence, and a naive split inside "$26.7M" chops the number (seen live 2026-07-04). */
function narrativeLines(answer: string | null): string[] {
  const raw = (answer ?? "").trim();
  if (!raw) return [];
  const prose = raw
    .split("\n")
    .map((line) => line.trim().replace(/^[-•*]\s+/, "")) // keep bullet text, drop the marker
    .filter((t) => t.length > 0 && !t.startsWith("|") && !/^#{1,6}\s/.test(t) && !/^[-–—]{3,}$/.test(t))
    .join(" ")
    .replace(/\*\*([^*]*)\*\*/g, "$1")
    .replace(/[`*_]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  if (!prose) return [];
  // Split ONLY at punctuation followed by whitespace — decimals ($26.7M) stay whole.
  const sentences = prose.split(/(?<=[.!?])\s+/);
  return sentences.map((s) => s.trim()).filter((s) => s.length > 2).slice(0, 4).map((s) => s.slice(0, 240));
}

/** A short MECE-ish section label from an action title (deck divider). */
function deriveLens(actionTitle: string, fallback: string): string {
  const words = actionTitle.replace(/[^A-Za-z0-9 %$.,-]/g, "").split(/\s+/).filter(Boolean);
  const label = words.slice(0, 2).join(" ");
  return (label || fallback).slice(0, 28);
}

/**
 * Ask the arranger LLM to turn the grounded pins + the user's brief into a Minto
 * pyramid. It returns narrative only (apex, order, action titles, SCQA, actions);
 * we hand it each pin's already-computed grounded value so it never needs to state
 * a figure. Returns null on any failure — the caller falls back to deterministic.
 */
async function arrangeWithLLM(
  grounded: GroundedPin[],
  ctx: { situation: string; period: string },
  brief?: string,
): Promise<Arrangement | null> {
  if (!process.env.LLM_API_KEY) return null;
  const pinLines = grounded
    .map((g, i) => {
      const q = (g.pin.question ?? g.pin.title ?? "").toString().trim();
      const gist = firstSentence((g.pin.answer ?? "").toString());
      // Kind hint so the arranger titles each artifact sensibly (a narrative pin
      // is a qualitative assertion; a chart/table pin is a visual exhibit).
      const kindHint =
        g.pin.source_kind === "narrative" ? "narrative (prose insight — title it as a qualitative assertion)" :
        g.pin.source_kind === "chart" ? "chart (visual exhibit)" :
        g.pin.source_kind === "table" ? "table (visual exhibit)" : g.pin.source_kind;
      return `[${i}] title: ${g.pin.title ?? q}\n     kind: ${kindHint}\n     source question: ${q}\n     grounded value: ${g.evidence.value} (${g.evidence.label}, ${g.evidence.rowCount} rows)\n     gist: ${gist}`;
    })
    .join("\n");

  const sys = [
    "You are Veta's deck arranger — a McKinsey-trained analyst building a board-ready deck from a set of ALREADY-GROUNDED, pinned findings, using Minto's pyramid principle.",
    "",
    "GROUNDING — non-negotiable: you NEVER write a number that isn't one of the grounded values handed to you. Each pin's headline value was computed by our code from live SQL. Use a pin's grounded value verbatim, or speak qualitatively. Do not invent, recompute, round, or aggregate figures yourself. Body lines must carry NO number that isn't a pin's grounded value.",
    "",
    "YOUR JOB:",
    "- Synthesise ONE governing thought — the single conclusion the audience should walk away with (the pyramid's apex), supported by the pins below it.",
    "- Order the pins into a MECE argument, most material first.",
    "- For each pin you keep, write an action title — a full so-what assertion (it MAY cite that pin's grounded value).",
    "- You MAY drop or merge a pin that doesn't fit the story — a tight argument beats completeness. Omit a dropped pin's index.",
    "- Write the SCQA (situation / complication / question) framing the deck.",
    "- Write 2–4 concrete recommended actions.",
    "",
    brief ? `THE USER'S BRIEF (let it shape the apex, audience, and emphasis): "${brief}"` : "No brief given — let the pins themselves dictate the story.",
    "",
    `GROUNDED CONTEXT (use verbatim if you reference the book): ${ctx.situation}`,
    `PERIOD: ${ctx.period}.`,
    "",
    "THE PINNED FINDINGS:",
    pinLines,
    "",
    "OUTPUT — reply with ONLY this JSON object (no prose, no code fences):",
    '{ "title": "deck title", "governingThought": "the apex assertion", "scqa": { "situation": "", "complication": "", "question": "" }, "order": [ { "pinIndex": 0, "lens": "1-2 word section label", "actionTitle": "full so-what assertion", "body": ["qualitative line", "qualitative line"] } ], "recommendations": ["action", "action"] }',
    "- order references the [index] of each pin above; include only the pins you keep, in presentation order.",
    "- body: 1–2 short qualitative lines per slide; no number that isn't that pin's grounded value.",
  ].join("\n");

  try {
    const client = new OpenAI({ apiKey: process.env.LLM_API_KEY, baseURL: ARRANGER_BASE_URL });
    const res = await client.chat.completions.create({
      model: ARRANGER_MODEL,
      max_tokens: 4000,
      temperature: 0.3,
      messages: [
        { role: "system", content: sys },
        { role: "user", content: "Assemble the deck. Output only the JSON object." },
      ],
    });
    const text = (res.choices[0]?.message?.content ?? "").trim();
    const json = extractJsonObject(text);
    if (!json) return null;
    const parsed = JSON.parse(json) as Partial<Arrangement>;
    if (!parsed || typeof parsed !== "object") return null;
    if (!Array.isArray(parsed.order)) return null;
    return {
      title: typeof parsed.title === "string" ? parsed.title : "",
      governingThought: typeof parsed.governingThought === "string" ? parsed.governingThought : "",
      scqa: {
        situation: parsed.scqa?.situation ?? "",
        complication: parsed.scqa?.complication ?? "",
        question: parsed.scqa?.question ?? "",
      },
      order: parsed.order
        .filter((o): o is Arrangement["order"][number] => !!o && Number.isInteger(o.pinIndex))
        .map((o) => ({
          pinIndex: o.pinIndex,
          lens: typeof o.lens === "string" ? o.lens : undefined,
          actionTitle: typeof o.actionTitle === "string" ? o.actionTitle : "",
          body: Array.isArray(o.body) ? o.body.filter((b): b is string => typeof b === "string") : [],
        })),
      recommendations: Array.isArray(parsed.recommendations)
        ? parsed.recommendations.filter((r): r is string => typeof r === "string")
        : [],
    };
  } catch {
    return null;
  }
}

/** The always-works arrangement: pins in tray order, titles from the pins themselves. */
function deterministicArrangement(grounded: GroundedPin[], ctx: { situation: string }, brief?: string): Arrangement {
  const apex =
    grounded[0]?.pin.title?.toString() ||
    grounded[0]?.pin.question?.toString() ||
    "A grounded review of the pinned findings.";
  return {
    title: brief ? `Veta Review — ${firstSentence(brief).slice(0, 60)}` : "Veta — Custom Review",
    governingThought: apex,
    scqa: {
      situation: ctx.situation,
      complication: grounded[0]?.pin.answer ? firstSentence(grounded[0].pin.answer.toString()) : apex,
      question: brief ? firstSentence(brief) : "What do these pinned findings imply, and what should we do about them?",
    },
    order: grounded.map((g, i) => ({
      pinIndex: i,
      lens: undefined,
      actionTitle: (g.pin.title || g.pin.question || `Insight ${i + 1}`).toString(),
      body: g.pin.answer ? [firstSentence(g.pin.answer.toString())] : [],
    })),
    recommendations: ["Review each pinned finding with its owning team.", "Sequence action by exposure — highest first."],
  };
}

/**
 * Build a grounded Minto deck from a collection of pins (the deck draft). The
 * arranger picks the narrative; our code re-grounds every number. Pure + testable
 * — storage is the caller's job (see storeDeck).
 */
export async function buildDeckFromPins(opts: { pins: SavedInsight[]; userId: string; brief?: string; id?: string }): Promise<DeckSpec> {
  const clock = dataClock();
  const period = periodLabel(clock.today);
  const id = opts.id ?? `pins-${crypto.randomUUID()}`;

  // Re-ground every pin first — only survivors reach the arranger. The dataset
  // gate uses the BUILDER's active dataset: a pin grounded elsewhere is dropped.
  const active = activeDatasetId(opts.userId);
  const grounded = opts.pins.map((p) => groundPin(p, active, opts.userId)).filter((g): g is GroundedPin => g !== null);

  // Base framing — descriptive aggregates, grounded the same way as the exec review.
  const { portfolio, seg, situation, contextTitle, mrrLabel, mrrValue } = baseFraming();

  const baseFrame = {
    id,
    subtitle: `RavenStack · corte em ${clock.today}${opts.brief ? ` · ${firstSentence(opts.brief).slice(0, 80)}` : ""}`,
    asOf: clock.today,
    datasetFrame: { today: clock.today, firstDate: clock.firstDate, lastDate: clock.lastDate },
  };

  // No pin re-grounded — be honest rather than fabricate a story.
  if (grounded.length === 0) {
    const title = `${period} — Custom Review`;
    const gt = "The pinned insights could not be re-grounded against the current data — nothing to assert.";
    return {
      ...baseFrame,
      title,
      governingThought: gt,
      scqa: { situation, complication: "Each pinned query returned no rows when re-run against the live warehouse.", question: "Re-pin current findings, then rebuild." },
      slides: [
        { layout: "cover", title, subtitle: gt, evidence: { label: mrrLabel, value: usd(mrrValue), rowCount: portfolio.rowCount, sql: portfolio.sql } },
        { layout: "context", title: situation, body: [situation], evidence: { label: mrrLabel, value: usd(mrrValue), rowCount: portfolio.rowCount, sql: portfolio.sql } },
        { layout: "recommendation", title: "Recommended actions", body: ["Re-pin current grounded answers from chat or the insight feed, then rebuild the deck."] },
      ],
      citedSql: uniq([portfolio.sql, seg.sql]),
    };
  }

  const arrangement = (await arrangeWithLLM(grounded, { situation, period }, opts.brief)) ?? deterministicArrangement(grounded, { situation }, opts.brief);

  // Validate the proposed order against the grounded set; empty/all-invalid → every pin, in tray order.
  const seen = new Set<number>();
  const order = arrangement.order
    .filter((o) => o.pinIndex >= 0 && o.pinIndex < grounded.length && !seen.has(o.pinIndex) && (seen.add(o.pinIndex), true));
  const usedOrder =
    order.length > 0
      ? order
      : grounded.map((g, i) => ({ pinIndex: i, lens: undefined, actionTitle: (g.pin.title || g.pin.question || `Insight ${i + 1}`).toString(), body: [] as string[] }));

  const firstArg = usedOrder[0];
  const firstGrounded = grounded[firstArg.pinIndex];
  const governingThought = arrangement.governingThought.trim() || firstArg.actionTitle || "A grounded review of the pinned findings.";
  const title = arrangement.title.trim() || `${period} — Custom Review`;

  const scqa = {
    situation, // always our grounded portfolio sentence — never a model rewrite of the numbers
    complication: arrangement.scqa.complication.trim() || firstArg.actionTitle || governingThought,
    question: arrangement.scqa.question.trim() || "What do these pinned findings imply, and what should we do about them?",
  };

  const slides: Slide[] = [];

  // 1 — Cover (governing thought as the hero), grounded by the lead pin's evidence.
  slides.push({ layout: "cover", title, subtitle: governingThought, evidence: firstGrounded.evidence });

  // 2 — Context (SCQA), grounded by the portfolio segment mix.
  slides.push({
    layout: "context",
    title: contextTitle,
    body: [scqa.situation, scqa.complication, scqa.question],
    chart: {
      kind: "bar",
      title: "MRR por plano (assinaturas sem data de fim)",
      categories: seg.data.map((d) => d.label),
      series: [{ name: "MRR", values: seg.data.map((d) => d.value), color: "#e3b341" }],
    },
    evidence: { label: mrrLabel, value: usd(mrrValue), rowCount: portfolio.rowCount, sql: portfolio.sql },
  });

  // 3..n — One divider + one argument slide per kept pin; every number is re-grounded.
  // Composition follows the pin's kind (chart-only / table-only / prose-only is
  // already decided at groundPin); a narrative pin's body is the USER's pinned
  // prose (2–4 sentences), not the arranger's — the pin IS the prose artifact.
  usedOrder.forEach((o, k) => {
    const g = grounded[o.pinIndex];
    const actionTitle = o.actionTitle.trim() || (g.pin.title || g.pin.question || `Insight ${k + 1}`).toString();
    const lens = (o.lens?.trim() || deriveLens(actionTitle, `Insight ${k + 1}`)).slice(0, 28);
    const body = g.pin.source_kind === "narrative" ? narrativeLines(g.pin.answer) : o.body;
    slides.push({ layout: "divider", title: lens, sectionNumber: pad2(k + 1), subtitle: actionTitle });
    slides.push({
      layout: "argument",
      title: actionTitle,
      body: body.length > 0 ? body : o.body,
      chart: g.chart,
      table: g.table,
      evidence: g.evidence,
      lineage: { conversationId: g.pin.conversation_id, question: g.pin.question, citedSql: g.citedSql },
    });
  });

  // Last — Recommended actions.
  const recs = arrangement.recommendations.map((r) => r.trim()).filter(Boolean);
  slides.push({
    layout: "recommendation",
    title: "Recommended actions",
    body: recs.length > 0 ? recs : ["Review each pinned finding with its owning team; sequence by exposure."],
  });

  const citedSql = uniq([portfolio.sql, seg.sql, ...usedOrder.flatMap((o) => grounded[o.pinIndex].citedSql)]);

  return { ...baseFrame, title, governingThought, scqa, slides, citedSql };
}

// ── Stored decks: a built pin-deck is a frozen, shareable snapshot ─────────────
// The exec review rebuilds live (deterministic + cheap). A pin-deck is assembled
// once from the draft (an LLM call + the user's brief), so we persist the built
// DeckSpec under its id and the deck page / pptx route resolve it by id. Every
// number still carries its cited SQL, so a stored deck stays fully traceable.

const DECK_CACHE_PREFIX = "deck:";

/** Persist a built deck so /deck/{id} and its .pptx resolve to the same snapshot. */
function deckKey(userId: string, id: string): string {
  return `${DECK_CACHE_PREFIX}${userId}:${id}`;
}

export function storeDeck(userId: string, spec: DeckSpec): void {
  putCache(deckKey(userId, spec.id), spec);
}

/** Load a previously built+stored deck by id, or null if unknown. */
export function getStoredDeck(userId: string, id: string): DeckSpec | null {
  return getCache<DeckSpec>(deckKey(userId, id));
}

/** A library-card view of a stored deck — enough to list it without loading every slide. */
export interface DeckSummary {
  id: string;
  title: string;
  governingThought: string;
  slideCount: number;
  citedCount: number; // # of distinct cited queries (the lineage trail)
  asOf: string; // the dataset clock the deck was grounded against
  builtAt: string; // when the deck was assembled (kv_cache created_at)
}

/**
 * The Deck Library: every built (pin-)deck that persisted, newest first. The
 * autonomous exec review is NOT here — it rebuilds live from current data, so it
 * has no stored snapshot. A malformed row is skipped rather than breaking the list.
 */
export function listStoredDecks(userId: string): DeckSummary[] {
  const out: DeckSummary[] = [];
  for (const row of listCacheByPrefix(`${DECK_CACHE_PREFIX}${userId}:`)) {
    let spec: DeckSpec;
    try {
      spec = JSON.parse(row.value) as DeckSpec;
    } catch {
      continue;
    }
    if (!spec || typeof spec.id !== "string" || !Array.isArray(spec.slides)) continue;
    out.push({
      id: spec.id,
      title: spec.title || "Untitled deck",
      governingThought: spec.governingThought || "",
      slideCount: spec.slides.length,
      citedCount: Array.isArray(spec.citedSql) ? spec.citedSql.length : 0,
      asOf: spec.asOf || "",
      builtAt: row.created_at,
    });
  }
  return out;
}

/** Remove a stored deck from the library. Returns true if one was deleted. */
export function deleteStoredDeck(userId: string, id: string): boolean {
  return deleteCache(deckKey(userId, id));
}
