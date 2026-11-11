// Funções puras: datas, ícone, faixa da nota, textos e formatação. Sem I/O.
import { CONFIG } from "./config";
import type { Estagio, FaixaNota, Icone, MotivoPerda, Porte } from "./tipos";

const DIA = 86_400_000;

export function diasEntre(de: string, ate: string): number {
  return Math.round((Date.parse(ate) - Date.parse(de)) / DIA);
}

export function somarDias(data: string, dias: number): string {
  return new Date(Date.parse(data) + dias * DIA).toISOString().slice(0, 10);
}

export function faixaNota(score: number | null): FaixaNota | null {
  if (score === null) return null;
  if (score >= CONFIG.faixasNota.alta) return "alta";
  if (score >= CONFIG.faixasNota.media) return "media";
  return "baixa";
}

/** Ícone do cartão (ESPEC-TELAS 2.4). diasSemContato considera só contatos registrados no CRM. */
export function icone(estagio: Estagio, dias: number | null, preco: number, diasSemContato: number | null): Icone | null {
  const c = CONFIG.icone;
  if (estagio !== "Engaging" || dias === null) return null;
  if (dias > c.diasMaxRisco) return "esfriou";
  if (dias > c.diasMaxQuente) return "em_risco";
  if (diasSemContato !== null && diasSemContato >= CONFIG.diasSemContatoRisco) return "em_risco";
  if (dias >= c.diasMinQuente && (c.precoMinQuente === null || preco >= c.precoMinQuente)) return "super_hot";
  return null;
}

export const ROTULO_ESTAGIO: Record<Estagio, string> = {
  Prospecting: "Prospecção",
  Engaging: "Em negociação",
  Won: "Fechado",
  Lost: "Perdido",
};

export const ROTULO_ICONE: Record<Icone, string> = {
  super_hot: "Super hot",
  em_risco: "Em risco de esfriar",
  esfriou: "Esfriou",
};

export const ROTULO_PORTE: Record<Porte, string> = { pequena: "pequena", media: "média", grande: "grande" };

export const ROTULO_MOTIVO: Record<MotivoPerda, string> = {
  preco: "Preço",
  concorrente: "Concorrente",
  sem_orcamento: "Sem orçamento",
  sem_resposta: "Sem resposta",
  outro: "Outro",
  cadastro_desfeito: "Cadastro desfeito",
};

export const SETORES: Record<string, string> = {
  employment: "recrutamento",
  entertainment: "entretenimento",
  finance: "finanças",
  marketing: "marketing",
  medical: "saúde",
  retail: "varejo",
  services: "serviços",
  software: "software",
  technology: "tecnologia",
  telecommunications: "telecomunicações",
};

export function rotuloSetor(setor: string | null): string {
  return setor ? (SETORES[setor] ?? setor) : "—";
}

export function nomePadrao(conta: string | null, produto: string): string {
  return `${conta?.trim() || "Sem empresa"} · ${produto}`;
}

/** Frase do ícone, mostrada ao passar o mouse e lida pelo leitor de tela. */
export function fraseIcone(i: Icone, dias: number | null): string {
  if (i === "super_hot") return "Na fase em que mais deals viram ganho.";
  if (i === "em_risco")
    return dias !== null && dias > CONFIG.icone.diasMaxQuente
      ? `Aberto há ${dias} dias. 90% dos ganhos fecham em até ${CONFIG.icone.diasMaxQuente} dias.`
      : `Sem contato há ${CONFIG.diasSemContatoRisco} dias ou mais.`;
  return `Aberto há ${dias ?? "muitos"} dias, mais que qualquer deal já fechado (${CONFIG.icone.diasMaxRisco}). Requalifique ou encerre.`;
}

// Moeda: o formatador único do CRM. Os valores do dataset são mostrados em reais, com os mesmos números
// (decisão do Leandro, adendo à O-30): troca só o símbolo e o formato, sem conversão de câmbio.
export const SIMBOLO_MOEDA = "R$";
export const NOME_MOEDA = "reais";
const inteiroFmt = new Intl.NumberFormat("pt-BR");

/** R$ 5.482 (inteiro, sem centavos). */
export function dinheiro(v: number | null | undefined): string {
  return v === null || v === undefined ? "—" : `${SIMBOLO_MOEDA} ${inteiroFmt.format(Math.round(v))}`;
}

/** R$ 1,1 mi / R$ 95 mil / R$ 3.525 */
export function dinheiroCurto(v: number): string {
  if (v >= 1_000_000) return `${SIMBOLO_MOEDA} ${(v / 1_000_000).toLocaleString("pt-BR", { maximumFractionDigits: 2 })} mi`;
  if (v >= 100_000) return `${SIMBOLO_MOEDA} ${Math.round(v / 1000).toLocaleString("pt-BR")} mil`;
  return dinheiro(v);
}

/** Valor em milhões (receita anual da empresa): R$ 12,5 mi. */
export function dinheiroMilhoes(v: number): string {
  return `${SIMBOLO_MOEDA} ${v.toLocaleString("pt-BR")} mi`;
}

/** Textos que já chegam prontos do banco e do score ("US$ 3300", "US$ 194.957"): passam para o formato do CRM. */
export function moedaNoTexto(t: string): string {
  return t.replace(/(?:US|R)\$ ?(\d{1,3}(?:\.\d{3})+|\d+)/g, (_, n: string) => dinheiro(Number(n.replace(/\./g, ""))));
}

export function inteiro(v: number): string {
  return inteiroFmt.format(v);
}

export function plural(n: number, um: string, varios: string): string {
  return `${inteiro(n)} ${n === 1 ? um : varios}`;
}

export function dataBR(iso: string | null): string {
  if (!iso) return "—";
  const [a, m, d] = iso.slice(0, 10).split("-");
  return `${d}/${m}/${a}`;
}

export function dataCurta(iso: string | null): string {
  if (!iso) return "—";
  const [, m, d] = iso.slice(0, 10).split("-");
  return `${d}/${m}`;
}

/** Variação percentual com seta; null quando não há base (nunca ∞%). */
export function variacao(atual: number, anterior: number): { texto: string; sobe: boolean } | null {
  if (!anterior) return null;
  const p = Math.round(((atual - anterior) / anterior) * 100);
  return { texto: `${p >= 0 ? "↑" : "↓"} ${Math.abs(p)}%`, sobe: p >= 0 };
}

export function slug(nome: string): string {
  return nome.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

export function semAcento(t: string): string {
  return t.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
}
