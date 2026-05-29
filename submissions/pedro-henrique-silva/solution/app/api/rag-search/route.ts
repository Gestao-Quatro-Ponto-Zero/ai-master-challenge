import { NextRequest } from "next/server";

import { buildRagSuggestion } from "@/lib/rag";
import { fail, ok, readBody } from "@/lib/api";
import { startTimer } from "@/lib/observability";

type RagBody = {
  text?: string;
};

export async function POST(request: NextRequest) {
  const body = await readBody<RagBody>(request);
  const text = body?.text?.trim();

  if (!text) {
    return fail("Campo text é obrigatório", 400);
  }

  const timer = startTimer();
  const result = await buildRagSuggestion(text);
  const elapsed = timer.done("rag_ms");

  return ok({
    suggestion: result.suggestion,
    confidence: result.confidence,
    sources: result.sources,
    latency_ms: elapsed,
  });
}
