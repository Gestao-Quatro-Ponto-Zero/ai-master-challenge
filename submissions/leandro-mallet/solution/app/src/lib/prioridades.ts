// Contas e ordem das Prioridades do dia. "Feitas" são só as marcadas com ✓; o ✗ (pulada) não conta para a meta.
// A ordem é a mesma do banco (migration 0030, acao_montar_prioridades), para todos os papéis:
//   1) atendimento atrasado; 2) lead novo (até 1 dia, sem contato) com FIT >= 75; 3) os demais;
//   em cada grupo, maior nota, depois maior HEAT, depois o código do deal. O valor esperado não entra.
import { moedaNoTexto } from "./calculos";
import { CONFIG } from "./config";
import type { DealVisao, Prioridade } from "./tipos";

export interface ResumoPrioridades {
  feitas: number;
  puladas: number;
  pendentes: number;
  /** Meta do dia: 10, ou o tamanho da lista quando a pessoa puxou mais. */
  meta: number;
}

export function resumoPrioridades(itens: Pick<Prioridade, "marcada">[]): ResumoPrioridades {
  return {
    feitas: itens.filter((i) => i.marcada === "feita").length,
    puladas: itens.filter((i) => i.marcada === "pulada").length,
    pendentes: itens.filter((i) => !i.marcada).length,
    meta: Math.max(CONFIG.metaPrioridadesDia, itens.length),
  };
}

/** O que a ordem precisa saber de um deal. */
export interface ItemOrdem {
  id: string;
  score: number | null;
  heat: number | null;
  fit: number | null;
  /** Momento em que o lead foi criado no CRM (nulo nos deals do dataset). */
  criadoEm: string | null;
  /** Há contato registrado no CRM? */
  comContato: boolean;
  marcadores: string[];
}

/** 0 = atendimento atrasado; 1 = lead novo com FIT alto; 2 = os demais. hoje = dia real (AAAA-MM-DD, no fuso do CRM). */
export function grupoPrioridade(d: ItemOrdem, hoje: string): 0 | 1 | 2 {
  if (d.comContato) return 2;
  if (d.marcadores.includes("atendimento_atrasado")) return 0;
  if (!d.criadoEm || (d.fit ?? 0) < CONFIG.fitMinimoFurarFila) return 2;
  const criado = new Date(d.criadoEm).toLocaleDateString("sv-SE", { timeZone: CONFIG.fusoHorario });
  const dias = Math.round((Date.parse(`${hoje}T00:00:00Z`) - Date.parse(`${criado}T00:00:00Z`)) / 86_400_000);
  return dias > 1 ? 0 : 1;
}

export function compararPrioridade(a: ItemOrdem, b: ItemOrdem, hoje: string): number {
  const nn = (v: number | null) => (v === null ? -Infinity : v);
  return (
    grupoPrioridade(a, hoje) - grupoPrioridade(b, hoje) ||
    nn(b.score) - nn(a.score) ||
    nn(b.heat) - nn(a.heat) ||
    (a.id < b.id ? -1 : a.id > b.id ? 1 : 0)
  );
}

export type FiltroGestor = "icone" | "atencao" | "todos";

/** Quais deals do escopo entram na lista do manager e do admin (o vendedor recebe todos os dele). */
export function entraNaListaDoGestor(d: Pick<DealVisao, "icone">, grupo: 0 | 1 | 2, filtro: FiltroGestor): boolean {
  if (filtro === "todos") return true;
  if (filtro === "atencao") return grupo < 2 || d.icone === "em_risco";
  return d.icone === "super_hot" || d.icone === "em_risco";
}

/** Linha de explicação do item: o 1º motivo da nota (score_motivos, ordem 1). */
export function explicacaoDoItem(motivos: readonly string[] | undefined): string | null {
  const m = motivos?.[0]?.trim();
  return m ? moedaNoTexto(m) : null;
}
