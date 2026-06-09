import {
  CONFIDENCE_THRESHOLD,
  HUMAN_REQUIRED_TYPES,
  TOPIC_TO_QUEUE,
} from "./constants";
import type { TicketPriority, TicketScenario, TicketStatus, TicketType } from "./types";

export interface RoutingInput {
  ticket_type: TicketType;
  ticket_priority: TicketPriority;
  topic_group: string;
  confidence: number;
  used_llm: boolean;
}

export interface RoutingResult {
  status: TicketStatus;
  scenario: TicketScenario;
  queue_slug: string;
  human_required_reason: string | null;
}

export function applyRoutingRules(input: RoutingInput): RoutingResult {
  if (HUMAN_REQUIRED_TYPES.includes(input.ticket_type as (typeof HUMAN_REQUIRED_TYPES)[number])) {
    return {
      status: "human_required",
      scenario: "human_required",
      queue_slug: "human-priority",
      human_required_reason: `Tipo DS1: ${input.ticket_type}`,
    };
  }

  if (input.ticket_priority === "Critical") {
    return {
      status: "human_required",
      scenario: "human_required",
      queue_slug: "human-priority",
      human_required_reason: "Prioridade Critical",
    };
  }

  if (input.topic_group === "Administrative rights") {
    return {
      status: "pending_review",
      scenario: input.used_llm ? "llm_reclassified" : "pending_review",
      queue_slug: "admin-rights",
      human_required_reason: "Administrative rights (F1 0,76 no DS2)",
    };
  }

  if (input.confidence < CONFIDENCE_THRESHOLD) {
    return {
      status: "pending_review",
      scenario: input.used_llm ? "llm_reclassified" : "pending_review",
      queue_slug: TOPIC_TO_QUEUE[input.topic_group] ?? "miscellaneous",
      human_required_reason: `Confiança ${input.confidence.toFixed(1)}% < ${CONFIDENCE_THRESHOLD}%`,
    };
  }

  return {
    status: "routed",
    scenario: input.used_llm ? "llm_reclassified" : "auto_routed",
    queue_slug: TOPIC_TO_QUEUE[input.topic_group] ?? "miscellaneous",
    human_required_reason: null,
  };
}

export function buildAckMessage(ticketNumber: number, customerName: string): string {
  return `Olá, ${customerName}! Recebemos seu chamado #${ticketNumber}. Nossa equipe RotaDesk já iniciou a triagem. Você receberá atualizações em breve.`;
}
