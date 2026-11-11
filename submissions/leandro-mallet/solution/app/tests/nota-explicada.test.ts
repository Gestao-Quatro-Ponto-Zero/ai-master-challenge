// O-36 — "Por que a nota é N": conta numa linha, barra empilhada, motivos com ícone e componentes em linhas.
import { describe, expect, it } from "vitest";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { NotaExplicada } from "@/components/NotaExplicada";
import { contaDaNota, contribuicoes, itensDoFit, itensDoGrupo, pontosDoItem, valorDoItemFit } from "@/lib/explicacaoNota";
import type { Componente } from "@/lib/tipos";

// Os dados reais do lead do print (GTX Plus Pro): FIT 66, HEAT 10, BONUS 5, nota 54.
const COMP: Componente[] = [
  { grupo: "bonus", nome: "Histórico da empresa", pontos: 5, maximo: 10 },
  { grupo: "bonus", nome: "Janela de compra", pontos: 0, maximo: 10 },
  { grupo: "fit", nome: "Desvio: receita pequena", pontos: 5.46, maximo: 10.92 },
  { grupo: "fit", nome: "Desvio: produto GTX Plus Pro", pontos: -4.93, maximo: 10.92 },
  { grupo: "fit", nome: "Encaixe com o vendedor (70%)", pontos: 46.21, maximo: 70 },
  { grupo: "heat", nome: "Faixa: 91 a 180 dias", pontos: 10, maximo: 100 },
  { grupo: "heat", nome: "Tempo de atendimento (30%)", pontos: 3, maximo: 30 },
];
const MOTIVOS = ["Encaixa no seu destaque: sede fora dos EUA.", "Parado há 139 dias.", "Empresa no terço do meio em compras: +5."];

describe("explicação da nota", () => {
  it("a conta numa linha e quanto cada parte soma", () => {
    expect(contaDaNota(66, 10, 5, 54)).toBe("0,7 × 66 + 0,3 × 10 + 5 = 54");
    const c = contribuicoes(66, 10, 5);
    expect(c.fit).toBeCloseTo(46.2);
    expect(c.heat).toBeCloseTo(3);
    expect(c.bonus).toBe(5);
  });

  it("os itens de cada componente não repetem a linha de contribuição; pontos com o máximo", () => {
    expect(itensDoGrupo(COMP, "fit").map((c) => c.nome)).toEqual(["Desvio: receita pequena", "Desvio: produto GTX Plus Pro"]);
    expect(itensDoGrupo(COMP, "heat").map((c) => c.nome)).toEqual(["Faixa: 91 a 180 dias"]);
    expect(pontosDoItem({ pontos: 5.46, maximo: 10.92 })).toBe("5,5 / 10,9");
    expect(pontosDoItem({ pontos: 0, maximo: 10 })).toBe("0 / 10");
    expect(pontosDoItem({ pontos: -4.93, maximo: 10.92 })).toBe("−4,9 / 10,9");
  });

  it("render: conta, barra empilhada com legenda, motivos com ícone do grupo e componentes em linhas", () => {
    const h = renderToStaticMarkup(createElement(NotaExplicada, { nota: 54, fit: 66, heat: 10, bonus: 5, componentes: COMP, motivos: MOTIVOS, grupos: ["fit", "heat", "bonus"] }));
    expect(h).toContain("0,7 × 66 + 0,3 × 10 + 5 = 54");
    expect(h).toContain('aria-label="Nota 54: FIT soma 46,2, HEAT soma 3 e BONUS soma 5, numa escala até 120."');
    for (const cor of ["bg-marinho", "bg-dourado-medio", "bg-bronze-escuro"]) expect(h).toContain(cor);
    expect(h).toContain("Performance do vendedor neste perfil (FIT)");
    expect(h).toContain(">66%<");
    expect(h).toContain("peso 70%");
    expect(h).toContain("peso 30%");
    expect(h).toContain("5,5 / 10,9");
    // texto do item quebra linha, nunca corta; pontos à direita sem quebrar
    expect(h).toContain('class="min-w-0 break-words">Desvio: produto GTX Plus Pro');
    expect(h).not.toMatch(/truncate/);
    // motivos sem bolinha: ícone do grupo
    expect(h).not.toContain("list-disc");
    expect(h).toContain("<svg");
    // sem caixas lado a lado
    expect(h).not.toContain("grid-cols-3");
  });
});

// O-52 — FIT absoluto (O-51 da #3): o FIT é a conversão do vendedor no perfil do lead; cada característica traz a
// conversão dela (máximo 100) e as que ficaram fora da conta vêm sem máximo ("poucos casos").
const COMP_ABS: Componente[] = [
  { grupo: "fit", nome: "Encaixe com o vendedor (70%)", pontos: 43.4, maximo: 70 },
  { grupo: "fit", nome: "Setor finanças", pontos: 65, maximo: 100 },
  { grupo: "fit", nome: "Sede fora dos EUA", pontos: 4, maximo: null },
  { grupo: "fit", nome: "Produto GTX Plus Pro", pontos: 59.04, maximo: 100 },
  { grupo: "heat", nome: "Faixa: 91 a 180 dias", pontos: 10, maximo: 100 },
];

describe("FIT absoluto na explicação (O-52)", () => {
  it("cada característica em %, as fora da conta como 'poucos casos', depois das que contam", () => {
    expect(itensDoFit(COMP_ABS).map((c) => [c.nome, valorDoItemFit(c)])).toEqual([
      ["Setor finanças", "65%"],
      ["Produto GTX Plus Pro", "59%"],
      ["Sede fora dos EUA", "poucos casos"],
    ]);
    // o formato antigo (antes da carga nova) continua legível
    expect(valorDoItemFit({ pontos: 5.46, maximo: 10.92 })).toBe("5,5 / 10,9");
  });

  it("render: cabeçalho 'Performance do vendedor neste perfil (FIT)' com o valor em %, sem desvio nem destaque", () => {
    const h = renderToStaticMarkup(createElement(NotaExplicada, { nota: 51, fit: 62, heat: 10, bonus: 5, componentes: COMP_ABS, motivos: [], grupos: [] }));
    expect(h).toContain("Performance do vendedor neste perfil (FIT)");
    expect(h).toContain(">62%<");
    expect(h).toContain(">65%<");
    expect(h).toContain("poucos casos");
    expect(h).not.toMatch(/Desvio|destaque/i);
    expect(h.indexOf("Produto GTX Plus Pro")).toBeLessThan(h.indexOf("Sede fora dos EUA"));
  });
});
