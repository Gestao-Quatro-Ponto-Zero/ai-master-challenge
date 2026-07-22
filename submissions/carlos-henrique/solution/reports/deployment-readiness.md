# JourneyGraph Deployment Readiness

## Classification

**READY_WITH_WARNINGS**

The application has a reproducible production build, local versioned data, no required secrets, and no runtime APIs. Public deployment remains a user-controlled action and requires a platform decision, smoke test, visibility review, and minimal production observability. The repository is not configured as a pure static export, so the target must support a Next.js runtime or an explicitly validated export change in a future phase.

## Readiness Assessment

| Area | Evidence | Classification | Deployment implication |
|---|---|---|---|
| Framework | Next.js 16, React 19, TypeScript strict | READY | Use a platform with supported Next.js build/runtime |
| Production build | `npm run build` passes with ten static routes including not-found | VALIDATED | Re-run in deployment pipeline |
| Static data | 15 versioned JSON snapshots under `public/data` | VALIDATED | Can deploy committed snapshots without rebuilding analytics |
| Environment variables | `.env.example` documents demo mode; no variable is required for the validated snapshot | READY | Do not add secrets or platform-only configuration without review |
| Secrets and credentials | None required by the application | VALIDATED | Secret scan must remain clean |
| Runtime APIs | None | VALIDATED | No API connectivity or egress is needed |
| File paths | App uses local public assets; build-data wrapper resolves platform-native paths | VALIDATED | Configure project root correctly |
| Case sensitivity | Repository paths use canonical casing | READY_WITH_WARNING | Verify on Linux deployment filesystem |
| Asset paths | Screenshots are documentation assets; app data uses `/data/*.json` | VALIDATED | Smoke-test all local data requests |
| Node version | 20.9 or newer documented; 24.15 validated locally | READY | Pin a supported major in platform settings |
| Python at runtime | Not required | VALIDATED | Do not add Python to runtime image |
| Python at build time | Required only if `npm run build:data` executes | OPTIONAL | Include pandas/NumPy and governed inputs only for rebuild strategy |
| `build:data` | Cross-platform wrapper, scoped EOL policy, and explicit serializer validate 25 inputs and reproduce 15 snapshots with zero drift | VALIDATED | Optional in deploy pipeline if committed snapshots are trusted |
| Package lock | `package-lock.json` is versioned, resolves Next.js `16.2.11`, and overrides `sharp 0.35.3` | VALIDATED | Use `npm ci`; fail if the versions, override, or audit change |
| Production start | `npm run start` after `npm run build` | VALIDATED LOCALLY | Platform may supply its own Next.js start command |
| Security | Next.js `16.2.11`, `sharp 0.35.3`, and zero production vulnerabilities at final validation | VALIDATED | Repeat `npm audit --omit=dev` before publication |
| Privacy | No displayed raw account keys or PII-like fields in demo snapshots | VALIDATED | Repeat PII/ID scan and route review |
| Authentication | Not implemented | WARNING | Publish only evidence intended for public access |
| Observability | No production monitoring or alerting | WARNING | Add basic availability/error monitoring for a persistent public demo |
| Rate limiting | Not applicable to a read-only local-data demo | NOT_APPLICABLE | Reassess if APIs are introduced |
| External service dependency | None at runtime | VALIDATED | Deployment should not request service credentials |

## Data Strategy for Public Deployment

### Recommended for the current demo: include generated JSONs

Deploy the 15 committed JSON snapshots and run `npm ci` followed by `npm run build`. This path minimizes build-time dependencies, preserves the validated inventory digest, and prevents raw or ignored data from entering the platform. The pipeline should still verify that the committed snapshots and metric matrix match the approved commit.

### Alternative: run `build:data` in the pipeline

Use this only if the platform can install Python 3 plus `requirements.txt` and has all 25 governed, versioned inputs. Run `npm run build:data` before `npm run build`, compare the 15 filenames and hashes with the approved baseline, and fail on divergence. Raw CSVs are neither required nor permitted in the deployment repository.

## Required Warnings Before Publication

- No authentication means the deployed evidence is public to anyone with access to the URL.
- The app is a fixed historical demonstration, not a live retention service.
- Availability monitoring and a rollback owner must be named.
- All seven routes, local JSON requests, mobile layout, and interpretation boundaries must be smoke-tested on the final URL.

## Publication Decision

Internal technical readiness supports a deployment attempt. External deployment itself is `PENDING_USER_ACTION` and must follow [deployment-runbook.md](deployment-runbook.md). No platform has been configured in this phase.
