import type {
  TicketCategory,
  TicketPriority,
  TicketSource,
  TicketStatus,
} from "@/lib/types";

const STATUS_LABELS: Record<TicketStatus, string> = {
  open: "Aberto",
  pending: "Pendente",
  resolved: "Resolvido",
  deflected: "Resolvido por IA",
};

const PRIORITY_LABELS: Record<TicketPriority, string> = {
  low: "Baixa",
  medium: "Média",
  high: "Alta",
  critical: "Crítica",
};

const SOURCE_LABELS: Record<TicketSource, string> = {
  text: "Texto",
  audio: "Áudio",
};

const CATEGORY_LABELS: Record<TicketCategory, string> = {
  Hardware: "Hardware",
  Software: "Software",
  Access: "Acesso",
  Storage: "Armazenamento",
  HR: "RH",
  Purchase: "Compras",
  Network: "Rede",
  Other: "Outros",
};

const CHANNEL_LABELS: Record<string, string> = {
  Email: "E-mail",
  Phone: "Telefone",
  Chat: "Chat",
  "Social media": "Mídias sociais",
  Unknown: "Não informado",
};

const TICKET_TYPE_LABELS: Record<string, string> = {
  "Refund request": "Solicitação de reembolso",
  "Technical issue": "Problema técnico",
  "Cancellation request": "Solicitação de cancelamento",
  "Product inquiry": "Dúvida sobre produto",
  "Billing inquiry": "Dúvida de cobrança",
  Unknown: "Não informado",
};

const DATASET_STATUS_LABELS: Record<string, string> = {
  Open: "Aberto",
  Closed: "Fechado",
  "Pending Customer Response": "Pendente de resposta do cliente",
};

export function statusLabel(value: TicketStatus) {
  return STATUS_LABELS[value];
}

export function priorityLabel(value: TicketPriority) {
  return PRIORITY_LABELS[value];
}

export function sourceLabel(value: TicketSource) {
  return SOURCE_LABELS[value];
}

export function categoryLabel(value: TicketCategory) {
  return CATEGORY_LABELS[value];
}

export function channelLabel(value: string) {
  return CHANNEL_LABELS[value] ?? value;
}

export function ticketTypeLabel(value: string) {
  return TICKET_TYPE_LABELS[value] ?? value;
}

export function datasetStatusLabel(value: string) {
  return DATASET_STATUS_LABELS[value] ?? value;
}
