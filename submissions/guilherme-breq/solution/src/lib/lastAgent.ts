/** Último vendedor que abriu o app neste navegador (para abrir direto na fila dele). Só no navegador. */
export const AGENT_KEY = "lead-scorer:vendedor:v1";
const VERSION = 1;
/** Nome de vendedor tem dezenas de caracteres; acima disto é lixo, não nome. */
const MAX_NAME = 80;

/** Tolerante a qualquer lixo: devolve "" (ninguém lembrado). */
export function parseAgent(raw: string | null): string {
  if (!raw) return "";
  try {
    const data: unknown = JSON.parse(raw);
    if (typeof data !== "object" || data === null || Array.isArray(data)) return "";
    const { v, agent } = data as { v?: unknown; agent?: unknown };
    return v === VERSION && typeof agent === "string" && agent.length <= MAX_NAME ? agent : "";
  } catch {
    return "";
  }
}

export const serializeAgent = (agent: string) => JSON.stringify({ v: VERSION, agent });
