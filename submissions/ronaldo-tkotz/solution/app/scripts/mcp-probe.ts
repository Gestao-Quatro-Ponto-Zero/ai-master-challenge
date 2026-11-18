import { dirname, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { CallToolResultSchema, type CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { tools } from "../src/engine/tools";

interface ProbeQueryResult {
  rows: Array<Record<string, unknown>>;
  rowCount: number;
}

const CLIENT_INFO = { name: "veta-mcp-probe", version: "0.1.0" } as const;
const PROJECT_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
type ProbeToolResponse = Awaited<ReturnType<Client["callTool"]>>;

function pass(message: string): void {
  process.stdout.write(`✓ ${message}\n`);
}

function fail(message: string): void {
  process.stdout.write(`✗ ${message}\n`);
}

function toCallToolResult(result: ProbeToolResponse): CallToolResult {
  if (!("content" in result)) {
    throw new Error("Tool call returned a legacy payload without content blocks.");
  }

  return result as CallToolResult;
}

function getTextContent(result: ProbeToolResponse): string {
  const textBlock = toCallToolResult(result).content.find((block) => block.type === "text");

  if (!textBlock || textBlock.type !== "text") {
    throw new Error("Tool result did not include a text content block.");
  }

  return textBlock.text;
}

function parseToolPayload(result: ProbeToolResponse): unknown {
  return JSON.parse(getTextContent(result));
}

function asQueryResult(value: unknown): ProbeQueryResult {
  if (
    typeof value !== "object" ||
    value === null ||
    !("rows" in value) ||
    !Array.isArray(value.rows) ||
    !("rowCount" in value) ||
    typeof value.rowCount !== "number"
  ) {
    throw new Error("Tool result was not a QueryResult-shaped object.");
  }

  return {
    rows: value.rows as Array<Record<string, unknown>>,
    rowCount: value.rowCount,
  };
}

function assertCheck(condition: boolean, passMessage: string, failMessage: string): boolean {
  if (condition) {
    pass(passMessage);
    return true;
  }

  fail(failMessage);
  return false;
}

async function main(): Promise<void> {
  const transport = new StdioClientTransport({
    command: "node",
    args: ["--import", "tsx", "src/mcp/server.ts"],
    cwd: PROJECT_ROOT,
  });
  const client = new Client(CLIENT_INFO);
  let hasFailure = false;

  try {
    await client.connect(transport);
    pass("Connected to MCP server over stdio");

    const listedTools = await client.listTools();
    const listedToolNames = new Set(listedTools.tools.map((tool) => tool.name));
    const missingTools = tools
      .map((tool) => tool.name)
      .filter((toolName) => !listedToolNames.has(toolName));

    if (
      !assertCheck(
        missingTools.length === 0,
        `listTools exposed all ${tools.length} engine tools`,
        `listTools was missing engine tools: ${missingTools.join(", ")}`,
      )
    ) {
      hasFailure = true;
    }

    const accountCountResult = await client.callTool({
      name: "query_warehouse",
      arguments: { sql: "SELECT COUNT(*) AS n FROM accounts" },
    }, CallToolResultSchema);

    if (accountCountResult.isError) {
      fail(`query_warehouse returned an MCP error: ${getTextContent(accountCountResult)}`);
      hasFailure = true;
    } else {
      const accountCountPayload = asQueryResult(parseToolPayload(accountCountResult));
      const accountCount = accountCountPayload.rows[0]?.n;

      if (
        !assertCheck(
          accountCount === 500,
          "query_warehouse returned accounts count = 500",
          `query_warehouse returned accounts count ${String(accountCount)} instead of 500`,
        )
      ) {
        hasFailure = true;
      }
    }

    const churnMensalResult = await client.callTool({
      name: "run_metric",
      arguments: { id: "churn_mensal" },
    }, CallToolResultSchema);

    if (churnMensalResult.isError) {
      fail(`run_metric returned an MCP error: ${getTextContent(churnMensalResult)}`);
      hasFailure = true;
    } else {
      const churnMensalPayload = asQueryResult(parseToolPayload(churnMensalResult));

      if (
        !assertCheck(
          churnMensalPayload.rowCount === 24 && churnMensalPayload.rows.length === 24,
          "run_metric returned 24 churn_mensal rows (one per month)",
          `run_metric returned rowCount=${churnMensalPayload.rowCount}, rows.length=${churnMensalPayload.rows.length}`,
        )
      ) {
        hasFailure = true;
      }
    }
  } catch (error) {
    fail(error instanceof Error ? error.message : String(error));
    hasFailure = true;
  } finally {
    await client.close().catch(() => undefined);
    await transport.close().catch(() => undefined);
  }

  if (hasFailure) {
    process.exit(1);
  }
}

void main().catch((error: unknown) => {
  fail(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
