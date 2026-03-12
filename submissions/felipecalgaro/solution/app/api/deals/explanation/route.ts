import { NextResponse } from "next/server";

import {
  getDealScoreExplanation,
  type DealExplanationRequest,
} from "@/utils/deal-explanation";

function isValidPayload(body: unknown): body is DealExplanationRequest {
  if (!body || typeof body !== "object") {
    return false;
  }

  const candidate = body as Partial<DealExplanationRequest>;

  return (
    typeof candidate.opportunityId === "string" &&
    typeof candidate.salesAgent === "string" &&
    typeof candidate.product === "string" &&
    typeof candidate.account === "string" &&
    typeof candidate.dealStage === "string" &&
    typeof candidate.score === "number" &&
    Array.isArray(candidate.topPositiveFactors) &&
    Array.isArray(candidate.topNegativeFactors)
  );
}

export async function POST(request: Request) {
  try {
    const body: unknown = await request.json();

    if (!isValidPayload(body)) {
      return NextResponse.json(
        { error: "Payload de solicitação de explicação invalido." },
        { status: 400 },
      );
    }

    const explanation = await getDealScoreExplanation(body);

    return NextResponse.json(explanation);
  } catch {
    return NextResponse.json(
      { error: "Não foi possivel gerar a explicação." },
      { status: 500 },
    );
  }
}
