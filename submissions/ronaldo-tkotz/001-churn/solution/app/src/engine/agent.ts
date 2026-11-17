/**
 * The analyst agent — a grounded, OpenAI-compatible tool-use loop.
 *
 * Manual loop (not an SDK runner) so we capture every tool call and the exact
 * SQL behind every answer for citation. Loops until the model stops asking for
 * tools, echoing the full assistant message back each turn (preserves order).
 *
 * Provider-agnostic: any OpenAI-compatible endpoint works (DeepSeek by default,
 * or OpenRouter / Together / Fireworks / a local server) via LLM_BASE_URL +
 * LLM_MODEL. The warehouse and tool layer never change — only the narrator does.
 */
import OpenAI from "openai";
import { openaiToolDefs, toolByName, type ChartSpec } from "./tools";
import { schemaSnapshot, type WarehouseContext } from "./warehouse";
import { dataClock, hasClock } from "./calendar";
import { activeDataset } from "./datasets";

const DEFAULT_MODEL = process.env.LLM_MODEL ?? "deepseek-chat";
const BASE_URL = process.env.LLM_BASE_URL ?? "https://api.deepseek.com";

export interface ToolCallTrace {
  name: string;
  input: unknown;
  result: unknown;
  isError: boolean;
}

/** A single grounded step, streamed to the UI as the loop runs. */
export interface AgentStep {
  index: number;
  tool: string;
  sql?: string;
  rowCount?: number;
  columns?: string[];
  rows?: Record<string, unknown>[];
  chart?: ChartSpec;
  isError: boolean;
}

export interface AgentResult {
  answer: string;
  model: string;
  steps: number;
  toolCalls: ToolCallTrace[];
  citedSql: string[];
  stopReason: string | null;
}

/**
 * Scrub leaked tool-call markup out of a narrative answer.
 *
 * DeepSeek (and other OpenAI-compatible providers) sometimes emit a function call in
 * the CONTENT channel instead of `tool_calls` — it surfaces as raw markup in the prose
 * ("<｜tool▁calls▁begin｜>…", "<invoke name=\"make_chart\">…", rendered on screen as the
 * mangled "< | | DSML | | invoke …>"). The model always writes these AFTER its prose, so
 * we truncate at the first tool-call marker, then belt-and-suspenders strip any residue.
 * If the whole content was a leaked call the answer goes empty and the forced-composition
 * fallback (tool_choice:"none") re-narrates from the grounded rows.
 */
export function sanitizeNarrative(text: string): string {
  if (!text) return "";
  const markers: RegExp[] = [
    /<｜/, // DeepSeek full-width-pipe token  <｜…｜>
    /<\|/, // ascii-degraded form  <|…|>
    /<invoke\b/i,
    /<\/?tool[_▁]?calls?\b/i,
    /<function[=\s>]/i,
    /<parameter\b/i,
  ];
  let cut = text.length;
  for (const m of markers) {
    const idx = text.search(m);
    if (idx >= 0 && idx < cut) cut = idx;
  }
  return text
    .slice(0, cut)
    .replace(/<｜[^\n]*?｜>/g, "")
    .replace(/<\/?(?:invoke|parameter|tool[_▁]?calls?|function)[^>]*>/gi, "")
    .trim();
}

/** Pull the grounded, renderable shape out of a tool result (query/metric). */
function toStep(index: number, name: string, result: unknown, isError: boolean): AgentStep {
  const r = (result ?? {}) as {
    sql?: string;
    rowCount?: number;
    columns?: string[];
    rows?: Record<string, unknown>[];
    chart?: ChartSpec;
  };
  return {
    index,
    tool: name,
    isError,
    sql: r.sql,
    rowCount: r.rowCount,
    columns: r.columns,
    rows: Array.isArray(r.rows) ? r.rows.slice(0, 50) : undefined,
    chart: r.chart,
  };
}

const CHART_LINES = [
  "CHARTS:",
  "- When the user asks for a chart, or when a figure is naturally visual (a trend over time, a comparison across categories), call make_chart with the exact rows you queried — it renders inline beside your answer.",
  "- Honour the chart type the user names. You can render: bar, column, stacked, line, area, pie, donut, scatter, radar, combo. If they ask for a 'pie', 'scatter', 'radar', 'column', 'stacked', or 'combo' chart, use exactly that type.",
  "- When the user doesn't name a type, pick the one that fits the shape: pie/donut for parts of a single whole, column/bar to compare a value across categories, stacked for composition, line/area for a trend over time, scatter for the correlation between two numeric columns, radar to profile an entity across several axes, combo for a value plus a rate (bars + line).",
  "- Always query the numbers first; make_chart only visualises rows you already grounded this turn. Never plot a number that isn't in a query result.",
  "- Keep the plotted set small: a chart reads best with at most ~40 rows. If a result has more (e.g. one row per account), write a query that aggregates or takes the top N (ORDER BY … LIMIT) for the chart, and pass only those rows as `data`. Never echo hundreds of rows into make_chart.",
];

