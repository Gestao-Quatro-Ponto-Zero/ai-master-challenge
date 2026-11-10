import "server-only";
// As rotas da rotina só respondem a quem manda "Authorization: Bearer <CRON_SECRET>" (a Vercel manda sozinha no cron).
// Sem o segredo configurado, ninguém entra.
import { createHash, timingSafeEqual } from "node:crypto";

const resumo = (t: string) => createHash("sha256").update(t).digest();

export function rotinaAutorizada(cabecalho: string | null): boolean {
  const segredo = process.env.CRON_SECRET;
  if (!segredo || !cabecalho?.startsWith("Bearer ")) return false;
  // compara os resumos (mesmo tamanho), em tempo constante
  return timingSafeEqual(resumo(cabecalho.slice("Bearer ".length)), resumo(segredo));
}
