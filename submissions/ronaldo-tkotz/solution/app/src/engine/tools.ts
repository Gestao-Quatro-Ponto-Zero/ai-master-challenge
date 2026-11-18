/**
 * The tool layer — the single spine of the engine.
 *
 * One engine, two faces: the chat analyst agent (src/engine/agent.ts) and the
 * MCP server (src/mcp/server.ts) both consume THIS list. A capability is a tool,
 * added once here, and both faces get it. Never let them diverge.
 */
import { runQuery, schemaSnapshot, type QueryResult, type WarehouseContext } from "./warehouse";
import { METRICS, listMetrics } from "./metrics";
import { buildExecutiveReview } from "./deck";

export interface EngineTool {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, unknown>;
    required?: string[];
    additionalProperties?: boolean;
  };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  handler: (input: any, ctx?: WarehouseContext) => unknown | Promise<unknown>;
}

/**
 * The chart vocabulary lives in parts.ts (its canonical, CLIENT-SAFE home —
 * parts.ts is bundled into browser components, so it can't depend on this
 * server-tangled module). Re-exported here so every server-side importer of
 * tools.ts keeps working unchanged (the grounded-honesty rule from ISC-15.7:
 * the make_chart enum can never offer a shape ChartView can't draw).
 */
export { CHART_TYPES, isChartType } from "./parts";
export type { ChartType, ChartSpec } from "./parts";
import { CHART_TYPES, isChartType, type ChartSpec } from "./parts";

export const tools: EngineTool[] = [
  {
    name: "query_warehouse",
    description:
      "Run a single read-only SQL query (SELECT or WITH only) against the RavenStack database (tables and views) and get the rows back. " +
      "This is how you ground every factual claim — never state a number you did not get from a query. " +
      "Returns the exact SQL, the column names, the rows, and the total row count.",
    inputSchema: {
      type: "object",
      properties: {
        sql: {
          type: "string",
          description: "A single read-only SELECT or WITH query. No writes, no DDL, no multiple statements.",
        },
      },
      required: ["sql"],
      additionalProperties: false,
    },
    handler: ({ sql }: { sql: string }, ctx?: WarehouseContext): QueryResult => runQuery(sql, ctx),
  },
  {
    name: "list_metrics",
    description:
      "List the vetted, named metrics available (monthly churn, churn reasons, MRR by plan, ticket satisfaction, usage by month, data-quality alerts, etc.). " +
      "Prefer running a named metric over hand-writing SQL when one matches the question.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    handler: () => listMetrics().map((m) => ({ id: m.id, title: m.title, description: m.description })),
  },
  {
    name: "run_metric",
    description: "Run one of the vetted named metrics by id (see list_metrics) and get its grounded rows back.",
    inputSchema: {
      type: "object",
      properties: { id: { type: "string", description: "The metric id, e.g. 'churn_mensal'." } },
      required: ["id"],
      additionalProperties: false,
    },
    handler: ({ id }: { id: string }, ctx?: WarehouseContext) => {
      const metric = METRICS[id];
      if (!metric) {
        throw new Error(`Unknown metric '${id}'. Call list_metrics for valid ids.`);
      }
      return { metric: id, ...runQuery(metric.sql, ctx) };
    },
  },
  {
    name: "make_chart",
    description:
      "Render a chart inline beside your answer from rows you already queried. Call this whenever the user asks for a " +
      "chart (honour the type they name), or when a figure is naturally visual. Pass the exact rows from your query " +
      "result as `data` (never invent rows). `x` is the category/axis column; `y` lists the numeric column(s). " +
      "Pick the type that fits the shape:\n" +
      "• bar — compare a value across categories (horizontal bars, good for long labels).\n" +
      "• column — compare a value across categories as vertical bars; pass several y columns for grouped columns.\n" +
      "• stacked — show composition: several y columns stacked into one bar per category (parts summing to a whole over categories).\n" +
      "• line — a trend over time / ordered x; pass several y columns for multiple lines.\n" +
      "• area — a cumulative or volume trend over time.\n" +
      "• pie / donut — parts of a single whole (one y value per category, a handful of categories that sum to 100%).\n" +
      "• scatter — correlation between TWO numeric columns (x numeric, y[0] numeric; one point per row).\n" +
      "• radar — profile one or more entities across several axes (x = the axis labels, each y = one entity's series).\n" +
      "• combo — a value and a rate together: y[0] renders as bars, y[1] as a line on a secondary axis.",
    inputSchema: {
      type: "object",
      properties: {
        type: {
          type: "string",
          enum: [...CHART_TYPES],
          description: "Chart type: bar | column | stacked | line | area | pie | donut | scatter | radar | combo.",
        },
        title: { type: "string", description: "Short chart title." },
        x: { type: "string", description: "Column name for the x-axis / category / scatter-x." },
        y: {
          type: "array",
          items: { type: "string" },
          description: "Numeric column(s) to plot. One for bar/pie/scatter; several for grouped/stacked/radar/line; exactly two for combo (bars, then line).",
        },
        data: { type: "array", items: { type: "object" }, description: "The exact rows to plot (from your query result)." },
      },
      required: ["type", "x", "y", "data"],
      additionalProperties: false,
    },
    handler: (spec: { type: unknown; title?: string; x: string; y?: string[]; data?: unknown[] }): { chart: ChartSpec } => ({
      chart: {
        type: isChartType(spec.type) ? spec.type : "bar",
        title: spec.title ?? "",
        x: spec.x,
        y: Array.isArray(spec.y) ? spec.y : [],
        data: Array.isArray(spec.data) ? (spec.data as Record<string, unknown>[]) : [],
      },
    }),
  },
  {
    name: "describe_schema",
    description: "Return the database schema (every table and view with its column names and types).",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    handler: (_input: unknown, ctx?: WarehouseContext) => schemaSnapshot(ctx),
  },
  {
    name: "generate_deck",
    description:
      "Generate a grounded executive deck as a Minto pyramid over the warehouse: a governing thought, " +
      "the commercial arguments the DATA actually supports (each with its evidence table/chart and the SQL behind it), " +
      "and recommended actions. The number of arguments reflects what the data backs — nothing is invented. " +
      "Returns a DeckSpec the app renders as an in-browser deck and a downloadable .pptx.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    handler: () => buildExecutiveReview(),
  },
];

export const toolByName: Record<string, EngineTool> = Object.fromEntries(tools.map((t) => [t.name, t]));

/** OpenAI-compatible tool definition (function-calling shape). */
export interface OpenAIToolDef {
  type: "function";
  function: {
    name: string;
    description: string;
    parameters: EngineTool["inputSchema"];
  };
}

/** The tool list shaped for the OpenAI-compatible Chat Completions API (chat face).
 *  Works with any OpenAI-compatible provider — DeepSeek, OpenRouter, Together, local. */
export function openaiToolDefs(): OpenAIToolDef[] {
  return tools.map((t) => ({
    type: "function" as const,
    function: { name: t.name, description: t.description, parameters: t.inputSchema },
  }));
}
