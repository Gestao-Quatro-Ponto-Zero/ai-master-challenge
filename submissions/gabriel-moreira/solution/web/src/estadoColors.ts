import type { Estado } from "./types";

/** Mapa único de cor por ESTADO — aplicado aos chips de filtro, à
 * listagem, ao painel de detalhe e ao rollup, para que um estado nunca
 * receba cores diferentes em superfícies diferentes (Requirement
 * "Identidade visual"). A cor de alerta é exclusiva de `revisao_lote`. */
export const ESTADO_CHIP_ATIVO: Record<Estado, string> = {
  prioritize: "bg-gold text-navy border-gold",
  acompanhar: "bg-navy text-white border-navy",
  qualificar: "bg-gray-300 text-navy border-gray-400",
  revisao_lote: "bg-alert text-white border-alert",
};

export const ESTADO_BADGE: Record<Estado, string> = {
  prioritize: "bg-gold/15 text-navy border-gold",
  acompanhar: "bg-navy/10 text-navy border-navy/30",
  qualificar: "bg-gray-100 text-navy border-gray-300",
  revisao_lote: "bg-alert/10 text-alert border-alert",
};

export const ESTADO_TEXT: Record<Estado, string> = {
  prioritize: "text-navy",
  acompanhar: "text-navy",
  qualificar: "text-navy",
  revisao_lote: "text-alert",
};

/** Mesma identidade visual, em hex — recharts pinta com `fill`, que não
 * aceita classes Tailwind. Mantém a mesma progressão navy→cinza→gold e
 * reserva alert exclusivamente para `revisao_lote`, como nas demais
 * superfícies. */
export const ESTADO_CHART_COLOR: Record<Estado, string> = {
  prioritize: "#B9915B",
  acompanhar: "#001F35",
  qualificar: "#9CA3AF",
  revisao_lote: "#AF4332",
};

/** Marcador de sobrecarga — dourado (`gold`, #B9915B), distinto do
 * vermelho de alerta exclusivo de `revisao_lote` (design.md, D7: "dois
 * alertas na mesma tela precisam ser distinguíveis"). */
export const SOBRECARGA_COLOR = "#B9915B";
export const SOBRECARGA_BADGE_CLASSES = "bg-red-400 text-navy border-gold";
