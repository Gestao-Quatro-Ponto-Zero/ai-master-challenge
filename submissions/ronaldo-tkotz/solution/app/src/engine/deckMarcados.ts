/**
 * The presentation built from the marked charts as a Minto pyramid (D45), the structure Veta's
 * deck arranger used (deck.ts): the answer first (the governing thought), the SCQA framing,
 * a key line of 2–4 MECE sections whose titles are assertions, one action title per chart, and
 * the recommended actions.
 *
 * Division of labour, as in Veta: the ARRANGER (the app's LLM) writes the narrative; OUR code
 * re-runs each chart's SQL and checks every number the arranger wrote against those rows. A
 * line whose number is not in the data is dropped (or replaced by the panel's own title) and
 * reported as a warning, so no unverifiable figure reaches a slide. Without an LLM, a plain
 * arrangement (sections by screen, panel titles) still produces a correct deck.
 */
import OpenAI from "openai";
import PptxGenJS from "pptxgenjs";
import { appdb, appdbGeracao } from "./appdb";
import { runQuery } from "./warehouse";
import { listarMarcados, arquivoMarcado, origemMarcado, TELAS, type Marcado } from "./marcados";
import { MOTIVOS } from "./tela2";
import { getConversation, getMessages } from "./appdb";
import { listarPedidos, obterTela } from "./telasUsuario";

// ── The deck ─────────────────────────────────────────────────────────────────

export interface SlideGrafico {
  marcadoId: number;
  /** Action title: the so-what of the chart, as a full sentence. */
  tituloAcao: string;
  /** 0–2 short supporting lines. */
  linhas: string[];
  tituloPainel: string;
  nota: string | null;
  tela: string;
  filtros: string;
}

export interface Secao {
  /** The section's assertion (a key-line point of the pyramid). */
  titulo: string;
  graficos: SlideGrafico[];
}

export interface DeckMarcados {
  titulo: string;
  /** The apex of the pyramid: the one conclusion the audience takes away. */
  ideiaCentral: string;
  scqa: { situacao: string; complicacao: string; pergunta: string };
  secoes: Secao[];
  recomendacoes: string[];
  briefing: string | null;
  autor: "ia" | "regra";
  /** What the number check removed or replaced, in plain words. */
  avisos: string[];
  marcadoIds: number[];
  criadoEm: string;
  /** D46.3: the audience picked, and the conversations and screens used as context (names). */
  publico?: string | null;
  fontes?: string[];
  /** Id in the deck history (D46.3). */
  id?: number;
}

/**
 * What the user already investigated with the analyst (D46.3): the conversations and custom screens
 * they picked, so the deck follows their question instead of a fixed template. The SQL behind those
 * answers is re-run, and its numbers join what the narrative may cite.
 */
export interface ContextoDeck {
  publico: string | null;
  conversas: { titulo: string; turnos: { pergunta: string; resposta: string }[] }[];
  telas: { nome: string; pedidos: { pedido: string; resposta: string }[] }[];
  sql: string[];
}

/** What the arranger returns — narrative only, indices point at the marked charts. */
export interface Arranjo {
  titulo: string;
  ideiaCentral: string;
  scqa: { situacao: string; complicacao: string; pergunta: string };
  secoes: { titulo: string; graficos: { indice: number; tituloAcao: string; linhas: string[] }[] }[];
  recomendacoes: string[];
}

export interface GraficoAterrado {
  indice: number;
  marcado: Marcado;
  tela: string;
  filtros: string;
  /** The rows of the chart's SQL, re-run now. */
  consultas: { colunas: string[]; linhas: Record<string, unknown>[] }[];
  /** The numbers in those rows: what a written number may be checked against. */
  valores: Valores;
}

export type Arranjador = (graficos: GraficoAterrado[], briefing: string | null, contexto?: ContextoDeck | null) => Promise<Arranjo | null>;

// ── Grounding ────────────────────────────────────────────────────────────────

function sqlDoMarcado(userId: string, id: number): string[] {
  const row = appdb().prepare("SELECT sql_json FROM graficos_marcados WHERE user_id = ? AND id = ?").get(userId, id) as { sql_json: string } | undefined;
  try {
    const arr = JSON.parse(row?.sql_json ?? "[]");
    return Array.isArray(arr) ? arr.filter((s): s is string => typeof s === "string" && s.trim().length > 0) : [];
  } catch {
    return [];
  }
}

/** Numbers a written figure may be checked against: counts and amounts apart from percentages. */
export interface Valores {
  n: number[];
  pct: number[];
}
const juntar = (...vs: Valores[]): Valores => ({ n: vs.flatMap((v) => v.n), pct: vs.flatMap((v) => v.pct) });
const PCT_COLUNA = /pct|taxa|rate|percent|share|parte|cresc|var/i;
export const COLUNA_PARTE = "parte_do_total_%";

/**
 * Re-runs each marked chart's SQL (read-only, through the warehouse guard). A column is a
 * percentage when its name says so or it has fractions; whole-number columns are counts, so
 * "85%" cannot pass on a count of 85. For a composition (a label and a whole-number count, up to
 * 12 rows) each row's share of the total is added as a column the arranger can cite.
 */
