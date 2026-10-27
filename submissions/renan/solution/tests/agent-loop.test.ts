import { beforeEach, describe, expect, it, vi } from "vitest";

/*
 * Teste de ponta a ponta do agente sem chave e sem rede: o cliente da Anthropic
 * é trocado por um mock que devolve respostas roteirizadas, e as classes de erro
 * reais do SDK são mantidas para testar o tratamento de erros.
 */
const create = vi.fn();

vi.mock("@anthropic-ai/sdk", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@anthropic-ai/sdk")>();
  class MockAnthropic extends actual.default {
    constructor(options: ConstructorParameters<typeof actual.default>[0]) {
      super(options);
      Object.defineProperty(this, "beta", { value: { messages: { create } } });
    }
  }
  return { ...actual, default: MockAnthropic };
});

const { default: Anthropic } = await import("@anthropic-ai/sdk");
const { POST } = await import("@/app/api/agente/route");
const { KEY_HEADER } = await import("@/lib/agent/config");
const { findDeal } = await import("@/lib/pipeline");

const toolUse = (id: string, name: string, input: unknown) => ({
  stop_reason: "tool_use",
  content: [{ type: "tool_use", id, name, input }],
});

function ask(body: Record<string, unknown> = {}) {
  return POST(
    new Request("http://localhost/api/agente", {
      method: "POST",
      headers: { "content-type": "application/json", [KEY_HEADER]: "chave-de-teste" },
      body: JSON.stringify({
        mensagens: [{ papel: "vendedor", texto: "O que a Rosalina deve atacar hoje?" }],
        modelo: "claude-opus-5-5",
        esforco: "medium",
        ...body,
      }),
    }),
  );
}

beforeEach(() => create.mockReset());

describe("loop do agente com API simulada", () => {
  it("consulta a ferramenta, responde em formato de painel e monta os deals a partir do motor", async () => {
    create
      .mockResolvedValueOnce(toolUse("t1", "resumo_vendedor", { vendedor: "Rosalina Dieter" }))
      .mockResolvedValueOnce(
        toolUse("t2", "responder", {
          resposta: "Comece pelo GTK 500.",
          destaques: [{ rotulo: "Valor esperado", valor: "US$ 18.948" }],
          deals: ["1LY8CAXD", "1ly8caxd", "NAOEXISTE"],
          acoes: ["Empurrar o fechamento do 1LY8CAXD"],
          proximas_perguntas: ["Quais parados da Rosalina revisar?"],
        }),
      );

    const response = await ask();
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.resposta).toBe("Comece pelo GTK 500.");
    expect(data.ferramentas).toEqual(["resumo_vendedor"]);
    expect(data.proximasPerguntas).toEqual(["Quais parados da Rosalina revisar?"]);
    // Código inexistente descartado; os valores vêm do motor, não do texto do modelo.
    expect(data.deals).toHaveLength(1);
    const engine = findDeal("1LY8CAXD")!;
    expect(data.deals[0]).toMatchObject({ id: "1LY8CAXD", produto: engine.deal.product, valorEsperado: engine.expectedValue });

    // A 2ª chamada levou o resultado real da ferramenta de volta ao modelo.
    const second = create.mock.calls[1][0];
    const toolResult = second.messages.at(-1).content[0];
    expect(toolResult.type).toBe("tool_result");
    expect(JSON.parse(toolResult.content).escopo).toBe("Rosalina Dieter");
  });

  it("envia o pedido restrito aos dados: sem busca web, com fallback de recusa no Opus", async () => {
    create.mockResolvedValueOnce(toolUse("t1", "responder", { resposta: "ok", destaques: [], deals: [], acoes: [], proximas_perguntas: [] }));
    await ask({ esforco: "high" });
    const params = create.mock.calls[0][0];

    expect(params.model).toBe("claude-opus-5-5");
    expect(params.output_config).toEqual({ effort: "high" });
    expect(params.fallbacks).toBe("default");
    expect(params.tools.some((t: { name: string }) => t.name === "web_search")).toBe(false);
    expect(params.system).toMatch(/regra absoluta/);
  });

  it("no Haiku não envia fallback (não suportado)", async () => {
    create.mockResolvedValueOnce(toolUse("t1", "responder", { resposta: "ok", destaques: [], deals: [], acoes: [], proximas_perguntas: [] }));
    await ask({ modelo: "claude-haiku-5-5" });
    const params = create.mock.calls[0][0];
    expect(params.fallbacks).toBeUndefined();
    expect(params.betas).toBeUndefined();
  });

  it("chave recusada vira 401 com mensagem para o usuário", async () => {
    create.mockRejectedValueOnce(Object.create(Anthropic.AuthenticationError.prototype));
    const response = await ask();
    expect(response.status).toBe(401);
    expect((await response.json()).erro).toMatch(/chave da API foi recusada/);
  });

  it("limite de uso vira 429", async () => {
    create.mockRejectedValueOnce(Object.create(Anthropic.RateLimitError.prototype));
    expect((await ask()).status).toBe(429);
  });

  it("recusa do modelo vira 422", async () => {
    create.mockResolvedValueOnce({ stop_reason: "refusal", content: [] });
    expect((await ask()).status).toBe(422);
  });

  it("se o modelo responder em texto sem a ferramenta, mostra o texto", async () => {
    create.mockResolvedValueOnce({ stop_reason: "end_turn", content: [{ type: "text", text: "Posso analisar o pipeline." }] });
    const data = await (await ask()).json();
    expect(data.resposta).toBe("Posso analisar o pipeline.");
    expect(data.deals).toEqual([]);
  });

  it("para depois do limite de iterações em vez de rodar para sempre", async () => {
    create.mockResolvedValue(toolUse("t", "fatos_metodologia", {}));
    const response = await ask();
    expect(response.status).toBe(504);
    expect(create).toHaveBeenCalledTimes(8);
  });

  it("resposta incompleta do modelo vira erro claro", async () => {
    create.mockResolvedValueOnce(toolUse("t1", "responder", { destaques: [] }));
    expect((await ask()).status).toBe(502);
  });
});
