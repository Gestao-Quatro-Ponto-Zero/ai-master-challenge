// Relógio do CRM (decisão 48, migration 0034): a data de negócio anda 1 dia por dia real, ancorada em
// 10/11/2026 (America/Sao_Paulo) = 31/12/2017. É a mesma conta de system_data_negocio() no banco.
import { CONFIG } from "./config";

const DIA = 86_400_000;
const utc = (iso: string) => Date.parse(`${iso}T00:00:00Z`);
const paraIso = (ms: number) => new Date(ms).toISOString().slice(0, 10);

// Um formatador só (criar um a cada chamada pesa: a reserva em memória pede a data para cada um dos 8.800 deals).
const formatoDia = new Intl.DateTimeFormat("sv-SE", { timeZone: CONFIG.fusoHorario, year: "numeric", month: "2-digit", day: "2-digit" });

/** Dia real (AAAA-MM-DD) no fuso do CRM. */
export function diaRealEm(agora: Date = new Date()): string {
  return formatoDia.format(agora);
}

let ultimo: { diaReal: string; negocio: string } | null = null;

/** Data de negócio de um dia real: âncora de negócio + dias reais desde a âncora real. */
export function dataNegocioEm(diaReal: string): string {
  if (ultimo?.diaReal === diaReal) return ultimo.negocio;
  const { ancoraReal, ancoraNegocio } = CONFIG.relogio;
  const negocio = paraIso(utc(ancoraNegocio) + (utc(diaReal) - utc(ancoraReal)));
  ultimo = { diaReal, negocio };
  return negocio;
}

/** Data de negócio de agora. */
export const dataNegocioAgora = (agora: Date = new Date()): string => dataNegocioEm(diaRealEm(agora));

/** Domingo? (dia do job semanal do score) */
export const ehDomingo = (data: string): boolean => new Date(utc(data)).getUTCDay() === 0;

/** Dias entre duas datas AAAA-MM-DD (b − a). */
export const diasEntreDatas = (a: string, b: string): number => Math.round((utc(b) - utc(a)) / DIA);
