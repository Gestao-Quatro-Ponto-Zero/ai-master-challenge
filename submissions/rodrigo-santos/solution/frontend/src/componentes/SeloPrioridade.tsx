/** Etiqueta colorida com a prioridade do deal (verde / amarelo / cinza). */

import type { Prioridade } from "../tipos";

const CLASSES: Record<Prioridade, string> = {
  Alta: "selo-alta",
  Média: "selo-media",
  Baixa: "selo-baixa",
};

export default function SeloPrioridade({ prioridade }: { prioridade: Prioridade }) {
  return <span className={`selo ${CLASSES[prioridade]}`}>{prioridade}</span>;
}