export function aterrar(userId: string, marcados: Marcado[]): GraficoAterrado[] {
  return marcados.map((m, indice) => {
    const consultas: GraficoAterrado["consultas"] = [];
    const valores: Valores = { n: [], pct: [] };
    for (const sql of sqlDoMarcado(userId, m.id)) {
      let r;
      try {
        r = runQuery(sql);
      } catch {
        continue; // a query that no longer runs grounds nothing
      }
      const colunas = [...r.columns];
      const linhas = r.rows.map((l) => ({ ...l }));
      for (const col of r.columns) {
        const brutos = r.rows.map((l) => l[col]);
        const nums = brutos.filter((v) => v !== null && v !== "" && typeof v !== "boolean").map(Number).filter((n) => Number.isFinite(n));
        const textos = brutos.filter((v): v is string => typeof v === "string" && !Number.isFinite(Number(v)));
        // Numbers inside text cells: band labels ("24 a 48 h") and names ("feature_28").
        for (const t of textos) for (const n of numerosDoTexto(t.replace(/_/g, " "))) (n.pct ? valores.pct : valores.n).push(n.valor);
        if (nums.length === 0) continue;
        const pct = PCT_COLUNA.test(col) || nums.some((n) => !Number.isInteger(n));
        valores.n.push(...nums);
        if (pct) valores.pct.push(...nums);
        const temRotulo = r.columns.some((c) => r.rows.some((l) => typeof l[c] === "string" && !Number.isFinite(Number(l[c]))));
        const total = nums.reduce((a, b) => a + b, 0);
        if (!pct && temRotulo && r.rows.length >= 2 && r.rows.length <= 12 && nums.length === r.rows.length && nums.every((n) => n >= 0) && total > 0 && !colunas.includes(COLUNA_PARTE)) {
          colunas.push(COLUNA_PARTE);
          linhas.forEach((l, i) => {
            const parte = Math.round((1000 * nums[i]) / total) / 10;
            l[COLUNA_PARTE] = parte;
            valores.pct.push(parte);
          });
        }
      }
      consultas.push({ colunas, linhas });
    }
    return { indice, marcado: m, ...origemMarcado(m), consultas, valores };
  });
}

/** The numbers in the rows of any SQL (the context's queries, D46.3), classified like a chart's. */
export function valoresDeSql(sqls: string[]): Valores {
  const valores: Valores = { n: [], pct: [] };
  for (const sql of sqls.slice(0, 25)) {
    let r;
    try {
      r = runQuery(sql, 500);
    } catch {
      continue;
    }
    for (const col of r.columns) {
      const brutos = r.rows.map((l) => l[col]);
      const nums = brutos.filter((v) => v !== null && v !== "" && typeof v !== "boolean").map(Number).filter((n) => Number.isFinite(n));
      for (const t of brutos.filter((v): v is string => typeof v === "string" && !Number.isFinite(Number(v))))
        for (const n of numerosDoTexto(t.replace(/_/g, " "))) (n.pct ? valores.pct : valores.n).push(n.valor);
      valores.n.push(...nums);
      if (PCT_COLUNA.test(col) || nums.some((n) => !Number.isInteger(n))) valores.pct.push(...nums);
    }
  }
  return valores;
}

/** Loads the conversations and screens the user picked (only theirs) as deck context. */
export function carregarContexto(userId: string, opts: { publico?: string | null; conversaIds?: string[]; telaIds?: string[] }): ContextoDeck {
  const sql: string[] = [];
  const conversas: ContextoDeck["conversas"] = [];
  for (const id of (opts.conversaIds ?? []).slice(0, 8)) {
    const c = getConversation(id, userId);
    if (!c) continue;
    const turnos: { pergunta: string; resposta: string }[] = [];
    let pergunta = "";
    for (const m of getMessages(id, userId)) {
      const p = JSON.parse(m.payload_json) as { role?: string; text?: string; answer?: string; citedSql?: string[] };
      if (p.role === "user") pergunta = p.text ?? "";
      else if (p.role === "assistant" && p.answer) {
        turnos.push({ pergunta, resposta: p.answer });
        sql.push(...(p.citedSql ?? []));
      }
    }
    if (turnos.length) conversas.push({ titulo: c.title, turnos });
  }
  const telas: ContextoDeck["telas"] = [];
  for (const id of (opts.telaIds ?? []).slice(0, 8)) {
    const t = obterTela(userId, id);
    if (!t) continue;
    const pedidos = listarPedidos(userId, id);
    for (const p of pedidos) sql.push(...p.sql);
    if (pedidos.length) telas.push({ nome: t.nome, pedidos: pedidos.map((p) => ({ pedido: p.pedido, resposta: p.resposta })) });
  }
  return { publico: opts.publico?.trim() ? opts.publico.trim().slice(0, 80) : null, conversas, telas, sql: [...new Set(sql)].slice(0, 25) };
}

/** The context as prompt text, capped so a long history cannot crowd out the charts. */
function contextoParaPrompt(c: ContextoDeck): string {
  const corta = (t: string, n: number) => (t.length > n ? `${t.slice(0, n)}…` : t);
  const partes: string[] = [];
  for (const conv of c.conversas) {
    partes.push(`Conversa "${conv.titulo}":`);
    for (const t of conv.turnos.slice(-6)) partes.push(`  P: ${corta(t.pergunta, 300)}\n  R: ${corta(t.resposta, 900)}`);
  }
  for (const tela of c.telas) {
    partes.push(`Tela própria "${tela.nome}":`);
    for (const p of tela.pedidos.slice(-6)) partes.push(`  Pedido: ${corta(p.pedido, 300)}\n  Analista: ${corta(p.resposta, 900)}`);
  }
  return corta(partes.join("\n"), 9000);
}

