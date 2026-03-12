# Copilot Instructions — Challenge 003 Lead Scorer

## Goal

Build a minimalist, simple and functional Next.js application that helps salespeople prioritize open deals using a _transparent_ scoring system based on the provided CRM CSV data.

This is a **product utility challenge**, not an academic ML challenge. Favor practical decisions, clarity, and maintainability over model complexity.

## Challenge Priorities (Non-Negotiable)

1. The app must run end to end (not mockups or static slides).
2. Use the real dataset files from `public/docs`:
   - `accounts.csv`
   - `products.csv`
   - `sales_teams.csv`
   - `sales_pipeline.csv`
3. Implement explicit deal scoring/prioritization logic (not just sorting by value).
4. Provide explainability: users must understand why each deal got its score.
5. Keep UX useful for non-technical sales users.

## Product Mindset

- Optimize for Monday-morning usage: a salesperson opens the app and immediately knows where to focus.
- Start simple and iterate. A robust heuristic scorer with clear explanations is preferred over opaque ML.
- Keep decision-support front and center: highlight priorities, risks, and suggested actions.

## Core User Flow

1. Login/selection page: user selects a salesperson from available agents.
2. Pipeline page: show that salesperson's open deals ranked by priority.
3. Deal explainability: each deal exposes top positive and negative scoring drivers.

## Scoring Guidance

- Build scoring as composable criteria with explicit multipliers/weights.
- Prefer deterministic, testable functions in a dedicated scoring module.
- Keep them explainable: each criterion should have a clear rationale that can be communicated to users.

## Explainability Requirements

For each deal, return:

- Final score.
- Criterion-level contributions (multiplier, signed impact, plain-language reason).
- Top positive and top negative factors.

UI should expose:

- Compact reasons in the table (2-3 chips).
- Full breakdown in detail panel/drawer.

## Next.js and Codebase Best Practices

- Use TypeScript strictly and keep domain types explicit.
- Keep pure business logic outside React components, put it inside `utils/` folder, especially the scoring logic.
- Validate parsed CSV schema and coerce types defensively.
- Isolate a component only when it has its own logic, it can be reused or it is a client component.

## UI/UX Standards

- Keep it simple, minimalist and functional. Avoid unnecessary decoration.
- Prioritized table must be scannable and sortable.
- Clearly label score tiers (e.g., High/Medium/Low) with accessible color contrast.
- Every score should have a visible rationale.
- Empty states and loading states must be explicit and user-friendly.

## Quality and Maintainability

- Write small, focused functions and avoid hidden side effects.
- Keep naming domain-driven (`deal`, `salesAgent`, `accountSector`, `scoreBreakdown`).
- Add concise comments only where logic is non-obvious.
- Preserve clean architecture and readable code for handoff.

## Testing Expectations

- Add unit tests for scoring functions and edge cases when possible.
- Validate that sorting and filtering match expected business rules.
- Smoke-test the full user flow locally before considering complete.

## Documentation Expectations

Ensure the repository clearly explains:

1. Setup: dependencies, commands, local URL.
2. Scoring logic: criteria used and business rationale.
3. Limitations: current constraints and what is needed to scale.
4. AI process evidence: what AI assisted with and how decisions were validated.

## AI Collaboration Principles

- When generating code, verify correctness against data and challenge goals.
- Keep artifacts transparent so evaluators can understand process quality.

## Implementation Guardrails

- Do not invent fields that are not present in the CSVs.
- Document any metric approximations explicitly.
- Keep scoring configurable (constants/weights centralized).
- Favor predictable behavior over clever but opaque heuristics.
