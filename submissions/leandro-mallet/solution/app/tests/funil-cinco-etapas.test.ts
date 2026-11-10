// O-31 — funil com 5 etapas: Novo lead, Atendimento, Em negociação, Fechado e Perdido.
// Novo lead e Atendimento são o Prospecting sem e com contato registrado; o primeiro contato muda a etapa sozinho.
import { beforeEach, describe, expect, it } from "vitest";
import { destinosDe, etapaDe, rotularLinhaDoTempo, rotuloDestino, rotuloDoDeal } from "@/lib/etapas";
import { interpretar } from "@/lib/filtro/interpretar";
import { funil } from "@/lib/painel";
import type { DealVisao, EventoLinhaDoTempo, Usuario } from "@/lib/tipos";

const deal = (x: Partial<DealVisao>) => ({ estagio: "Prospecting", ultimoContato: null, closeValue: null, preco: 100, valorEsperado: 80, ...x }) as DealVisao;

describe("etapa do deal", () => {
  it("Prospecting sem contato = Novo lead; com contato = Atendimento; os demais pelo estágio", () => {
    expect(etapaDe(deal({}))).toBe("novo");
    expect(etapaDe(deal({ ultimoContato: "2017-12-30" }))).toBe("atendimento");
    expect(etapaDe(deal({ estagio: "Engaging", ultimoContato: null }))).toBe("negociacao");
    expect(etapaDe(deal({ estagio: "Won" }))).toBe("fechado");
    expect(etapaDe(deal({ estagio: "Lost" }))).toBe("perdido");
    expect(rotuloDoDeal(deal({ estagio: "Won" }))).toBe("Fechado");
  });

  it("destinos: Atendimento só para Novo lead; nunca volta para Novo lead; reabrir é de manager e admin", () => {
    expect(destinosDe("novo", "vendedor")).toEqual(["atendimento", "negociacao", "perdido"]);
    expect(destinosDe("atendimento", "vendedor")).toEqual(["negociacao", "perdido"]);
    expect(destinosDe("negociacao", "vendedor")).toEqual(["fechado", "perdido"]);
    expect(destinosDe("fechado", "vendedor")).toEqual([]);
    expect(destinosDe("perdido", "manager")).toEqual(["negociacao"]);
    for (const e of ["novo", "atendimento", "negociacao", "fechado", "perdido"] as const) expect(destinosDe(e, "admin")).not.toContain("novo");
    expect(rotuloDestino("novo", "atendimento")).toBe("Registrar atendimento");
    expect(rotuloDestino("atendimento", "perdido")).toBe("Descartar (Perdido)");
  });
});

describe("funil do Painel", () => {
  it("5 barras na ordem, com Perdido no fim; valores por etapa", () => {
    const barras = funil([
      deal({}),
      deal({ ultimoContato: "2017-12-30" }),
      deal({ estagio: "Engaging" }),
      deal({ estagio: "Won", closeValue: 300 }),
      deal({ estagio: "Lost", preco: 55 }),
    ]);
    expect(barras.map((b) => [b.etapa, b.quantidade, b.valor])).toEqual([
      ["novo", 1, 80],
      ["atendimento", 1, 80],
      ["negociacao", 1, 80],
      ["fechado", 1, 300],
      ["perdido", 1, 55],
    ]);
  });
});

describe("linha do tempo com as etapas", () => {
  const ev = (descricao: string, tipo: EventoLinhaDoTempo["tipo"] = "estagio", desfeito = false) => ({ tipo, descricao, desfeito });
  it("Prospecção vira Novo lead antes do primeiro contato e Atendimento depois; Ganho vira Fechado", () => {
    const l = rotularLinhaDoTempo([
      ev("Cadastrado no CRM", "criado"),
      ev("Liguei", "acao", true),
      ev("Estágio: Prospecção → Perdido"),
      ev("Estágio: Perdido → Em negociação"),
      ev('Atendimento: Ligação — "Pediu a proposta."', "acao"),
      ev("Estágio: Prospecção → Em negociação"),
      ev("Estágio: Em negociação → Ganho (R$ 3.300)"),
      ev("Ganho: R$ 3.300", "fechado"),
    ]).map((e) => e.descricao);
    expect(l[2]).toBe("Estágio: Novo lead → Perdido");
    expect(l[5]).toBe("Estágio: Atendimento → Em negociação");
    expect(l[6]).toBe("Estágio: Em negociação → Fechado (R$ 3.300)");
    expect(l[7]).toBe("Fechado: R$ 3.300");
  });
});