const ENFASE: Record<string, string> = {
  Diretoria: "decisão e impacto no negócio (receita, onde agir primeiro); linguagem de diretoria, pouco detalhe técnico",
  "Customer Success": "segmentos e contas a acompanhar, sinais de risco, ações de relacionamento",
  Produto: "uso de recursos, erros, o que o produto pode mudar",
  Investidores: "tendência, tamanho do problema e plano, em poucas mensagens",
};

// ── The number check ─────────────────────────────────────────────────────────

interface Numero {
  texto: string;
  valor: number;
  casas: number;
  escala: number;
  pct: boolean;
}

/** Numbers as written in Portuguese (or English) prose: "22,3%", "1.077", "US$ 7,99 mi", "3.98". */
export function numerosDoTexto(s: string): Numero[] {
  const out: Numero[] = [];
  const re = /\d[\d.,]*/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(s))) {
    const tok = m[0].replace(/[.,]+$/, "");
    let valor: number;
    let casas = 0;
    if (tok.includes(",")) {
      const [int, dec = ""] = tok.split(",");
      valor = Number(int.replace(/\./g, "") + "." + dec);
      casas = dec.length;
    } else if (/^\d{1,3}(\.\d{3})+$/.test(tok)) {
      valor = Number(tok.replace(/\./g, ""));
    } else if (tok.includes(".")) {
      valor = Number(tok);
      casas = tok.split(".")[1]?.length ?? 0;
    } else {
      valor = Number(tok);
    }
    if (!Number.isFinite(valor)) continue;
    const depois = s.slice(m.index + tok.length, m.index + tok.length + 12).toLowerCase();
    const pct = /^\s*(%|p\.?p\.?|pontos? percentua)/.test(depois);
    const escala = /^\s*(mi\b|milh)/.test(depois) ? 1e6 : /^\s*(mil\b|k\b)/.test(depois) ? 1e3 : /^\s*(bi\b|bilh)/.test(depois) ? 1e9 : 1;
    out.push({ texto: tok, valor, casas, escala, pct });
  }
  return out;
}

const arred = (v: number, casas: number) => Math.round(v * 10 ** casas) / 10 ** casas;

/**
 * A written number is grounded when some value in the data, at the precision written, equals it.
 * A percentage must match a percentage (or a fraction × 100); a plain number may match any value.
 */
export function numeroConfere(n: Numero, valores: Valores | number[]): boolean {
  const v = Array.isArray(valores) ? { n: valores, pct: valores } : valores;
  const iguais = (c: number) => Math.abs(arred(c, n.casas) - n.valor) < 1e-9;
  if (n.pct) return v.pct.some((x) => iguais(Math.abs(x))) || [...v.n, ...v.pct].some((x) => Math.abs(x) <= 1 && iguais(Math.abs(x) * 100));
  return [...v.n, ...v.pct].some((x) => iguais(Math.abs(x) / n.escala));
}

/** Numbers that need no data behind them: the period, small counts and those in the labels. */
function numerosLivres(textos: string[]): Valores {
  const livres: Valores = { n: [2023, 2024, 1, 2, 3, 4, 5], pct: [] };
  for (const t of textos) for (const n of numerosDoTexto(t)) (n.pct ? livres.pct : livres.n).push(n.valor);
  return livres;
}

/** The text if every number in it is grounded, else null. */
export function textoAterrado(texto: string, valores: Valores | number[]): string | null {
  return numerosDoTexto(texto).every((n) => numeroConfere(n, valores)) ? texto : null;
}

// ── The arrangers ────────────────────────────────────────────────────────────

const MODELO = process.env.LLM_MODEL ?? "deepseek-chat";
const BASE_URL = process.env.LLM_BASE_URL ?? "https://api.deepseek.com";

function fmtValor(v: unknown): string {
  if (v === null || v === undefined) return "";
  const n = Number(v);
  if (typeof v === "number" || (typeof v === "string" && v.trim() !== "" && Number.isFinite(n))) {
    return Number.isInteger(n) ? String(n) : String(Math.round(n * 10000) / 10000);
  }
  return String(v).slice(0, 40);
}

function dadosParaPrompt(g: GraficoAterrado): string {
  if (g.consultas.length === 0) return "     (sem dados: a consulta não rodou)";
  return g.consultas
    .map((c) => {
      const linhas = c.linhas.slice(0, 60).map((l) => "       " + c.colunas.map((col) => fmtValor(l[col])).join(" | "));
      const resto = c.linhas.length > 60 ? [`       … mais ${c.linhas.length - 60} linhas`] : [];
      return ["       " + c.colunas.join(" | "), ...linhas, ...resto].join("\n");
    })
    .join("\n\n");
}

/** Pulls the first balanced JSON object out of a reply. */
function extrairJson(texto: string): string | null {
  const ini = texto.indexOf("{");
  if (ini === -1) return null;
  let prof = 0;
  let str = false;
  let esc = false;
  for (let i = ini; i < texto.length; i++) {
    const ch = texto[i];
    if (str) {
      if (esc) esc = false;
      else if (ch === "\\") esc = true;
      else if (ch === '"') str = false;
    } else if (ch === '"') str = true;
    else if (ch === "{") prof++;
    else if (ch === "}" && --prof === 0) return texto.slice(ini, i + 1);
  }
  return null;
}

