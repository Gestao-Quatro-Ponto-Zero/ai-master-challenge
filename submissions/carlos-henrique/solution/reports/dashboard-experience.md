# Dashboard Experience

## Product intent

JourneyGraph Retention Intelligence is an answer-first demonstration for executives, retention operators, data teams, and governance reviewers. Its core narrative is: fragmented operational events become usable only after quality gates; usable events become governed journeys; promoted, stable evidence supports human investigation; hypotheses remain untested until a future governed experiment is approved.

The interface is in English to maximize evaluator and enterprise-demo accessibility. Every primary view shows the fixed historical cutoff and demo status.

## Information architecture

| Area | Route | Decision supported | Boundary |
|---|---|---|---|
| Executive Overview | `/` | Understand scale, evidence flow, and headline limitations | No causal or predictive conclusion |
| Data & Quality | `/quality` | Separate usable evidence from quality backlog | Quarantine is not behavioral signal |
| Journey Explorer | `/journeys` | Inspect three representative anonymous journeys | No raw IDs or account ranking |
| JourneyGraph | `/graph` | Explore bounded event, pattern, and governance evidence | Reduced, filtered, descriptive view |
| Watchlist | `/watchlist` | Review queues and evidence packets | Human review only |
| Experiment Lab | `/experiments` | Compare future test designs and feasibility | All hypotheses remain `UNTESTED` |
| Governance | `/governance` | Audit privacy, temporal, semantic, and operational controls | No live enforcement service |
| Guided Demo | `/demo` | Deliver the product story in eight steps | Historical local snapshot |

## Executive comprehension

The landing page leads with eight reconciled metrics: 500 anonymous accounts, 35,586 processed events, 13,927 usable events, 4,221 journeys, 435 promoted patterns, 43 promoted transitions, seven review queues, and eight untested experiments. The evidence pipeline immediately explains the transformation from raw data to experiment design. Supporting cards keep data quality, journey outcomes, and business context separate.

Charts use neutral titles, visible populations, explicit denominators, and zero baselines where appropriate. Associated MRR is shown only as context and never as risk, saved value, or causal impact.

## Interaction design

- Journey filters change demo account, scope, outcome, quality, and timeline evidence.
- Graph controls change mode, minimum support, and top-N nodes. The initial event-flow view is limited to 16 of 35 prepared relationships to prevent a hairball.
- Watchlist filters preserve queue and priority semantics; evidence opens in a governed detail panel.
- Experiment cards open specifications with eligibility, sample planning, metrics, SAP, safeguards, and `UNTESTED` status.
- `Explain this` disclosures use deterministic source data to expose observation, population, denominator, quality, stability, limitations, authorized next step, and prohibited interpretation.
- Guided Demo provides eight keyboard-operable steps with back/next navigation and direct route links.

## Visual system and accessibility

The product uses a restrained B2B SaaS palette: navy navigation, slate surfaces, blue interaction color, amber warnings, green reviewed states, and red only for genuine blocks. Typography is compact but readable, with a stable grid and consistent card hierarchy.

The app includes semantic landmarks, visible focus states, labelled inputs, button names, `aria-live` detail areas, graph alternative labels, reduced-motion support, responsive tables/cards, loading UI, error boundary, not-found state, and reusable empty/error components. The production app was exercised at 1440x1000 desktop, iPad Mini tablet, and 390x844 mobile viewports.

## Reviewed screenshots

The following files were captured by Playwright from the actual production build and visually reviewed:

1. `screenshots/01-executive-overview.png`
2. `screenshots/02-data-quality.png`
3. `screenshots/03-journey-explorer.png`
4. `screenshots/04-journeygraph.png`
5. `screenshots/05-watchlist.png`
6. `screenshots/06-experiment-lab.png`
7. `screenshots/07-governance.png`

The review covered hierarchy, labels, numbers, chart scales, graph density, MRR wording, limitations, PII exposure, causal language, and responsive behavior. The graph was refined after review from 35 initially visible parallel relationships to a 16-edge circular overview.

## Intentional limitations

This is a static local demonstration. There is no authentication, live backend, live refresh, operational account lookup, production observability, automated intervention, experiment execution, external LLM, or outbound integration. Empty and error states are implemented and unit-tested, but production failure telemetry is outside this phase.
