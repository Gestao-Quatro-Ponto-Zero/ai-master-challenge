import "server-only";
// Fonte dos dados. Hoje: arquivos dentro do app (data/base.json, gerado por scripts/dados.mjs a partir
// dos CSVs limpos, e data/deals_scored.json quando o score existir).
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

type LinhaDeal = [string, string, string, string | null, Estagio, string | null, string | null, number | null];

interface ArquivoBase {
  dataReferencia: string;
  equipe: Base["equipe"];
  produtos: Base["produtos"];
  contas: ContaBase[];
  deals: LinhaDeal[];
}

const pasta = () => path.join(process.cwd(), "data");

async function carregarNotas(): Promise<Map<string, NotaBase>> {
  const arq = path.join(pasta(), "deals_scored.json");
  const notas = new Map<string, NotaBase>();
  if (!existsSync(arq)) return notas;
  const json = JSON.parse(await readFile(arq, "utf8")) as { deals?: Record<string, unknown>[] };
  const n = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? Math.round(v) : null);
  const grupoDe = (k: string): "fit" | "heat" | "bonus" => (k.startsWith("heat") ? "heat" : k.startsWith("bonus") ? "bonus" : "fit");
  for (const d of json.deals ?? []) {
    const comp = (d.components ?? {}) as Record<string, unknown>;
    notas.set(String(d.opportunity_id), {
      score: n(d.score),
      fit: n(d.fit),
      heat: n(d.heat),
      bonus: n(d.bonus),
      acaoSugerida: ["focar", "requalificar", "desistir"].includes(String(d.action)) ? (d.action as NotaBase["acaoSugerida"]) : null,
      valorEsperado: n(d.expected_value),
      marcadores: Array.isArray(d.flags) ? d.flags.map(String) : [],
      componentes: Object.entries(comp).map(([k, v]) => ({ grupo: grupoDe(k), nome: k, pontos: Number(v) || 0, maximo: null })),
      motivos: Array.isArray(d.reasons) ? d.reasons.map(String) : [],
    });
  }
  return notas;
}

export async function carregarBase(): Promise<Base> {
  const [texto, notas] = await Promise.all([readFile(path.join(pasta(), "base.json"), "utf8"), carregarNotas()]);
  const b = JSON.parse(texto) as ArquivoBase;
  return {
    origem: "arquivo",
    notasDisponiveis: notas.size > 0,
    dataReferencia: b.dataReferencia,
    equipe: b.equipe,
    produtos: b.produtos,
    contas: b.contas,
    deals: b.deals.map(([id, vendedor, produto, conta, estagio, dataAbertura, closeDate, closeValue]) => ({
      id, vendedor, produto, conta, estagio, dataAbertura, closeDate, closeValue,
      nome: `${conta ?? "Sem empresa"} · ${produto}`,
    })),
    notas,
  };
}