const strs = (v: unknown): string[] => (Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : []);
const str = (v: unknown): string => (typeof v === "string" ? v.trim() : "");

/** The app's LLM, briefed as Veta's arranger was: a McKinsey-trained analyst using Minto's pyramid. */
export const arranjadorLLM: Arranjador = async (graficos, briefing, contexto) => {
  if (!process.env.LLM_API_KEY) return null;
  const blocos = graficos
    .map((g) =>
      [
        `[${g.indice}] ${g.marcado.titulo}`,
        g.marcado.nota ? `     nota do painel: ${g.marcado.nota}` : "",
        `     origem: ${g.tela} · filtros: ${g.filtros}`,
        "     dados (linhas do SQL do gráfico):",
        dadosParaPrompt(g),
      ]
        .filter(Boolean)
        .join("\n"),
    )
    .join("\n\n");

  const sistema = [
    "Você é o arranjador de apresentações do app: um analista treinado na McKinsey que monta uma apresentação executiva a partir de gráficos JÁ FUNDAMENTADOS, usando o princípio da pirâmide de Barbara Minto.",
    "O assunto é o churn da RavenStack (SaaS B2B), de jan/2023 a dez/2024. Escreva em português do Brasil, frases curtas e diretas, sem jargão.",
    "",
    "NÚMEROS — regra inegociável:",
    "- Só escreva um número que apareça nos dados do gráfico (as linhas do SQL abaixo de cada um). Copie o valor arredondado como quiser, mas não calcule nada novo: nada de somas, diferenças, razões, médias ou variações que não estejam nas linhas.",
    "- Formato brasileiro: 22,3% ; 1.077 ; US$ 7,99 mi.",
    "- Na dúvida, fale qualitativamente (\"o maior\", \"cresce\", \"fica estável\"). Uma linha com número fora dos dados será apagada.",
    "- Os dados mostram associação, não causa. Não afirme causa: evite \"causa\", \"por trás\", \"leva a\", \"explica\", \"por causa de\". Descreva o que o gráfico mostra (\"concentra\", \"coincide\", \"é maior em\"). Motivos de cancelamento são o que o cliente declarou, não a causa comprovada.",
    "",
    `- Taxa × fatia: nos gráficos de \"% das contas com churn\" por grupo, o valor é a TAXA do grupo (31% das contas de DevTools tiveram churn), não a fatia do churn total. Escreva \"31% das contas de DevTools tiveram churn\", nunca \"DevTools concentra 31% do churn\". Para falar de fatia, use a coluna ${COLUNA_PARTE} (a parte de cada linha no total); a coluna de contagem é número de contas, nunca porcentagem.`,
    "",
    `RÓTULOS: as linhas trazem códigos do banco em inglês. Escreva como as telas mostram: ${Object.entries(MOTIVOS).map(([k, v]) => `${k} → ${v}`).join(", ")}; feature_N → Recurso N.`,
    "",
    "A PIRÂMIDE:",
    "- ideiaCentral: UMA conclusão que a plateia deve levar (o topo da pirâmide), sustentada pelos gráficos abaixo. Uma frase.",
    "- scqa: situação (o que é estável e consensual), complicação (o que mudou ou incomoda), pergunta (a que a apresentação responde). A resposta é a ideiaCentral.",
    "- secoes: a linha-chave, de 2 a 4 seções MECE (mutuamente exclusivas, coletivamente exaustivas). O título de cada seção é uma AFIRMAÇÃO que resume os gráficos dela, não um rótulo (\"O churn se concentra em DevTools\", não \"Setores\").",
    "- Cada gráfico marcado entra em exatamente uma seção, na ordem que sustenta o argumento (o mais importante primeiro). Use todos os gráficos.",
    "- tituloAcao: o \"e daí\" do gráfico, frase completa de até 14 palavras.",
    "- linhas: 1 ou 2 frases curtas que sustentam o título com o que o gráfico mostra.",
    "- recomendacoes: 2 a 4 ações concretas que decorrem dos achados, com verbo no imperativo. Sem números novos.",
    "",
    contexto?.publico ? `PÚBLICO: ${contexto.publico}${ENFASE[contexto.publico] ? ` — dê ênfase a ${ENFASE[contexto.publico]}` : ""}.` : "",
    briefing ? `OBJETIVO DO USUÁRIO (o briefing; deixe que ele oriente a ideia central e a ênfase): "${briefing}"` : contexto?.publico ? "" : "Sem briefing: o público é a liderança da RavenStack, que quer entender por que o churn sobe.",
    ...(contexto && (contexto.conversas.length || contexto.telas.length)
      ? [
          "",
          "O QUE O USUÁRIO JÁ INVESTIGOU COM O ANALISTA (conversas e telas que ele escolheu como contexto). Leia para entender a pergunta que ele quer responder e o que ele já descobriu: a ideia central, a ordem das seções, os títulos de ação e as recomendações devem refletir essa investigação, não um roteiro genérico. Um número citado aqui só pode ser usado se estiver nas consultas dessas conversas (o código confere e apaga o que não estiver).",
          contextoParaPrompt(contexto),
        ]
      : []),
    "",
    "OS GRÁFICOS MARCADOS:",
    blocos,
    "",
    "RESPONDA SÓ com este objeto JSON (sem texto antes ou depois, sem cercas de código):",
    '{ "titulo": "título da apresentação", "ideiaCentral": "", "scqa": { "situacao": "", "complicacao": "", "pergunta": "" }, "secoes": [ { "titulo": "afirmação da seção", "graficos": [ { "indice": 0, "tituloAcao": "", "linhas": [""] } ] } ], "recomendacoes": [""] }',
  ].join("\n");

  try {
    const client = new OpenAI({ apiKey: process.env.LLM_API_KEY, baseURL: BASE_URL });
    const res = await client.chat.completions.create({
      model: MODELO,
      max_tokens: 4000,
      temperature: 0.3,
      messages: [
        { role: "system", content: sistema },
        { role: "user", content: "Monte a apresentação. Responda só com o JSON." },
      ],
    });
    const json = extrairJson((res.choices[0]?.message?.content ?? "").trim());
    if (!json) return null;
    const p = JSON.parse(json) as Record<string, unknown>;
    const scqa = (p.scqa ?? {}) as Record<string, unknown>;
    return {
      titulo: str(p.titulo),
      ideiaCentral: str(p.ideiaCentral),
      scqa: { situacao: str(scqa.situacao), complicacao: str(scqa.complicacao), pergunta: str(scqa.pergunta) },
      secoes: (Array.isArray(p.secoes) ? p.secoes : []).map((s: Record<string, unknown>) => ({
        titulo: str(s.titulo),
        graficos: (Array.isArray(s.graficos) ? s.graficos : [])
          .filter((g: Record<string, unknown>) => Number.isInteger(g.indice))
          .map((g: Record<string, unknown>) => ({ indice: g.indice as number, tituloAcao: str(g.tituloAcao), linhas: strs(g.linhas) })),
      })),
      recomendacoes: strs(p.recomendacoes),
    };
  } catch {
    return null;
  }
};

