import type { Express, Request, Response } from "express";
import type { Server } from "http";
import { storage, comparePasswords } from "./storage";
import { api } from "@shared/routes";
import { registerSchema, loginSchema } from "@shared/schema";
import { z } from "zod";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.AI_INTEGRATIONS_OPENAI_API_KEY,
  baseURL: process.env.AI_INTEGRATIONS_OPENAI_BASE_URL,
});

declare module "express-session" {
  interface SessionData {
    userId: number;
  }
}

function requireAuth(req: Request, res: Response, next: any) {
  if (!req.session?.userId) return res.status(401).json({ message: "Não autenticado" });
  next();
}

async function requireAdmin(req: Request, res: Response, next: any) {
  if (!req.session?.userId) return res.status(401).json({ message: "Não autenticado" });
  const user = await storage.getUser(req.session.userId);
  if (!user || user.role !== "admin") return res.status(403).json({ message: "Acesso negado" });
  next();
}

export async function registerRoutes(httpServer: Server, app: Express): Promise<Server> {
  // ── AUTH ────────────────────────────────────────
  app.post(api.auth.register.path, async (req, res) => {
    try {
      const data = registerSchema.parse(req.body);
      const existing = await storage.getUserByEmail(data.email);
      if (existing) return res.status(409).json({ message: "E-mail já cadastrado" });
      const user = await storage.createUserWithPassword(data);
      req.session!.userId = user.id;
      res.status(201).json(user);
    } catch (err) {
      if (err instanceof z.ZodError) return res.status(400).json({ message: err.errors[0].message });
      res.status(500).json({ message: "Erro interno" });
    }
  });

  app.post(api.auth.login.path, async (req, res) => {
    try {
      const data = loginSchema.parse(req.body);
      const user = await storage.getUserByEmail(data.email);
      if (!user) return res.status(401).json({ message: "E-mail ou senha incorretos" });
      const valid = await comparePasswords(data.password, user.passwordHash);
      if (!valid) return res.status(401).json({ message: "E-mail ou senha incorretos" });
      req.session!.userId = user.id;
      const { passwordHash, ...safe } = user;
      res.json(safe);
    } catch (err) {
      if (err instanceof z.ZodError) return res.status(400).json({ message: err.errors[0].message });
      res.status(500).json({ message: "Erro interno" });
    }
  });

  app.post(api.auth.logout.path, (req, res) => {
    req.session!.destroy(() => res.json({ message: "Sessão encerrada" }));
  });

  app.get(api.auth.me.path, async (req, res) => {
    if (!req.session?.userId) return res.json(null);
    const user = await storage.getUser(req.session.userId);
    if (!user) return res.json(null);
    const { passwordHash, ...safe } = user;
    res.json(safe);
  });

  // ── TICKETS ────────────────────────────────────
  app.get(api.tickets.list.path, requireAuth, async (req, res) => {
    try {
      const tickets = await storage.getTickets();
      res.json(tickets);
    } catch { res.status(500).json({ message: "Erro interno" }); }
  });

  app.get(api.tickets.myTickets.path, requireAuth, async (req, res) => {
    try {
      const tickets = await storage.getTicketsByUser(req.session!.userId!);
      res.json(tickets);
    } catch { res.status(500).json({ message: "Erro interno" }); }
  });

  app.get(api.tickets.get.path, requireAuth, async (req, res) => {
    try {
      const ticket = await storage.getTicket(Number(req.params.id));
      if (!ticket) return res.status(404).json({ message: "Chamado não encontrado" });
      res.json(ticket);
    } catch { res.status(500).json({ message: "Erro interno" }); }
  });

  app.post(api.tickets.create.path, requireAuth, async (req, res) => {
    try {
      const input = api.tickets.create.input.parse(req.body);
      const ticket = await storage.createTicket({
        ...input,
        customerId: req.session!.userId,
      });
      res.status(201).json(ticket);
    } catch (err) {
      if (err instanceof z.ZodError) return res.status(400).json({ message: err.errors[0].message });
      res.status(500).json({ message: "Erro interno" });
    }
  });

  app.patch(api.tickets.update.path, requireAuth, async (req, res) => {
    try {
      const id = Number(req.params.id);
      const input = api.tickets.update.input.parse(req.body);
      const ticket = await storage.updateTicket(id, input);
      if (!ticket) return res.status(404).json({ message: "Chamado não encontrado" });
      res.json(ticket);
    } catch (err) {
      if (err instanceof z.ZodError) return res.status(400).json({ message: err.errors[0].message });
      res.status(500).json({ message: "Erro interno" });
    }
  });

  // ── TICKET MESSAGES ────────────────────────────
  app.get(api.tickets.messages.list.path, requireAuth, async (req, res) => {
    try {
      const msgs = await storage.getTicketMessages(Number(req.params.id));
      res.json(msgs);
    } catch { res.status(500).json({ message: "Erro interno" }); }
  });

  app.post(api.tickets.messages.create.path, requireAuth, async (req, res) => {
    try {
      const ticketId = Number(req.params.id);
      const user = await storage.getUser(req.session!.userId!);
      const msg = await storage.createTicketMessage({
        ticketId,
        senderType: "user",
        senderName: user?.name || "Usuário",
        message: req.body.message,
      });
      res.status(201).json(msg);
    } catch { res.status(500).json({ message: "Erro interno" }); }
  });

  // ── AI CLASSIFY ────────────────────────────────
  app.post(api.tickets.classify.path, requireAuth, async (req, res) => {
    try {
      const { description } = req.body;
      const response = await openai.chat.completions.create({
        model: "gpt-5.1",
        messages: [{
          role: "system",
          content: `Você é um classificador de chamados de TI do sistema Hermes.
Classifique o chamado em uma das categorias: Acesso, Direitos Administrativos, Suporte RH, Hardware, Projeto Interno, Diversos, Compra, Armazenamento.
Determine a prioridade: Baixa, Média, Alta, Crítica.
Responda SOMENTE em JSON: { "category": "...", "confidence": 0.95, "priority": "..." }`
        }, { role: "user", content: description }],
        response_format: { type: "json_object" },
      });
      const result = JSON.parse(response.choices[0].message.content || "{}");
      res.json({ category: result.category || "Diversos", confidence: result.confidence || 0.5, priority: result.priority || "Baixa" });
    } catch { res.status(500).json({ message: "Falha na classificação" }); }
  });

  // ── AI SUGGEST RESPONSE ────────────────────────
  app.post(api.tickets.suggestResponse.path, requireAuth, async (req, res) => {
    try {
      const ticketId = Number(req.params.id);
      const ticket = await storage.getTicket(ticketId);
      if (!ticket) return res.status(404).json({ message: "Chamado não encontrado" });
      const response = await openai.chat.completions.create({
        model: "gpt-5.1",
        messages: [{
          role: "system",
          content: "Você é um especialista sênior de suporte de TI. Gere uma resposta profissional e útil em português (PT-BR) para o chamado do usuário.",
        }, {
          role: "user",
          content: `Título: ${ticket.title}\nDescrição: ${ticket.description}`,
        }],
      });
      const suggestion = await storage.createSuggestion({
        ticketId,
        suggestedResponse: response.choices[0].message.content || "Como posso ajudar?",
        confidence: 0.9,
      });
      res.json(suggestion);
    } catch { res.status(500).json({ message: "Falha ao gerar sugestão" }); }
  });

  // ── AI CHAT AGENT ──────────────────────────────
  app.post(api.ai.chat.path, requireAuth, async (req, res) => {
    try {
      const { messages } = req.body as { messages: { role: "user" | "assistant"; content: string }[] };

      const systemPrompt = `Você é o Assistente Hermes, um agente de suporte de TI inteligente.
Seu objetivo é ajudar o usuário a abrir um chamado de suporte de TI através de uma conversa natural.

Você deve:
1. Entender o problema do usuário fazendo perguntas claras e objetivas
2. Coletar as informações necessárias: qual é o problema, qual produto/sistema está afetado, descrição detalhada
3. Quando tiver informações suficientes (mínimo: descrição clara do problema), confirme com o usuário e registre o chamado

Categorias disponíveis: Acesso, Direitos Administrativos, Suporte RH, Hardware, Projeto Interno, Diversos, Compra, Armazenamento.
Prioridades: Baixa, Média, Alta, Crítica.

Quando você tiver informações suficientes para abrir o chamado, responda com um JSON no seguinte formato ao final da mensagem:
<TICKET_DATA>
{"title":"...", "description":"...", "category":"...", "priority":"...", "channel":"chat"}
</TICKET_DATA>

Sempre responda em português brasileiro de forma amigável e profissional.`;

      const response = await openai.chat.completions.create({
        model: "gpt-5.1",
        messages: [
          { role: "system", content: systemPrompt },
          ...messages,
        ],
        max_completion_tokens: 1024,
      });

      const reply = response.choices[0].message.content || "";

      // Extract ticket data if present
      const match = reply.match(/<TICKET_DATA>([\s\S]*?)<\/TICKET_DATA>/);
      let ticketData = null;
      let cleanReply = reply;

      if (match) {
        try {
          ticketData = JSON.parse(match[1]);
          cleanReply = reply.replace(/<TICKET_DATA>[\s\S]*?<\/TICKET_DATA>/, "").trim();
        } catch { /* ignore */ }
      }

      res.json({
        reply: cleanReply,
        ticketData,
        isComplete: !!ticketData,
      });
    } catch { res.status(500).json({ message: "Erro no agente de IA" }); }
  });

  // ── DASHBOARD ──────────────────────────────────
  app.get(api.dashboard.metrics.path, requireAuth, async (req, res) => {
    try {
      res.json(await storage.getMetrics());
    } catch { res.status(500).json({ message: "Erro interno" }); }
  });

  // ── USERS / TEAMS ──────────────────────────────
  app.get(api.users.list.path, requireAuth, async (req, res) => {
    try { res.json(await storage.getUsers()); }
    catch { res.status(500).json({ message: "Erro interno" }); }
  });

  app.get(api.teams.list.path, requireAuth, async (req, res) => {
    try { res.json(await storage.getTeams()); }
    catch { res.status(500).json({ message: "Erro interno" }); }
  });

  await seedDatabase();
  return httpServer;
}

