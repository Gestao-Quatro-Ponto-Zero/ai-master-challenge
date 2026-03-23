import { NextRequest, NextResponse } from "next/server";
import { z } from "zod/v4";
import { createClient } from "@/lib/supabase/server";
import { SCENARIO_LABELS } from "@/lib/routing/taxonomy";
import { classifyTicket } from "@/app/api/prototype/classify/route";

// ─── GET: Fetch messages for a conversation ──────────────────────────

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: conversationId } = await params;
  const supabase = await createClient();

  const { data: messages, error } = await supabase
    .from("messages")
    .select("id, conversation_id, role, content, created_at, metadata")
    .eq("conversation_id", conversationId)
    .order("created_at", { ascending: true });

  if (error) {
    return NextResponse.json(
      { error: "Erro ao buscar mensagens", details: error.message },
      { status: 500 }
    );
  }

  return NextResponse.json({ messages: messages || [] });
}
import {
  checkGate,
  computeDensity,
  computeEffectiveConfidence,
} from "@/lib/prototype/classification-gate";
import {
  extractEmail,
  extractName,
  detectContinueIntent,
  detectTicketStatusIntent,
  IDENTITY_MESSAGES,
  type IdentityState,
} from "@/lib/prototype/identity-flow";
import { searchKB, formatArticlesForPrompt, type RAGArticle } from "@/lib/prototype/rag";
import { findBestOperator, getOperatorTier } from "@/lib/prototype/escalation";

// SLA deadlines by scenario (in minutes)
const SLA_MINUTES: Record<string, number> = {
  acelerar: 30,
  quarentena: 60,
  desacelerar: 240,
  redirecionar: 120,
  manter: 480,
  liberar: 1440,
};

function computeSlaDeadline(scenario: string): string {
  const minutes = SLA_MINUTES[scenario] || 480;
  return new Date(Date.now() + minutes * 60 * 1000).toISOString();
}

// ─── Input Validation ────────────────────────────────────────────────

const SendMessageInput = z.object({
  role: z.enum(["customer", "operator"]),
  content: z.string().min(1, "Mensagem obrigatória"),
  grouped_messages: z.array(z.string()).optional(),
});

// ─── OpenAI Helper ──────────────────────────────────────────────────

async function callOpenAI(
  systemPrompt: string,
  userPrompt: string,
  maxTokens = 512
): Promise<string | null> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) return null;

  try {
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userPrompt },
        ],
        temperature: 0.3,
        max_tokens: maxTokens,
      }),
    });

    if (!res.ok) return null;

    const data = await res.json();
    return data.choices?.[0]?.message?.content?.trim() || null;
  } catch {
    return null;
  }
}

// ─── Response Generators ────────────────────────────────────────────

async function generateKBResponse(
  articles: RAGArticle[],
  customerMessage: string,
  conversationHistory: string,
  subject: string
): Promise<string> {
  const articlesContext = formatArticlesForPrompt(articles);

  const systemPrompt = `Você é um assistente de suporte técnico da OptiFlow. Responda em português brasileiro, de forma natural e prestativa.

Você tem acesso aos seguintes artigos da base de conhecimento (ordenados por relevância):

${articlesContext}

REGRAS:
- Use esses artigos como referência para ajudar o cliente, mas NUNCA mencione que consultou artigos ou uma base de conhecimento
- Responda como se VOCÊ soubesse a resposta diretamente
- Seja claro e objetivo, use passos numerados quando apropriado
- Dê instruções CONCRETAS e ACIONÁVEIS baseadas no conteúdo de referência
- Combine informações dos artigos mais relevantes para uma resposta completa
- Ao final, pergunte: "Conseguiu seguir esses passos? Resolveu o problema?"
- Use tom profissional mas amigável
- Nunca prometa que VAI funcionar — use "isso geralmente resolve" ou "tente os seguintes passos"
- IMPORTANTE: Só pergunte se resolveu se você REALMENTE deu passos concretos para tentar resolver`;

  const userPrompt = `Histórico da conversa:
${conversationHistory}

Mensagem atual do cliente: ${customerMessage}
Problema identificado como: ${subject}

Gere uma resposta com passos concretos de troubleshooting baseada nas informações de referência.`;

  const response = await callOpenAI(systemPrompt, userPrompt);
  return response || `Baseado no que você descreveu, vou sugerir alguns passos para tentar resolver. Me dê um momento para verificar as melhores opções para o seu caso.`;
}

