import type {
  DeflectionEvent,
  RagSource,
  Ticket,
  TicketCategory,
  TicketPriority,
  TicketStatus,
} from "@/lib/types";

type MockDb = {
  tickets: Ticket[];
  deflections: DeflectionEvent[];
  kb: RagSource[];
  nextTicketId: number;
  nextDeflectionId: number;
};

const globalDb = globalThis as typeof globalThis & { __g4MockDb?: MockDb };
const LEGACY_KB_MARKER = "Não consigo acessar o sistema após reset de senha";

function seedKb(): RagSource[] {
  return [
    {
      id: "kb-001",
      description: "Paguei e não recebi confirmação ou acesso ao curso",
      resolution:
        "Verifique spam/lixo eletrônico e confirme o e-mail da compra. Boleto pode levar até 3 dias úteis. Em PIX/cartão, se não liberar acesso, envie comprovante ao suporte.",
      category: "Pagamento e Faturamento",
      similarity: 0.9,
    },
    {
      id: "kb-002",
      description: "Pagamento recusado com débito no cartão",
      resolution:
        "Isso costuma ser reserva de limite da operadora. Aguarde o prazo de estorno. Se não ocorrer na próxima fatura, envie comprovante ao suporte.",
      category: "Pagamento e Faturamento",
      similarity: 0.86,
    },
    {
      id: "kb-003",
      description: "Não recebi a nota fiscal da compra",
      resolution:
        "A nota fiscal é enviada automaticamente ao e-mail cadastrado após a confirmação do pagamento. Caso não encontre, solicite segunda via com CPF/CNPJ.",
      category: "Pagamento e Faturamento",
      similarity: 0.83,
    },
    {
      id: "kb-004",
      description: "Comprei o curso e não consigo acessar a plataforma",
      resolution:
        "Use o mesmo e-mail da compra e tente 'Esqueci minha senha'. Se as credenciais continuarem falhando, acione o suporte para validação da conta.",
      category: "Acesso à Plataforma",
      similarity: 0.8,
    },
    {
      id: "kb-005",
      description: "Vídeo não carrega ou material em PDF está com erro",
      resolution:
        "Limpe o cache, teste aba anônima e outro navegador. Se persistir, envie ao suporte o curso, módulo e aula para correção técnica.",
      category: "Acesso à Plataforma",
      similarity: 0.78,
    },
    {
      id: "kb-006",
      description: "Quero solicitar reembolso de curso online",
      resolution:
        "O direito de arrependimento é de até 7 dias após a compra. Solicite ao suporte com e-mail de compra e motivo; estorno no meio de pagamento original.",
      category: "Cancelamento e Reembolso",
      similarity: 0.76,
    },
    {
      id: "kb-007",
      description: "Como cancelar a assinatura do G4 Pass",
      resolution:
        "Cancele a renovação automática na área do aluno em 'Assinaturas'. O acesso continua até o final do período já pago.",
      category: "Cancelamento e Reembolso",
      similarity: 0.75,
    },
    {
      id: "kb-008",
      description: "Concluí o curso e o certificado não apareceu",
      resolution:
        "Confira se o progresso está em 100%. Se o certificado não for gerado automaticamente, solicite emissão manual ao suporte.",
      category: "Certificados e Dúvidas Gerais",
      similarity: 0.74,
    },
    {
      id: "kb-009",
      description: "Nome incorreto no certificado",
      resolution:
        "Atualize o nome em 'Minha Conta' e gere novamente. Se o erro persistir, o suporte faz a correção manual.",
      category: "Certificados e Dúvidas Gerais",
      similarity: 0.72,
    },
    {
      id: "kb-010",
      description: "O que está incluso no G4 Pass",
      resolution:
        "Acesso vitalício aos cursos online atuais e futuros, com +100 cursos, +400 horas de conteúdo e +100 ferramentas.",
      category: "G4 Pass",
      similarity: 0.71,
    },
    {
      id: "kb-011",
      description: "O que é o G4 Tools",
      resolution:
        "Marketplace de serviços e tecnologia do G4 com curadoria para CRM, ERP, Marketing, Vendas e Gestão.",
      category: "G4 Tools",
      similarity: 0.7,
    },
  ];
}

