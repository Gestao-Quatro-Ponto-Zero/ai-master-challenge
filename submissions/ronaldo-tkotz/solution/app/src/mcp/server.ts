import process from "node:process";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  type CallToolResult,
  type ListToolsResult,
} from "@modelcontextprotocol/sdk/types.js";
import { tools, type EngineTool } from "../engine/tools";

const SERVER_INFO = { name: "veta-mcp", version: "0.1.0" } as const;
type McpTool = ListToolsResult["tools"][number];

function asMcpInputSchema(tool: EngineTool): McpTool["inputSchema"] {
  return tool.inputSchema as McpTool["inputSchema"];
}

function listEngineTools(): ListToolsResult {
  return {
    tools: tools.map((tool) => ({
      name: tool.name,
      description: tool.description,
      inputSchema: asMcpInputSchema(tool),
    })),
  };
}

function textResult(text: string, isError = false): CallToolResult {
  return {
    content: [{ type: "text", text }],
    ...(isError ? { isError: true } : {}),
  };
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return String(error);
}

function buildToolLookup(): Map<string, EngineTool> {
  return new Map(tools.map((tool) => [tool.name, tool]));
}

function createServer(): Server {
  const server = new Server(SERVER_INFO, { capabilities: { tools: {} } });
  const toolLookup = buildToolLookup();

  server.setRequestHandler(ListToolsRequestSchema, async () => listEngineTools());

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const tool = toolLookup.get(request.params.name);

    if (!tool) {
      return textResult(`Unknown tool '${request.params.name}'.`, true);
    }

    try {
      const result = await tool.handler(request.params.arguments ?? {});
      return textResult(JSON.stringify(result, null, 2));
    } catch (error) {
      return textResult(errorMessage(error), true);
    }
  });

  return server;
}

export async function main(): Promise<void> {
  const server = createServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

void main().catch((error: unknown) => {
  process.stderr.write(`Failed to start MCP server: ${errorMessage(error)}\n`);
  process.exit(1);
});
