/**
 * The user's own screens (D46.2, ISC-41). A screen is a name plus panels; the user asks the analyst
 * (the same grounded DeepSeek agent as the chat) for an analysis in plain language and each chart
 * the analyst makes becomes a panel, kept with the SQL its numbers came from. Every request and its
 * answer are kept too: a follow-up sees the screen's earlier analyses, and the presentation can use
 * them as context (D46.3). Lives in the app DB, never in the read-only RavenStack database.
 */
import { appdb } from "./appdb";
import { ask, type AgentResult } from "./agent";
import type { ChartSpec } from "./parts";

const DDL = `
  CREATE TABLE IF NOT EXISTS telas_usuario (
    id            TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL,
    nome          TEXT NOT NULL,
    criado_em     TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_telas_usuario_user ON telas_usuario(user_id, criado_em);
  CREATE TABLE IF NOT EXISTS pedidos_tela (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tela_id    TEXT NOT NULL,
    user_id    TEXT NOT NULL,
    pedido     TEXT NOT NULL,
    resposta   TEXT NOT NULL,
    sql_json   TEXT NOT NULL DEFAULT '[]',
    criado_em  TEXT NOT NULL,
    FOREIGN KEY (tela_id) REFERENCES telas_usuario(id) ON DELETE CASCADE
  );
  CREATE TABLE IF NOT EXISTS paineis_tela (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tela_id    TEXT NOT NULL,
    user_id    TEXT NOT NULL,
    pedido_id  INTEGER,
    titulo     TEXT NOT NULL,
    chart_json TEXT NOT NULL,
    sql_json   TEXT NOT NULL DEFAULT '[]',
    criado_em  TEXT NOT NULL,
    FOREIGN KEY (tela_id) REFERENCES telas_usuario(id) ON DELETE CASCADE
  );
  CREATE INDEX IF NOT EXISTS idx_paineis_tela ON paineis_tela(tela_id, id);
`;

let pronto = false;
function db() {
  const d = appdb();
  if (!pronto) {
    d.exec(DDL);
    pronto = true;
  }
  return d;
}

export interface TelaUsuario {
  id: string;
  nome: string;
  criado_em: string;
  atualizado_em: string;
}
export interface PedidoTela {
  id: number;
  pedido: string;
  resposta: string;
  sql: string[];
  criado_em: string;
}
export interface PainelTela {
  id: number;
  pedido_id: number | null;
  titulo: string;
  chart: ChartSpec;
  sql: string[];
  criado_em: string;
}

const agora = () => new Date().toISOString();
const ID_RE = /^tl_[a-z0-9]{12}$/;
export const idTelaValido = (id: string) => ID_RE.test(id);

export function criarTela(userId: string, nome: string): TelaUsuario {
  const limpo = nome.trim().slice(0, 80) || "Nova tela";
  const id = `tl_${crypto.randomUUID().replace(/-/g, "").slice(0, 12)}`;
  const t = agora();
  db().prepare("INSERT INTO telas_usuario (id, user_id, nome, criado_em, atualizado_em) VALUES (?, ?, ?, ?, ?)").run(id, userId, limpo, t, t);
  return { id, nome: limpo, criado_em: t, atualizado_em: t };
}

export function listarTelas(userId: string): TelaUsuario[] {
  return db().prepare("SELECT id, nome, criado_em, atualizado_em FROM telas_usuario WHERE user_id = ? ORDER BY criado_em ASC").all(userId) as TelaUsuario[];
}

export function obterTela(userId: string, id: string): TelaUsuario | null {
  if (!idTelaValido(id)) return null;
  return (db().prepare("SELECT id, nome, criado_em, atualizado_em FROM telas_usuario WHERE user_id = ? AND id = ?").get(userId, id) as TelaUsuario | undefined) ?? null;
}

/** A screen's name by id (for the origin line of a marked chart); null when it does not exist. */
export function nomeTela(id: string): string | null {
  if (!idTelaValido(id)) return null;
  return ((db().prepare("SELECT nome FROM telas_usuario WHERE id = ?").get(id) as { nome: string } | undefined)?.nome) ?? null;
}

export function renomearTela(userId: string, id: string, nome: string): boolean {
  const limpo = nome.trim().slice(0, 80);
  if (!limpo) return false;
  return db().prepare("UPDATE telas_usuario SET nome = ?, atualizado_em = ? WHERE user_id = ? AND id = ?").run(limpo, agora(), userId, id).changes > 0;
}

export function apagarTela(userId: string, id: string): boolean {
  const d = db();
  return d.transaction(() => {
    d.prepare("DELETE FROM paineis_tela WHERE user_id = ? AND tela_id = ?").run(userId, id);
    d.prepare("DELETE FROM pedidos_tela WHERE user_id = ? AND tela_id = ?").run(userId, id);
    return d.prepare("DELETE FROM telas_usuario WHERE user_id = ? AND id = ?").run(userId, id).changes > 0;
  })();
}

export function listarPedidos(userId: string, telaId: string): PedidoTela[] {
  return (
    db().prepare("SELECT id, pedido, resposta, sql_json, criado_em FROM pedidos_tela WHERE user_id = ? AND tela_id = ? ORDER BY id").all(userId, telaId) as (Omit<PedidoTela, "sql"> & {
      sql_json: string;
    })[]
  ).map(({ sql_json, ...p }) => ({ ...p, sql: JSON.parse(sql_json) as string[] }));
}

