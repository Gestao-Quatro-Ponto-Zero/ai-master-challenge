/**
 * Charts marked on the screens for the presentation (D44). A mark keeps a faithful copy of the
 * chart as it was on screen — the SVG and a PNG made from it in the browser — with the screen,
 * the filters in force and the panel's title and note. Marks live in the app DB, never in the
 * read-only RavenStack database. The presentation is built from them in deckMarcados.ts (D45).
 */
import { appdb } from "./appdb";
import { lerFiltros, descreverFiltros } from "./filtros";

const DDL = `
  CREATE TABLE IF NOT EXISTS graficos_marcados (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT    NOT NULL,
    chave      TEXT    NOT NULL,
    rota       TEXT    NOT NULL,
    filtros    TEXT    NOT NULL,
    titulo     TEXT    NOT NULL,
    nota       TEXT,
    svg        TEXT    NOT NULL,
    png        TEXT    NOT NULL,
    sql_json   TEXT    NOT NULL DEFAULT '[]',
    largura    INTEGER NOT NULL,
    altura     INTEGER NOT NULL,
    criado_em  TEXT    NOT NULL,
    UNIQUE (user_id, chave)
  );
  CREATE INDEX IF NOT EXISTS idx_marcados_user ON graficos_marcados(user_id, criado_em);
`;

let pronto = false;
function db() {
  const d = appdb();
  if (!pronto) {
    d.exec(DDL);
    const cols = (d.prepare("PRAGMA table_info(graficos_marcados)").all() as { name: string }[]).map((c) => c.name);
    if (!cols.includes("sql_json")) d.exec("ALTER TABLE graficos_marcados ADD COLUMN sql_json TEXT NOT NULL DEFAULT '[]'");
    pronto = true;
  }
  return d;
}

/** Screen names by route — the menu's labels. */
export const TELAS: Record<string, string> = {
  "/": "Visão geral",
  "/tela/1": "Tela 1 · As três afirmações",
  "/tela/2": "Tela 2 · O que causa o churn",
  "/tela/3": "Tela 3 · Suporte e uso do produto",
};

export interface Marcado {
  id: number;
  chave: string;
  rota: string;
  filtros: string;
  titulo: string;
  nota: string | null;
  largura: number;
  altura: number;
  criado_em: string;
}

export interface NovoMarcado {
  chave: string;
  rota: string;
  filtros: string;
  titulo: string;
  nota: string | null;
  svg: string;
  png: string;
  /** The panel's SQL, so the deck can re-run it and check every number (D45). */
  sql: string[];
  largura: number;
  altura: number;
}

const LIMITE_BYTES = 4_000_000;
const PNG_PREFIXO = "data:image/png;base64,";

/** Checks an untrusted payload; returns the reason it is refused, or null. */
export function validarMarcado(m: Partial<NovoMarcado>): string | null {
  if (typeof m.chave !== "string" || !m.chave || m.chave.length > 500) return "chave inválida";
  if (typeof m.rota !== "string" || !(m.rota in TELAS)) return "tela desconhecida";
  if (typeof m.filtros !== "string" || m.filtros.length > 500) return "filtros inválidos";
  if (typeof m.titulo !== "string" || !m.titulo.trim() || m.titulo.length > 200) return "título inválido";
  if (typeof m.svg !== "string" || !m.svg.startsWith("<svg") || m.svg.length > LIMITE_BYTES) return "SVG inválido";
  if (/<script|<foreignObject|\son[a-z]+\s*=|javascript:/i.test(m.svg)) return "SVG com conteúdo ativo";
  if (!Array.isArray(m.sql) || m.sql.length > 10 || !m.sql.every((q) => typeof q === "string" && q.length < 20_000)) return "SQL inválido";
  if (typeof m.png !== "string" || !m.png.startsWith(PNG_PREFIXO) || m.png.length > LIMITE_BYTES) return "PNG inválido";
  if (!Number.isFinite(m.largura) || !Number.isFinite(m.altura) || (m.largura as number) < 1 || (m.altura as number) < 1) return "tamanho inválido";
  return null;
}

/** Marks a chart; marking the same chart again (same screen, title and filters) refreshes the copy. */
export function marcar(userId: string, m: NovoMarcado): Marcado {
  db()
    .prepare(
      `INSERT INTO graficos_marcados (user_id, chave, rota, filtros, titulo, nota, svg, png, sql_json, largura, altura, criado_em)
       VALUES (@user_id, @chave, @rota, @filtros, @titulo, @nota, @svg, @png, @sql_json, @largura, @altura, @criado_em)
       ON CONFLICT(user_id, chave) DO UPDATE SET titulo=@titulo, nota=@nota, svg=@svg, png=@png, sql_json=@sql_json, largura=@largura, altura=@altura`,
    )
    .run({ chave: m.chave, rota: m.rota, filtros: m.filtros, titulo: m.titulo, svg: m.svg, png: m.png, sql_json: JSON.stringify(m.sql ?? []), nota: m.nota ?? null, largura: Math.round(m.largura), altura: Math.round(m.altura), user_id: userId, criado_em: new Date().toISOString() });
  return db().prepare("SELECT id, chave, rota, filtros, titulo, nota, largura, altura, criado_em FROM graficos_marcados WHERE user_id = ? AND chave = ?").get(userId, m.chave) as Marcado;
}

export function desmarcar(userId: string, chave: string): boolean {
  return db().prepare("DELETE FROM graficos_marcados WHERE user_id = ? AND chave = ?").run(userId, chave).changes > 0;
}

export function removerMarcado(userId: string, id: number): boolean {
  return db().prepare("DELETE FROM graficos_marcados WHERE user_id = ? AND id = ?").run(userId, id).changes > 0;
}

/** The marks in the order they were made (the slide order). */
export function listarMarcados(userId: string): Marcado[] {
  return db()
    .prepare("SELECT id, chave, rota, filtros, titulo, nota, largura, altura, criado_em FROM graficos_marcados WHERE user_id = ? ORDER BY criado_em ASC, id ASC")
    .all(userId) as Marcado[];
}

export function arquivoMarcado(userId: string, id: number): { titulo: string; svg: string; png: string } | null {
  return (db().prepare("SELECT titulo, svg, png FROM graficos_marcados WHERE user_id = ? AND id = ?").get(userId, id) as { titulo: string; svg: string; png: string } | undefined) ?? null;
}

/** "Tela 2 · O que causa o churn · FinTech · plano Pro" — where the chart came from. */
export function origemMarcado(m: Pick<Marcado, "rota" | "filtros">): { tela: string; filtros: string } {
  const params = Object.fromEntries(new URLSearchParams(m.filtros));
  return { tela: TELAS[m.rota] ?? m.rota, filtros: descreverFiltros(lerFiltros(params)) };
}

/** "churn-por-setor" — a file name from a title. */
export function nomeArquivo(titulo: string): string {
  return (
    titulo
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 60) || "grafico"
  );
}
