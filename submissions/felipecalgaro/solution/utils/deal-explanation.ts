import OpenAI from "openai";

import type { ScoreFactor } from "@/utils/deal-score";

export type DealExplanationRequest = {
  opportunityId: string;
  salesAgent: string;
  product: string;
  account: string;
  dealStage: string;
  score: number;
  topPositiveFactors: ScoreFactor[];
  topNegativeFactors: ScoreFactor[];
};

export type DealExplanationResponse = {
  summary: string;
  nextAction: string;
  generatedAt: string;
  source: "placeholder" | "openai";
};

type ModelExplanation = {
  summary?: string;
  nextAction?: string;
};

function readApiKey(): string | null {
  const key = process.env.OPENAI_API_KEY?.trim();
  return key ? key : null;
}

function buildFactorSummary(
  factor: ScoreFactor | undefined,
  fallback: string,
): string {
  if (!factor) {
    return fallback;
  }

  return `${factor.label}: ${factor.reason}`;
}

function scoreTier(score: number): "Alta" | "Media" | "Baixa" {
  if (score >= 67) return "Alta";
  if (score >= 45) return "Media";
  return "Baixa";
}

function serializeFactors(factors: ScoreFactor[]): string {
  return factors
    .map((factor) => {
      return `- ${factor.label}: ${factor.reason}`;
    })
    .join("\n");
}

function normalizeFactorsForNarrative(input: DealExplanationRequest): {
  positiveFactors: ScoreFactor[];
  negativeFactors: ScoreFactor[];
} {
  const positiveFactors = input.topPositiveFactors.filter(
    (factor) => factor.signedImpact > 0,
  );

  // A clipped max score can still carry tiny negative factors. Hide negligible
  // negatives to keep the explanation aligned with the displayed score.
  const minNegativeImpact = input.score >= 99 ? 0.25 : 0.05;
  const negativeFactors = input.topNegativeFactors.filter(
    (factor) => factor.signedImpact < -minNegativeImpact,
  );

  return { positiveFactors, negativeFactors };
}

function coerceModelExplanation(
  raw: string | null | undefined,
): ModelExplanation {
  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw) as ModelExplanation;
  } catch {
    return {};
  }
}

function extractJsonObject(raw: string): string | null {
  const firstBrace = raw.indexOf("{");
  const lastBrace = raw.lastIndexOf("}");

  if (firstBrace === -1 || lastBrace === -1 || lastBrace <= firstBrace) {
    return null;
  }

  return raw.slice(firstBrace, lastBrace + 1);
}

function parseModelExplanation(
  raw: string | null | undefined,
): ModelExplanation {
  const direct = coerceModelExplanation(raw);
  if (direct.summary || direct.nextAction) {
    return direct;
  }

  if (!raw) {
    return {};
  }

  const extracted = extractJsonObject(raw);
  if (!extracted) {
    return {};
  }

  return coerceModelExplanation(extracted);
}

function buildPrompt(input: DealExplanationRequest): string {
  const narrativeFactors = normalizeFactorsForNarrative(input);
  const positiveFactors = serializeFactors(narrativeFactors.positiveFactors);
  const negativeFactors = serializeFactors(narrativeFactors.negativeFactors);
  const riskInstruction =
    narrativeFactors.negativeFactors.length > 0
      ? "- Mencione pontos positivos e riscos quando ambos existirem."
      : "- Não mencione riscos ou pontos negativos quando nenhum for informado nos principais fatores negativos.";

  return `Contexto:\n- Objetivo do app: ajudar vendedores a decidir onde focar em seguida.\n- Objetivo da explicação: justificativa objetiva e personalizada para o score deste negócio.\n\nResumo do negócio:\n- Vendedor: ${input.salesAgent}\n- Produto: ${input.product}\n- Conta: ${input.account}\n- Etapa do negócio: ${input.dealStage}\n- Faixa de prioridade: ${scoreTier(input.score)}\n\nPrincipais fatores positivos de score (linguagem simples):\n${positiveFactors || "- Nenhum"}\n\nPrincipais fatores negativos de score (linguagem simples):\n${negativeFactors || "- Nenhum"}\n\nRequisitos de saida:\n- Retorne apenas JSON valido com as chaves: summary, nextAction.\n- summary: 2-4 frases, clara e objetiva, adaptada ao contexto deste vendedor/negócio.\n- Comece direto pelos fatores principais e contexto; não abra com repetição de metadados.\n- Não mencione o ID da oportunidade nem o score numerico na resposta. Mencionar o nome da conta/empresa e permitido.\n- nextAction: uma ação especifica e pratica para o vendedor.\n- Não inclua mecanicas internas de score (IDs de criterio, impactos, pesos, multiplicadores, formulas ou metadados numericos).\n${riskInstruction}`;
}

function buildFallbackResponse(
  input: DealExplanationRequest,
): DealExplanationResponse {
  const strongestPositive = input.topPositiveFactors[0];
  const strongestNegative = input.topNegativeFactors[0];

  return {
    summary: `Esta e uma explicação provisoria da IA para ${input.opportunityId}. O score atual e ${input.score}. Sinal positivo mais forte: ${buildFactorSummary(
      strongestPositive,
      "Nenhum sinal positivo foi identificado.",
    )} Strongest risk signal: ${buildFactorSummary(
      strongestNegative,
      "Nenhum sinal de risco relevante foi identificado.",
    )}`,
    nextAction:
      "Confirme o cronograma de compra na proxima conversa e revalide os criterios de decisao antes de comprometer o forecast.",
    generatedAt: new Date().toISOString(),
    source: "placeholder",
  };
}

export async function getDealScoreExplanation(
  input: DealExplanationRequest,
): Promise<DealExplanationResponse> {
  const apiKey = readApiKey();

  if (!apiKey) {
    return buildFallbackResponse(input);
  }

  const client = new OpenAI({ apiKey });

  const model = process.env.OPENAI_MODEL?.trim() || "gpt-5-nano";

  try {
    const response = await client.responses.create({
      model,
      instructions:
        "Voce e um assistente de enablement de vendas para um app de priorização de leads em CRM. Produza uma explicação objetiva, concisa e personalizada sobre por que um negócio recebeu seu score. Fale diretamente com o vendedor em portugues brasileiro. Baseie sua resposta apenas em fatos e fatores fornecidos. Não invente dados. Não mencione pontos negativos quando nenhum for fornecido no contexto de entrada. Nunca exponha mecanicas internas de score como IDs de criterio, impactos, pesos, multiplicadores, formulas ou calculos brutos. Não mencione o ID da oportunidade nem o score numerico. Mencionar o nome da conta/empresa e permitido. Retorne apenas JSON valido.",
      input: buildPrompt(input),
    });

    const parsed = parseModelExplanation(response.output_text);
    const summary = parsed.summary?.trim();
    const nextAction = parsed.nextAction?.trim();

    if (!summary || !nextAction) {
      return buildFallbackResponse(input);
    }

    return {
      summary,
      nextAction,
      generatedAt: new Date().toISOString(),
      source: "openai",
    };
  } catch (error) {
    console.error("Falha ao gerar explicação com OpenAI", error);
    return buildFallbackResponse(input);
  }
}
