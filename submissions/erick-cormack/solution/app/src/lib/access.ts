// Acesso de demonstração: válido por 15 dias a partir de 05/11/2026.
export const ACCESS_EXPIRES_AT = new Date("2026-11-20T23:59:59-03:00");

export function isAccessExpired(now: Date = new Date()): boolean {
  return now > ACCESS_EXPIRES_AT;
}

export const ACCESS_EXPIRES_LABEL = ACCESS_EXPIRES_AT.toLocaleDateString("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: "America/Sao_Paulo",
});
