import { NextRequest } from "next/server";

import { getDemoUser, isAdmin } from "@/lib/auth";
import { fail, ok, readBody } from "@/lib/api";
import { addTicket, listTickets, updateTicket } from "@/lib/mock-db";
import type { TicketCategory, TicketPriority, TicketSource, TicketStatus } from "@/lib/types";

type CreateTicketBody = {
  source?: TicketSource;
  audio_path?: string;
  raw_text?: string;
  category?: TicketCategory;
  priority?: TicketPriority;
  rag_suggestion?: string;
  rag_confidence?: number;
};

type UpdateTicketBody = {
  id?: number;
  status?: TicketStatus;
  priority?: TicketPriority;
  category?: TicketCategory;
};

export async function GET(request: NextRequest) {
  const user = getDemoUser(request);

  if (!user) {
    return fail("Não autenticado", 401);
  }

  const items = listTickets(isAdmin(user) ? "admin" : "customer", user.id);
  return ok({ items });
}

export async function POST(request: NextRequest) {
  const user = getDemoUser(request);

  if (!user) {
    return fail("Não autenticado", 401);
  }

  const body = await readBody<CreateTicketBody>(request);

  if (!body?.raw_text || !body.source) {
    return fail("source e raw_text são obrigatórios", 400);
  }

  const ticket = addTicket({
    customerId: user.id,
    source: body.source,
    rawText: body.raw_text,
    category: body.category ?? "Other",
    priority: body.priority ?? "medium",
    ragSuggestion: body.rag_suggestion,
    ragConfidence: body.rag_confidence,
    audioPath: body.audio_path,
  });

  return ok({ ticket }, 201);
}

export async function PATCH(request: NextRequest) {
  const user = getDemoUser(request);

  if (!user || !isAdmin(user)) {
    return fail("Apenas admin pode atualizar tickets", 403);
  }

  const body = await readBody<UpdateTicketBody>(request);

  if (!body?.id) {
    return fail("id é obrigatório", 400);
  }

  const ticket = updateTicket(body.id, {
    status: body.status,
    priority: body.priority,
    category: body.category,
  });

  if (!ticket) {
    return fail("Ticket não encontrado", 404);
  }

  return ok({ ticket });
}