function buildSystem(ctx: WarehouseContext = {}): string {
  const schema = schemaSnapshot(ctx)
    .map((t) => `  ${t.table}(${t.columns.map((c) => c.name).join(", ")})`)
    .join("\n");
  const clock = dataClock(ctx);
  const active = ctx.userId ? activeDataset(ctx.userId) : { is_default: 1, label: "RavenStack" };

  // The built-in RavenStack database — the framing the metrics + prompts are tuned for.
  if (active.is_default === 1) {
    return [
      "You are Veta, a data analyst for RavenStack, a B2B SaaS company (synthetic dataset). The CEO says churn went up, CS says satisfaction is fine, Product says usage grew — the numbers do not add up.",
      "ALWAYS answer in Brazilian Portuguese.",
      "",
      "GROUNDING — non-negotiable:",
      "- Every figure you state MUST come from a query_warehouse or run_metric result this turn. Never invent, estimate, or recall a number.",
      "- Prefer run_metric when a vetted metric matches the question (list_metrics shows them); use query_warehouse for the rest.",
      "- Lead with the answer, then the evidence. Be concise and specific — name accounts (account_id) and dollar figures.",
      "- Separate correlation from causation: describe what the data shows; never claim a cause the data cannot prove.",
      "- NEVER paste raw SQL, code blocks, or backticks into your written answer. The exact query behind every figure is already shown to the user as inspectable evidence beside your answer.",
      `- The analysis window runs from ${clock.firstDate} to the cutoff ${clock.lastDate} (table parametros). Every month in it is complete.`,
      "",
      "DEFINITIONS — decided by the human (process-log/decisions.md); follow them exactly:",
      "- Churn = a row in churn_events (D20). accounts.churn_flag and subscriptions.end_date/churn_flag are NOT the churn definition; use them only to reconcile.",
      "- Headline unit = accounts with at least one churn event; volume over time = events. Always label which one (D21).",
      "- Every number names the table it comes from (D29): accounts, churn_events, subscriptions, support_tickets or feature_usage. Never say \"accounts with churn\" without the source: 352 accounts have a row in churn_events (600 events), while accounts.churn_flag = 1 marks 110 accounts and 486 subscriptions have an end_date (in 312 accounts). When a number crosses tables (e.g. MRR of subscriptions of accounts with an event), name both.",
      "- Every event counts, in its own month, including repeated events and reactivations. Counting accounts, an account counts once per month with an event (D21).",
      "- An account is ACTIVE in a month when it has at least one subscription with start_date <= end of month and end_date NULL or >= start of month (D21). vw_mes already implements this.",
      "- Each number stays on the identifier it belongs to (D23): churn events, tickets, refund and reactivation are ACCOUNT-level (account_id); MRR, ARR, plan, billing, trial and usage are SUBSCRIPTION-level (subscription_id). MRR/ARR reach an account only as the total of that account's own subscriptions (vw_conta). Never attribute a subscription's MRR to a churn event.",
      "- Data-quality alerts (table dq_checks, severity 'alerta') stay in the analysis by default; when excluding the affected records changes a result, show BOTH numbers (D21). Known alerts: usage dated outside its own subscription period (T06), tickets opened before the account signup (T08), 825 of 2,000 tickets without satisfaction score.",
      "",
      "HOW TO QUERY:",
      "- Every date is TEXT in the format 'YYYY-MM-DD HH:MM:SS' (dates without time were stored as 00:00:00). Filter a year or month with substr(col,1,4) = '2024' or substr(col,1,7) = '2024-12', or with col < 'next day 00:00:00'. NEVER compare with a bare 'YYYY-MM-DD' upper bound: col <= '2024-12-31' silently drops every row dated '2024-12-31 00:00:00'.",
      "- NEVER do arithmetic in your answer (sums, differences, percentages, shares). Every total, difference or percentage you state must be computed in SQL (SUM, COUNT, ROUND) and read from a query result.",
      "- Prefer the views: vw_conta (one row per account, all five tables aggregated), vw_assinatura (one row per subscription), vw_mes (one row per month), vw_uso_detalhe / vw_ticket_detalhe / vw_churn_detalhe (detail rows enriched with account attributes).",
      "- Never join subscriptions directly with tickets or churn_events on account_id — it multiplies rows. Aggregate the child table to the account first (or use vw_conta).",
      "",
      ...CHART_LINES,
      "",
      "DATABASE SCHEMA (tables and views):",
      schema,
    ].join("\n");
  }

  // An uploaded warehouse the engine has never seen — generic grounded analyst.
  const timeLine = hasClock(clock)
    ? `- "Today" is ${clock.today}. The data spans ${clock.firstDate} to ${clock.lastDate}.`
    : "- This dataset has no detected time frame; infer temporal context from the data itself (look for date columns).";
  return [
    `You are Veta, a sharp data analyst connected to an uploaded dataset ("${active.label}") you have not seen before.`,
    "",
    "GROUNDING — non-negotiable:",
    "- Call describe_schema first to learn the tables and columns, then write SQL grounded in what you find.",
    "- Every figure you state MUST come from a query_warehouse result this turn. Never invent, estimate, or recall a number.",
    "- The prebuilt metrics (run_metric) are tuned for a different dataset — don't rely on them here; use query_warehouse.",
    "- Lead with the answer, then the evidence. Be concise and specific.",
    "- NEVER paste raw SQL, code blocks, or backticks into your written answer. The exact query behind every figure is shown to the user as inspectable evidence beside your answer. Write in plain business English only.",
    timeLine,
    "",
    ...CHART_LINES,
    "",
    "WAREHOUSE SCHEMA:",
    schema,
  ].join("\n");
}

