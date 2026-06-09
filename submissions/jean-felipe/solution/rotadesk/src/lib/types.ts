export type TicketChannel = "Email" | "Phone" | "Chat" | "Social media";

export type TicketType =
  | "Refund request"
  | "Technical issue"
  | "Cancellation request"
  | "Product inquiry"
  | "Billing inquiry";

export type TicketPriority = "Low" | "Medium" | "High" | "Critical";

export type TicketStatus =
  | "open"
  | "triagem"
  | "pending_review"
  | "routed"
  | "human_required"
  | "pending_customer"
  | "closed";

export type TicketScenario =
  | "auto_routed"
  | "human_required"
  | "pending_review"
  | "llm_reclassified"
  | "auto_resolved"
  | "ack_only";

export type ResolvedBy = "auto_ia" | "human";

export interface Ticket {
  id: string;
  ticket_number: number;
  customer_name: string;
  customer_email: string | null;
  channel: TicketChannel;
  ticket_type: TicketType;
  ticket_priority: TicketPriority;
  subject: string;
  description: string;
  status: TicketStatus;
  scenario: TicketScenario | null;
  topic_group: string | null;
  topic_group_llm: string | null;
  confidence: number | null;
  queue_slug: string | null;
  human_required_reason: string | null;
  first_response_at: string | null;
  ack_message: string | null;
  resolved_at: string | null;
  resolved_by: ResolvedBy | null;
  created_at: string;
  updated_at: string;
}

export interface TicketMessage {
  id: string;
  ticket_id: string;
  role: "customer" | "agent" | "system";
  content: string;
  created_at: string;
}

export interface DashboardMetrics {
  open: number;
  in_progress: number;
  waiting_human: number;
  auto_resolved_ia: number;
  resolved_total: number;
  by_scenario: Record<string, number>;
  by_channel: Record<string, number>;
  by_status: Record<string, number>;
  tickets_per_hour: { hour: string; count: number }[];
  recent_tickets: Ticket[];
}

export const STATUS_LABELS: Record<TicketStatus, string> = {
  open: "Aberto",
  triagem: "Em triagem",
  pending_review: "Revisão humana",
  routed: "Roteado",
  human_required: "Humano obrigatório",
  pending_customer: "Aguardando cliente",
  closed: "Resolvido",
};

export const SCENARIO_LABELS: Record<TicketScenario, string> = {
  auto_routed: "Roteado automaticamente",
  human_required: "Fila humana (regra DS1)",
  pending_review: "Baixa confiança",
  llm_reclassified: "Reclassificado por IA",
  auto_resolved: "Resolvido automaticamente",
  ack_only: "Apenas confirmação",
};
