// Explicação da nota no deal (O-36): a conta, a contribuição de cada parte e os itens de cada componente.
// Só organiza os mesmos dados do score (score_deals e score_componentes); não recalcula a nota.
import { CONFIG } from "./config";
import type { Componente } from "./tipos";

export type Grupo = Componente["grupo"];

export const ROTULO_GRUPO: Record<Grupo, { nome: string; sigla: string; peso: string }> = {
  fit: { nome: "Encaixe com o vendedor", sigla: "FIT", peso: `peso ${Math.round(CONFIG.pesosNota.fit * 100)}%` },
  heat: { nome: "Tempo de atendimento", sigla: "HEAT", peso: `peso ${Math.round(CONFIG.pesosNota.heat * 100)}%` },
  bonus: { nome: "Bônus da empresa", sigla: "BONUS", peso: "soma direto, de 0 a 20" },
};

const num = (v: number, casas = 1) => v.toLocaleString("pt-BR", { maximumFractionDigits: casas });

/** "0,7 × 66 + 0,3 × 10 + 5 = 54" */
export function contaDaNota(fit: number, heat: number, bonus: number, nota: number): string {
  return `${num(CONFIG.pesosNota.fit)} × ${num(fit)} + ${num(CONFIG.pesosNota.heat)} × ${num(heat)} + ${num(bonus)} = ${num(nota)}`;
}

/** Quanto cada parte soma na nota (para a barra empilhada). */
export function contribuicoes(fit: number, heat: number, bonus: number): Record<Grupo, number> {
  return { fit: fit * CONFIG.pesosNota.fit, heat: heat * CONFIG.pesosNota.heat, bonus };
}

/** Itens de um componente, sem a linha de contribuição ("Encaixe com o vendedor (70%)"), que já está na conta. */
export function itensDoGrupo(componentes: Componente[], grupo: Grupo): Componente[] {
  return componentes.filter((c) => c.grupo === grupo && !/\(\d+%\)\s*$/.test(c.nome));
}

/** "4,7 / 10,9" · "0 / 10" · "−4,9 / 10,9" */
export function pontosDoItem(c: Pick<Componente, "pontos" | "maximo">): string {
  const p = `${c.pontos < 0 ? "−" : ""}${num(Math.abs(c.pontos))}`;
  return c.maximo === null ? p : `${p} / ${num(c.maximo)}`;
}
