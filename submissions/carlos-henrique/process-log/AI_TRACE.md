# AI Collaboration Trace

## Scope

JourneyGraph used an AI coding assistant for task decomposition, initial code and documentation drafts, review prompts, test scaffolding, risk identification, alternative generation, and iterative corrections. Its outputs were proposals. Carlos Henrique retained responsibility for scope, evidence interpretation, methodological gates, privacy boundaries, validation acceptance, and every commit. No AI capability runs inside the delivered product.

## Tools

| Tool | Role | Typical use | Human oversight | Limitations observed |
|---|---|---|---|---|
| AI coding assistant in the Codex task environment | Repository-scoped implementation and review support | Break a phase into checks, draft bounded changes, inspect outputs, propose tests, and summarize evidence | Carlos supplied phase gates, accepted or rejected alternatives, reviewed diffs and visible output, required tests, and authorized local commits | Model/version was not preserved in repository evidence; suggestions could be incomplete, overbroad, platform-specific, or linguistically inconsistent |

No undocumented model name or version is claimed. Python, Git, npm, Vitest, Playwright, and NetworkX were deterministic engineering or validation tools, not AI authorities.

## Phase-by-Phase Trace

| Phase | Objective | AI contribution | Human intervention | Validation | Outcome |
|---|---|---|---|---|---|
| Dataset audit | Establish grains, keys, temporal fields, and join safety | Drafted profiling and relationship checks | Rejected the mega-join and required immutable raw inputs | Reconciliations, hashes, relationship multipliers, pytest | Audited sources; unsafe joins documented |
| Event log | Create one governed temporal contract | Drafted event normalization, quality flags, and tests | Required canonical identities, quarantine, recurrence, and no silent repair | Event reconciliation, idempotence, temporal tests | 13,927 active and 21,659 quarantined events |
| Churn analysis | Produce descriptive retention diagnostics | Drafted cutoff-safe features and reports | Defined account grain, recurrent outcomes, MAIN/STRICT sensitivity, and non-causal language | Reconciliations, leakage checks, pytest | Governed descriptive diagnostics |
| Survival analysis | Describe time-to-first-churn with censoring | Drafted Kaplan–Meier, Nelson–Aalen, RMST, and landmarks | Withheld Cox after reviewing event count, warning sensitivity, and untested assumptions | At-risk tables, sensitivity reports, deterministic hashes | Descriptive survival evidence with warnings |
| Journey mining | Build ordered histories and recurring sequences | Drafted scoped sequences, n-grams, stability classes, and taxonomy | Required account support, exposure controls, and rejection of unstable patterns | MAIN/STRICT comparison, support gates, tests | Stable patterns separated from rejected evidence |
| Graph construction | Connect promoted journey evidence | Drafted NetworkX graphs, metrics, exports, and queries | Selected NetworkX-first, optional Neo4j, bounded promotion, and descriptive semantics | Graph reconciliation, quality gate, tests | Governed local JourneyGraph |
| Watchlist | Organize evidence for review | Drafted deterministic rules, evidence packets, and queue metrics | Prohibited probability claims and separated quality from behavioral review | Rule reconciliation, confidence gates, tests | Seven human-review queues |
| Experiment Lab | Turn observations into test designs | Drafted hypotheses, power checks, SAP, guardrails, and simulations | Kept all causal statuses `UNTESTED` and classified feasibility | Registry reconciliation, leakage and execution checks | Eight governed designs; no experiment result |
| Dashboard | Build evaluator-facing product narrative | Drafted local JSON builder, pages, components, and test coverage | Required fixed snapshots, causal/privacy guardrails, reduced graph density, and human-review language | Lint, typecheck, Vitest, Playwright, build, visual review | Deterministic local demonstration |
| Localization | Deliver a coherent pt-BR interface | Drafted translations and test updates | Rejected lexical substitution, required complete messages, aliases, and visual review | 18 Vitest checks, 36 Playwright checks, build, screenshots | Fully localized and anonymized interface |
| Submission documentation | Make the result evaluator-navigable | Drafted README, architecture narrative, and consistency checks | Reconciled every metric, removed unsupported deployment claims, and bounded limitations | Documentation validator and link checks | Consolidated submission documentation |
| Cross-platform hardening | Make the official build path executable across systems | Drafted a Node wrapper and focused test | Reproduced the Windows failure, rejected a manual workaround, and required one official command | Two deterministic rebuilds, Vitest, lint, typecheck, build | Cross-platform `npm run build:data` |

## Prompt Evidence

| Phase evidence | Repository reference | Evidence type | Summary |
|---|---|---|---|
| Foundations through cross-platform hardening | [prompts.md](prompts.md) | `reconstructed instruction summary` | Phase objectives, boundaries, expected gates, and authorized commit messages were summarized after execution. |
| Human judgment and AI collaboration | [prompts.md](prompts.md#fase-10b--evidências-de-julgamento-humano-e-colaboração-com-ia) | `reconstructed instruction summary` | Required a repository-backed separation of suggestion, judgment, correction, rejection, and validation. |
| Corrective implementation evidence | [workflow.md](workflow.md) | Execution record | Phase steps, failures, corrections, tests, and final gates provide stronger evidence than an unpreserved chat transcript. |

The exact wording of many interactions is unavailable. Those entries are not quoted and are identified as `reconstructed instruction summary`.

## Verification Model

```text
AI suggestion → human review → test → correction → revalidation → local commit
```

The cycle was fail-closed: a proposal did not become accepted evidence merely because code ran. Human review checked the intended grain, time boundary, privacy, causal language, operating-system behavior, and evaluator experience; deterministic tests and reports then checked the approved contract.

## Limitations of the Trace

- Not every interaction was preserved.
- Some prompts were reconstructed by objective and are explicitly labeled `reconstructed instruction summary`.
- External tool logs and transient terminal output may be incomplete.
- Git history, repository reports, tests, and validation outputs are the primary verifiable sources.
- The trace demonstrates review and correction, but cannot reproduce private reasoning or every discarded draft.
- Future operational decisions, interventions, and experiments remain outside this evidence boundary and require fresh human approval.
