import "server-only";
// Fonte dos dados. Hoje: arquivos (CSVs limpos + deals_scored.json quando existir).
// Depois: o banco (views e functions de solution/db), sem mexer nas telas — elas só usam o repositório.
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import type { Estagio, Porte } from "@/lib/tipos";

export interface DealBase {
  id: string;
  nome: string;
  vendedor: string;
  produto: string;
  conta: string | null;
  estagio: Estagio;
  dataAbertura: string | null;
  closeDate: string | null;
  closeValue: number | null;
}

export interface ContaBase {
  nome: string;
  setor: string | null;
  anoFundacao: number | null;
  receitaMilhoes: number | null;
  funcionarios: number | null;
  porte: Porte | null;
  sede: string | null;
  empresaMae: string | null;
}

export interface NotaBase {
  score: number | null;
  fit: number | null;
  heat: number | null;
  bonus: number | null;
  acaoSugerida: "focar" | "requalificar" | "desistir" | null;
  valorEsperado: number | null;
  marcadores: string[];
  componentes: { grupo: "fit" | "heat" | "bonus"; nome: string; pontos: number; maximo: number | null }[];
  motivos: string[];
}

export interface Base {
  origem: "arquivo";
  notasDisponiveis: boolean;
  dataReferencia: string;
  equipe: { vendedor: string; manager: string; regiao: string }[];
  produtos: { nome: string; serie: string; preco: number }[];
  contas: ContaBase[];
  deals: DealBase[];
  notas: Map<string, NotaBase>;
}

function pastaDados(): string {
  return process.env.G4_DADOS_DIR || path.resolve(process.cwd(), "..", "data");
}

/** CSV simples com aspas opcionais (os arquivos limpos não têm quebra de linha dentro de campo). */
export function lerCsv(texto: string): Record<string, string>[] {
  const linhas = texto.replace(/\r/g, "").split("\n").filter((l) => l.length > 0);
  const campos = (l: string): string[] => {
    const out: string[] = [];
    let atual = "";
    let aspas = false;
    for (let i = 0; i < l.length; i++) {
      const c = l[i];
      if (c === '"') {
        if (aspas && l[i + 1] === '"') { atual += '"'; i++; } else aspas = !aspas;
      } else if (c === "," && !aspas) { out.push(atual); atual = ""; } else atual += c;
    }
    out.push(atual);
    return out;
  };
  const [cab, ...resto] = linhas;
  if (!cab) return [];
  const nomes = campos(cab);
  return resto.map((l) => {
    const v = campos(l);
    return Object.fromEntries(nomes.map((n, i) => [n, v[i] ?? ""]));
  });
}

const vazio = (t: string | undefined) => (t === undefined || t.trim() === "" ? null : t.trim());
const num = (t: string | undefined) => (vazio(t) === null ? null : Number(t));
const int = (t: string | undefined) => (vazio(t) === null ? null : Math.round(Number(t)));

async function carregarNotas(pasta: string): Promise<Map<string, NotaBase>> {
  const arq = path.join(pasta, "scored", "deals_scored.json");
  const notas = new Map<string, NotaBase>();
  if (!existsSync(arq)) return notas;
  const json = JSON.parse(await readFile(arq, "utf8")) as { deals?: Record<string, unknown>[] };
  for (const d of json.deals ?? []) {
    const comp = (d.components ?? {}) as Record<string, number>;
    const grupoDe = (k: string): "fit" | "heat" | "bonus" => (k.startsWith("heat") ? "heat" : k.startsWith("bonus") ? "bonus" : "fit");
    notas.set(String(d.opportunity_id), {
      score: typeof d.score === "number" ? Math.round(d.score) : null,
      fit: typeof d.fit === "number" ? Math.round(d.fit) : null,
      heat: typeof d.heat === "number" ? Math.round(d.heat) : null,
      bonus: typeof d.bonus === "number" ? Math.round(d.bonus) : null,
      acaoSugerida: (d.action as NotaBase["acaoSugerida"]) ?? null,
      valorEsperado: typeof d.expected_value === "number" ? Math.round(d.expected_value) : null,
      marcadores: Array.isArray(d.flags) ? (d.flags as string[]) : [],
      componentes: Object.entries(comp).map(([k, v]) => ({ grupo: grupoDe(k), nome: k, pontos: Number(v), maximo: null })),
      motivos: Array.isArray(d.reasons) ? (d.reasons as string[]) : [],
    });
  }
  return notas;
}

export async function carregarBase(): Promise<Base> {
  const pasta = pastaDados();
  const ler = async (n: string) => lerCsv(await readFile(path.join(pasta, "clean", n), "utf8"));
  const [equipe, produtos, contas, deals, notas] = await Promise.all([
    ler("sales_teams.csv"),
    ler("products.csv"),
    ler("accounts.csv"),
    ler("deals.csv"),
    carregarNotas(pasta),
  ]);
  return {
    origem: "arquivo",
    notasDisponiveis: notas.size > 0,
    dataReferencia: "2017-12-31",
    equipe: equipe.map((r) => ({ vendedor: r.sales_agent ?? "", manager: r.manager ?? "", regiao: r.regional_office ?? "" })),
    produtos: produtos.map((r) => ({ nome: r.product ?? "", serie: r.series ?? "", preco: Math.round(Number(r.sales_price)) })),
    contas: contas.map((r) => ({
      nome: r.account ?? "",
      setor: vazio(r.sector),
      anoFundacao: int(r.year_established),
      receitaMilhoes: num(r.revenue),
      funcionarios: int(r.employees),
      porte: (vazio(r.employees_band) as Porte | null) ?? null,
      sede: vazio(r.office_location),
      empresaMae: vazio(r.subsidiary_of),
    })),
    deals: deals.map((r) => ({
      id: r.opportunity_id ?? "",
      nome: `${vazio(r.account) ?? "Sem empresa"} · ${r.product ?? ""}`,
      vendedor: r.sales_agent ?? "",
      produto: r.product ?? "",
      conta: vazio(r.account),
      estagio: (r.deal_stage ?? "Prospecting") as Estagio,
      dataAbertura: vazio(r.engage_date),
      closeDate: vazio(r.close_date),
      closeValue: int(r.close_value),
    })),
    notas,
  };
}
