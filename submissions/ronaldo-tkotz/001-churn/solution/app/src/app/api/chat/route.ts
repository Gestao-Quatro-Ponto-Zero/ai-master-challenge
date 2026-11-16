/**
 * The chat face of the engine — streams a grounded analyst answer over SSE.
 *
 * Same engine as the MCP server: this route just drives `ask()` and forwards
 * every grounded step (the SQL, the row count, the rows) to the browser live,
 * then the final answer. The warehouse stays read-only; nothing here can mutate.
 */
import { requireUser, authErrorResponse } from "@/app/lib/auth";
import { ask, type AgentStep } from "@/engine/agent";

export const runtime = "nodejs"; // better-sqlite3 is a native addon — never Edge.
export const dynamic = "force-dynamic"; // every answer is computed at request time.

interface ChatRequest {
  question?: unknown;
}

function sse(obj: unknown): Uint8Array {
  return new TextEncoder().encode(`data: ${JSON.stringify(obj)}\n\n`);
}

export async function POST(req: Request): Promise<Response> {
  const user = await requireUser().catch((e) => e);
  if (user instanceof Error) return authErrorResponse(user) ?? Response.json({ error: "unauthorized" }, { status: 401 });
  let body: ChatRequest;
  try {
    body = (await req.json()) as ChatRequest;
  } catch {
    return Response.json({ error: "Body must be JSON." }, { status: 400 });
  }

  const question = typeof body.question === "string" ? body.question.trim() : "";
  if (!question) {
    return Response.json({ error: "Ask a question." }, { status: 400 });
  }

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const send = (obj: unknown): void => controller.enqueue(sse(obj));

      if (!process.env.LLM_API_KEY) {
        send({
          type: "error",
          message:
            "No model key set. Drop LLM_API_KEY into veta/.env.local (DeepSeek by default) and restart — the analyst goes live instantly. The proactive insight feed runs without a key.",
        });
        controller.close();
        return;
      }

      try {
        send({ type: "start", question });
        const result = await ask(question, {
          userId: user.id,
          onStep: (step: AgentStep) => send({ type: "step", step }),
        });
        send({
          type: "answer",
          text: result.answer,
          citedSql: result.citedSql,
          model: result.model,
          steps: result.steps,
        });
      } catch (e) {
        send({ type: "error", message: e instanceof Error ? e.message : String(e) });
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
