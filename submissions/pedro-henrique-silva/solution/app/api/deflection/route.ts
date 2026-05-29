import { NextRequest } from "next/server";

import { getDemoUser } from "@/lib/auth";
import { fail, ok, readBody } from "@/lib/api";
import { addDeflection } from "@/lib/mock-db";
import type { RagSource } from "@/lib/types";

type Body = {
  raw_text?: string;
  top_matches?: RagSource[];
};

export async function POST(request: NextRequest) {
  const user = getDemoUser(request);

  if (!user) {
    return fail("Não autenticado", 401);
  }

  const body = await readBody<Body>(request);

  if (!body?.raw_text) {
    return fail("raw_text é obrigatório", 400);
  }

  const event = addDeflection({
    customerId: user.id,
    rawText: body.raw_text,
    topMatches: body.top_matches ?? [],
  });

  return ok({ event }, 201);
}
