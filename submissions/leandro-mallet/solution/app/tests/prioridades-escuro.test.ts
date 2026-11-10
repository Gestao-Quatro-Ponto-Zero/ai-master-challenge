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
