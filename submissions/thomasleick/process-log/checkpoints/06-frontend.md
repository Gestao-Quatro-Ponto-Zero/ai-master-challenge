CHECKPOINT: 06 — Executive frontend
STATUS: PASS
OBJECTIVE: Deliver the four-chapter narrative, evidence exploration, revenue caveats and decision simulator over the REST API.
WORK COMPLETED:
- Added React/TypeScript/Vite application with Guided Investigation and Explore the Evidence modes.
- Four chapters are represented in navigation and include actual API data paths, segment comparison, reconciliation queue, transparent unknowns and scenario inputs.
- Responsive CSS and reduced-motion preference are included. The Evidence chapter now includes ticket-level first-response, resolution and escalation summaries with retrospective caveats; the Decision Room includes an explicit 30/60/90-day sequence.
- Removed unused imports/locals and removed a jsdom test-environment setting because no jsdom dependency is needed.
FILES CREATED: solution/apps/web source, package manifests, Nginx config and Dockerfile.
FILES MODIFIED: None outside candidate package.
COMMANDS EXECUTED: npm ci --ignore-scripts --no-audit --no-fund; npm run build; npm test; npm audit --audit-level=moderate; browser inspection at http://localhost:5173 with navigation through all chapters and a changed budget scenario; viewport test at 390×844.
TESTS EXECUTED: Vitest and manual browser interaction.
TEST RESULTS: Vitest 2/2 passed; npm audit found 0 vulnerabilities. All four chapters rendered against the rebuilt API. Scenario recalculated to 25 selected and 2.5 expected under assumptions. Browser console had no errors. Mobile document width 375 px at 390 px viewport; no horizontal overflow.
EVIDENCE LEVEL: LOCAL_RUNTIME.
BUSINESS FINDINGS: NONE.
UNKNOWN: Full assistive-technology evaluation and complete keyboard audit were not performed; source includes labels, semantic buttons/tables and reduced-motion CSS.
BLOCKERS: None known.
RISKS: Browser-level visual behavior must not be claimed from source inspection.
NEXT STEP: Preserve the manual browser/accessibility boundary and use the documented local Compose setup.
