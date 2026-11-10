// O-32 — bloco Prioridades no padrão escuro, item fino e clique que abre o racional da nota.
import { describe, expect, it, vi } from "vitest";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type { DealVisao, Prioridade } from "@/lib/tipos";

vi.mock("next/link", () => ({
  default: ({ href, children, ...resto }: { href: string; children: unknown }) => createElement("a", { href, ...resto }, children as never),
}));

const deal = (x: Partial<DealVisao> = {}): DealVisao => ({
  id: "B0000001", nome: "Streethex · MG Advanced", estagio: "Prospecting", vendedor: "Anna Snelling", manager: "Dustin Brinkmann", regiao: "Central",
  produto: "MG Advanced", serie: "MG", preco: 3393, conta: "Streethex", setor: "retail", porte: "pequena", contato: null,
  dataAbertura: null, diasDesdeAbertura: null, ultimoContato: null, closeDate: null, closeValue: null, motivoPerda: null,
  fit: 80, heat: 50, bonus: 5, score: 70, faixaNota: "alta", acaoSugerida: "focar", marcadores: [], valorEsperado: 3393,
  valorPeloPrecoDeTabela: false, icone: null, tags: [], qtdComentarios: 0, atualizadoDepoisDaNota: false, criadoEm: null,
  atualizadoEm: "2026-11-10T00:00:00Z", ...x,
});
const item = (x: Partial<Prioridade> = {}): Prioridade => ({ posicao: 1, deal: deal(), marcada: null, puladoDiasSeguidos: 0, motivo: "Encaixa no destaque do vendedor.", atendimentoAtrasado: false, ...x });

async function html(itens: Prioridade[]) {
  const { Prioridades } = await import("@/components/Prioridades");
  return renderToStaticMarkup(createElement(Prioridades, { itens, papel: "vendedor", somenteLeitura: false }));
}

describe("Prioridades no escuro (O-32)", () => {
  it("fundo do deck, título claro, contador e nota em dourado, itens separados por fio dourado", async () => {
    const h = await html([item(), item({ deal: deal({ id: "B0000002", nome: "Nam-zim · MG Special", produto: "MG Special", score: 69 }) })]);
    expect(h).toContain("fundo-escuro");
    expect(h).toContain("text-claro");
    expect(h).toContain("text-ouro");
    expect(h).toContain("border-fio-ouro");
    expect(h).not.toContain("rounded-cartao border border-linha");
  });

  it("item fino: nome · produto e nota na mesma linha; motivo não aparece aberto (só no título do link)", async () => {
    const h = await html([item()]);
    expect(h).toContain("Streethex · MG Advanced");
    expect(h).toContain('aria-label="Nota 70"');
    expect(h).not.toMatch(/<p[^>]*>Encaixa no destaque do vendedor\.<\/p>/);
    expect(h).toContain('title="Ver por que a nota é 70. Encaixa no destaque do vendedor."');
  });

  it("nome próprio sem o produto ganha o produto ao lado", async () => {
    expect(await html([item({ deal: deal({ nome: "Renovação anual" }) })])).toContain("Renovação anual · MG Advanced");
  });

  it("clique no lead abre o deal na parte da nota; ✓ e ✕ ficam fora do link", async () => {
    const h = await html([item()]);
    expect(h).toContain('href="/painel?deal=B0000001&amp;secao=nota"');
    const link = h.slice(h.indexOf("<a "), h.indexOf("</a>"));
    expect(link).not.toContain("<button");
    expect(h).toContain('aria-label="Feito: Streethex · MG Advanced"');
    expect(h).toContain('aria-label="Pular hoje: Streethex · MG Advanced"');
    expect(h).toContain("bg-ouro");
    expect(h).toContain("border-fio-ouro");
  });

  it("linha pequena com valor, dias e alerta", async () => {
    const h = await html([item({ deal: deal({ icone: "em_risco", diasDesdeAbertura: 120 }), atendimentoAtrasado: true })]);
    expect(h).toContain("R$ 3.393");
    expect(h).toContain("há 120 dias");
    expect(h).toContain("Em risco de esfriar");
    expect(h).toContain("Atendimento atrasado");
  });
});

