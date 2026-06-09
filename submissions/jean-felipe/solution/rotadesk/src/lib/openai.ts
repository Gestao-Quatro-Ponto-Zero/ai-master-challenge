import OpenAI from "openai";
import { DS2_CATEGORIES } from "./constants";

function getOpenAI() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) throw new Error("OPENAI_API_KEY não configurada");
  return new OpenAI({ apiKey: key });
}

export interface LlmClassification {
  topic_group: string;
  confidence: number;
  reasoning: string;
}

export async function reclassifyWithLlm(
  text: string,
  sklearnGuess: string,
  sklearnConfidence: number
): Promise<LlmClassification> {
  const response = await getOpenAI().chat.completions.create({
    model: "gpt-4o-mini",
    temperature: 0.2,
    response_format: { type: "json_object" },
    messages: [
      {
        role: "system",
        content: `Você classifica tickets de suporte de TI em uma destas categorias: ${DS2_CATEGORIES.join(", ")}.
Responda em JSON: {"topic_group": "...", "confidence": 0-100, "reasoning": "..."}.
O classificador sklearn sugeriu "${sklearnGuess}" com confiança de ${sklearnConfidence}%.`,
      },
      { role: "user", content: text },
    ],
  });

  const raw = response.choices[0]?.message?.content ?? "{}";
  const parsed = JSON.parse(raw) as LlmClassification;
  return parsed;
}

export async function generateDraftReply(
  ticketSubject: string,
  ticketDescription: string,
  topicGroup: string,
  ragContext: string
): Promise<string> {
  const response = await getOpenAI().chat.completions.create({
    model: "gpt-4o-mini",
    temperature: 0.4,
    messages: [
      {
        role: "system",
        content: `Você é agente da RotaDesk. Escreva um rascunho de resposta em português do Brasil, com tom profissional e objetivo. Use acentuação e pontuação corretas.
Categoria: ${topicGroup}
Base de conhecimento:
${ragContext}`,
      },
      {
        role: "user",
        content: `Assunto: ${ticketSubject}\n\n${ticketDescription}`,
      },
    ],
  });
  return response.choices[0]?.message?.content ?? "";
}

export async function generateChatReply(
  messages: { role: "user" | "assistant"; content: string }[],
  ragContext: string,
  ticketMeta: string
): Promise<string> {
  const response = await getOpenAI().chat.completions.create({
    model: "gpt-4o-mini",
    temperature: 0.5,
    messages: [
      {
        role: "system",
        content: `Você é a equipe RotaDesk em um atendimento de suporte. Responda em português do Brasil, com acentuação e pontuação corretas.
${ticketMeta}
Base de conhecimento (RAG):
${ragContext}`,
      },
      ...messages,
    ],
  });
  return response.choices[0]?.message?.content ?? "";
}
