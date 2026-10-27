import type Anthropic from "@anthropic-ai/sdk";
import { z } from "zod";
import { analysis, applyFilters, dataset, findDeal, history, MOMENTUM_ORDER, options, pipeline, summarize } from "@/lib/pipeline";
import { MOMENTUM_LABEL, type ScoredDeal } from "@/lib/scoring/score";
import { buildInsights } from "./insights";

/*
 * Ferramentas de leitura que o agente usa para responder com os dados da Régua.
 * Todas são somente leitura e devolvem números já calculados pelo motor de score,
 * para o modelo citar em vez de estimar.
 */

const round = (x: number, digits = 1) => Math.round(x * 10 ** digits) / 10 ** digits;

function dealSummary(s: ScoredDeal) {
  return {
    id: s.deal.id,
    produto: s.deal.product,
    vendedor: s.deal.agent,
    conta: s.deal.account ?? "não informada no CRM",
    momento: MOMENTUM_LABEL[s.momentum],
    dias_aberto: s.daysOpen,
    chance_pct: s.winProbability === null ? null : round(s.winProbability * 100),
    valor_esperado_usd: Math.round(s.expectedValue),
    preco_tabela_usd: s.deal.listPrice,
    score: s.score,
    proxima_acao: s.nextAction,
  };
}

const agentName = z.string().refine((v) => options.agents.includes(v), "vendedor não existe no CRM");

const schemas = {
  resumo_vendedor: z.object({ vendedor: agentName.optional() }),
  detalhe_deal: z.object({ id: z.string().min(1) }),
  listar_deals: z.object({
    vendedor: agentName.optional(),
    momento: z.enum(MOMENTUM_ORDER as [string, ...string[]]).optional(),
    produto: z.string().optional(),
    limite: z.number().int().min(1).max(25).optional(),
  }),
  fila_parados: z.object({ vendedor: agentName.optional(), limite: z.number().int().min(1).max(25).optional() }),
  visao_time: z.object({ manager: z.string().optional() }),
  fatos_metodologia: z.object({}),
  radar: z.object({ vendedor: agentName.optional(), manager: z.string().optional() }),
};

type ToolName = keyof typeof schemas;

