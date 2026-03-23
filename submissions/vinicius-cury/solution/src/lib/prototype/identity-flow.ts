// ─── Identity Flow State Machine ────────────────────────────────────
// Handles chat-based identity collection before classification begins.
// Only applies to user-initiated conversations (not simulation-created).

export type IdentityState =
  | "greeting"
  | "asking_name"
  | "asking_email"
  | "returning_user_check"
  | "ready"
  | "support";

export interface IdentityContext {
  state: IdentityState;
  name?: string;
  email?: string;
  isReturning?: boolean;
  previousTickets?: number;
}

// ─── Email Extraction ───────────────────────────────────────────────

const EMAIL_REGEX = /[\w.-]+@[\w.-]+\.\w{2,}/;

export function extractEmail(text: string): string | null {
  const match = text.match(EMAIL_REGEX);
  return match ? match[0].toLowerCase() : null;
}

// ─── Name Extraction ────────────────────────────────────────────────

export function extractName(text: string): string {
  // Clean up the input
  const cleaned = text.trim();

  // If user says something like "Meu nome é João" or "Me chamo João"
  const namePatterns = [
    /(?:meu nome [eé]|me chamo|sou(?: o| a)?|pode me chamar de)\s+(.+)/i,
  ];

  for (const pattern of namePatterns) {
    const match = cleaned.match(pattern);
    if (match) {
      return capitalizeWords(match[1].trim());
    }
  }

  // If short (1-3 words), treat the whole thing as the name
  const words = cleaned.split(/\s+/);
  if (words.length <= 3) {
    return capitalizeWords(cleaned);
  }

  // Otherwise, take the first two words
  return capitalizeWords(words.slice(0, 2).join(" "));
}

function capitalizeWords(str: string): string {
  return str
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

// ─── Returning User Detection (intent) ─────────────────────────────

export function detectContinueIntent(text: string): "continue" | "new" | "unclear" {
  const continuePatterns = [
    /\b(continu|anterior|último|ultima|aberto|pendente|sim|quero\s+continu)/i,
  ];
  const newPatterns = [
    /\b(nov[oa]|abrir|diferente|outro|n[aã]o)/i,
  ];

  const isContinue = continuePatterns.some((p) => p.test(text));
  const isNew = newPatterns.some((p) => p.test(text));

  if (isContinue && !isNew) return "continue";
  if (isNew && !isContinue) return "new";
  return "unclear";
}

// ─── Ticket Status Intent Detection ─────────────────────────────────

export function detectTicketStatusIntent(text: string): boolean {
  const patterns = [
    /status\s+d[eo]\s+(meu|minha)?\s*(ticket|chamado|atendimento)/i,
    /meu[s]?\s+(ticket|chamado|atendimento)/i,
    /como\s+(est[aá]|anda)\s+(meu|minha)?\s*(ticket|chamado|atendimento)/i,
    /verificar\s+(meu|minha)?\s*(ticket|chamado|atendimento)/i,
    /consultar\s+(meu|minha)?\s*(ticket|chamado|atendimento)/i,
  ];
  return patterns.some((p) => p.test(text));
}

// ─── Response Messages ─────────────────────────────────────────────

export const IDENTITY_MESSAGES = {
  welcome:
    "Olá! Sou o assistente virtual da OptiFlow. Como posso ajudar você hoje?",
  askName:
    "Para que eu possa te ajudar melhor, pode me dizer seu nome?",
  askEmail: (name: string) =>
    `Prazer, ${name}! E qual seu e-mail para eu registrar o atendimento?`,
  invalidEmail:
    "Hmm, não consegui identificar seu e-mail. Pode digitar novamente?",
  ready: (name: string) =>
    `Perfeito, ${name}! Agora me conta, qual o problema que você está enfrentando?`,
  returningUser: (name: string, count: number) =>
    `Olá de novo, ${name}! Vi que você já entrou em contato conosco ${count} ${count === 1 ? "vez" : "vezes"}. Quer continuar um atendimento anterior ou abrir um novo?`,
  continueWhich: (tickets: { id: string; subject: string; status: string }[]) => {
    const list = tickets
      .map(
        (t, i) =>
          `${i + 1}. ${t.subject || "Sem assunto"} (${t.status})`
      )
      .join("\n");
    return `Aqui estão seus atendimentos abertos:\n${list}\n\nQual deles você gostaria de continuar?`;
  },
  startFresh: (name: string) =>
    `Certo, ${name}! Me conta então, qual o problema que você está enfrentando?`,
  ticketStatus: (summary: string) => summary,
};
