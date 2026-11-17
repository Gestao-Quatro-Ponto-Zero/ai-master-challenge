/**
 * The presentation built from the marked charts (D45). Run: bun run deck-marcados-test.
 * Throwaway app DB, real RavenStack SQL, a scripted arranger (no LLM call): the number check
 * keeps grounded numbers and drops the rest, every marked chart lands on a slide, the plain
 * arrangement works without an LLM, and the .pptx follows the pyramid.
 */
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import JSZip from "jszip";

const dir = mkdtempSync(path.join(tmpdir(), "deck-marcados-"));
process.env.APP_DB_PATH = path.join(dir, "app.sqlite");

let failed = 0;
function check(name: string, cond: boolean, detail = ""): void {
  process.stdout.write(`${cond ? "✓" : "✗"} ${name}${detail ? ` — ${detail}` : ""}\n`);
  if (!cond) failed++;
}

(async () => {
  const d = await import("../src/engine/deckMarcados");
  const m = await import("../src/engine/marcados");
  const { churnPorSetor } = await import("../src/engine/visaoGeral");
  const { lerFiltros } = await import("../src/engine/filtros");

  // The number reader and the check.
  const ns = d.numerosDoTexto("DevTools tem 31% de churn, 1.077 tickets e US$ 7,99 mi; nota 3.98");
  check("lê 31%, 1.077, 7,99 mi e 3.98", ns.map((n) => `${n.valor}${n.pct ? "%" : ""}${n.escala === 1e6 ? "mi" : ""}`).join(" ") === "31% 1077 7.99mi 3.98", ns.map((n) => n.valor).join(" "));
  check("22,3% confere com 22.3", d.textoAterrado("FinTech: 22,3%", [22.3]) !== null);
  check("22% confere com 22.3 (arredondado)", d.textoAterrado("cerca de 22%", [22.3]) !== null);
  check("23% não confere com 22.3", d.textoAterrado("23% das contas", [22.3]) === null);
  check("US$ 8,0 mi confere com 7.990.982", d.textoAterrado("US$ 8,0 mi", [7990982]) !== null);
  check("taxa 0,223 escrita como 22,3%", d.textoAterrado("22,3%", [0.223]) !== null);
  check("85% não confere com a contagem 85", d.textoAterrado("85% das contas", { n: [85, 25], pct: [77.3, 22.7] }) === null);
  check("77% confere com a fatia 77,3", d.textoAterrado("77% das contas", { n: [85, 25], pct: [77.3, 22.7] }) !== null);
  check("85 contas confere com a contagem", d.textoAterrado("85 contas pagas", { n: [85, 25], pct: [] }) !== null);
  check("texto sem número passa", d.textoAterrado("O churn se concentra em DevTools", []) !== null);

  // Two real charts, with their real SQL.
  const png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=";
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200"></svg>';
  const setor = churnPorSetor(lerFiltros({}));
  const u = "teste";
  m.marcar(u, { chave: "a", rota: "/tela/2", filtros: "", titulo: "Churn por indústria", nota: "% das contas com churn", svg, png, largura: 400, altura: 200, sql: [setor.sql] });
  m.marcar(u, { chave: "b", rota: "/", filtros: "", titulo: "Idade média da base", nota: null, svg, png, largura: 900, altura: 200, sql: [] });
  const g = d.aterrar(u, m.listarMarcados(u));
  check("aterrar re-roda o SQL do gráfico (5 setores)", g[0].consultas[0]?.linhas.length === 5, String(g[0].consultas[0]?.linhas.length));
  check("DevTools 31 está entre os valores", g[0].valores.pct.includes(31));
  const { composicaoTrial } = await import("../src/engine/tela2");
  m.marcar(u, { chave: "c", rota: "/tela/2", filtros: "", titulo: "Churn no teste × no pago", nota: null, svg, png, largura: 400, altura: 300, sql: [composicaoTrial(lerFiltros({})).sql] });
  const gt = d.aterrar(u, m.listarMarcados(u))[2];
  check("composição ganha a fatia de cada linha (77,3 e 22,7)", gt.consultas[0].colunas.includes(d.COLUNA_PARTE) && gt.valores.pct.includes(77.3) && gt.valores.pct.includes(22.7), JSON.stringify(gt.valores.pct));
  check("a contagem 85 não vira porcentagem", !gt.valores.pct.includes(85));
  m.desmarcar(u, "c");

  // A scripted arranger: one grounded title, one made-up number, one chart left out.
  const arranjador: import("../src/engine/deckMarcados").Arranjador = async () => ({
    titulo: "Churn da RavenStack",
    ideiaCentral: "O churn se concentra em poucos setores, com DevTools no topo",
    scqa: { situacao: "A base cresce.", complicacao: "O churn sobe.", pergunta: "Onde agir primeiro?" },
    secoes: [{ titulo: "DevTools perde 31% das contas", graficos: [{ indice: 0, tituloAcao: "DevTools tem o maior churn: 31% das contas", linhas: ["FinTech vem depois, com 22,3%", "EdTech perde 47% das contas"] }] }],
    recomendacoes: ["Priorize DevTools na retenção", "Reduza o churn em 15 pontos"],
  });
  const deck = await d.montarDeck(u, { arranjador });
  const s0 = deck.secoes[0].graficos[0];
  check("título com número dos dados fica", s0.tituloAcao === "DevTools tem o maior churn: 31% das contas");
  check("linha com número dos dados fica, a inventada sai", s0.linhas.length === 1 && s0.linhas[0].includes("22,3%"), JSON.stringify(s0.linhas));
  check("recomendação com número inventado sai", deck.recomendacoes.length === 1 && deck.recomendacoes[0].startsWith("Priorize"));
  check("o gráfico deixado de fora entra numa seção à parte", deck.secoes.length === 2 && deck.secoes[1].graficos[0].tituloPainel === "Idade média da base");
  check("avisos contam o que saiu", deck.avisos.length === 3, deck.avisos.join(" | "));
  check("deck guardado e atual", d.deckAtual(u)?.criadoEm === deck.criadoEm && !d.deckDesatualizado(u, deck));

  // Without an LLM: the plain arrangement.
  const regra = await d.montarDeck(u, { arranjador: async () => null });
  check("sem LLM: uma seção por tela, títulos dos painéis", regra.autor === "regra" && regra.secoes.map((s) => s.titulo).join("|") === "Visão geral|Tela 2 · O que causa o churn", regra.secoes.map((s) => s.titulo).join("|"));

  // The .pptx follows the pyramid: cover, summary, context, (divider + charts) per section, actions.
  const zip = await JSZip.loadAsync(await d.deckParaPptx(u, deck));
  const slides = Object.keys(zip.files).filter((f) => /^ppt\/slides\/slide\d+\.xml$/.test(f));
  check("pptx: 3 + 2 divisórias + 2 gráficos + ações = 8 slides", slides.length === 8, String(slides.length));
  const txt = async (i: number) => (await zip.file(`ppt/slides/slide${i}.xml`)!.async("string")).replace(/<[^>]+>/g, " ");
  check("pptx: capa com a ideia central", (await txt(1)).includes("O churn se concentra em poucos setores"));
  check("pptx: resumo executivo com as seções", (await txt(2)).includes("RESUMO EXECUTIVO") && (await txt(2)).includes("DevTools perde 31% das contas"));
  check("pptx: contexto com situação, complicação e resposta", (await txt(3)).includes("SITUAÇÃO") && (await txt(3)).includes("RESPOSTA"));
  check("pptx: slide do gráfico com título de ação e fonte", (await txt(5)).includes("DevTools tem o maior churn") && (await txt(5)).includes("Fonte: base RavenStack"));
  check("pptx: ações recomendadas no fim", (await txt(8)).includes("Ações recomendadas"));

  m.desmarcar(u, "b");
  check("marcas mudaram: deck desatualizado", d.deckDesatualizado(u, deck));

  rmSync(dir, { recursive: true, force: true });
  process.stdout.write(failed === 0 ? "\nDECK MARCADOS OK\n" : `\n${failed} FAILED\n`);
  process.exit(failed === 0 ? 0 : 1);
})();