/** The always-works arrangement: one section per screen, the panels' own titles. */
export function arranjoPorRegra(graficos: GraficoAterrado[]): Arranjo {
  const ordem = Object.keys(TELAS);
  // The fixed screens first, in menu order; the user's own screens after them (D46.2).
  const pos = (rota: string) => (ordem.includes(rota) ? ordem.indexOf(rota) : ordem.length);
  const porTela = new Map<string, GraficoAterrado[]>();
  for (const g of [...graficos].sort((a, b) => pos(a.marcado.rota) - pos(b.marcado.rota))) {
    porTela.set(g.tela, [...(porTela.get(g.tela) ?? []), g]);
  }
  return {
    titulo: "Diagnóstico de churn da RavenStack",
    ideiaCentral: "O que os dados da RavenStack mostram sobre o churn de jan/2023 a dez/2024",
    scqa: {
      situacao: "A RavenStack é um SaaS B2B com dados de contas, assinaturas, uso e suporte de jan/2023 a dez/2024.",
      complicacao: "O churn preocupa a liderança, e as explicações disponíveis não batem entre si.",
      pergunta: "O que os dados mostram sobre onde e por que o churn acontece?",
    },
    secoes: [...porTela.entries()].map(([tela, gs]) => ({
      titulo: tela,
      graficos: gs.map((g) => ({ indice: g.indice, tituloAcao: g.marcado.titulo, linhas: g.marcado.nota ? [g.marcado.nota] : [] })),
    })),
    recomendacoes: [],
  };
}

// ── Assembly: arrangement + number check ─────────────────────────────────────

const DDL = `CREATE TABLE IF NOT EXISTS deck_marcados (user_id TEXT PRIMARY KEY, json TEXT NOT NULL, criado_em TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS decks_historico (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, json TEXT NOT NULL, criado_em TEXT NOT NULL);`;
// The generation of the app DB the DDL ran on: a DB swapped in from the remote state (D46.4) runs it again.
let pronto = -1;
function db() {
  const d = appdb();
  if (pronto !== appdbGeracao()) {
    d.exec(DDL);
    pronto = appdbGeracao();
  }
  return d;
}

/**
 * Builds and stores the user's presentation from their marked charts. Every number the arranger
 * wrote is checked against the rows of the chart it talks about (or of all charts, for the apex,
 * SCQA and recommendations); what fails is dropped or replaced, and listed in `avisos`.
 */
