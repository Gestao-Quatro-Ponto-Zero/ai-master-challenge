# Índice de Artefatos de Código — G4 Hermes

**Data:** 24 de março de 2026  
**Localização:** `/submissions/renygrando/hermes-code/`  
**Status:** ✅ Código completo e acessível para auditoria

---

## 📂 Mapa de Navegação

### Raiz do Projeto

```
hermes-code/
├── package.json              # Dependências e scripts
├── tsconfig.json             # Configuração TypeScript
├── vite.config.ts            # Build configuration
├── tailwind.config.ts        # Estilos CSS
├── drizzle.config.ts         # ORM database
├── components.json           # Shadcn UI config
├── postcss.config.js         # CSS processing
├── .gitignore                # Git ignore rules
├── replit.md                 # Instruções Replit
└── README_SUBMISSAO.md       # 📌 START HERE
```

---

## 🎯 Arquivos Principais

### Frontend — React + TypeScript

```
client/
├── src/
│   ├── App.tsx                           # App raiz
│   ├── main.tsx                          # Entry point
│   ├── index.css                         # Tailwind imports
│   ├── context/
│   │   ├── auth.tsx                      # 🔐 Context de autenticação
│   │   └── theme.tsx                     # 🎨 Context de tema
│   ├── components/
│   │   ├── ui/                           # 🧩 Componentes reutilizáveis (Shadcn)
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── table.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── card.tsx
│   │   │   └── [+10 mais]
│   │   ├── Header.tsx                    # 📍 Cabeçalho + navegação
│   │   ├── Sidebar.tsx                   # 📍 Menu lateral
│   │   ├── AuthForm.tsx                  # 🔐 Login/registro
│   │   └── [componentes específicos]
│   ├── pages/
│   │   ├── Dashboard.tsx                 # 📊 Dashboard principal
│   │   ├── TicketList.tsx                # 📋 Lista de tickets
│   │   ├── TicketDetail.tsx              # 🔍 Detalhes de ticket
│   │   ├── NewTicket.tsx                 # ➕ Criar ticket
│   │   ├── Analytics.tsx                 # 📈 Análises
│   │   ├── Settings.tsx                  # ⚙️ Configurações
│   │   └── Login.tsx                     # 🔓 Página login
│   └── types/
│       └── index.ts                      # TypeScript types
└── tsconfig.json
```

**Funcionalidades Frontend:**

- ✅ Autenticação com JWT
- ✅ Formulários de criação/edição de tickets
- ✅ Dashboard com métricas em tempo real
- ✅ Busca e filtros avançados
- ✅ Interface responsiva (Tailwind + Shadcn)
- ✅ Temas dark/light

---

### Backend — Node.js + Express

```
server/
├── index.ts                              # 🚀 Servidor Express (entry point)
├── db.ts                                 # 💾 Conexão banco de dados (Drizzle)
├── routes.ts                             # 🔀 Definição de rotas
├── storage.ts                            # 💾 Sistema de armazenamento
├── static.ts                             # 🖼️ Servir arquivos estáticos
├── vite.ts                               # ⚡ Vite dev server
├── api/
│   ├── auth.ts                           # 🔐 Endpoints autenticação
│   │   └── POST /api/auth/login          # Login
│   │   └── POST /api/auth/register       # Registro
│   │   └── POST /api/auth/logout         # Logout
│   ├── tickets.ts                        # 📋 Endpoints de tickets
│   │   └── GET /api/tickets              # Listar
│   │   └── POST /api/tickets             # Criar
│   │   └── GET /api/tickets/:id          # Detalhe
│   │   └── PATCH /api/tickets/:id        # Atualizar
│   │   └── DELETE /api/tickets/:id       # Deletar
│   ├── classification.ts                 # 🤖 Classificação com IA
│   │   └── POST /api/classify            # Classificar ticket
│   ├── suggestions.ts                    # 💡 Sugestões de resposta
│   │   └── POST /api/suggestions         # Gerar sugestão
│   ├── analytics.ts                      # 📊 Métricas operacionais
│   │   └── GET /api/analytics/overview   # Resumo
│   │   └── GET /api/analytics/trends     # Tendências
│   └── health.ts                         # ❤️ Health check
├── middleware/
│   ├── auth.ts                           # 🔐 Verificação JWT
│   ├── error.ts                          # ❌ Tratamento de erros
│   ├── cors.ts                           # 🔄 CORS
│   └── validation.ts                     # ✓ Validação de input
├── models/
│   ├── ticket.ts                         # 📋 Schema ticket
│   ├── user.ts                           # 👤 Schema user
│   ├── response.ts                       # 💬 Schema resposta
│   └── analytics.ts                      # 📊 Schema métricas
├── ai/
│   ├── gemini.ts                         # 🤖 Integração Google Gemini
│   ├── prompts/
│   │   ├── classify.prompt               # Prompt classificação
│   │   ├── response.prompt               # Prompt geração de resposta
│   │   └── priority.prompt               # Prompt detecção prioridade
│   └── utils.ts                          # Utilitários IA
└── utils/
    ├── logger.ts                         # 📝 Logging
    ├── validators.ts                     # ✓ Validadores
    └── helpers.ts                        # 🛠️ Funções auxiliares
```

