# JourneyGraph Retention Intelligence

A local, governed demonstration dashboard that turns the audited outputs from Phases 3-8 into an executive product narrative. It presents historical observations, quality limitations, anonymous journeys, bounded graph evidence, human-review queues, and untested experiment designs. It does not run interventions or make causal or predictive claims.

## Requirements

- Node.js 20.9 or newer (validated with Node.js 24.15)
- npm 10 or newer (validated with npm 11.12)
- Python virtual environment at `../.venv/` with pandas, NumPy, and pytest
- Phase 3-8 artifacts at their governed paths under `../artifacts/`, `../data/processed/`, and `../config/`

No backend, database, cloud account, external API, external LLM, or network service is required at runtime.

## Install

From `solution/app`:

```powershell
npm ci
```

`node_modules`, `.next`, test reports, caches, and TypeScript build metadata are ignored and must not be committed.

## Build the local demo data

```powershell
npm run build:data
```

The builder verifies the SHA-256 hashes of 25 authorized Phase 3-8 inputs before writing exactly 15 deterministic JSON files to `public/data/`. It fails closed on input drift, PII-like fields, raw operational IDs, prohibited product language, non-finite numbers, graph-limit violations, invalid priorities, or executed-experiment states.

## Run

Development:

```powershell
npm run dev
```

Production:

```powershell
npm run build
npm run start
```

Open `http://localhost:3000`. The product always shows a demo badge and the historical cutoff. `NEXT_PUBLIC_DEMO_MODE=true` is documented in `.env.example`, but the demonstration does not depend on environment-specific services.

## Routes

- `/` - Executive Overview
- `/quality` - Data & Quality
- `/journeys` - Journey Explorer
- `/graph` - JourneyGraph
- `/watchlist` - Intervention Watchlist
- `/experiments` - Experiment Lab
- `/governance` - Governance
- `/demo` - eight-step Guided Demo
- `/methodology` - evidence and interpretation boundaries

## Tests and validation

```powershell
npm run lint
npm run typecheck
npm run test
npm run build
npm run test:smoke
npm audit --omit=dev
```

The smoke suite starts the production server and checks all eight primary routes in desktop, tablet, and mobile Chromium profiles. Desktop route checks also refresh the seven reviewed screenshots in `../reports/screenshots/`.

From `solution`:

```powershell
.venv\Scripts\python.exe -m compileall -q src scripts
.venv\Scripts\python.exe -m pytest -q
```

## Architecture

```text
Governed Phase 3-8 artifacts
              |
              v
scripts/build_dashboard_data.py
  hash gate + schema/privacy/semantic gates
              |
              v
app/public/data/*.json (15 local snapshots)
              |
              v
Next.js App Router + server-side Zod parsing
              |
              v
Client interactions: Recharts, Cytoscape, deterministic Explain This
```

The application is statically prerendered. Data files are local, versioned snapshots; there is no live backend. Interactive components only filter, select, or explain already-governed evidence.

## Privacy and interpretation boundaries

- No raw `account_id`, account name, email, feedback text, or other PII is displayed.
- Three real analytical accounts are represented only by `DEMO_A`, `DEMO_B`, and `DEMO_C` in the interface. Their internal `acct_*` keys are deterministic anonymous keys, not operational IDs.
- Watchlist rows are bounded demonstration evidence and require human review.
- There is no score, probability, automated action, outbound integration, or live experiment.
- Graph relationships and historical patterns are descriptive. They do not establish causality.
- Revenue is contextual associated MRR, not revenue at risk, saved revenue, or attributed impact.

## Known limitations

The app is a local demonstration surface, not a production operations console. Authentication, authorization, production observability, live freshness, intervention delivery, experiment execution, external LLM explanations, and outbound integrations are intentionally not implemented. Graph views are reduced and explicitly truncated. Historical data quality warnings remain visible and limit interpretation.