export async function montarDeck(
  userId: string,
  opts: { briefing?: string | null; publico?: string | null; conversaIds?: string[]; telaIds?: string[]; arranjador?: Arranjador } = {},
): Promise<DeckMarcados> {
  const marcados = listarMarcados(userId);
  if (marcados.length === 0) throw new Error("Nenhum gráfico marcado.");
  const briefing = opts.briefing?.trim() ? opts.briefing.trim().slice(0, 600) : null;
  const graficos = aterrar(userId, marcados);
  const livres = numerosLivres(marcados.flatMap((m) => [m.titulo, m.nota ?? ""]));
  const contexto = carregarContexto(userId, opts);
  // Numbers the user wrote in the brief, and the rows behind the analyst's answers they picked (D46.3).
  const todos = juntar(livres, numerosLivres([briefing ?? ""]), valoresDeSql(contexto.sql), ...graficos.map((g) => g.valores));

  const doLLM = await (opts.arranjador ?? arranjadorLLM)(graficos, briefing, contexto);
  const regra = arranjoPorRegra(graficos);
  const a = doLLM && doLLM.secoes.length > 0 ? doLLM : regra;
  const avisos: string[] = [];
  const conferir = (texto: string, valores: Valores, onde: string): string | null => {
    if (!texto) return null;
    const ok = textoAterrado(texto, valores);
    if (!ok) avisos.push(`${onde}: saiu "${texto}" (número que não está nos dados)`);
    return ok;
  };

  const titulo = conferir(a.titulo, todos, "Título") ?? regra.titulo;
  const ideiaCentral = conferir(a.ideiaCentral, todos, "Ideia central") ?? regra.ideiaCentral;
  const scqa = {
    situacao: conferir(a.scqa.situacao, todos, "Situação") ?? regra.scqa.situacao,
    complicacao: conferir(a.scqa.complicacao, todos, "Complicação") ?? regra.scqa.complicacao,
    pergunta: conferir(a.scqa.pergunta, todos, "Pergunta") ?? regra.scqa.pergunta,
  };

  const usados = new Set<number>();
  const secoes: Secao[] = [];
  a.secoes.forEach((s, k) => {
    const graficosSecao: SlideGrafico[] = [];
    for (const item of s.graficos) {
      const g = graficos[item.indice];
      if (!g || usados.has(item.indice)) continue;
      usados.add(item.indice);
      const valores = juntar(livres, g.valores);
      const onde = `"${g.marcado.titulo}"`;
      graficosSecao.push({
        marcadoId: g.marcado.id,
        tituloAcao: conferir(item.tituloAcao, valores, `Título de ${onde}`) ?? g.marcado.titulo,
        linhas: item.linhas.slice(0, 2).map((l) => conferir(l, valores, `Texto de ${onde}`)).filter((l): l is string => !!l),
        tituloPainel: g.marcado.titulo,
        nota: g.marcado.nota,
        tela: g.tela,
        filtros: g.filtros,
      });
    }
    if (graficosSecao.length > 0) {
      const t = conferir(s.titulo, todos, `Seção ${k + 1}`) ?? `Seção ${k + 1}`;
      secoes.push({ titulo: t, graficos: graficosSecao });
    }
  });
  // Every marked chart is on a slide: the ones the arranger left out close the last section.
  const fora = graficos.filter((g) => !usados.has(g.indice));
  if (fora.length > 0) {
    if (doLLM) avisos.push(`${fora.length} gráfico(s) que o arranjador deixou de fora entraram numa seção à parte`);
    secoes.push({
      titulo: "Outros gráficos marcados",
      graficos: fora.map((g) => ({ marcadoId: g.marcado.id, tituloAcao: g.marcado.titulo, linhas: [], tituloPainel: g.marcado.titulo, nota: g.marcado.nota, tela: g.tela, filtros: g.filtros })),
    });
  }
  const recomendacoes = a.recomendacoes.slice(0, 4).map((r, i) => conferir(r, todos, `Recomendação ${i + 1}`)).filter((r): r is string => !!r);
  if (!doLLM) avisos.push("O LLM não respondeu: a apresentação foi montada por regra (uma seção por tela, títulos dos painéis).");

  const deck: DeckMarcados = {
    titulo, ideiaCentral, scqa, secoes, recomendacoes, briefing,
    publico: contexto.publico,
    fontes: [...contexto.conversas.map((c) => `Conversa: ${c.titulo}`), ...contexto.telas.map((t) => `Tela: ${t.nome}`)],
    autor: doLLM ? "ia" : "regra",
    avisos,
    marcadoIds: marcados.map((m) => m.id),
    criadoEm: new Date().toISOString(),
  };
  // Every build is kept (D46.3): an earlier deck can still be downloaded.
  const ins = db().prepare("INSERT INTO decks_historico (user_id, json, criado_em) VALUES (?, ?, ?)").run(userId, JSON.stringify(deck), deck.criadoEm);
  deck.id = Number(ins.lastInsertRowid);
  db().prepare("UPDATE decks_historico SET json = ? WHERE id = ?").run(JSON.stringify(deck), deck.id);
  db().prepare("INSERT INTO deck_marcados (user_id, json, criado_em) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET json = excluded.json, criado_em = excluded.criado_em")
    .run(userId, JSON.stringify(deck), deck.criadoEm);
  return deck;
}

export function deckAtual(userId: string): DeckMarcados | null {
  const row = db().prepare("SELECT json FROM deck_marcados WHERE user_id = ?").get(userId) as { json: string } | undefined;
  return row ? (JSON.parse(row.json) as DeckMarcados) : null;
}

/** The earlier builds, newest first (D46.3). */
export function historicoDecks(userId: string): { id: number; titulo: string; ideiaCentral: string; publico: string | null; fontes: string[]; criadoEm: string }[] {
  return (db().prepare("SELECT id, json FROM decks_historico WHERE user_id = ? ORDER BY id DESC LIMIT 20").all(userId) as { id: number; json: string }[]).map((r) => {
    const d = JSON.parse(r.json) as DeckMarcados;
    return { id: r.id, titulo: d.titulo, ideiaCentral: d.ideiaCentral, publico: d.publico ?? null, fontes: d.fontes ?? [], criadoEm: d.criadoEm };
  });
}

export function deckDoHistorico(userId: string, id: number): DeckMarcados | null {
  const r = db().prepare("SELECT json FROM decks_historico WHERE user_id = ? AND id = ?").get(userId, id) as { json: string } | undefined;
  return r ? (JSON.parse(r.json) as DeckMarcados) : null;
}