**Funcionalidades Backend:**

- ✅ API REST completa (CRUD)
- ✅ Autenticação JWT com refresh tokens
- ✅ Classificação de tickets com Gemini API
- ✅ Geração de respostas sugeridas
- ✅ Detecção de prioridade automática
- ✅ Métricas operacionais em tempo real
- ✅ Tratamento de erros centralizado
- ✅ Validação de inputs

---

### Dados Compartilhados

```
shared/
├── schema.ts                             # 🗄️ Schema Drizzle ORM
├── routes.ts                             # 🛣️ Definição de rotas tipo-safe
├── models/
│   ├── chat.ts                           # 💬 Modelo conversa IA
│   ├── ticket.ts                         # 📋 Modelo ticket
│   ├── user.ts                           # 👤 Modelo usuário
│   ├── response.ts                       # 💬 Modelo resposta
│   └── analytics.ts                      # 📊 Modelo métricas
└── types.ts                              # 🔤 Tipos TypeScript globals
```

---

### Scripts & Configuração

```
script/
├── build.ts                              # 🏗️ Build script
└── seed.ts                               # 🌱 Seed com dados de teste

tailwind.config.ts                        # 🎨 Estilos Tailwind
drizzle.config.ts                         # 💾 ORM config
vite.config.ts                            # ⚡ Build config
tsconfig.json                             # 🔤 TypeScript config
components.json                           # 🧩 Shadcn UI config
package.json                              # 📦 Dependências
```

---

## 🔍 Guia Rápido por Funcionalidade

### 1. Autenticação

📁 `/server/api/auth.ts` + `/server/middleware/auth.ts`  
🎨 `/client/src/pages/Login.tsx`  
🔐 `/client/src/context/auth.tsx`

**Como traça:** Login → JWT generated → Stored em localStorage → Headers em requests

### 2. Criação de Ticket

📁 `/server/api/tickets.ts` (POST endpoint)  
🎨 `/client/src/pages/NewTicket.tsx`  
🤖 `/server/api/classification.ts` (classifica automaticamente)

**Fluxo:** User submete → Backend valida → Gemini classifica → Prioridade gerada → Salvo no DB

### 3. Classificação Automática com IA

📁 `/server/api/classification.ts` (endpoint)  
📁 `/server/ai/gemini.ts` (integração IA)  
📁 `/server/ai/prompts/classify.prompt` (prompt)

**Como funciona:** Ticket text → Gemini API → Category + Confidence → Stored

### 4. Dashboard com Métricas

📁 `/client/src/pages/Dashboard.tsx` (frontend)  
📁 `/server/api/analytics.ts` (backend)

**Métricas:** Volume, CSAT médio, tempo resolução, taxa automação, SLA breaches

### 5. Sugestões de Resposta

📁 `/server/api/suggestions.ts` (endpoint)  
📁 `/server/ai/gemini.ts` (geração)  
📁 `/server/ai/prompts/response.prompt` (template)

**Como:** Ticket → Gemini gera sugestão → User aprova/edita → Responde cliente

---

## 🗄️ Banco de Dados

### Schema Drizzle

📁 `/shared/schema.ts`

**Tabelas:**

- `users` — Usuários (email, senha hash, role)
- `tickets` — Tickets (descrição, categoria, prioridade, status)
- `responses` — Respostas (texto, timestamp, author)
- `analytics` — Métricas agregadas (CSAT, tempo resolução, volume)
- `ai_classifications` — Histórico de classificações (para melhoria modelo)

**Relacionamentos:**

- `tickets` → `users` (creator_id, assigned_to)
- `responses` → `tickets` (ticket_id)
- `responses` → `users` (author_id)

---

## 🚀 Como Rodar

### Instalação

```bash
cd hermes-code
npm install
```

### Desenvolvimento

```bash
npm run dev
# Frontend: http://localhost:5173
# Backend: http://localhost:3000
```

### Build Produção

```bash
npm run build
npm run preview
```

### Seed Dados

```bash
npm run db:seed
```

---

## 🔗 Endpoints API Principais

| Método | Endpoint                  | Autenticação | Descrição               |
| ------ | ------------------------- | ------------ | ----------------------- |
| POST   | `/api/auth/login`         | ❌           | Login usuário           |
| POST   | `/api/auth/register`      | ❌           | Registrar usuário       |
| GET    | `/api/tickets`            | ✅           | Listar tickets          |
| POST   | `/api/tickets`            | ✅           | Criar ticket            |
| GET    | `/api/tickets/:id`        | ✅           | Detalhe ticket          |
| PATCH  | `/api/tickets/:id`        | ✅           | Atualizar ticket        |
| POST   | `/api/classify`           | ✅           | Classificar com IA      |
| POST   | `/api/suggestions`        | ✅           | Gerar resposta sugerida |
| GET    | `/api/analytics/overview` | ✅           | Métricas                |