async function seedDatabase() {
  const existing = await storage.getUserByEmail("admin@hermes.io");
  if (!existing) {
    await storage.createUserWithPassword({ name: "Administrador Hermes", email: "admin@hermes.io", password: "hermes123", role: "admin" });
    const user = await storage.createUserWithPassword({ name: "João Silva", email: "joao@empresa.com", password: "senha123", role: "user" });

    const itTeam = await storage.createTeam({ name: "Suporte TI", type: "Técnico", slaHours: 24 });
    const hrTeam = await storage.createTeam({ name: "Suporte RH", type: "Recursos Humanos", slaHours: 48 });

    await storage.createTicket({ title: "Não consigo acessar a VPN", description: "Recebo o erro 403 ao tentar conectar na VPN corporativa após a última atualização do Windows.", category: "Acesso", priority: "Alta", status: "Aberto", channel: "web", confidenceScore: 0.95, customerId: user.id, assignedTeamId: itTeam.id });
    await storage.createTicket({ title: "Mouse com duplo clique", description: "O mouse do meu notebook está dando duplo clique com um único clique. Preciso de um substituto.", category: "Hardware", priority: "Baixa", status: "Resolvido", channel: "web", confidenceScore: 0.88, customerId: user.id, assignedTeamId: itTeam.id, resolutionTime: 120 });
    await storage.createTicket({ title: "Solicitar acesso ao sistema ERP", description: "Precisamos de acesso ao módulo financeiro do ERP para o novo colaborador do departamento.", category: "Direitos Administrativos", priority: "Média", status: "Em Andamento", channel: "chat", confidenceScore: 0.91, customerId: user.id, assignedTeamId: itTeam.id });
  }
}