function initDb(): MockDb {
  return {
    tickets: [],
    deflections: [],
    kb: seedKb(),
    nextTicketId: 1,
    nextDeflectionId: 1,
  };
}

if (!globalDb.__g4MockDb) {
  globalDb.__g4MockDb = initDb();
}

// If the process kept an old singleton in memory (dev hot reload),
// refresh only the KB seed to avoid returning legacy articles.
if (globalDb.__g4MockDb?.kb?.some((item) => item.description === LEGACY_KB_MARKER)) {
  globalDb.__g4MockDb.kb = seedKb();
}

export const db = globalDb.__g4MockDb;

export function addTicket(input: {
  customerId: string;
  source: "text" | "audio";
  rawText: string;
  category: TicketCategory;
  priority: TicketPriority;
  status?: TicketStatus;
  ragSuggestion?: string;
  ragConfidence?: number;
  resolvedByAi?: boolean;
  audioPath?: string;
}) {
  const ticket: Ticket = {
    id: db.nextTicketId++,
    customer_id: input.customerId,
    source: input.source,
    raw_text: input.rawText,
    category: input.category,
    priority: input.priority,
    status: input.status ?? "open",
    rag_suggestion: input.ragSuggestion,
    rag_confidence: input.ragConfidence,
    resolved_by_ai: input.resolvedByAi ?? false,
    audio_path: input.audioPath,
    created_at: new Date().toISOString(),
  };

  db.tickets.unshift(ticket);
  return ticket;
}

export function updateTicket(
  id: number,
  updates: Partial<Pick<Ticket, "status" | "priority" | "category">>
) {
  const ticket = db.tickets.find((item) => item.id === id);
  if (!ticket) {
    return null;
  }

  if (updates.status) ticket.status = updates.status;
  if (updates.priority) ticket.priority = updates.priority;
  if (updates.category) ticket.category = updates.category;

  if (updates.status === "resolved") {
    ticket.resolved_at = new Date().toISOString();
  }

  return ticket;
}

export function listTickets(scope: "admin" | "customer", customerId?: string) {
  if (scope === "admin") {
    return db.tickets;
  }

  return db.tickets.filter((ticket) => ticket.customer_id === customerId);
}

export function addDeflection(input: {
  customerId: string;
  rawText: string;
  topMatches: RagSource[];
}) {
  const event: DeflectionEvent = {
    id: db.nextDeflectionId++,
    customer_id: input.customerId,
    raw_text: input.rawText,
    top_matches: input.topMatches,
    created_at: new Date().toISOString(),
  };

  db.deflections.unshift(event);
  return event;
}

export function getDeflectionMetrics() {
  const totalSessions = db.deflections.length + db.tickets.length;
  const deflectionRate = totalSessions === 0 ? 0 : db.deflections.length / totalSessions;
  const confidences = db.tickets
    .map((item) => item.rag_confidence)
    .filter((value): value is number => typeof value === "number");
  const confidenceAverage =
    confidences.length > 0
      ? confidences.reduce((sum, value) => sum + value, 0) / confidences.length
      : 0;

  const topResolvedQuestions = db.deflections.slice(0, 5).map((item) => item.raw_text);

  return {
    total_sessions: totalSessions,
    deflections: db.deflections.length,
    deflection_rate: Number(deflectionRate.toFixed(2)),
    confidence_average: Number(confidenceAverage.toFixed(2)),
    top_resolved_questions: topResolvedQuestions,
  };
}

export function findTopKbMatches(text: string, topN = 5): RagSource[] {
  const terms = text
    .toLowerCase()
    .split(/\W+/)
    .filter((term) => term.length > 2);

  const scored = db.kb.map((entry) => {
    const content = `${entry.description} ${entry.resolution}`.toLowerCase();
    const hits = terms.reduce((sum, term) => (content.includes(term) ? sum + 1 : sum), 0);
    const denom = Math.max(terms.length, 1);
    const score = Math.min(0.98, Math.max(0.3, hits / denom));

    return {
      ...entry,
      similarity: Number(score.toFixed(2)),
    };
  });

  return scored.sort((a, b) => b.similarity - a.similarity).slice(0, topN);
}
