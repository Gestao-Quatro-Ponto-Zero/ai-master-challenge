// O-28 — objetos da interface (src/components/ui): um conjunto só para todas as telas.
import { describe, expect, it } from "vitest";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { BarraNota } from "@/components/ui/BarraNota";
import { Botao, classeBotao } from "@/components/ui/Botao";
import { classeCampo } from "@/components/ui/Campo";
import { Etiqueta } from "@/components/ui/Etiqueta";
import { Seletor } from "@/components/ui/Seletor";
import { Marcador } from "@/components/ui/Superficie";
import { IconeDeal } from "@/components/Nota";

const html = (el: Parameters<typeof renderToStaticMarkup>[0]) => renderToStaticMarkup(el);

describe("botão em 3 níveis", () => {
  it("mesma altura e raio nos três níveis; só o fundo e a borda mudam", () => {
    const [p, s, d] = (["primario", "secundario", "discreto"] as const).map((n) => classeBotao(n));
    for (const c of [p, s, d]) expect(c).toMatch(/\bh-10\b.*rounded-controle|rounded-controle.*\bh-10\b/);
    expect(p).toContain("bg-marinho");
    expect(s).toContain("border-borda");
    expect(s).not.toContain("dourado");
    expect(d).toContain("bg-transparent");
    expect(classeBotao("primario", "compacto")).toContain("h-8");
  });

  it("ícone em SVG, nada de glifo", () => {
    const h = html(createElement(Botao, { nivel: "primario", icone: "check" }, "Feito"));
    expect(h).toContain("<svg");
    expect(h).not.toMatch(/[✓✗×]/);
  });
});

describe("campo e seletor", () => {
  it("campo com a altura do botão e borda neutra em repouso", () => {
    expect(classeCampo()).toContain("h-10");
    expect(classeCampo()).toContain("border-borda");
    expect(classeCampo()).not.toContain("dourado");
  });

  it("seletor estilizado: botão com listbox, rótulo para leitor de tela e sem <select> nativo", () => {
    const h = html(createElement(Seletor, { rotulo: "Ordenar", valor: "nota", onMudar: () => {}, opcoes: [{ valor: "nota", rotulo: "Nota" }, { valor: "valor", rotulo: "Valor" }] }));
    expect(h).not.toContain("<select");
    expect(h).toContain('aria-haspopup="listbox"');
    expect(h).toContain('aria-expanded="false"');
    expect(h).toContain('aria-label="Ordenar: Nota"');
    expect(h).toContain("h-10");
  });

  it("modo ação (troca de estágio no cartão): compacto e mostra o estágio atual", () => {
    const h = html(createElement(Seletor, { acao: true, tamanho: "compacto", rotulo: "Estágio", textoVazio: "Prospecção", valor: "", onMudar: () => {}, opcoes: [{ valor: "Engaging", rotulo: "Mover para Em negociação" }] }));
    expect(h).toContain("Prospecção");
    expect(h).toContain("h-8");
  });
});

describe("etiqueta: uma forma, tom por significado", () => {
  it("cada tom tem fundo e texto próprios, na mesma forma", () => {
    const tons = ["neutro", "atencao", "negativo", "positivo", "destaque"] as const;
    const hs = tons.map((t) => html(Etiqueta({ tom: t, children: "x" })));
    tons.forEach((t, i) => expect(hs[i]).toContain(`bg-tom-${t}`));
    for (const h of hs) expect(h).toContain("h-6");
  });

  it("ícones do deal: super hot = destaque com ícone e texto; em risco = atenção; esfriou = negativo", () => {
    const quente = html(createElement(IconeDeal, { icone: "super_hot", dias: 40 }));
    expect(quente).toContain("bg-tom-destaque");
    expect(quente).toContain("<svg");
    expect(quente).toContain("Super hot");
    expect(html(createElement(IconeDeal, { icone: "em_risco", dias: 120 }))).toContain("bg-tom-atencao");
    expect(html(createElement(IconeDeal, { icone: "esfriou", dias: 200 }))).toContain("bg-tom-negativo");
  });
});

describe("barra de nota única", () => {
  it("fina, cor pela faixa, número em Manrope 600 com algarismos tabulares", () => {
    const h = html(createElement(BarraNota, { score: 70, faixa: "alta" }));
    expect(h).toContain("h-1.5");
    expect(h).toContain("bg-nota-alta");
    expect(h).toContain("font-texto");
    expect(h).toContain("font-semibold");
    expect(h).toContain("tabular-nums");
    expect(h).not.toContain("font-titulo");
    expect(h).toContain('aria-label="Nota 70, faixa alta"');
    expect(html(createElement(BarraNota, { score: 45, faixa: "media" }))).toContain("bg-nota-media");
    expect(html(createElement(BarraNota, { score: null, faixa: null }))).toContain("Sem nota ainda");
  });
});

describe("caixa de marcar da tabela", () => {
  it("continua sendo um checkbox (teclado e leitor de tela), com aparência própria", () => {
    const h = html(createElement(Marcador, { checked: true, onChange: () => {}, rotulo: "Selecionar Hottechi" }));
    expect(h).toContain('type="checkbox"');
    expect(h).toContain("appearance-none");
    expect(h).toContain('aria-label="Selecionar Hottechi"');
  });
});

