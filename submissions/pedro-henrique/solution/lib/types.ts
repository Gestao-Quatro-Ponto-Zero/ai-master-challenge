export type Role = "admin" | "customer";

export type TicketSource = "text" | "audio";

export type TicketPriority = "low" | "medium" | "high" | "critical";

export type TicketStatus = "open" | "pending" | "resolved" | "deflected";

export type TicketCategory =
  | "Hardware"
  | "Software"
  | "Access"
  | "Storage"
  | "HR"
  | "Purchase"
  | "Network"
  | "Other";

export type SessionUser = {
  id: string;
  email: string;
  role: Role;
};

export type RagSource = {
  id: string;
  description: string;
  resolution: string;
  category: string;
  similarity: number;
};

export type Ticket = {
  id: number;
  customer_id: string;
  source: TicketSource;
  audio_path?: string;
  raw_text: string;
  category: TicketCategory;
  priority: TicketPriority;
  status: TicketStatus;
  rag_suggestion?: string;
  rag_confidence?: number;
  resolved_by_ai: boolean;
  created_at: string;
  resolved_at?: string;
};

export type DeflectionEvent = {
  id: number;
  customer_id: string;
  raw_text: string;
  top_matches: RagSource[];
  created_at: string;
};