export function listarPaineis(userId: string, telaId: string): PainelTela[] {
  return (
    db().prepare("SELECT id, pedido_id, titulo, chart_json, sql_json, criado_em FROM paineis_tela WHERE user_id = ? AND tela_id = ? ORDER BY id").all(userId, telaId) as {
      id: number;
      pedido_id: number | null;
      titulo: string;
      chart_json: string;
      sql_json: string;
      criado_em: string;
    }[]
  ).map((p) => ({ id: p.id, pedido_id: p.pedido_id, titulo: p.titulo, chart: JSON.parse(p.chart_json) as ChartSpec, sql: JSON.parse(p.sql_json) as string[], criado_em: p.criado_em }));
}

export function removerPainel(userId: string, telaId: string, painelId: number): boolean {
  return db().prepare("DELETE FROM paineis_tela WHERE user_id = ? AND tela_id = ? AND id = ?").run(userId, telaId, painelId).changes > 0;
}

/** Adds a chart to a screen (also used from the chat: "send to a screen", ISC-43). */
export function adicionarPainel(userId: string, telaId: string, chart: ChartSpec, sql: string[], pedidoId: number | null = null): PainelTela {
  const titulo = (chart.title || "Gráfico").trim().slice(0, 160);
  const dados = Array.isArray(chart.data) ? chart.data.slice(0, 200) : [];
  const spec: ChartSpec = { ...chart, title: titulo, data: dados };
  const t = agora();
  const r = db()
    .prepare("INSERT INTO paineis_tela (tela_id, user_id, pedido_id, titulo, chart_json, sql_json, criado_em) VALUES (?, ?, ?, ?, ?, ?, ?)")
    .run(telaId, userId, pedidoId, titulo, JSON.stringify(spec), JSON.stringify(sql.slice(0, 10)), t);
  db().prepare("UPDATE telas_usuario SET atualizado_em = ? WHERE id = ?").run(t, telaId);
  return { id: Number(r.lastInsertRowid), pedido_id: pedidoId, titulo, chart: spec, sql: sql.slice(0, 10), criado_em: t };
}

/**
 * Each chart the analyst made, with the SQL behind its rows: the query (or metric) the analyst ran
 * last before calling make_chart. Charts never carry numbers that were not queried (the agent's
 * grounding rule); keeping that SQL lets the deck re-run it and check the narrative (D45).
 */
export function graficosDaResposta(r: Pick<AgentResult, "toolCalls">): { chart: ChartSpec; sql: string[] }[] {
  const saida: { chart: ChartSpec; sql: string[] }[] = [];
  let ultimoSql: string | null = null;
  for (const c of r.toolCalls) {
    if (c.isError) continue;
    if (c.name === "query_warehouse" || c.name === "run_metric") {
      const sql = (c.result as { sql?: string })?.sql;
      if (sql) ultimoSql = sql;
    } else if (c.name === "make_chart") {
      const chart = (c.result as { chart?: ChartSpec })?.chart;
      if (chart && Array.isArray(chart.data) && chart.data.length > 0) saida.push({ chart, sql: ultimoSql ? [ultimoSql] : [] });
    }
  }
  return saida;
}

const INSTRUCAO_TELA = [
  "VOCÊ ESTÁ MONTANDO UMA TELA DE ANÁLISE para o usuário.",
  "- Cada gráfico que você fizer com make_chart vira um painel fixo na tela dele, então faça de 1 a 3 gráficos que respondam o pedido, cada um com um título curto e claro em português (até 8 palavras).",
  "- Sempre consulte os números antes (query_warehouse ou run_metric) e passe para make_chart exatamente as linhas da consulta. Use nomes de colunas em português legíveis (ex.: taxa_churn_pct, contas, eventos).",
  "- Prefira um gráfico por consulta. Para taxas use colunas terminadas em _pct já em porcentagem (0 a 100).",
  "- Na resposta escrita, em até 6 linhas: o que os gráficos mostram e o que chama atenção, sem afirmar causa.",
].join("\n");

export interface ResultadoAnalise {
  pedido: PedidoTela;
  paineis: PainelTela[];
}

/** Runs one request on a screen: the analyst sees the screen's earlier requests, and its charts become panels. */
export async function analisarNaTela(
  userId: string,
  telaId: string,
  pedido: string,
  opts: { perguntar?: typeof ask } = {},
): Promise<ResultadoAnalise> {
  const tela = obterTela(userId, telaId);
  if (!tela) throw new Error("tela não encontrada");
  const texto = pedido.trim().slice(0, 2000);
  if (!texto) throw new Error("escreva o pedido");
  const anteriores = listarPedidos(userId, telaId).slice(-6);
  const paineis = listarPaineis(userId, telaId);
  const contexto = [
    INSTRUCAO_TELA,
    `A tela se chama "${tela.nome}".`,
    paineis.length ? `Painéis que já estão na tela: ${paineis.map((p) => `"${p.titulo}"`).join("; ")}. Não repita um gráfico que já existe.` : "A tela ainda está vazia.",
  ].join("\n");
  const perguntar = opts.perguntar ?? ask;
  const r = await perguntar(texto, {
    userId,
    extraSystem: contexto,
    history: anteriores.map((p) => ({ question: p.pedido, answer: p.resposta })),
  });
  const graficos = graficosDaResposta(r);
  const sqlTodos = r.citedSql.slice(0, 10);
  const t = agora();
  const ins = db()
    .prepare("INSERT INTO pedidos_tela (tela_id, user_id, pedido, resposta, sql_json, criado_em) VALUES (?, ?, ?, ?, ?, ?)")
    .run(telaId, userId, texto, r.answer || "(o analista não escreveu resposta)", JSON.stringify(sqlTodos), t);
  const pedidoId = Number(ins.lastInsertRowid);
  const novos = graficos.map((g) => adicionarPainel(userId, telaId, g.chart, g.sql, pedidoId));
  return {
    pedido: { id: pedidoId, pedido: texto, resposta: r.answer, sql: sqlTodos, criado_em: t },
    paineis: novos,
  };
}
