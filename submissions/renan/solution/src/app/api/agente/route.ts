import Anthropic from "@anthropic-ai/sdk";
import { z } from "zod";
import { isEffort, isModelId, KEY_HEADER, type ModelId } from "@/lib/agent/config";
import { describeApiError } from "@/lib/agent/errors";
import { ANSWER_TOOL, DATA_TOOLS, runDataTool } from "@/lib/agent/tools";
import { dataset, findDeal, history, options } from "@/lib/pipeline";
import { MOMENTUM_LABEL } from "@/lib/scoring/score";

export const maxDuration = 60;

const MAX_ITERATIONS = 8;

const bodySchema = z.object({
  mensagens: z
    .array(z.object({ papel: z.enum(["vendedor", "agente"]), texto: z.string().min(1).max(4000) }))
    .min(1)
    .max(20),
  vendedor: z.string().optional(),
  modelo: z.string(),
  esforco: z.string(),
});

const answerSchema = z.object({
  resposta: z.string(),
  destaques: z.array(z.object({ rotulo: z.string(), valor: z.string() })).max(4).catch([]),
  grafico: z
    .object({
      titulo: z.string(),
      unidade: z.enum(["usd", "deals", "pct", "dias"]),
      barras: z.array(z.object({ rotulo: z.string(), valor: z.number() })).max(12),
    })
    .optional()
    .catch(undefined),
  deals: z.array(z.string()).max(10).catch([]),
  acoes: z.array(z.string()).max(4).catch([]),
  proximas_perguntas: z.array(z.string()).max(3).catch([]),
});

const SYSTEM = `Você é o Agente Gestor da Régua: um analista de dados de vendas, como o "pergunte aos dados" de um Power BI, dentro de uma ferramenta de priorização de pipeline. Responda em português do Brasil.

Escopo (regra absoluta): você só fala dos dados da Régua: deals abertos, vendedores, managers, escritórios, produtos, contas, a fila de parados, o histórico de fechamentos e a metodologia do score. Pipeline do CRM em ${dataset.referenceDate.split("-").reverse().join("/")}, ${options.agents.length} vendedores ativos.
- Todo número que você citar precisa ter vindo de uma ferramenta nesta conversa. Nunca estime, arredonde por conta própria ou complete com conhecimento geral.
- Não dê conselhos genéricos de vendas, opiniões ou informações de fora dos dados. Ações recomendadas devem sair dos dados (ex.: a próxima ação de um deal, revisar um parado, cadastrar uma conta).
- Se a pergunta estiver fora do escopo, responda em uma frase que você analisa os dados do pipeline e ofereça, em "proximas_perguntas", três perguntas que você consegue responder sobre o mesmo tema. Não diga "não sei".
- Diferenças de taxa de vitória entre vendedores são compatíveis com o acaso: nunca ranqueie vendedores por desempenho. Nenhum deal fechou depois de ${history.maxCycle} dias.

Seja ativo, não passivo: comece pela conclusão, traga o número que importa, aponte o que fazer e proponha o próximo passo da análise. Para "briefing" ou "o que preciso saber", use a ferramenta radar.

Termine sempre chamando a ferramenta "responder", uma única vez. Use "grafico" quando houver comparação entre categorias e "deals" para listar os códigos dos deals citados (a tela mostra os dados de cada um). Não escreva a resposta fora dela.`;

/** Dados de um deal para a tabela da resposta, lidos do motor de score (nunca do texto do modelo). */
function dealRow(id: string) {
  const s = findDeal(id.trim().toUpperCase());
  if (!s) return null;
  return {
    id: s.deal.id,
    produto: s.deal.product,
    vendedor: s.deal.agent,
    momento: MOMENTUM_LABEL[s.momentum],
    parado: s.momentum === "stalled",
    dias: s.daysOpen,
    chance: s.winProbability,
    valorEsperado: s.expectedValue,
    precoTabela: s.deal.listPrice,
    proximaAcao: s.nextAction,
  };
}

