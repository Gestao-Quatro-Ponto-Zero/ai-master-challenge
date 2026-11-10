// Contas das Prioridades do dia. "Feitas" são só as marcadas com ✓; o ✗ (pulada) não conta para a meta.
import { CONFIG } from "./config";
import type { Prioridade } from "./tipos";

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