/** True when the marks changed after the deck was built (it must be built again). */
export function deckDesatualizado(userId: string, deck: DeckMarcados): boolean {
  const atuais = listarMarcados(userId).map((m) => m.id).sort((x, y) => x - y);
  const doDeck = [...deck.marcadoIds].sort((x, y) => x - y);
  return atuais.length !== doDeck.length || atuais.some((id, i) => id !== doDeck[i]);
}

// ── The .pptx (Veta's visual language: obsidian and gold, paper for the argument) ──

const OURO = "E3B341";
const OBSIDIANA = "0E0E10";
const PAPEL = "FAF8F4";
const BRANCO = "FFFFFF";
const N300 = "D4D4D4";
const N400 = "A3A3A3";
const N500 = "737373";
const N600 = "525252";
const N900 = "171717";
const PAINEL = "121218";
const FONTE = "Arial";
const MONO = "Courier New";
const X0 = 0.7;
const LARG = 11.93;

type Slide = ReturnType<PptxGenJS["addSlide"]>;

function rodape(s: Slide, texto: string, n: number, escuro: boolean): void {
  s.addText(texto, { x: X0, y: 7.0, w: 10.6, h: 0.25, fontFace: FONTE, fontSize: 9.5, color: escuro ? N500 : N400, margin: 0 });
  s.addText(String(n), { x: 12.13, y: 7.0, w: 0.5, h: 0.25, fontFace: MONO, fontSize: 9.5, color: escuro ? N500 : N400, align: "right", margin: 0 });
}

function rotulo(s: Slide, texto: string, y: number): void {
  s.addText(texto.toUpperCase(), { x: X0, y, w: 8, h: 0.24, fontFace: FONTE, fontSize: 11, bold: true, color: OURO, charSpacing: 3, margin: 0 });
}

