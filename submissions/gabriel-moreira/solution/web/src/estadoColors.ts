import type { Estado } from "./types";

/** Mapa único de cor por ESTADO — aplicado aos chips de filtro, à
 * listagem, ao painel de detalhe e ao rollup, para que um estado nunca
 * receba cores diferentes em superfícies diferentes (Requirement
 * "Identidade visual"). A cor de alerta é exclusiva de Desistir. */
export const ESTADO_CHIP_ATIVO: Record<Estado, string> = {
  foco_urgente: "bg-gold text-navy border-gold",
  acompanhar: "bg-navy text-white border-navy",
  engajar: "bg-navy/80 text-white border-navy/80",
  qualificar: "bg-gray-300 text-navy border-gray-400",
  desistir: "bg-alert text-white border-alert",
};

export const ESTADO_BADGE: Record<Estado, string> = {
  foco_urgente: "bg-gold/15 text-navy border-gold",
  acompanhar: "bg-navy/10 text-navy border-navy/30",
  engajar: "bg-navy/5 text-navy border-navy/20",
  qualificar: "bg-gray-100 text-navy border-gray-300",
  desistir: "bg-alert/10 text-alert border-alert",
};

export const ESTADO_TEXT: Record<Estado, string> = {
  foco_urgente: "text-navy",
  acompanhar: "text-navy",
  engajar: "text-navy",
  qualificar: "text-navy",
  desistir: "text-alert",
};

/** Mesma identidade visual, em hex — recharts pinta com `fill`, que não
 * aceita classes Tailwind. Mantém a mesma progressão navy→cinza→gold e
 * reserva alert exclusivamente para Desistir, como nas demais superfícies. */
export const ESTADO_CHART_COLOR: Record<Estado, string> = {
  foco_urgente: "#B9915B",
  acompanhar: "#001F35",
  engajar: "#4A6580",
  qualificar: "#9CA3AF",
  desistir: "#AF4332",
};
