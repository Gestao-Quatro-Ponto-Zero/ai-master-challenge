import { NextRequest, NextResponse } from "next/server";
import { GoogleGenerativeAI } from "@google/generative-ai";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: "GEMINI_API_KEY não configurada." }, { status: 500 });
  }

  const deal = await req.json();

  const prompt = `Você é um coach de vendas B2B especialista em pipelines comerciais.
Analise este deal e forneça uma avaliação estratégica objetiva em português.

DADOS DO DEAL:
- Conta: ${deal.account || "Não identificada"}
- Produto: ${deal.product || "—"}
- Ticket: $${deal.product_price?.toLocaleString() || "—"}
- Receita da conta: ${deal.account_revenue ? `$${deal.account_revenue.toFixed(0)}M` : "—"}
- Setor: ${deal.account_sector || "—"}
- Stage atual: ${deal.deal_stage}
- Dias no stage: ${deal.days_in_stage}
- Score de qualificação: ${deal.score}/100
- Vendedor: ${deal.sales_agent || "—"}
- Manager: ${deal.manager || "—"}
- Região: ${deal.regional_office || "—"}

BENCHMARKS DO PIPELINE:
- Ciclo médio saudável em Engaging: 52 dias
- Score ≥70 = Alta prioridade | 40–69 = Média | <40 = Baixa

Responda SOMENTE com um JSON válido neste formato exato (sem markdown, sem \`\`\`):
{
  "urgencia": "alta|media|baixa",
  "resumo": "1 frase de avaliação geral do deal (máx 20 palavras)",
  "acao": "1 ação específica e concreta para o vendedor fazer HOJE (máx 30 palavras)",
  "raciocinio": "Explicação em 2-3 frases baseada nos dados numéricos do deal"
}`;

  try {
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });
    const result = await model.generateContent(prompt);
    const text = result.response.text().trim();

    // Strip markdown code fences if Gemini adds them
    const clean = text.replace(/^```json\s*/i, "").replace(/^```\s*/i, "").replace(/\s*```$/i, "").trim();
    const parsed = JSON.parse(clean);

    return NextResponse.json(parsed);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("Gemini error:", msg);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
