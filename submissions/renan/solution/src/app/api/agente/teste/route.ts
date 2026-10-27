import Anthropic from "@anthropic-ai/sdk";
import { isModelId, KEY_HEADER } from "@/lib/agent/config";
import { describeApiError } from "@/lib/agent/errors";

/** Testa a chave do usuário consultando o modelo escolhido (não gera tokens). */
export async function POST(request: Request) {
  const apiKey = request.headers.get(KEY_HEADER)?.trim();
  const { modelo } = (await request.json().catch(() => ({}))) as { modelo?: unknown };
  if (!apiKey) return Response.json({ erro: "Informe a chave da API." }, { status: 400 });
  if (!isModelId(modelo)) return Response.json({ erro: "Modelo inválido." }, { status: 400 });

  try {
    const model = await new Anthropic({ apiKey, maxRetries: 0 }).models.retrieve(modelo);
    return Response.json({ ok: true, modelo: model.display_name });
  } catch (error) {
    const { status, message } = describeApiError(error);
    return Response.json({ erro: message }, { status });
  }
}