async function generateClarifyingQuestion(
  customerMessage: string,
  conversationHistory: string,
  currentCategory: string,
  possibleSubjects: string[]
): Promise<string> {
  const systemPrompt = `Você é um assistente de suporte técnico da OptiFlow. Faça UMA pergunta objetiva para entender melhor o problema do cliente.

REGRAS:
- Pergunta em português brasileiro
- Máximo 2 frases
- Foque em detalhes que ajudem a distinguir entre estas possíveis categorias: ${possibleSubjects.join(", ")}
- Seja natural, não pareça um formulário
- Não repita informações que o cliente já deu`;

  const userPrompt = `Categoria provável: ${currentCategory}

Histórico:
${conversationHistory}

Mensagem atual: ${customerMessage}

Gere uma pergunta clarificadora.`;

  const response = await callOpenAI(systemPrompt, userPrompt, 128);
  return response || "Poderia me dar mais detalhes sobre o problema que está enfrentando?";
}

async function generateEscalationSummary(
  conversationHistory: string
): Promise<string> {
  const systemPrompt = `Você é um assistente que gera resumos de conversas para operadores de suporte.

REGRAS:
- Resumo em português brasileiro
- Máximo 3-4 frases
- Inclua: problema principal, o que já foi tentado, expectativa do cliente
- Formato objetivo, para um operador ler rapidamente`;

  const response = await callOpenAI(systemPrompt, `Resuma esta conversa:\n\n${conversationHistory}`, 256);
  return response || "Cliente com problema não resolvido pelo atendimento automatizado. Requer análise do operador.";
}

function detectNegativeResponse(content: string): boolean {
  const negativePatterns = [
    /\bn[aã]o\b/i,
    /\bnão\s+(ajudou|resolveu|funcionou|deu\s+certo)/i,
    /\bnada\b/i,
    /\bnem\b/i,
    /\bcontinua\s+(com|o|a)\s+problem/i,
    /\bmesmo\s+problema/i,
    /\bnão\s+consigo/i,
    /\bainda\s+não/i,
  ];
  return negativePatterns.some((p) => p.test(content));
}

// ─── Identity Flow Handler ──────────────────────────────────────────

async function handleIdentityFlow(
  supabase: Awaited<ReturnType<typeof createClient>>,
  conversationId: string,
  conversation: Record<string, unknown>,
  content: string,
  savedMessage: Record<string, unknown>
): Promise<NextResponse | null> {
  const identityState = (conversation.identity_state as IdentityState) || "support";

  // If identity is already complete, return null to proceed with classification
  if (identityState === "support" || identityState === "ready") {
    return null;
  }

  let responseContent: string;
  let newState: IdentityState;
  const updates: Record<string, unknown> = {
    updated_at: new Date().toISOString(),
  };

  switch (identityState) {
    case "greeting": {
      // User sent first message after welcome. Ask for name.
      responseContent = IDENTITY_MESSAGES.askName;
      newState = "asking_name";
      break;
    }

    case "asking_name": {
      // Extract name from user message
      const name = extractName(content);
      updates.customer_name = name;
      responseContent = IDENTITY_MESSAGES.askEmail(name);
      newState = "asking_email";
      break;
    }

    case "asking_email": {
      // Extract email from user message
      const email = extractEmail(content);
      if (!email) {
        responseContent = IDENTITY_MESSAGES.invalidEmail;
        newState = "asking_email";
        break;
      }

      updates.customer_email = email;
      const customerName = (conversation.customer_name as string) || "Cliente";

      // Check for returning user
      const { data: previousConversations } = await supabase
        .from("conversations")
        .select("id, subject_classified, status, created_at")
        .eq("customer_email", email)
        .neq("id", conversationId)
        .order("created_at", { ascending: false });

      const prevCount = previousConversations?.length || 0;

      if (prevCount > 0) {
        // Returning user
        updates.identity_state = "returning_user_check";
        responseContent = IDENTITY_MESSAGES.returningUser(customerName, prevCount);
        newState = "returning_user_check";

        // Store previous conversations info in metadata for later use
        const openTickets = previousConversations?.filter(
          (c) => c.status === "active" || c.status === "escalated" || c.status === "in_progress"
        ) || [];

        if (openTickets.length > 0) {
          responseContent += `\n\nVocê tem ${openTickets.length} atendimento${openTickets.length > 1 ? "s" : ""} em aberto.`;
        }
      } else {
        // New user — go straight to support
        responseContent = IDENTITY_MESSAGES.ready(customerName);
        newState = "support";
      }
      break;
    }

    case "returning_user_check": {
      const intent = detectContinueIntent(content);
      const customerName = (conversation.customer_name as string) || "Cliente";
      const customerEmail = (conversation.customer_email as string) || "";

      if (intent === "continue") {
        // Find open conversations for this user
        const { data: openConvs } = await supabase
          .from("conversations")
          .select("id, subject_classified, status, category_classified")
          .eq("customer_email", customerEmail)
          .neq("id", conversationId)
          .in("status", ["active", "escalated", "in_progress"])
          .order("created_at", { ascending: false })
          .limit(5);

        if (openConvs && openConvs.length > 0) {
          const tickets = openConvs.map((c) => ({
            id: c.id as string,
            subject: (c.subject_classified as string) || "Sem assunto",
            status: c.status as string,
          }));
          responseContent = IDENTITY_MESSAGES.continueWhich(tickets);
          newState = "support";
        } else {
          responseContent = IDENTITY_MESSAGES.startFresh(customerName);
          newState = "support";
        }
      } else {
        // New conversation or unclear intent
        responseContent = IDENTITY_MESSAGES.startFresh(customerName);
        newState = "support";
      }
      break;
    }

    default:
      return null;
  }

  updates.identity_state = newState;

  // Update conversation state
  await supabase
    .from("conversations")
    .update(updates)
    .eq("id", conversationId);

  // Save assistant response
  const { data: assistantMessage } = await supabase
    .from("messages")
    .insert({
      conversation_id: conversationId,
      role: "assistant",
      content: responseContent,
      metadata: { type: "identity_flow", state: newState },
    })
    .select()
    .single();

  return NextResponse.json({
    messages: [savedMessage, assistantMessage].filter(Boolean),
    classification: null,
    identity_state: newState,
  });
}