describe("cartão de número do Painel (O-30)", () => {
  it("faixa e ícone na cor do grupo; número grande em Manrope bold; destaque com número dourado", async () => {
    const { CartaoNumero } = await import("@/components/ui/CartaoNumero");
    const leads = html(createElement(CartaoNumero, { grupo: "leads", icone: "pessoas", rotulo: "Leads hoje", valor: "8" }));
    expect(leads).toContain("bg-grupo-leads");
    expect(leads).toContain("text-numero");
    expect(leads).toContain("whitespace-nowrap");
    expect(leads).toContain("font-bold");
    expect(leads).toContain("rounded-numero");
    expect(html(createElement(CartaoNumero, { grupo: "fechamento", icone: "trofeu", rotulo: "Fechamentos", valor: "2" }))).toContain("bg-grupo-fechamento");
    const total = html(createElement(CartaoNumero, { destaque: true, grupo: "leads", icone: "pessoas", rotulo: "Total de leads", valor: "449" }));
    expect(total).toContain("text-numero-dourado");
    expect(total).toContain("from-creme-1");
  });

  it("pílula de variação: verde quando sobe, vermelha quando cai, seta em SVG", async () => {
    const { PilulaVariacao } = await import("@/components/ui/CartaoNumero");
    const sobe = html(createElement(PilulaVariacao, { variacao: { texto: "↑ 18% vs 30 dias antes", sobe: true } }));
    expect(sobe).toContain("bg-tom-positivo");
    expect(sobe).toContain("<svg");
    expect(sobe).toContain("18% vs 30 dias antes");
    expect(sobe).not.toContain("↑");
    expect(html(createElement(PilulaVariacao, { variacao: { texto: "↓ 62%", sobe: false } }))).toContain("bg-tom-negativo");
    expect(html(createElement(PilulaVariacao, { variacao: null }))).toContain("sem base para comparar");
  });
});

describe("moeda em reais (adendo à O-30)", () => {
  it("um formatador só: R$ com os mesmos números, sem conversão", async () => {
    const { dinheiro, dinheiroCurto, dinheiroMilhoes, moedaNoTexto, NOME_MOEDA } = await import("@/lib/calculos");
    expect(dinheiro(5482)).toBe("R$ 5.482");
    expect(dinheiro(null)).toBe("—");
    expect(dinheiroCurto(217_400)).toBe("R$ 217 mil");
    expect(dinheiroCurto(1_100_000)).toBe("R$ 1,1 mi");
    expect(dinheiroCurto(3525)).toBe("R$ 3.525");
    expect(dinheiroMilhoes(12.5)).toBe("R$ 12,5 mi");
    expect(NOME_MOEDA).toBe("reais");
    // texto pronto da linha do tempo do banco
    expect(moedaNoTexto("Estágio: Em negociação → Ganho (US$ 3300)")).toBe("Estágio: Em negociação → Ganho (R$ 3.300)");
    expect(moedaNoTexto("Ganho: US$ 55")).toBe("Ganho: R$ 55");
    expect(moedaNoTexto("111 compras ganhas. US$ 194.957 em receita.")).toBe("111 compras ganhas. R$ 194.957 em receita.");
  });

  it("o filtro livre aceita R$ e mostra a etiqueta em reais", async () => {
    const { interpretar } = await import("@/lib/filtro/interpretar");
    const ctx = { modo: "leads", papel: "vendedor", vendedores: [], managers: [], regioes: [], produtos: [], series: [], empresas: [], setores: [], tags: [], sedes: [], hoje: "2017-12-31" } as unknown as Parameters<typeof interpretar>[1];
    const rotulos = interpretar("acima de R$ 3.000", ctx).etiquetas.map((e) => e.rotulo);
    expect(rotulos).toContain("Valor ≥ R$ 3.000");
  });
});

describe("variação zero (ajuste da O-30)", () => {
  it("0% e 0 p.p. viram pílula neutra, cinza e sem seta", async () => {
    const { PilulaVariacao, variacaoZero } = await import("@/components/ui/CartaoNumero");
    for (const texto of ["↑ 0% vs 30d ant.", "0 p.p. vs 30d ant.", "↑ 0,0 p.p."]) {
      expect(variacaoZero(texto)).toBe(true);
      const h = html(createElement(PilulaVariacao, { variacao: { texto, sobe: true } }));
      expect(h).toContain("bg-tom-neutro");
      expect(h).not.toContain("bg-tom-positivo");
      expect(h).not.toContain("<svg");
    }
    expect(variacaoZero("↑ 10% vs 30d ant.")).toBe(false);
    expect(variacaoZero("↑ 0,5 p.p.")).toBe(false);
  });
});

describe("sem rodapé de data e fonte (O-48)", () => {
  it("nenhuma tela mostra data dos dados, fonte ou moeda como subtítulo (adendo: o do Painel sai inteiro)", async () => {
    const { readFileSync, readdirSync, statSync } = await import("node:fs");
    const { join } = await import("node:path");
    const arquivos = (d: string): string[] => readdirSync(d).flatMap((f) => (statSync(join(d, f)).isDirectory() ? arquivos(join(d, f)) : f.endsWith(".tsx") ? [join(d, f)] : []));
    for (const f of [...arquivos("src/app"), ...arquivos("src/components")]) {
      const s = readFileSync(f, "utf8");
      expect(s, f).not.toMatch(/[Dd]ados até|Fonte: |Valores em|em \{NOME_MOEDA\}/);
    }
    expect(readFileSync("src/app/painel/page.tsx", "utf8")).not.toMatch(/<h1[^>]*>Painel<\/h1>\s*<p/);
  });
});
