# G4 Tech Support Tickets

A full-featured customer support and helpdesk platform built with React, TypeScript, Vite, Tailwind CSS, and Supabase. Includes omnichannel ticket management, AI agents, knowledge base, operator workspace, campaign management, LLM observability, and more.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Edge Functions](#edge-functions)
- [Creating the First Admin User](#creating-the-first-admin-user)
- [Running the Project](#running-the-project)
- [Roles and Permissions](#roles-and-permissions)
- [Main Features](#main-features)

---

## Prerequisites

- [Node.js](https://nodejs.org/) v18 or higher
- [npm](https://www.npmjs.com/) v9 or higher
- A [Supabase](https://supabase.com/) account and project (already provisioned)

---

## Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Frontend    | React 18, TypeScript, Vite          |
| Styling     | Tailwind CSS                        |
| Icons       | Lucide React                        |
| Routing     | React Router DOM v7                 |
| Database    | Supabase (PostgreSQL + RLS)         |
| Auth        | Supabase Auth (email/password)      |
| Backend     | Supabase Edge Functions (Deno)      |
| CSV Parsing | PapaParse                           |

---

## Project Structure

```
src/
├── channels/          # Channel adapters (email, chat, API) and normalizers
├── components/        # Feature-specific UI components
│   ├── agents/        # AI agent management components
│   ├── ai-usage/      # AI usage analytics
│   ├── automations/   # Automation rule editor
│   ├── budget/        # LLM budget management
│   ├── campaigns/     # Campaign management UI
│   ├── costs/         # LLM cost tracking
│   ├── customer-analytics/
│   ├── dashboard/
│   ├── events/
│   ├── knowledge/     # Knowledge base management
│   ├── layout/        # Sidebar, main layout
│   ├── llm/           # LLM model, policy and log components
│   ├── metrics/       # Operator performance metrics
│   ├── operators/
│   ├── queues/
│   ├── router/        # LLM router debug
│   ├── scheduler/     # Campaign scheduler
│   ├── segments/      # Customer segmentation
│   ├── supervisor/    # Supervisor monitoring dashboard
│   ├── tickets/       # Ticket list, detail, composer
│   ├── tokens/        # Token usage tracking
│   ├── users/
│   └── workspace/     # Operator workspace
├── contexts/          # React context providers (Auth)
├── hooks/             # Custom React hooks
├── layouts/           # Page layouts
├── lib/               # Supabase client, API client
├── pages/             # Route-level page components
├── router/            # React Router configuration
├── services/          # Business logic and Supabase service calls
├── types/             # TypeScript type definitions
└── widgets/           # Embeddable chat widget

supabase/
├── functions/         # Supabase Edge Functions (Deno)
└── migrations/        # SQL migrations (applied in order)
```

---

## Installation

1. **Clone the repository:**

```bash
git clone <repository-url>
cd g4-tech-support-tickets
```

2. **Install dependencies:**

```bash
npm install
```

3. **Configure environment variables** (see next section).

---

## Environment Variables

Create a `.env` file at the root of the project with the following variables:

```env
VITE_SUPABASE_URL=https://<your-project-ref>.supabase.co
VITE_SUPABASE_ANON_KEY=<your-supabase-anon-key>
```

You can find these values in your Supabase project under **Project Settings > API**.

> **Note:** Never commit your `.env` file to version control. It is already listed in `.gitignore`.

---

## Database Setup

All database migrations are located in `supabase/migrations/` and must be applied in order. The migrations cover:

- RBAC (Roles, Permissions, User Roles)
- User profiles with extended fields
- Audit logs (immutable)
- Omnichannel tickets and conversations
- SLA policies
- Tags system
- Automation rules
- Macros
- Operator presence
- AI Agents schema
- Knowledge base with vector search (pgvector)
- LLM usage logs, model registry, token tracking, cost calculator
- LLM policies and budgets
- Customer analytics, events, segmentation
- Campaign management, scheduler, delivery, analytics
- API keys and integration logs

### Applying migrations

If you are using the Supabase dashboard, navigate to **SQL Editor** and run each migration file in chronological order, or use the Supabase MCP tools if available in your environment.

---

## Edge Functions

The following Edge Functions are deployed to Supabase:

| Function                    | Description                                      |
|-----------------------------|--------------------------------------------------|
| `create-admin-user`         | Creates a new auth user with admin privileges    |
| `agent-executor`            | Executes AI agent runs                           |
| `agent-router`              | Routes requests to the appropriate agent         |
| `agent-memory`              | Manages agent memory (short and long term)       |
| `agent-observability`       | Logs agent traces and metrics                    |
| `agent-tools`               | Provides tool execution for agents               |
| `llm-router`                | Routes LLM requests with policy enforcement      |
| `llm-manager`               | Manages LLM model configurations                 |
| `rag-engine`                | Retrieval-Augmented Generation engine            |
| `retrieval-service`         | Vector similarity retrieval                      |
| `document-ingest`           | Ingests documents into the knowledge base        |
| `document-process`          | Processes and chunks documents                   |
| `embedding-pipeline`        | Generates and stores embeddings                  |
| `channel-ingest`            | Ingests messages from external channels          |
| `campaign-scheduler-worker` | Triggers scheduled campaigns                     |
| `campaign-delivery-worker`  | Executes campaign message delivery               |

---

## Creating the First Admin User

After applying all migrations, you need to create an admin user. Call the `create-admin-user` Edge Function:

```bash
curl -X POST https://<your-project-ref>.supabase.co/functions/v1/create-admin-user \
  -H "Authorization: Bearer <your-supabase-anon-key>" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your-secure-password"}'
```

After the user is created, go to the Supabase **SQL Editor** and assign the admin role:

```sql
INSERT INTO user_roles (user_id, role_id)
SELECT '<user-id-returned>', id FROM roles WHERE name = 'admin';
```

---

## Running the Project

**Development server:**

```bash
npm run dev
```

The app will be available at `http://localhost:5173`.

**Type checking:**

```bash
npm run typecheck
```

**Production build:**

```bash
npm run build
```

**Preview production build:**

```bash
npm run preview
```

---

## Roles and Permissions

The system ships with four default roles:

| Role       | Description                                           |
|------------|-------------------------------------------------------|
| admin      | Full system access — manages users, roles, all modules |
| supervisor | Manages tickets and users, views reports              |
| operator   | Creates and resolves tickets, handles workspace       |
| viewer     | Read-only access to tickets                           |

Roles can be customized via the **Roles** page (requires `roles.manage` permission). Custom roles can be created and fine-grained permissions can be assigned per role.

---

## Main Features

### Ticketing
- Omnichannel support: email, chat, API
- Ticket creation, assignment, SLA tracking, tagging, macros
- Automated rules (automations)
- Resolution with notes

### Operator Workspace
- Real-time conversation panel
- Internal notes
- Transfer between operators and queues
- Presence indicators

### Supervisor Dashboard
- Live queue monitoring
- Operator performance metrics
- Active ticket oversight

### AI Agents
- Agent creation and configuration
- LLM model assignment
- Tool definitions and execution
- Agent memory (short/long term)
- Observability traces

### Knowledge Base
- Document ingestion and processing
- Chunk viewer and embedding monitor
- Vector similarity search (pgvector)
- Feedback loop for retrieval quality

### LLM Observability
- Model registry
- Request logging
- Token usage tracking
- Cost calculator per model and agent
- Budget limits per agent/model
- Prompt policies enforcement
- Router debug panel

### Customer Management
- Customer profiles with event history
- Segmentation with rule builder
- CSV import

### Campaigns
- Campaign creation and targeting by segment
- Scheduler with recurring execution
- Delivery engine with status tracking
- Analytics and performance charts

### Integrations & Developers
- API key management
- Integration logs
- Developer portal

### Administration
- User management
- Role and permission editor
- Audit log (immutable)
- CSV import