// ─── Ticket Status Handler ──────────────────────────────────────────

async function handleTicketStatusQuery(
  supabase: Awaited<ReturnType<typeof createClient>>,
  conversationId: string,
  customerEmail: string,
  savedMessage: Record<string, unknown>
): Promise<NextResponse | null> {
  const { data: userConversations } = await supabase
    .from("conversations")
    .select("id, subject_classified, status, category_classified, created_at")
    .eq("customer_email", customerEmail)
    .neq("id", conversationId)
    .order("created_at", { ascending: false })
    .limit(10);

  if (!userConversations || userConversations.length === 0) {
    const responseContent = "Não encontrei nenhum atendimento anterior registrado no seu e-mail. Este é o seu primeiro contato conosco!";
    const { data: assistantMessage } = await supabase
      .from("messages")
      .insert({
        conversation_id: conversationId,
        role: "assistant",
        content: responseContent,
        metadata: { type: "ticket_status_query" },
      })
      .select()
      .single();

    return NextResponse.json({
      messages: [savedMessage, assistantMessage].filter(Boolean),
      classification: null,
    });
  }

  const statusMap: Record<string, string> = {
    active: "em andamento",
    escalated: "escalado",
    in_progress: "em atendimento",
    resolved: "resolvido",
  };

  const counts: Record<string, number> = {};
  for (const conv of userConversations) {
    const status = (conv.status as string) || "active";
    counts[status] = (counts[status] || 0) + 1;
  }

  let summary = `Você tem ${userConversations.length} atendimento${userConversations.length > 1 ? "s" : ""} registrado${userConversations.length > 1 ? "s" : ""}:`;
  const parts = Object.entries(counts).map(
    ([status, count]) => `${count} ${statusMap[status] || status}`
  );
  summary += " " + parts.join(", ") + ".";

  // List open tickets
  const openTickets = userConversations.filter(
    (c) => c.status !== "resolved"
  );
  if (openTickets.length > 0) {
    summary += "\n\nAtendimentos abertos:";
    for (const t of openTickets.slice(0, 5)) {
      const subject = (t.subject_classified as string) || "Sem assunto definido";
      const status = statusMap[(t.status as string)] || (t.status as string);
      summary += `\n- ${subject} (${status})`;
    }
  }

  summary += "\n\nPosso ajudar com algo mais?";

  const { data: assistantMessage } = await supabase
    .from("messages")
    .insert({
      conversation_id: conversationId,
      role: "assistant",
      content: summary,
      metadata: { type: "ticket_status_query" },
    })
    .select()
    .single();

  return NextResponse.json({
    messages: [savedMessage, assistantMessage].filter(Boolean),
    classification: null,
  });
}

