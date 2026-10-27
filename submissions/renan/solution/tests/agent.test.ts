import { describe, expect, it } from "vitest";
import { POST } from "@/app/api/agente/route";
import { KEY_HEADER } from "@/lib/agent/config";
import { DATA_TOOLS, runDataTool } from "@/lib/agent/tools";
import { buildInsights } from "@/lib/agent/insights";
import { history, pipeline } from "@/lib/pipeline";

const parse = (name: string, input: unknown) => {
  const { content, isError } = runDataTool(name, input);
  return { data: JSON.parse(isError ? "null" : content), isError, content };
};

describe("ferramentas de dados do agente", () => {
  it("toda ferramenta declarada tem implementação", () => {
    for (const tool of DATA_TOOLS) {
      expect(runDataTool(tool.name, {}).content).not.toMatch(/Ferramenta desconhecida/);
    }
  });

  it("detalhe_deal devolve os números do motor de score", () => {
    const top = pipeline[0];
    const { data } = parse("detalhe_deal", { id: top.deal.id.toLowerCase() });
    expect(data.id).toBe(top.deal.id);
    expect(data.valor_esperado_usd).toBe(Math.round(top.expectedValue));
    expect(data.fatores_da_chance.length).toBeGreaterThan(0);
  });

  it("resumo_vendedor recusa vendedor inexistente", () => {
    const { isError, content } = parse("resumo_vendedor", { vendedor: "Fulano Inventado" });
    expect(isError).toBe(true);
    expect(content).toMatch(/vendedor não existe/);
  });

  it("fila_parados só traz deals parados, do maior valor para o menor", () => {
    const { data } = parse("fila_parados", { limite: 5 });
    expect(data.maiores).toHaveLength(5);
    expect(data.maiores.every((d: { momento: string }) => d.momento === "Parado")).toBe(true);
    const prices = data.maiores.map((d: { preco_tabela_usd: number }) => d.preco_tabela_usd);
    expect(prices).toEqual([...prices].sort((a: number, b: number) => b - a));
  });

  it("ferramenta desconhecida vira erro, não exceção", () => {
    expect(runDataTool("apagar_tudo", {}).isError).toBe(true);
  });
});

describe("rota /api/agente", () => {
  const body = { mensagens: [{ papel: "vendedor", texto: "Oi" }], modelo: "claude-opus-5-5", esforco: "medium" };

  it("exige a chave do próprio usuário", async () => {
    const response = await POST(new Request("http://x/api/agente", { method: "POST", body: JSON.stringify(body) }));
    expect(response.status).toBe(401);
  });

  it("rejeita modelo fora da lista", async () => {
    const response = await POST(
      new Request("http://x/api/agente", {
        method: "POST",
        headers: { [KEY_HEADER]: "sk-ant-teste" },
        body: JSON.stringify({ ...body, modelo: "gpt-qualquer" }),
      }),
    );
    expect(response.status).toBe(400);
  });
});

describe("radar", () => {
  it("avisa sobre deals prestes a passar do maior ciclo, com números reais", () => {
    const insights = buildInsights();
    const cooling = insights.find((i) => i.id === "esfriando");
    const expected = pipeline.filter((s) => s.momentum !== "stalled" && s.daysOpen !== null && s.daysOpen > history.maxCycle - 14).length;
    expect(cooling?.title).toContain(String(expected));
    expect(insights.every((i) => i.question.length > 0 && i.href.startsWith("/"))).toBe(true);
  });

  it("respeita o recorte por vendedor e não ranqueia vendedores dentro dele", () => {
    const agent = pipeline[0].deal.agent;
    const insights = buildInsights({ agent });
    expect(insights.some((i) => i.id === "higiene")).toBe(false);
    expect(insights.every((i) => !i.title.includes("time"))).toBe(true);
  });

  it("fica disponível para o agente como ferramenta", () => {
    expect(parse("radar", {}).data.length).toBeGreaterThan(0);
  });
});
