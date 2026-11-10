import type { ViewOption } from "@/components/shared/view-toggle"

/** Toggles internos das 3 áreas (PRD §3). A primeira opção é o padrão. */
export const PAINEL_VIEWS = [
  { value: "diagnostico", label: "Diagnóstico" },
  { value: "roi", label: "ROI" },
  { value: "operacao", label: "Operação" },
] as const satisfies readonly ViewOption[]

export const CONSOLE_VIEWS = [
  { value: "triagem", label: "Triagem" },
  { value: "fila", label: "Fila" },
  { value: "caixa", label: "Caixa" },
] as const satisfies readonly ViewOption[]

export const METODO_VIEWS = [
  { value: "proposta", label: "Proposta" },
  { value: "decisoes", label: "Decisões" },
  { value: "conducao", label: "Condução" },
] as const satisfies readonly ViewOption[]

export type PainelView = (typeof PAINEL_VIEWS)[number]["value"]
export type ConsoleView = (typeof CONSOLE_VIEWS)[number]["value"]
export type MetodoView = (typeof METODO_VIEWS)[number]["value"]

/** Lê o valor de um toggle de searchParams, com fallback para a primeira opção. */
export function readView<V extends string>(raw: string | string[] | undefined, options: readonly { value: V }[]): V {
  const v = Array.isArray(raw) ? raw[0] : raw
  return (options.find((o) => o.value === v)?.value ?? options[0].value) as V
}