describe("20 por dia, todos à mostra (O-34)", () => {
  const vinte = Array.from({ length: 20 }, (_, i) =>
    item({
      posicao: i + 1,
      deal: deal({ id: `B${String(i).padStart(7, "0")}`, nome: `Lead ${i + 1} · MG Advanced`, score: 90 - i }),
      marcada: i === 0 ? "feita" : i === 1 ? "pulada" : null,
    }),
  );

  it("mostra os 20, sem fila nem 'puxar mais'; contador X de 20", async () => {
    const h = await html(vinte);
    for (let i = 1; i <= 20; i++) expect(h).toContain(`Lead ${i} · MG Advanced`);
    expect(h).not.toContain("Próximos");
    expect(h).not.toContain("Puxar mais");
    expect(h).toMatch(/>1<\/span> de 20 feitas/);
  });

  it("o marcado fica na lista, esmaecido, com o estado e sem os botões", async () => {
    const h = await html(vinte);
    expect(h).toContain("opacity-60");
    expect(h).toContain(">Feito<");
    expect(h).toContain(">Pulado<");
    expect(h).not.toContain('aria-label="Feito: Lead 1 · MG Advanced"');
    expect(h).not.toContain('aria-label="Pular hoje: Lead 2 · MG Advanced"');
    expect(h).toContain('aria-label="Feito: Lead 3 · MG Advanced"');
  });

  it("reserva em memória: a lista do dia tem 20 e não anda depois do ✕", async () => {
    delete process.env.SUPABASE_URL;
    delete process.env.SUPABASE_SERVICE_ROLE_KEY;
    process.env.G4_ESCRITA_EM_MEMORIA = "1";
    (globalThis as { __g4Estado?: unknown }).__g4Estado = undefined;
    const r = await import("@/server/repositorio");
    const anna = (await r.listarUsuarios()).find((u) => u.nome === "Anna Snelling")!;
    const antes = await r.prioridadesDoDia(anna);
    expect(antes).toHaveLength(20);
    await r.marcarPrioridade(anna, antes[0]!.deal.id, "pulada");
    const depois = await r.prioridadesDoDia(anna);
    expect(depois.map((p) => p.deal.id)).toEqual(antes.map((p) => p.deal.id));
    expect(depois[0]!.marcada).toBe("pulada");
  });
});

describe("ordem dos itens marcados (O-34)", () => {
  it("os que faltam fazer vêm primeiro; os marcados descem, na ordem da nota", async () => {
    const lista = [
      item({ posicao: 1, deal: deal({ id: "M0000001", nome: "Primeiro · MG Advanced" }), marcada: "feita" }),
      item({ posicao: 2, deal: deal({ id: "M0000002", nome: "Segundo · MG Advanced" }) }),
      item({ posicao: 3, deal: deal({ id: "M0000003", nome: "Terceiro · MG Advanced" }), marcada: "pulada" }),
      item({ posicao: 4, deal: deal({ id: "M0000004", nome: "Quarto · MG Advanced" }) }),
    ];
    const h = await html(lista);
    const pos = (t: string) => h.indexOf(t);
    expect(pos("Segundo")).toBeLessThan(pos("Quarto"));
    expect(pos("Quarto")).toBeLessThan(pos("Primeiro"));
    expect(pos("Primeiro")).toBeLessThan(pos("Terceiro"));
  });
});

describe("barra de nota fina no item (adendo à O-36)", () => {
  it("barra de 3 px na 2ª linha, dourada sobre trilho translúcido; sem nota, sem barra", async () => {
    const h = await html([item()]);
    expect(h).toContain("data-barra-nota");
    expect(h).toContain("h-[3px]");
    expect(h).toContain("bg-trilho-escuro");
    expect(h).toContain('aria-label="Nota 70 de 120"');
    expect(h).toContain("width:58.333");
    expect(await html([item({ deal: deal({ score: null, faixaNota: null }) })])).not.toContain("data-barra-nota");
  });
});
