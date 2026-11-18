/**
 * Custom screens (ISC-41) on a throwaway app DB, with a scripted analyst (no LLM): charts become
 * panels with the SQL behind their rows, follow-ups see earlier requests, panels go away, screens
 * are per user, and a chart on a custom screen can be marked.
 */
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

const dir = mkdtempSync(path.join(tmpdir(), "telas-"));
process.env.APP_DB_PATH = path.join(dir, "app.sqlite");
let n = 0;
const ok = (c: unknown, m: string) => { assert.ok(c, m); n++; };

(async () => {
  const t = await import("../src/engine/telasUsuario");
  const { runQuery } = await import("../src/engine/warehouse");
  const m = await import("../src/engine/marcados");

  const tela = t.criarTela("u1", "  Churn Enterprise  ");
  ok(t.idTelaValido(tela.id) && tela.nome === "Churn Enterprise", "cria com id e nome limpo");
  ok(t.obterTela("u2", tela.id) === null, "outro usuário não vê a tela");

  const sql = "SELECT plan_tier AS plano, round(100.0 * avg(churn_flag), 1) AS taxa_churn_pct FROM accounts GROUP BY plan_tier";
  const q = runQuery(sql);
  const vistos: { history?: unknown; extraSystem?: string }[] = [];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const roteiro = async (_pergunta: string, opts: any) => {
    vistos.push({ history: opts.history, extraSystem: opts.extraSystem });
    return {
      answer: "Enterprise tem a maior taxa.",
      model: "roteiro",
      steps: 2,
      stopReason: "stop",
      citedSql: [q.sql],
      toolCalls: [
        { name: "query_warehouse", input: { sql }, result: q, isError: false },
        { name: "make_chart", input: {}, result: { chart: { type: "column", title: "Taxa de churn por plano", x: "plano", y: ["taxa_churn_pct"], data: q.rows } }, isError: false },
        { name: "make_chart", input: {}, result: { chart: { type: "bar", title: "vazio", x: "a", y: ["b"], data: [] } }, isError: false },
      ],
    };
  };
  const r1 = await t.analisarNaTela("u1", tela.id, "taxa de churn por plano", { perguntar: roteiro as never });
  ok(r1.paineis.length === 1, "um painel por gráfico com dados (o vazio fica de fora)");
  ok(r1.paineis[0].sql[0] === q.sql, "o painel guarda o SQL da consulta anterior ao gráfico");
  ok(vistos[0].extraSystem?.includes("Churn Enterprise") && (vistos[0].history as unknown[]).length === 0, "1º pedido: instrução da tela, sem histórico");

  await t.analisarNaTela("u1", tela.id, "agora por cobrança", { perguntar: roteiro as never });
  const h = vistos[1].history as { question: string; answer: string }[];
  ok(h.length === 1 && h[0].question === "taxa de churn por plano" && h[0].answer.startsWith("Enterprise"), "2º pedido vê o 1º");
  ok(vistos[1].extraSystem?.includes("Taxa de churn por plano"), "o analista sabe que painéis já existem");
  ok(t.listarPaineis("u1", tela.id).length === 2 && t.listarPedidos("u1", tela.id).length === 2, "painéis e pedidos persistem");

  ok(t.removerPainel("u1", tela.id, r1.paineis[0].id) && t.listarPaineis("u1", tela.id).length === 1, "remove painel");
  ok(!t.removerPainel("u2", tela.id, t.listarPaineis("u1", tela.id)[0].id), "outro usuário não remove");

  const viaChat = t.adicionarPainel("u1", tela.id, { type: "pie", title: "Do chat", x: "plano", y: ["taxa_churn_pct"], data: q.rows }, [q.sql]);
  ok(viaChat.pedido_id === null && t.listarPaineis("u1", tela.id).length === 2, "gráfico vindo do chat entra na tela");

  // marking on a custom screen
  ok(m.rotaValida(`/telas/${tela.id}`) && !m.rotaValida("/telas/../x") && !m.rotaValida("/telas/tl_x"), "rota de tela própria aceita, outras não");
  ok(m.origemMarcado({ rota: `/telas/${tela.id}`, filtros: "" }).tela === "Minha tela · Churn Enterprise", "origem com o nome da tela");

  ok(t.apagarTela("u1", tela.id) && t.listarPaineis("u1", tela.id).length === 0 && t.listarTelas("u1").length === 0, "apaga a tela e os painéis");
  ok(m.origemMarcado({ rota: `/telas/${tela.id}`, filtros: "" }).tela === "Minha tela · apagada", "marca de tela apagada continua legível");

  rmSync(dir, { recursive: true, force: true });
  console.log(`TELAS OK (${n} checagens)`);
})().catch((e) => {
  rmSync(dir, { recursive: true, force: true });
  console.error(e);
  process.exit(1);
});
