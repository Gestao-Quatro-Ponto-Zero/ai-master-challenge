# Process Log — AI Master Challenge

## Objective

Build a Churn Intelligence System that combines analytics, machine learning, generative AI, and product thinking to help executives identify churn risk, prioritize accounts, and convert insights into action.

---

## Tools Used

- **ChatGPT** — architecture design, KPI review, debugging, product framing, submission writing
- **VS Code** — implementation and backend development
- **FastAPI** — API layer
- **XGBoost** — churn prediction model
- **Gemini** — executive Q&A and insight generation
- **Lovable** — frontend prototyping
- **ngrok** — temporary API exposure for frontend integration

---

## Workflow

1. Reviewed the challenge and reframed the solution as a **decision intelligence system**, not just a dashboard.
2. Explored the RavenStack dataset and identified a key issue: historical churn, current active status, and predictive churn could not be treated as the same thing.
3. Built the backend in FastAPI, separating ingestion, processing, analytics, ML, and AI orchestration.
4. Trained an XGBoost model to generate `churn_score` and `risk_level`.
5. Corrected financial metrics that were initially distorted by using average revenue instead of aggregated account revenue.
6. Redesigned KPIs to distinguish:
   - total MRR
   - active MRR
   - inactive MRR
   - revenue at risk
   - ARPU variants
   - LTV proxy
7. Reworked revenue segmentation to show:
   - historical churn by revenue range
   - predictive churn by revenue range
   - active vs inactive MRR
8. Adjusted Top 10 risk ranking so it would reflect **active accounts only**, prioritized by:
   - risk level
   - MRR
   - churn score
   - ABC classification
9. Connected Gemini to provide executive interpretation and recommendations.
10. Structured the product into modules:
   - Executive Dashboard
   - Churn Risk
   - Recommendations
   - Kanban
   - WhatsApp approval simulation

---

## Where AI Was Wrong and How I Corrected It

### 1. Revenue logic
AI initially suggested revenue interpretations that used average MRR as executive revenue. I corrected this to use aggregated account MRR.

### 2. Active vs churned accounts
The dataset did not provide a reliable current active/inactive field. I defined operational logic based on churn history and account state in the analytical snapshot.

### 3. ARPU and LTV
Initial formulas mixed historical revenue with active account counts. I corrected ARPU to use the appropriate population and treated LTV as a transparent proxy.

### 4. Top 10 risk ranking
The first ranking mixed active and inactive accounts. I redesigned it to reflect only active accounts and prioritize executive relevance.

### 5. Dashboard consistency
Some visuals became inconsistent because cards, tables, and charts were not using the same population filters. I aligned them around the same business logic.

---

## What I Added That AI Alone Would Not

- Executive interpretation of KPI meaning
- Separation of historical churn vs predictive churn
- Prioritization based on revenue impact, not just risk score
- Product framing beyond analytics into workflow and decision support
- Consistency rules across metrics, charts, and ranking tables

---

## Key Design Decisions

- Use **historical churn** as a conservative base for LTV proxy
- Use **predictive churn** only for active accounts
- Use **active accounts only** for executive risk views
- Keep Top 10 risk aligned with executive prioritization
- Treat the system as a **Revenue Protection platform**, not just churn analytics

---

## Evidence Included

- API screenshots
- Dashboard screenshots
- Git history
- AI-assisted design and debugging flow
- Final code structure