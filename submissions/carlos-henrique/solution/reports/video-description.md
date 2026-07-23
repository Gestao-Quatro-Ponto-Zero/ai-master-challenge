# JourneyGraph Video Description
**Tagline:** Governed Retention Intelligence from Temporal Customer Journeys.


## Short — English

JourneyGraph converts fragmented SaaS events into governed customer journeys, stable graph evidence, explainable human-review queues, and `UNTESTED` experiment designs. This local demo uses a fixed historical snapshot and performs no automatic customer action.

Repository: [REPOSITORY_URL_PENDING]
Public demo: [PUBLIC_DEMO_URL_PENDING]
Pull Request: [PR_URL_PENDING]

## Full — English

JourneyGraph is a governed retention-intelligence product built for fragmented SaaS data. Account, subscription, usage, support, churn, and reactivation records arrive at different grains, so direct joins and static account labels can create inflated or incomplete views.

The pipeline audits source relationships, reconstructs a canonical temporal event log, preserves invalid chronology in quarantine, builds customer journeys, and promotes only supported stable evidence into a NetworkX-first graph. Deterministic review queues keep evidence explainable and require human disposition. An Experiment Lab translates observations into eight test designs with eligibility, power, safeguards, and readiness status; every design remains `UNTESTED`.

The demonstration uses Next.js, Python, and NetworkX with fixed local JSON snapshots. It runs without an external API, database, credential, or runtime AI service. The official local flow is:

```bash
cd submissions/carlos-henrique/solution/app
npm ci
npm run build:data
npm run dev
```

All evidence comes from a historical snapshot through December 31, 2024. Results are descriptive, graph relationships are non-causal, queues are for human review, and the application performs no customer action.

- Repository: [REPOSITORY_URL_PENDING]
- Public demo: [PUBLIC_DEMO_URL_PENDING]
- Pull Request: [PR_URL_PENDING]

## Curta — Português do Brasil

O JourneyGraph transforma eventos SaaS fragmentados em jornadas governadas, evidência de grafo estável, filas explicáveis para revisão humana e desenhos experimentais `UNTESTED`. A demonstração usa um snapshot histórico fixo, não produz score preditivo e não executa ação sobre clientes.

Repositório: [REPOSITORY_URL_PENDING]
Demonstração pública: [PUBLIC_DEMO_URL_PENDING]
Pull Request: [PR_URL_PENDING]

## Publication Note

The placeholders must be replaced only after each destination exists and has been opened in a clean browser session. No video URL is included until upload and visibility validation are complete.
