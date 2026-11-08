/**
 * Marcações do vendedor sobre cada deal (Feito, Adiar, Não está vivo).
 * Só no navegador (localStorage): o app não tem backend nem login. Parte pura e testada;
 * o acesso ao storage fica em `useMarks.ts`.
 */
export type Mark = "feito" | "adiado" | "morto";
export type Marks = Readonly<Record<string, Mark>>;

/** Versionada: se o formato mudar, a versão nova ignora o que a antiga gravou em vez de quebrar. */
export const MARKS_KEY = "lead-scorer:marcas:v1";
const VERSION = 1;
const VALID: ReadonlySet<string> = new Set<Mark>(["feito", "adiado", "morto"]);

/** Tolerante a qualquer lixo: valor ausente, JSON inválido, formato ou versão diferentes → vazio. */
export function parseMarks(raw: string | null): Marks {
  if (!raw) return {};
  let data: unknown;
  try {
    data = JSON.parse(raw);
  } catch {
    return {};
  }
  if (typeof data !== "object" || data === null || Array.isArray(data)) return {};
  const { v, marks } = data as { v?: unknown; marks?: unknown };
  if (v !== VERSION || typeof marks !== "object" || marks === null || Array.isArray(marks)) return {};
  const out: Record<string, Mark> = {};
  for (const [id, mark] of Object.entries(marks)) {
    // "__proto__" nunca é id de deal; descartar evita qualquer surpresa com o protótipo.
    if (id !== "__proto__" && typeof mark === "string" && VALID.has(mark)) out[id] = mark as Mark;
  }
  return out;
}

export function serializeMarks(marks: Marks): string {
  return JSON.stringify({ v: VERSION, marks });
}

/** Devolve um novo objeto; `null` remove a marcação (desfazer). */
export function withMark(marks: Marks, id: string, mark: Mark | null): Marks {
  const { [id]: _removed, ...rest } = marks;
  void _removed;
  return mark ? { ...rest, [id]: mark } : rest;
}

/** Feito e "não está vivo" tiram o deal da fila; adiado continua nela, só vai para o fim. */
export const isResolved = (mark: Mark | undefined) => mark === "feito" || mark === "morto";
