import type { Level, PathKey } from "@/lib/types"

/** Os 3 caminhos da triagem na interface (PRD §5). "nível 1/2/3" fica só no banco e nas ADRs. */
export const PATHS: Record<PathKey, { level: Level; label: string; short: string; description: string }> = {
  auto: {
    level: 1,
    label: "Resposta automática",
    short: "Automática",
    description: "A IA responde adaptando uma solução já validada por humanos.",
  },
  review: {
    level: 2,
    label: "Revisão humana",
    short: "Revisão",
    description: "A IA redige um rascunho e um atendente aprova, edita ou rejeita antes do envio.",
  },
  human: {
    level: 3,
    label: "Somente humano",
    short: "Humano",
    description: "A IA classifica e resume; o atendimento é feito por uma pessoa.",
  },
}

export function pathFromLevel(level: Level | number | null | undefined): PathKey {
  if (level === 1) return "auto"
  if (level === 2) return "review"
  return "human"
}
