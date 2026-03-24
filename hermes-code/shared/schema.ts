import { pgTable, text, serial, integer, timestamp, json, real, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  passwordHash: text("password_hash").notNull(),
  role: text("role").notNull().default("user"), // 'admin' | 'user'
  team: text("team"),
  createdAt: timestamp("created_at").defaultNow(),
});

export const teams = pgTable("teams", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  type: text("type").notNull(),
  slaHours: integer("sla_hours").notNull(),
});

export const tickets = pgTable("tickets", {
  id: serial("id").primaryKey(),
  title: text("title").notNull(),
  description: text("description").notNull(),
  category: text("category").notNull(),
  priority: text("priority").notNull(),
  status: text("status").notNull(),
  confidenceScore: real("confidence_score"),
  channel: text("channel").notNull().default("web"),
  customerId: integer("customer_id").references(() => users.id),
  assignedTeamId: integer("assigned_team").references(() => teams.id),
  assignedUserId: integer("assigned_user").references(() => users.id),
  resolution: text("resolution"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
  resolutionTime: integer("resolution_time"),
});

export const ticketMessages = pgTable("ticket_messages", {
  id: serial("id").primaryKey(),
  ticketId: integer("ticket_id").notNull().references(() => tickets.id, { onDelete: "cascade" }),
  senderType: text("sender_type").notNull(), // 'user' | 'agent' | 'ai'
  senderName: text("sender_name"),
  message: text("message").notNull(),
  timestamp: timestamp("timestamp").defaultNow(),
});

export const ticketEvents = pgTable("ticket_events", {
  id: serial("id").primaryKey(),
  ticketId: integer("ticket_id").notNull().references(() => tickets.id),
  eventType: text("event_type").notNull(),
  metadata: json("metadata"),
  timestamp: timestamp("timestamp").defaultNow(),
});

export const knowledgeBase = pgTable("knowledge_base", {
  id: serial("id").primaryKey(),
  title: text("title").notNull(),
  content: text("content").notNull(),
  category: text("category").notNull(),
  embedding: json("embedding"),
});

export const suggestions = pgTable("suggestions", {
  id: serial("id").primaryKey(),
  ticketId: integer("ticket_id").notNull().references(() => tickets.id),
  suggestedResponse: text("suggested_response").notNull(),
  confidence: real("confidence").notNull(),
  isApplied: boolean("is_applied").default(false),
});

export const bottlenecks = pgTable("bottlenecks", {
  id: serial("id").primaryKey(),
  category: text("category").notNull(),
  avgResolution: real("avg_resolution").notNull(),
  ticketCount: integer("ticket_count").notNull(),
  riskScore: real("risk_score").notNull(),
  timestamp: timestamp("timestamp").defaultNow(),
});

// Zod schemas
export const insertUserSchema = createInsertSchema(users).omit({ id: true, createdAt: true });
export const insertTeamSchema = createInsertSchema(teams).omit({ id: true });
export const insertTicketSchema = createInsertSchema(tickets).omit({ id: true, createdAt: true, updatedAt: true, resolutionTime: true });
export const insertTicketMessageSchema = createInsertSchema(ticketMessages).omit({ id: true, timestamp: true });
export const insertTicketEventSchema = createInsertSchema(ticketEvents).omit({ id: true, timestamp: true });
export const insertKnowledgeBaseSchema = createInsertSchema(knowledgeBase).omit({ id: true });
export const insertSuggestionSchema = createInsertSchema(suggestions).omit({ id: true });

// Auth schemas
export const registerSchema = z.object({
  name: z.string().min(2, "Nome deve ter pelo menos 2 caracteres"),
  email: z.string().email("E-mail inválido"),
  password: z.string().min(6, "Senha deve ter pelo menos 6 caracteres"),
  role: z.enum(["user", "admin"]).optional(),
});
export const loginSchema = z.object({
  email: z.string().email("E-mail inválido"),
  password: z.string().min(1, "Senha obrigatória"),
});

// Types
export type User = typeof users.$inferSelect;
export type Team = typeof teams.$inferSelect;
export type Ticket = typeof tickets.$inferSelect;
export type TicketMessage = typeof ticketMessages.$inferSelect;
export type TicketEvent = typeof ticketEvents.$inferSelect;
export type KnowledgeBaseArticle = typeof knowledgeBase.$inferSelect;
export type Suggestion = typeof suggestions.$inferSelect;
export type Bottleneck = typeof bottlenecks.$inferSelect;

export type InsertUser = z.infer<typeof insertUserSchema>;
export type InsertTeam = z.infer<typeof insertTeamSchema>;
export type InsertTicket = z.infer<typeof insertTicketSchema>;
export type InsertTicketMessage = z.infer<typeof insertTicketMessageSchema>;

export type CreateTicketRequest = InsertTicket;
export type UpdateTicketRequest = Partial<InsertTicket>;
export type RegisterRequest = z.infer<typeof registerSchema>;
export type LoginRequest = z.infer<typeof loginSchema>;

export type SafeUser = Omit<User, "passwordHash">;

export type DashboardMetricsResponse = {
  activeTickets: number;
  avgResolutionTime: number;
  slaRiskCount: number;
  automationRate: number;
  bottlenecks: Bottleneck[];
  ticketsByCategory: Record<string, number>;
  totalTickets: number;
  resolvedTickets: number;
};
