CHECKPOINT: 20 — Final runtime and responsive visual validation
STATUS: PASS
OBJECTIVE: Verify the post-correction application in Compose, finish mobile viewport coverage, and exercise the Decision Room through the real browser.
WORK COMPLETED:
- Rechecked project-scoped API and web containers; both were healthy. Direct API and frontend proxy health routes returned `status=ok`, `analysis=loaded`, `data=source-csv`.
- Revisited all four chapters at 390×844 after the prior mobile CSS correction; `documentElement.scrollWidth` did not exceed the viewport width.
- Revisited all four chapters at 320×568. The pass found a genuine Chapter 03 overflow: the account-candidate header badge extended to x=326 in a 320px viewport.
- Changed only the small-screen header layout for `.account-candidates .panel-head` to stack and align left. Rebuilt the web container and repeated all four 320×568 checks; each had `scrollWidth=320`, `innerWidth=320`.
- Submitted the Chapter 04 scenario from the actual rendered UI. It selected 50 contacts, calculated 5 assumed incremental retained accounts and 5,000 user-supplied cost units; value and net remained UNKNOWN because assumed monthly value is zero.
- Checked keyboard Tab focus (visible 3px gold outline) and emulated `prefers-reduced-motion: reduce` (chapter animation 0.01ms; document scroll behavior auto).
- Prior current-mission browser measurements remain applicable at 1440×900, 1366×768, 768×1024 and 390×844; the final CSS addition is limited to widths ≤760px.
FILES CREATED: None in this checkpoint.
FILES MODIFIED: `solution/apps/web/src/styles.css` (mobile-only Chapter 03 panel-head layout).
COMMANDS EXECUTED:
- `docker compose -p ravenstack-remediation -f compose.yaml ps` (from workspace root and standalone solution root).
- `curl -fsS http://localhost:8000/api/health`; `curl -fsS http://localhost:5173/api/health`.
- `docker compose -p ravenstack-remediation -f compose.yaml up --build -d web` (standalone solution root).
- `npm test -- --run`; `npm run build` (from `solution/apps/web`).
- Playwright page navigation, viewport changes, DOM geometry, UI scenario submission, keyboard and reduced-motion checks.
TESTS EXECUTED: Frontend Vitest suite and TypeScript/Vite production build; real browser responsive and scenario smoke checks.
TEST RESULTS: 6 frontend tests passed; build passed (2,200 modules). All four chapters passed no-horizontal-overflow checks at 390px and 320px after the corrections. Live scenario response matched displayed arithmetic. Vite still warns on 662.02kB minified JS (186.41kB gzip).
EVIDENCE LEVEL: LOCAL_RUNTIME
BUSINESS FINDINGS: NONE
UNKNOWN: No final screenshot could be saved in the submission because the browser screenshot tool only allows files under its configured LeickOS roots. No screenshot was written outside the authorized package. Rendered page content and browser geometry were observed directly.
BLOCKERS: Screenshot artifact persistence is blocked by the browser tool's allowed-root policy; the interface itself remained available for visual and interaction inspection.
RISKS: Bundle warning remains. This was a focused browser smoke check, not a full assistive-technology audit or automated E2E suite.
NEXT STEP: Publish the consolidated evidence and run the final analytical/API/frontend/Compose verification matrix.
