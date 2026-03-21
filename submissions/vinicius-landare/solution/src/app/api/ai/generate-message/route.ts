import { NextResponse } from "next/server";
import { callLLM } from "@/lib/openrouter";

export async function POST(req: Request) {
  try {
    const { context, data } = await req.json();

    let prompt = "";

    if (context === "calendar_content") {
      const { roteiro, platform, niche } = data;
      prompt = `Você é um assistente de comunicação da equipe G4 Strategy.

Gere uma mensagem profissional e direta para enviar via WhatsApp a um influenciador ou parceiro de produção de conteúdo.
A mensagem deve incluir o roteiro completo abaixo, formatado de forma clara e legível para WhatsApp.

ROTEIRO:
${roteiro}

Plataforma: ${platform}
Mercado: ${niche}

Regras:
- Use linguagem profissional mas próxima
- Inclua o roteiro completo na mensagem (não resuma)
- Formate com emojis leves para facilitar leitura no WhatsApp
- Máximo de 1500 caracteres
- Comece com uma introdução de 1 linha, depois o roteiro, depois o próximo passo (ex: "Pode confirmar disponibilidade?")
- Não use asteriscos para negrito (WhatsApp usa *texto*)`;
    } else {
      return NextResponse.json({ message: data.fallback || "" });
    }

    const response = await callLLM({
      system: "Você gera mensagens profissionais de WhatsApp para equipes de social media.",
      user: prompt,
      model: "google/gemini-flash-1.5",
      temperature: 0.6,
      maxTokens: 600,
    });

    return NextResponse.json({ message: response.trim() });
  } catch (err) {
    console.error("[generate-message] Erro:", err);
    return NextResponse.json(
      { error: "Falha ao gerar mensagem", message: "" },
      { status: 500 }
    );
  }
}