const handlers: { [K in ToolName]: (input: z.infer<(typeof schemas)[K]>) => unknown } = {
  resumo_vendedor: ({ vendedor }) => {
    const deals = applyFilters(pipeline, { agent: vendedor });
    const { active, stalled, activeExpectedValue, stalledValueShare, withoutAccount } = summarize(deals);
    return {
      escopo: vendedor ?? "time inteiro",
      data_referencia: dataset.referenceDate,
      deals_ativos: active.length,
      valor_esperado_ativo_usd: Math.round(activeExpectedValue),
      na_reta_final: active.filter((s) => s.momentum === "closing").length,
      em_prospeccao: active.filter((s) => s.momentum === "prospecting").length,
      parados: stalled.length,
      parcela_valor_parado_pct: round(stalledValueShare * 100),
      deals_sem_conta: withoutAccount,
      pauta_top5: active.slice(0, 5).map(dealSummary),
    };
  },
  detalhe_deal: ({ id }) => {
    const s = findDeal(id.trim().toUpperCase());
    if (!s) return { erro: `Deal ${id} não está no pipeline aberto.` };
    return {
      ...dealSummary(s),
      manager: s.deal.manager,
      escritorio: s.deal.regionalOffice,
      setor: s.deal.sector,
      engajamento: s.deal.engageDate,
      fatores_da_chance: s.factors.map((f) => ({ fator: f.label, pontos_percentuais: round(f.points, 2), detalhe: f.detail })),
      taxa_base_pct: round(history.baseRate * 100),
    };
  },
  listar_deals: ({ vendedor, momento, produto, limite }) => {
    const deals = applyFilters(pipeline, {
      agent: vendedor,
      momentum: momento as ScoredDeal["momentum"] | undefined,
      product: produto && options.products.includes(produto) ? produto : undefined,
    });
    return { total: deals.length, deals: deals.slice(0, limite ?? 10).map(dealSummary) };
  },
  fila_parados: ({ vendedor, limite }) => {
    const stalled = applyFilters(pipeline, { agent: vendedor, momentum: "stalled" }).sort((a, b) => b.deal.listPrice - a.deal.listPrice);
    return {
      total: stalled.length,
      valor_tabela_usd: stalled.reduce((s, d) => s + d.deal.listPrice, 0),
      regra: `Abertos há mais de ${history.maxCycle} dias; nenhum dos ${history.closedDeals} deals fechados levou mais que isso.`,
      maiores: stalled.slice(0, limite ?? 10).map(dealSummary),
    };
  },
  visao_time: ({ manager }) => {
    const validManager = manager && options.managers.includes(manager) ? manager : undefined;
    const team = applyFilters(pipeline, { manager: validManager });
    return {
      escopo: validManager ?? "todos os managers",
      aviso: "Sem ranking de desempenho: diferenças de taxa de vitória entre vendedores são compatíveis com o acaso.",
      vendedores: dataset.agents
        .filter((a) => !validManager || a.manager === validManager)
        .map((a) => {
          const s = summarize(team.filter((d) => d.deal.agent === a.name));
          return {
            vendedor: a.name,
            ativos: s.active.length,
            valor_esperado_usd: Math.round(s.activeExpectedValue),
            parados: s.stalled.length,
            parcela_valor_parado_pct: round(s.stalledValueShare * 100),
            sem_conta: s.withoutAccount,
          };
        })
        .filter((v) => v.ativos + v.parados > 0),
    };
  },
  fatos_metodologia: () => ({
    taxa_geral_vitoria_pct: round(history.baseRate * 100),
    deals_fechados: history.closedDeals,
    maior_ciclo_dias: history.maxCycle,
    mediana_ciclo_perdidos_dias: history.lostMedianCycle,
    p75_ciclo_ganhos_dias: history.wonP75Cycle,
    chance_por_tempo_aberto: analysis.survivalPoints.map((p) => ({ apos_dias: p.day, chance_pct: round(p.winRate * 100) })),
    fim_de_trimestre: {
      vitoria_ultimo_mes_pct: round(analysis.quarter.quarterEnd.winRate * 100),
      vitoria_outros_meses_pct: round(analysis.quarter.otherMonths.winRate * 100),
      ressalva: "Pode ser artefato do dataset; não entra no score.",
    },
    fatores: "Produto, setor e porte não separam ganhos de perdas; diferenças entre vendedores são compatíveis com o acaso.",
    backtest: "Chance com AUC ≈ 0,5; valor esperado captura ~50% da receita no top 20% (acaso ~19%).",
  }),
  radar: ({ vendedor, manager }) =>
    buildInsights({ agent: vendedor, manager: manager && options.managers.includes(manager) ? manager : undefined }).map(
      ({ severity, title, detail, metric }) => ({ severidade: severity, alerta: title, detalhe: detail, numero: metric }),
    ),
};

export const DATA_TOOLS: Anthropic.Beta.BetaTool[] = [
  {
    name: "resumo_vendedor",
    description:
      "Resumo do pipeline aberto de um vendedor (ou do time, sem vendedor): deals ativos, valor esperado, reta final, parados, deals sem conta e os 5 deals prioritários.",
    input_schema: {
      type: "object",
      properties: { vendedor: { type: "string", description: `Nome exato do vendedor. Opções: ${options.agents.join(", ")}` } },
      additionalProperties: false,
    },
  },
  {
    name: "detalhe_deal",
    description: "Detalhe de um deal aberto pelo código (ex.: 1LY8CAXD): chance, fatores em pontos percentuais, valor esperado, momento e próxima ação.",
    input_schema: {
      type: "object",
      properties: { id: { type: "string", description: "Código do deal (opportunity_id)." } },
      required: ["id"],
      additionalProperties: false,
    },
  },
  {
    name: "listar_deals",
    description: "Lista deals abertos ordenados por valor esperado, com filtros opcionais de vendedor, momento e produto.",
    input_schema: {
      type: "object",
      properties: {
        vendedor: { type: "string" },
        momento: { type: "string", enum: MOMENTUM_ORDER, description: "prospecting, early, progressing, closing (reta final) ou stalled (parado)." },
        produto: { type: "string", description: `Opções: ${options.products.join(", ")}` },
        limite: { type: "integer", minimum: 1, maximum: 25 },
      },
      additionalProperties: false,
    },
  },
  {
    name: "fila_parados",
    description: `Deals parados (abertos há mais de ${history.maxCycle} dias), do maior valor de tabela para o menor, para revisar ou desqualificar.`,
    input_schema: {
      type: "object",
      properties: { vendedor: { type: "string" }, limite: { type: "integer", minimum: 1, maximum: 25 } },
      additionalProperties: false,
    },
  },
  {
    name: "visao_time",
    description: `Higiene do pipeline por vendedor de um manager (ou de todos). Managers: ${options.managers.join(", ")}.`,
    input_schema: { type: "object", properties: { manager: { type: "string" } }, additionalProperties: false },
  },
  {
    name: "radar",
    description: "Alertas ativos do recorte (deals prestes a passar do maior ciclo, reta final, valor parado, higiene do CRM). Use para briefings e para perguntas como \"o que preciso saber hoje\".",
    input_schema: {
      type: "object",
      properties: { vendedor: { type: "string" }, manager: { type: "string" } },
      additionalProperties: false,
    },
  },
  {
    name: "fatos_metodologia",
    description: "Fatos do histórico do CRM: taxa de vitória, ciclos, chance por tempo aberto, efeito de fim de trimestre e resultado do backtest.",
    input_schema: { type: "object", properties: {}, additionalProperties: false },
  },
];

