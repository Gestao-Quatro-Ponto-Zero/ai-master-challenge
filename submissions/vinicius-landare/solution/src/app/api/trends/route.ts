import { NextRequest, NextResponse } from "next/server";
import { callLLM, extractJSON } from "@/lib/openrouter";

const TRENDS_SYSTEM = `Você é um analista de tendências de social media. Receba dados comparativos entre dois períodos e identifique as mudanças mais relevantes para o gestor agir.

REGRAS:
- Foque em mudanças ACIONÁVEIS, não em variações insignificantes
- Se a diferença for menor que 1pp, marque como "estável" e não recomende ação
- Priorize tendências que podem impactar receita ou engagement significativamente
- Seja conciso e direto

FORMATO DE RESPOSTA (JSON válido):
{
  "trends": [
    {
      "metric": "nome da métrica que mudou",
      "direction": "up" | "down" | "stable",
      "magnitude": "variação em pp ou %",
      "significance": "high" | "medium" | "low",
      "action": "ação recomendada em 1 frase"
    }
  ],
  "summary": "resumo executivo em 2-3 frases"
}`;

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { current_period, previous_period, context = "dataset geral" } = body;

    if (!current_period || !previous_period) {
      return NextResponse.json(
        { error: "Missing required fields: current_period, previous_period" },
        { status: 400 }
      );
    }

    const userMessage = `Contexto: ${context}

Período anterior:
${JSON.stringify(previous_period, null, 2)}

Período atual:
${JSON.stringify(current_period, null, 2)}

Identifique as tendências mais relevantes e recomende ações.`;

    const response = await callLLM({
      system: TRENDS_SYSTEM,
      user: userMessage,
      temperature: 0.3,
      maxTokens: 1500,
    });

    const result = extractJSON<Record<string, unknown>>(response);

    return NextResponse.json({
      success: true,
      model_used: response._model_used,
      ...result,
    });
  } catch (err) {
    console.error("Trends API error:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Internal error" },
      { status: 500 }
    );
  }
}