// ─── Main Handler ───────────────────────────────────────────────────

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: conversationId } = await params;

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Corpo da requisição inválido" },
      { status: 400 }
    );
  }

  const parsed = SendMessageInput.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Dados inválidos", details: parsed.error.issues },
      { status: 400 }
    );
  }

  const { role, content, grouped_messages } = parsed.data;
  const supabase = await createClient();

  // Verify conversation exists
  const { data: conversation, error: convError } = await supabase
    .from("conversations")
    .select("*")
    .eq("id", conversationId)
    .single();

  if (convError || !conversation) {
    return NextResponse.json(
      { error: "Conversa não encontrada" },
      { status: 404 }
    );
  }

  // Save the incoming message(s)
  // When grouped_messages is provided, store each individual message for accurate transcript
  // but use the concatenated content for classification and response generation
  let savedMessage: Record<string, unknown> | null = null;
  const savedGroupedMessages: Record<string, unknown>[] = [];
  const groupedCount = grouped_messages && grouped_messages.length > 1 ? grouped_messages.length : undefined;

  if (grouped_messages && grouped_messages.length > 1) {
    for (const msg of grouped_messages) {
      const { data: individualMsg, error: msgError } = await supabase
        .from("messages")
        .insert({
          conversation_id: conversationId,
          role,
          content: msg,
          metadata: { grouped: true, grouped_count: grouped_messages.length },
        })
        .select()
        .single();

      if (msgError || !individualMsg) {
        return NextResponse.json(
          { error: "Erro ao salvar mensagem", details: msgError?.message },
          { status: 500 }
        );
      }
      savedGroupedMessages.push(individualMsg as Record<string, unknown>);
    }
    savedMessage = savedGroupedMessages[savedGroupedMessages.length - 1];
  } else {
    const { data: singleMsg, error: saveError } = await supabase
      .from("messages")
      .insert({
        conversation_id: conversationId,
        role,
        content,
      })
      .select()
      .single();

    if (saveError || !singleMsg) {
      return NextResponse.json(
        { error: "Erro ao salvar mensagem", details: saveError?.message },
        { status: 500 }
      );
    }
    savedMessage = singleMsg as Record<string, unknown>;
  }

  // If operator message, just save and return
  if (role === "operator") {
    const returnMessages = savedGroupedMessages.length > 0 ? savedGroupedMessages : [savedMessage];
    return NextResponse.json({
      messages: returnMessages,
      classification: null,
    });
  }

  // ─── Identity Flow: handle before classification ─────────────────

  const identityResponse = await handleIdentityFlow(
    supabase,
    conversationId,
    conversation as Record<string, unknown>,
    content,
    savedMessage as Record<string, unknown>
  );

  if (identityResponse) {
    return identityResponse;
  }

  // ─── Ticket Status Query ──────────────────────────────────────────

  const customerEmail = conversation.customer_email as string;
  if (customerEmail && detectTicketStatusIntent(content)) {
    const statusResponse = await handleTicketStatusQuery(
      supabase,
      conversationId,
      customerEmail,
      savedMessage as Record<string, unknown>
    );
    if (statusResponse) {
      return statusResponse;
    }
  }

  // ─── Escalated Guard: conversation already with operator ─────────
  if (conversation.status === "escalated" || conversation.status === "in_progress") {
    const guardContent = conversation.status === "in_progress"
      ? "Seu caso já está sendo atendido por um de nossos especialistas. Ele(a) responderá em breve pelo painel de atendimento."
      : "Seu caso já foi encaminhado para um especialista e está na fila de atendimento. Você será notificado assim que um operador assumir o seu ticket.";

    const { data: guardMsg } = await supabase
      .from("messages")
      .insert({
        conversation_id: conversationId,
        role: "assistant",
        content: guardContent,
        metadata: { type: "escalated_guard" },
      })
      .select()
      .single();

    const guardCustomerMessages = savedGroupedMessages.length > 0
      ? savedGroupedMessages
      : [savedMessage];
    return NextResponse.json({
      messages: [...guardCustomerMessages, guardMsg].filter(Boolean),
      classification: {
        category: conversation.category_classified,
        subject: conversation.subject_classified,
        scenario: conversation.scenario,
        confidence: conversation.confidence,
        escalated: true,
        turn_count: (conversation.turn_count || 0) + 1,
      },
    });
  }

  // ─── Customer message: trigger classification + response pipeline ───

  // Get all messages for context (exclude identity flow messages)
  const { data: allMessages } = await supabase
    .from("messages")
    .select("role, content, metadata")
    .eq("conversation_id", conversationId)
    .order("created_at", { ascending: true });

  const messageHistory = (allMessages || []).filter(
    (m) => !(m.metadata as Record<string, unknown>)?.type || (m.metadata as Record<string, unknown>)?.type !== "identity_flow"
  );
  const conversationHistory = messageHistory
    .map((m) => `${m.role === "customer" ? "Cliente" : "Assistente"}: ${m.content}`)
    .join("\n");

  // Increment turn count
  const newTurnCount = (conversation.turn_count || 0) + 1;

  // Check if customer said "no" to a previous KB response
  const isNegativeToKB =
    newTurnCount >= 3 && detectNegativeResponse(content);

  // If conversation is already classified and customer gives negative feedback, escalate
  if (isNegativeToKB && conversation.scenario) {
    const summary = await generateEscalationSummary(conversationHistory);

    const scenarioInfo = SCENARIO_LABELS[conversation.scenario as string];
    const channelRec = conversation.channel === "Chat" ? "Telefone" : "Chat";

    const scenarioExplanation = conversation.scenario === "acelerar"
      ? "Como seu problema precisa de resolução rápida, vou encaminhar para a fila prioritária."
      : conversation.scenario === "quarentena"
      ? "Seu caso requer uma investigação especial pela nossa equipe sênior."
      : conversation.scenario === "redirecionar"
      ? `Para este tipo de problema, recomendamos o atendimento por ${channelRec}, que tem melhor taxa de resolução.`
      : "Vou encaminhar para um especialista que pode ajudar diretamente.";

    const escalationContent = `Entendo que os passos sugeridos não resolveram. ${scenarioExplanation}\n\nSeu caso foi registrado com toda a conversa e classificação. Um operador receberá seu ticket com o contexto completo para dar continuidade.`;

    // Save escalation message
    const { data: escalationMsg } = await supabase
      .from("messages")
      .insert({
        conversation_id: conversationId,
        role: "system",
        content: escalationContent,
        metadata: { type: "escalation", summary },
      })
      .select()
      .single();

    // Find best operator via intelligent routing
    const bestOperator = await findBestOperator(
      conversation.scenario as string | null,
      conversation.category_classified as string | null,
      1, // start at tier 1
      supabase
    );

    // Update conversation to escalated
    const escalationUpdates: Record<string, unknown> = {
      status: "escalated",
      turn_count: newTurnCount,
      summary,
      escalation_channel: channelRec,
      escalation_tier: bestOperator ? getOperatorTier(bestOperator.level) : 1,
      sla_deadline: computeSlaDeadline(conversation.scenario as string),
      updated_at: new Date().toISOString(),
    };

    if (bestOperator) {
      escalationUpdates.assigned_operator_id = bestOperator.id;
    }

    await supabase
      .from("conversations")
      .update(escalationUpdates)
      .eq("id", conversationId);

    // Atomically increment assigned operator's active_tickets
    if (bestOperator) {
      await supabase.rpc("increment_active_tickets", { operator_id: bestOperator.id });
    }

    const escalationCustomerMessages = savedGroupedMessages.length > 0
      ? savedGroupedMessages
      : [savedMessage];
    return NextResponse.json({
      messages: [...escalationCustomerMessages, escalationMsg].filter(Boolean),
      classification: {
        category: conversation.category_classified,
        subject: conversation.subject_classified,
        scenario: conversation.scenario,
        confidence: conversation.confidence,
        action: scenarioInfo?.action || "",
        escalated: true,
        escalation_details: {
          operator_name: bestOperator?.name || null,
          operator_level: bestOperator?.level || null,
          tier: bestOperator ? getOperatorTier(bestOperator.level) : 1,
          sla_deadline: computeSlaDeadline(conversation.scenario as string),
          escalation_channel: channelRec,
          original_channel: conversation.channel,
        },
        summary,
        turn_count: newTurnCount,
        grouped_count: groupedCount,
      },
    });
  }

  // ─── Accumulate customer context for gate + density ───
  // After identity is complete, short replies like "nao recebi" to a clarifying
  // question would be blocked by the gate if evaluated alone. We concatenate ALL
  // customer messages so the gate and density see the full conversation context.

  let accumulatedContext = content; // default: current message only

  const identityDone =
    (conversation.identity_state as string) === "support" ||
    (conversation.identity_state as string) === "ready";

  if (identityDone) {
    // Find when identity completed (the assistant message with state="support")
    // so we only accumulate customer messages AFTER that point.
    // Identity messages (greeting, name, email) would trigger the gate's
    // greeting detector if included (e.g., "oi" matches ^oi\b).
    const { data: identityCompleteMsg } = await supabase
      .from("messages")
      .select("created_at")
      .eq("conversation_id", conversationId)
      .eq("role", "assistant")
      .contains("metadata", { type: "identity_flow", state: "support" })
      .order("created_at", { ascending: false })
      .limit(1)
      .single();

    const identityCutoff = identityCompleteMsg?.created_at || null;

    let query = supabase
      .from("messages")
      .select("content, role")
      .eq("conversation_id", conversationId)
      .eq("role", "customer")
      .order("created_at", { ascending: true });

    // Only include messages after identity completion
    if (identityCutoff) {
      query = query.gt("created_at", identityCutoff);
    }

    const { data: prevCustomerMessages } = await query;

    const previousTexts = (prevCustomerMessages || [])
      .map((m) => m.content as string)
      .filter(Boolean);

    if (previousTexts.length > 0) {
      accumulatedContext = previousTexts.join(" ");
    }
  }

  // ─── Pre-Classification Gate ───

  // Safety: if the gate blocked 2+ times in a row, force-pass to classifier.
  // We don't want the customer stuck in a loop of "tell me more" forever.
  let consecutiveGateBlocks = 0;
  if (identityDone) {
    const { data: recentAssistantMsgs } = await supabase
      .from("messages")
      .select("metadata")
      .eq("conversation_id", conversationId)
      .eq("role", "assistant")
      .order("created_at", { ascending: false })
      .limit(3);

    for (const msg of recentAssistantMsgs || []) {
      const meta = msg.metadata as Record<string, unknown> | null;
      if (meta?.type === "gate_blocked") {
        consecutiveGateBlocks++;
      } else {
        break; // stop counting at first non-gate message
      }
    }
  }

  const gateResult = checkGate(accumulatedContext);
  const forcePassGate = identityDone && consecutiveGateBlocks >= 2;

  if (!gateResult.passed && !forcePassGate) {
    // Gate blocked — but NEVER send a greeting mid-conversation.
    // After identity is done, always ask for more context in a human way.
    let gateResponse: string;

    if (identityDone) {
      // Post-identity: ask for more detail, never reset
      const customerName = (conversation.customer_name as string) || "";
      const namePrefix = customerName ? `${customerName}, ` : "";

      const contextualFollowUps = [
        `${namePrefix}entendi que você precisa de ajuda. Pode me explicar com mais detalhes o que está acontecendo? Por exemplo, o que você estava tentando fazer quando o problema apareceu?`,
        `${namePrefix}quero te ajudar! Me conta um pouco mais — qual sistema ou ferramenta está dando problema? E o que exatamente acontece quando você tenta usar?`,
        `${namePrefix}preciso de um pouco mais de contexto para te ajudar. Pode descrever o passo a passo do que você fez até chegar no problema?`,
        `${namePrefix}sem problemas! Para eu entender melhor: qual é o erro ou situação que está enfrentando? Me dê o máximo de detalhes que puder.`,
      ];
      gateResponse = contextualFollowUps[Math.floor(Math.random() * contextualFollowUps.length)];
    } else {
      // Pre-identity: use the default gate response
      gateResponse = gateResult.suggestedResponse || "Como posso ajudar?";
    }

    const { data: gateMessage } = await supabase
      .from("messages")
      .insert({
        conversation_id: conversationId,
        role: "assistant",
        content: gateResponse,
        metadata: { type: "gate_blocked", gate_reason: gateResult.reason },
      })
      .select()
      .single();

    // Update turn count only
    await supabase
      .from("conversations")
      .update({
        turn_count: newTurnCount,
        updated_at: new Date().toISOString(),
      })
      .eq("id", conversationId);

    const gateCustomerMessages = savedGroupedMessages.length > 0
      ? savedGroupedMessages
      : [savedMessage];
    return NextResponse.json({
      messages: [...gateCustomerMessages, gateMessage].filter(Boolean),
      classification: {
        gate_passed: false,
        gate_reason: gateResult.reason,
        turn_count: newTurnCount,
        category: null,
        subject: null,
        scenario: null,
        confidence: null,
        action: null,
        auto_routed: false,
        escalated: false,
        fallback: false,
        grouped_count: groupedCount,
      },
    });
  }

  // ─── Information Density ───

  const densityResult = computeDensity(accumulatedContext);

  // RAG articles placeholder — populated inside shouldAutoRoute block
  let ragArticles: RAGArticle[] = [];

  // Escalation tracking — populated if auto-escalation happens in this turn
  let didEscalate = false;
  let escalationDetails: {
    operator_name?: string | null;
    operator_level?: string | null;
    tier?: number;
    sla_deadline?: string;
    escalation_channel?: string;
    original_channel?: string;
  } | null = null;

  // ─── Classification Pipeline ───

  // Call classifier directly (no HTTP self-call — avoids Vercel middleware issues)
  const classificationResult = await classifyTicket({
    text: accumulatedContext,
    channel: conversation.channel,
    conversationHistory: messageHistory
      .filter((m) => m.role === "customer")
      .map((m) => m.content),
  });

  // Compute effective confidence using density score
  const rawConfidence = classificationResult.confidence;
  const effectiveConfidence = computeEffectiveConfidence(rawConfidence, densityResult.score);
  const shouldAutoRoute = effectiveConfidence >= 0.85 || newTurnCount >= 3;

  let assistantContent: string;
  let responseMetadata: Record<string, unknown> = {};

  if (shouldAutoRoute) {
    // Auto-route: classification is confident enough or we've hit max turns
    const conversationUpdates: Record<string, unknown> = {
      category_classified: classificationResult.category,
      subject_classified: classificationResult.subject,
      scenario: classificationResult.scenario,
      confidence: effectiveConfidence,
      turn_count: newTurnCount,
      updated_at: new Date().toISOString(),
    };

    const scenarioInfo = SCENARIO_LABELS[classificationResult.scenario];
    const scenarioLabel = scenarioInfo?.label || classificationResult.scenario;

    // RAG: semantic search for relevant KB articles
    const ragResult = await searchKB(content);
    ragArticles = ragResult.articles;

    if (ragArticles.length > 0 && ragArticles[0].similarity >= 0.3) {
      // Generate KB-based response using top 3 articles from RAG
      assistantContent = await generateKBResponse(
        ragArticles,
        content,
        conversationHistory,
        classificationResult.subject
      );

      responseMetadata = {
        type: "kb_response",
        rag_articles: ragArticles.map((a) => ({
          title: a.title,
          similarity: a.similarity,
        })),
        classification: classificationResult,
        auto_routed: true,
      };
    } else {
      // No relevant KB articles found — explain what we identified and route to specialist
      const routingExplanation = classificationResult.scenario === "acelerar"
        ? "Identifiquei que este tipo de problema precisa de atenção prioritária."
        : classificationResult.scenario === "redirecionar"
        ? `Para este tipo de problema, o canal mais eficiente seria outro. Recomendo entrar em contato por ${classificationResult.explanation?.includes("redirecionar para:") ? classificationResult.explanation.split("redirecionar para: ")[1] : "telefone"}.`
        : classificationResult.scenario === "quarentena"
        ? "Este tipo de situação requer uma investigação mais detalhada pela nossa equipe especializada."
        : classificationResult.scenario === "desacelerar"
        ? "Este problema precisa de uma análise cuidadosa por um especialista."
        : "Vou direcionar seu caso para o atendimento adequado.";

      // Never show "Other" or raw classification labels to the customer
      const subjectDisplay = classificationResult.subject.toLowerCase() === "other"
        ? `um problema na área de ${classificationResult.category}`
        : classificationResult.subject;

      assistantContent = `Identifiquei seu problema como: **${subjectDisplay}**.\n\n${routingExplanation}\n\nVou encaminhar você para um especialista que pode ajudar diretamente. Um momento, por favor.`;

      responseMetadata = {
        type: "routing_explanation",
        classification: classificationResult,
        auto_routed: true,
      };

      // Auto-escalate since we have no KB to try
      conversationUpdates.status = "escalated";
      const slaDeadline = computeSlaDeadline(classificationResult.scenario);
      conversationUpdates.sla_deadline = slaDeadline;
      const escChannel = classificationResult.scenario === "redirecionar"
        ? (classificationResult.explanation?.split("redirecionar para: ")[1] || "Telefone")
        : conversation.channel as string;
      conversationUpdates.escalation_channel = escChannel;
      const summary = await generateEscalationSummary(conversationHistory);
      conversationUpdates.summary = summary;

      // Find best operator via intelligent routing
      const noKBOperator = await findBestOperator(
        classificationResult.scenario,
        classificationResult.category,
        1,
        supabase
      );
      didEscalate = true;
      if (noKBOperator) {
        conversationUpdates.assigned_operator_id = noKBOperator.id;
        conversationUpdates.escalation_tier = getOperatorTier(noKBOperator.level);
        escalationDetails = {
          operator_name: noKBOperator.name,
          operator_level: noKBOperator.level,
          tier: getOperatorTier(noKBOperator.level),
          sla_deadline: slaDeadline,
          escalation_channel: escChannel,
          original_channel: conversation.channel as string,
        };
        // Atomically increment operator active tickets
        await supabase.rpc("increment_active_tickets", { operator_id: noKBOperator.id });
      } else {
        conversationUpdates.escalation_tier = 1;
        escalationDetails = {
          tier: 1,
          sla_deadline: slaDeadline,
          escalation_channel: escChannel,
          original_channel: conversation.channel as string,
        };
      }
    }

    // If this is a forced classification (turn 3+, low confidence), flag it
    if (newTurnCount >= 3 && effectiveConfidence < 0.85) {
      conversationUpdates.confidence = effectiveConfidence;
      responseMetadata.low_confidence_forced = true;
    }

    // Suppress unused variable warning
    void scenarioLabel;

    await supabase
      .from("conversations")
      .update(conversationUpdates)
      .eq("id", conversationId);
  } else {
    // Low confidence, ask clarifying question
    const { D2_TO_D1 } = await import("@/lib/routing/taxonomy");
    const possibleSubjects = D2_TO_D1[classificationResult.category] || [];

    assistantContent = await generateClarifyingQuestion(
      content,
      conversationHistory,
      classificationResult.category,
      possibleSubjects
    );

    responseMetadata = {
      type: "clarifying_question",
      classification: classificationResult,
      auto_routed: false,
    };

    // Update turn count and partial classification
    await supabase
      .from("conversations")
      .update({
        turn_count: newTurnCount,
        category_classified: classificationResult.category,
        confidence: effectiveConfidence,
        updated_at: new Date().toISOString(),
      })
      .eq("id", conversationId);
  }

  // Save assistant response
  const { data: assistantMessage } = await supabase
    .from("messages")
    .insert({
      conversation_id: conversationId,
      role: "assistant",
      content: assistantContent,
      metadata: responseMetadata,
    })
    .select()
    .single();

  const returnedCustomerMessages = savedGroupedMessages.length > 0
    ? savedGroupedMessages
    : [savedMessage];

  return NextResponse.json({
    messages: [...returnedCustomerMessages, assistantMessage].filter(Boolean),
    classification: {
      category: classificationResult.category,
      subject: classificationResult.subject,
      scenario: classificationResult.scenario,
      confidence: effectiveConfidence,
      action: classificationResult.action,
      explanation: classificationResult.explanation,
      kb_title: ragArticles?.[0]?.title || null,
      rag_articles: ragArticles.length ? ragArticles.map((a: RAGArticle) => ({ title: a.title, similarity: a.similarity })) : null,
      auto_routed: shouldAutoRoute,
      escalated: didEscalate,
      escalation_details: escalationDetails,
      turn_count: newTurnCount,
      fallback: classificationResult.fallback,
      gate_passed: true,
      gate_reason: null,
      density_score: densityResult.score,
      density_details: {
        tokenCount: densityResult.tokenCount,
        technicalTerms: densityResult.technicalTerms,
        problemVerbs: densityResult.problemVerbs,
        hasErrorCode: densityResult.hasErrorCode,
      },
      raw_confidence: rawConfidence,
      effective_confidence: effectiveConfidence,
      grouped_count: groupedCount,
    },
  });
}