/**
 * Agente gestor: loop de tool use sobre os dados da Régua, restrito a eles.
 * Usa somente a chave enviada pelo próprio usuário; o servidor não tem chave.
 */
export async function POST(request: Request) {
  const apiKey = request.headers.get(KEY_HEADER)?.trim();
  if (!apiKey) {
    return Response.json({ erro: "Cadastre sua chave da API em Configurações para usar o agente." }, { status: 401 });
  }

  const parsed = bodySchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success || !isModelId(parsed.data.modelo) || !isEffort(parsed.data.esforco)) {
    return Response.json({ erro: "Pedido inválido." }, { status: 400 });
  }
  const { mensagens, vendedor, modelo, esforco } = parsed.data;
  const model: ModelId = modelo;

  const client = new Anthropic({ apiKey, maxRetries: 1 });

  const context = vendedor && options.agents.includes(vendedor) ? `\n\n[Contexto: o usuário está analisando ${vendedor}.]` : "";
  const messages: Anthropic.Beta.BetaMessageParam[] = mensagens.map((m, i) => ({
    role: m.papel === "vendedor" ? "user" : "assistant",
    content: i === mensagens.length - 1 && m.papel === "vendedor" ? m.texto + context : m.texto,
  }));

  const tools: Anthropic.Beta.BetaToolUnion[] = [...DATA_TOOLS, ANSWER_TOOL];
  const usedTools = new Set<string>();

  try {
    for (let i = 0; i < MAX_ITERATIONS; i++) {
      const response = await client.beta.messages.create({
        model,
        max_tokens: 8000,
        system: SYSTEM,
        messages,
        tools,
        output_config: { effort: esforco },
        // Fallback de recusa no servidor: disponível para Opus e Sonnet, não para o Haiku.
        ...(model === "claude-haiku-5-5" ? {} : { betas: ["server-side-fallback-2026-07-01"], fallbacks: "default" as const }),
      });

      if (response.stop_reason === "refusal") {
        return Response.json({ erro: "O modelo recusou esta pergunta. Tente reformular." }, { status: 422 });
      }

      const toolUses = response.content.filter((b): b is Anthropic.Beta.BetaToolUseBlock => b.type === "tool_use");
      const answer = toolUses.find((b) => b.name === ANSWER_TOOL.name);
      if (answer) {
        const result = answerSchema.safeParse(answer.input);
        if (!result.success) return Response.json({ erro: "O agente devolveu uma resposta incompleta. Tente de novo." }, { status: 502 });
        const { deals, proximas_perguntas, ...rest } = result.data;
        return Response.json({
          ...rest,
          deals: [...new Map(deals.map(dealRow).flatMap((d) => (d ? [[d.id, d] as const] : []))).values()],
          proximasPerguntas: proximas_perguntas,
          ferramentas: [...usedTools],
        });
      }

      if (toolUses.length === 0) {
        // Respondeu em texto sem chamar "responder": mostra o texto como resposta simples.
        const text = response.content
          .filter((b): b is Anthropic.Beta.BetaTextBlock => b.type === "text")
          .map((b) => b.text)
          .join("\n")
          .trim();
        return Response.json({ resposta: text, destaques: [], deals: [], acoes: [], proximasPerguntas: [], ferramentas: [...usedTools] });
      }

      messages.push({ role: "assistant", content: response.content });
      const results: Anthropic.Beta.BetaToolResultBlockParam[] = toolUses.map((tool) => {
        usedTools.add(tool.name);
        const { content, isError } = runDataTool(tool.name, tool.input);
        return { type: "tool_result", tool_use_id: tool.id, content, is_error: isError };
      });
      messages.push({ role: "user", content: results });
    }
    return Response.json({ erro: "O agente não concluiu a análise a tempo. Tente uma pergunta mais específica." }, { status: 504 });
  } catch (error) {
    const { status, message } = describeApiError(error);
    return Response.json({ erro: message }, { status });
  }
}
