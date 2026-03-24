# Hermes - AI-Native IT Support Ticket System

## Overview
Hermes is an AI-powered IT support ticketing platform that automates ticket classification, routing, and response suggestions. Inspired by the Greek god Hermes — messenger, negotiator, and guide between worlds.

## Architecture
- **Frontend**: React + TypeScript + Tailwind CSS + Shadcn UI + Recharts
- **Backend**: Express.js + TypeScript
- **Database**: PostgreSQL with Drizzle ORM
- **AI**: OpenAI via Replit AI Integrations (gpt-5.1 for classification/suggestions)

## Design System
- Primary: Deep Emerald Green #0F3D2E
- Secondary: Antique Gold #C8A44D
- Background: Marble white #F4F1EA
- Accent: Dark bronze #5A4633
- Fonts: Playfair Display (headings) + Inter (body)

## Key Features
- **AI Ticket Classification**: Auto-categorizes tickets (Hardware, Access, HR Support, Storage, Purchase, Administrative rights, Internal Project, Misc)
- **AI Response Suggestions**: Generates professional responses for tickets
- **Dashboard**: Real-time metrics (active tickets, resolution time, SLA risk, automation rate)
- **Ticket Management**: Full CRUD with status/priority tracking
- **Knowledge Base**: Browse articles by category
- **Analytics**: Charts for ticket volume, category distribution
- **Settings**: AI automation rule toggles

## Database Tables
- `users` - System users (admin, agent, customer)
- `teams` - Support teams with SLA hours
- `tickets` - Main ticket records with AI confidence scores
- `ticket_events` - Event log for tickets
- `knowledge_base` - KB articles
- `suggestions` - AI-generated response suggestions
- `bottlenecks` - Operational bottleneck tracking

## API Endpoints
- `GET/POST /api/tickets` - List/create tickets
- `GET/PATCH /api/tickets/:id` - Get/update ticket
- `POST /api/tickets/classify` - AI classification
- `POST /api/tickets/:id/suggest-response` - AI response suggestion
- `GET /api/dashboard/metrics` - Dashboard data
- `GET /api/users` - List users
- `GET /api/teams` - List teams

## Integrations
- `javascript_database` - PostgreSQL (installed)
- `javascript_openai_ai_integrations` - OpenAI AI (installed)

## File Structure
- `shared/schema.ts` - Drizzle tables + Zod schemas
- `shared/routes.ts` - API contract definitions
- `server/routes.ts` - Express route handlers + seed data
- `server/storage.ts` - Database storage layer
- `server/db.ts` - Database connection
- `client/src/pages/` - React pages (dashboard, tickets, analytics, knowledge-base, settings, login)
- `client/src/components/` - Reusable components (sidebar, stat cards, badges)