export const ANSWER_TOOL: Anthropic.Beta.BetaTool = {
  name: "responder",
  description:
    "Entrega a resposta final, no formato de um painel de BI. Chame exatamente uma vez, no fim. Todo número precisa ter vindo de uma ferramenta nesta conversa.",
  input_schema: {
    type: "object",
    properties: {
      resposta: { type: "string", description: "Resposta direta, em 1 a 4 frases curtas (markdown simples). Comece pela conclusão." },
      destaques: {
        type: "array",
        maxItems: 4,
        description: "Até 4 indicadores-chave da resposta, com o valor já formatado em pt-BR (ex.: US$ 18.948, 71%, 12 deals).",
        items: {
          type: "object",
          properties: { rotulo: { type: "string" }, valor: { type: "string" } },
          required: ["rotulo", "valor"],
          additionalProperties: false,
        },
      },
      grafico: {
        type: "object",
        description: "Gráfico de barras opcional quando a resposta compara categorias. Omita se não ajudar.",
        properties: {
          titulo: { type: "string" },
          unidade: { type: "string", enum: ["usd", "deals", "pct", "dias"] },
          barras: {
            type: "array",
            maxItems: 12,
            items: {
              type: "object",
              properties: { rotulo: { type: "string" }, valor: { type: "number" } },
              required: ["rotulo", "valor"],
              additionalProperties: false,
            },
          },
        },
        required: ["titulo", "unidade", "barras"],
        additionalProperties: false,
      },
      deals: {
        type: "array",
        maxItems: 10,
        description: "Códigos dos deals citados na resposta, na ordem de prioridade. A tela monta a tabela a partir dos dados.",
        items: { type: "string" },
      },
      acoes: { type: "array", maxItems: 4, description: "Ações concretas derivadas dos dados (ex.: revisar o deal X).", items: { type: "string" } },
      proximas_perguntas: {
        type: "array",
        maxItems: 3,
        description: "Até 3 perguntas de aprofundamento que o usuário pode clicar, todas sobre os dados da Régua.",
        items: { type: "string" },
      },
    },
    required: ["resposta", "destaques", "deals", "acoes", "proximas_perguntas"],
    additionalProperties: false,
  },
};

export function runDataTool(name: string, input: unknown): { content: string; isError: boolean } {
  if (!(name in schemas)) return { content: `Ferramenta desconhecida: ${name}`, isError: true };
  const key = name as ToolName;
  const parsed = schemas[key].safeParse(input ?? {});
  if (!parsed.success) return { content: `Entrada inválida: ${parsed.error.issues[0]?.message}`, isError: true };
  // O cast une os pares schema/handler, que o TypeScript não correlaciona sozinho.
  const result = (handlers[key] as (i: unknown) => unknown)(parsed.data);
  return { content: JSON.stringify(result), isError: false };
}
