import { classifyText } from "./classifier";
import { CONFIDENCE_THRESHOLD } from "./constants";
import { reclassifyWithLlm } from "./openai";
import { applyRoutingRules, buildAckMessage } from "./routing";
import { createServerClient } from "./supabase/server";
import type { TicketChannel, TicketPriority, TicketType } from "./types";

export interface CreateTicketInput {
  customer_name: string;
  customer_email?: string;
  channel: TicketChannel;
  ticket_type: TicketType;
  ticket_priority: TicketPriority;
  subject: string;
  description: string;
}

export async function processNewTicket(input: CreateTicketInput) {
  const supabase = createServerClient();
  const now = new Date().toISOString();

  const { data: ticket, error: insertError } = await supabase
    .from("tickets")
    .insert({
      customer_name: input.customer_name,
      customer_email: input.customer_email ?? null,
      channel: input.channel,
      ticket_type: input.ticket_type,
      ticket_priority: input.ticket_priority,
      subject: input.subject,
      description: input.description,
      status: "open",
    })
    .select()
    .single();

  if (insertError || !ticket) throw new Error(insertError?.message ?? "Falha ao criar ticket");

  const text = `${input.subject}\n${input.description}`;
  let classification = await classifyText(text);
  let topic_group = classification.topic_group;
  let confidence = classification.confidence;
  let topic_group_llm: string | null = null;
  let used_llm = false;

  if (
    confidence < CONFIDENCE_THRESHOLD &&
    process.env.OPENAI_API_KEY
  ) {
    try {
      const llm = await reclassifyWithLlm(text, topic_group, confidence);
      topic_group_llm = llm.topic_group;
      topic_group = llm.topic_group;
      confidence = llm.confidence;
      used_llm = true;
    } catch {
      // mantem classificacao sklearn se LLM falhar
    }
  }

  const routing = applyRoutingRules({
    ticket_type: input.ticket_type,
    ticket_priority: input.ticket_priority,
    topic_group,
    confidence,
    used_llm,
  });

  const ack = buildAckMessage(ticket.ticket_number, input.customer_name);

  const { data: updated, error: updateError } = await supabase
    .from("tickets")
    .update({
      status: routing.status === "human_required" ? "human_required" : routing.status,
      scenario: routing.scenario,
      topic_group: classification.topic_group,
      topic_group_llm,
      confidence,
      queue_slug: routing.queue_slug,
      human_required_reason: routing.human_required_reason,
      first_response_at: now,
      ack_message: ack,
    })
    .eq("id", ticket.id)
    .select()
    .single();

  if (updateError) throw new Error(updateError.message);

  await supabase.from("ticket_messages").insert([
    { ticket_id: ticket.id, role: "system", content: ack },
  ]);

  await supabase.from("ticket_events").insert({
    ticket_id: ticket.id,
    event_type: "ack_sent",
    payload: { at: now },
  });

  await supabase.from("ticket_events").insert({
    ticket_id: ticket.id,
    event_type: "classified",
    payload: {
      topic_group: classification.topic_group,
      topic_group_llm,
      confidence,
      used_llm,
      routing,
    },
  });

  return updated;
}