---

## 🤖 Integração IA (Gemini)

**Arquivo:** `/server/ai/gemini.ts`

### Prompts Utilizados

1. **Classificação**
   - Input: Texto do ticket
   - Output: { category, confidence }
   - Modelo: zero-shot classification

2. **Resposta**
   - Input: Ticket + histórico similar
   - Output: { suggested_response, tone }
   - Modelo: few-shot com história

3. **Prioridade**
   - Input: Tickets anteriores do même cliente
   - Output: { priority_level, justification }
   - Modelo: rule-based + IA

### Variáveis de Ambiente

```env
GEMINI_API_KEY=seu-api-key-aqui
```

---

## 📊 Estrutura de Dados Exemplo

### Ticket

```json
{
  "id": "ticket-001",
  "title": "Cannot reset password",
  "description": "I tried to reset my password but didn't receive the email",
  "category": "Access",
  "priority": "High",
  "status": "Open",
  "created_at": "2026-03-24T10:00:00Z",
  "created_by": "customer@email.com",
  "assigned_to": "agent1@company.com",
  "csat_rating": null
}
```

### Response

```json
{
  "id": "response-001",
  "ticket_id": "ticket-001",
  "text": "Please check your spam folder...",
  "created_at": "2026-03-24T10:15:00Z",
  "author": "agent1@company.com",
  "is_automated": false
}
```

### Analytics

```json
{
  "period": "2026-03-24",
  "total_tickets": 45,
  "avg_resolution_time_hours": 12.3,
  "avg_csat": 3.8,
  "auto_resolved_percentage": 28.5,
  "sla_breaches": 2
}
```

---

## 🧪 Testes (Código Presente)

```bash
# Unit tests
npm run test

# Integration tests
npm run test:integration

# E2E (opcional)
npm run test:e2e
```

---

## 📋 Checklist de Auditoria

Use este checklist para auditar o código:

- [ ] **Frontend rodando** — `npm run dev` e acessar http://localhost:5173
- [ ] **Backend respondendo** — GET http://localhost:3000/health
- [ ] **Autenticação funcionando** — Login com admin/user
- [ ] **Criar ticket** — POST novo ticket via UI
- [ ] **Classificação IA** — Ticket é classificado automaticamente
- [ ] **Dashboard mostra métricas** — Analytics página exibe dados
- [ ] **Banco de dados criado** — SQL queries retornam dados
- [ ] **Env vars configuradas** — Gemini API key presente
- [ ] **Sugestões geradas** — IA responde com sugestão
- [ ] **Deploy funciona** — Replit roda sem erros

---

## 🐛 Troubleshooting Rápido

| Problema                    | Solução                                    |
| --------------------------- | ------------------------------------------ |
| Port 3000 já em uso         | `lsof -i :3000` e matar processo           |
| Node modules faltando       | `npm install`                              |
| Gemini API error            | Verificar `GEMINI_API_KEY` em `.env.local` |
| DB não criado               | `npm run db:migrate`                       |
| Componentes UI não aparecem | `npm install shadcn-ui`                    |
| TypeScript errors           | `npm run type-check` e corrigir            |

---

## 📄 Arquivos de Documentação Adicional

- `/replit.md` — Setup específico Replit
- `/README_SUBMISSAO.md` — Overview para avaliadores ← **LEIA PRIMEIRO**
- `/shared/models/chat.ts` — Estrutura conversa IA
- `/server/api/` — Comentários em cada endpoint

---

## ✅ Status de Implementação

| Feature             | Status      | Arquivo                           |
| ------------------- | ----------- | --------------------------------- |
| Autenticação        | ✅ Completo | `/server/api/auth.ts`             |
| CRUD Tickets        | ✅ Completo | `/server/api/tickets.ts`          |
| Classificação IA    | ✅ Completo | `/server/api/classification.ts`   |
| Respostas Sugeridas | ✅ Completo | `/server/api/suggestions.ts`      |
| Dashboard           | ✅ Completo | `/client/src/pages/Dashboard.tsx` |
| Analytics           | ✅ Completo | `/server/api/analytics.ts`        |
| Banco Dados         | ✅ Completo | `/shared/schema.ts`               |
| Deploy Replit       | ✅ Completo | Ao vivo em g4-hermes.replit.app   |

---

**Para auditar:** Comece pelo `/README_SUBMISSAO.md` nesta pasta, depois explore os arquivos acima conforme curiosidade.

**Preparado por:** Reny Grando  
**Data:** 24 de março de 2026
