import { z } from 'zod';
import { insertTicketSchema, tickets, users, teams, registerSchema, loginSchema } from './schema';

export const errorSchemas = {
  validation: z.object({ message: z.string(), field: z.string().optional() }),
  notFound: z.object({ message: z.string() }),
  unauthorized: z.object({ message: z.string() }),
  internal: z.object({ message: z.string() }),
};

export const api = {
  auth: {
    register: {
      method: 'POST' as const,
      path: '/api/auth/register' as const,
      input: registerSchema,
      responses: { 201: z.object({ id: z.number(), name: z.string(), email: z.string(), role: z.string() }) },
    },
    login: {
      method: 'POST' as const,
      path: '/api/auth/login' as const,
      input: loginSchema,
      responses: { 200: z.object({ id: z.number(), name: z.string(), email: z.string(), role: z.string() }) },
    },
    logout: {
      method: 'POST' as const,
      path: '/api/auth/logout' as const,
      responses: { 200: z.object({ message: z.string() }) },
    },
    me: {
      method: 'GET' as const,
      path: '/api/auth/me' as const,
      responses: {
        200: z.object({ id: z.number(), name: z.string(), email: z.string(), role: z.string() }).nullable(),
      },
    },
  },
  tickets: {
    list: {
      method: 'GET' as const,
      path: '/api/tickets' as const,
      responses: { 200: z.array(z.custom<typeof tickets.$inferSelect>()) },
    },
    myTickets: {
      method: 'GET' as const,
      path: '/api/tickets/mine' as const,
      responses: { 200: z.array(z.custom<typeof tickets.$inferSelect>()) },
    },
    get: {
      method: 'GET' as const,
      path: '/api/tickets/:id' as const,
      responses: { 200: z.custom<typeof tickets.$inferSelect>(), 404: errorSchemas.notFound },
    },
    create: {
      method: 'POST' as const,
      path: '/api/tickets' as const,
      input: insertTicketSchema,
      responses: { 201: z.custom<typeof tickets.$inferSelect>(), 400: errorSchemas.validation },
    },
    update: {
      method: 'PATCH' as const,
      path: '/api/tickets/:id' as const,
      input: insertTicketSchema.partial(),
      responses: { 200: z.custom<typeof tickets.$inferSelect>(), 404: errorSchemas.notFound },
    },
    classify: {
      method: 'POST' as const,
      path: '/api/tickets/classify' as const,
      input: z.object({ description: z.string() }),
      responses: { 200: z.object({ category: z.string(), confidence: z.number(), priority: z.string() }) },
    },
    suggestResponse: {
      method: 'POST' as const,
      path: '/api/tickets/:id/suggest-response' as const,
      responses: { 200: z.any(), 404: errorSchemas.notFound },
    },
    messages: {
      list: {
        method: 'GET' as const,
        path: '/api/tickets/:id/messages' as const,
        responses: { 200: z.array(z.any()) },
      },
      create: {
        method: 'POST' as const,
        path: '/api/tickets/:id/messages' as const,
        input: z.object({ message: z.string() }),
        responses: { 201: z.any() },
      },
    },
  },
  ai: {
    chat: {
      method: 'POST' as const,
      path: '/api/ai/chat' as const,
      input: z.object({
        messages: z.array(z.object({ role: z.enum(['user', 'assistant']), content: z.string() })),
      }),
      responses: {
        200: z.object({
          reply: z.string(),
          ticketData: z.object({
            title: z.string(),
            description: z.string(),
            category: z.string(),
            priority: z.string(),
            channel: z.string(),
          }).nullable(),
          isComplete: z.boolean(),
        }),
      },
    },
  },
  dashboard: {
    metrics: {
      method: 'GET' as const,
      path: '/api/dashboard/metrics' as const,
      responses: { 200: z.any() },
    },
  },
  users: {
    list: { method: 'GET' as const, path: '/api/users' as const, responses: { 200: z.array(z.any()) } },
  },
  teams: {
    list: { method: 'GET' as const, path: '/api/teams' as const, responses: { 200: z.array(z.any()) } },
  },
};

export function buildUrl(path: string, params?: Record<string, string | number>): string {
  let url = path;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (url.includes(`:${key}`)) url = url.replace(`:${key}`, String(value));
    });
  }
  return url;
}