/** Ask the analyst a question. Requires LLM_API_KEY (DeepSeek by default). */
export async function ask(
  question: string,
  opts: { model?: string; maxSteps?: number; userId?: string; onStep?: (step: AgentStep) => void } = {},
): Promise<AgentResult> {
  const client = new OpenAI({ apiKey: process.env.LLM_API_KEY, baseURL: BASE_URL });
  const model = opts.model ?? DEFAULT_MODEL;
  const maxSteps = opts.maxSteps ?? 10;

  const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
    { role: "system", content: buildSystem(opts.userId ? { userId: opts.userId } : {}) },
    { role: "user", content: question },
  ];
  const tools = openaiToolDefs() as OpenAI.Chat.Completions.ChatCompletionTool[];
  const toolCalls: ToolCallTrace[] = [];
  const citedSql: string[] = [];
  let answer = "";
  let stopReason: string | null = null;
  let modelCalls = 0;

  for (let step = 0; step < maxSteps; step++) {
    const res = await client.chat.completions.create({
      model,
      max_tokens: 8000,
      messages,
      tools,
      tool_choice: "auto",
    });
    modelCalls++;
    const choice = res.choices[0];
    stopReason = choice?.finish_reason ?? null;
    const msg = choice?.message;
    if (!msg) break;

    // Echo the assistant turn back (carries any tool_calls the model wants run).
    messages.push({
      role: "assistant",
      content: msg.content ?? "",
      ...(msg.tool_calls && msg.tool_calls.length > 0 ? { tool_calls: msg.tool_calls } : {}),
    });

    const calls = msg.tool_calls ?? [];
    if (calls.length === 0) {
      answer = sanitizeNarrative(msg.content ?? "");
      break;
    }

    for (const call of calls) {
      if (call.type !== "function") continue;
      const name = call.function.name;
      const tool = toolByName[name];
      let input: unknown = {};
      let result: unknown;
      let isError = false;
      try {
        input = call.function.arguments ? JSON.parse(call.function.arguments) : {};
        if (!tool) throw new Error(`unknown tool: ${name}`);
        result = await tool.handler(input, opts.userId ? { userId: opts.userId } : {});
      } catch (e) {
        isError = true;
        result = { error: e instanceof Error ? e.message : String(e) };
      }
      toolCalls.push({ name, input, result, isError });
      opts.onStep?.(toStep(toolCalls.length - 1, name, result, isError));
      if (!isError && (name === "query_warehouse" || name === "run_metric")) {
        const sql = (result as { sql?: string }).sql;
        if (sql) citedSql.push(sql);
      }
      messages.push({
        role: "tool",
        tool_call_id: call.id,
        content: JSON.stringify(result).slice(0, 100_000),
      });
    }
  }

  // A complex question can exhaust the step budget with evidence gathered but
  // no prose composed — the loop above only sets `answer` when the model stops
  // calling tools on its own. One final tool-less call turns "ran out of steps"
  // from an EMPTY answer into a grounded one: the query results are already in
  // the transcript, and with tool_choice:"none" the model may only narrate them.
  if (!answer && toolCalls.length > 0) {
    const res = await client.chat.completions.create({
      model,
      max_tokens: 8000,
      messages: [
        ...messages,
        {
          role: "user",
          content:
            "Step budget reached — compose your final answer NOW from the query results above. " +
            "Cite only numbers present in those results. If something material is still unqueried, name it in one closing line.",
        },
      ],
      tools,
      tool_choice: "none",
    });
    modelCalls++;
    answer = sanitizeNarrative(res.choices[0]?.message?.content ?? "");
    stopReason = res.choices[0]?.finish_reason ?? stopReason;
  }

  return { answer, model, steps: modelCalls, toolCalls, citedSql, stopReason };
}
