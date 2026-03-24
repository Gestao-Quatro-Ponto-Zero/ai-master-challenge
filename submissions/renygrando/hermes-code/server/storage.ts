import { db } from "./db";
import {
  users, teams, tickets, ticketMessages, ticketEvents, knowledgeBase, bottlenecks, suggestions,
  type InsertUser, type InsertTeam, type InsertTicket, type InsertTicketMessage,
  type User, type Team, type Ticket, type TicketMessage, type TicketEvent,
  type KnowledgeBaseArticle, type Bottleneck, type Suggestion,
  type CreateTicketRequest, type UpdateTicketRequest, type SafeUser,
} from "@shared/schema";
import { eq, desc, and } from "drizzle-orm";
import { scrypt, randomBytes, timingSafeEqual } from "crypto";
import { promisify } from "util";

const scryptAsync = promisify(scrypt);

export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16).toString("hex");
  const buf = (await scryptAsync(password, salt, 64)) as Buffer;
  return `${buf.toString("hex")}.${salt}`;
}

export async function comparePasswords(supplied: string, stored: string): Promise<boolean> {
  const [hashed, salt] = stored.split(".");
  const hashedBuf = Buffer.from(hashed, "hex");
  const suppliedBuf = (await scryptAsync(supplied, salt, 64)) as Buffer;
  return timingSafeEqual(hashedBuf, suppliedBuf);
}

export function toSafeUser(user: User): SafeUser {
  const { passwordHash, ...safe } = user;
  return safe;
}

export interface IStorage {
  // Auth
  getUserByEmail(email: string): Promise<User | undefined>;
  createUserWithPassword(data: { name: string; email: string; password: string; role?: string }): Promise<SafeUser>;

  // Users
  getUser(id: number): Promise<User | undefined>;
  getUsers(): Promise<SafeUser[]>;

  // Teams
  getTeams(): Promise<Team[]>;
  getTeam(id: number): Promise<Team | undefined>;
  createTeam(team: InsertTeam): Promise<Team>;

  // Tickets
  getTickets(filters?: { status?: string; category?: string }): Promise<Ticket[]>;
  getTicketsByUser(userId: number): Promise<Ticket[]>;
  getTicket(id: number): Promise<Ticket | undefined>;
  createTicket(ticket: CreateTicketRequest): Promise<Ticket>;
  updateTicket(id: number, ticket: UpdateTicketRequest): Promise<Ticket | undefined>;

  // Ticket Messages
  getTicketMessages(ticketId: number): Promise<TicketMessage[]>;
  createTicketMessage(msg: InsertTicketMessage): Promise<TicketMessage>;

  // Suggestions
  createSuggestion(suggestion: any): Promise<Suggestion>;
  getSuggestions(ticketId: number): Promise<Suggestion[]>;

  // Dashboard
  getMetrics(): Promise<any>;
}

export class DatabaseStorage implements IStorage {
  async getUserByEmail(email: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.email, email));
    return user;
  }

  async createUserWithPassword(data: { name: string; email: string; password: string; role?: string }): Promise<SafeUser> {
    const passwordHash = await hashPassword(data.password);
    const [user] = await db.insert(users).values({
      name: data.name,
      email: data.email,
      passwordHash,
      role: data.role || "user",
    }).returning();
    return toSafeUser(user);
  }

  async getUser(id: number): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }

  async getUsers(): Promise<SafeUser[]> {
    const all = await db.select().from(users);
    return all.map(toSafeUser);
  }

  async getTeams(): Promise<Team[]> {
    return await db.select().from(teams);
  }

  async getTeam(id: number): Promise<Team | undefined> {
    const [team] = await db.select().from(teams).where(eq(teams.id, id));
    return team;
  }

  async createTeam(team: InsertTeam): Promise<Team> {
    const [created] = await db.insert(teams).values(team).returning();
    return created;
  }

  async getTickets(filters?: { status?: string; category?: string }): Promise<Ticket[]> {
    return await db.select().from(tickets).orderBy(desc(tickets.createdAt));
  }

  async getTicketsByUser(userId: number): Promise<Ticket[]> {
    return await db.select().from(tickets).where(eq(tickets.customerId, userId)).orderBy(desc(tickets.createdAt));
  }

  async getTicket(id: number): Promise<Ticket | undefined> {
    const [ticket] = await db.select().from(tickets).where(eq(tickets.id, id));
    return ticket;
  }

  async createTicket(ticket: CreateTicketRequest): Promise<Ticket> {
    const [created] = await db.insert(tickets).values(ticket).returning();
    return created;
  }

  async updateTicket(id: number, update: UpdateTicketRequest): Promise<Ticket | undefined> {
    const [updated] = await db.update(tickets)
      .set({ ...update, updatedAt: new Date() })
      .where(eq(tickets.id, id))
      .returning();
    return updated;
  }

  async getTicketMessages(ticketId: number): Promise<TicketMessage[]> {
    return await db.select().from(ticketMessages).where(eq(ticketMessages.ticketId, ticketId)).orderBy(ticketMessages.timestamp);
  }

  async createTicketMessage(msg: InsertTicketMessage): Promise<TicketMessage> {
    const [created] = await db.insert(ticketMessages).values(msg).returning();
    return created;
  }

  async createSuggestion(suggestion: any): Promise<Suggestion> {
    const [created] = await db.insert(suggestions).values(suggestion).returning();
    return created;
  }

  async getSuggestions(ticketId: number): Promise<Suggestion[]> {
    return await db.select().from(suggestions).where(eq(suggestions.ticketId, ticketId));
  }

  async getMetrics(): Promise<any> {
    const allTickets = await db.select().from(tickets);
    const activeTickets = allTickets.filter(t => t.status !== 'Resolvido' && t.status !== 'Fechado' && t.status !== 'Resolved' && t.status !== 'Closed').length;
    const resolvedTickets = allTickets.filter(t => t.status === 'Resolvido' || t.status === 'Resolved' || t.status === 'Fechado' || t.status === 'Closed');
    const avgResolutionTime = resolvedTickets.length > 0
      ? resolvedTickets.reduce((acc, t) => acc + (t.resolutionTime || 0), 0) / resolvedTickets.length
      : 0;
    const slaRiskCount = allTickets.filter(t => t.priority === 'Alta' || t.priority === 'Crítica' || t.priority === 'High' || t.priority === 'Critical').length;
    const ticketsByCategory = allTickets.reduce((acc: any, t) => {
      acc[t.category] = (acc[t.category] || 0) + 1;
      return acc;
    }, {});
    const autoResolved = allTickets.filter(t => t.confidenceScore && t.confidenceScore > 0.9 && (t.status === 'Resolvido' || t.status === 'Resolved')).length;
    const automationRate = allTickets.length > 0 ? Math.round((autoResolved / allTickets.length) * 100) : 0;
    const allBottlenecks = await db.select().from(bottlenecks).orderBy(desc(bottlenecks.timestamp));
    return {
      activeTickets,
      totalTickets: allTickets.length,
      resolvedTickets: resolvedTickets.length,
      avgResolutionTime,
      slaRiskCount,
      automationRate,
      ticketsByCategory,
      bottlenecks: allBottlenecks,
    };
  }
}

export const storage = new DatabaseStorage();
