---
name: G4 CRM Dashboard — Project Context
description: Full context on the G4 Business CRM Sales Analytics Dashboard implementation
type: project
---

This is a Next.js 14 (App Router) + TypeScript + Tailwind CSS dashboard for G4 Business CRM Sales Analytics.

**Why:** The project is a submission for the AI Master Challenge, challenge `data-001-churn`. The CRM dashboard demonstrates sales pipeline analytics using real CSV data.

**How to apply:** Always build on top of the existing project structure. Run `npm run dev` from `submissions/pedrolorenzoni/` to start.

## Tech Stack
- Next.js 14 App Router + TypeScript
- Tailwind CSS (configured from id-visual.md tokens)
- Recharts for charts
- React Context for auth (no backend)
- lucide-react for icons
- clsx for className merging

## Architecture
- `app/login/page.tsx` — login page with seller dropdown + admin button
- `app/dashboard/page.tsx` — main dashboard with KPI row + sidebar + list/kanban views
- `app/accounts/page.tsx` — account directory grid with rating badges, modal drawer, filters/sort
- `app/products/page.tsx` — product catalog cards + value staircase bar chart + revenue pie chart
- `app/team/page.tsx` — org chart by region + agent leaderboard table + agent detail drawer
- `app/deals/page.tsx` — paginated deals table (50/page) with filters, sortable columns, deal modal
- `app/performance/page.tsx` — KPI row + tabbed leaderboard (Agents/Managers/Regions) + region bar chart
- `context/AuthContext.tsx` — AuthProvider with role/agent state, localStorage persistence
- `lib/data.ts` — hardcoded CSV data as TypeScript arrays (DEALS, ACCOUNTS, PRODUCTS, SALES_AGENTS)
- `lib/accountRating.ts` — computeAllAccountRatings(), getRatingColor(), getRatingClass() — cached
- `lib/killScore.ts` — computeAllKillScores(), getKillScoreColor(), getKillScoreClass() — cached
- `components/DashboardNavbar.tsx` — fixed 70px navy navbar; view/onViewChange are optional props now; includes nav links (Dashboard/Contas/Produtos/Equipe/Deals/Performance); uses usePathname to highlight active link
- `components/AccountsSidebar.tsx` — 280px sidebar with search/filter/sort
- `components/DealDetailPanel.tsx` — right-side drawer for deal details + recommendations
- `components/views/ListView.tsx` — list view sorted by Deal Smell
- `components/views/KanbanView.tsx` — kanban by deal_stage (4 columns)
- `components/ui/Button.tsx` — 5 variants (primary/secondary/ghost/dark/gold)
- `components/ui/Badge.tsx` — pill badges for stages and scores
- `components/ui/Card.tsx` — card with hover gold border + killerPulse animation

## Navbar notes
- DashboardNavbar props are now optional: `view?` and `onViewChange?`
- View toggle only renders on /dashboard (checked via usePathname)
- New pages pass no props to DashboardNavbar (just `<DashboardNavbar />`)

## TypeScript gotcha
- Use `Array.from(new Set(...))` instead of `[...new Set(...)]` — tsconfig target doesn't support Set spread

## Data
- 81 active Engaging deals, 19 Won deals, 10 Lost deals in lib/data.ts
- 85 accounts from accounts.csv (all included)
- 35 sales agents from sales_teams.csv
- 8 products from products.csv

## Auth Roles
- Seller: sees only their own deals (filtered by sales_agent === agent)
- Admin: sees all deals; ListView shows grouped by agent with top 5 per agent

## Killer Deal Logic
- Deal Smell (0-100): 30% stage + 25% value + 25% account revenue + 20% recency
- Killer Score (0-100): 35% product price + 30% account employees + 20% stage urgency + 15% freshness
- KS >= 80 triggers "KILLER" badge + killer-pulse CSS animation