export async function deckParaPptx(userId: string, deck: DeckMarcados): Promise<Buffer> {
  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE"; // 13.33 × 7.5 in
  pptx.title = deck.titulo;
  const fonte = "Fonte: base RavenStack, jan/2023 a dez/2024; cada número vem de uma consulta SQL no app";
  let n = 0;

  // 1 — Cover: the governing thought is the hero.
  {
    const s = pptx.addSlide();
    n++;
    s.background = { color: OBSIDIANA };
    rotulo(s, "RavenStack · diagnóstico de churn", 1.45);
    s.addText(deck.titulo, { x: X0, y: 1.85, w: 10.5, h: 1.4, fontFace: FONTE, fontSize: 36, bold: true, color: BRANCO, valign: "top", margin: 0, fit: "shrink" });
    s.addText(deck.ideiaCentral, { x: X0, y: 3.4, w: 9.4, h: 1.2, fontFace: FONTE, fontSize: 17, color: N300, valign: "top", margin: 0, fit: "shrink" });
    s.addShape(pptx.ShapeType.rect, { x: X0, y: 4.95, w: 2.4, h: 0.02, fill: { color: OURO }, line: { type: "none" } });
    s.addText(`Base RavenStack · jan/2023 a dez/2024 · ${new Date(deck.criadoEm).toLocaleDateString("pt-BR")}`, {
      x: X0, y: 6.55, w: 8, h: 0.22, fontFace: MONO, fontSize: 11, color: N500, margin: 0,
    });
  }

  // 2 — Executive summary: the pyramid on one page (apex, then the key line and its support).
  {
    const s = pptx.addSlide();
    n++;
    s.background = { color: PAPEL };
    rotulo(s, "Resumo executivo", 0.45);
    s.addText(deck.ideiaCentral, { x: X0, y: 0.8, w: LARG, h: 0.95, fontFace: FONTE, fontSize: 22, bold: true, color: N900, valign: "top", margin: 0, fit: "shrink" });
    const cols = deck.secoes.length;
    const gap = 0.25;
    const w = (LARG - gap * (cols - 1)) / Math.max(1, cols);
    deck.secoes.forEach((sec, i) => {
      const x = X0 + i * (w + gap);
      s.addShape(pptx.ShapeType.rect, { x, y: 2.0, w, h: 0.04, fill: { color: OURO }, line: { type: "none" } });
      s.addText(String(i + 1).padStart(2, "0"), { x, y: 2.15, w: 0.6, h: 0.3, fontFace: MONO, fontSize: 13, bold: true, color: OURO, margin: 0 });
      s.addText(sec.titulo, { x, y: 2.5, w, h: 1.0, fontFace: FONTE, fontSize: 14, bold: true, color: N900, valign: "top", margin: 0, fit: "shrink" });
      s.addText(
        sec.graficos.map((g) => ({ text: g.tituloAcao, options: { bullet: { code: "25AA" }, breakLine: true, paraSpaceAfter: 6 } })),
        { x, y: 3.6, w, h: 3.1, fontFace: FONTE, fontSize: 11.5, color: N600, valign: "top", margin: 0, fit: "shrink" },
      );
    });
    rodape(s, fonte, n, false);
  }

  // 3 — Context: SCQA, answered by the governing thought.
  {
    const s = pptx.addSlide();
    n++;
    s.background = { color: PAPEL };
    rotulo(s, "Contexto", 0.45);
    s.addText(deck.scqa.pergunta, { x: X0, y: 0.8, w: LARG, h: 0.9, fontFace: FONTE, fontSize: 24, bold: true, color: N900, valign: "top", margin: 0, fit: "shrink" });
    const blocos: [string, string][] = [["Situação", deck.scqa.situacao], ["Complicação", deck.scqa.complicacao], ["Resposta", deck.ideiaCentral]];
    blocos.forEach(([rot, texto], i) => {
      const y = 2.05 + i * 1.55;
      const resposta = rot === "Resposta";
      s.addShape(pptx.ShapeType.rect, { x: X0, y, w: 0.06, h: 1.2, fill: { color: resposta ? OURO : "D4D4D4" }, line: { type: "none" } });
      s.addText(rot.toUpperCase(), { x: X0 + 0.25, y, w: 3, h: 0.25, fontFace: FONTE, fontSize: 10.5, bold: true, color: resposta ? "B8891A" : N500, charSpacing: 2, margin: 0 });
      s.addText(texto, { x: X0 + 0.25, y: y + 0.3, w: LARG - 0.25, h: 0.9, fontFace: FONTE, fontSize: resposta ? 17 : 15, bold: resposta, color: resposta ? N900 : N600, valign: "top", margin: 0, fit: "shrink" });
    });
    rodape(s, fonte, n, false);
  }

  // 4…n — Per section: a divider, then one argument slide per chart.
  for (const [i, sec] of deck.secoes.entries()) {
    {
      const s = pptx.addSlide();
      n++;
      s.background = { color: OBSIDIANA };
      s.addText(String(i + 1).padStart(2, "0"), { x: X0, y: 2.0, w: 2.4, h: 0.74, fontFace: MONO, fontSize: 54, bold: true, color: OURO, margin: 0 });
      s.addText(sec.titulo, { x: X0, y: 2.95, w: 10.5, h: 1.4, fontFace: FONTE, fontSize: 32, bold: true, color: BRANCO, valign: "top", margin: 0, fit: "shrink" });
      s.addText(`${sec.graficos.length} ${sec.graficos.length === 1 ? "gráfico" : "gráficos"}`, { x: X0, y: 4.5, w: 6, h: 0.3, fontFace: FONTE, fontSize: 14, color: N400, margin: 0 });
    }
    for (const g of sec.graficos) {
      const arq = arquivoMarcado(userId, g.marcadoId);
      const m = listarMarcados(userId).find((x) => x.id === g.marcadoId);
      if (!arq || !m) continue;
      const s = pptx.addSlide();
      n++;
      s.background = { color: PAPEL };
      s.addText(sec.titulo.toUpperCase(), { x: X0, y: 0.38, w: LARG, h: 0.22, fontFace: FONTE, fontSize: 9.5, bold: true, color: "B8891A", charSpacing: 2, margin: 0 });
      s.addText(g.tituloAcao, { x: X0, y: 0.65, w: LARG, h: 0.85, fontFace: FONTE, fontSize: 22, bold: true, color: N900, valign: "top", margin: 0, fit: "shrink" });

      // Wide charts take the full width with the text below; the rest sit right of the text.
      const largo = m.largura / m.altura >= 2.2;
      const area = largo ? { x: X0, y: 1.65, w: LARG, h: g.linhas.length ? 4.15 : 5.1 } : { x: 4.95, y: 1.65, w: 7.68, h: 5.1 };
      s.addShape(pptx.ShapeType.roundRect, { ...area, fill: { color: PAINEL }, line: { type: "none" }, rectRadius: 0.06 });
      const pad = 0.15;
      const esc = Math.min((area.w - 2 * pad) / m.largura, (area.h - 2 * pad) / m.altura);
      const iw = m.largura * esc;
      const ih = m.altura * esc;
      s.addImage({ data: arq.png, x: area.x + (area.w - iw) / 2, y: area.y + (area.h - ih) / 2, w: iw, h: ih });

      const texto = [
        ...g.linhas.map((l) => ({ text: l, options: { bullet: { code: "25AA" }, breakLine: true, paraSpaceAfter: 8, color: N600, fontSize: largo ? 13 : 14 } })),
        { text: `${g.tituloPainel}${g.nota ? ` · ${g.nota}` : ""}`, options: { breakLine: true, color: N400, fontSize: 10.5, paraSpaceBefore: 6 } },
      ];
      s.addText(texto, largo ? { x: X0, y: 5.95, w: LARG, h: 0.95, fontFace: FONTE, valign: "top", margin: 0, fit: "shrink" } : { x: X0, y: 1.75, w: 3.95, h: 4.9, fontFace: FONTE, valign: "top", margin: 0, fit: "shrink" });
      rodape(s, `${g.tela} · ${g.filtros} · ${fonte}`, n, false);
    }
  }

  // Last — Recommended actions.
  if (deck.recomendacoes.length > 0) {
    const s = pptx.addSlide();
    n++;
    s.background = { color: OBSIDIANA };
    rotulo(s, "O que fazer", 1.1);
    s.addText("Ações recomendadas", { x: X0, y: 1.45, w: 9, h: 0.6, fontFace: FONTE, fontSize: 32, bold: true, color: BRANCO, margin: 0 });
    s.addText(
      deck.recomendacoes.map((r) => ({ text: r, options: { bullet: { code: "25AA" }, breakLine: true, paraSpaceAfter: 12 } })),
      { x: X0, y: 2.4, w: 10.5, h: 3.6, fontFace: FONTE, fontSize: 17, color: "E5E5E5", valign: "top", margin: 0, fit: "shrink" },
    );
    s.addShape(pptx.ShapeType.rect, { x: X0, y: 6.3, w: 2.4, h: 0.02, fill: { color: OURO }, line: { type: "none" } });
  }

  return (await pptx.write({ outputType: "nodebuffer" })) as Buffer;
}