describe("filtro livre com os nomes novos", () => {
  const ctx = { modo: "leads", papel: "vendedor", vendedores: [], managers: [], regioes: [], produtos: [], series: [], empresas: [], setores: [], tags: [], sedes: [], hoje: "2017-12-31" } as unknown as Parameters<typeof interpretar>[1];
  const rotulos = (t: string) => interpretar(t, ctx).etiquetas.map((e) => e.rotulo);
  it("novo lead, atendimento e fechado", () => {
    expect(rotulos("novos leads")).toContain("Estágio: Novo lead");
    expect(rotulos("em atendimento")).toContain("Estágio: Atendimento");
    expect(rotulos("fechados")).toContain("Estágio: Fechado");
    expect(rotulos("ganhos em 2017")).toContain("Estágio: Fechado");
    expect(interpretar("atendimento", ctx).etiquetas[0]).toMatchObject({ chave: "etapas", valor: ["atendimento"] });
  });
});

describe("Pipeline e registro de atendimento (reserva em memória)", () => {
  const g = globalThis as { __g4Estado?: unknown };
  beforeEach(() => {
    delete process.env.SUPABASE_URL;
    delete process.env.SUPABASE_SERVICE_ROLE_KEY;
    delete process.env.G4_SOMENTE_LEITURA;
    process.env.G4_ESCRITA_EM_MEMORIA = "1";
    g.__g4Estado = undefined;
  });
  const repo = () => import("@/server/repositorio");
  const anna = async (): Promise<Usuario> => (await (await repo()).listarUsuarios()).find((u) => u.nome === "Anna Snelling")!;

  it("5 colunas; o primeiro contato registrado leva o lead de Novo lead para Atendimento", async () => {
    const { colunasPipeline, escopoDe, registrarAtendimento, buscarDeals } = await repo();
    const u = await anna();
    const antes = await colunasPipeline(escopoDe(u), {}, "nota", 5);
    expect(antes.map((c) => c.etapa)).toEqual(["novo", "atendimento", "negociacao", "fechado", "perdido"]);
    const novo = antes[0]!.cartoes[0]!;
    const totalNovo = antes[0]!.total;

    await expect(registrarAtendimento(u, novo.id, "ligacao", "   ")).rejects.toMatchObject({ codigo: "GS400" });
    await registrarAtendimento(u, novo.id, "ligacao", "Pediu a proposta.");

    const depois = await colunasPipeline(escopoDe(u), {}, "nota", 500);
    expect(depois[0]!.total).toBe(totalNovo - 1);
    expect(depois[1]!.cartoes.map((d) => d.id)).toContain(novo.id);
    // o filtro "atendimento" acha o lead
    const filtrado = await buscarDeals(escopoDe(u), { etapas: ["atendimento"] }, "padrao_leads");
    expect(filtrado.linhas.map((d) => d.id)).toContain(novo.id);
  });

  it("não registra atendimento em deal encerrado", async () => {
    const { colunasPipeline, escopoDe, registrarAtendimento } = await repo();
    const u = await anna();
    const fechado = (await colunasPipeline(escopoDe(u), {}, "nota", 1)).find((c) => c.etapa === "fechado")!.cartoes[0]!;
    await expect(registrarAtendimento(u, fechado.id, "ligacao", "Pós-venda.")).rejects.toMatchObject({ codigo: "GS422" });
  });
});
